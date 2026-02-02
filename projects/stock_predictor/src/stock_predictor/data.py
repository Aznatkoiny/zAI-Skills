"""Data download and feature engineering for stock prediction."""
import numpy as np
import yfinance as yf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


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


def prepare_data(
    ticker: str,
    lookback: int = 60,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15
) -> dict:
    """Prepare data for LSTM training.

    Downloads data, adds indicators, normalizes, and creates sequences.

    Args:
        ticker: Stock ticker symbol
        lookback: Number of past days to use as input
        train_ratio: Fraction of data for training
        val_ratio: Fraction of data for validation

    Returns:
        Dict with X_train, y_train, X_val, y_val, X_test, y_test, scaler
    """
    # Download and add indicators
    df = download_stock_data(ticker, period="5y")
    df = add_technical_indicators(df)

    # Select features (10 total as per design)
    feature_cols = [
        "Close", "Volume", "SMA_10", "SMA_30", "RSI_14",
        "MACD", "MACD_signal", "BB_upper", "BB_lower", "Returns"
    ]
    df = df[feature_cols].dropna()

    # Convert to numpy
    data = df.values

    # Split indices (chronological)
    n = len(data)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    # Fit scaler on training data only
    scaler = MinMaxScaler()
    scaler.fit(data[:train_end])

    # Normalize all data
    data_scaled = scaler.transform(data)

    # Create sequences
    X, y = [], []
    for i in range(lookback, len(data_scaled)):
        X.append(data_scaled[i - lookback:i])
        y.append(data_scaled[i, 0])  # Predict Close (column 0)

    X = np.array(X)
    y = np.array(y)

    # Split sequences (adjust indices for lookback offset)
    train_end_seq = train_end - lookback
    val_end_seq = val_end - lookback

    return {
        "X_train": X[:train_end_seq],
        "y_train": y[:train_end_seq],
        "X_val": X[train_end_seq:val_end_seq],
        "y_val": y[train_end_seq:val_end_seq],
        "X_test": X[val_end_seq:],
        "y_test": y[val_end_seq:],
        "scaler": scaler,
    }
