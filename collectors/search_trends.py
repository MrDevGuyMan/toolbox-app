# search_trends.py
"""
Google Search Trends collector using pytrends.
"""

from __future__ import annotations

import time
from typing import List, Dict, Optional
import pandas as pd
from pytrends.request import TrendReq

# Optional: silence future pandas warning
pd.set_option("future.no_silent_downcasting", True)

# --- Internal: singleton-ish client -------------------------------------------------
_pytrends_client: Optional[TrendReq] = None


def _get_client(hl: str = "en-US", tz: int = 0) -> TrendReq:
    global _pytrends_client
    if _pytrends_client is None:
        _pytrends_client = TrendReq(hl=hl, tz=tz)
    return _pytrends_client


# --- Helpers ------------------------------------------------------------------------
def _retry(fn, retries: int = 3, backoff: float = 3.0):
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == retries:
                raise
            wait = backoff * attempt
            print(
                f"⚠️ Google Trends error ({e}). Retry {attempt}/{retries} in {wait:.0f}s...")
            time.sleep(wait)


# --- Public API ---------------------------------------------------------------------
def get_interest_over_time(keyword: str,
                           timeframe: str = "now 7-d",
                           geo: str = "",
                           retries: int = 3) -> List[Dict]:
    pt = _get_client()
    kw_list = [keyword]

    def _do():
        pt.build_payload(kw_list, timeframe=timeframe, geo=geo)
        df = pt.interest_over_time()
        if df.empty:
            return []
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        series = df[keyword]
        return [
            {"date": idx.to_pydatetime().strftime(
                "%Y-%m-%d %H:%M:%S"), "value": int(val)}
            for idx, val in series.items()
        ]

    return _retry(_do, retries=retries)


def get_related_queries(keyword: str, geo: str = "", retries: int = 3) -> Dict[str, List[Dict]]:
    pt = _get_client()
    kw_list = [keyword]

    def _do():
        try:
            pt.build_payload(kw_list, geo=geo)
            all_related = pt.related_queries()
            if keyword not in all_related:
                print(f"⚠️ No related queries returned for '{keyword}'")
                return {"top": [], "rising": []}
        except Exception as e:
            print(f"⚠️ Could not fetch related queries: {e}")
            return {"top": [], "rising": []}

        data = all_related[keyword]

        def _df_to_list(df: Optional[pd.DataFrame]) -> List[Dict]:
            if df is None or df.empty:
                return []
            cols = {c.lower(): c for c in df.columns}
            return [{"query": str(row[cols["query"]]), "value": int(row[cols["value"]])}
                    for _, row in df.iterrows()]

        return {
            "top": _df_to_list(data.get("top")),
            "rising": _df_to_list(data.get("rising")),
        }

    return _retry(_do, retries=retries)


def get_trending_searches_daily(region: str = "united_states", retries: int = 3) -> List[str]:
    pt = _get_client()

    def _do():
        df = pt.trending_searches(pn=region)
        if df.empty:
            return []
        return [str(val) for val in df.iloc[:, 0].tolist()]

    return _retry(_do, retries=retries)
