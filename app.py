from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

app = Flask(__name__)

# Environment Variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
X_API_BEARER_TOKEN = os.environ.get("X_API_BEARER_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

# --- Helper Functions ---

def get_google_trends_serpapi(region="US") -> Optional[List[str]]:
    """Fetches trending searches from Google Trends using SerpApi."""
    try:
        params = {
            "engine": "google_trends",
            "api_key": SERPAPI_API_KEY,
            "hl": "en",
            "gl": region,
            "cat": "h",
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "daily_searches" in results:
            trends = [item["title"] for item in results["daily_searches"][0]["searches"]]
            return trends
        else:
            print("Error: 'daily_searches' not found in SerpApi response.")
            return None
    except Exception as e:
        print(f"Error fetching Google Trends from SerpApi: {e}")
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
        print(f"Error processing X Trends response: {e}")
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

def search_telegram_channels_serpapi(keyword: str) -> Optional[List[Dict]]:
    """Searches for Telegram channels using SerpApi."""
    try:
        params = {
            "engine": "telegram",
            "api_key": SERPAPI_API_KEY,
            "query": keyword,
            "type": "channels"
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "channels" in results:
            channels = []
            for channel in results["channels"]:
                channels.append({
                    'username': channel.get("username"),
                    'name': channel.get("title"),
                    'subscribers': channel.get("members_count"),
                    'description': channel.get("description"),
                    'rank': channel.get('position')
                })
            return channels
        else:
            print("Error: 'channels' not found in SerpApi response.")
            return None

    except Exception as e:
        print(f"Error fetching Telegram channels from SerpApi: {e}")
        return None

def generate_metadata(keyword: str, trends: List[str]) -> Dict:
    """Generates channel metadata suggestions."""
    name = f"{keyword.title()} Trends"
    username = re.sub(r'[^a-zA-Z0-9_]', '', keyword.lower()) + "_trends"
    username = username[:32]
    description = f"Latest {keyword} trends! {', '.join(trends[:3])} #TelegramSEO"
    return {'name': name, 'username': username, 'description': description}

# --- Flask Routes ---

@app.route('/')
def index() -> str:
    """Renders the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze() -> jsonify:
    """Handles the analysis request."""
    print("Received /analyze request")
    print(f"Request form data: {request.form}")
    keyword = request.form.get('keyword')
    print(f"Keyword: {keyword}")

    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400

    google_trends = get_google_trends_serpapi() or []
    x_trends = get_x_trends() or []
    youtube_trends = get_youtube_trending_titles() or []
    all_trends = list(set(google_trends + x_trends + youtube_trends))

    telegram_results = search_telegram_channels_serpapi(keyword) or []
    metadata_suggestions = generate_metadata(keyword, all_trends)

    return jsonify({
        'google_trends': google_trends,
        'x_trends': x_trends,
        'youtube_trends': youtube_trends,
        'telegram_channels': telegram_results,
        'metadata': metadata_suggestions
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=(os.environ.get("DEBUG_MODE", "False").lower() == "true"), host='0.0.0.0', port=port)
