# news.py
import feedparser
import requests
from datetime import datetime
from config import load_config

config = load_config()
NEWS_API_KEY = config.get("NEWS_API_KEY")


def scrape_rss_news(query: str, limit: int = 5):
    """
    Fetch news articles via RSS from Google News.
    """
    encoded_query = query.replace(" ", "+")
    feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"

    feed = feedparser.parse(feed_url)
    entries = feed.entries[:limit]

    results = []
    for entry in entries:
        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
        })

    return results


def fetch_news_api(query: str, limit: int = 5):
    """
    Fetch news using the NewsAPI (https://newsapi.org).
    Requires NEWS_API_KEY in .env.
    """
    if not NEWS_API_KEY:
        print("⚠️ Missing NEWS_API_KEY. Skipping News API.")
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": limit,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except Exception as e:
        print(f"⚠️ News API error: {e}")
        return []

    return [
        {
            "title": a["title"],
            "source": a["source"]["name"],
            "url": a["url"],
            "publishedAt": a["publishedAt"]
        }
        for a in articles
    ]
