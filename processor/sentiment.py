# sentiment.py
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Ensure VADER lexicon is downloaded
try:
    nltk.data.find("sentiment/vader_lexicon")
except LookupError:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> dict:
    """
    Run VADER sentiment analysis and return:
    {
        'neg': ..., 'neu': ..., 'pos': ..., 'compound': ...
    }
    """
    return sia.polarity_scores(text)


def get_sentiment_label(score: float) -> str:
    """
    Convert compound score to label: negative, neutral, positive
    """
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    return "neutral"
