import os
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.config import DATA_DIR, GROUP_LOOKBACK_WINDOW, GROUP_SCALERS_DIR
from src.data_loader import fetch_data
from src.data_multi_horizon import prepare_multi_horizon_data, resample_data
from src.groups import GROUP_COMPANIES


GROUP_DATA_DIR = os.path.join(DATA_DIR, "groups")
GROUP_SCALER_DIR = GROUP_SCALERS_DIR
REQUIRED_OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def _company_data_path(ticker: str, interval: str) -> str:
    os.makedirs(GROUP_DATA_DIR, exist_ok=True)
    return os.path.join(GROUP_DATA_DIR, f"{ticker}_{interval}.csv")


def _normalize_intraday_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)

    if not isinstance(out.index, pd.DatetimeIndex):
        if "Datetime" in out.columns:
            out["Datetime"] = pd.to_datetime(out["Datetime"], errors="coerce", utc=True)
            out = out.dropna(subset=["Datetime"])
            out = out.set_index("Datetime")
        else:
            out.index = pd.to_datetime(out.index, errors="coerce", utc=True)
            out = out[~out.index.isna()]

    if not isinstance(out.index, pd.DatetimeIndex):
        return pd.DataFrame()

    # Force a single timezone representation so concat won't degrade index dtype.
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    else:
        out.index = out.index.tz_convert("UTC")
    out.index = out.index.tz_convert("Asia/Kolkata")

    if not set(REQUIRED_OHLCV).issubset(set(out.columns)):
        return pd.DataFrame()

    out = out[REQUIRED_OHLCV].dropna(subset=["Open", "High", "Low", "Close"])
    out = out[out["Volume"] > 0]
    out = out[~out.index.duplicated(keep="last")]
    out.sort_index(inplace=True)
    return out


def _load_cached_intraday(ticker: str, interval: str = "5m") -> pd.DataFrame:
    path = _company_data_path(ticker, interval)
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return _normalize_intraday_df(df)


def load_cached_intraday(ticker: str, interval: str = "5m") -> pd.DataFrame:
    return _load_cached_intraday(ticker, interval=interval)


def _save_intraday_cache(df: pd.DataFrame, ticker: str, interval: str = "5m") -> None:
    path = _company_data_path(ticker, interval)
    clean_df = _normalize_intraday_df(df)
    if clean_df.empty:
        return
    clean_df.to_csv(path)


def refresh_intraday_cache(
    ticker: str,
    interval: str = "5m",
    period: str = "59d",
    exchange: str = "NSE",
) -> pd.DataFrame:
    def fetch_with_exchange_and_alias_fallback(symbol: str, req_interval: str, req_period: str) -> pd.DataFrame:
        exchange_candidates = [exchange]
        alternate_exchange = "BSE" if exchange == "NSE" else "NSE"
        exchange_candidates.append(alternate_exchange)

        for ex in exchange_candidates:
            df_candidate = fetch_data(symbol, interval=req_interval, period=req_period, exchange=ex)
            if df_candidate is not None and not df_candidate.empty:
                return df_candidate

        alias_symbols = {
            "TATAMOTORS": ["TATAMOTORS.BO"],
        }
        for alias in alias_symbols.get(symbol.upper(), []):
            df_candidate = fetch_data(alias, interval=req_interval, period=req_period, exchange=exchange)
            if df_candidate is not None and not df_candidate.empty:
                return df_candidate

        return pd.DataFrame()

    historical_df = _load_cached_intraday(ticker, interval=interval)
    new_df = fetch_with_exchange_and_alias_fallback(ticker, req_interval=interval, req_period=period)

    # Yahoo occasionally returns false "possibly delisted" for 5m/59d.
    # Retry with shorter windows, then fallback to 1m->5m aggregation.
    if (new_df is None or new_df.empty) and interval == "5m":
        for retry_period in ("30d", "7d"):
            new_df = fetch_with_exchange_and_alias_fallback(
                ticker, req_interval="5m", req_period=retry_period
            )
            if new_df is not None and not new_df.empty:
                break

        if new_df is None or new_df.empty:
            one_min_df = fetch_with_exchange_and_alias_fallback(
                ticker, req_interval="1m", req_period="7d"
            )
            if one_min_df is not None and not one_min_df.empty:
                new_df = resample_data(one_min_df, "5min")

    historical_df = _normalize_intraday_df(historical_df)
    new_df = _normalize_intraday_df(new_df)

    if new_df is None or new_df.empty:
        return historical_df

    combined = pd.concat([historical_df, new_df], axis=0)
    combined = _normalize_intraday_df(combined)
    _save_intraday_cache(combined, ticker, interval=interval)
    return combined


def _scale_company_arrays(
    X: np.ndarray,
    y_10m: np.ndarray,
    y_30m: np.ndarray,
    y_1h: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, MinMaxScaler]]:
    num_samples, lookback, num_features = X.shape
    x_flat = X.reshape(-1, num_features)

    feature_scaler = MinMaxScaler(feature_range=(0, 1))
    x_scaled = feature_scaler.fit_transform(x_flat).reshape(num_samples, lookback, num_features)

    scaler_10m = MinMaxScaler(feature_range=(0, 1))
    y_10m_scaled = scaler_10m.fit_transform(y_10m)

    scaler_30m = MinMaxScaler(feature_range=(0, 1))
    y_30m_scaled = scaler_30m.fit_transform(y_30m)

    scaler_1h = MinMaxScaler(feature_range=(0, 1))
    y_1h_scaled = scaler_1h.fit_transform(y_1h)

    scalers = {
        "feature": feature_scaler,
        "target_10m": scaler_10m,
        "target_30m": scaler_30m,
        "target_1h": scaler_1h,
    }
    return x_scaled, y_10m_scaled, y_30m_scaled, y_1h_scaled, scalers


def _scaler_paths(group_key: str, ticker: str) -> Dict[str, str]:
    base_dir = os.path.join(GROUP_SCALER_DIR, group_key)
    os.makedirs(base_dir, exist_ok=True)
    return {
        "feature": os.path.join(base_dir, f"{ticker}_feature_scaler.pkl"),
        "target_10m": os.path.join(base_dir, f"{ticker}_target_10m_scaler.pkl"),
        "target_30m": os.path.join(base_dir, f"{ticker}_target_30m_scaler.pkl"),
        "target_1h": os.path.join(base_dir, f"{ticker}_target_1h_scaler.pkl"),
    }


def save_company_scalers(group_key: str, ticker: str, scalers: Dict[str, MinMaxScaler]) -> None:
    paths = _scaler_paths(group_key, ticker)
    for key, scaler in scalers.items():
        joblib.dump(scaler, paths[key])


def load_company_scalers(group_key: str, ticker: str) -> Dict[str, MinMaxScaler]:
    paths = _scaler_paths(group_key, ticker)
    return {name: joblib.load(path) for name, path in paths.items()}


def build_group_company_datasets(
    group_key: str,
    lookback: int = GROUP_LOOKBACK_WINDOW,
    refresh: bool = True,
    interval: str = "5m",
    period: str = "59d",
    exchange: str = "NSE",
    min_samples: int = 200,
) -> Dict[str, Dict[str, np.ndarray]]:
    if group_key not in GROUP_COMPANIES:
        raise ValueError(f"Unknown group key: {group_key}")

    datasets: Dict[str, Dict[str, np.ndarray]] = {}
    for company in GROUP_COMPANIES[group_key]:
        ticker = company.ticker
        if refresh:
            intraday_df = refresh_intraday_cache(
                ticker=ticker,
                interval=interval,
                period=period,
                exchange=exchange,
            )
        else:
            intraday_df = _load_cached_intraday(ticker, interval=interval)

        if intraday_df.empty:
            continue

        df_10m = resample_data(intraday_df, "10min")
        if df_10m.empty:
            continue

        X, y_10m, y_30m, y_1h = prepare_multi_horizon_data(df_10m, lookback=lookback)
        if len(X) < min_samples:
            continue

        x_scaled, y10_scaled, y30_scaled, y1h_scaled, scalers = _scale_company_arrays(
            X, y_10m, y_30m, y_1h
        )
        save_company_scalers(group_key, ticker, scalers)

        datasets[ticker] = {
            "X": x_scaled,
            "y_10m": y10_scaled,
            "y_30m": y30_scaled,
            "y_1h": y1h_scaled,
        }

    return datasets
