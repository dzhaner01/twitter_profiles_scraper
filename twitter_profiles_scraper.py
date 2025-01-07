import asyncio
import json
import os
import logging
import time
import random
from tqdm import tqdm
from datetime import timedelta
import csv

from twikit import Client
from dotenv import load_dotenv
from twikit.errors import Unauthorized, AccountSuspended, TooManyRequests, UserNotFound, UserUnavailable, BadRequest, TwitterException

# Load environment variables from a .env file
load_dotenv()

# Configuration Constants
MAX_RETRIES = 5
INITIAL_WAIT_TIME = 60  # seconds
SLEEP_BETWEEN_USERS_MIN = 15
SLEEP_BETWEEN_USERS_MAX = 30
TWEET_LIMIT = 200
HIGHLIGHT_TWEET_LIMIT = 200
FETCH_COUNT = 200
COOKIES_FILE = 'cookies.json'
OUTPUT_FILE = 'twitter_profiles_data.json'
USERS_CSV_FILE = 'users.csv'
TWEETS_CSV_FILE = 'tweets.csv'
HIGHLIGHT_TWEETS_CSV_FILE = 'highlight_tweets.csv'
BACKOFF_FACTOR = 2.5

# Configure logging
# File Logger
logging.basicConfig(filename='twitter_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Console logger
console_logger = logging.getLogger('console_logger')
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
console_logger.addHandler(console_handler)

# Initialize client
client = Client('en-US')

async def login_and_load_cookies():
    try:
        if os.path.exists(COOKIES_FILE):
            client.load_cookies(COOKIES_FILE)
            logging.info("Loaded cookies from file.")
        else:
            await client.login(auth_info_1=os.getenv('AUTH_INFO_1'), auth_info_2=os.getenv('AUTH_INFO_2'), password=os.getenv('PASSWORD'))
            client.save_cookies(COOKIES_FILE)
            logging.info("Logged in and saved cookies to file.")
    except Unauthorized:
        logging.error("Failed to authenticate. Please check your credentials or cookies.")
        return False
    except TwitterException as e:
        logging.error(f"An error occurred during login: {e}")
        return False
    return True

async def fetch_user_profile(username):
    try:
        user_profile = await client.get_user_by_screen_name(username)
        return user_profile
    except (UserNotFound, UserUnavailable, BadRequest, AccountSuspended) as e:
        logging.error(f"User: {username} - Error fetching user profile: {e}")
        return None
    except TwitterException as e:
        logging.error(f"User: {username} - An unexpected error occurred while fetching user: {e}")
        return None

async def fetch_tweets_with_cursor(user_id, tweet_type, limit):
    """Fetches tweets using cursor-based pagination."""
    all_tweets = []
    cursor = None
    retries = 0
    wait_time = INITIAL_WAIT_TIME
    while len(all_tweets) < limit and retries < MAX_RETRIES:
        try:
            # Use client.get_user_tweets with the user_id
            result = await client.get_user_tweets(user_id=user_id, tweet_type=tweet_type, count=min(FETCH_COUNT, limit - len(all_tweets)), cursor=cursor)
            if not result:
                break
            for tweet in result:
                all_tweets.append({
                    'tweet_id': tweet.id,
                    'user_id': user_id,
                    'text': tweet.full_text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.retweet_count,
                    'favorite_count': tweet.favorite_count,
                    'reply_count': tweet.reply_count,
                    'quote_count': tweet.quote_count,
                    'view_count': tweet.view_count,
                    'view_count_state': tweet.view_count_state,
                    'lang': tweet.lang,
                    'is_quote_status': tweet.is_quote_status,
                    'possibly_sensitive': tweet.possibly_sensitive,
                    'is_edit_eligible': tweet.is_edit_eligible,
                    'edits_remaining': tweet.edits_remaining
                })
                if len(all_tweets) >= limit:
                    break
            if len(all_tweets) >= limit:
                break
            cursor = result.next_cursor
            if not cursor:
              break
            retries = 0 # reset retries if successful
            wait_time = INITIAL_WAIT_TIME # reset the wait time
            await asyncio.sleep(random.uniform(1,3))  # Add a small delay between each API call
        except TooManyRequests:
            logging.warning(f"User ID: {user_id} - Rate limit exceeded when fetching tweets. Retrying in {wait_time} seconds... {retries + 1} retries done")
            retries += 1
            try:
                await asyncio.wait_for(asyncio.sleep(wait_time), timeout=wait_time + 10)
            except asyncio.TimeoutError:
                logging.error("asyncio.sleep() timed out!")
            wait_time = wait_time * BACKOFF_FACTOR + random.uniform(-5, 5)
        except TwitterException as e:
            logging.error(f"User ID: {user_id} - Error fetching tweets: {e}")
            break

    return all_tweets

async def fetch_highlight_tweets_with_cursor(user_id, limit):
    """Fetches highlight tweets using cursor-based pagination."""
    all_tweets = []
    cursor = None
    retries = 0
    wait_time = INITIAL_WAIT_TIME
    while len(all_tweets) < limit and retries < MAX_RETRIES:
        try:
            # Use client.get_user_highlights_tweets with the user_id
            result = await client.get_user_highlights_tweets(user_id=user_id, count=min(FETCH_COUNT, limit - len(all_tweets)), cursor=cursor)
            if not result:
              break
            for tweet in result:
                all_tweets.append({
                    'tweet_id': tweet.id,
                    'user_id': user_id,
                    'text': tweet.full_text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.retweet_count,
                    'favorite_count': tweet.favorite_count,
                    'reply_count': tweet.reply_count,
                    'quote_count': tweet.quote_count,
                    'view_count': tweet.view_count,
                    'view_count_state': tweet.view_count_state,
                    'lang': tweet.lang,
                    'is_quote_status': tweet.is_quote_status,
                    'possibly_sensitive': tweet.possibly_sensitive,
                    'is_edit_eligible': tweet.is_edit_eligible,
                    'edits_remaining': tweet.edits_remaining
                })
                if len(all_tweets) >= limit:
                    break
            if len(all_tweets) >= limit:
                break
            cursor = result.next_cursor
            if not cursor:
               break
            retries = 0 # reset retries if successful
            wait_time = INITIAL_WAIT_TIME
            await asyncio.sleep(random.uniform(1,3))  # Add a small delay between each API call
        except TooManyRequests:
            logging.warning(f"User ID: {user_id} - Rate limit exceeded when fetching highlight tweets. Retrying in {wait_time} seconds... {retries + 1} retries done")
            retries += 1
            try:
                await asyncio.wait_for(asyncio.sleep(wait_time), timeout=wait_time + 10)
            except asyncio.TimeoutError:
                logging.error("asyncio.sleep() timed out!")
            wait_time = wait_time * BACKOFF_FACTOR + random.uniform(-5, 5)
        except TwitterException as e:
            logging.error(f"User ID: {user_id} - Error fetching highlight tweets: {e}")
            break

    return all_tweets

async def fetch_tweet_data(user_id, tweet_type, limit):
    """Fetches tweet data for a given user profile."""
    all_tweets = await fetch_tweets_with_cursor(user_id, tweet_type, limit)
    return all_tweets

async def fetch_highlight_tweet_data(user_id, limit):
    """Fetches highlight tweets for a given user profile."""
    all_tweets = await fetch_highlight_tweets_with_cursor(user_id, limit)
    return all_tweets

async def fetch_user_details_data(user_profile):
    """Fetches detailed information about a user."""
    try:
        return {
            'id': getattr(user_profile, 'id', 'N/A'),
            'name': getattr(user_profile, 'name', 'N/A'),
            'screen_name': getattr(user_profile, 'screen_name', 'N/A'),
            'created_at': getattr(user_profile, 'created_at', 'N/A'),
            'description': getattr(user_profile, 'description', 'N/A'),
            'location': getattr(user_profile, 'location', 'N/A'),
            'url': getattr(user_profile, 'url', 'N/A'),
            'profile_image_url': getattr(user_profile, 'profile_image_url', 'N/A'),
            'protected': getattr(user_profile, 'protected', 'N/A'),
            'is_blue_verified': getattr(user_profile, 'is_blue_verified', 'N/A'),
            'followers_count': getattr(user_profile, 'followers_count', 'N/A'),
            'statuses_count': getattr(user_profile, 'statuses_count', 'N/A'),
            'listed_count': getattr(user_profile, 'listed_count', 'N/A'),
            'profile_banner_url': getattr(user_profile, 'profile_banner_url', 'N/A'),
            'description_urls': getattr(user_profile, 'description_urls', 'N/A'),
            'urls': getattr(user_profile, 'urls', 'N/A'),
            'pinned_tweet_ids': getattr(user_profile, 'pinned_tweet_ids', 'N/A'),
            'verified': getattr(user_profile, 'verified', 'N/A'),
            'possibly_sensitive': getattr(user_profile, 'possibly_sensitive', 'N/A'),
            'can_dm': getattr(user_profile, 'can_dm', 'N/A'),
            'can_media_tag': getattr(user_profile, 'can_media_tag', 'N/A'),
            'want_retweets': getattr(user_profile, 'want_retweets', 'N/A'),
            'default_profile': getattr(user_profile, 'default_profile', 'N/A'),
            'default_profile_image': getattr(user_profile, 'default_profile_image', 'N/A'),
            'has_custom_timelines': getattr(user_profile, 'has_custom_timelines', 'N/A'),
            'fast_followers_count': getattr(user_profile, 'fast_followers_count', 'N/A'),
            'normal_followers_count': getattr(user_profile, 'normal_followers_count', 'N/A'),
            'favourites_count': getattr(user_profile, 'favourites_count', 'N/A'),
            'media_count': getattr(user_profile, 'media_count', 'N/A'),
            'is_translator': getattr(user_profile, 'is_translator', 'N/A'),
            'translator_type': getattr(user_profile, 'translator_type', 'N/A'),
            'profile_interstitial_type': getattr(user_profile, 'profile_interstitial_type', 'N/A'),
            'withheld_in_countries': getattr(user_profile, 'withheld_in_countries', 'N/A'),
        }
    except Exception as e:
        logging.error(f"Error fetching details for {user_profile.screen_name}: {e}")
        return {}

async def fetch_user_data(username):
    logging.info(f"Fetching data for user: {username}")
    user_profile = await fetch_user_profile(username)
    if not user_profile:
        return None

    user_details = await fetch_user_details_data(user_profile)
    tweets = await fetch_tweet_data(user_profile.id, 'Tweets', TWEET_LIMIT)
    highlight_tweets = await fetch_highlight_tweet_data(user_profile.id, HIGHLIGHT_TWEET_LIMIT)

    return user_details, tweets, highlight_tweets

def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def write_data_to_csv(filepath, data, header):
    """Writes data to a CSV file.

    Args:
        filepath: The path to the CSV file.
        data: A list of dictionaries (each dictionary representing a row).
        header: A list of keys to be used as the header row.
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)  # Use DictWriter
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        print(f"Error writing to CSV {filepath}: {e}")

def create_csvs_from_json(json_file, users_csv, tweets_csv, highlight_tweets_csv):
    """Creates users, tweets, and highlight_tweets CSV files from a JSON file.

    Args:
        json_file: Path to the input JSON file.
        users_csv: Path to the output users CSV file.
        tweets_csv: Path to the output tweets CSV file.
        highlight_tweets_csv: Path to the output highlight tweets CSV file.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data['users']:
            write_data_to_csv(users_csv, data['users'], list(data['users'][0].keys()))
        if data['tweets']:
            write_data_to_csv(tweets_csv, data['tweets'], list(data['tweets'][0].keys()))
        if data['highlight_tweets']:
            write_data_to_csv(highlight_tweets_csv, data['highlight_tweets'], list(data['highlight_tweets'][0].keys()))

    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
    except KeyError as e:
        print(f"Error: Missing key in JSON data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def main():
    console_logger.info("Starting Twitter data fetching script...")
    try:
        console_logger.info("Attempting login...")
        if not await login_and_load_cookies():
            console_logger.error("Login failed, exiting.")
            return
        console_logger.info("Login successful.")

        usernames = []
        try:
            with open('usernames.txt', 'r') as f:
                usernames = [line.strip() for line in f]
        except FileNotFoundError:
            logging.error("Usernames file 'usernames.txt' not found.")
            return

        all_data = {"users": [], "tweets": [], "highlight_tweets": []}

        with tqdm(usernames, desc="Fetching data", unit="user", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}  [{elapsed} taken, {remaining} remaining]') as progress_bar:
            for username in progress_bar:
                retries = 0
                wait_time = INITIAL_WAIT_TIME
                while retries < MAX_RETRIES:
                    try:
                        user_data, tweets_data, highlight_tweets_data = await fetch_user_data(username)
                        if user_data:
                            all_data["users"].append(user_data)
                            all_data["tweets"].extend(tweets_data)
                            all_data["highlight_tweets"].extend(highlight_tweets_data)
                        break  # Successfully fetched, so break retry loop
                    except TooManyRequests:
                        progress_bar.set_description(f"Rate limited: {username}")
                        logging.warning(f"User: {username} - TooManyRequests error. Retrying in {wait_time} seconds... {retries + 1} retries done")
                        retries += 1
                        try:
                            await asyncio.wait_for(asyncio.sleep(wait_time), timeout=wait_time + 10)
                        except asyncio.TimeoutError:
                            logging.error("asyncio.sleep() timed out!")
                        wait_time = wait_time * BACKOFF_FACTOR + random.uniform(-5, 5)
                    except Exception as e:
                        progress_bar.set_description(f"Error: {username}")
                        logging.error(f"User: {username} - An unexpected error occurred while fetching data: {e}")
                        break  # Break retry loop for other exceptions

                await asyncio.sleep(random.uniform(SLEEP_BETWEEN_USERS_MIN, SLEEP_BETWEEN_USERS_MAX))

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            json.dump(all_data, outfile, indent=4, ensure_ascii=False)
        console_logger.info(f"Data fetching complete. Output saved to '{OUTPUT_FILE}'.")

        # Convert JSON to CSV after successful JSON creation
        create_csvs_from_json(OUTPUT_FILE, USERS_CSV_FILE, TWEETS_CSV_FILE, HIGHLIGHT_TWEETS_CSV_FILE)
        console_logger.info(f"Data converted to CSV format. Users saved to '{USERS_CSV_FILE}', Tweets to '{TWEETS_CSV_FILE}', and Highlight Tweets to '{HIGHLIGHT_TWEETS_CSV_FILE}'.")

    except KeyboardInterrupt:
        console_logger.info("Script interrupted by user.")
    except asyncio.exceptions.CancelledError:
        console_logger.info("Script Cancelled by user")
    finally:
        console_logger.info("Exiting the script...")

if __name__ == "__main__":
    asyncio.run(main())