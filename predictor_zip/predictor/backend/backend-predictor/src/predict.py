import argparse
import pandas as pd
import numpy as np
import joblib
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR, LOOKBACK_WINDOW
from src.data_loader import fetch_data
from src.preprocessing import add_technical_indicators
from src.model_lstm import load_custom_model

def predict_next_ohlc(ticker, interval="1h"):
    print(f"Generating prediction for {ticker} ({interval})...")
    
    # 1. Load Model and Scalers
    model_path = f"lstm_{ticker}_{interval}.h5"
    model = load_custom_model(model_path)
    if model is None:
        print("Model not found. Please train first.")
        return None
        
    try:
        feature_scaler = joblib.load(os.path.join(MODELS_DIR, 'feature_scaler.pkl'))
        target_scaler = joblib.load(os.path.join(MODELS_DIR, 'target_scaler.pkl'))
    except Exception as e:
        print(f"Error loading scalers: {e}")
        return None
    
    # 2. Fetch Latest Data
    # We need enough data for lookback + indicators calculation (e.g. SMA50 needs 50)
    # So fetch LOOKBACK_WINDOW + 50 + buffer = 150 points
    # For intraday, yfinance limit for 1m is 7d, for <1h is 60d.
    if interval in ["1m", "2m", "5m", "15m", "30m", "90m"]:
        period = "59d"
    elif interval == "1h":
        period = "729d" # 2 years
    else:
        period = "1y"
        
    df = fetch_data(ticker, interval=interval, period=period)
    
    if df is None or len(df) < LOOKBACK_WINDOW + 50:
        print("Not enough recent data.")
        return None
        
    # 3. Preprocess
    try:
        df_processed = add_technical_indicators(df)
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None
    
    # Use the last LOOKBACK_WINDOW points
    last_sequence_df = df_processed.tail(LOOKBACK_WINDOW)
    
    # Scale features
    try:
        features = feature_scaler.transform(last_sequence_df)
    except ValueError as e:
        print(f"Feature mismatch: {e}")
        print(f"Expected {feature_scaler.n_features_in_} features, got {last_sequence_df.shape[1]}")
        return None
    
    # Reshape for LSTM (1, lookback, features)
    input_sequence = features.reshape(1, LOOKBACK_WINDOW, features.shape[1])
    
    # 4. Predict
    prediction_scaled = model.predict(input_sequence)
    
    # 5. Inverse Transform
    prediction = target_scaler.inverse_transform(prediction_scaled)
    
    # Output
    ohlc = prediction[0]
    print(f"\nPrediction for next {interval} candle:")
    print(f"Open: {ohlc[0]:.2f}")
    print(f"High: {ohlc[1]:.2f}")
    print(f"Low:  {ohlc[2]:.2f}")
    print(f"Close:{ohlc[3]:.2f}")
    
    return ohlc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict Next OHLC')
    parser.add_argument('--ticker', type=str, default='RELIANCE', help='Stock Ticker')
    parser.add_argument('--interval', type=str, default='1h', help='Interval (10m, 30m, 1h)')
    
    args = parser.parse_args()
    
    predict_next_ohlc(args.ticker, args.interval)
