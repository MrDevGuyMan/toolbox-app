# ai_summary.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


def generate_summary_and_prediction(keyword: str, posts: list[dict]) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("Missing GROQ_API_KEY in .env")

    content = "\n".join(
        f"- {p['content']}" for p in posts[:20]) or "No content available."
    prompt = f"""
You are an expert trend analyst.

Given the following posts mentioning the keyword "{keyword}", generate:

1. A short 3-4 sentence **summary** of what people are saying.
2. A **prediction** about the trend's short-term direction (e.g. gaining interest, fading out, controversial).

Be concise and insightful.

Posts:
{content}
"""

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system",
                "content": "You are a helpful AI summarizer and trend predictor."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            GROQ_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        return {"keyword": keyword, "summary": answer.strip()}
    except Exception as e:
        return {"keyword": keyword, "summary": f"⚠️ AI error: {e}"}
