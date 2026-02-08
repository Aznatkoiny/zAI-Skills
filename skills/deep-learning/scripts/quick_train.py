#!/usr/bin/env python3
"""
Quick Training Script for Keras 3

A reusable training template with best practices:
- Standard callbacks (EarlyStopping, ModelCheckpoint, TensorBoard)
- Learning rate scheduling
- Training history plotting

Usage:
    # Import and customize
    from quick_train import train_with_best_practices

    history = train_with_best_practices(
        model=model,
        train_data=(x_train, y_train),
        val_data=(x_val, y_val),
        epochs=100,
        batch_size=32
    )
"""

import os
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

# Support both standalone Keras 3 and TensorFlow's bundled Keras
try:
    import keras
except ImportError:
    from tensorflow import keras

import numpy as np
import matplotlib.pyplot as plt


def get_standard_callbacks(
    model_path: str = "best_model.keras",
    log_dir: str = "./logs",
    patience: int = 10,
    reduce_lr_patience: int = 5,
    reduce_lr_factor: float = 0.5,
    min_lr: float = 1e-6
) -> list:
    """
    Create standard callbacks for training.

    Args:
        model_path: Path to save best model
        log_dir: Directory for TensorBoard logs
        patience: EarlyStopping patience
        reduce_lr_patience: ReduceLROnPlateau patience
        reduce_lr_factor: Factor to reduce LR by
        min_lr: Minimum learning rate

    Returns:
        List of Keras callbacks
    """
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=model_path,
            monitor="val_loss",
            save_best_only=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=reduce_lr_factor,
            patience=reduce_lr_patience,
            min_lr=min_lr,
            verbose=1
        ),
        keras.callbacks.TensorBoard(
            log_dir=log_dir,
            histogram_freq=1
        )
    ]


def train_with_best_practices(
    model: keras.Model,
    train_data: tuple,
    val_data: tuple,
    epochs: int = 100,
    batch_size: int = 32,
    model_path: str = "best_model.keras",
    log_dir: str = "./logs",
    patience: int = 10,
    extra_callbacks: list = None
) -> keras.callbacks.History:
    """
    Train a model with standard best practices.

    Args:
        model: Compiled Keras model
        train_data: Tuple of (x_train, y_train) or tf.data.Dataset
        val_data: Tuple of (x_val, y_val) or tf.data.Dataset
        epochs: Maximum epochs to train
        batch_size: Batch size (ignored if using Dataset)
        model_path: Path to save best model
        log_dir: Directory for TensorBoard logs
        patience: Early stopping patience
        extra_callbacks: Additional callbacks to include

    Returns:
        Training history
    """
    callbacks = get_standard_callbacks(
        model_path=model_path,
        log_dir=log_dir,
        patience=patience
    )

    if extra_callbacks:
        callbacks.extend(extra_callbacks)

    # Handle both tuple and Dataset inputs
    if isinstance(train_data, tuple):
        x_train, y_train = train_data
        x_val, y_val = val_data
        history = model.fit(
            x_train, y_train,
            validation_data=(x_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks
        )
    else:
        # Assume tf.data.Dataset
        history = model.fit(
            train_data,
            validation_data=val_data,
            epochs=epochs,
            callbacks=callbacks
        )

    return history


def plot_training_history(
    history: keras.callbacks.History,
    metrics: list = None,
    save_path: str = None,
    figsize: tuple = (12, 4)
) -> None:
    """
    Plot training history curves.

    Args:
        history: Keras training history
        metrics: List of metrics to plot (default: loss + first metric)
        save_path: Optional path to save figure
        figsize: Figure size
    """
    hist = history.history

    if metrics is None:
        # Default: loss and first metric (usually accuracy)
        metrics = ["loss"]
        for key in hist.keys():
            if key not in ["loss", "val_loss", "lr"]:
                metrics.append(key.replace("val_", ""))
                break
        metrics = list(set(metrics))

    n_plots = len(metrics)
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)
    if n_plots == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        if metric in hist:
            ax.plot(hist[metric], label=f"Train {metric}")
        val_metric = f"val_{metric}"
        if val_metric in hist:
            ax.plot(hist[val_metric], label=f"Val {metric}")

        ax.set_xlabel("Epoch")
        ax.set_ylabel(metric.capitalize())
        ax.set_title(f"Training {metric.capitalize()}")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved figure to {save_path}")

    plt.show()


# Example usage
if __name__ == "__main__":
    # Demo with MNIST
    print("Loading MNIST dataset...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

    # Preprocess
    x_train = x_train.reshape(-1, 28 * 28).astype("float32") / 255
    x_test = x_test.reshape(-1, 28 * 28).astype("float32") / 255

    # Split validation
    x_val, y_val = x_train[-10000:], y_train[-10000:]
    x_train, y_train = x_train[:-10000], y_train[:-10000]

    # Build model
    print("Building model...")
    model = keras.Sequential([
        keras.layers.Dense(128, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(10, activation="softmax")
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    # Train
    print("Training with best practices...")
    history = train_with_best_practices(
        model=model,
        train_data=(x_train, y_train),
        val_data=(x_val, y_val),
        epochs=50,
        batch_size=128,
        patience=5
    )

    # Plot
    plot_training_history(history, save_path="training_history.png")

    # Evaluate
    print("\nEvaluating on test set...")
    test_loss, test_acc = model.evaluate(x_test, y_test)
    print(f"Test accuracy: {test_acc:.4f}")
