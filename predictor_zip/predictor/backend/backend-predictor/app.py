import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf
from keras.models import load_model

sys.path.append(os.getcwd())

from src.config import GROUP_LOOKBACK_WINDOW, MODELS_DIR, SECTOR_MODELS_DIR
from src.data_loader import get_ticker_symbol
from src.data_multi_horizon import generate_synthetic_data, resample_data
from src.group_dataset import load_company_scalers
from src.groups import (
    GROUP_A,
    GROUP_B,
    find_company_by_label as find_group_company_by_label,
    find_group_for_ticker,
    get_group_model_filename,
    list_company_labels as list_group_company_labels,
)
from src.preprocessing import add_technical_indicators
from src.sector_dataset import load_sector_company_scalers
from src.sectors import (
    SECTOR_COMPANIES,
    find_sector_company_by_label,
    find_sector_for_ticker,
    get_sector_model_filename,
    list_sector_company_labels,
)


def _ticker_from_label(label: str) -> Optional[str]:
    match = re.search(r"\(([^)]+)\)", label)
    if not match:
        return None
    return match.group(1).upper().strip()


def list_all_company_labels():
    labels = []
    seen_tickers = set()

    for label in list_sector_company_labels():
        t = _ticker_from_label(label)
        if t and t not in seen_tickers:
            labels.append(label)
            seen_tickers.add(t)

    legacy_group_a = os.path.join(MODELS_DIR, "group_models", get_group_model_filename(GROUP_A))
    legacy_group_b = os.path.join(MODELS_DIR, "group_models", get_group_model_filename(GROUP_B))
    legacy_group_a_root = os.path.join(MODELS_DIR, get_group_model_filename(GROUP_A))
    legacy_group_b_root = os.path.join(MODELS_DIR, get_group_model_filename(GROUP_B))
    legacy_available = any(
        os.path.exists(path)
        for path in [legacy_group_a, legacy_group_b, legacy_group_a_root, legacy_group_b_root]
    )
    if legacy_available:
        for label in list_group_company_labels():
            t = _ticker_from_label(label)
            if t and t not in seen_tickers:
                labels.append(label)
                seen_tickers.add(t)

    return labels


def infer_label_from_query(query: str, labels) -> Optional[str]:
    q = query.strip().lower()
    if not q:
        return None
    for label in labels:
        ticker = _ticker_from_label(label) or ""
        if ticker.lower() in q:
            return label
        if label.split("(")[0].strip().lower() in q:
            return label
    return None


def company_from_label(label: str) -> Tuple[Optional[str], Optional[str]]:
    sector_company = find_sector_company_by_label(label)
    if sector_company is not None:
        sector_key = find_sector_for_ticker(sector_company.ticker)
        return sector_company.ticker, sector_key
    group_company = find_group_company_by_label(label)
    if group_company is not None:
        group_key = find_group_for_ticker(group_company.ticker)
        return group_company.ticker, group_key
    return None, None


def _load_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _extract_metric(metrics: dict, candidates) -> Optional[float]:
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


def load_validation_mae_rupees(model_path: str, scalers: Dict[str, object]) -> Dict[str, Optional[float]]:
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


def load_model_and_scalers(selected_ticker: str):
    ticker = selected_ticker.upper().strip()

    # Sector-first routing.
    sector_key = find_sector_for_ticker(ticker)
    if sector_key:
        sector_model_path = os.path.join(SECTOR_MODELS_DIR, get_sector_model_filename(sector_key))
        if os.path.exists(sector_model_path):
            try:
                scalers = load_sector_company_scalers(sector_key, ticker)
                model = load_model(sector_model_path, compile=False)
                return model, scalers, sector_key, sector_model_path, "sector", f"sector_{sector_key}"
            except Exception:
                pass

    # Legacy fallback routing.
    group_key = find_group_for_ticker(ticker)
    if group_key:
        group_model_name = get_group_model_filename(group_key)
        model_candidates = [
            os.path.join(MODELS_DIR, "group_models", group_model_name),
            os.path.join(MODELS_DIR, group_model_name),
        ]
        for model_path in model_candidates:
            if not os.path.exists(model_path):
                continue
            try:
                scalers = load_company_scalers(group_key, ticker)
                model = load_model(model_path, compile=False)
                return model, scalers, group_key, model_path, "group", group_key
            except Exception:
                continue

    return None, None, None, None, None, None


def market_open_info():
    ist = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(ist)
    weekday = now_ist.weekday()
    market_start = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open = (weekday < 5) and (market_start <= now_ist <= market_end)
    return is_open, now_ist, market_start, market_end


def load_trust_metrics(analytics_key: str) -> Optional[dict]:
    return _load_json(os.path.join(MODELS_DIR, "analytics", f"{analytics_key}_accuracy_30d.json"))


def load_explainability_artifact(analytics_key: str) -> Optional[dict]:
    return _load_json(os.path.join(MODELS_DIR, "analytics", f"{analytics_key}_explainability.json"))


def load_backtest_artifact(analytics_key: str) -> Optional[pd.DataFrame]:
    path = os.path.join(MODELS_DIR, "analytics", f"{analytics_key}_backtest.csv")
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def render_confidence_band(label: str, pred_close: float, mae_rupees: Optional[float]):
    if mae_rupees is None:
        st.caption(f"{label} confidence band: unavailable (validation MAE metadata not found).")
        return
    low = pred_close - mae_rupees
    high = pred_close + mae_rupees
    st.caption(f"{label} confidence band (+/- MAE): Rs {low:.2f} to Rs {high:.2f}")


st.header("Indian Stock Market Multi-Horizon Predictor")
st.caption("Forecasts: 10m, 30m, 1h.")

with st.expander("Predictor Workflow", expanded=True):
    st.markdown(
        "- Layer 1 (Basic): session status, predictions, confidence range.\n"
        "- Layer 2 (Trust): optional 30-day directional accuracy and MAE.\n"
        "- Layer 3 (Deep Dive): explainability snapshot + backtest table."
    )

st.sidebar.header("Configuration")
demo_mode = st.sidebar.checkbox("Demo Mode (Use Synthetic Data)", value=False)
closed_market_mode = st.sidebar.selectbox(
    "When Market Is Closed",
    ["Simulation (allow predictions)", "Block predictions"],
)
show_accuracy_metrics = st.checkbox("Show accuracy metrics")

all_labels = list_all_company_labels()
query_text = st.text_input("User Query (optional)", "Predict the price of Infosys.")
prefill_label = infer_label_from_query(query_text, all_labels)
default_index = all_labels.index(prefill_label) if prefill_label in all_labels else 0

company_label = st.selectbox("Select Company", all_labels, index=default_index)
selected_ticker, mapped_key = company_from_label(company_label)
if selected_ticker is None:
    st.error("Invalid company selection.")
    st.stop()

stock = get_ticker_symbol(selected_ticker, exchange="NSE")
model, scalers, route_key, model_path, route_type, analytics_key = load_model_and_scalers(selected_ticker)
if model is None or scalers is None:
    st.error(
        "No matching sector/group model+scalers found for this ticker. "
        "Train sector models first, or keep legacy group artifacts available."
    )
    st.stop()

st.write(f"Analyzing: **{stock}**")
st.caption(f"Model: `{os.path.basename(model_path)}` | Lookback: `{GROUP_LOOKBACK_WINDOW}` candles")

if demo_mode:
    st.info("Using synthetic 5m data.")
    df_5m = generate_synthetic_data(length=1800, start_price=2500)
else:
    st.write("Fetching latest 5m candles...")
    try:
        df_5m = yf.download(stock, interval="5m", period="10d", progress=False, auto_adjust=True)
    except Exception:
        df_5m = None

if df_5m is None or df_5m.empty:
    st.error("Failed to fetch real data. Use Demo Mode if needed.")
    st.stop()

if hasattr(df_5m.columns, "nlevels") and df_5m.columns.nlevels > 1:
    df_5m.columns = df_5m.columns.get_level_values(0)

df_10m = resample_data(df_5m, "10min")
st.write(f"Processed {len(df_10m)} ten-minute candles.")
st.line_chart(df_10m["Close"])

try:
    df_features = add_technical_indicators(df_10m)
except Exception as e:
    st.error(f"Preprocessing error: {e}")
    st.stop()

if len(df_features) < GROUP_LOOKBACK_WINDOW:
    st.error(f"Not enough processed candles. Need at least {GROUP_LOOKBACK_WINDOW}.")
    st.stop()

feature_scaler = scalers["feature"]
feature_cols = (
    list(feature_scaler.feature_names_in_)
    if hasattr(feature_scaler, "feature_names_in_")
    else df_features.columns.tolist()
)
last_seq = df_features.iloc[-GROUP_LOOKBACK_WINDOW:][feature_cols]
input_seq = feature_scaler.transform(last_seq).reshape(1, GROUP_LOOKBACK_WINDOW, -1)

current_price = float(df_10m["Close"].iloc[-1])
is_market_open, now_ist, market_start, market_end = market_open_info()

status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    st.metric("Market Session", "OPEN" if is_market_open else "CLOSED")
with status_col2:
    st.metric("Current IST", now_ist.strftime("%H:%M:%S"))
with status_col3:
    st.metric("Session Window", f"{market_start:%H:%M} - {market_end:%H:%M}")

if demo_mode:
    st.warning("Demo mode enabled: predictions are simulation.")
elif not is_market_open:
    st.warning("Market is closed. Forecasts are hypothetical unless blocked.")
    if closed_market_mode == "Block predictions":
        st.subheader("Market Closed Snapshot")
        st.metric("Last Available Close", f"Rs {current_price:.2f}")
        st.stop()
else:
    st.success("Market is open. Running live-session forecast.")

preds = model.predict(input_seq, verbose=0)
p_10m = scalers["target_10m"].inverse_transform(preds[0])[0]
p_30m = scalers["target_30m"].inverse_transform(preds[1])[0]
p_1h = scalers["target_1h"].inverse_transform(preds[2])[0]
mae_rupees = load_validation_mae_rupees(model_path, scalers)

st.subheader("Multi-Horizon Forecasts (OHLCV)")
c1, c2, c3 = st.columns(3)

with c1:
    close_10m = float(p_10m[3])
    st.markdown("### 10 Min")
    st.metric("Close", f"Rs {close_10m:.2f}", f"{(close_10m - current_price):.2f}")
    st.write(f"High: {p_10m[1]:.2f}")
    st.write(f"Low: {p_10m[2]:.2f}")
    st.write(f"Volume: {p_10m[4]:.0f}")
    render_confidence_band("10m", close_10m, mae_rupees.get("10m"))

with c2:
    close_30m = float(p_30m[3])
    st.markdown("### 30 Min")
    st.metric("Close", f"Rs {close_30m:.2f}", f"{(close_30m - current_price):.2f}")
    st.write(f"High: {p_30m[1]:.2f}")
    st.write(f"Low: {p_30m[2]:.2f}")
    st.write(f"Volume: {p_30m[4]:.0f}")
    render_confidence_band("30m", close_30m, mae_rupees.get("30m"))

with c3:
    close_1h = float(p_1h[3])
    st.markdown("### 1 Hour")
    st.metric("Close", f"Rs {close_1h:.2f}", f"{(close_1h - current_price):.2f}")
    st.write(f"High: {p_1h[1]:.2f}")
    st.write(f"Low: {p_1h[2]:.2f}")
    st.write(f"Volume: {p_1h[4]:.0f}")
    render_confidence_band("1h", close_1h, mae_rupees.get("1h"))

st.success(
    f"Predicted close: 10m -> Rs {p_10m[3]:.2f}, "
    f"30m -> Rs {p_30m[3]:.2f}, 1h -> Rs {p_1h[3]:.2f}"
)

if show_accuracy_metrics:
    st.subheader("Trust Metrics (Last 30 Days)")
    trust_metrics = load_trust_metrics(analytics_key)
    if trust_metrics is None:
        st.info(f"Expected `models/analytics/{analytics_key}_accuracy_30d.json`.")
    else:
        st.json(trust_metrics)

with st.expander("See detailed explanation", expanded=False):
    st.markdown("**Explainability Snapshot**")
    explainability = load_explainability_artifact(analytics_key)
    if explainability is None:
        st.info(f"Expected `models/analytics/{analytics_key}_explainability.json`.")
    else:
        if "core_indicators" in explainability and isinstance(explainability["core_indicators"], dict):
            st.write("Core indicators (importance):")
            st.json(explainability["core_indicators"])
        if "top_features" in explainability and isinstance(explainability["top_features"], list):
            st.dataframe(pd.DataFrame(explainability["top_features"]), use_container_width=True)
        else:
            st.json(explainability)

    st.markdown("**Backtest Comparison (Recent Predictions vs Actuals)**")
    backtest_df = load_backtest_artifact(analytics_key)
    if backtest_df is None or backtest_df.empty:
        st.info(f"Expected `models/analytics/{analytics_key}_backtest.csv`.")
    else:
        st.dataframe(backtest_df.tail(20), use_container_width=True)
        if "error" in backtest_df.columns:
            st.write(f"Error MAE: Rs {backtest_df['error'].abs().mean():.2f}")
