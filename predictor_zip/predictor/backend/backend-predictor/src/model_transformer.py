import tensorflow as tf
from tensorflow.keras import layers, Model, Input
from tensorflow.keras.optimizers import Adam
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR

def build_transformer_model(input_shape, output_units=4, num_heads=4, key_dim=64, ff_dim=128, dropout_rate=0.1, learning_rate=0.001):
    """
    Build Transformer model for OHLC prediction.
    
    Args:
        input_shape (tuple): (lookback_window, num_features)
        output_units (int): Number of output units (4 for OHLC)
        num_heads (int): Number of attention heads
        key_dim (int): Dimension of the key/query/value projections
        ff_dim (int): Hidden layer size in feed forward network
        dropout_rate (float): Dropout rate
        learning_rate (float): Learning rate
        
    Returns:
        model: Keras model
    """
    inputs = Input(shape=input_shape)
    
    # Multi-Head Attention
    # Attention output will be (batch_size, timesteps, features)
    x = layers.MultiHeadAttention(num_heads=num_heads, key_dim=key_dim)(inputs, inputs)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x + inputs) # Residual connection
    
    # Feed Forward Network
    x_ff = layers.Dense(ff_dim, activation="relu")(x)
    x_ff = layers.Dense(input_shape[1])(x_ff) # Project back to embedding dim
    x_ff = layers.Dropout(dropout_rate)(x_ff)
    
    # Second Residual Connection & Norm
    # Note: In standard transformer, the FF network output dim matches input dim.
    # Here we are simplifying. Let's make sure dimensions align for residual.
    # The MHA output `x` has shape (batch, timesteps, features).
    # `x_ff` after Dense(ff_dim) is (batch, timesteps, ff_dim).
    # We need to project it back to `features` dimension or flatten it later.
    # Standard Transformer encoder block structure:
    # x = LayerNorm(x + MHA(x))
    # x = LayerNorm(x + FFN(x))
    
    # Correct FFN implementation
    res = x
    x = layers.Dense(ff_dim, activation="relu")(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(input_shape[-1])(x) # Project back to feature dimension
    x = layers.LayerNormalization(epsilon=1e-6)(x + res)
    
    # Global Average Pooling or Flatten to get vector for final prediction
    x = layers.GlobalAveragePooling1D()(x)
    # Alternatively use Flatten(): x = layers.Flatten()(x)
    
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(64, activation="relu")(x)
    
    # Output Layer
    outputs = layers.Dense(output_units)(x)
    
    model = Model(inputs, outputs)
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    return model

def save_transformer_model(model, filename):
    """Save model to models directory."""
    path = os.path.join(MODELS_DIR, filename)
    model.save(path)
    print(f"Transformer model saved to {path}")
