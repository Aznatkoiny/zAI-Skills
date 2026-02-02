"""Training utilities for stock predictor."""
import keras


def train_model(
    model: keras.Model,
    data: dict,
    epochs: int = 100,
    batch_size: int = 32,
    checkpoint_path: str = "best_model.keras",
    patience: int = 10
) -> keras.callbacks.History:
    """Train the LSTM model with callbacks.

    Args:
        model: Keras model to train
        data: Dict with X_train, y_train, X_val, y_val
        epochs: Maximum training epochs
        batch_size: Training batch size
        checkpoint_path: Path to save best model
        patience: Early stopping patience

    Returns:
        Training history object
    """
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"]
    )

    # Setup callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience,
            restore_best_weights=True
        ),
        keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor="val_loss",
            save_best_only=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )
    ]

    # Train
    history = model.fit(
        data["X_train"],
        data["y_train"],
        validation_data=(data["X_val"], data["y_val"]),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=0
    )

    return history
