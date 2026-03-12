import argparse
import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import INTERVALS, LOOKBACK_WINDOW, TARGET_HORIZON
from src.data_loader import fetch_data, save_data, load_data
from src.preprocessing import prepare_data
from src.model_lstm import build_lstm_model, save_model
from src.model_transformer import build_transformer_model, save_transformer_model

def train_model(ticker, interval="1h", epochs=50, batch_size=32, model_type="lstm"):
    print(f"Starting training for {ticker} ({interval}) using {model_type.upper()}...")
    
    # 1. Fetch Data
    filename = f"{ticker}_{interval}.csv"
    df = load_data(filename)
    if df is None:
        # Determine appropriate period based on interval
        if interval in ["1m", "2m", "5m", "15m", "30m", "90m"]:
            period = "59d" # yfinance limit is 60d
        elif interval == "1h":
            period = "729d" # yfinance limit is 730d
        else:
            period = "max"
            
        df = fetch_data(ticker, interval=interval, period=period)
        if df is not None:
            save_data(df, filename)
        else:
            print("Failed to fetch data.")
            return None
            
    # 2. Preprocess Data
    try:
        X_train, y_train, X_test, y_test, feature_scaler, target_scaler = prepare_data(
            df, seq_length=LOOKBACK_WINDOW, prediction_window=TARGET_HORIZON
        )
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None
    
    print(f"Training Data Shape: X={X_train.shape}, y={y_train.shape}")
    print(f"Testing Data Shape: X={X_test.shape}, y={y_test.shape}")
    
    if len(X_train) == 0:
        print("Not enough data to train.")
        return None

    # 3. Build Model
    input_shape = (X_train.shape[1], X_train.shape[2])
    
    if model_type.lower() == "transformer":
        model = build_transformer_model(input_shape)
        model_filename = f"transformer_{ticker}_{interval}.h5"
        save_func = save_transformer_model
    else:
        model = build_lstm_model(input_shape)
        model_filename = f"lstm_{ticker}_{interval}.h5"
        save_func = save_model
    
    # 4. Train Model
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.1,
        verbose=1
    )
    
    # 5. Evaluate
    loss, mae = model.evaluate(X_test, y_test)
    print(f"Test Loss (MSE): {loss:.4f}, Test MAE: {mae:.4f}")
    
    # 6. Save Model
    save_func(model, model_filename)
    
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Model for Stock Prediction')
    parser.add_argument('--ticker', type=str, default='RELIANCE', help='Stock Ticker')
    parser.add_argument('--interval', type=str, default='1h', help='Interval (10m, 30m, 1h)')
    parser.add_argument('--epochs', type=int, default=20, help='Epochs')
    parser.add_argument('--model', type=str, default='lstm', help='Model Type (lstm, transformer)')
    
    args = parser.parse_args()
    
    train_model(args.ticker, args.interval, args.epochs, model_type=args.model)
