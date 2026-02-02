"""Tests for train module."""
import pytest
import numpy as np
import tempfile
import os


class TestTrainModel:
    """Tests for train_model function."""

    @pytest.fixture
    def dummy_data(self):
        """Create small dummy data for fast tests."""
        np.random.seed(42)
        n_samples = 100
        lookback = 60
        n_features = 10
        return {
            "X_train": np.random.rand(n_samples, lookback, n_features).astype(np.float32),
            "y_train": np.random.rand(n_samples).astype(np.float32),
            "X_val": np.random.rand(20, lookback, n_features).astype(np.float32),
            "y_val": np.random.rand(20).astype(np.float32),
        }

    def test_returns_history(self, dummy_data):
        """Should return training history."""
        from stock_predictor.train import train_model
        from stock_predictor.model import create_model
        model = create_model(lookback=60, n_features=10)
        history = train_model(model, dummy_data, epochs=2)
        assert hasattr(history, "history")
        assert "loss" in history.history

    def test_model_is_trained(self, dummy_data):
        """Model should have different weights after training."""
        from stock_predictor.train import train_model
        from stock_predictor.model import create_model
        import keras
        model = create_model(lookback=60, n_features=10)
        initial_weights = model.get_weights()[0].copy()
        train_model(model, dummy_data, epochs=2)
        trained_weights = model.get_weights()[0]
        assert not np.allclose(initial_weights, trained_weights)

    def test_checkpoint_created(self, dummy_data):
        """Should save model checkpoint."""
        from stock_predictor.train import train_model
        from stock_predictor.model import create_model
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = os.path.join(tmpdir, "best.keras")
            model = create_model(lookback=60, n_features=10)
            train_model(model, dummy_data, epochs=2, checkpoint_path=checkpoint_path)
            assert os.path.exists(checkpoint_path)
