# Hello Bob - Stock Analysis Pipeline

A quantitative stock analysis pipeline combining market sentiment from PTT with technical indicators.

## Features

- **PTT Sentiment Analysis**: Fetches and analyzes posts from PTT Stock board (stock 板)
- **Technical Indicators**: Comprehensive indicator calculations using pandas-ta
  - Trend: SMA, EMA
  - Momentum: RSI, MACD, Stochastic, CCI, Williams %R
  - Volatility: Bollinger Bands, ATR
  - Volume: Volume SMA
- **ML-Ready**: Designed for machine learning with proper NaN handling and no lookahead bias
- **Database Logging**: SQLite-based storage for sentiment and indicator data

## Installation

```bash
# Clone the repository
git clone https://github.com/RobertWell/hello-bob.git
cd hello-bob

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Fetch PTT Sentiment

```python
from ptt_bus import fetch_ptt_posts, analyze_sentiment

# Fetch recent posts
posts = fetch_ptt_posts(limit=50)

# Analyze sentiment
sentiment = analyze_sentiment(posts)
print(f"Bullish: {sentiment['bullish_count']}")
print(f"Bearish: {sentiment['bearish_count']}")
print(f"Sentiment Score: {sentiment['sentiment_score']}")
```

### Calculate Technical Indicators

```python
import pandas as pd
from indicators import add_indicators

# Prepare data
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Add indicators
df_with_indicators = add_indicators(df)
```

### Run Full Update

```bash
python update_market_sentiment.py
```

## Project Structure

```
hello-bob/
├── ptt_bus.py                  # PTT scraper and sentiment analysis
├── indicators.py               # Technical indicators
├── update_market_sentiment.py  # Main update script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── logs/                       # Log files (auto-created)
```

## Indicator Details

### Trend Indicators
- **sma_20**: 20-period Simple Moving Average
- **ema_20**: 20-period Exponential Moving Average

### Momentum Indicators
- **rsi_14**: 14-period Relative Strength Index
- **macd**: MACD line (12, 26, 9)
- **macd_signal**: MACD signal line
- **macd_hist**: MACD histogram
- **stoch_k**: Stochastic %K
- **stoch_d**: Stochastic %D
- **cci_20**: 20-period Commodity Channel Index
- **willr_14**: 14-period Williams %R

### Volatility Indicators
- **bb_upper**: Bollinger Bands upper band
- **bb_middle**: Bollinger Bands middle band
- **bb_lower**: Bollinger Bands lower band
- **bb_width**: Bollinger Bands width (normalized)
- **atr_14**: 14-period Average True Range

### ML Features
- **price_to_sma**: Price relative to SMA (normalized)
- **bb_position**: Price position in Bollinger Bands (0-1)

## Design Principles

1. **No Lookahead Bias**: All indicators use only past data
2. **Handle NaN Properly**: Explicit handling of missing data
3. **Vectorized Operations**: No loops for performance
4. **Clean Structure**: Reusable, well-documented code
5. **ML-Ready**: Suitable for machine learning pipelines

## Sentiment Analysis

Sentiment is determined by keyword matching:

**Bullish Keywords**: 多頭，看漲，買進，加碼，上攻，突破，新高，噴出，涨停，大漲，創高，利多，強勢，反彈，反攻

**Bearish Keywords**: 空頭，看跌，賣出，停損，下探，破底，新低，崩盤，跌停，大跌，高點，利空，弱勢，修正，下檔

## Database Schema

### sentiment_log
- id: Primary key
- timestamp: When analysis was run
- bullish_count: Number of bullish posts
- bearish_count: Number of bearish posts
- neutral_count: Number of neutral posts
- sentiment_score: Overall sentiment (-1 to 1)

### stock_indicators
- id: Primary key
- timestamp: When indicator was calculated
- symbol: Stock symbol
- indicator_type: Type of indicator
- value: Indicator value

## License

MIT

## Author

Robert Lin (@RobertWell)
