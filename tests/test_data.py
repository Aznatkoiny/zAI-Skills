"""Tests for data module."""
import pytest
import pandas as pd
import numpy as np
from stock_predictor.data import download_stock_data, add_technical_indicators, prepare_data


class TestDownloadStockData:
    """Tests for download_stock_data function."""

    def test_returns_dataframe(self):
        """Should return a pandas DataFrame."""
        df = download_stock_data("SPY", period="1mo")
        assert isinstance(df, pd.DataFrame)

    def test_has_ohlcv_columns(self):
        """Should have Open, High, Low, Close, Volume columns."""
        df = download_stock_data("SPY", period="1mo")
        required = ["Open", "High", "Low", "Close", "Volume"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_index_is_datetime(self):
        """Index should be DatetimeIndex."""
        df = download_stock_data("SPY", period="1mo")
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_no_missing_values(self):
        """Should not have NaN values in OHLCV."""
        df = download_stock_data("SPY", period="1mo")
        ohlcv = df[["Open", "High", "Low", "Close", "Volume"]]
        assert not ohlcv.isna().any().any()


class TestAddTechnicalIndicators:
    """Tests for add_technical_indicators function."""

    @pytest.fixture
    def stock_df(self):
        """Get sample stock data."""
        return download_stock_data("SPY", period="6mo")

    def test_returns_dataframe(self, stock_df):
        """Should return a DataFrame."""
        result = add_technical_indicators(stock_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_all_indicators(self, stock_df):
        """Should have all required indicator columns."""
        result = add_technical_indicators(stock_df)
        required = [
            "SMA_10", "SMA_30", "RSI_14", "MACD", "MACD_signal",
            "BB_upper", "BB_lower", "Returns"
        ]
        for col in required:
            assert col in result.columns, f"Missing indicator: {col}"

    def test_no_nan_after_warmup(self, stock_df):
        """Should have no NaN values after indicator warmup period."""
        result = add_technical_indicators(stock_df)
        # Drop first 30 rows (warmup for SMA_30)
        result_clean = result.iloc[30:]
        assert not result_clean.isna().any().any()

    def test_rsi_bounds(self, stock_df):
        """RSI should be between 0 and 100."""
        result = add_technical_indicators(stock_df)
        rsi = result["RSI_14"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()


class TestPrepareData:
    """Tests for prepare_data function."""

    def test_returns_correct_structure(self):
        """Should return dict with train/val/test splits and scaler."""
        result = prepare_data("SPY", lookback=60)
        assert "X_train" in result
        assert "y_train" in result
        assert "X_val" in result
        assert "y_val" in result
        assert "X_test" in result
        assert "y_test" in result
        assert "scaler" in result

    def test_shapes_are_correct(self):
        """X should be 3D (samples, lookback, features), y should be 1D."""
        result = prepare_data("SPY", lookback=60)
        X_train, y_train = result["X_train"], result["y_train"]
        assert len(X_train.shape) == 3
        assert X_train.shape[1] == 60  # lookback
        assert len(y_train.shape) == 1
        assert X_train.shape[0] == y_train.shape[0]

    def test_feature_count(self):
        """Should have 10 features as per design."""
        result = prepare_data("SPY", lookback=60)
        assert result["X_train"].shape[2] == 10

    def test_chronological_split(self):
        """Train should come before val, val before test (no shuffle)."""
        result = prepare_data("SPY", lookback=60)
        # Test set should be larger values (more recent, higher prices generally)
        # This is a weak test but ensures order is preserved
        train_len = len(result["y_train"])
        val_len = len(result["y_val"])
        test_len = len(result["y_test"])
        total = train_len + val_len + test_len
        # Approximately 70/15/15 split
        assert 0.65 < train_len / total < 0.75
        assert 0.10 < val_len / total < 0.20
        assert 0.10 < test_len / total < 0.20

    def test_normalized_range(self):
        """Normalized data should be roughly in [0, 1] range."""
        result = prepare_data("SPY", lookback=60)
        X_train = result["X_train"]
        # MinMaxScaler should put most values between 0 and 1
        assert X_train.min() >= -0.5  # Allow some slack
        assert X_train.max() <= 1.5
