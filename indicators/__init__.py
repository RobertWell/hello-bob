"""
Technical Indicators Package

Exports the lightweight indicator API used across this repository.
"""

from typing import List

import pandas as pd

from .indicator_base import (
    calculate_adx,
    calculate_all_indicators,
    calculate_aroon,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_cci,
    calculate_ema,
    calculate_keltner_channel,
    calculate_macd,
    calculate_mfi,
    calculate_obv,
    calculate_rsi,
    calculate_sma,
    calculate_stochastic,
    calculate_vwap,
    calculate_williams_r,
    get_indicator_columns as base_indicator_columns,
)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the core set of indicators expected by the stock-analysis scripts.
    """
    result = df.copy()

    for col in ["open", "high", "low", "close", "volume"]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    close = result["close"]
    high = result["high"]
    low = result["low"]
    volume = result["volume"]

    result["sma_20"] = close.rolling(window=20, min_periods=20).mean()
    result["ema_20"] = close.ewm(span=20, adjust=False, min_periods=20).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss
    result["rsi_14"] = 100 - (100 / (1 + rs))

    ema_fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
    result["macd"] = ema_fast - ema_slow
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
    result["macd_hist"] = result["macd"] - result["macd_signal"]

    rolling_std = close.rolling(window=20, min_periods=20).std()
    result["bb_middle"] = result["sma_20"]
    result["bb_upper"] = result["bb_middle"] + 2.0 * rolling_std
    result["bb_lower"] = result["bb_middle"] - 2.0 * rolling_std
    result["bb_width"] = (result["bb_upper"] - result["bb_lower"]) / result["bb_middle"]

    result["volume_sma_20"] = volume.rolling(window=20, min_periods=20).mean()

    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr_14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    low_14 = low.rolling(window=14, min_periods=14).min()
    high_14 = high.rolling(window=14, min_periods=14).max()
    result["stoch_k"] = 100 * (close - low_14) / (high_14 - low_14)
    result["stoch_d"] = result["stoch_k"].rolling(window=3, min_periods=3).mean()

    typical_price = (high + low + close) / 3
    tp_sma = typical_price.rolling(window=20, min_periods=20).mean()
    mean_dev = typical_price.rolling(window=20, min_periods=20).apply(
        lambda values: (abs(values - values.mean())).mean(),
        raw=False,
    )
    result["cci_20"] = (typical_price - tp_sma) / (0.015 * mean_dev)
    result["willr_14"] = -100 * (high_14 - close) / (high_14 - low_14)
    result["price_to_sma"] = result["close"] / result["sma_20"]
    result["bb_position"] = (result["close"] - result["bb_lower"]) / (result["bb_upper"] - result["bb_lower"])

    return result


def get_indicator_columns() -> List[str]:
    return [
        "sma_20",
        "ema_20",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_hist",
        "bb_lower",
        "bb_middle",
        "bb_upper",
        "bb_width",
        "volume_sma_20",
        "atr_14",
        "stoch_k",
        "stoch_d",
        "cci_20",
        "willr_14",
        "price_to_sma",
        "bb_position",
    ]


def validate_dataframe(df: pd.DataFrame) -> bool:
    required_cols = {"open", "high", "low", "close", "volume"}
    return required_cols.issubset(df.columns)


__all__ = [
    "add_indicators",
    "validate_dataframe",
    "get_indicator_columns",
    "calculate_sma",
    "calculate_ema",
    "calculate_macd",
    "calculate_rsi",
    "calculate_bollinger_bands",
    "calculate_atr",
    "calculate_stochastic",
    "calculate_adx",
    "calculate_cci",
    "calculate_williams_r",
    "calculate_obv",
    "calculate_mfi",
    "calculate_keltner_channel",
    "calculate_vwap",
    "calculate_aroon",
    "calculate_all_indicators",
    "base_indicator_columns",
]
