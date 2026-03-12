import os
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from src.config import GROUP_LOOKBACK_WINDOW, SECTOR_SCALERS_DIR
from src.data_multi_horizon import prepare_multi_horizon_data, resample_data
from src.group_dataset import load_cached_intraday, refresh_intraday_cache
from src.sectors import SECTOR_COMPANIES


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


def _scaler_paths(sector_key: str, ticker: str) -> Dict[str, str]:
    base_dir = os.path.join(SECTOR_SCALERS_DIR, sector_key)
    os.makedirs(base_dir, exist_ok=True)
    return {
        "feature": os.path.join(base_dir, f"{ticker}_feature_scaler.pkl"),
        "target_10m": os.path.join(base_dir, f"{ticker}_target_10m_scaler.pkl"),
        "target_30m": os.path.join(base_dir, f"{ticker}_target_30m_scaler.pkl"),
        "target_1h": os.path.join(base_dir, f"{ticker}_target_1h_scaler.pkl"),
    }


def save_sector_company_scalers(sector_key: str, ticker: str, scalers: Dict[str, MinMaxScaler]) -> None:
    paths = _scaler_paths(sector_key, ticker)
    for key, scaler in scalers.items():
        joblib.dump(scaler, paths[key])


def load_sector_company_scalers(sector_key: str, ticker: str) -> Dict[str, MinMaxScaler]:
    paths = _scaler_paths(sector_key, ticker)
    return {name: joblib.load(path) for name, path in paths.items()}


def build_sector_company_datasets(
    sector_key: str,
    lookback: int = GROUP_LOOKBACK_WINDOW,
    refresh: bool = True,
    interval: str = "5m",
    period: str = "59d",
    exchange: str = "NSE",
    min_samples: int = 200,
) -> Dict[str, Dict[str, np.ndarray]]:
    if sector_key not in SECTOR_COMPANIES:
        raise ValueError(f"Unknown sector key: {sector_key}")

    datasets: Dict[str, Dict[str, np.ndarray]] = {}
    for company in SECTOR_COMPANIES[sector_key]:
        ticker = company.ticker
        if refresh:
            intraday_df = refresh_intraday_cache(
                ticker=ticker,
                interval=interval,
                period=period,
                exchange=exchange,
            )
        else:
            intraday_df = load_cached_intraday(ticker, interval=interval)

        if intraday_df is None or intraday_df.empty:
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
        save_sector_company_scalers(sector_key, ticker, scalers)

        datasets[ticker] = {
            "X": x_scaled,
            "y_10m": y10_scaled,
            "y_30m": y30_scaled,
            "y_1h": y1h_scaled,
        }

    return datasets
