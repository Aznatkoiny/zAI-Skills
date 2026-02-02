"""Tests for data module."""
import pytest
import pandas as pd
from stock_predictor.data import download_stock_data, add_technical_indicators


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
