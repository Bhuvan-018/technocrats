import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Tuple

import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

from db import cache_get, cache_set

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "ITC.NS",
    "HINDUNILVR.NS",
]


def market_status() -> dict:
    now_ist = datetime.now(IST)
    weekday = now_ist.weekday()
    is_open = weekday < 5 and (9 <= now_ist.hour < 15 or (now_ist.hour == 15 and now_ist.minute <= 30))
    return {
        "is_open": is_open,
        "current_time_ist": now_ist.isoformat(),
        "session_start": "09:15",
        "session_end": "15:30",
    }


def companies() -> dict:
    tickers_env = os.environ.get("MARKET_TICKERS", "")
    tickers = [t.strip() for t in tickers_env.split(",") if t.strip()] or DEFAULT_TICKERS
    return get_company_quotes(tickers)


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()
    df = df[list(required)].copy()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return df


def _normalize_multi(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def chart(ticker: str, period: str = "1d", interval: str = "5m") -> dict:
    cache_key = f"chart:{ticker}:{period}:{interval}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    if yf is None:
        return {"points": []}
    try:
        df = yf.download(ticker, interval=interval, period=period, progress=False, auto_adjust=True)
    except Exception:
        df = pd.DataFrame()
    df = _normalize_df(df)
    if df.empty:
        return {"points": []}
    points = []
    for idx, row in df.iterrows():
        points.append(
            {
                "time": str(pd.Timestamp(idx).to_pydatetime().isoformat()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        )
    payload = {"points": points}
    cache_set(cache_key, json.dumps(payload), ttl_seconds=60)
    return payload


def oil_price() -> dict:
    cached = cache_get("oil_price")
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    if yf is None:
        return {
            "ticker": "CL=F",
            "price": 0.0,
            "change": 0.0,
            "changePercent": 0.0,
            "timestamp": datetime.now(IST).isoformat(),
            "available": False,
        }
    try:
        df = yf.download("CL=F", period="2d", interval="1d", progress=False, auto_adjust=True)
    except Exception:
        df = pd.DataFrame()
    if df is None or df.empty:
        return {
            "ticker": "CL=F",
            "price": 0.0,
            "change": 0.0,
            "changePercent": 0.0,
            "timestamp": datetime.now(IST).isoformat(),
            "available": False,
        }

    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df["CL=F"]
        except Exception:
            df = df
    df = _normalize_multi(df)
    if df.empty:
        return {
            "ticker": "CL=F",
            "price": 0.0,
            "change": 0.0,
            "changePercent": 0.0,
            "timestamp": datetime.now(IST).isoformat(),
            "available": False,
        }

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    def _scalar(val):
        if isinstance(val, pd.Series):
            return float(val.iloc[0])
        return float(val)

    price = _scalar(last["Close"])
    prev_close = _scalar(prev["Close"])
    change = float(price - prev_close)
    change_percent = (change / prev_close) * 100 if prev_close else 0.0
    payload = {
        "ticker": "CL=F",
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "timestamp": datetime.now(IST).isoformat(),
        "available": True,
    }
    cache_set("oil_price", json.dumps(payload), ttl_seconds=300)
    return payload


def get_indices() -> list[dict]:
    cache_key = "indices"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    if yf is None:
        return []
    tickers = {"NIFTY 50": "^NSEI", "SENSEX": "^BSESN"}
    try:
        df = yf.download(
            " ".join(tickers.values()),
            period="2d",
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )
    except Exception:
        return []

    results = []
    for name, symbol in tickers.items():
        try:
            series = df[symbol] if isinstance(df.columns, pd.MultiIndex) else df
            series = _normalize_multi(series)
            if series.empty:
                continue
            last = series.iloc[-1]
            prev = series.iloc[-2] if len(series) > 1 else last
            value = float(last["Close"])
            change = float(value - float(prev["Close"]))
            change_percent = (change / float(prev["Close"])) * 100 if float(prev["Close"]) else 0.0
            results.append(
                {
                    "name": name,
                    "value": value,
                    "change": change,
                    "changePercent": change_percent,
                }
            )
        except Exception:
            continue

    cache_set(cache_key, json.dumps(results), ttl_seconds=120)
    return results


def get_company_quotes(tickers: list[str]) -> list[dict]:
    if not tickers:
        return []
    cache_key = f"companies:{','.join(tickers)}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    if yf is None:
        return []
    try:
        df = yf.download(
            " ".join(tickers),
            period="2d",
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )
    except Exception:
        return []

    results = []
    for symbol in tickers:
        try:
            if isinstance(df.columns, pd.MultiIndex):
                series = df[symbol]
            else:
                series = df
            series = _normalize_multi(series)
            if series.empty:
                continue
            last = series.iloc[-1]
            prev = series.iloc[-2] if len(series) > 1 else last
            price = float(last["Close"])
            change = float(price - float(prev["Close"]))
            change_percent = (change / float(prev["Close"])) * 100 if float(prev["Close"]) else 0.0
            volume = float(last.get("Volume", 0.0))
            results.append(
                {
                    "symbol": symbol,
                    "name": symbol,
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": volume,
                }
            )
        except Exception:
            continue

    cache_set(cache_key, json.dumps(results), ttl_seconds=60)
    return results
