from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty, ChannelParticipantsSearch
from telethon.errors import ChannelPrivateError, ChannelInvalidError
import os
import re
import time
import random
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Environment Variables
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
X_API_BEARER_TOKEN = os.environ.get("X_API_BEARER_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# --- Helper Functions ---

def get_google_trends(region="US"):
    """Fetches trending searches from Google Trends."""
    try:
        url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={region}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        return [item.title.text for item in soup.find_all('item')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Google Trends: {e}")
        return None

def get_x_trends(location_woeid=1):
    """Fetches trends from X/Twitter."""
    try:
        headers = {'Authorization': f'Bearer {X_API_BEARER_TOKEN}'}
        url = f'https://api.twitter.com/1.1/trends/place.json?id={location_woeid}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return [trend['name'] for trend in response.json()[0]['trends']]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching X Trends: {e}")
        return None

def get_youtube_trending_titles(region_code="US"):
    """Fetches trending YouTube titles."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", chart="mostPopular", regionCode=region_code, maxResults=10)
        response = request.execute()
        return [item['snippet']['title'] for item in response['items']]
    except Exception as e:
        print(f"Error fetching YouTube Trends: {e}")
        return None

def analyze_telegram_channel(channel_username: str) -> Optional[Dict]:
    """Analyzes a Telegram channel."""
    try:
        with TelegramClient('anon', API_ID, API_HASH) as client:
            client.start()
            full_channel = client(GetFullChannelRequest(channel_username))
            return {
                'subscribers': full_channel.full_chat.participants_count,
                'name': full_channel.chats[0].title,
                'description': full_channel.full_chat.about,
                'success': True
            }
    except (ChannelPrivateError, ChannelInvalidError, ValueError) as e:
        print(f"Error with channel {channel_username}: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f"General error analyzing channel: {e}")
        return {'success': False, 'error': str(e)}

def generate_metadata(keyword: str, trends: List[str]) -> Dict:
    """Generates channel metadata."""
    name = f"{keyword.title()} Trends"
    username = re.sub(r'[^a-zA-Z0-9_]', '', keyword.lower()) + "_trends"
    username = username[:32]
    description = f"Latest {keyword} trends!  {', '.join(trends[:3])} #TelegramTips"
    return {'name': name, 'username': username, 'description': description}

def heuristic_channel_ranking(channel_data: List[Dict]) -> List[Dict]:
    """Ranks channels by subscribers."""
    sorted_channels = sorted(channel_data, key=lambda x: x.get('subscribers', 0), reverse=True)
    for i, channel in enumerate(sorted_channels):
        channel['rank'] = i + 1
    return sorted_channels

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handles the analysis request."""
    keyword = request.form.get('keyword')
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400

    google_trends = get_google_trends() or []
    x_trends = get_x_trends() or []
    youtube_trends = get_youtube_trending_titles() or []
    all_trends = list(set(google_trends + x_trends + youtube_trends))

    telegram_results = []
    try:
        with TelegramClient('anon', API_ID, API_HASH) as client:
            client.start()
            search_results = client(SearchRequest(
                peer='telegram',  # Search globally
                q=keyword,
                filter=InputMessagesFilterEmpty(),
                min_date=None,
                max_date=None,
                offset_id=0,
                add_offset=0,
                limit=20,  # Limit the number of results
                max_id=0,
                min_id=0,
                hash=0
            ))
             # Process search results to extract channel usernames
            for chat in search_results.chats:
                 if hasattr(chat, 'username') and chat.username: # Ensure is a valid channel
                    channel_data = analyze_telegram_channel(chat.username)
                    if channel_data and channel_data['success']:
                        telegram_results.append({
                            'username': chat.username,
                            'subscribers': channel_data['subscribers'],
                            'name': channel_data['name'],
                            'description': channel_data['description']
                        })
                    time.sleep(random.uniform(0.5, 1.5))

    except Exception as e:
        print(f"Error during Telegram search: {e}")
        return jsonify({'error': 'Error during Telegram search'}), 500

    ranked_channels = heuristic_channel_ranking(telegram_results)
    metadata_suggestions = generate_metadata(keyword, all_trends)

    return jsonify({
        'google_trends': google_trends,
        'x_trends': x_trends,
        'youtube_trends': youtube_trends,
        'telegram_channels': ranked_channels,
        'metadata': metadata_suggestions
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=(os.environ.get("DEBUG_MODE", "False").lower() == "true"), host='0.0.0.0', port=port)
