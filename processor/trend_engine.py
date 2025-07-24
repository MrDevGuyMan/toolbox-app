# trend_engine.py
from collections import defaultdict
from processor.sentiment import analyze_sentiment
from processor.text_cleaner import clean_text
from utils.text_utils import STOPWORDS  # ⬅️ Add this import


def score_trends(posts: list[dict]) -> list[dict]:
    keyword_map = defaultdict(list)

    for post in posts:
        content = clean_text(post["content"])
        for word in content.split():
            if word in STOPWORDS:  # ⬅️ Skip unwanted words
                continue
            keyword_map[word].append(content)

    scored = []

    for keyword, texts in keyword_map.items():
        sentiments = [analyze_sentiment(t)["compound"] for t in texts]
        avg_sent = sum(sentiments) / len(sentiments)
        freq = len(texts)

        score = freq * (0.5 + avg_sent)

        scored.append({
            "keyword": keyword,
            "count": freq,
            "avg_sentiment": round(avg_sent, 3),
            "score": round(score, 3)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
