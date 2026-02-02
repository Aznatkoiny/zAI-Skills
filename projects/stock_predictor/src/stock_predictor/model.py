"""LSTM model for stock price prediction."""
import keras
from keras import layers


def create_model(
    lookback: int = 60,
    n_features: int = 10,
    lstm_units: int = 32,
    recurrent_dropout: float = 0.2,
    dropout: float = 0.3
) -> keras.Model:
    """Create LSTM model for stock price prediction.

    Architecture:
        Input (lookback, n_features)
        -> LSTM (lstm_units, recurrent_dropout)
        -> Dropout
        -> Dense (1)

    Args:
        lookback: Number of timesteps in input sequence
        n_features: Number of features per timestep
        lstm_units: Number of LSTM units
        recurrent_dropout: Dropout rate for recurrent connections
        dropout: Dropout rate after LSTM

    Returns:
        Uncompiled Keras Model
    """
    inputs = keras.Input(shape=(lookback, n_features))
    x = layers.LSTM(lstm_units, recurrent_dropout=recurrent_dropout)(inputs)
    x = layers.Dropout(dropout)(x)
    outputs = layers.Dense(1)(x)

    model = keras.Model(inputs=inputs, outputs=outputs)
    return model
