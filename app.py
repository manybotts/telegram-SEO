from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelPrivateError, ChannelInvalidError

load_dotenv()

app = Flask(__name__)

# Environment Variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Used for YouTube
X_API_BEARER_TOKEN = os.environ.get("X_API_BEARER_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID"))  # Ensure this is an integer
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")


# --- Helper Functions ---

def get_google_trends(region="US") -> Optional[List[str]]:
    """Fetches trending searches from Google Trends (web scraping)."""
    try:
        url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={region}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        return [item.title.text for item in soup.find_all('item')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Google Trends: {e}")
        return None
    except Exception as e:
        print(f"Error parsing Google Trends data: {e}")
        return None

def get_x_trends(location_woeid=1) -> Optional[List[str]]:
    """Fetches trends from X."""
    try:
        headers = {'Authorization': f'Bearer {X_API_BEARER_TOKEN}'}
        url = f'https://api.twitter.com/1.1/trends/place.json?id={location_woeid}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return [trend['name'] for trend in response.json()[0]['trends']]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching X Trends: {e}")
        return None
    except Exception as e:
        print(f"Error processing X Trends response: {e}")  # More specific error
        return None

def get_youtube_trending_titles(region_code="US") -> Optional[List[str]]:
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
    """Analyzes a Telegram channel using the Telethon library.

    Args:
        channel_username (str): The username of the Telegram channel.

    Returns:
        dict:  A dictionary containing channel data, or None on error.  Includes
               'subscribers', 'name', 'description' (or None if not available),
               'success': True/False (indicating if data retrieval was successful).
    """
    try:
        with TelegramClient('anon', API_ID, API_HASH) as client:
            client.start()  # Start the client (no need to log in for public channels)
            try:
                full_channel = client(GetFullChannelRequest(channel_username))
                subscribers = full_channel.full_chat.participants_count
                channel_name = full_channel.chats[0].title
                # Handle cases where about/description might be missing.
                description = full_channel.full_chat.about if full_channel.full_chat.about else None

                return {
                    'subscribers': subscribers,
                    'name': channel_name,
                    'description': description,
                    'success': True
                }
            except ChannelPrivateError:
                print(f"Channel {channel_username} is private.")
                return {'success': False, 'error': 'Channel is private'}
            except ChannelInvalidError:
                print(f"Channel {channel_username} not found.")
                return {'success': False, 'error': 'Channel not found'}
            except ValueError as e:
                if "Cannot find any entity" in str(e):
                     print(f"Channel {channel_username} not found (ValueError).")
                     return {'success': False, 'error': 'Channel not found'}
                else:
                    print(f"ValueError with Telethon: {e}")
                    return {'success': False, 'error': 'Telethon error'}


    except Exception as e:
        print(f"Error analyzing Telegram channel: {e}")
        return {'success': False, 'error': str(e)}


def generate_metadata(username: str, trends: List[str]) -> Dict:  # Changed keyword to username
    """Generates channel metadata suggestions."""
    # Use the provided username if possible, otherwise base it on trends
    name = f"{username or trends[0]} Trends" if trends else "Telegram Channel" # Fallback name
    description = f"Updates and insights about {username or ', '.join(trends[:3])}. #TelegramSEO"
    return {'name': name, 'username': username, 'description': description}


# --- Flask Routes ---

@app.route('/')
def index() -> str:
    """Renders the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze() -> jsonify:
    """Handles the analysis request."""
    channel_username = request.form.get('channel_username')  # Get username, not keyword
    if not channel_username:
        return jsonify({'error': 'Channel username is required'}), 400

    google_trends = get_google_trends() or []
    x_trends = get_x_trends() or []
    youtube_trends = get_youtube_trending_titles() or []
    all_trends = list(set(google_trends + x_trends + youtube_trends))

    telegram_data = analyze_telegram_channel(channel_username)
    if telegram_data and telegram_data['success']:
      telegram_results = {
          'username': channel_username,
          'subscribers': telegram_data['subscribers'],
          'name': telegram_data['name'],
          'description': telegram_data['description']
      }
    else:
      telegram_results = {}


    metadata_suggestions = generate_metadata(channel_username, all_trends)

    return jsonify({
        'google_trends': google_trends,
        'x_trends': x_trends,
        'youtube_trends': youtube_trends,
        'telegram_channel': telegram_results,  # Return data for a *single* channel
        'metadata': metadata_suggestions
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=(os.environ.get("DEBUG_MODE", "False").lower() == "true"), host='0.0.0.0', port=port)
