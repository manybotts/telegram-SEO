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
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID")) if os.environ.get("TELEGRAM_API_ID") else None
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
    """Fetches trends from X using the v2 API."""
    try:
        headers = {'Authorization': f'Bearer {X_API_BEARER_TOKEN}'}
        # Use the v2 endpoint for getting trending topics by WOEID
        url = f'https://api.twitter.com/2/trends/available'  # Changed to v2 endpoint


        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response_json = response.json()
        trends_available = []
        for locations in response_json:
          if locations['woeid'] == location_woeid:
            place_name = locations['name']
            parent_id = locations['parentid']

        url_trends_location = f'https://api.twitter.com/1.1/trends/place.json?id={location_woeid}'
        response = requests.get(url_trends_location, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response_location_json = response.json()
        trends = [trend['name'] for trend in response_location_json[0]['trends']]
        return trends


    except requests.exceptions.RequestException as e:
        print(f"Error fetching X Trends: {e}")
        return None
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error processing X Trends response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error with X API: {e}")
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
    """Analyzes a Telegram channel using the Telethon library."""
    try:
        # Use the globals, but with extra checks
        api_id = int(os.environ.get("TELEGRAM_API_ID")) if os.environ.get("TELEGRAM_API_ID") else None
        api_hash = os.environ.get("TELEGRAM_API_HASH")

        if not api_id or not api_hash:
            print("Error: TELEGRAM_API_ID or TELEGRAM_API_HASH not set.")
            return {'success': False, 'error': 'Telegram API credentials not configured.'}

        with TelegramClient('anon', api_id, api_hash) as client:
            client.start()
            try:
                full_channel = client(GetFullChannelRequest(channel_username))
                subscribers = full_channel.full_chat.participants_count
                channel_name = full_channel.chats[0].title
                description = full_channel.full_chat.about if full_channel.full_chat.about else None

                return {
                    'subscribers': subscribers,
                    'name': channel_name,
                    'description': description,
                    'success': True
                }
            except (ChannelPrivateError, ChannelInvalidError, ValueError) as e:
                error_message = str(e)
                if isinstance(e, ChannelPrivateError):
                    error_message = "This channel is private."
                elif isinstance(e, ChannelInvalidError):
                    error_message = "Channel not found."
                elif "Cannot find any entity" in error_message:
                    error_message = "Channel not found."
                print(f"Telegram channel analysis error: {error_message}")  # Log the error
                return {'success': False, 'error': error_message}
            except Exception as e:
                print(f"Unexpected error analyzing Telegram channel: {e}")
                return {'success': False, 'error': 'An unexpected error occurred.'}

    except Exception as e:
        print(f"Error initializing Telegram client: {e}")
        return {'success': False, 'error': 'Failed to connect to Telegram. Check your API ID and Hash.'}



def generate_metadata(username: str, trends: List[str]) -> Dict:
    """Generates channel metadata suggestions."""
    name = f"{username or (trends[0] if trends else 'Telegram')} Trends"
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
    telegram_results = {}  # Initialize as empty
    if telegram_data and telegram_data['success']:
        telegram_results = {
            'username': channel_username,
            'subscribers': telegram_data['subscribers'],
            'name': telegram_data['name'],
            'description': telegram_data['description']
        }
    # No else:  We'll handle the error in the JavaScript

    metadata_suggestions = generate_metadata(channel_username, all_trends)

    return jsonify({
        'google_trends': google_trends,
        'x_trends': x_trends,
        'youtube_trends': youtube_trends,
        'telegram_channel': telegram_results,  # Always return, even if empty
        'telegram_error': telegram_data.get('error') if telegram_data and not telegram_data['success'] else None, # Pass error
        'metadata': metadata_suggestions
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=(os.environ.get("DEBUG_MODE", "False").lower() == "true"), host='0.0.0.0', port=port)
