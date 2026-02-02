# Stock Price Predictor

An LSTM-based stock price predictor for SPY that forecasts next-day closing price using 60-day lookback windows and technical indicators.

## Overview

This project demonstrates practical application of the **deep-learning** skill, implementing:
- Time series forecasting with LSTM networks
- Technical indicator feature engineering
- Keras 3 functional API patterns
- TDD (Test-Driven Development) workflow

## Architecture

```
Input (60 days × 10 features)
    ↓
LSTM (32 units, recurrent_dropout=0.2)
    ↓
Dropout (0.3)
    ↓
Dense (1) → Predicted Close Price
```

## Features

**10 input features:**
- Close, Volume (raw OHLCV)
- SMA_10, SMA_30 (Simple Moving Averages)
- RSI_14 (Relative Strength Index)
- MACD, MACD_signal
- BB_upper, BB_lower (Bollinger Bands)
- Returns (daily percentage change)

## Installation

```bash
# Install with Poetry
poetry install

# Or with pip (legacy)
pip install -r requirements.txt
```

## Usage

### Train and Evaluate

```bash
# With Poetry
poetry run stock-predictor --ticker SPY --epochs 100

# Or activate the virtual environment first
poetry shell
stock-predictor --ticker SPY --epochs 100

# Legacy (without Poetry)
python -m stock_predictor.main --ticker SPY --epochs 100 --output-dir output
```

**Options:**
- `--ticker`: Stock symbol (default: SPY)
- `--lookback`: Days of history per sample (default: 60)
- `--epochs`: Training epochs (default: 100)
- `--lstm-units`: LSTM layer size (default: 32)
- `--output-dir`: Where to save model and plots (default: output)

### Run Tests

```bash
poetry run pytest
```

## Project Structure

```
stock_predictor/
├── pyproject.toml       # Poetry configuration
├── requirements.txt     # Legacy pip requirements
├── README.md
├── src/
│   └── stock_predictor/
│       ├── __init__.py
│       ├── data.py      # download_stock_data, add_technical_indicators, prepare_data
│       ├── model.py     # create_model (LSTM)
│       ├── train.py     # train_model with callbacks
│       ├── evaluate.py  # naive_baseline, evaluate_model, plot_predictions
│       └── main.py      # CLI entry point
└── tests/
    ├── test_data.py     # 14 tests
    ├── test_model.py    # 5 tests
    ├── test_train.py    # 3 tests
    └── test_evaluate.py # 7 tests
```

## Training Callbacks

- **EarlyStopping**: Stops when val_loss plateaus (patience=10)
- **ModelCheckpoint**: Saves best model based on val_loss
- **ReduceLROnPlateau**: Halves learning rate when stuck (patience=5)

## Evaluation

The model is compared against a **naive baseline** (predict yesterday's price for today). A useful model should have lower MAE than the baseline.

## Data Pipeline

1. Download 5 years of data via yfinance
2. Compute technical indicators (30-day warmup)
3. Normalize with MinMaxScaler (fit on train only)
4. Create sliding window sequences (60-day lookback)
5. Split chronologically: 70% train / 15% val / 15% test
