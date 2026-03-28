#!/usr/bin/env python3
"""
Historical Multi-Day Analysis Report

Generates comprehensive report covering multiple days:
- Daily composite scores for each stock
- Trend analysis (score changes over time)
- Golden cross/death cross evolution
- Volume trends
- Sector performance
- Key events detection

Usage:
    python3 reports/generate_historical_report.py [--days 7] [--output reports/historical_analysis.md]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from analysis.composite_analysis import CompositeAnalyzer
from indicators.indicator_base import calculate_all_indicators
from config import STOCK_UNIVERSE
import yfinance as yf
import pandas as pd
import numpy as np


def analyze_historical(symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Analyze a single stock over multiple days
    Returns DataFrame with daily analysis
    """
    # Get more data for indicator calculation
    ticker = yf.Ticker(f"{symbol}.TW")
    df = ticker.history(period=f'{days + 30}d')  # Extra buffer for indicators
    
    if len(df) < 30:
        return None
    
    # Calculate indicators
    df = calculate_all_indicators(df)
    
    # Run composite analysis for each day
    analyzer = CompositeAnalyzer()
    
    results = []
    for i in range(min(days, len(df))):
        # Use rolling window up to current day
        window_df = df.iloc[:len(df)-i if i == 0 else len(df)-i+len(df)-i]
        
        if len(window_df) < 30:
            continue
            
        try:
            analysis = analyzer.full_analysis(window_df, symbol)
            
            # Extract key metrics
            result = {
                'date': df.index[-(i+1)] if i < len(df) else df.index[-1],
                'symbol': symbol,
                'price': df['Close'].iloc[-(i+1)] if i < len(df) else df['Close'].iloc[-1],
                'volume': df['Volume'].iloc[-(i+1)] if i < len(df) else df['Volume'].iloc[-1],
                'composite_score': analysis['composite_score'],
                'signal': analysis['signal'],
                'confidence': analysis['confidence'],
                'market_regime': analysis['market_regime'].value,
                'short_term_signal': analysis['timeframe_analysis']['short_term']['signal'],
                'medium_term_signal': analysis['timeframe_analysis']['medium_term']['signal'],
                'long_term_signal': analysis['timeframe_analysis']['long_term']['signal'],
                'golden_cross': analysis['timeframe_analysis']['ma_alignment'].get('golden_cross', False),
                'death_cross': analysis['timeframe_analysis']['ma_alignment'].get('death_cross', False),
                'ma_spread': analysis['timeframe_analysis']['ma_alignment'].get('spread_pct', 0),
                'rsi': analysis['momentum_analysis']['rsi']['value'],
                'macd_signal': analysis['momentum_analysis']['macd']['signal'],
                'change_pct': ((df['Close'].iloc[-(i+1)] / df['Close'].iloc[-(i+2)]) - 1) * 100 if i+1 < len(df) else 0,
            }
            results.append(result)
        except:
            continue
    
    if not results:
        return None
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('date')
    
    return result_df


def generate_report(days: int = 7, output_file: str = 'reports/historical_analysis.md'):
    """
    Generate comprehensive historical report
    """
    print(f"Generating {days}-day historical analysis...")
    
    # Analyze key stocks
    key_stocks = ['2330', '2317', '2454', '2800', '1301', '1101', '0050']
    
    all_results = {}
    for symbol in key_stocks:
        print(f"  Analyzing {symbol}...")
        try:
            df = analyze_historical(symbol, days)
            if df is not None:
                all_results[symbol] = df
        except Exception as e:
            print(f"    Error: {e}")
    
    if not all_results:
        print("No data available!")
        return
    
    # Generate report
    report = []
    report.append("# 📊 台股歷史综合分析報告")
    report.append(f"\n**報告生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**分析期間**: 過去 {days} 個交易日\n")
    report.append(f"**分析標的**: {', '.join(key_stocks)}\n")
    
    # Section 1: Score Evolution
    report.append("\n## 📈 綜合評分變化趨勢\n")
    report.append("### 評分走勢\n")
    report.append("```\n")
    
    # Create score timeline
    header = f"{'日期':<12}"
    for symbol in key_stocks:
        if symbol in all_results:
            header += f" {symbol:<8}"
    report.append(header)
    report.append("-" * (12 + 10 * len(key_stocks)))
    
    # Get unique dates
    all_dates = set()
    for symbol, df in all_results.items():
        all_dates.update(df['date'].dt.date.tolist())
    all_dates = sorted(list(all_dates))
    
    for date in all_dates[-days:]:
        line = f"{date.strftime('%Y-%m-%d'):<12}"
        for symbol in key_stocks:
            if symbol in all_results:
                symbol_df = all_results[symbol]
                day_data = symbol_df[symbol_df['date'].dt.date == date]
                if not day_data.empty:
                    score = day_data['composite_score'].iloc[0]
                    line += f" {score:<8.2f}"
                else:
                    line += f" {'-':<8}"
            else:
                line += f" {'-':<8}"
        report.append(line)
    
    report.append("```\n")
    
    # Section 2: Signal Changes
    report.append("\n### 訊號變化\n")
    report.append("各股票綜合訊號的變化：\n")
    
    for symbol in key_stocks:
        if symbol in all_results:
            symbol_df = all_results[symbol]
            report.append(f"\n**{symbol}**:\n")
            
            prev_signal = None
            for _, row in symbol_df.iterrows():
                if row['signal'] != prev_signal:
                    date_str = row['date'].strftime('%Y-%m-%d')
                    report.append(f"- {date_str}: {row['signal']} (評分 {row['composite_score']:.2f})")
                    prev_signal = row['signal']
    
    # Section 3: Golden/Death Cross Events
    report.append("\n## 🔔 重要訊號事件\n")
    report.append("### 黃金交叉\n")
    
    golden_events = []
    for symbol in key_stocks:
        if symbol in all_results:
            symbol_df = all_results[symbol]
            golden = symbol_df[symbol_df['golden_cross'] == True]
            for _, row in golden.iterrows():
                golden_events.append({
                    'date': row['date'],
                    'symbol': symbol,
                    'type': 'golden_cross',
                    'score': row['composite_score']
                })
    
    if golden_events:
        for event in sorted(golden_events, key=lambda x: x['date'], reverse=True):
            report.append(f"- {event['date'].strftime('%Y-%m-%d')} {event['symbol']} 黃金交叉 (評分 {event['score']:.2f})")
    else:
        report.append("近期無黃金交叉事件\n")
    
    report.append("\n### 死亡交叉\n")
    death_events = []
    for symbol in key_stocks:
        if symbol in all_results:
            symbol_df = all_results[symbol]
            death = symbol_df[symbol_df['death_cross'] == True]
            for _, row in death.iterrows():
                death_events.append({
                    'date': row['date'],
                    'symbol': symbol,
                    'type': 'death_cross',
                    'score': row['composite_score']
                })
    
    if death_events:
        for event in sorted(death_events, key=lambda x: x['date'], reverse=True):
            report.append(f"- {event['date'].strftime('%Y-%m-%d')} {event['symbol']} 死亡交叉 (評分 {event['score']:.2f})")
    else:
        report.append("近期無死亡交叉事件\n")
    
    # Section 4: Market Regime Evolution
    report.append("\n## 🌡️ 市場狀態變化\n")
    
    for symbol in key_stocks:
        if symbol in all_results:
            symbol_df = all_results[symbol]
            regimes = symbol_df['market_regime'].tolist()
            dates = symbol_df['date'].tolist()
            
            if len(regimes) > 0:
                report.append(f"\n**{symbol}**:\n")
                prev_regime = None
                for i, regime in enumerate(regimes):
                    if regime != prev_regime:
                        report.append(f"- {dates[i].strftime('%Y-%m-%d')}: {regime}")
                        prev_regime = regime
    
    # Section 5: Volume Analysis
    report.append("\n## 📊 成交量趨勢\n")
    
    for symbol in key_stocks:
        if symbol in all_results:
            symbol_df = all_results[symbol]
            avg_vol = symbol_df['volume'].mean()
            latest_vol = symbol_df['volume'].iloc[-1] if len(symbol_df) > 0 else 0
            vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1
            
            report.append(f"\n**{symbol}**:\n")
            report.append(f"- 平均成交量：{avg_vol:,.0f}\n")
            report.append(f"- 最新成交量：{latest_vol:,.0f} ({vol_ratio:.1f}x)\n")
            
            if vol_ratio > 1.5:
                report.append(f"- ⚠️ 成交量異常放大 ({vol_ratio:.1f}x)\n")
            elif vol_ratio < 0.5:
                report.append(f"- ⚠️ 成交量異常萎縮 ({vol_ratio:.1f}x)\n")
    
    # Section 6: Summary & Recommendations
    report.append("\n## 💡 綜合建議\n")
    
    # Latest analysis
    report.append("\n### 目前狀態\n")
    for symbol in key_stocks:
        if symbol in all_results:
            latest = all_results[symbol].iloc[-1]
            report.append(f"**{symbol}**: {latest['signal']} (評分 {latest['composite_score']:.2f}) - {latest['market_regime']}")
    
    # Trend analysis
    report.append("\n### 趨勢觀察\n")
    for symbol in key_stocks:
        if symbol in all_results and len(all_results[symbol]) > 3:
            symbol_df = all_results[symbol]
            score_change = symbol_df['composite_score'].iloc[-1] - symbol_df['composite_score'].iloc[-4] if len(symbol_df) > 3 else 0
            
            if score_change > 0.2:
                report.append(f"- {symbol}: 評分顯著提升 (+{score_change:.2f})，留意轉強訊號")
            elif score_change < -0.2:
                report.append(f"- {symbol}: 評分顯著下降 ({score_change:.2f})，留意轉弱訊號")
    
    # Save report
    report_text = "\n".join(report)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n✅ 報告已儲存至：{output_file}")
    return report_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate historical analysis report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--output', type=str, default='reports/historical_analysis.md', help='Output file path')
    
    args = parser.parse_args()
    
    generate_report(days=args.days, output_file=args.output)
