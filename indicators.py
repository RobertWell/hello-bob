"""
Stock Technical Indicators Module

Quantitative analysis module for calculating technical indicators.
Uses pandas-ta for reliable, production-quality indicator calculations.

Design Principles:
- No lookahead bias (only use past data)
- Handle NaN properly
- Vectorized operations (no loops)
- Clean, reusable structure
- Suitable for machine learning
"""

import pandas as pd
from typing import List, Optional


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add comprehensive technical indicators to a DataFrame.
    
    This function follows Ta4j-style indicator mapping:
    - ClosePriceIndicator -> df["close"]
    - SMAIndicator(close, 20) -> rolling mean
    - EMAIndicator(close, 20) -> ewm
    - RSIIndicator(close, 14) -> gain/loss method
    - MACDIndicator(close) -> EMA(12) - EMA(26)
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with required columns:
        - open: Open price
        - high: High price
        - low: Low price
        - close: Close price
        - volume: Trading volume
        Index should be datetime.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added indicator columns.
        Does not mutate input - returns new DataFrame.
    
    Added Columns
    -------------
    Trend Indicators:
        - sma_20: Simple Moving Average (20 periods)
        - ema_20: Exponential Moving Average (20 periods)
    
    Momentum Indicators:
        - rsi_14: Relative Strength Index (14 periods)
        - macd: MACD line (12, 26, 9)
        - macd_signal: MACD signal line
        - macd_hist: MACD histogram
    
    Volatility Indicators:
        - bb_upper: Bollinger Bands upper band
        - bb_middle: Bollinger Bands middle band (SMA 20)
        - bb_lower: Bollinger Bands lower band
        - bb_width: Bollinger Bands width (normalized)
    """
    # Create a copy to avoid mutating input
    result = df.copy()
    
    # Ensure numeric types for calculations
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')

    close = result['close']
    high = result['high']
    low = result['low']
    volume = result['volume']
    
    # ==================== TREND INDICATORS ====================
    # SMA (Simple Moving Average) - window=20
    result['sma_20'] = close.rolling(window=20, min_periods=20).mean()
    
    # EMA (Exponential Moving Average) - window=20
    result['ema_20'] = close.ewm(span=20, adjust=False, min_periods=20).mean()
    
    # ==================== MOMENTUM INDICATORS ====================
    # RSI (Relative Strength Index) - window=14
    # Formula: RSI = 100 - (100 / (1 + RS)), where RS = avg_gain / avg_loss
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss
    result['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD (Moving Average Convergence Divergence)
    # MACD = EMA(12) - EMA(26), signal = EMA(macd, 9)
    ema_fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
    result['macd'] = ema_fast - ema_slow
    result['macd_signal'] = result['macd'].ewm(span=9, adjust=False, min_periods=9).mean()
    result['macd_hist'] = result['macd'] - result['macd_signal']
    
    # ==================== VOLATILITY INDICATORS ====================
    # Bollinger Bands - window=20, std=2
    # Formula: BB = SMA ± 2 * rolling std
    rolling_std = close.rolling(window=20, min_periods=20).std()
    result['bb_middle'] = result['sma_20']
    result['bb_upper'] = result['bb_middle'] + 2.0 * rolling_std
    result['bb_lower'] = result['bb_middle'] - 2.0 * rolling_std
    
    # Bollinger Bands Width (normalized for ML)
    # Formula: (Upper - Lower) / Middle
    result['bb_width'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']
    
    # ==================== VOLUME INDICATORS ====================
    # Volume SMA (20 periods)
    result['volume_sma_20'] = volume.rolling(window=20, min_periods=20).mean()
    
    # ==================== ADDITIONAL USEFUL INDICATORS ====================
    # ATR (Average True Range) - volatility measure
    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result['atr_14'] = true_range.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    
    # Stochastic Oscillator - momentum
    low_14 = low.rolling(window=14, min_periods=14).min()
    high_14 = high.rolling(window=14, min_periods=14).max()
    result['stoch_k'] = 100 * (close - low_14) / (high_14 - low_14)
    result['stoch_d'] = result['stoch_k'].rolling(window=3, min_periods=3).mean()
    
    # CCI (Commodity Channel Index) - momentum
    typical_price = (high + low + close) / 3
    tp_sma = typical_price.rolling(window=20, min_periods=20).mean()
    mean_dev = typical_price.rolling(window=20, min_periods=20).apply(
        lambda values: (abs(values - values.mean())).mean(),
        raw=False,
    )
    result['cci_20'] = (typical_price - tp_sma) / (0.015 * mean_dev)
    
    # Williams %R - momentum
    result['willr_14'] = -100 * (high_14 - close) / (high_14 - low_14)
    
    # ==================== ML-FRIENDLY NORMALIZATION ====================
    # Price relative to moving average (normalized price)
    result['price_to_sma'] = result['close'] / result['sma_20']
    
    # Price position in Bollinger Bands (0 = lower band, 1 = upper band)
    result['bb_position'] = (result['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
    
    return result


def get_indicator_columns() -> List[str]:
    """
    Return list of indicator column names added by add_indicators().
    
    Returns
    -------
    List[str]
        List of column names for all indicators.
    """
    return [
        # Trend
        'sma_20', 'ema_20',
        # Momentum
        'rsi_14', 'macd', 'macd_signal', 'macd_hist',
        # Volatility
        'bb_lower', 'bb_middle', 'bb_upper', 'bb_width',
        # Volume
        'volume_sma_20',
        # Additional
        'atr_14', 'stoch_k', 'stoch_d', 'cci_20', 'willr_14',
        # ML features
        'price_to_sma', 'bb_position'
    ]


def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that DataFrame has required columns for indicator calculation.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.
    
    Returns
    -------
    bool
        True if valid, False otherwise.
    """
    required_cols = {'open', 'high', 'low', 'close', 'volume'}
    return required_cols.issubset(df.columns)


# Example usage
if __name__ == "__main__":
    # Create sample data for testing
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    sample_data = {
        'open': 100 + (range(100)),
        'high': 105 + (range(100)),
        'low': 95 + (range(100)),
        'close': 102 + (range(100)),
        'volume': [1000000] * 100
    }
    df = pd.DataFrame(sample_data, index=dates)
    
    # Add indicators
    result = add_indicators(df)
    
    # Display results
    print("DataFrame with indicators:")
    print(result.tail())
    print(f"\nShape: {result.shape}")
    print(f"\nColumns: {result.columns.tolist()}")
    print(f"\nNaN count per column:\n{result.isna().sum()}")
