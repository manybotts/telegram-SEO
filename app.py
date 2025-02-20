from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
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

def get_google_trends(region="US") -> Optional[List[str]]:
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

def analyze_telegram_channel(channel_username: str) -> Dict:
    """Analyzes a Telegram channel and returns data or an error."""
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
        return {'success': False, 'error': str(e)}  # ALWAYS return success: False
    except Exception as e:
