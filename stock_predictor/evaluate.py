"""Evaluation utilities for stock predictor."""
import numpy as np


def naive_baseline(y_true: np.ndarray) -> float:
    """Calculate MAE for naive baseline (predict yesterday's price).

    Args:
        y_true: Array of true values in sequence order

    Returns:
        Mean Absolute Error of predicting y[t-1] for y[t]
    """
    # Predict yesterday's value for today
    y_pred = y_true[:-1]  # All but last
    y_actual = y_true[1:]  # All but first
    mae = np.mean(np.abs(y_actual - y_pred))
    return float(mae)
