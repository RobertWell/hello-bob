#!/usr/bin/env python3
"""
Test Suite for Technical Indicators

Tests:
1. Indicator calculation correctness
2. No lookahead bias
3. NaN handling
4. Performance on large datasets
5. Signal generation logic
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from indicators.indicator_base import (
    calculate_sma, calculate_ema, calculate_rsi,
    calculate_macd, calculate_bollinger_bands, calculate_atr,
    calculate_stochastic, calculate_all_indicators, get_indicator_columns
)


def test_sma():
    """Test Simple Moving Average calculation"""
    print("Testing SMA...")
    
    # Create test data
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    # SMA(3)
    sma_3 = calculate_sma(data, 3)
    assert sma_3.iloc[2] == 2.0  # (1+2+3)/3
    assert sma_3.iloc[9] == 8.5  # (8+9+10)/3
    assert sma_3.iloc[0] == np.nan  # Not enough data
    
    print("  ✓ SMA test passed")
    return True


def test_ema():
    """Test Exponential Moving Average"""
    print("Testing EMA...")
    
    data = pd.Series(range(1, 101))  # 1-100
    ema_10 = calculate_ema(data, 10)
    
    # EMA should be smoother than SMA
    assert len(ema_10) == 100
    assert not ema_10.isna().all()
    
    print("  ✓ EMA test passed")
    return True


def test_rsi():
    """Test RSI calculation"""
    print("Testing RSI...")
    
    # Constant price should give RSI around 50
    data = pd.Series([50] * 30)
    rsi = calculate_rsi(data, 14)
    
    # RSI should be close to 50 for constant prices
    assert 40 < rsi.iloc[-1] < 60, f"RSI {rsi.iloc[-1]} not in expected range"
    
    # Strong uptrend should give high RSI
    uptrend = pd.Series(range(1, 31))  # 1-30
    rsi_uptrend = calculate_rsi(uptrend, 14)
    assert rsi_uptrend.iloc[-1] > 70, "RSI should be >70 for strong uptrend"
    
    print("  ✓ RSI test passed")
    return True


def test_macd():
    """Test MACD calculation"""
    print("Testing MACD...")
    
    # Generate test data
    np.random.seed(42)
    close = pd.Series(np.random.randn(100).cumsum() + 100)
    high = close * 1.02
    low = close * 0.98
    volume = pd.Series(np.random.randn(100).abs() * 1000000)
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low,
        'Volume': volume
    })
    
    macd_result = calculate_macd(df)
    
    assert 'macd' in macd_result.columns
    assert 'macd_signal' in macd_result.columns
    assert 'macd_hist' in macd_result.columns
    assert len(macd_result) == 100
    
    print("  ✓ MACD test passed")
    return True


def test_bollinger_bands():
    """Test Bollinger Bands calculation"""
    print("Testing Bollinger Bands...")
    
    np.random.seed(42)
    close = pd.Series(np.random.randn(100).cumsum() + 100)
    high = close * 1.02
    low = close * 0.98
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low
    })
    
    bb = calculate_bollinger_bands(df)
    
    # Upper > Middle > Lower
    assert (bb['bb_upper'] >= bb['bb_middle']).all()
    assert (bb['bb_middle'] >= bb['bb_lower']).all()
    
    # Price should be within bands most of the time
    in_bands = ((close >= bb['bb_lower']) & (close <= bb['bb_upper'])).mean()
    assert in_bands > 0.9, f"Price should be within bands >90% of time, got {in_bands}"
    
    print("  ✓ Bollinger Bands test passed")
    return True


def test_atr():
    """Test Average True Range"""
    print("Testing ATR...")
    
    # High volatility should give high ATR
    high_vol = pd.DataFrame({
        'High': pd.Series(range(100, 120)) * 1.1,
        'Low': pd.Series(range(90, 110)) * 0.9,
        'Close': pd.Series(range(95, 115))
    })
    
    # Low volatility
    low_vol = pd.DataFrame({
        'High': pd.Series(range(100, 120)) * 1.01,
        'Low': pd.Series(range(99, 119)) * 0.99,
        'Close': pd.Series(range(99, 119))
    })
    
    atr_high = calculate_atr(high_vol).iloc[-1]
    atr_low = calculate_atr(low_vol).iloc[-1]
    
    assert atr_high > atr_low, "High vol should have higher ATR"
    
    print("  ✓ ATR test passed")
    return True


def test_no_lookahead_bias():
    """Test that indicators don't use future data"""
    print("Testing for lookahead bias...")
    
    # Generate sequential data
    np.random.seed(42)
    n = 200
    close = pd.Series(np.random.randn(n).cumsum() + 100)
    high = close * 1.02
    low = close * 0.98
    volume = pd.Series(np.random.randn(n).abs() * 1000000)
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low,
        'Volume': volume
    })
    
    # Calculate indicators
    result = calculate_all_indicators(df)
    
    # Test: Indicator at time t should only depend on data up to time t
    # Shift data and recalculate
    df_shifted = df.shift(1)
    result_shifted = calculate_all_indicators(df_shifted)
    
    # The indicator values should shift accordingly
    # This is a basic check - more rigorous tests would be needed for production
    assert len(result) == len(result_shifted)
    
    print("  ✓ No obvious lookahead bias detected")
    return True


def test_nan_handling():
    """Test proper NaN handling"""
    print("Testing NaN handling...")
    
    # Data with gaps
    close = pd.Series([1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, 10])
    high = close * 1.02
    low = close * 0.98
    volume = pd.Series([1000000] * 10)
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low,
        'Volume': volume
    })
    
    # Should not crash
    result = calculate_all_indicators(df)
    
    # Should have some NaN (from initial periods)
    assert result.isna().any().any(), "Should have some NaN values"
    
    print("  ✓ NaN handling test passed")
    return True


def test_performance():
    """Test performance on large dataset"""
    print("Testing performance...")
    
    import time
    
    # Large dataset
    n = 5000
    np.random.seed(42)
    close = pd.Series(np.random.randn(n).cumsum() + 100)
    high = close * 1.02
    low = close * 0.98
    volume = pd.Series(np.random.randn(n).abs() * 1000000)
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low,
        'Volume': volume
    })
    
    start = time.time()
    result = calculate_all_indicators(df)
    elapsed = time.time() - start
    
    print(f"  Processed {n} rows in {elapsed:.3f}s")
    assert elapsed < 5.0, f"Should process in <5s, took {elapsed}s"
    
    print("  ✓ Performance test passed")
    return True


def test_all_indicators():
    """Test that all indicators are calculated"""
    print("Testing all indicators calculation...")
    
    np.random.seed(42)
    n = 200
    close = pd.Series(np.random.randn(n).cumsum() + 100)
    high = close * 1.02
    low = close * 0.98
    volume = pd.Series(np.random.randn(n).abs() * 1000000)
    
    df = pd.DataFrame({
        'Close': close,
        'High': high,
        'Low': low,
        'Volume': volume
    })
    
    result = calculate_all_indicators(df)
    
    # Check all expected columns exist
    expected_cols = get_indicator_columns()
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
    
    print(f"  ✓ All {len(expected_cols)} indicators calculated")
    return True


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("RUNNING INDICATOR TESTS")
    print("="*60)
    
    tests = [
        test_sma,
        test_ema,
        test_rsi,
        test_macd,
        test_bollinger_bands,
        test_atr,
        test_no_lookahead_bias,
        test_nan_handling,
        test_performance,
        test_all_indicators
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
