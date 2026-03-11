import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from keras.models import load_model

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import ANALYTICS_DIR, GROUP_LOOKBACK_WINDOW, MODELS_DIR, SECTOR_MODELS_DIR
from src.data_multi_horizon import resample_data
from src.group_dataset import load_cached_intraday, load_company_scalers, refresh_intraday_cache
from src.groups import GROUP_A, GROUP_B, GROUP_COMPANIES, get_group_model_filename
from src.preprocessing import add_technical_indicators
from src.sector_dataset import load_sector_company_scalers
from src.sectors import (
    SECTOR_BANKING,
    SECTOR_COMPANIES,
    SECTOR_ENERGY,
    SECTOR_IT,
    get_sector_model_filename,
)


LEGACY_GROUP_KEYS = [GROUP_A, GROUP_B]
SECTOR_KEYS = [SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT]


def _is_sector(key: str) -> bool:
    return key in SECTOR_COMPANIES


def _company_dict(key: str):
    if _is_sector(key):
        return SECTOR_COMPANIES
    return GROUP_COMPANIES


def _model_path(key: str) -> str:
    if _is_sector(key):
        return os.path.join(SECTOR_MODELS_DIR, get_sector_model_filename(key))
    # Backward compatibility: group models may exist either in root models/ or models/group_models/.
    root_path = os.path.join(MODELS_DIR, get_group_model_filename(key))
    group_models_path = os.path.join(MODELS_DIR, "group_models", get_group_model_filename(key))
    if os.path.exists(group_models_path):
        return group_models_path
    return root_path


def _load_scalers(key: str, ticker: str):
    if _is_sector(key):
        return load_sector_company_scalers(key, ticker)
    return load_company_scalers(key, ticker)


def _output_prefix(key: str) -> str:
    return f"sector_{key}" if _is_sector(key) else key


def _load_intraday_for_eval(
    ticker: str,
    refresh: bool = False,
    period: str = "59d",
    interval: str = "5m",
) -> pd.DataFrame:
    if refresh:
        df_5m = refresh_intraday_cache(ticker=ticker, interval=interval, period=period, exchange="NSE")
    else:
        df_5m = load_cached_intraday(ticker=ticker, interval=interval)
    if df_5m is None or df_5m.empty:
        return pd.DataFrame()
    return resample_data(df_5m, "10min")


def _build_eval_samples(
    df_10m: pd.DataFrame,
    lookback: int = GROUP_LOOKBACK_WINDOW,
    days: int = 30,
):
    df_features = add_technical_indicators(df_10m)
    if df_features.empty:
        return tuple(np.array([]) for _ in range(5)) + ([], [])

    df_base = df_10m.loc[df_features.index]
    target_cols = ["Open", "High", "Low", "Close", "Volume"]
    feature_cols = df_features.columns.tolist()
    close_feature_idx = feature_cols.index("Close")
    cutoff = df_features.index.max() - pd.Timedelta(days=days)

    X, y_10m, y_30m, y_1h, current_close, timestamps = [], [], [], [], [], []
    max_steps = 6
    values = df_features[feature_cols].values

    for i in range(lookback - 1, len(df_features) - max_steps):
        ts = df_features.index[i]
        if ts < cutoff:
            continue

        seq = values[i - lookback + 1 : i + 1]
        t10 = df_base.iloc[i + 1][target_cols].values
        slice_30m = df_base.iloc[i + 1 : i + 4]
        slice_1h = df_base.iloc[i + 1 : i + 7]
        if len(slice_30m) < 3 or len(slice_1h) < 6:
            continue

        t30 = np.array(
            [
                slice_30m["Open"].iloc[0],
                slice_30m["High"].max(),
                slice_30m["Low"].min(),
                slice_30m["Close"].iloc[-1],
                slice_30m["Volume"].sum(),
            ]
        )
        t1h = np.array(
            [
                slice_1h["Open"].iloc[0],
                slice_1h["High"].max(),
                slice_1h["Low"].min(),
                slice_1h["Close"].iloc[-1],
                slice_1h["Volume"].sum(),
            ]
        )

        X.append(seq)
        y_10m.append(t10)
        y_30m.append(t30)
        y_1h.append(t1h)
        current_close.append(seq[-1, close_feature_idx])
        timestamps.append(ts)

    if not X:
        return tuple(np.array([]) for _ in range(5)) + (feature_cols, timestamps)

    return (
        np.array(X),
        np.array(y_10m),
        np.array(y_30m),
        np.array(y_1h),
        np.array(current_close),
        feature_cols,
        timestamps,
    )


def _align_and_scale_X(X: np.ndarray, feature_cols: List[str], feature_scaler):
    scaler_cols = (
        list(feature_scaler.feature_names_in_)
        if hasattr(feature_scaler, "feature_names_in_")
        else feature_cols
    )
    index_map = [feature_cols.index(c) for c in scaler_cols]
    X_aligned = X[:, :, index_map]
    n_samples, lookback, n_features = X_aligned.shape
    flat = X_aligned.reshape(-1, n_features)
    flat_scaled = feature_scaler.transform(flat)
    return flat_scaled.reshape(n_samples, lookback, n_features), scaler_cols


def _directional_accuracy(pred_close: np.ndarray, actual_close: np.ndarray, current_close: np.ndarray) -> float:
    pred_dir = np.sign(pred_close - current_close)
    true_dir = np.sign(actual_close - current_close)
    return float(np.mean(pred_dir == true_dir))


def _save_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _compute_explainability(
    model,
    X_scaled: np.ndarray,
    feature_cols: List[str],
    max_samples: int = 256,
) -> dict:
    if len(X_scaled) == 0:
        return {"method": "permutation_sensitivity", "top_features": []}

    sample_X = X_scaled[: min(len(X_scaled), max_samples)]
    baseline = model.predict(sample_X, verbose=0)
    baseline_close = np.stack([baseline[0][:, 3], baseline[1][:, 3], baseline[2][:, 3]], axis=1)

    importances = []
    for j, feat_name in enumerate(feature_cols):
        perturbed = sample_X.copy()
        fill_value = float(np.median(sample_X[:, :, j]))
        perturbed[:, :, j] = fill_value
        pert_pred = model.predict(perturbed, verbose=0)
        pert_close = np.stack([pert_pred[0][:, 3], pert_pred[1][:, 3], pert_pred[2][:, 3]], axis=1)
        score = float(np.mean(np.abs(pert_close - baseline_close)))
        importances.append((feat_name, score))

    total = sum(v for _, v in importances) or 1.0
    ranked = sorted(
        [{"feature": k, "importance": float(v / total)} for k, v in importances],
        key=lambda x: x["importance"],
        reverse=True,
    )
    return {"method": "permutation_sensitivity", "top_features": ranked}


def build_analytics(
    key: str,
    days: int = 30,
    refresh: bool = False,
    max_explain_samples: int = 256,
) -> bool:
    model_path = _model_path(key)
    if not os.path.exists(model_path):
        print(f"[{key}] model not found: {model_path}")
        return False

    model = load_model(model_path, compile=False)
    companies = _company_dict(key)[key]
    tickers = [c.ticker for c in companies]

    agg_pred = {"10m": [], "30m": [], "1h": []}
    agg_true = {"10m": [], "30m": [], "1h": []}
    agg_curr = {"10m": [], "30m": [], "1h": []}
    backtest_rows = []
    feature_importance_accum: Dict[str, float] = {}
    feature_importance_weight = 0
    companies_used = []

    for ticker in tickers:
        try:
            scalers = _load_scalers(key, ticker)
        except Exception as e:
            print(f"[{key}/{ticker}] scalers missing: {e}")
            continue

        df_10m = _load_intraday_for_eval(ticker=ticker, refresh=refresh)
        if df_10m.empty:
            print(f"[{key}/{ticker}] no intraday data")
            continue

        X, y_10m, y_30m, y_1h, current_close, feature_cols, timestamps = _build_eval_samples(
            df_10m, lookback=GROUP_LOOKBACK_WINDOW, days=days
        )
        if len(X) == 0:
            print(f"[{key}/{ticker}] no eval samples")
            continue

        X_scaled, scaler_cols = _align_and_scale_X(X, feature_cols, scalers["feature"])
        preds = model.predict(X_scaled, verbose=0)

        p10 = scalers["target_10m"].inverse_transform(preds[0])
        p30 = scalers["target_30m"].inverse_transform(preds[1])
        p1h = scalers["target_1h"].inverse_transform(preds[2])

        pred_close_10m, pred_close_30m, pred_close_1h = p10[:, 3], p30[:, 3], p1h[:, 3]
        true_close_10m, true_close_30m, true_close_1h = y_10m[:, 3], y_30m[:, 3], y_1h[:, 3]

        agg_pred["10m"].append(pred_close_10m)
        agg_pred["30m"].append(pred_close_30m)
        agg_pred["1h"].append(pred_close_1h)
        agg_true["10m"].append(true_close_10m)
        agg_true["30m"].append(true_close_30m)
        agg_true["1h"].append(true_close_1h)
        agg_curr["10m"].append(current_close)
        agg_curr["30m"].append(current_close)
        agg_curr["1h"].append(current_close)
        companies_used.append(ticker)

        explain = _compute_explainability(
            model=model,
            X_scaled=X_scaled,
            feature_cols=scaler_cols,
            max_samples=max_explain_samples,
        )
        sample_weight = len(X_scaled)
        feature_importance_weight += sample_weight
        for item in explain.get("top_features", []):
            feat = item["feature"]
            score = float(item["importance"]) * sample_weight
            feature_importance_accum[feat] = feature_importance_accum.get(feat, 0.0) + score

        for i, ts in enumerate(timestamps):
            backtest_rows.extend(
                [
                    {
                        "date": str(ts),
                        "ticker": ticker,
                        "horizon": "10m",
                        "predicted_close": float(pred_close_10m[i]),
                        "actual_close": float(true_close_10m[i]),
                        "error": float(pred_close_10m[i] - true_close_10m[i]),
                        "abs_error": float(abs(pred_close_10m[i] - true_close_10m[i])),
                        "direction_correct": int(np.sign(pred_close_10m[i] - current_close[i]) == np.sign(true_close_10m[i] - current_close[i])),
                    },
                    {
                        "date": str(ts),
                        "ticker": ticker,
                        "horizon": "30m",
                        "predicted_close": float(pred_close_30m[i]),
                        "actual_close": float(true_close_30m[i]),
                        "error": float(pred_close_30m[i] - true_close_30m[i]),
                        "abs_error": float(abs(pred_close_30m[i] - true_close_30m[i])),
                        "direction_correct": int(np.sign(pred_close_30m[i] - current_close[i]) == np.sign(true_close_30m[i] - current_close[i])),
                    },
                    {
                        "date": str(ts),
                        "ticker": ticker,
                        "horizon": "1h",
                        "predicted_close": float(pred_close_1h[i]),
                        "actual_close": float(true_close_1h[i]),
                        "error": float(pred_close_1h[i] - true_close_1h[i]),
                        "abs_error": float(abs(pred_close_1h[i] - true_close_1h[i])),
                        "direction_correct": int(np.sign(pred_close_1h[i] - current_close[i]) == np.sign(true_close_1h[i] - current_close[i])),
                    },
                ]
            )

    if not companies_used or not backtest_rows:
        print(f"[{key}] no usable company data for analytics")
        return False

    def _cat(values):
        return np.concatenate(values) if values else np.array([])

    p10_all, p30_all, p1h_all = _cat(agg_pred["10m"]), _cat(agg_pred["30m"]), _cat(agg_pred["1h"])
    y10_all, y30_all, y1h_all = _cat(agg_true["10m"]), _cat(agg_true["30m"]), _cat(agg_true["1h"])
    c10_all, c30_all, c1h_all = _cat(agg_curr["10m"]), _cat(agg_curr["30m"]), _cat(agg_curr["1h"])

    mae_10m = float(np.mean(np.abs(p10_all - y10_all)))
    mae_30m = float(np.mean(np.abs(p30_all - y30_all)))
    mae_1h = float(np.mean(np.abs(p1h_all - y1h_all)))
    dir_10m = _directional_accuracy(p10_all, y10_all, c10_all)
    dir_30m = _directional_accuracy(p30_all, y30_all, c30_all)
    dir_1h = _directional_accuracy(p1h_all, y1h_all, c1h_all)

    accuracy_payload = {
        "key": key,
        "window_days": days,
        "companies_used": sorted(companies_used),
        "sample_count": int(len(backtest_rows) // 3),
        "directional_accuracy": float(np.mean([dir_10m, dir_30m, dir_1h])),
        "mean_absolute_error": float(np.mean([mae_10m, mae_30m, mae_1h])),
        "horizons": {
            "10m": {"directional_accuracy": dir_10m, "mean_absolute_error": mae_10m},
            "30m": {"directional_accuracy": dir_30m, "mean_absolute_error": mae_30m},
            "1h": {"directional_accuracy": dir_1h, "mean_absolute_error": mae_1h},
        },
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    if feature_importance_weight > 0:
        ranked = sorted(
            [
                {"feature": k, "importance": float(v / feature_importance_weight)}
                for k, v in feature_importance_accum.items()
            ],
            key=lambda x: x["importance"],
            reverse=True,
        )
    else:
        ranked = []

    fmap = {item["feature"]: item["importance"] for item in ranked}
    explainability_payload = {
        "key": key,
        "method": "permutation_sensitivity_weighted",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "top_features": ranked[:10],
        "core_indicators": {
            "RSI": float(fmap.get("RSI", 0.0)),
            "SMA20": float(fmap.get("SMA_20", 0.0)),
            "ATR": float(fmap.get("ATR", 0.0)),
        },
        "RSI": float(fmap.get("RSI", 0.0)),
        "SMA20": float(fmap.get("SMA_20", 0.0)),
        "ATR": float(fmap.get("ATR", 0.0)),
    }

    backtest_df = pd.DataFrame(backtest_rows)
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    prefix = _output_prefix(key)
    accuracy_path = os.path.join(ANALYTICS_DIR, f"{prefix}_accuracy_30d.json")
    explainability_path = os.path.join(ANALYTICS_DIR, f"{prefix}_explainability.json")
    backtest_path = os.path.join(ANALYTICS_DIR, f"{prefix}_backtest.csv")

    _save_json(accuracy_path, accuracy_payload)
    _save_json(explainability_path, explainability_payload)
    backtest_df.to_csv(backtest_path, index=False)

    print(f"[{key}] saved -> {accuracy_path}")
    print(f"[{key}] saved -> {explainability_path}")
    print(f"[{key}] saved -> {backtest_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build analytics artifacts for group/sector models")
    parser.add_argument(
        "--group",
        default="all",
        choices=["all", *LEGACY_GROUP_KEYS, *SECTOR_KEYS],
    )
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--refresh", action="store_true", help="Refresh intraday cache before analytics")
    parser.add_argument("--max-explain-samples", type=int, default=256)
    args = parser.parse_args()

    if args.group == "all":
        keys = [*LEGACY_GROUP_KEYS, *SECTOR_KEYS]
    else:
        keys = [args.group]

    for key in keys:
        try:
            build_analytics(
                key=key,
                days=args.days,
                refresh=args.refresh,
                max_explain_samples=args.max_explain_samples,
            )
        except Exception as e:
            print(f"[{key}] failed: {e}")


if __name__ == "__main__":
    main()
