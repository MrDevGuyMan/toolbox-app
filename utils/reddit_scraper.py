import os
import praw
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
    raise EnvironmentError("Missing Reddit API credentials in .env file.")

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)


def fetch_subreddit_content(subreddit_name: str, post_limit: int = 10, comment_limit: int = 5) -> str:
    """
    Fetches the titles and top-level comments from a subreddit's top weekly posts.
    Returns the data as a single formatted text block.
    """
    try:
        subreddit = reddit.subreddit(subreddit_name)
        content_blocks = []

        for submission in subreddit.top(time_filter='week', limit=post_limit):
            block = f"Title: {submission.title}\n"
            submission.comments.replace_more(limit=0)
            comments = [
                comment.body for comment in submission.comments[:comment_limit]]
            block += "Comments:\n" + "\n".join(comments)
            content_blocks.append(block)

        if not content_blocks:
            raise ValueError("No content returned from subreddit.")

        return "\n\n".join(content_blocks)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch from r/{subreddit_name}: {e}")
