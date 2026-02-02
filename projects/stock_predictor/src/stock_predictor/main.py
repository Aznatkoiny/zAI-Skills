#!/usr/bin/env python3
"""Main entry point for stock predictor training and evaluation."""
import argparse
import os

os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import keras
import matplotlib.pyplot as plt

from stock_predictor.data import prepare_data
from stock_predictor.model import create_model
from stock_predictor.train import train_model
from stock_predictor.evaluate import naive_baseline, evaluate_model, plot_predictions


def main():
    """Run full training and evaluation pipeline."""
    parser = argparse.ArgumentParser(description="Train stock price predictor")
    parser.add_argument("--ticker", default="SPY", help="Stock ticker symbol")
    parser.add_argument("--lookback", type=int, default=60, help="Lookback window")
    parser.add_argument("--epochs", type=int, default=100, help="Max epochs")
    parser.add_argument("--lstm-units", type=int, default=32, help="LSTM units")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Preparing data for {args.ticker}...")
    data = prepare_data(args.ticker, lookback=args.lookback)
    print(f"  Train: {len(data['X_train'])} samples")
    print(f"  Val:   {len(data['X_val'])} samples")
    print(f"  Test:  {len(data['X_test'])} samples")

    print("\nCreating model...")
    model = create_model(
        lookback=args.lookback,
        n_features=data["X_train"].shape[2],
        lstm_units=args.lstm_units
    )
    model.summary()

    print("\nTraining...")
    checkpoint_path = os.path.join(args.output_dir, "best_model.keras")
    history = train_model(
        model, data,
        epochs=args.epochs,
        checkpoint_path=checkpoint_path
    )
    print(f"  Best val_loss: {min(history.history['val_loss']):.6f}")

    print("\nEvaluating...")
    # Load best model
    model = keras.models.load_model(checkpoint_path)
    results = evaluate_model(model, data)
    print(f"  Test MSE: {results['mse']:.6f}")
    print(f"  Test MAE: {results['mae']:.6f}")

    # Naive baseline for comparison
    # Denormalize y_test for baseline calculation
    scaler = data["scaler"]
    y_test_denorm = results["y_test"] * (scaler.data_max_[0] - scaler.data_min_[0]) + scaler.data_min_[0]
    baseline_mae = naive_baseline(y_test_denorm)
    print(f"  Naive baseline MAE: ${baseline_mae:.2f}")

    # Plot and save
    fig = plot_predictions(results["y_test"], results["predictions"])
    fig.savefig(os.path.join(args.output_dir, "predictions.png"), dpi=150)
    print(f"\nSaved plot to {args.output_dir}/predictions.png")
    plt.close(fig)

    print("\nDone!")


if __name__ == "__main__":
    main()
