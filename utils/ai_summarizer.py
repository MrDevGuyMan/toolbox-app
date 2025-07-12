import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not set in environment variables.")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def summarize_sentiment(text: str) -> str:
    """
    Uses Groq API (LLaMA3-70B) to analyze Reddit content and return a concise mood summary.
    """
    if not text.strip():
        return "No content found to summarize."

    MAX_CHARS = 6000
    text = text[:MAX_CHARS]

    prompt = (
        "You're an AI trained to read Reddit posts and summarize online sentiment.\n"
        "Analyze the tone (optimistic, angry, sad, excited), what topics come up often, "
        "and how users feel overall.\n\n"
        "Write a clear, conversational summary in 3–5 sentences, like you're explaining it to a friend:\n\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You summarize Reddit sentiment for users."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Groq AI summarization failed: {e}"
