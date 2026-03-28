"""
Technical Indicators Base Module

Provides 20+ technical indicators for stock analysis:
- Trend Indicators: SMA, EMA, MACD, ADX, etc.
- Momentum Indicators: RSI, Stochastic, CCI, Williams %R
- Volatility Indicators: Bollinger Bands, ATR, Keltner Channel
- Volume Indicators: OBV, Volume SMA, MFI

All indicators are vectorized (no loops) and avoid lookahead bias.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    MACD Indicator
    Returns: MACD line, Signal line, Histogram
    """
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'macd_signal': signal_line,
        'macd_hist': histogram
    })


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (RSI)
    Range: 0-100
    >70: Overbought, <30: Oversold
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Avoid division by zero
    rs = gain / loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Bollinger Bands
    Returns: Upper, Middle, Lower bands
    """
    middle = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    return pd.DataFrame({
        'bb_upper': upper,
        'bb_middle': middle,
        'bb_lower': lower,
        'bb_width': (upper - lower) / middle,  # Bandwidth
        'bb_pct': (df['Close'] - lower) / (upper - lower)  # %B
    })


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) - Volatility indicator
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """
    Stochastic Oscillator
    %K and %D lines
    """
    lowest_low = df['Low'].rolling(window=k_period).min()
    highest_high = df['High'].rolling(window=k_period).max()
    
    k = 100 * ((df['Close'] - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    
    return pd.DataFrame({
        'stoch_k': k,
        'stoch_d': d
    })


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average Directional Index (ADX) - Trend strength
    >25: Strong trend, <20: Weak trend
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # +DM and -DM
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smoothed values
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.inf)
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Commodity Channel Index (CCI)
    >100: Overbought, <-100: Oversold
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    sma = typical_price.rolling(window=period).mean()
    mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (typical_price - sma) / (0.015 * mad)
    
    return cci


def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Williams %R - Momentum indicator
    Range: -100 to 0
    <-20: Overbought, >-80: Oversold
    """
    highest_high = df['High'].rolling(window=period).max()
    lowest_low = df['Low'].rolling(window=period).min()
    
    wr = -100 * ((highest_high - df['Close']) / (highest_high - lowest_low))
    
    return wr


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    On-Balance Volume (OBV) - Volume-based momentum
    """
    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    return obv


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Money Flow Index (MFI) - Volume-weighted RSI
    Range: 0-100
    >80: Overbought, <20: Oversold
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    
    delta = typical_price.diff()
    positive_flow = money_flow.where(delta > 0, 0)
    negative_flow = money_flow.where(delta < 0, 0)
    
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + positive_mf / negative_mf.replace(0, np.inf)))
    
    return mfi


def calculate_keltner_channel(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> pd.DataFrame:
    """
    Keltner Channel - Volatility-based envelope
    """
    ema = df['Close'].ewm(span=period, adjust=False).mean()
    atr = calculate_atr(df, period)
    
    return pd.DataFrame({
        'kc_upper': ema + (multiplier * atr),
        'kc_middle': ema,
        'kc_lower': ema - (multiplier * atr)
    })


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume Weighted Average Price (VWAP)
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap


def calculate_aroon(df: pd.DataFrame, period: int = 25) -> pd.DataFrame:
    """
    Aroon Indicator - Trend direction and strength
    """
    rolling_high = df['High'].rolling(window=period + 1)
    rolling_low = df['Low'].rolling(window=period + 1)
    
    high_idx = rolling_high.apply(lambda x: x.argmax(), raw=True)
    low_idx = rolling_low.apply(lambda x: x.argmin(), raw=True)
    
    aroon_up = 100 * (period - high_idx) / period
    aroon_down = 100 * (period - low_idx) / period
    
    return pd.DataFrame({
        'aroon_up': aroon_up,
        'aroon_down': arooon_down,
        'aroon_osc': aroon_up - aroon_down
    })


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all 20+ technical indicators
    
    Returns DataFrame with all indicators:
    - SMA(5, 10, 20, 60, 120)
    - EMA(12, 26)
    - RSI(14)
    - MACD(12, 26, 9) + Signal + Histogram
    - Bollinger Bands (20, 2)
    - ATR(14)
    - Stochastic (14, 3)
    - ADX(14)
    - CCI(20)
    - Williams %R(14)
    - OBV
    - MFI(14)
    - Keltner Channel
    - VWAP
    - Aroon
    
    Total: 20+ indicators
    """
    result = df.copy()
    
    # Moving Averages
    for period in [5, 10, 20, 60, 120]:
        result[f'sma_{period}'] = calculate_sma(df['Close'], period)
    
    result['ema_12'] = calculate_ema(df['Close'], 12)
    result['ema_26'] = calculate_ema(df['Close'], 26)
    
    # MACD
    macd = calculate_macd(df)
    result['macd'] = macd['macd']
    result['macd_signal'] = macd['macd_signal']
    result['macd_hist'] = macd['macd_hist']
    
    # RSI
    result['rsi_14'] = calculate_rsi(df['Close'], 14)
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(df)
    result['bb_upper'] = bb['bb_upper']
    result['bb_middle'] = bb['bb_middle']
    result['bb_lower'] = bb['bb_lower']
    result['bb_width'] = bb['bb_width']
    result['bb_pct'] = bb['bb_pct']
    
    # ATR
    result['atr_14'] = calculate_atr(df)
    
    # Stochastic
    stoch = calculate_stochastic(df)
    result['stoch_k'] = stoch['stoch_k']
    result['stoch_d'] = stoch['stoch_d']
    
    # ADX
    result['adx_14'] = calculate_adx(df)
    
    # CCI
    result['cci_20'] = calculate_cci(df)
    
    # Williams %R
    result['williams_r'] = calculate_williams_r(df)
    
    # OBV
    result['obv'] = calculate_obv(df)
    
    # MFI
    result['mfi_14'] = calculate_mfi(df)
    
    # Keltner Channel
    kc = calculate_keltner_channel(df)
    result['kc_upper'] = kc['kc_upper']
    result['kc_middle'] = kc['kc_middle']
    result['kc_lower'] = kc['kc_lower']
    
    # VWAP
    result['vwap'] = calculate_vwap(df)
    
    # Aroon
    aroon = calculate_aroon(df)
    result['aroon_up'] = aroon['aroon_up']
    result['aroon_down'] = aroon['aroon_down']
    result['aroon_osc'] = aroon['aroon_osc']
    
    # Additional derived indicators
    result['price_to_sma20'] = df['Close'] / result['sma_20']
    result['ema_12_26_diff'] = result['ema_12'] - result['ema_26']
    
    return result


def get_indicator_columns() -> List[str]:
    """Return list of all indicator column names"""
    return [
        'sma_5', 'sma_10', 'sma_20', 'sma_60', 'sma_120',
        'ema_12', 'ema_26',
        'macd', 'macd_signal', 'macd_hist',
        'rsi_14',
        'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_pct',
        'atr_14',
        'stoch_k', 'stoch_d',
        'adx_14',
        'cci_20',
        'williams_r',
        'obv',
        'mfi_14',
        'kc_upper', 'kc_middle', 'kc_lower',
        'vwap',
        'aroon_up', 'aroon_down', 'aroon_osc',
        'price_to_sma20',
        'ema_12_26_diff'
    ]
