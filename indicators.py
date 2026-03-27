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
import pandas_ta as ta
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
    
    # ==================== TREND INDICATORS ====================
    # SMA (Simple Moving Average) - window=20
    result['sma_20'] = ta.sma(result['close'], length=20)
    
    # EMA (Exponential Moving Average) - window=20
    result['ema_20'] = ta.ema(result['close'], length=20)
    
    # ==================== MOMENTUM INDICATORS ====================
    # RSI (Relative Strength Index) - window=14
    # Formula: RSI = 100 - (100 / (1 + RS)), where RS = avg_gain / avg_loss
    result['rsi_14'] = ta.rsi(result['close'], length=14)
    
    # MACD (Moving Average Convergence Divergence)
    # MACD = EMA(12) - EMA(26), signal = EMA(macd, 9)
    macd_result = ta.macd(result['close'], fast=12, slow=26, signal=9)
    result['macd'] = macd_result['MACD_12_26_9']
    result['macd_signal'] = macd_result['MACDs_12_26_9']
    result['macd_hist'] = macd_result['MACDh_12_26_9']
    
    # ==================== VOLATILITY INDICATORS ====================
    # Bollinger Bands - window=20, std=2
    # Formula: BB = SMA ± 2 * rolling std
    bb_result = ta.bbands(result['close'], length=20, std=2.0)
    result['bb_lower'] = bb_result['BBL_20_2.0']
    result['bb_middle'] = bb_result['BBM_20_2.0']
    result['bb_upper'] = bb_result['BBU_20_2.0']
    
    # Bollinger Bands Width (normalized for ML)
    # Formula: (Upper - Lower) / Middle
    result['bb_width'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']
    
    # ==================== VOLUME INDICATORS ====================
    # Volume SMA (20 periods)
    result['volume_sma_20'] = ta.sma(result['volume'], length=20)
    
    # ==================== ADDITIONAL USEFUL INDICATORS ====================
    # ATR (Average True Range) - volatility measure
    result['atr_14'] = ta.atr(result['high'], result['low'], result['close'], length=14)
    
    # Stochastic Oscillator - momentum
    stoch_result = ta.stoch(result['high'], result['low'], result['close'], k=14, d=3)
    result['stoch_k'] = stoch_result['STOCHk_14_3_3']
    result['stoch_d'] = stoch_result['STOCHd_14_3_3']
    
    # CCI (Commodity Channel Index) - momentum
    result['cci_20'] = ta.cci(result['high'], result['low'], result['close'], length=20)
    
    # Williams %R - momentum
    result['willr_14'] = ta.willr(result['high'], result['low'], result['close'], length=14)
    
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
