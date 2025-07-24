# toolbox_app/routes/trend.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from processor.trend_engine import score_trends
from collectors.social_media import scrape_social_media
from collectors.market_collector import fetch_and_store_crypto_price
from storage.db import init_db, Trend, Post, MarketData
from utils.text_utils import extract_keywords
from processor.ai_summary import generate_summary_and_prediction
from visualizer.plot_trends import generate_trend_charts

router = APIRouter()
templates = Jinja2Templates(directory="templates/tools/trend_analyser")

init_db()


@router.get("/", response_class=HTMLResponse)
async def trend_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def trend_results(request: Request, phrase: str = Form(...)):
    phrase = phrase.strip()
    if not phrase:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Please enter a keyword."
        })

    posts = scrape_social_media(phrase, limit=50)
    all_text = " ".join(p["content"] for p in posts)
    keywords = extract_keywords(all_text, top_n=3)

    keyword_data, all_market_rows = [], []

    for keyword in keywords:
        keyword_posts = scrape_social_media(keyword, limit=10)
        trend_scores = score_trends(keyword_posts)

        if not trend_scores:
            keyword_data.append({
                "keyword": keyword,
                "score": 0,
                "avg_sentiment": 0,
                "count": 0,
                "summary": "⚠️ No posts found or data too weak for analysis."
            })
            continue

        top_score = trend_scores[0]
        trend = Trend.get_or_create_latest(
            keyword=top_score["keyword"],
            count=top_score["count"],
            avg_sentiment=top_score["avg_sentiment"],
            score=top_score["score"]
        )

        for p in keyword_posts:
            if not Post.exists(p["content"]):
                Post.create(
                    trend=trend,
                    source=p["source"],
                    user_id=p["user_id"],
                    date=p["date"],
                    content=p["content"],
                    content_hash=Post.hash_content(p["content"])
                )

        summary = generate_summary_and_prediction(
            top_score["keyword"], keyword_posts)

        keyword_data.append({
            "keyword": top_score["keyword"],
            "score": top_score["score"],
            "avg_sentiment": top_score["avg_sentiment"],
            "count": top_score["count"],
            "summary": summary.get("summary", "No AI summary.")
        })

        symbol = keyword.lower()
        market_rows = MarketData.select().where(
            (MarketData.symbol == symbol) |
            (MarketData.symbol.contains(symbol))
        )

        if not market_rows:
            fetch_and_store_crypto_price(symbol, trend)
            market_rows = MarketData.select().where(MarketData.symbol == symbol)

        for row in market_rows:
            all_market_rows.append({
                "symbol": row.symbol,
                "price": row.price,
                "timestamp": row.timestamp,
                "source": row.source,
                "change": row.change,
                "percent_change": row.percent_change
            })

    charts_list = generate_trend_charts(keyword_data, all_market_rows)
    trend_charts = {
        "score_chart": charts_list[0] if len(charts_list) > 0 else None,
        "sentiment_chart": charts_list[1] if len(charts_list) > 1 else None,
        "market_chart": charts_list[2] if len(charts_list) > 2 else None
    }

    return templates.TemplateResponse("results.html", {
        "request": request,
        "phrase": phrase,
        "keywords": keyword_data,
        "charts": trend_charts
    })
