"""
Technical Indicator Analysis Module

Analyzes stocks based on 20+ technical indicators and generates:
- Trend analysis
- Momentum signals
- Volatility assessment
- Volume confirmation
- Overall scoring
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from indicators.indicator_base import calculate_all_indicators, get_indicator_columns


class IndicatorAnalyzer:
    """
    Analyze stocks using technical indicators
    
    Usage:
        analyzer = IndicatorAnalyzer()
        df = analyzer.load_data('2330.TW')
        df = analyzer.add_indicators(df)
        analysis = analyzer.analyze(df)
        report = analyzer.generate_report(analysis)
    """
    
    def __init__(self):
        self.indicator_columns = get_indicator_columns()
    
    def load_data(self, symbol: str, period: str = '2mo') -> pd.DataFrame:
        """Load stock data from yfinance"""
        import yfinance as yf
        ticker = yf.Ticker(f"{symbol}.TW")
        df = ticker.history(period=period)
        return df
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators to dataframe"""
        return calculate_all_indicators(df)
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        Analyze trend indicators
        - SMA alignment
        - MACD signal
        - ADX strength
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
        
        # SMA Alignment
        sma_bullish = (latest['sma_5'] > latest['sma_10'] > latest['sma_20'] > latest['sma_60'])
        
        # MACD
        macd_bullish = latest['macd'] > latest['macd_signal']
        macd_crossing = (latest['macd'] > latest['macd_signal'] and 
                        prev['macd'] <= prev['macd_signal'])
        
        # ADX
        adx_strong = latest['adx_14'] > 25
        adx_weak = latest['adx_14'] < 20
        
        # Aroon
        aroon_bullish = latest['aroon_up'] > 70
        aroon_bearish = latest['aroon_down'] > 70
        
        return {
            'trend': 'BULLISH' if sma_bullish else 'BEARISH',
            'sma_alignment': sma_bullish,
            'macd_signal': 'BUY' if macd_bullish else 'SELL',
            'macd_crossing': macd_crossing,
            'adx_strength': 'STRONG' if adx_strong else 'WEAK' if adx_weak else 'MODERATE',
            'aroon_signal': 'BULLISH' if aroon_bullish else 'BEARISH' if aroon_bearish else 'NEUTRAL',
            'trend_score': sum([
                sma_bullish,
                macd_bullish,
                adx_strong,
                latest['aroon_up'] > latest['aroon_down']
            ]) / 4
        }
    
    def analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """
        Analyze momentum indicators
        - RSI
        - Stochastic
        - CCI
        - Williams %R
        """
        latest = df.iloc[-1]
        
        # RSI
        rsi_overbought = latest['rsi_14'] > 70
        rsi_oversold = latest['rsi_14'] < 30
        rsi_neutral = not rsi_overbought and not rsi_oversold
        
        # Stochastic
        stoch_overbought = latest['stoch_k'] > 80
        stoch_oversold = latest['stoch_k'] < 20
        stoch_bullish_cross = latest['stoch_k'] > latest['stoch_d'] and prev['stoch_k'] <= prev['stoch_d'] if len(df) > 1 else False
        
        # CCI
        cci_overbought = latest['cci_20'] > 100
        cci_oversold = latest['cci_20'] < -100
        
        # Williams %R
        wr_overbought = latest['williams_r'] > -20
        wr_oversold = latest['williams_r'] < -80
        
        # MFI
        mfi_overbought = latest['mfi_14'] > 80
        mfi_oversold = latest['mfi_14'] < 20
        
        return {
            'rsi_status': 'OVERBOUGHT' if rsi_overbought else 'OVERSOLD' if rsi_oversold else 'NEUTRAL',
            'rsi_value': latest['rsi_14'],
            'stochastic_status': 'OVERBOUGHT' if stoch_overbought else 'OVERSOLD' if stoch_oversold else 'NEUTRAL',
            'stochastic_signal': latest['stoch_k'],
            'cci_status': 'OVERBOUGHT' if cci_overbought else 'OVERSOLD' if cci_oversold else 'NEUTRAL',
            'williams_status': 'OVERBOUGHT' if wr_overbought else 'OVERSOLD' if wr_oversold else 'NEUTRAL',
            'mfi_status': 'OVERBOUGHT' if mfi_overbought else 'OVERSOLD' if mfi_oversold else 'NEUTRAL',
            'momentum_score': sum([
                not rsi_overbought,
                not stoch_overbought,
                not cci_overbought,
                not wr_overbought
            ]) / 4
        }
    
    def analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """
        Analyze volatility indicators
        - Bollinger Bands
        - ATR
        - Keltner Channel
        """
        latest = df.iloc[-1]
        
        # Bollinger Bands
        bb_position = latest['bb_pct']
        bb_squeeze = latest['bb_width'] < df['bb_width'].mean()
        bb_expansion = latest['bb_width'] > df['bb_width'].mean()
        
        # Price position
        price_near_upper = latest['Close'] > latest['bb_upper'] * 0.98
        price_near_lower = latest['Close'] < latest['bb_lower'] * 1.02
        
        # Keltner
        inside_kc = (latest['Close'] > latest['kc_lower'] and 
                    latest['Close'] < latest['kc_upper'])
        
        return {
            'bb_position': bb_position,
            'bb_status': 'UPPER' if price_near_upper else 'LOWER' if price_near_lower else 'MIDDLE',
            'bb_squeeze': bb_squeeze,
            'bb_expansion': bb_expansion,
            'atr_value': latest['atr_14'],
            'volatility_regime': 'HIGH' if latest['bb_width'] > df['bb_width'].mean() else 'LOW',
            'keltner_position': 'INSIDE' if inside_kc else 'OUTSIDE',
            'volatility_score': 0.5 if bb_squeeze else 0.7 if bb_expansion else 0.5
        }
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """
        Analyze volume indicators
        - OBV trend
        - Volume SMA
        - MFI
        """
        latest = df.iloc[-1]
        
        # OBV trend
        obv_ma = df['obv'].rolling(window=10).mean()
        obv_uptrend = latest['obv'] > obv_ma.iloc[-1]
        
        # Volume trend
        volume_ma = df['Volume'].rolling(window=20).mean()
        volume_spike = latest['Volume'] > volume_ma.iloc[-1] * 1.5
        volume_dry = latest['Volume'] < volume_ma.iloc[-1] * 0.5
        
        return {
            'obv_trend': 'UPTREND' if obv_uptrend else 'DOWNTREND',
            'volume_trend': 'HIGH' if latest['Volume'] > volume_ma.iloc[-1] else 'LOW',
            'volume_spike': volume_spike,
            'volume_dry': volume_dry,
            'mfi_value': latest['mfi_14'],
            'volume_score': sum([
                obv_uptrend,
                latest['Volume'] > volume_ma.iloc[-1]
            ]) / 2
        }
    
    def generate_signal(self, trend: Dict, momentum: Dict, volatility: Dict, volume: Dict) -> Dict:
        """
        Generate overall trading signal
        """
        # Calculate scores
        trend_score = trend['trend_score']
        momentum_score = momentum['momentum_score']
        volatility_score = volatility['volatility_score']
        volume_score = volume['volume_score']
        
        # Overall score
        overall_score = (trend_score + momentum_score + volatility_score + volume_score) / 4
        
        # Signal
        if overall_score > 0.7:
            signal = 'STRONG BUY'
        elif overall_score > 0.5:
            signal = 'BUY'
        elif overall_score > 0.3:
            signal = 'HOLD'
        else:
            signal = 'SELL'
        
        # Confidence
        confidence = 'HIGH' if overall_score > 0.7 or overall_score < 0.3 else 'MEDIUM'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'overall_score': overall_score,
            'trend_score': trend_score,
            'momentum_score': momentum_score,
            'volatility_score': volatility_score,
            'volume_score': volume_score
        }
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete analysis of a stock
        
        Returns:
            Dictionary with all analysis results
        """
        # Add indicators if not present
        if 'sma_20' not in df.columns:
            df = self.add_indicators(df)
        
        # Drop NaN rows
        df = df.dropna()
        
        if len(df) == 0:
            return {'error': 'Insufficient data'}
        
        # Run all analyses
        trend = self.analyze_trend(df)
        momentum = self.analyze_momentum(df)
        volatility = self.analyze_volatility(df)
        volume = self.analyze_volume(df)
        signal = self.generate_signal(trend, momentum, volatility, volume)
        
        return {
            'trend': trend,
            'momentum': momentum,
            'volatility': volatility,
            'volume': volume,
            'signal': signal,
            'latest_price': df.iloc[-1]['Close'],
            'timestamp': df.index[-1]
        }
    
    def analyze_multiple(self, symbols: List[str], period: str = '2mo') -> Dict:
        """
        Analyze multiple stocks
        
        Returns:
            Dictionary with analysis for each symbol
        """
        results = {}
        for symbol in symbols:
            try:
                df = self.load_data(symbol, period)
                if len(df) == 0:
                    results[symbol] = {'error': 'No data'}
                    continue
                    
                analysis = self.analyze(df)
                results[symbol] = analysis
            except Exception as e:
                results[symbol] = {'error': str(e)}
        
        return results
    
    def generate_report(self, analysis: Dict, symbol: str = '') -> str:
        """
        Generate human-readable report from analysis
        """
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        report = f"""
# Technical Analysis Report: {symbol}

## Summary
- **Signal**: {analysis['signal']['signal']}
- **Confidence**: {analysis['signal']['confidence']}
- **Overall Score**: {analysis['signal']['overall_score']:.2f}/1.00
- **Latest Price**: {analysis['latest_price']:.2f}

## Trend Analysis
- **Trend**: {analysis['trend']['trend']}
- **SMA Alignment**: {'Bullish' if analysis['trend']['sma_alignment'] else 'Bearish'}
- **MACD Signal**: {analysis['trend']['macd_signal']}
- **ADX Strength**: {analysis['trend']['adx_strength']}

## Momentum
- **RSI**: {analysis['momentum']['rsi_value']:.1f} ({analysis['momentum']['rsi_status']})
- **Stochastic**: {analysis['momentum']['stochastic_signal']:.1f} ({analysis['momentum']['stochastic_status']})
- **CCI**: {analysis['momentum']['cci_status']}
- **Williams %R**: {analysis['momentum']['williams_status']}

## Volatility
- **BB Position**: {analysis['volatility']['bb_status']}
- **BB Squeeze**: {'Yes' if analysis['volatility']['bb_squeeze'] else 'No'}
- **ATR**: {analysis['volatility']['atr_value']:.2f}
- **Regime**: {analysis['volatility']['volatility_regime']}

## Volume
- **OBV Trend**: {analysis['volume']['obv_trend']}
- **Volume**: {analysis['volume']['volume_trend']}
- **Volume Spike**: {'Yes' if analysis['volume']['volume_spike'] else 'No'}

## Scores
- Trend: {analysis['signal']['trend_score']:.2f}
- Momentum: {analysis['signal']['momentum_score']:.2f}
- Volatility: {analysis['signal']['volatility_score']:.2f}
- Volume: {analysis['signal']['volume_score']:.2f}
"""
        return report


# Convenience function
def analyze_stock(symbol: str, period: str = '2mo') -> Dict:
    """Quick analysis of a single stock"""
    analyzer = IndicatorAnalyzer()
    df = analyzer.load_data(symbol, period)
    return analyzer.analyze(df)
