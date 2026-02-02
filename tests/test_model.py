"""Tests for model module."""
import pytest
import numpy as np


class TestCreateModel:
    """Tests for create_model function."""

    def test_returns_keras_model(self):
        """Should return a Keras Model instance."""
        from stock_predictor.model import create_model
        import keras
        model = create_model(lookback=60, n_features=10)
        assert isinstance(model, keras.Model)

    def test_correct_input_shape(self):
        """Input shape should match (lookback, n_features)."""
        from stock_predictor.model import create_model
        model = create_model(lookback=60, n_features=10)
        assert model.input_shape == (None, 60, 10)

    def test_correct_output_shape(self):
        """Output should be single value (regression)."""
        from stock_predictor.model import create_model
        model = create_model(lookback=60, n_features=10)
        assert model.output_shape == (None, 1)

    def test_can_compile(self):
        """Model should compile without errors."""
        from stock_predictor.model import create_model
        model = create_model(lookback=60, n_features=10)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        assert model.optimizer is not None

    def test_can_predict(self):
        """Model should accept input and produce output."""
        from stock_predictor.model import create_model
        model = create_model(lookback=60, n_features=10)
        model.compile(optimizer="adam", loss="mse")
        X_dummy = np.random.rand(5, 60, 10).astype(np.float32)
        preds = model.predict(X_dummy, verbose=0)
        assert preds.shape == (5, 1)
