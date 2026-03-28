#!/usr/bin/env python3
"""
Composite Analysis Demo

Demonstrates the advanced composite analysis with:
1. Multi-timeframe MA analysis
2. Dynamic momentum scoring
3. Market regime detection
4. Scenario-based recommendations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.composite_analysis import CompositeAnalyzer, analyze_composite
from indicators.indicator_base import calculate_all_indicators
import yfinance as yf


def demo_single_stock(symbol: str = '2330'):
    """
    Demo analysis for a single stock
    """
    print("="*80)
    print(f"COMPOSITE ANALYSIS: {symbol}")
    print("="*80)
    
    # Load data
    ticker = yf.Ticker(f"{symbol}.TW")
    df = ticker.history(period='3mo')
    
    if len(df) < 30:
        print(f"Insufficient data for {symbol}")
        return
    
    # Add indicators
    df = calculate_all_indicators(df)
    
    # Run composite analysis
    analyzer = CompositeAnalyzer()
    result = analyzer.full_analysis(df, symbol)
    
    # Display results
    print(f"\n📊 {symbol} - {result['symbol']}")
    print(f"Price: NT$ {result['price']:.2f}")
    print(f"Analysis Date: {result['timestamp']}")
    
    print(f"\n🎯 SIGNAL: {result['signal']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Composite Score: {result['composite_score']:.2f}/1.00")
    print(f"Market Regime: {result['market_regime'].value}")
    
    # Timeframe analysis
    tf = result['timeframe_analysis']
    print(f"\n⏰ TIMEFRAME ANALYSIS:")
    print(f"  Short-term (5-10 day):  {tf['short_term']['signal']} (Score: {tf['short_term']['score']:.2f})")
    print(f"  Medium-term (20-60 day): {tf['medium_term']['signal']} (Score: {tf['medium_term']['score']:.2f})")
    print(f"  Long-term (120 day):    {tf['long_term']['signal']} (Score: {tf['long_term']['score']:.2f})")
    
    # MA Alignment
    ma = tf['ma_alignment']
    print(f"\n📈 MA ALIGNMENT:")
    print(f"  Status: {ma['alignment']}")
    print(f"  Short MA: {ma['short_ma']:.2f}")
    print(f"  Medium MA: {ma['medium_ma']:.2f}")
    print(f"  Long MA: {ma['long_ma']:.2f}")
    print(f"  Spread: {ma['spread_pct']:+.2f}%")
    
    if ma['golden_cross']:
        print("  ✨ GOLDEN CROSS DETECTED!")
    elif ma['death_cross']:
        print("  ⚠️ DEATH CROSS DETECTED!")
    
    # Momentum analysis
    mom = result['momentum_analysis']
    print(f"\n🚀 MOMENTUM ANALYSIS:")
    print(f"  RSI: {mom['rsi']['value']:.1f} ({mom['rsi']['signal']})")
    print(f"  MACD: {mom['macd']['signal']} (Score: {mom['macd']['score']:.2f})")
    if mom['macd']['crossover']:
        print("  🟢 MACD BULLISH CROSSOVER!")
    elif mom['macd']['crossunder']:
        print("  🔴 MACD BEARISH CROSSUNDER!")
    print(f"  Stochastic: {mom['stochastic']['signal']}")
    print(f"  Volatility Regime: {mom['volatility_regime']}")
    
    # Component scores
    print(f"\n📊 COMPONENT SCORES:")
    for comp, score in result['component_scores'].items():
        weight = result['weights'][comp]
        print(f"  {comp.capitalize():12} {score:.2f} (weight: {weight:.1%})")
    
    # Scenarios
    print(f"\n🔮 SCENARIO ANALYSIS:")
    for scenario in result['scenarios']:
        print(f"\n  {scenario['name']} ({scenario['probability']}):")
        print(f"    Target: {scenario['target']:.2f}")
        print(f"    Stop Loss: {scenario['stop_loss']:.2f}")
        print(f"    Action: {scenario['action']}")
        print(f"    Conditions:")
        for condition in scenario['conditions']:
            print(f"      - {condition}")
    
    # Final recommendation
    print(f"\n💡 RECOMMENDATION:")
    print(result['recommendation'])
    
    return result


def demo_multiple_stocks(symbols: list):
    """
    Demo analysis for multiple stocks
    """
    print("="*80)
    print("COMPOSITE ANALYSIS - MULTIPLE STOCKS")
    print("="*80)
    
    results = []
    
    for symbol in symbols:
        try:
            result = analyze_composite(symbol)
            if 'error' not in result:
                results.append(result)
                
                # Quick summary
                signal_emoji = {
                    'STRONG BUY': '🟢',
                    'BUY': '🟢',
                    'HOLD': '🟡',
                    'SELL': '🔴',
                    'STRONG SELL': '🔴'
                }
                emoji = signal_emoji.get(result['signal'], '⚪')
                print(f"{emoji} {symbol}: {result['signal']} (Score: {result['composite_score']:.2f})")
            else:
                print(f"⚠️ {symbol}: {result['error']}")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
    
    # Sort by score
    print("\n" + "="*80)
    print("RANKED BY COMPOSITE SCORE")
    print("="*80)
    
    sorted_results = sorted(results, key=lambda x: x['composite_score'], reverse=True)
    
    print(f"{'Rank':<5} {'Symbol':<8} {'Signal':<15} {'Score':<8} {'Regime':<20}")
    print("-" * 60)
    
    for i, result in enumerate(sorted_results, 1):
        print(f"{i:<5} {result['symbol']:<8} {result['signal']:<15} {result['composite_score']:<8.2f} {result['market_regime'].value:<20}")
    
    return sorted_results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        demo_single_stock(symbol)
    else:
        # Demo multiple stocks
        symbols = ['2330', '2317', '2454', '2800', '1301', '1101', '0050']
        demo_multiple_stocks(symbols)
