import tensorflow as tf
from tensorflow.keras import layers, Model, Input
from tensorflow.keras.optimizers import Adam
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config import MODELS_DIR

def mixed_mae_mse_loss(mse_weight=0.5, mae_weight=0.5, directional_weight=0.0):
    def loss(y_true, y_pred):
        mse = tf.reduce_mean(tf.square(y_true - y_pred), axis=-1)
        mae = tf.reduce_mean(tf.abs(y_true - y_pred), axis=-1)
        base_loss = (mse_weight * mse) + (mae_weight * mae)
        if directional_weight <= 0:
            return base_loss

        # Direction proxy: candle direction using close-open sign.
        true_dir = tf.sign(y_true[:, 3] - y_true[:, 0])
        pred_dir = tf.tanh(5.0 * (y_pred[:, 3] - y_pred[:, 0]))
        direction_penalty = tf.square(true_dir - pred_dir)
        return base_loss + (directional_weight * direction_penalty)
    return loss


def compile_multi_head_model(
    model,
    learning_rate=0.001,
    horizon_loss_weights=None,
    mse_weight=0.5,
    mae_weight=0.5,
    directional_weight=0.0,
):
    if horizon_loss_weights is None:
        horizon_loss_weights = {
            'forecast_10m': 1.0,
            'forecast_30m': 1.0,
            'forecast_1h': 1.0
        }

    mixed_loss = mixed_mae_mse_loss(
        mse_weight=mse_weight,
        mae_weight=mae_weight,
        directional_weight=directional_weight,
    )

    losses = {
        'forecast_10m': mixed_loss,
        'forecast_30m': mixed_loss,
        'forecast_1h': mixed_loss
    }

    metrics = {
        'forecast_10m': ['mae', 'mse'],
        'forecast_30m': ['mae', 'mse'],
        'forecast_1h': ['mae', 'mse']
    }

    optimizer = Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss=losses,
        loss_weights=horizon_loss_weights,
        metrics=metrics
    )
    return model


def build_multi_head_transformer(
    input_shape,
    output_units=5,
    num_heads=4,
    key_dim=64,
    ff_dim=128,
    dropout_rate=0.1,
    learning_rate=0.001,
    horizon_loss_weights=None,
    mse_weight=0.5,
    mae_weight=0.5,
    directional_weight=0.0,
):
    """
    Build Multi-Head Transformer for Multi-Horizon Forecasting.
    
    Args:
        input_shape (tuple): (lookback_window, num_features)
        output_units (int): Number of output units (5 for OHLCV) per head
        num_heads (int): Number of attention heads
        key_dim (int): Dimension of the key/query/value projections
        ff_dim (int): Hidden layer size in feed forward network
        dropout_rate (float): Dropout rate
        learning_rate (float): Learning rate
        
    Returns:
        model: Keras model with 3 outputs (10m, 30m, 1h)
    """
    inputs = Input(shape=input_shape)
    
    # Shared Encoder (Transformer Block)
    # Layer 1
    x = layers.MultiHeadAttention(num_heads=num_heads, key_dim=key_dim)(inputs, inputs)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x + inputs)
    
    # Feed Forward
    res = x
    x = layers.Dense(ff_dim, activation="relu")(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(input_shape[-1])(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x + res)
    
    # Layer 2 (Stacking for deeper representation)
    res = x
    x = layers.MultiHeadAttention(num_heads=num_heads, key_dim=key_dim)(x, x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x + res)
    
    res = x
    x = layers.Dense(ff_dim, activation="relu")(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(input_shape[-1])(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x + res)
    
    # Global Pooling to get a fixed vector representation
    shared_features = layers.GlobalAveragePooling1D()(x)
    shared_features = layers.Dropout(dropout_rate)(shared_features)
    
    # Separate Output Heads
    
    # Head 1: 10m Forecast
    h1 = layers.Dense(64, activation="relu")(shared_features)
    output_10m = layers.Dense(output_units, name='forecast_10m')(h1)
    
    # Head 2: 30m Forecast
    h2 = layers.Dense(64, activation="relu")(shared_features)
    output_30m = layers.Dense(output_units, name='forecast_30m')(h2)
    
    # Head 3: 1h Forecast
    h3 = layers.Dense(64, activation="relu")(shared_features)
    output_1h = layers.Dense(output_units, name='forecast_1h')(h3)
    
    # Model
    model = Model(inputs=inputs, outputs=[output_10m, output_30m, output_1h])
    
    compile_multi_head_model(
        model=model,
        learning_rate=learning_rate,
        horizon_loss_weights=horizon_loss_weights,
        mse_weight=mse_weight,
        mae_weight=mae_weight,
        directional_weight=directional_weight,
    )
    return model

def save_multi_head_model(model, filename):
    """Save model to models directory."""
    path = os.path.join(MODELS_DIR, filename)
    model.save(path)
    print(f"Multi-Head Transformer model saved to {path}")
