import json
import os
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf
from keras.models import load_model

from src.config import GROUP_LOOKBACK_WINDOW, MODELS_DIR, SECTOR_MODELS_DIR
from src.data_loader import get_ticker_symbol
from src.data_multi_horizon import resample_data
from src.group_dataset import load_cached_intraday, load_company_scalers
from src.groups import GROUP_A, GROUP_B, GROUP_COMPANIES, find_group_for_ticker, get_group_model_filename
from src.preprocessing import add_technical_indicators
from src.sector_dataset import load_sector_company_scalers
from src.sectors import SECTOR_COMPANIES, find_sector_for_ticker, get_sector_model_filename


REQUIRED_OHLCV = ["Open", "High", "Low", "Close", "Volume"]
HORIZONS = ["10m", "30m", "1h"]
BIAS_CORRECTION_FACTOR = 0.7
MIN_SIGNAL_EDGE_PCT = 0.004  # 0.4% expected move beyond uncertainty band
MIN_TRUST_FOR_SIGNAL = 0.53
IST = ZoneInfo("Asia/Kolkata")
LEGACY_FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "SMA_20",
    "SMA_50",
    "RSI",
    "MACD",
    "Signal_Line",
    "BB_Upper",
    "BB_Lower",
    "Volume_MA_20",
    "ROC",
    "ATR",
]
ENHANCED_FEATURE_COLUMNS = LEGACY_FEATURE_COLUMNS + [
    "Return_1",
    "Return_5",
    "Return_10",
    "Momentum_5",
    "Momentum_10",
    "Volume_Change_1",
    "Volume_Change_5",
    "Volatility_10",
    "Volatility_20",
    "Range_Pct",
    "ATR_Pct",
    "BB_Width",
    "Close_vs_SMA20",
]
_model_cache: Dict[str, object] = {}
_scaler_cache: Dict[str, Dict[str, object]] = {}
_cache_lock = Lock()


class BackendServiceError(Exception):
    pass


def _load_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _extract_metric(metrics: dict, candidates: List[str]) -> Optional[float]:
    for key in candidates:
        if key in metrics:
            try:
                return float(metrics[key])
            except Exception:
                return None
    return None


def _scaled_mae_to_rupees(mae_scaled: Optional[float], scaler) -> Optional[float]:
    if mae_scaled is None:
        return None
    if not hasattr(scaler, "data_min_") or not hasattr(scaler, "data_max_"):
        return None
    close_idx = 3
    try:
        close_range = float(scaler.data_max_[close_idx] - scaler.data_min_[close_idx])
        return abs(mae_scaled * close_range)
    except Exception:
        return None


def _analytics_key_for_ticker(ticker: str) -> Optional[str]:
    sector_key = find_sector_for_ticker(ticker)
    if sector_key:
        return f"sector_{sector_key}"
    group_key = find_group_for_ticker(ticker)
    if group_key:
        return group_key
    return None


def _analytics_backtest_df_for_ticker(ticker: str) -> Optional[pd.DataFrame]:
    key = _analytics_key_for_ticker(ticker.upper().strip())
    if key is None:
        return None
    path = os.path.join(MODELS_DIR, "analytics", f"{key}_backtest.csv")
    df = _load_csv(path)
    if df is None or df.empty:
        return None
    if not {"ticker", "horizon", "error"}.issubset(df.columns):
        return None
    df = df.copy()
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["horizon"] = df["horizon"].astype(str)
    df["error"] = pd.to_numeric(df["error"], errors="coerce")
    df = df.dropna(subset=["error"])
    return df


def _bias_corrections_for_ticker(ticker: str) -> Dict[str, float]:
    t = ticker.upper().strip()
    df = _analytics_backtest_df_for_ticker(t)
    corrections = {h: 0.0 for h in HORIZONS}
    if df is None or df.empty:
        return corrections

    for horizon in HORIZONS:
        per_ticker = df[(df["ticker"] == t) & (df["horizon"] == horizon)]
        source = per_ticker if len(per_ticker) >= 30 else df[df["horizon"] == horizon]
        if source.empty:
            continue
        # Median error is robust to outliers; error = predicted - actual.
        median_error = float(source["error"].median())
        corrections[horizon] = BIAS_CORRECTION_FACTOR * median_error
    return corrections


def _apply_bias_correction(row, correction: float):
    arr = pd.Series(row, dtype="float64").to_numpy()
    arr[0:4] = arr[0:4] - correction
    arr[1] = max(arr[1], arr[0], arr[3])  # keep High valid
    arr[2] = min(arr[2], arr[0], arr[3])  # keep Low valid
    return arr


def _signal_for_prediction(
    ticker: str,
    current_price: float,
    predicted_close_by_horizon: Dict[str, float],
    mae_rupees_by_horizon: Dict[str, Optional[float]],
) -> dict:
    # Use a weighted directional vote and only emit BUY/SELL when movement exceeds uncertainty.
    horizon_weights = {"10m": 0.5, "30m": 0.3, "1h": 0.2}
    weighted_vote = 0.0
    weighted_edge = 0.0
    total_weight = 0.0

    if current_price <= 0:
        return {
            "decision": "HOLD",
            "trend": "neutral",
            "confidence": 0.0,
            "expected_edge_pct": 0.0,
            "reason": "invalid_current_price",
        }

    for horizon in HORIZONS:
        pred_close = float(predicted_close_by_horizon[horizon])
        delta_pct = (pred_close - current_price) / current_price
        band_rupees = float(mae_rupees_by_horizon.get(horizon) or 0.0)
        band_pct = abs(band_rupees / current_price)
        edge_pct = max(0.0, abs(delta_pct) - band_pct)
        direction = 1.0 if delta_pct > 0 else (-1.0 if delta_pct < 0 else 0.0)

        w = horizon_weights[horizon]
        weighted_vote += w * direction
        weighted_edge += w * edge_pct
        total_weight += w

    if total_weight <= 0:
        return {
            "decision": "HOLD",
            "trend": "neutral",
            "confidence": 0.0,
            "expected_edge_pct": 0.0,
            "reason": "no_horizon_weight",
        }

    weighted_vote /= total_weight
    weighted_edge /= total_weight

    trust = 0.0
    try:
        trust = float(trust_metrics_payload(ticker).get("directional_accuracy", 0.0))
    except Exception:
        trust = 0.0

    if weighted_edge < MIN_SIGNAL_EDGE_PCT:
        return {
            "decision": "HOLD",
            "trend": "neutral",
            "confidence": 0.0,
            "expected_edge_pct": weighted_edge,
            "reason": "edge_below_threshold",
        }

    if abs(weighted_vote) < 0.4:
        return {
            "decision": "HOLD",
            "trend": "neutral",
            "confidence": 0.0,
            "expected_edge_pct": weighted_edge,
            "reason": "horizon_disagreement",
        }

    if trust < MIN_TRUST_FOR_SIGNAL:
        return {
            "decision": "HOLD",
            "trend": "neutral",
            "confidence": 0.0,
            "expected_edge_pct": weighted_edge,
            "reason": "trust_below_threshold",
        }

    decision = "BUY" if weighted_vote > 0 else "SELL"
    trend = "up" if decision == "BUY" else "down"
    confidence = max(0.0, min(1.0, abs(weighted_vote) * 0.7 + min(weighted_edge / 0.02, 1.0) * 0.3))
    return {
        "decision": decision,
        "trend": trend,
        "confidence": float(confidence),
        "expected_edge_pct": float(weighted_edge),
        "reason": "ok",
    }


def _group_models_available() -> bool:
    candidates = [
        os.path.join(MODELS_DIR, "group_models", get_group_model_filename(GROUP_A)),
        os.path.join(MODELS_DIR, "group_models", get_group_model_filename(GROUP_B)),
        os.path.join(MODELS_DIR, get_group_model_filename(GROUP_A)),
        os.path.join(MODELS_DIR, get_group_model_filename(GROUP_B)),
    ]
    return any(os.path.exists(path) for path in candidates)


def list_companies() -> List[Dict[str, str]]:
    companies: Dict[str, str] = {}
    for sector_companies in SECTOR_COMPANIES.values():
        for company in sector_companies:
            companies[company.ticker] = company.name

    if _group_models_available():
        for group_companies in GROUP_COMPANIES.values():
            for company in group_companies:
                companies.setdefault(company.ticker, company.name)

    return [
        {"ticker": ticker, "name": name}
        for ticker, name in sorted(companies.items(), key=lambda kv: kv[1].lower())
    ]


def market_status_payload() -> dict:
    now_ist = datetime.now(IST)
    weekday = now_ist.weekday()
    market_start = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open = (weekday < 5) and (market_start <= now_ist <= market_end)
    return {
        "is_open": is_open,
        "current_time_ist": now_ist.isoformat(),
        "session_start": "09:15",
        "session_end": "15:30",
        "mode": "live" if is_open else "simulation",
    }


def _normalize_market_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED_OHLCV)
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    if not set(REQUIRED_OHLCV).issubset(out.columns):
        return pd.DataFrame(columns=REQUIRED_OHLCV)
    out = out[REQUIRED_OHLCV].copy()
    for col in REQUIRED_OHLCV:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    out = out[out["Volume"] > 0]
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()
    return out


def _fetch_live_5m_df(ticker: str, period: str = "10d", interval: str = "5m") -> pd.DataFrame:
    symbol = get_ticker_symbol(ticker, exchange="NSE")
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=True)
    except Exception:
        df = pd.DataFrame()

    df = _normalize_market_df(df)
    if not df.empty:
        return df

    cached = load_cached_intraday(ticker=ticker, interval="5m")
    cached = _normalize_market_df(cached)
    if not cached.empty:
        return cached

    raise BackendServiceError(f"No market data available for {ticker}")


def _align_feature_frame_for_scaler(df_features: pd.DataFrame, feature_scaler) -> pd.DataFrame:
    # Keep inference resilient when serving code and saved scalers temporarily diverge.
    if df_features is None or df_features.empty:
        return df_features

    expected = int(getattr(feature_scaler, "n_features_in_", len(df_features.columns)))
    current = int(len(df_features.columns))
    if current == expected:
        return df_features

    if expected == len(ENHANCED_FEATURE_COLUMNS):
        return df_features.reindex(columns=ENHANCED_FEATURE_COLUMNS, fill_value=0.0)
    if expected == len(LEGACY_FEATURE_COLUMNS):
        return df_features.reindex(columns=LEGACY_FEATURE_COLUMNS, fill_value=0.0)

    # Generic fallback for unknown schemas.
    if current > expected:
        return df_features.iloc[:, :expected]
    for i in range(current, expected):
        df_features[f"_pad_{i}"] = 0.0
    return df_features


def _model_and_scalers_for_ticker(ticker: str):
    t = ticker.upper().strip()
    if not t:
        raise BackendServiceError("Ticker is required")

    sector_key = find_sector_for_ticker(t)
    if sector_key:
        model_path = os.path.join(SECTOR_MODELS_DIR, get_sector_model_filename(sector_key))
        if not os.path.exists(model_path):
            raise BackendServiceError(f"Sector model not found for {t} at {model_path}")
        scaler_key = f"sector::{sector_key}::{t}"
        with _cache_lock:
            if model_path not in _model_cache:
                _model_cache[model_path] = load_model(model_path, compile=False)
            if scaler_key not in _scaler_cache:
                _scaler_cache[scaler_key] = load_sector_company_scalers(sector_key, t)
            return (
                _model_cache[model_path],
                _scaler_cache[scaler_key],
                sector_key,
                model_path,
                f"sector_{sector_key}",
            )

    group_key = find_group_for_ticker(t)
    if group_key:
        model_name = get_group_model_filename(group_key)
        model_candidates = [
            os.path.join(MODELS_DIR, "group_models", model_name),
            os.path.join(MODELS_DIR, model_name),
        ]
        model_path = next((p for p in model_candidates if os.path.exists(p)), None)
        if model_path is None:
            raise BackendServiceError(f"Group model not found for {t}")

        scaler_key = f"group::{group_key}::{t}"
        with _cache_lock:
            if model_path not in _model_cache:
                _model_cache[model_path] = load_model(model_path, compile=False)
            if scaler_key not in _scaler_cache:
                _scaler_cache[scaler_key] = load_company_scalers(group_key, t)
            return (
                _model_cache[model_path],
                _scaler_cache[scaler_key],
                group_key,
                model_path,
                group_key,
            )

    raise BackendServiceError(f"Ticker {t} is not mapped to an available model")


def _validation_mae_rupees(model_path: str, scalers: Dict[str, object]) -> Dict[str, Optional[float]]:
    meta_path = model_path.replace(".keras", "_meta.json")
    payload = _load_json(meta_path) or {}
    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}

    mae_10m_scaled = _extract_metric(metrics, ["forecast_10m_mae", "forecast_10m_mean_absolute_error"])
    mae_30m_scaled = _extract_metric(metrics, ["forecast_30m_mae", "forecast_30m_mean_absolute_error"])
    mae_1h_scaled = _extract_metric(metrics, ["forecast_1h_mae", "forecast_1h_mean_absolute_error"])

    return {
        "10m": _scaled_mae_to_rupees(mae_10m_scaled, scalers["target_10m"]),
        "30m": _scaled_mae_to_rupees(mae_30m_scaled, scalers["target_30m"]),
        "1h": _scaled_mae_to_rupees(mae_1h_scaled, scalers["target_1h"]),
    }


def predict_payload(ticker: str, allow_simulation: bool = True) -> dict:
    t = ticker.upper().strip()
    market = market_status_payload()
    if not market["is_open"] and not allow_simulation:
        raise BackendServiceError("Market is closed and simulation is not allowed")

    model, scalers, _, model_path, _ = _model_and_scalers_for_ticker(t)
    df_5m = _fetch_live_5m_df(t, period="10d", interval="5m")
    df_10m = resample_data(df_5m, "10min")
    if df_10m.empty:
        raise BackendServiceError(f"Unable to build 10m candles for {t}")

    df_features = add_technical_indicators(df_10m)
    if len(df_features) < GROUP_LOOKBACK_WINDOW:
        raise BackendServiceError(
            f"Not enough processed candles for {t}. Need at least {GROUP_LOOKBACK_WINDOW}."
        )

    feature_scaler = scalers["feature"]
    df_features = _align_feature_frame_for_scaler(df_features, feature_scaler)
    feature_cols = (
        list(feature_scaler.feature_names_in_)
        if hasattr(feature_scaler, "feature_names_in_")
        else df_features.columns.tolist()
    )
    last_seq = df_features.iloc[-GROUP_LOOKBACK_WINDOW:][feature_cols]
    input_seq = feature_scaler.transform(last_seq).reshape(1, GROUP_LOOKBACK_WINDOW, -1)

    preds = model.predict(input_seq, verbose=0)
    p_10m = scalers["target_10m"].inverse_transform(preds[0])[0]
    p_30m = scalers["target_30m"].inverse_transform(preds[1])[0]
    p_1h = scalers["target_1h"].inverse_transform(preds[2])[0]

    bias_corrections = _bias_corrections_for_ticker(t)
    p_10m = _apply_bias_correction(p_10m, bias_corrections["10m"])
    p_30m = _apply_bias_correction(p_30m, bias_corrections["30m"])
    p_1h = _apply_bias_correction(p_1h, bias_corrections["1h"])

    current_price = float(df_10m["Close"].iloc[-1])
    last_candle_time = pd.Timestamp(df_10m.index[-1]).tz_convert(IST).isoformat() if getattr(df_10m.index, "tz", None) else pd.Timestamp(df_10m.index[-1]).tz_localize(IST).isoformat()
    mae_rupees = _validation_mae_rupees(model_path=model_path, scalers=scalers)
    signal = _signal_for_prediction(
        ticker=t,
        current_price=current_price,
        predicted_close_by_horizon={
            "10m": float(p_10m[3]),
            "30m": float(p_30m[3]),
            "1h": float(p_1h[3]),
        },
        mae_rupees_by_horizon=mae_rupees,
    )

    def horizon_payload(row, mae):
        close_value = float(row[3])
        band = float(mae) if mae is not None else 0.0
        return {
            "open": float(row[0]),
            "high": float(row[1]),
            "low": float(row[2]),
            "close": close_value,
            "volume": float(row[4]),
            "confidence_low": close_value - band,
            "confidence_high": close_value + band,
        }

    company_name = next((item["name"] for item in list_companies() if item["ticker"] == t), t)
    return {
        "ticker": t,
        "name": company_name,
        "market_status": {
            "is_open": market["is_open"],
            "mode": market["mode"],
        },
        "current_price": current_price,
        "last_candle_time": last_candle_time,
        "predictions": {
            "10m": horizon_payload(p_10m, mae_rupees.get("10m")),
            "30m": horizon_payload(p_30m, mae_rupees.get("30m")),
            "1h": horizon_payload(p_1h, mae_rupees.get("1h")),
        },
        "trade_signal": signal,
        "trend": signal["trend"],
        "confidence": signal["confidence"],
        "calibration": {
            "type": "median_error_bias_correction",
            "factor": BIAS_CORRECTION_FACTOR,
            "by_horizon": bias_corrections,
        },
    }


def trust_metrics_payload(ticker: str) -> dict:
    key = _analytics_key_for_ticker(ticker.upper().strip())
    if key is None:
        raise BackendServiceError("Unknown ticker")
    path = os.path.join(MODELS_DIR, "analytics", f"{key}_accuracy_30d.json")
    payload = _load_json(path)
    if payload is None:
        raise BackendServiceError(f"Trust metrics not found for {ticker}")
    return {
        "directional_accuracy": float(payload.get("directional_accuracy", 0.0)),
        "mean_absolute_error": float(payload.get("mean_absolute_error", 0.0)),
        "window_days": int(payload.get("window_days", 30)),
        "sample_count": int(payload.get("sample_count", 0)),
        "horizons": payload.get("horizons", {}),
    }


def explainability_payload(ticker: str) -> dict:
    key = _analytics_key_for_ticker(ticker.upper().strip())
    if key is None:
        raise BackendServiceError("Unknown ticker")
    path = os.path.join(MODELS_DIR, "analytics", f"{key}_explainability.json")
    payload = _load_json(path)
    if payload is None:
        raise BackendServiceError(f"Explainability not found for {ticker}")
    return {
        "top_features": payload.get("top_features", []),
        "core_indicators": payload.get("core_indicators", {}),
    }


def backtest_payload(ticker: str, limit: int = 10, horizon: str = "10m") -> dict:
    key = _analytics_key_for_ticker(ticker.upper().strip())
    if key is None:
        raise BackendServiceError("Unknown ticker")

    path = os.path.join(MODELS_DIR, "analytics", f"{key}_backtest.csv")
    df = _load_csv(path)
    if df is None or df.empty:
        return {"rows": []}

    if "ticker" in df.columns:
        filtered = df[df["ticker"].astype(str).str.upper() == ticker.upper().strip()]
        if not filtered.empty:
            df = filtered

    selected_horizon = horizon if horizon in HORIZONS else "10m"
    if "horizon" in df.columns:
        filtered_h = df[df["horizon"].astype(str) == selected_horizon]
        if not filtered_h.empty:
            df = filtered_h

    if "date" in df.columns:
        df = df.sort_values("date", ascending=False)

    rows = []
    for _, row in df.head(max(1, int(limit))).iterrows():
        rows.append(
            {
                "date": str(row.get("date", "")),
                "horizon": str(row.get("horizon", selected_horizon)),
                "predicted_close": float(row.get("predicted_close", 0.0)),
                "actual_close": float(row.get("actual_close", 0.0)),
                "error": float(row.get("error", 0.0)),
            }
        )
    return {"rows": rows}


def chart_payload(ticker: str, period: str = "2d", interval: str = "5m") -> dict:
    t = ticker.upper().strip()
    valid_intervals = {"1m", "5m", "15m", "30m", "60m", "1h"}
    valid_periods = {"1d", "2d", "5d", "7d", "1mo", "3mo", "6mo"}
    interval = interval if interval in valid_intervals else "5m"
    period = period if period in valid_periods else "2d"

    symbol = get_ticker_symbol(t, exchange="NSE")
    fetch_periods = [period]
    if period == "2d":
        # Fetch a wider window and then slice to the last 2 trading sessions.
        fetch_periods = ["5d", "7d"]

    df = pd.DataFrame()
    for candidate_period in fetch_periods:
        try:
            raw = yf.download(
                symbol,
                interval=interval,
                period=candidate_period,
                progress=False,
                auto_adjust=True,
            )
        except Exception:
            raw = pd.DataFrame()
        df = _normalize_market_df(raw)
        if not df.empty:
            break

    if df.empty:
        return {"points": []}

    if period == "2d":
        ts_index = pd.DatetimeIndex(df.index)
        if ts_index.tz is None:
            ts_index = ts_index.tz_localize(IST)
        else:
            ts_index = ts_index.tz_convert(IST)
        day_index = pd.Index(ts_index.date)
        unique_days = day_index.drop_duplicates()
        if len(unique_days) > 2:
            keep_days = set(unique_days[-2:])
            df = df[day_index.isin(keep_days)]

    points = []
    for idx, row in df.tail(500).iterrows():
        ts = pd.Timestamp(idx)
        if ts.tzinfo is None:
            ts = ts.tz_localize(IST)
        else:
            ts = ts.tz_convert(IST)
        points.append({"time": ts.isoformat(), "close": float(row["Close"])})
    return {"points": points}
