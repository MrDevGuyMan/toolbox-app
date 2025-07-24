# symbol_table.py
import requests
import csv
import os
from functools import lru_cache

# --- COINGECKO CRYPTO MAP --- #


@lru_cache(maxsize=1)
def get_crypto_symbol_map() -> dict:
    """
    Build a dict like {'BTC': 'bitcoin', 'ETH': 'ethereum'} from CoinGecko.
    """
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Failed to load crypto symbol map: {e}")
        return {}

    mapping = {}
    for coin in data:
        name = coin["id"]
        symbol = coin["symbol"].upper()
        mapping[symbol] = name
    return mapping


# --- STOCK SYMBOL MAP --- #
STOCK_SYMBOL_FILE = os.path.join(
    os.path.dirname(__file__), "stock_symbols.csv")


@lru_cache(maxsize=1)
def get_stock_symbol_map() -> dict:
    """
    Load stock symbol map from CSV: ticker,name
    Example row: AAPL,Apple Inc.
    """
    if not os.path.exists(STOCK_SYMBOL_FILE):
        print(f"⚠️ Missing stock symbol CSV: {STOCK_SYMBOL_FILE}")
        return {}

    mapping = {}
    with open(STOCK_SYMBOL_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["ticker"].upper()] = row["name"]
    return mapping


# --- Unified Lookup --- #
def resolve_crypto_name(ticker: str) -> str | None:
    return get_crypto_symbol_map().get(ticker.upper())


def resolve_stock_name(ticker: str) -> str | None:
    return get_stock_symbol_map().get(ticker.upper())
