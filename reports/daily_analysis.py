#!/usr/bin/env python3
"""
Daily Analysis Report with Historical Context

Generates comprehensive daily report including:
- Current day analysis
- Historical comparison (7 days)
- Trend analysis
- Key events detection
- Actionable recommendations

Usage:
    python3 reports/daily_analysis.py [--days 7]
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from analysis.composite_analysis import analyze_composite, CompositeAnalyzer
from indicators.indicator_base import calculate_all_indicators
from config import STOCK_UNIVERSE
import yfinance as yf
import pandas as pd
import numpy as np


def get_historical_data(symbol: str, days: int = 7):
    """Get historical composite scores for a symbol"""
    try:
        ticker = yf.Ticker(f"{symbol}.TW")
        # Get enough data for indicators
        df = ticker.history(period=f'{days + 60}d')
        
        if len(df) < 30:
            return None
        
        # Calculate indicators
        df = calculate_all_indicators(df)
        
        analyzer = CompositeAnalyzer()
        
        historical = []
        # Analyze each day (going backwards)
        for i in range(min(days, len(df) - 30)):
            # Use data up to this day
            end_idx = len(df) - i
            window = df.iloc[:end_idx]
            
            if len(window) < 30:
                continue
            
            try:
                analysis = analyzer.full_analysis(window, symbol)
                
                historical.append({
                    'date': window.index[-1],
                    'price': window['Close'].iloc[-1],
                    'volume': window['Volume'].iloc[-1],
                    'composite_score': analysis['composite_score'],
                    'signal': analysis['signal'],
                    'market_regime': analysis['market_regime'].value,
                    'golden_cross': analysis['timeframe_analysis']['ma_alignment'].get('golden_cross', False),
                    'death_cross': analysis['timeframe_analysis']['ma_alignment'].get('death_cross', False),
                    'short_term': analysis['timeframe_analysis']['short_term']['signal'],
                    'medium_term': analysis['timeframe_analysis']['medium_term']['signal'],
                    'long_term': analysis['timeframe_analysis']['long_term']['signal'],
                })
            except:
                continue
        
        return pd.DataFrame(historical).sort_values('date')
    
    except Exception as e:
        return None


def generate_daily_report(days: int = 7):
    """Generate comprehensive daily report"""
    
    print("="*80)
    print("📊 台股每日综合分析报告")
    print(f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析期間：過去 {days} 個交易日")
    print("="*80)
    
    # Analyze key stocks
    key_stocks = ['2330', '2317', '2454', '2800', '1301', '1101', '0050']
    
    current_analysis = {}
    historical_data = {}
    
    # Current analysis
    print("\n📍 分析目前狀態...")
    for symbol in key_stocks:
        try:
            result = analyze_composite(symbol)
            if 'error' not in result:
                current_analysis[symbol] = result
                
                # Get historical
                hist_df = get_historical_data(symbol, days)
                if hist_df is not None:
                    historical_data[symbol] = hist_df
                    
        except Exception as e:
            print(f"  {symbol} 分析失敗：{e}")
    
    # Build report
    report = []
    report.append("# 📊 台股每日综合分析报告")
    report.append(f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**分析期間**: 過去 {days} 個交易日\n")
    
    # Section 1: Current Status
    report.append("\n## 🎯 目前狀態\n")
    report.append("| 代號 | 訊號 | 評分 | 市場狀態 | 短期 | 中期 | 長期 |\n")
    report.append("|------|------|------|---------|------|------|------|\n")
    
    for symbol in key_stocks:
        if symbol in current_analysis:
            r = current_analysis[symbol]
            tf = r['timeframe_analysis']
            report.append(f"| {symbol} | {r['signal']} | {r['composite_score']:.2f} | {r['market_regime'].value} | {tf['short_term']['signal'][:4]} | {tf['medium_term']['signal'][:4]} | {tf['long_term']['signal'][:4]} |")
    
    # Section 2: Score Trend
    report.append("\n## 📈 評分趨勢 (過去{0}日)\n".format(days))
    
    for symbol in key_stocks:
        if symbol in historical_data:
            hist = historical_data[symbol]
            if len(hist) > 0:
                report.append(f"### {symbol}\n")
                report.append(f"- 目前評分：{hist['composite_score'].iloc[-1]:.2f}\n")
                
                if len(hist) > 1:
                    score_change = hist['composite_score'].iloc[-1] - hist['composite_score'].iloc[0]
                    report.append(f"- 變化：{score_change:+.2f} ({'上升' if score_change > 0 else '下降'}{abs(score_change)*100:.0f}%)\n")
                
                # Trend
                if len(hist) > 3:
                    recent_avg = hist['composite_score'].iloc[-3:].mean()
                    older_avg = hist['composite_score'].iloc[:3].mean()
                    if recent_avg > older_avg + 0.1:
                        report.append(f"- 趨勢：📈 上升趨勢\n")
                    elif recent_avg < older_avg - 0.1:
                        report.append(f"- 趨勢：📉 下降趨勢\n")
                    else:
                        report.append(f"- 趨勢：➡️ 盤整\n")
                
                report.append("\n")
    
    # Section 3: Key Events
    report.append("\n## 🔔 重要事件\n")
    
    # Golden crosses
    golden = []
    death = []
    for symbol in key_stocks:
        if symbol in historical_data:
            hist = historical_data[symbol]
            if len(hist) > 0:
                latest = hist.iloc[-1]
                if latest.get('golden_cross'):
                    golden.append(symbol)
                if latest.get('death_cross'):
                    death.append(symbol)
    
    if golden:
        report.append(f"\n### ✨ 黃金交叉\n")
        for symbol in golden:
            report.append(f"- {symbol}: 出現黃金交叉，目前評分 {current_analysis.get(symbol, {}).get('composite_score', 0):.2f}")
    
    if death:
        report.append(f"\n### ⚠️ 死亡交叉\n")
        for symbol in death:
            report.append(f"- {symbol}: 出現死亡交叉，目前評分 {current_analysis.get(symbol, {}).get('composite_score', 0):.2f}")
    
    if not golden and not death:
        report.append("今日無特殊交叉事件\n")
    
    # Section 4: Recommendations
    report.append("\n## 💡 操作建議\n")
    
    strong_buy = [s for s in key_stocks if s in current_analysis and current_analysis[s]['signal'] == 'STRONG BUY']
    buy = [s for s in key_stocks if s in current_analysis and current_analysis[s]['signal'] == 'BUY']
    hold = [s for s in key_stocks if s in current_analysis and current_analysis[s]['signal'] == 'HOLD']
    sell = [s for s in key_stocks if s in current_analysis and current_analysis[s]['signal'] == 'SELL']
    
    if strong_buy:
        report.append(f"\n### 🟢 強烈買進 ({len(strong_buy)} 檔)\n")
        for s in strong_buy:
            r = current_analysis[s]
            report.append(f"- {s}: 評分 {r['composite_score']:.2f} ({r['market_regime'].value})")
    
    if buy:
        report.append(f"\n### 🟢 買進 ({len(buy)} 檔)\n")
        for s in buy:
            r = current_analysis[s]
            report.append(f"- {s}: 評分 {r['composite_score']:.2f} ({r['market_regime'].value})")
    
    if hold:
        report.append(f"\n### 🟡 觀望 ({len(hold)} 檔)\n")
        for s in hold:
            report.append(f"- {s}")
    
    if sell:
        report.append(f"\n### 🔴 賣出 ({len(sell)} 檔)\n")
        for s in sell:
            r = current_analysis[s]
            report.append(f"- {s}: 評分 {r['composite_score']:.2f}")
    
    # Section 5: Detailed Analysis
    report.append("\n## 📋 個別分析\n")
    
    for symbol in key_stocks:
        if symbol in current_analysis:
            r = current_analysis[symbol]
            report.append(f"\n### {symbol}\n")
            report.append(f"- 訊號：{r['signal']}\n")
            report.append(f"- 評分：{r['composite_score']:.2f}/1.00\n")
            report.append(f"- 市場狀態：{r['market_regime'].value}\n")
            
            # Historical context
            if symbol in historical_data:
                hist = historical_data[symbol]
                if len(hist) > 0:
                    report.append(f"- 7 日最高評分：{hist['composite_score'].max():.2f}\n")
                    report.append(f"- 7 日最低評分：{hist['composite_score'].min():.2f}\n")
                    report.append(f"- 平均評分：{hist['composite_score'].mean():.2f}\n")
            
            # Recommendation
            report.append(f"\n**建議**: {r['recommendation']}\n")
    
    # Save report
    report_text = "\n".join(report)
    output_file = 'reports/daily_analysis_full.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n✅ 完整報告已儲存至：{output_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 重點摘要")
    print("="*80)
    
    if strong_buy:
        print(f"\n🟢 強烈買進：{', '.join(strong_buy)}")
    if buy:
        print(f"🟢 買進：{', '.join(buy)}")
    if hold:
        print(f"🟡 觀望：{', '.join(hold)}")
    if sell:
        print(f"🔴 賣出：{', '.join(sell)}")
    
    if golden:
        print(f"\n✨ 黃金交叉：{', '.join(golden)}")
    if death:
        print(f"⚠️ 死亡交叉：{', '.join(death)}")
    
    print("\n" + "="*80)
    
    return report_text


if __name__ == "__main__":
    generate_report(days=7)
