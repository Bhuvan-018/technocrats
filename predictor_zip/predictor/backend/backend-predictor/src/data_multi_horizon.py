import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.preprocessing import add_technical_indicators

def resample_data(df, interval):
    """
    Resample 1m/5m data to higher timeframes (10m, 30m, 1h).
    df index must be DatetimeIndex.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if not isinstance(df.index, pd.DatetimeIndex):
        date_cols = [c for c in ["Datetime", "Date", "date", "timestamp", "Timestamp"] if c in df.columns]
        if date_cols:
            col = date_cols[0]
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            df = df.dropna(subset=[col]).set_index(col)
        else:
            parsed_index = pd.to_datetime(df.index, errors="coerce", utc=True)
            valid = ~parsed_index.isna()
            df = df.loc[valid].copy()
            df.index = parsed_index[valid]

    if not isinstance(df.index, pd.DatetimeIndex) or len(df) == 0:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    if not set(required_cols).issubset(df.columns):
        return pd.DataFrame(columns=required_cols)

    df = df[required_cols].copy()
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df = df[df["Volume"] > 0]
    df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()

    # Define aggregation rules
    agg_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }
    
    # Resample
    df_resampled = df.resample(interval).agg(agg_dict)
    
    # Drop NaN rows (e.g. gaps in trading hours)
    df_resampled.dropna(inplace=True)
    if len(df_resampled) == 0:
        return pd.DataFrame(columns=required_cols)
    
    return df_resampled

def prepare_multi_horizon_data(df_base, lookback=60):
    """
    Prepare data for multi-horizon forecasting.
    Input: Base dataframe (e.g., 5m or 10m data).
    Outputs:
        X: Sequence of past candles (from base interval)
        y_10m: Next 10m candle (OHLCV)
        y_30m: Next 30m candle (OHLCV)
        y_1h: Next 1h candle (OHLCV)
    
    We assume df_base is already at the lowest common denominator or we resample from it.
    Let's assume df_base is 10m data (resampled from 1m/5m if needed).
    """
    # 1. Ensure df_base is 10m
    # If not, the user should provide 1m/5m and we resample to 10m first as the "base" step
    # But for simplicity, let's assume we work with a base 10m dataframe.
    
    # 2. Generate higher timeframe targets
    # We need to look ahead.
    # For a given time T (index i), we want:
    # - y_10m: The candle at T+10m (which is just the next row in 10m data)
    # - y_30m: The aggregate of next 3 candles (10m * 3)
    # - y_1h: The aggregate of next 6 candles (10m * 6)
    
    # Add indicators to base data for input features
    df_features = add_technical_indicators(df_base)
    
    # Prepare targets
    targets_10m = []
    targets_30m = []
    targets_1h = []
    valid_indices = []
    
    # Columns to predict
    target_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Iterate through the dataframe
    # We need enough future data for the largest horizon (1h = 6 steps of 10m)
    max_steps = 6
    
    for i in range(len(df_features) - max_steps):
        # Current time T is at index i.
        # Input sequence ends at i.
        # y_10m is at i+1
        
        # 10m Target (Next step)
        t_10m = df_base.iloc[i+1][target_cols].values
        
        # 30m Target (Next 3 steps)
        slice_30m = df_base.iloc[i+1 : i+4]
        if len(slice_30m) < 3:
            continue
            
        t_30m = [
            slice_30m['Open'].iloc[0],
            slice_30m['High'].max(),
            slice_30m['Low'].min(),
            slice_30m['Close'].iloc[-1],
            slice_30m['Volume'].sum()
        ]
        
        # 1h Target (Next 6 steps)
        slice_1h = df_base.iloc[i+1 : i+7]
        if len(slice_1h) < 6:
            continue
            
        t_1h = [
            slice_1h['Open'].iloc[0],
            slice_1h['High'].max(),
            slice_1h['Low'].min(),
            slice_1h['Close'].iloc[-1],
            slice_1h['Volume'].sum()
        ]
        
        targets_10m.append(t_10m)
        targets_30m.append(t_30m)
        targets_1h.append(t_1h)
        valid_indices.append(i)
        
    # Create Inputs X corresponding to valid_indices
    # X needs `lookback` past candles ending at `i`
    # So we need i >= lookback-1
    
    X = []
    final_y_10m = []
    final_y_30m = []
    final_y_1h = []
    
    # Feature columns (OHLCV + Indicators)
    feature_cols = df_features.columns.tolist()
    data_values = df_features[feature_cols].values
    
    for idx, i in enumerate(valid_indices):
        if i < lookback - 1:
            continue
            
        # Sequence from i-lookback+1 to i (inclusive)
        seq = data_values[i-lookback+1 : i+1]
        X.append(seq)
        
        final_y_10m.append(targets_10m[idx])
        final_y_30m.append(targets_30m[idx])
        final_y_1h.append(targets_1h[idx])
        
    return np.array(X), np.array(final_y_10m), np.array(final_y_30m), np.array(final_y_1h)

def generate_synthetic_data(length=10000, start_price=2500):
    """
    Generate synthetic 5m OHLCV data for testing when API fails.
    """
    print("Generating synthetic data for testing...")
    
    # Generate random walk for Close price
    np.random.seed(42)
    returns = np.random.normal(0, 0.001, length)
    price = start_price * np.exp(np.cumsum(returns))
    
    # Create OHLCV
    high = price * (1 + np.abs(np.random.normal(0, 0.0005, length)))
    low = price * (1 - np.abs(np.random.normal(0, 0.0005, length)))
    open_p = price * (1 + np.random.normal(0, 0.0002, length))
    volume = np.random.randint(1000, 100000, length)
    
    # Ensure High is highest and Low is lowest
    high = np.maximum(high, np.maximum(open_p, price))
    low = np.minimum(low, np.minimum(open_p, price))
    
    # Create DataFrame
    # 5m intervals
    dates = pd.date_range(end=pd.Timestamp.now(), periods=length, freq='5min')
    
    df = pd.DataFrame({
        'Open': open_p,
        'High': high,
        'Low': low,
        'Close': price,
        'Volume': volume
    }, index=dates)
    
    return df

def load_and_process_multitimeframe(ticker, period='59d'):
    """
    Fetch 5m data (max 60d) and process into multi-horizon dataset.
    """
    import yfinance as yf
    
    # Attempt to patch cache (simplified)
    try:
        import yfinance.cache
        # If we can't access TzCache, maybe it's renamed or different structure
        # We'll just ignore if it fails
    except:
        pass

    from src.data_loader import get_ticker_symbol
    
    symbol = get_ticker_symbol(ticker, "NSE")
    print(f"Fetching 5m data for {symbol}...")
    
    df = pd.DataFrame()
    
    try:
        # Try fetching data
        df = yf.download(symbol, interval="5m", period=period, progress=False, auto_adjust=True)
    except Exception as e:
        print(f"yfinance download failed: {e}")

    # Check if data is valid
    if df.empty or 'Close' not in df.columns:
        print("Real data fetch failed. Falling back to SYNTHETIC DATA for demonstration.")
        df = generate_synthetic_data()
        
    # Handle MultiIndex columns if present (yfinance sometimes returns them)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    # Resample to 10m as base
    print("Resampling to 10m base...")
    df_10m = resample_data(df, '10min')
    
    return df_10m
