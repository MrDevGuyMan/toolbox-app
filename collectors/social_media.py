# social_media.py

import tweepy
import re
import praw
import requests
from googleapiclient.discovery import build
from config import load_config

config = load_config()


def scrape_tweets(keyword: str, limit: int = 10):
    bearer_token = config["TWITTER_BEARER_TOKEN"]
    if not bearer_token:
        raise ValueError("Missing TWITTER_BEARER_TOKEN in environment")

    client = tweepy.Client(bearer_token=bearer_token)

    try:
        response = client.search_recent_tweets(
            query=keyword,
            max_results=max(10, min(limit, 100)),
            tweet_fields=["created_at", "author_id", "text"]
        )
    except tweepy.TooManyRequests:
        print("⚠️ Rate limited. Skipping Twitter scrape.")
        return []
    except Exception as e:
        print(f"⚠️ Twitter API error: {e}")
        return []

    tweets = []
    for tweet in response.data or []:
        content = re.sub(r"http\S+", "", tweet.text).replace("\n", " ").strip()
        tweets.append({
            "source": "twitter",
            "user_id": tweet.author_id,
            "date": tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content
        })

    return tweets


def scrape_reddit_posts(keyword: str, limit: int = 10):
    reddit = praw.Reddit(
        client_id=config.get("REDDIT_CLIENT_ID"),
        client_secret=config.get("REDDIT_CLIENT_SECRET"),
        user_agent=config.get("REDDIT_USER_AGENT") or "trend_analyser_app"
    )

    try:
        posts = reddit.subreddit("all").search(
            keyword, sort="new", limit=limit)
    except Exception as e:
        print(f"⚠️ Reddit API error: {e}")
        return []

    results = []
    for post in posts:
        results.append({
            "source": "reddit",
            "user_id": post.author.name if post.author else "[deleted]",
            "date": post.created_utc,
            "content": post.title
        })

    return results


def scrape_4chan_posts(keyword: str, limit: int = 10, board: str = "biz"):
    url = f"https://a.4cdn.org/{board}/catalog.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        catalog = response.json()
    except Exception as e:
        print(f"⚠️ 4chan error fetching catalog: {e}")
        return []

    posts = []
    for page in catalog:
        for thread in page.get("threads", []):
            thread_id = thread.get("no")
            thread_url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
            try:
                thread_resp = requests.get(thread_url, timeout=10)
                thread_resp.raise_for_status()
                thread_data = thread_resp.json()
            except Exception:
                continue

            for post in thread_data.get("posts", []):
                content = post.get("com", "")
                if keyword.lower() in content.lower():
                    clean_text = re.sub(r"<[^>]+>", "", content).strip()
                    posts.append({
                        "source": "4chan",
                        "user_id": f"anon-{post.get('no')}",
                        "date": post.get("time"),
                        "content": clean_text
                    })
                    if len(posts) >= limit:
                        return posts
    return posts


def scrape_hacker_news(keyword: str, limit: int = 10):
    url = f"https://hn.algolia.com/api/v1/search?query={keyword}&tags=story"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Hacker News error: {e}")
        return []

    results = []
    for hit in data.get("hits", [])[:limit]:
        results.append({
            "source": "hackernews",
            "user_id": hit.get("author", "[unknown]"),
            "date": hit.get("created_at", ""),
            "content": hit.get("title", "")
        })
    return results


def scrape_youtube_videos(keyword: str, limit: int = 10):
    api_key = config.get("YOUTUBE_API_KEY")
    if not api_key:
        print("⚠️ Missing YOUTUBE_API_KEY in environment")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        search_response = youtube.search().list(
            q=keyword,
            part="snippet",
            type="video",
            maxResults=limit
        ).execute()
    except Exception as e:
        print(f"⚠️ YouTube API error: {e}")
        return []

    results = []
    for item in search_response.get("items", []):
        snippet = item["snippet"]
        results.append({
            "source": "youtube",
            "user_id": snippet.get("channelTitle", "[unknown]"),
            "date": snippet.get("publishedAt", ""),
            "content": snippet.get("title", "")
        })
    return results


def scrape_stackoverflow(keyword: str, limit: int = 10):
    url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=creation&q={keyword}&site=stackoverflow"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ StackOverflow API error: {e}")
        return []

    results = []
    for item in data.get("items", [])[:limit]:
        results.append({
            "source": "stackoverflow",
            "user_id": item.get("owner", {}).get("display_name", "[unknown]"),
            "date": item.get("creation_date", 0),
            "content": item.get("title", "")
        })
    return results


def scrape_mastodon(keyword: str, limit: int = 10):
    url = f"https://mastodon.social/api/v2/search?q={keyword}&type=statuses&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Mastodon API error: {e}")
        return []

    results = []
    for status in data.get("statuses", []):
        results.append({
            "source": "mastodon",
            "user_id": status.get("account", {}).get("username", "[unknown]"),
            "date": status.get("created_at", ""),
            "content": re.sub(r"<[^>]+>", "", status.get("content", "")).strip()
        })
    return results


def scrape_medium(keyword: str, limit: int = 10):
    url = f"https://medium.com/feed/tag/{keyword}"
    try:
        import feedparser
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"⚠️ Medium RSS error: {e}")
        return []

    results = []
    for entry in feed.entries[:limit]:
        results.append({
            "source": "medium",
            "user_id": entry.get("author", "[unknown]"),
            "date": entry.get("published", ""),
            "content": entry.get("title", "")
        })
    return results


def scrape_producthunt(keyword: str, limit: int = 10):
    token = config.get("PRODUCTHUNT_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    query = """{
      posts(first: 20, order: VOTES) {
        edges {
          node {
            name
            tagline
            createdAt
            user {
              name
            }
          }
        }
      }
    }"""

    try:
        response = requests.post(
            "https://api.producthunt.com/v2/api/graphql", json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ ProductHunt API error: {e}")
        return []

    results = []
    for edge in data.get("data", {}).get("posts", {}).get("edges", []):
        node = edge.get("node", {})
        if keyword.lower() in (node.get("name", "") + node.get("tagline", "")).lower():
            results.append({
                "source": "producthunt",
                "user_id": node.get("user", {}).get("name", "[unknown]"),
                "date": node.get("createdAt", ""),
                "content": node.get("name", "") + " - " + node.get("tagline", "")
            })
            if len(results) >= limit:
                break
    return results


def scrape_social_media(keyword: str, limit: int = 10):
    all_data = []
    sources = [
        ("twitter", scrape_tweets),
        ("reddit", scrape_reddit_posts),
        ("4chan", scrape_4chan_posts),
        ("hackernews", scrape_hacker_news),
        ("youtube", scrape_youtube_videos),
        ("stackoverflow", scrape_stackoverflow),
        ("mastodon", scrape_mastodon),
        ("medium", scrape_medium),
        ("producthunt", scrape_producthunt)
    ]

    for name, func in sources:
        try:
            print(f"🔍 Scraping {name}...")
            data = func(keyword, limit)
            all_data.extend(data)
        except Exception as e:
            print(f"⚠️ Failed to scrape {name}: {e}")

    print(f"✅ Total collected from all sources: {len(all_data)}")
    return all_data
