import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR

def build_lstm_model(input_shape, output_units=4, units=[64, 64], dropout_rate=0.2, learning_rate=0.001):
    """
    Build LSTM model for OHLC prediction.
    
    Args:
        input_shape (tuple): (lookback_window, num_features)
        output_units (int): Number of output units (4 for OHLC)
        units (list): List of units for each LSTM layer
        dropout_rate (float): Dropout rate
        learning_rate (float): Learning rate
        
    Returns:
        model: Keras model
    """
    model = Sequential()
    
    # Input Layer
    model.add(Input(shape=input_shape))
    
    # Hidden LSTM Layers
    for i, u in enumerate(units):
        return_sequences = (i < len(units) - 1) # True for all except last LSTM layer
        model.add(LSTM(units=u, return_sequences=return_sequences))
        model.add(Dropout(dropout_rate))
        
    # Output Layer
    model.add(Dense(output_units))
    
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    return model

def save_model(model, filename):
    """Save model to models directory."""
    path = os.path.join(MODELS_DIR, filename)
    model.save(path)
    print(f"Model saved to {path}")

def load_custom_model(filename):
    """Load model from models directory."""
    path = os.path.join(MODELS_DIR, filename)
    if os.path.exists(path):
        return tf.keras.models.load_model(path)
    else:
        print(f"Model {filename} not found.")
        return None
