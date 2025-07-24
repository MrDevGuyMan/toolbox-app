# visualizer/plot_trends.py
import io
import base64
import matplotlib.pyplot as plt
import pandas as pd
from storage.db import Trend, MarketData


def fig_to_base64(fig):
    """Convert a Matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_trend_charts(trend_data: list[dict], market_data: list[dict] = None):
    """
    Generate charts for trends (and optionally market data).
    Returns list of base64 image strings.
    """
    images = []

    if not trend_data:
        return images

    df = pd.DataFrame(trend_data)

    # --- Chart 1: Trend Score Bar Chart ---
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(df["keyword"], df["score"])
    ax1.set_title("Top Trend Scores")
    ax1.set_ylabel("Score")
    ax1.set_xlabel("Keyword")
    images.append(fig_to_base64(fig1))
    plt.close(fig1)

    # --- Chart 2: Sentiment vs Frequency ---
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.scatter(df["count"], df["avg_sentiment"])
    for _, row in df.iterrows():
        ax2.text(row["count"], row["avg_sentiment"], row["keyword"])
    ax2.set_title("💬 Sentiment vs Post Frequency")
    ax2.set_xlabel("Post Count")
    ax2.set_ylabel("Avg. Sentiment")
    ax2.grid(True)
    images.append(fig_to_base64(fig2))
    plt.close(fig2)

    # --- Chart 3: Optional Market Price Over Time ---
    if market_data:
        dfm = pd.DataFrame(market_data)
        dfm.sort_values("timestamp", inplace=True)
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.plot(dfm["timestamp"], dfm["price"], marker="o")
        ax3.set_title(
            f"💹 Market Price Over Time: {dfm['symbol'].iloc[0].upper()}")
        ax3.set_ylabel("Price ($)")
        ax3.set_xlabel("Time")
        fig3.autofmt_xdate()
        images.append(fig_to_base64(fig3))
        plt.close(fig3)

    return images
