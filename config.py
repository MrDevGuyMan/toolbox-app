# config.py

from dotenv import load_dotenv
import os


def load_config():
    load_dotenv()
    return {
        "ENV": os.getenv("ENV", "development"),

        # Twitter API
        "TWITTER_BEARER_TOKEN": os.getenv("TWITTER_BEARER_TOKEN"),

        # News API
        "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),

        # Reddit API
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
        "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET"),
        "REDDIT_USER_AGENT": os.getenv("REDDIT_USER_AGENT"),

        # YouTube API
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),

        # ProductHunt API (GraphQL)
        "PRODUCTHUNT_API_TOKEN": os.getenv("PRODUCTHUNT_API_TOKEN"),
    }
