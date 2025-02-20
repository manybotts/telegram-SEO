# Telegram Channel Optimizer

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME)

This web application helps Telegram channel owners optimize their channels for better search visibility and ranking within the Telegram ecosystem.  It provides keyword research, competitor analysis, and metadata suggestions.

## Features

*   **Keyword Research:** Integrates with Google Trends, X/Twitter Trends, and YouTube Trends to identify popular keywords.
*   **Content Analysis:** Analyzes top-ranking Telegram channels for a given keyword, extracting data like subscriber count and name.
*   **Metadata Generation:** Suggests optimized channel names, usernames, and descriptions.
*   **API Integrations:** Uses the YouTube Data API, X/Twitter API, and Telegram API.
*   **User-Friendly Interface:**  Provides a clean, easy-to-use web interface.

## Deployment (Heroku - One-Click)

1.  **Click the "Deploy to Heroku" button above.** This will take you to the Heroku deployment page.
2.  **Fill in the required environment variables:**
    *   `TELEGRAM_API_ID`: Your Telegram API ID (integer).  Obtain this from [https://my.telegram.org/](https://my.telegram.org/) (under "API development tools").
    *   `TELEGRAM_API_HASH`: Your Telegram API Hash (string). Obtain this from [https://my.telegram.org/](https://my.telegram.org/) (under "API development tools").
    *   `GOOGLE_API_KEY`:  Your Google API Key (for Google Custom Search).  Get this from the Google Cloud Console ([https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)).  You'll need to enable the "Custom Search API" and create an API key.
    *   `X_API_BEARER_TOKEN`: Your X/Twitter API Bearer Token.  You'll need a developer account and an app on X/Twitter ([https://developer.twitter.com/](https://developer.twitter.com/)).
    *   `YOUTUBE_API_KEY`: Your YouTube Data API Key.  Get this from the Google Cloud Console ([https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)). You'll need to enable the "YouTube Data API v3" and create an API key.
3.  **Click "Deploy app".**  Heroku will build and deploy your application.
4.  **Click "View"** to open your newly deployed app!

## Manual Deployment (Heroku - CLI)

1.  **Create a Heroku Account:**  [https://signup.heroku.com/](https://signup.heroku.com/)
2.  **Install the Heroku CLI:**  [https://devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3.  **Clone this repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git](https://www.google.com/search?q=https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```
4.  **Login to Heroku:**
    ```bash
    heroku login
    ```
5.  **Create a Heroku app:**
    ```bash
    heroku create
    ```
    This will create a new Heroku app and associate it with your local Git repository.  It will also output the URL of your new app.
6.  **Set environment variables:**  You *must* set these environment variables for the app to work.  Use the `heroku config:set` command:
    ```bash
    heroku config:set TELEGRAM_API_ID=your_telegram_api_id
    heroku config:set TELEGRAM_API_HASH=your_telegram_api_hash
    heroku config:set GOOGLE_API_KEY=your_google_api_key
    heroku config:set X_API_BEARER_TOKEN=your_x_api_bearer_token
    heroku config:set YOUTUBE_API_KEY=your_youtube_api_key
    heroku config:set DEBUG_MODE=False  # Important for production!
    ```
    Replace `your_telegram_api_id`, etc., with your *actual* API keys.
7.  **Deploy your code:**
    ```bash
    git push heroku master
    ```
8.  **Open your app:**
    ```bash
    heroku open
    ```

## Local Development

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git](https://www.google.com/search?q=https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file:**  Create a file named `.env` in the project root and add your API keys (see the `.env` section above).
5.  **Run the app:**
    ```bash
    python app.py
    ```
6.  **Open your browser:** Go to `http://127.0.0.1:5000/`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (You should create a LICENSE file).
