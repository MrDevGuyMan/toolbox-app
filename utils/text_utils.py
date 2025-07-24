# utils/text_utils.py
from collections import Counter
import re

STOPWORDS = set([
    # Basic grammar and filler
    "the", "a", "an", "and", "or", "in", "on", "for", "of", "to", "by", "at", "from", "with",
    "as", "is", "are", "was", "were", "be", "been", "am", "that", "this", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "our", "their", "mine", "yours", "ours", "theirs", "its",
    "do", "does", "did", "have", "has", "had", "will", "would", "should", "can", "could", "may", "might", "must",
    "just", "not", "no", "yes", "if", "then", "than", "because", "about", "but", "so", "up", "out", "into", "how", "what", "when", "where", "why",
    "now",

    # Web garbage
    "https", "http", "www", "com", "net", "org", "rt", "t", "amp", "quot",

    # Contractions and variants
    "it's", "i'm", "you're", "he's", "she's", "we're", "they're", "i've", "you've", "we've", "they've",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll", "don't", "doesn't", "didn't", "can't", "couldn't",
    "won't", "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't", "hadn't",

    # Custom additions based on noise
    "gt", "use", "get", "see", "go", "make", "know", "want", "need", "like",
])


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """
    Extracts top N clean, non-junk keywords based on frequency.
    """
    # Normalize and split into words, only keep alpha
    text = text.lower()
    text = re.sub(r"[’']", "", text)  # Remove apostrophes from contractions
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)  # Only words of length >=3

    # Filter stopwords
    filtered = [w for w in words if w not in STOPWORDS]

    counts = Counter(filtered)
    keywords = []
    for word, _ in counts.most_common():
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= top_n:
            break

    return keywords
