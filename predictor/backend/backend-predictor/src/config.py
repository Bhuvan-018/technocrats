import os

# Resolve all paths relative to backend-predictor root, not current working directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Data Configuration
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
GROUP_MODELS_DIR = os.path.join(MODELS_DIR, 'group_models')
SECTOR_MODELS_DIR = os.path.join(MODELS_DIR, 'sector_models')
ANALYTICS_DIR = os.path.join(MODELS_DIR, 'analytics')
GROUP_SCALERS_DIR = os.path.join(MODELS_DIR, 'group_scalers')
SECTOR_SCALERS_DIR = os.path.join(MODELS_DIR, 'sector_scalers')
MODEL_ARCHIVE_DIR = os.path.join(MODELS_DIR, 'archive')
LEGACY_ARCHIVE_DIR = os.path.join(MODELS_DIR, 'legacy_archive')
TRAINING_LOGS_DIR = os.path.join(MODELS_DIR, 'training_logs')
CHECKPOINTS_DIR = os.path.join(MODELS_DIR, 'checkpoints')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(GROUP_MODELS_DIR, exist_ok=True)
os.makedirs(SECTOR_MODELS_DIR, exist_ok=True)
os.makedirs(ANALYTICS_DIR, exist_ok=True)
os.makedirs(GROUP_SCALERS_DIR, exist_ok=True)
os.makedirs(SECTOR_SCALERS_DIR, exist_ok=True)
os.makedirs(MODEL_ARCHIVE_DIR, exist_ok=True)
os.makedirs(LEGACY_ARCHIVE_DIR, exist_ok=True)
os.makedirs(TRAINING_LOGS_DIR, exist_ok=True)
os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

# Market Configuration
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"

# User Requirements: 10m, 30m, 1h forecasts
INTERVALS = ["10m", "30m", "1h"]
DEFAULT_PERIOD = "60d"  # For intraday data, yfinance has limits (7d for 1m, 60d for <1h)
# Note: 1h data is available for 730d (2 years)

# Model Configuration
LOOKBACK_WINDOW = 60  # Number of past candles to look at
GROUP_LOOKBACK_WINDOW = 100  # Grouped model lookback for multi-company training
TARGET_HORIZON = 1    # Number of steps ahead to predict
TEST_SIZE = 0.2       # 20% for testing (time-based split)
VALIDATION_SIZE = 0.1 # 10% for validation

# Features
FEATURES = ['Open', 'High', 'Low', 'Close', 'Volume']
TARGET_COLUMNS = ['Open', 'High', 'Low', 'Close']  # Predicting OHLC
