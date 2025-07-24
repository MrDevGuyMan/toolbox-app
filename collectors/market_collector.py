# market_collector.py
import requests
from datetime import datetime
from storage.db import MarketData, Trend
from storage.symbol_table import resolve_crypto_name, resolve_stock_name


def fetch_and_store_crypto_price(ticker: str, trend: Trend | None = None):
    """
    Fetch current price of a crypto asset and store it in MarketData, linked to the trend if provided.
    """
    coin_id = resolve_crypto_name(ticker)
    if not coin_id:
        print(f"⚠️ Unknown crypto ticker: {ticker}")
        return

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        price = data[coin_id]["usd"]
    except Exception as e:
        print(f"⚠️ Failed to fetch price for {ticker}: {e}")
        return

    MarketData.create(
        trend=trend,
        symbol=ticker.lower(),
        price=price,
        timestamp=datetime.utcnow(),
        source="coingecko",
        change=0.0,
        percent_change=0.0
    )
    print(
        f"✅ Stored {ticker} price: ${price} (linked to trend ID: {trend.id if trend else 'none'})")
