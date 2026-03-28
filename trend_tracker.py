#!/usr/bin/env python3
"""
Trend Tracker

Tracks indicator trends and generates alerts for significant changes.

Features:
- Trend direction analysis (up/down/sideways)
- Momentum changes
- Breakout detection
- Divergence identification

Usage:
    python trend_tracker.py --symbols 2330,2317
    python trend_tracker.py --all
"""

import argparse
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config import STOCK_UNIVERSE, ANALYSIS_CONFIG, DB_PATH
from indicators import add_indicators

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_stock_data(symbol: str, days: int = None) -> Optional[pd.DataFrame]:
    """
    Get historical data for a stock.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
    days : int
        Number of days to retrieve
    
    Returns
    -------
    pd.DataFrame
        Stock data with indicators
    """
    if days is None:
        days = ANALYSIS_CONFIG['history_days']
    
    conn = sqlite3.connect(DB_PATH)
    
    query = '''
        SELECT date, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=[symbol, days])
    conn.close()
    
    if df.empty:
        logger.warning(f"No data for {symbol}")
        return None
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df.sort_index()
    
    # Add indicators
    df_with_indicators = add_indicators(df)
    
    return df_with_indicators


def analyze_trend_direction(df: pd.DataFrame, column: str = 'close', window: int = 20) -> Dict:
    """
    Analyze trend direction for a price series.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with price data
    column : str
        Column to analyze
    window : int
        Window for trend analysis
    
    Returns
    -------
    Dict
        Trend analysis results
    """
    if len(df) < window:
        return {'direction': 'insufficient_data'}
    
    recent = df[column].iloc[-1]
    past = df[column].iloc[-window]
    
    # Simple trend: compare current to window ago
    change_pct = (recent - past) / past * 100
    
    if change_pct > 5:
        direction = 'strong_uptrend'
    elif change_pct > 0:
        direction = 'uptrend'
    elif change_pct > -5:
        direction = 'sideways'
    elif change_pct > -10:
        direction = 'downtrend'
    else:
        direction = 'strong_downtrend'
    
    return {
        'direction': direction,
        'change_pct': round(change_pct, 2),
        'current_value': round(recent, 2),
        'past_value': round(past, 2)
    }


def analyze_momentum(df: pd.DataFrame) -> Dict:
    """
    Analyze momentum indicators.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with RSI, MACD, etc.
    
    Returns
    -------
    Dict
        Momentum analysis
    """
    result = {}
    
    # RSI analysis
    if 'rsi_14' in df.columns:
        current_rsi = df['rsi_14'].iloc[-1]
        past_rsi = df['rsi_14'].iloc[-5] if len(df) > 5 else current_rsi
        
        if current_rsi > 70:
            result['rsi_status'] = 'overbought'
        elif current_rsi < 30:
            result['rsi_status'] = 'oversold'
        else:
            result['rsi_status'] = 'neutral'
        
        result['rsi_trend'] = 'improving' if current_rsi > past_rsi else 'weakening'
        result['rsi_value'] = round(current_rsi, 2)
    
    # MACD analysis
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        current_macd = df['macd'].iloc[-1]
        current_signal = df['macd_signal'].iloc[-1]
        
        if current_macd > current_signal:
            result['macd_status'] = 'bullish'
        else:
            result['macd_status'] = 'bearish'
        
        # Check for crossover
        if len(df) > 1:
            prev_macd = df['macd'].iloc[-2]
            prev_signal = df['macd_signal'].iloc[-2]
            
            if prev_macd <= prev_signal and current_macd > current_signal:
                result['macd_signal_event'] = 'bullish_crossover'
            elif prev_macd >= prev_signal and current_macd < current_signal:
                result['macd_signal_event'] = 'bearish_crossover'
    
    return result


def analyze_volatility(df: pd.DataFrame) -> Dict:
    """
    Analyze volatility indicators.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with volatility data
    
    Returns
    -------
    Dict
        Volatility analysis
    """
    result = {}
    
    # Bollinger Bands position
    if 'bb_position' in df.columns:
        bb_pos = df['bb_position'].iloc[-1]
        
        if bb_pos > 0.9:
            result['bb_status'] = 'near_upper_band'
        elif bb_pos < 0.1:
            result['bb_status'] = 'near_lower_band'
        else:
            result['bb_status'] = 'middle'
        
        result['bb_position'] = round(bb_pos, 3)
    
    # ATR (volatility)
    if 'atr_14' in df.columns:
        current_atr = df['atr_14'].iloc[-1]
        avg_atr = df['atr_14'].mean()
        
        if current_atr > avg_atr * 1.5:
            result['volatility'] = 'high'
        elif current_atr < avg_atr * 0.5:
            result['volatility'] = 'low'
        else:
            result['volatility'] = 'normal'
        
        result['atr'] = round(current_atr, 2)
    
    return result


def generate_alerts(symbol: str, trend: Dict, momentum: Dict, volatility: Dict) -> List[str]:
    """
    Generate trading alerts based on analysis.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
    trend : Dict
        Trend analysis
    momentum : Dict
        Momentum analysis
    volatility : Dict
        Volatility analysis
    
    Returns
    -------
    List[str]
        List of alert messages
    """
    alerts = []
    
    # Trend alerts
    if trend.get('direction') == 'strong_uptrend':
        alerts.append(f"📈 {symbol}: Strong uptrend (+{trend['change_pct']}%)")
    elif trend.get('direction') == 'strong_downtrend':
        alerts.append(f"📉 {symbol}: Strong downtrend ({trend['change_pct']}%)")
    
    # Momentum alerts
    if momentum.get('rsi_status') == 'overbought':
        alerts.append(f"⚠️ {symbol}: RSI overbought ({momentum['rsi_value']})")
    elif momentum.get('rsi_status') == 'oversold':
        alerts.append(f"✅ {symbol}: RSI oversold ({momentum['rsi_value']})")
    
    if momentum.get('macd_signal_event') == 'bullish_crossover':
        alerts.append(f"🚀 {symbol}: MACD bullish crossover")
    elif momentum.get('macd_signal_event') == 'bearish_crossover':
        alerts.append(f"💥 {symbol}: MACD bearish crossover")
    
    # Volatility alerts
    if volatility.get('bb_status') == 'near_lower_band':
        alerts.append(f"🎯 {symbol}: Price near lower Bollinger Band")
    elif volatility.get('bb_status') == 'near_upper_band':
        alerts.append(f"🎯 {symbol}: Price near upper Bollinger Band")
    
    return alerts


def analyze_all_stocks(symbols: List[str] = None) -> Dict:
    """
    Analyze all stocks in universe.
    
    Parameters
    ----------
    symbols : List[str], optional
        List of symbols to analyze
    
    Returns
    -------
    Dict
        Analysis results for all stocks
    """
    if symbols is None:
        symbols = list(STOCK_UNIVERSE.keys())
    
    results = {}
    
    for symbol in symbols:
        logger.info(f"Analyzing {symbol}...")
        
        try:
            df = get_stock_data(symbol)
            
            if df is None or df.empty:
                continue
            
            trend = analyze_trend_direction(df)
            momentum = analyze_momentum(df)
            volatility = analyze_volatility(df)
            alerts = generate_alerts(symbol, trend, momentum, volatility)
            
            results[symbol] = {
                'name': STOCK_UNIVERSE.get(symbol, symbol),
                'trend': trend,
                'momentum': momentum,
                'volatility': volatility,
                'alerts': alerts,
                'last_price': df['close'].iloc[-1],
                'last_date': df.index[-1].strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            results[symbol] = {'error': str(e)}
    
    return results


def print_report(results: Dict):
    """
    Print analysis report.
    
    Parameters
    ----------
    results : Dict
        Analysis results
    """
    print("\n" + "="*80)
    print("STOCK TREND ANALYSIS REPORT")
    print("="*80)
    
    for symbol, data in results.items():
        if 'error' in data:
            continue
        
        print(f"\n{symbol} - {data['name']}")
        print(f"  Date: {data['last_date']} | Price: ${data['last_price']:.2f}")
        
        # Trend
        trend = data['trend']
        print(f"  Trend: {trend.get('direction', 'N/A').upper()}")
        if 'change_pct' in trend:
            print(f"    Change: {trend['change_pct']:+.2f}%")
        
        # Momentum
        momentum = data['momentum']
        if momentum:
            print(f"  Momentum:")
            if 'rsi_status' in momentum:
                print(f"    RSI: {momentum['rsi_status']} ({momentum.get('rsi_value', 'N/A')})")
            if 'macd_status' in momentum:
                print(f"    MACD: {momentum['macd_status']}")
        
        # Volatility
        volatility = data['volatility']
        if volatility:
            print(f"  Volatility:")
            for key, value in volatility.items():
                print(f"    {key}: {value}")
        
        # Alerts
        if data['alerts']:
            print(f"  Alerts:")
            for alert in data['alerts']:
                print(f"    {alert}")


def main():
    parser = argparse.ArgumentParser(description='Analyze stock trends')
    parser.add_argument('--symbols', type=str, help='Comma-separated symbols')
    parser.add_argument('--all', action='store_true', help='Analyze all stocks')
    
    args = parser.parse_args()
    
    if args.all:
        symbols = list(STOCK_UNIVERSE.keys())
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        # Default: top tech stocks
        symbols = ['2330', '2317', '2454']
    
    results = analyze_all_stocks(symbols)
    print_report(results)


if __name__ == "__main__":
    main()
