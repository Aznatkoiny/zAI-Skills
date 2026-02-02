"""Tests for evaluate module."""
import pytest
import numpy as np


class TestNaiveBaseline:
    """Tests for naive_baseline function."""

    def test_returns_mae(self):
        """Should return a float MAE value."""
        from stock_predictor.evaluate import naive_baseline
        y_true = np.array([100, 102, 105, 103, 107])
        mae = naive_baseline(y_true)
        assert isinstance(mae, float)

    def test_correct_calculation(self):
        """MAE should be mean of |y[t] - y[t-1]|."""
        from stock_predictor.evaluate import naive_baseline
        # [100, 102, 105, 103, 107]
        # Predictions: [100, 102, 105, 103] for targets [102, 105, 103, 107]
        # Errors: |102-100|=2, |105-102|=3, |103-105|=2, |107-103|=4
        # MAE = (2+3+2+4)/4 = 2.75
        y_true = np.array([100.0, 102.0, 105.0, 103.0, 107.0])
        mae = naive_baseline(y_true)
        assert np.isclose(mae, 2.75)

    def test_handles_constant_sequence(self):
        """Constant sequence should have MAE of 0."""
        from stock_predictor.evaluate import naive_baseline
        y_true = np.array([100.0, 100.0, 100.0, 100.0])
        mae = naive_baseline(y_true)
        assert mae == 0.0


class TestEvaluateModel:
    """Tests for evaluate_model function."""

    @pytest.fixture
    def trained_model(self):
        """Create a simple trained model for testing."""
        from stock_predictor.model import create_model
        import keras
        model = create_model(lookback=60, n_features=10)
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        return model

    @pytest.fixture
    def dummy_test_data(self):
        """Create dummy test data."""
        np.random.seed(42)
        return {
            "X_test": np.random.rand(50, 60, 10).astype(np.float32),
            "y_test": np.random.rand(50).astype(np.float32),
        }

    def test_returns_dict(self, trained_model, dummy_test_data):
        """Should return dict with metrics."""
        from stock_predictor.evaluate import evaluate_model
        result = evaluate_model(trained_model, dummy_test_data)
        assert isinstance(result, dict)
        assert "mse" in result
        assert "mae" in result

    def test_predictions_returned(self, trained_model, dummy_test_data):
        """Should include predictions in result."""
        from stock_predictor.evaluate import evaluate_model
        result = evaluate_model(trained_model, dummy_test_data)
        assert "predictions" in result
        assert len(result["predictions"]) == len(dummy_test_data["y_test"])


import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for tests
import matplotlib.pyplot as plt


class TestPlotPredictions:
    """Tests for plot_predictions function."""

    def test_creates_figure(self):
        """Should create a matplotlib figure."""
        from stock_predictor.evaluate import plot_predictions
        y_true = np.array([100, 102, 105, 103, 107])
        y_pred = np.array([99, 101, 104, 104, 106])
        fig = plot_predictions(y_true, y_pred)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_legend(self):
        """Figure should have a legend."""
        from stock_predictor.evaluate import plot_predictions
        y_true = np.array([100, 102, 105, 103, 107])
        y_pred = np.array([99, 101, 104, 104, 106])
        fig = plot_predictions(y_true, y_pred)
        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        plt.close(fig)
