import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR

def add_technical_indicators(df):
    """
    Calculate and add technical indicators to the DataFrame.
    """
    df = df.copy()
    
    # Ensure no NaN values initially
    df.dropna(inplace=True)
    
    # Ensure columns are 1D series
    if isinstance(df['Close'], pd.DataFrame):
         df['Close'] = df['Close'].iloc[:, 0]
    if isinstance(df['High'], pd.DataFrame):
         df['High'] = df['High'].iloc[:, 0]
    if isinstance(df['Low'], pd.DataFrame):
         df['Low'] = df['Low'].iloc[:, 0]
    if isinstance(df['Volume'], pd.DataFrame):
         df['Volume'] = df['Volume'].iloc[:, 0]
         
    # Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    df['MACD'] = macd
    df['Signal_Line'] = signal
    
    # Bollinger Bands
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + 2 * bb_std
    df['BB_Lower'] = df['SMA_20'] - 2 * bb_std
    
    # Volume MA
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    
    # Momentum (Rate of Change)
    df['ROC'] = df['Close'].pct_change(periods=10) * 100
    
    # Volatility (ATR - Average True Range) - Simplified
    # Use iloc or numpy to avoid index alignment issues if dataframe has duplicate columns/indices? No, should be fine.
    # Just ensuring we are doing series operations.
    high_low = df['High'] - df['Low']
    # Use abs() from numpy or pandas
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    # axis=1 max might return a series, which is what we want.
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()

    # Lagged return and momentum features
    close_safe = df['Close'].replace(0, np.nan)
    vol_safe = df['Volume'].replace(0, np.nan)
    df['Return_1'] = np.log(close_safe / close_safe.shift(1))
    df['Return_5'] = np.log(close_safe / close_safe.shift(5))
    df['Return_10'] = np.log(close_safe / close_safe.shift(10))
    df['Momentum_5'] = df['Close'] - df['Close'].shift(5)
    df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
    df['Volume_Change_1'] = np.log(vol_safe / vol_safe.shift(1))
    df['Volume_Change_5'] = np.log(vol_safe / vol_safe.shift(5))

    # Rolling volatility and regime-strength proxies
    df['Volatility_10'] = df['Return_1'].rolling(window=10).std()
    df['Volatility_20'] = df['Return_1'].rolling(window=20).std()
    df['Range_Pct'] = (df['High'] - df['Low']) / close_safe
    df['ATR_Pct'] = df['ATR'] / close_safe
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / close_safe
    df['Close_vs_SMA20'] = (df['Close'] - df['SMA_20']) / close_safe
    
    # Guard against inf from divide/log then drop incomplete rows from rolling windows.
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    return df

def create_sequences(features, targets, seq_length, prediction_window=1):
    """
    Create sequences for LSTM training.
    
    Args:
        features (np.array): Scaled feature data.
        targets (np.array): Scaled target data.
        seq_length (int): Lookback window size.
        prediction_window (int): Steps ahead to predict.
        
    Returns:
        X (np.array): Sequences of shape (samples, seq_length, num_features)
        y (np.array): Targets of shape (samples, prediction_window, num_targets) or (samples, num_targets) if window=1
    """
    xs, ys = [], []
    # Ensure we don't go out of bounds
    # We need seq_length past points for X, and prediction_window future points for y
    for i in range(len(features) - seq_length - prediction_window + 1):
        x = features[i:(i + seq_length)]
        y = targets[(i + seq_length):(i + seq_length + prediction_window)]
        
        xs.append(x)
        ys.append(y)
        
    X = np.array(xs)
    y = np.array(ys)
    
    # If prediction window is 1, flatten y to (samples, num_targets)
    if prediction_window == 1:
        y = y.reshape(y.shape[0], y.shape[2])
        
    return X, y

def prepare_data(df, seq_length=60, prediction_window=1, test_size=0.2, target_cols=['Open', 'High', 'Low', 'Close']):
    """
    Prepare data for LSTM model: Feature engineering, scaling, sequence creation, train/test split.
    """
    # 1. Feature Engineering
    df_processed = add_technical_indicators(df)
    
    # 2. Split Data (Time-based)
    train_size = int(len(df_processed) * (1 - test_size))
    train_df = df_processed.iloc[:train_size]
    test_df = df_processed.iloc[train_size:]
    
    # 3. Define Features and Targets
    feature_cols = df_processed.columns.tolist()
    
    # 4. Scaling
    # Feature Scaler
    feature_scaler = MinMaxScaler(feature_range=(0, 1))
    train_features = feature_scaler.fit_transform(train_df[feature_cols])
    test_features = feature_scaler.transform(test_df[feature_cols])
    
    # Target Scaler (for inverse transform of predictions)
    target_scaler = MinMaxScaler(feature_range=(0, 1))
    train_targets = target_scaler.fit_transform(train_df[target_cols])
    test_targets = target_scaler.transform(test_df[target_cols])
    
    # 5. Create Sequences
    X_train, y_train = create_sequences(train_features, train_targets, seq_length, prediction_window)
    X_test, y_test = create_sequences(test_features, test_targets, seq_length, prediction_window)
    
    # Save scalers for later use (inference)
    joblib.dump(feature_scaler, os.path.join(MODELS_DIR, 'feature_scaler.pkl'))
    joblib.dump(target_scaler, os.path.join(MODELS_DIR, 'target_scaler.pkl'))
    
    return X_train, y_train, X_test, y_test, feature_scaler, target_scaler
