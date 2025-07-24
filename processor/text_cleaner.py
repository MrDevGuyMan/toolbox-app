# text_cleaner.py
import re
import html
from typing import Optional


def clean_text(text: str, lower: bool = True, remove_links: bool = True) -> str:
    """
    Clean and normalize raw text from social media/news.
    - Unescape HTML
    - Remove tags, emojis, links
    - Normalize whitespace
    """
    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    if remove_links:
        text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Remove emojis and non-text characters
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r"", text)

    # Remove extra whitespace & control characters
    text = re.sub(r"\s+", " ", text).strip()

    if lower:
        text = text.lower()

    return text
