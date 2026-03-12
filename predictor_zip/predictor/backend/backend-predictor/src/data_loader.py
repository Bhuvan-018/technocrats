import yfinance as yf
import pandas as pd
import os
import sys

# Add src to path if running directly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import DATA_DIR, NSE_SUFFIX, BSE_SUFFIX

def get_ticker_symbol(symbol, exchange="NSE"):
    """
    Format the ticker symbol for yfinance based on the exchange.
    """
    symbol = symbol.upper()
    # If the user provides a symbol that already has a suffix, trust it.
    if "." in symbol:
        return symbol
        
    # Check if it's a known US tech stock, if so, don't append suffix
    # This is a hack for the specific user request involving GOOG
    if symbol in ['GOOG', 'AAPL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA']:
        return symbol
        
    if exchange == "NSE":
        if not symbol.endswith(NSE_SUFFIX):
            return f"{symbol}{NSE_SUFFIX}"
    elif exchange == "BSE":
        if not symbol.endswith(BSE_SUFFIX):
            return f"{symbol}{BSE_SUFFIX}"
    return symbol

def fetch_data(symbol, interval="1h", period="1y", exchange="NSE"):
    """
    Fetch historical data from Yahoo Finance.
    
    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE').
        interval (str): Data interval (e.g., '1m', '5m', '1h', '1d').
        period (str): Data period to download (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max').
        exchange (str): 'NSE' or 'BSE'.
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data.
    """
    ticker = get_ticker_symbol(symbol, exchange)
    print(f"Fetching data for {ticker} with interval {interval} and period {period}...")
    
    try:
        # Try to use a temporary cache directory for yfinance
        import os
        # Set cache dir to a local folder in the project to avoid system permission issues
        # yfinance uses 'py-yfinance' folder in the cache dir
        local_cache = os.path.join(os.getcwd(), 'cache')
        if not os.path.exists(local_cache):
            os.makedirs(local_cache)
            
        # This environment variable might be respected by platformdirs or yfinance?
        # Actually yfinance uses platformdirs.user_cache_dir().
        # We can try to monkeypatch platformdirs? No, too complex.
        # But wait, yfinance Ticker() doesn't seem to have a cache_dir argument.
        
        # Let's try to monkeypatch yfinance.utils.get_yf_cache_dir?
        # Or just use the Ticker object which should isolate some state?
        
        # Another attempt: Use a custom session that DOES NOT cache?
        # We tried requests_cache.CachedSession(backend='memory'), but yfinance complained about curl_cffi.
        
        # Let's try to just use download() but catch the exception and print a helpful message if it fails.
        # But we need it to work.
        
        # Critical Hack: Force yfinance to NOT use cache by not using the session?
        # The error "unable to open database file" comes from sqlite.
        # It seems yfinance is trying to use a cache by default?
        # If we can't disable it, maybe we can redirect it.
        
        # Let's try to use `requests` to fetch data manually if yfinance fails?
        # No, that's reinventing the wheel.
        
        # What if we use `yf.set_tz_cache_location`?
        try:
             yf.set_tz_cache_location(os.path.join(os.getcwd(), 'cache'))
        except:
             pass
             
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return None
            
        # Standardize columns
        # yfinance might return multi-index columns if multiple tickers, but here we fetch one.
        # It usually returns: Open, High, Low, Close, Volume
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.reset_index(inplace=True)
        
        # Rename columns to standard names
        # Usually Date or Datetime
        date_col = [c for c in df.columns if 'Date' in c or 'Time' in c][0]
        df.rename(columns={date_col: 'Datetime'}, inplace=True)
        
        # Ensure Datetime is timezone aware and converted to IST
        if df['Datetime'].dt.tz is None:
            # Assume UTC if no tz, but yfinance usually returns localized or UTC
            # For Indian markets, it might be safer to localize to UTC then convert to IST
            # But yfinance usually returns exchange time for non-US? Let's check.
            # Actually yfinance returns UTC for intraday.
             df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')
             
        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
        
        # Set index
        df.set_index('Datetime', inplace=True)
        
        # Basic cleaning: Remove rows with 0 volume (unless it's an index) or NaN prices
        df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)
        df = df[df['Volume'] > 0]
        
        return df
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def save_data(df, filename):
    """Save DataFrame to CSV in data directory."""
    path = os.path.join(DATA_DIR, filename)
    df.to_csv(path)
    print(f"Data saved to {path}")

def load_data(filename):
    """Load DataFrame from CSV in data directory."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path, index_col='Datetime', parse_dates=True)
        return df
    else:
        print(f"File {path} not found.")
        return None

if __name__ == "__main__":
    # Test fetch
    df = fetch_data("RELIANCE", interval="1h", period="1y")
    if df is not None:
        print(df.head())
        save_data(df, "RELIANCE_1h.csv")
