# 🐦 Twitter Profile Scraper

Python script for fetching and storing data from public Twitter profiles, including user information, recent tweets, and highlighted tweets.

## ✨ Features

- **User Profile Data**: Retrieves comprehensive user profile information such as name, bio, follower count, creation date, and more.
- **Recent Tweets**: Fetches a specified number of the user's most recent tweets, including details like text, creation date, engagement metrics (retweets, likes, replies, quotes), and view counts.
- **Highlighted Tweets**:  Retrieves a specified number of the user's highlighted tweets.
- **Rate Limit Handling**: Implements robust error handling and retry mechanisms with exponential backoff to gracefully manage Twitter API rate limits.
- **Cookie-Based Authentication**: Supports authentication via Twitter cookies to potentially reduce the frequency of full logins.
- **Asynchronous Operations**: Utilizes `asyncio` for efficient and concurrent data fetching.
- **Data Persistence**: Saves the collected data in both JSON and CSV formats for easy analysis and integration.
- **Logging**: Includes comprehensive logging for tracking script execution, errors, and rate limit occurrences.

## 🛠 Requirements

- Python 3.7 or higher
- `twikit` library
- `python-dotenv` library
- `tqdm` library
- `asyncio` library
- `csv` library
- `json` library
- An active Twitter account (for cookie-based authentication)

## 📥 Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/dzhaner01/twitter_profiles_scraper.git
    cd twitter_profiles_scraper
    ```

2. Install the required libraries manually using pip:
    ```bash
    pip install twikit python-dotenv tqdm
    ```

3. **Configuration**:
    - Create a `.env` file in the root directory of the project.
    - Add your Twitter credentials to the `.env` file. You will need either your username/email and password, or your cookie information. For cookie-based authentication, you'll log in once, and the script will save the cookies.

    ```dotenv
    AUTH_INFO_1=YOUR_USERNAME
    AUTH_INFO_2=YOUR_EMAIL
    PASSWORD=YOUR_PASSWORD
    ```
    *(You only need to fill in these values if you're not using cookie-based authentication. After the first successful login, the script will save cookies to `cookies.json`.)*

    - Create a `usernames.txt` file in the root directory. Each line should contain the Twitter screen name (handle) of a user you want to scrape data from.

    ```plaintext
    elonmusk
    realDonaldTrump
    ```

## 🚀 Usage

1. Ensure you have followed the installation steps and configured the `.env` and `usernames.txt` files.
2. Run the script:
    ```bash
    python twitter_profiles_scraper.py
    ```

## 📋 Output

The script will generate the following output files in the same directory:

- **`twitter_scraper.log`**: Contains detailed logs of the script's execution, including successful fetches, errors, and rate limit warnings.
- **`cookies.json`**: Stores your Twitter authentication cookies after a successful login (if applicable). This allows for faster subsequent runs without needing to re-enter credentials.
- **`twitter_profiles_data.json`**: A JSON file containing a list of dictionaries. Each dictionary represents a scraped user and includes their profile details, recent tweets, and highlighted tweets.
    ```json
    {
        "users": [
            {
                "id": "...",
                "name": "...",
                "screen_name": "...",
                // ... other user profile fields
            },
            // ... more users
        ],
        "tweets": [
            {
                "tweet_id": "...",
                "user_id": "...",
                "text": "...",
                // ... other tweet fields
            },
            // ... more tweets
        ],
        "highlight_tweets": [
            {
                "tweet_id": "...",
                "user_id": "...",
                "text": "...",
                // ... other highlight tweet fields
            },
            // ... more highlight tweets
        ]
    }
    ```
- **`users.csv`**: A CSV file containing the user profile data.
    ```csv
    id,name,screen_name,...
    "...", "...", "...",...
    "...", "...", "...",...
    ```
- **`tweets.csv`**: A CSV file containing the recent tweets data.
    ```csv
    tweet_id,user_id,text,created_at,...
    "...", "...", "...", "...",...
    "...", "...", "...", "...",...
    ```
- **`highlight_tweets.csv`**: A CSV file containing the highlighted tweets data.
    ```csv
    tweet_id,user_id,text,created_at,...
    "...", "...", "...", "...",...
    "...", "...", "...", "...",...
    ```

## 💡 Notes

- The script handles potential `TooManyRequests` errors from the Twitter API by implementing a retry mechanism with exponential backoff.
- You can adjust the `TWEET_LIMIT` and `HIGHLIGHT_TWEET_LIMIT` constants in the script to fetch more or fewer tweets.
- For scraping a large number of users, consider the Twitter API rate limits and adjust the sleep times (`SLEEP_BETWEEN_USERS_MIN`, `SLEEP_BETWEEN_USERS_MAX`) accordingly.
- It's recommended to use cookie-based authentication after the initial login to potentially reduce the chance of being flagged for excessive login attempts.
- This script is intended for educational and research purposes only. Please adhere to Twitter's terms of service and API usage guidelines.