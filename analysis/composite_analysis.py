"""
Composite Technical Analysis

Advanced analysis combining multiple indicators with:
1. Multi-timeframe moving average analysis
2. Dynamic weighted scoring based on market regime
3. Comprehensive signal generation with confidence levels
4. Scenario-based recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum


class TimeFrame(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class MarketRegime(Enum):
    BULL_STRONG = "bull_strong"
    BULL_WEAK = "bull_weak"
    BEAR_STRONG = "bear_strong"
    BEAR_WEAK = "bear_weak"
    SIDEWAYS = "sideways"


class CompositeAnalyzer:
    """
    Advanced composite analysis combining multiple indicators
    with dynamic weighting based on market conditions.
    """
    
    # Moving average timeframes
    SHORT_MAS = ['sma_5', 'sma_10']
    MEDIUM_MAS = ['sma_20', 'sma_60']
    LONG_MAS = ['sma_120']
    
    # Weights for different market regimes
    REGIME_WEIGHTS = {
        MarketRegime.BULL_STRONG: {
            'trend': 0.4,
            'momentum': 0.3,
            'volume': 0.2,
            'volatility': 0.1
        },
        MarketRegime.BULL_WEAK: {
            'trend': 0.3,
            'momentum': 0.3,
            'volume': 0.2,
            'volatility': 0.2
        },
        MarketRegime.BEAR_STRONG: {
            'trend': 0.4,
            'momentum': 0.3,
            'volume': 0.2,
            'volatility': 0.1
        },
        MarketRegime.BEAR_WEAK: {
            'trend': 0.3,
            'momentum': 0.2,
            'volume': 0.2,
            'volatility': 0.3
        },
        MarketRegime.SIDEWAYS: {
            'trend': 0.2,
            'momentum': 0.3,
            'volume': 0.2,
            'volatility': 0.3
        }
    }
    
    def __init__(self):
        pass
    
    def analyze_ma_timeframes(self, df: pd.DataFrame) -> Dict:
        """
        Analyze moving averages across short, medium, and long timeframes
        
        Returns:
            Dict with MA analysis for each timeframe
        """
        latest = df.iloc[-1]
        
        # Short-term MA analysis
        short_bullish = sum(1 for ma in self.SHORT_MAS if ma in df.columns and latest['Close'] > latest[ma])
        short_score = short_bullish / len(self.SHORT_MAS) if self.SHORT_MAS else 0
        
        # Medium-term MA analysis
        medium_bullish = sum(1 for ma in self.MEDIUM_MAS if ma in df.columns and latest['Close'] > latest[ma])
        medium_score = medium_bullish / len(self.MEDIUM_MAS) if self.MEDIUM_MAS else 0
        
        # Long-term MA analysis
        long_bullish = sum(1 for ma in self.LONG_MAS if ma in df.columns and latest['Close'] > latest[ma])
        long_score = long_bullish / len(self.LONG_MAS) if self.LONG_MAS else 0
        
        # MA alignment (golden cross/death cross)
        ma_alignment = self._check_ma_alignment(df)
        
        # Timeframe consensus
        timeframe_scores = [short_score, medium_score, long_score]
        consensus_strength = sum(1 for s in timeframe_scores if s > 0.5) / len(timeframe_scores)
        
        return {
            'short_term': {
                'score': short_score,
                'signal': 'BULLISH' if short_score > 0.5 else 'BEARISH',
                'bullish_count': short_bullish,
                'total': len(self.SHORT_MAS)
            },
            'medium_term': {
                'score': medium_score,
                'signal': 'BULLISH' if medium_score > 0.5 else 'BEARISH',
                'bullish_count': medium_bullish,
                'total': len(self.MEDIUM_MAS)
            },
            'long_term': {
                'score': long_score,
                'signal': 'BULLISH' if long_score > 0.5 else 'BEARISH',
                'bullish_count': long_bullish,
                'total': len(self.LONG_MAS)
            },
            'ma_alignment': ma_alignment,
            'timeframe_consensus': consensus_strength,
            'overall_score': (short_score * 0.4 + medium_score * 0.4 + long_score * 0.2)
        }
    
    def _check_ma_alignment(self, df: pd.DataFrame) -> Dict:
        """
        Check if MAs are aligned (golden cross, death cross, etc.)
        """
        latest = df.iloc[-1]
        
        # Check for golden cross (short > medium > long)
        short_ma = np.mean([latest[ma] for ma in self.SHORT_MAS if ma in df.columns])
        medium_ma = np.mean([latest[ma] for ma in self.MEDIUM_MAS if ma in df.columns])
        long_ma = np.mean([latest[ma] for ma in self.LONG_MAS if ma in df.columns])
        
        golden_cross = short_ma > medium_ma > long_ma
        death_cross = short_ma < medium_ma < long_ma
        
        # MA spread
        ma_spread = (short_ma - long_ma) / long_ma * 100 if long_ma > 0 else 0
        
        return {
            'golden_cross': golden_cross,
            'death_cross': death_cross,
            'short_ma': short_ma,
            'medium_ma': medium_ma,
            'long_ma': long_ma,
            'spread_pct': ma_spread,
            'alignment': 'BULLISH' if golden_cross else 'BEARISH' if death_cross else 'MIXED'
        }
    
    def dynamic_momentum_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Analyze momentum with dynamic weighting based on market conditions
        """
        latest = df.iloc[-1]
        
        # RSI analysis with context
        rsi = latest.get('rsi_14', 50)
        if rsi > 70:
            rsi_signal = 'OVERBOUGHT'
            rsi_score = 0.2
        elif rsi < 30:
            rsi_signal = 'OVERSOLD'
            rsi_score = 0.8
        else:
            rsi_signal = 'NEUTRAL'
            rsi_score = 0.5 + (50 - abs(rsi - 50)) / 100
        
        # MACD analysis with trend context
        macd_score = 0.5
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            macd_bullish = latest['macd'] > latest['macd_signal']
            macd_score = 0.8 if macd_bullish else 0.3
            
            # Check for MACD crossover
            if len(df) > 1:
                prev = df.iloc[-2]
                crossover = (latest['macd'] > latest['macd_signal'] and 
                           prev['macd'] <= prev['macd_signal'])
                crossunder = (latest['macd'] < latest['macd_signal'] and 
                            prev['macd'] >= prev['macd_signal'])
            else:
                crossover = crossunder = False
        else:
            crossover = crossunder = False
        
        # Stochastic analysis
        stoch_score = 0.5
        if 'stoch_k' in df.columns:
            stoch_k = latest['stoch_k']
            if stoch_k > 80:
                stoch_signal = 'OVERBOUGHT'
                stoch_score = 0.3
            elif stoch_k < 20:
                stoch_signal = 'OVERSOLD'
                stoch_score = 0.7
            else:
                stoch_signal = 'NEUTRAL'
                stoch_score = 0.5
        else:
            stoch_signal = 'N/A'
        
        # Dynamic weighting based on volatility
        volatility = self._calculate_volatility_regime(df)
        
        # Adjust weights based on regime
        if volatility == 'HIGH':
            # In high volatility, trust momentum less
            momentum_score = rsi_score * 0.4 + macd_score * 0.4 + stoch_score * 0.2
        else:
            # In normal volatility, balanced weighting
            momentum_score = rsi_score * 0.4 + macd_score * 0.3 + stoch_score * 0.3
        
        return {
            'rsi': {
                'value': rsi,
                'signal': rsi_signal,
                'score': rsi_score
            },
            'macd': {
                'signal': 'BULLISH' if macd_score > 0.5 else 'BEARISH',
                'crossover': crossover,
                'crossunder': crossunder,
                'score': macd_score
            },
            'stochastic': {
                'signal': stoch_signal,
                'score': stoch_score
            },
            'volatility_regime': volatility,
            'overall_score': momentum_score,
            'confidence': 'HIGH' if volatility == 'LOW' else 'MEDIUM'
        }
    
    def _calculate_volatility_regime(self, df: pd.DataFrame) -> str:
        """
        Determine volatility regime
        """
        if 'bb_width' not in df.columns:
            return 'NORMAL'
        
        current_bb_width = df['bb_width'].iloc[-1]
        avg_bb_width = df['bb_width'].mean()
        
        if current_bb_width > avg_bb_width * 1.5:
            return 'HIGH'
        elif current_bb_width < avg_bb_width * 0.5:
            return 'LOW'
        else:
            return 'NORMAL'
    
    def determine_market_regime(self, df: pd.DataFrame) -> MarketRegime:
        """
        Determine current market regime based on multiple factors
        """
        ma_analysis = self.analyze_ma_timeframes(df)
        ma_score = ma_analysis['overall_score']
        
        # Trend strength
        if 'adx_14' in df.columns:
            adx = df['adx_14'].iloc[-1]
            trend_strength = 'STRONG' if adx > 25 else 'WEAK'
        else:
            trend_strength = 'UNKNOWN'
        
        # Determine regime
        if ma_score > 0.7:
            regime = MarketRegime.BULL_STRONG if trend_strength == 'STRONG' else MarketRegime.BULL_WEAK
        elif ma_score < 0.3:
            regime = MarketRegime.BEAR_STRONG if trend_strength == 'STRONG' else MarketRegime.BEAR_WEAK
        else:
            regime = MarketRegime.SIDEWAYS
        
        return regime
    
    def composite_score(self, df: pd.DataFrame) -> Dict:
        """
        Generate composite score combining all indicators with dynamic weighting
        """
        # Get market regime
        regime = self.determine_market_regime(df)
        
        # Get weights for current regime
        weights = self.REGIME_WEIGHTS[regime]
        
        # Calculate component scores
        ma_analysis = self.analyze_ma_timeframes(df)
        momentum_analysis = self.dynamic_momentum_analysis(df)
        
        # Volume score (simplified)
        volume_score = 0.5
        if 'obv' in df.columns:
            obv_trend = df['obv'].iloc[-1] > df['obv'].rolling(window=10).mean().iloc[-1]
            volume_score = 0.7 if obv_trend else 0.3
        
        # Volatility score
        volatility_regime = self._calculate_volatility_regime(df)
        volatility_score = 0.7 if volatility_regime == 'LOW' else 0.5 if volatility_regime == 'NORMAL' else 0.3
        
        # Weighted composite score
        composite = (
            ma_analysis['overall_score'] * weights['trend'] +
            momentum_analysis['overall_score'] * weights['momentum'] +
            volume_score * weights['volume'] +
            volatility_score * weights['volatility']
        )
        
        # Generate signal
        if composite > 0.7:
            signal = 'STRONG BUY'
            confidence = 'HIGH'
        elif composite > 0.55:
            signal = 'BUY'
            confidence = 'MEDIUM'
        elif composite > 0.45:
            signal = 'HOLD'
            confidence = 'MEDIUM'
        elif composite > 0.3:
            signal = 'SELL'
            confidence = 'MEDIUM'
        else:
            signal = 'STRONG SELL'
            confidence = 'HIGH'
        
        return {
            'regime': regime,
            'composite_score': composite,
            'signal': signal,
            'confidence': confidence,
            'components': {
                'trend': ma_analysis['overall_score'],
                'momentum': momentum_analysis['overall_score'],
                'volume': volume_score,
                'volatility': volatility_score
            },
            'weights': weights,
            'ma_analysis': ma_analysis,
            'momentum_analysis': momentum_analysis
        }
    
    def generate_scenario_analysis(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate scenario-based analysis
        """
        scenarios = []
        
        # Bull scenario
        bull_df = df.copy()
        if len(bull_df) > 0:
            last_price = bull_df['Close'].iloc[-1]
            bull_target = last_price * 1.05  # +5%
            bull_stop = last_price * 0.95    # -5%
            
            scenarios.append({
                'name': 'Bull Case',
                'probability': '30%',
                'target': bull_target,
                'stop_loss': bull_stop,
                'conditions': [
                    'Price breaks above recent high',
                    'Volume increases >20%',
                    'RSI stays above 50'
                ],
                'action': 'BUY on breakout'
            })
        
        # Bear scenario
        bear_target = df['Close'].iloc[-1] * 0.95  # -5%
        bear_stop = df['Close'].iloc[-1] * 1.05    # +5%
        
        scenarios.append({
            'name': 'Bear Case',
            'probability': '30%',
            'target': bear_target,
            'stop_loss': bear_stop,
            'conditions': [
                'Price breaks below support',
                'Volume spike on downside',
                'RSI drops below 50'
            ],
            'action': 'SELL on breakdown'
        })
        
        # Sideways scenario
        scenarios.append({
            'name': 'Sideways Case',
            'probability': '40%',
            'target': df['Close'].iloc[-1] * 1.02,
            'stop_loss': df['Close'].iloc[-1] * 0.98,
            'conditions': [
                'Price oscillates in range',
                'Low volume',
                'Mixed signals'
            ],
            'action': 'WAIT for breakout'
        })
        
        return scenarios
    
    def full_analysis(self, df: pd.DataFrame, symbol: str = '') -> Dict:
        """
        Complete composite analysis
        """
        # All components
        ma_analysis = self.analyze_ma_timeframes(df)
        momentum_analysis = self.dynamic_momentum_analysis(df)
        composite = self.composite_score(df)
        scenarios = self.generate_scenario_analysis(df)
        
        return {
            'symbol': symbol,
            'timestamp': df.index[-1],
            'price': df['Close'].iloc[-1],
            'market_regime': composite['regime'],
            'composite_score': composite['composite_score'],
            'signal': composite['signal'],
            'confidence': composite['confidence'],
            'timeframe_analysis': {
                'short_term': ma_analysis['short_term'],
                'medium_term': ma_analysis['medium_term'],
                'long_term': ma_analysis['long_term'],
                'ma_alignment': ma_analysis['ma_alignment']
            },
            'momentum_analysis': momentum_analysis,
            'component_scores': composite['components'],
            'weights': composite['weights'],
            'scenarios': scenarios,
            'recommendation': self._generate_recommendation(composite, scenarios)
        }
    
    def _generate_recommendation(self, composite: Dict, scenarios: List[Dict]) -> str:
        """
        Generate human-readable recommendation
        """
        signal = composite['signal']
        regime = composite['regime']
        score = composite['composite_score']
        
        rec = f"**當前訊號**: {signal}\n"
        rec += f"**市場狀態**: {regime.value}\n"
        rec += f"**綜合評分**: {score:.2f}/1.00\n\n"
        
        # 短中長期分析
        tf = composite.get('ma_analysis', {}).get('timeframe_analysis', {})
        if tf:
            rec += "**時間框架分析**:\n"
            rec += f"- 短期 (5-10 日): {tf.get('short_term', {}).get('signal', 'N/A')}\n"
            rec += f"- 中期 (20-60 日): {tf.get('medium_term', {}).get('signal', 'N/A')}\n"
            rec += f"- 長期 (120 日): {tf.get('long_term', {}).get('signal', 'N/A')}\n\n"
        
        # 關鍵發現
        rec += "**關鍵發現**:\n"
        
        # MA alignment
        ma_align = tf.get('ma_alignment', {})
        if ma_align.get('golden_cross'):
            rec += "✅ 出現黃金交叉（短線多頭排列）\n"
        elif ma_align.get('death_cross'):
            rec += "❌ 出現死亡交叉（短線空頭排列）\n"
        
        # Momentum
        mom = composite.get('momentum_analysis', {})
        rsi_signal = mom.get('rsi', {}).get('signal', '')
        if rsi_signal == 'OVERBOUGHT':
            rec += "⚠️ RSI 超買，留意回檔風險\n"
        elif rsi_signal == 'OVERSOLD':
            rec += "💡 RSI 超賣，留意反彈機會\n"
        
        if mom.get('macd', {}).get('crossover'):
            rec += "✅ MACD 黃金交叉\n"
        elif mom.get('macd', {}).get('crossunder'):
            rec += "❌ MACD 死亡交叉\n"
        
        # 情境分析
        rec += "\n**情境分析**:\n"
        for scenario in scenarios[:2]:
            rec += f"- {scenario['name']} ({scenario['probability']}): {scenario['action']}\n"
        
        return rec


def analyze_composite(symbol: str, period: str = '3mo') -> Dict:
    """
    Convenience function for quick composite analysis
    """
    import yfinance as yf
    from indicators.indicator_base import calculate_all_indicators
    
    # Load data
    ticker = yf.Ticker(f"{symbol}.TW")
    df = ticker.history(period=period)
    
    if len(df) < 30:
        return {'error': 'Insufficient data'}
    
    # Add indicators
    df = calculate_all_indicators(df)
    
    # Run analysis
    analyzer = CompositeAnalyzer()
    return analyzer.full_analysis(df, symbol)