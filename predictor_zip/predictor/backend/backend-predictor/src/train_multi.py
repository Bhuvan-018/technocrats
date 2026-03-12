import argparse
import pandas as pd
import numpy as np
import os
import sys
import joblib
from sklearn.preprocessing import MinMaxScaler

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR, LOOKBACK_WINDOW
from src.data_multi_horizon import load_and_process_multitimeframe, prepare_multi_horizon_data
from src.model_multi_head import build_multi_head_transformer, save_multi_head_model

def train_multi_horizon_model(ticker, epochs=50, batch_size=32):
    print(f"Starting Multi-Horizon Training for {ticker}...")
    
    # 1. Fetch Data
    # We fetch 5m data and resample to 10m as base
    # Max period for 5m is 60d
    df_base = load_and_process_multitimeframe(ticker, period='59d')
    
    if df_base is None or df_base.empty:
        print("Failed to fetch data.")
        return None
        
    print(f"Base Data (10m) Shape: {df_base.shape}")
    
    # 2. Prepare Data (Sequences & Targets)
    X, y_10m, y_30m, y_1h = prepare_multi_horizon_data(df_base, lookback=LOOKBACK_WINDOW)
    
    print(f"Processed Samples: {len(X)}")
    if len(X) == 0:
        print("Not enough data after processing.")
        return None
        
    # 3. Scaling
    # We need separate scalers for input features and each target horizon
    
    # Input Scaler
    # X is (samples, lookback, features)
    # We flatten to fit scaler, then reshape back
    num_samples, lookback, num_features = X.shape
    X_flat = X.reshape(-1, num_features)
    
    feature_scaler = MinMaxScaler(feature_range=(0, 1))
    X_scaled_flat = feature_scaler.fit_transform(X_flat)
    X_scaled = X_scaled_flat.reshape(num_samples, lookback, num_features)
    
    # Target Scalers
    # Targets are (samples, 5) -> OHLCV
    scaler_10m = MinMaxScaler(feature_range=(0, 1))
    y_10m_scaled = scaler_10m.fit_transform(y_10m)
    
    scaler_30m = MinMaxScaler(feature_range=(0, 1))
    y_30m_scaled = scaler_30m.fit_transform(y_30m)
    
    scaler_1h = MinMaxScaler(feature_range=(0, 1))
    y_1h_scaled = scaler_1h.fit_transform(y_1h)
    
    # Save Scalers
    scaler_prefix = f"{ticker}_multi"
    joblib.dump(feature_scaler, os.path.join(MODELS_DIR, f'{scaler_prefix}_feature_scaler.pkl'))
    joblib.dump(scaler_10m, os.path.join(MODELS_DIR, f'{scaler_prefix}_target_10m_scaler.pkl'))
    joblib.dump(scaler_30m, os.path.join(MODELS_DIR, f'{scaler_prefix}_target_30m_scaler.pkl'))
    joblib.dump(scaler_1h, os.path.join(MODELS_DIR, f'{scaler_prefix}_target_1h_scaler.pkl'))
    
    # 4. Train/Test Split
    test_split = 0.2
    split_idx = int(len(X) * (1 - test_split))
    
    X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
    
    y_train_10m, y_test_10m = y_10m_scaled[:split_idx], y_10m_scaled[split_idx:]
    y_train_30m, y_test_30m = y_30m_scaled[:split_idx], y_30m_scaled[split_idx:]
    y_train_1h, y_test_1h = y_1h_scaled[:split_idx], y_1h_scaled[split_idx:]
    
    # 5. Build Model
    input_shape = (lookback, num_features)
    model = build_multi_head_transformer(input_shape, output_units=5) # 5 units for OHLCV
    
    # 6. Train
    # Targets are passed as a dictionary matching output layer names
    train_targets = {
        'forecast_10m': y_train_10m,
        'forecast_30m': y_train_30m,
        'forecast_1h': y_train_1h
    }
    
    test_targets = {
        'forecast_10m': y_test_10m,
        'forecast_30m': y_test_30m,
        'forecast_1h': y_test_1h
    }
    
    history = model.fit(
        X_train, train_targets,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test, test_targets),
        verbose=1
    )
    
    # 7. Evaluate
    results = model.evaluate(X_test, test_targets)
    print("Evaluation Results:", results)
    
    # 8. Save Model
    model_filename = f"transformer_{ticker}_multi.keras"
    save_multi_head_model(model, model_filename)
    
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Multi-Horizon Transformer')
    parser.add_argument('--ticker', type=str, default='RELIANCE', help='Stock Ticker')
    parser.add_argument('--epochs', type=int, default=50, help='Epochs')
    
    args = parser.parse_args()
    
    train_multi_horizon_model(args.ticker, args.epochs)
