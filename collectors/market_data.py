# market_data.py

import requests
import yfinance as yf
from functools import lru_cache


# --- Crypto ---
def get_crypto_price(coin_id: str, currency: str = "usd"):
    """
    Fetch current price and 24h change of a cryptocurrency from CoinGecko.
    """
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies={currency}&include_24hr_change=true"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"CoinGecko API error: {response.status_code}")

    data = response.json().get(coin_id, {})
    return {
        "symbol": coin_id,
        "price": data.get(currency),
        "change_24h": data.get(f"{currency}_24h_change")
    }


# --- Stocks ---
def get_stock_price(ticker: str):
    """
    Fetch latest stock price and percent change using Yahoo Finance.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    if hist.empty:
        return None

    latest = hist.iloc[-1]
    return {
        "symbol": ticker,
        "price": round(latest["Close"], 2),
        "change": round(latest["Close"] - latest["Open"], 2),
        "percent_change": round(((latest["Close"] - latest["Open"]) / latest["Open"]) * 100, 2)
    }


# --- Validation Logic ---
@lru_cache(maxsize=1)
def get_supported_cryptos():
    """
    Cached list of valid CoinGecko coin IDs.
    """
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    return [coin['id'] for coin in data]


def validate_asset_type(keyword: str):
    """
    Determine whether a keyword is a valid crypto ID (CoinGecko) or stock ticker (Yahoo Finance).
    Returns one of: 'crypto', 'stock', or None
    """
    # Check CoinGecko
    keyword_lower = keyword.lower()
    if keyword_lower in get_supported_cryptos():
        return "crypto"

    # Check Yahoo Finance
    try:
        stock = yf.Ticker(keyword.upper())
        hist = stock.history(period="1d")
        if not hist.empty:
            return "stock"
    except Exception:
        pass

    return None
