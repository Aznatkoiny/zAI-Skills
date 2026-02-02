"""Data download and feature engineering for stock prediction."""
import numpy as np
import yfinance as yf
import pandas as pd


def download_stock_data(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Download stock data from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g., 'SPY')
        period: Data period ('1mo', '1y', '5y', 'max')

    Returns:
        DataFrame with OHLCV data, DatetimeIndex, no NaN values
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    # Drop any rows with missing data
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to stock DataFrame.

    Args:
        df: DataFrame with OHLCV columns

    Returns:
        DataFrame with additional indicator columns:
        - SMA_10, SMA_30: Simple moving averages
        - RSI_14: Relative Strength Index
        - MACD, MACD_signal: MACD and signal line
        - BB_upper, BB_lower: Bollinger Bands
        - Returns: Daily percentage returns
    """
    df = df.copy()

    # Simple Moving Averages
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_30"] = df["Close"].rolling(window=30).mean()

    # Daily Returns
    df["Returns"] = df["Close"].pct_change()

    # RSI (14-day)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands (20-day, 2 std)
    sma_20 = df["Close"].rolling(window=20).mean()
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_upper"] = sma_20 + (2 * std_20)
    df["BB_lower"] = sma_20 - (2 * std_20)

    return df
