#!/usr/bin/env python3
"""
Daily Stock Report Generator

Generates comprehensive daily reports including:
- Market overview
- Top gainers/losers
- Sentiment analysis
- Technical indicator summary
- Correlation insights
- Trading alerts

Usage:
    python daily_report.py --output report.md
    python daily_report.py --email  # Send via email
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd

from config import STOCK_UNIVERSE, ANALYSIS_CONFIG, DB_PATH
from trend_tracker import analyze_all_stocks, get_stock_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_market_overview() -> Dict:
    """
    Generate market overview statistics.
    
    Returns
    -------
    Dict
        Market statistics
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = '''
        SELECT symbol, date, close, volume
        FROM stock_prices
        WHERE date = (
            SELECT MAX(date) FROM stock_prices
        )
    '''
    
    latest_df = pd.read_sql_query(query, conn)
    conn.close()
    
    if latest_df.empty:
        return {}
    
    # Calculate market stats
    latest_df['prev_close'] = latest_df['close'].shift(1)
    latest_df['change_pct'] = (latest_df['close'] - latest_df['prev_close']) / latest_df['prev_close'] * 100
    
    return {
        'total_stocks': len(latest_df),
        'avg_change': latest_df['change_pct'].mean(),
        'stocks_up': (latest_df['change_pct'] > 0).sum(),
        'stocks_down': (latest_df['change_pct'] < 0).sum(),
        'total_volume': latest_df['volume'].sum()
    }


def get_top_movers(limit: int = 5) -> Dict:
    """
    Get top gainers and losers.
    
    Parameters
    ----------
    limit : int
        Number of top movers to return
    
    Returns
    -------
    Dict
        Top gainers and losers
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = '''
        SELECT 
            symbol,
            close,
            (close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) * 100 as change_pct,
            volume
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
        ORDER BY change_pct
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return {'gainers': [], 'losers': []}
    
    # Top gainers
    gainers = df.nlargest(limit, 'change_pct')
    gainers_list = [
        {'symbol': row['symbol'], 'change': row['change_pct'], 'price': row['close']}
        for _, row in gainers.iterrows()
    ]
    
    # Top losers
    losers = df.nsmallest(limit, 'change_pct')
    losers_list = [
        {'symbol': row['symbol'], 'change': row['change_pct'], 'price': row['close']}
        for _, row in losers.iterrows()
    ]
    
    return {
        'gainers': gainers_list,
        'losers': losers_list
    }


def generate_sentiment_summary() -> Dict:
    """
    Generate sentiment summary from recent PTT posts.
    
    Returns
    -------
    Dict
        Sentiment analysis summary
    """
    try:
        from ptt_bus import fetch_ptt_posts, analyze_sentiment
        
        posts = fetch_ptt_posts(limit=50)
        if not posts:
            return {'status': 'no_data'}
        
        sentiment = analyze_sentiment(posts)
        sentiment['status'] = 'success'
        return sentiment
        
    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        return {'status': 'error', 'error': str(e)}


def generate_technical_summary(symbols: List[str] = None) -> List[Dict]:
    """
    Generate technical indicator summary for stocks.
    
    Parameters
    ----------
    symbols : List[str], optional
        List of symbols to analyze
    
    Returns
    -------
    List[Dict]
        Technical summary for each stock
    """
    if symbols is None:
        symbols = ['2330', '2317', '2454', '2881', '1301']  # Top stocks
    
    summary = []
    
    for symbol in symbols:
        try:
            df = get_stock_data(symbol)
            
            if df is None or df.empty:
                continue
            
            latest = df.iloc[-1]
            
            summary.append({
                'symbol': symbol,
                'name': STOCK_UNIVERSE.get(symbol, symbol),
                'price': round(latest['close'], 2),
                'sma_20': round(latest['sma_20'], 2) if 'sma_20' in latest else None,
                'rsi_14': round(latest['rsi_14'], 2) if 'rsi_14' in latest else None,
                'macd': round(latest['macd'], 3) if 'macd' in latest else None,
                'bb_position': round(latest['bb_position'], 3) if 'bb_position' in latest else None,
            })
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    return summary


def generate_report(output_file: str = None, format: str = 'markdown') -> str:
    """
    Generate comprehensive daily report.
    
    Parameters
    ----------
    output_file : str, optional
        File to save report
    format : str
        Report format ('markdown' or 'text')
    
    Returns
    -------
    str
        Report content
    """
    logger.info("Generating daily report...")
    
    report_lines = []
    report_lines.append("# 📊 每日股票市場報告")
    report_lines.append(f"**日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("")
    
    # Market Overview
    overview = generate_market_overview()
    if overview:
        report_lines.append("## 🌍 市場概覽")
        report_lines.append(f"- 追蹤股票數：{overview.get('total_stocks', 'N/A')}")
        report_lines.append(f"- 上漲家數：{overview.get('stocks_up', 'N/A')}")
        report_lines.append(f"- 下跌家數：{overview.get('stocks_down', 'N/A')}")
        report_lines.append(f"- 平均漲幅：{overview.get('avg_change', 0):.2f}%")
        report_lines.append("")
    
    # Top Movers
    movers = get_top_movers(5)
    if movers:
        report_lines.append("## 📈 漲幅前五名")
        for i, gainer in enumerate(movers.get('gainers', []), 1):
            symbol = gainer['symbol']
            name = STOCK_UNIVERSE.get(symbol, symbol)
            report_lines.append(f"{i}. **{symbol} {name}**: {gainer['change']:+.2f}% (${gainer['price']:.2f})")
        report_lines.append("")
        
        report_lines.append("## 📉 跌幅前五名")
        for i, loser in enumerate(movers.get('losers', []), 1):
            symbol = loser['symbol']
            name = STOCK_UNIVERSE.get(symbol, symbol)
            report_lines.append(f"{i}. **{symbol} {name}**: {loser['change']:+.2f}% (${loser['price']:.2f})")
        report_lines.append("")
    
    # Sentiment Analysis
    sentiment = generate_sentiment_summary()
    if sentiment.get('status') == 'success':
        report_lines.append("## 💭 PTT 情緒分析")
        report_lines.append(f"- 多頭：{sentiment.get('bullish_count', 0)}")
        report_lines.append(f"- 空頭：{sentiment.get('bearish_count', 0)}")
        report_lines.append(f"- 中性：{sentiment.get('neutral_count', 0)}")
        report_lines.append(f"- 情緒分數：{sentiment.get('sentiment_score', 0):.3f}")
        report_lines.append("")
    
    # Technical Summary
    report_lines.append("## 📊 技術指標摘要")
    report_lines.append("")
    report_lines.append("| 代號 | 名稱 | 價格 | SMA20 | RSI14 | MACD | BB 位置 |")
    report_lines.append("|------|------|------|-------|-------|------|---------|")
    
    tech_summary = generate_technical_summary()
    for stock in tech_summary:
        sma = f"{stock['sma_20']:.2f}" if stock['sma_20'] else "N/A"
        rsi = f"{stock['rsi_14']:.1f}" if stock['rsi_14'] else "N/A"
        macd = f"{stock['macd']:.3f}" if stock['macd'] else "N/A"
        bb = f"{stock['bb_position']:.2f}" if stock['bb_position'] else "N/A"
        
        report_lines.append(
            f"| {stock['symbol']} | {stock['name']} | {stock['price']:.2f} | {sma} | {rsi} | {macd} | {bb} |"
        )
    
    report_lines.append("")
    
    # Alerts
    report_lines.append("## 🚨 交易警訊")
    results = analyze_all_stocks(['2330', '2317', '2454', '2881', '1301'])
    has_alerts = False
    
    for symbol, data in results.items():
        if 'alerts' in data and data['alerts']:
            has_alerts = True
            report_lines.append(f"\n**{symbol} - {data.get('name', symbol)}**:")
            for alert in data['alerts']:
                report_lines.append(f"- {alert}")
    
    if not has_alerts:
        report_lines.append("目前無重大警訊")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*報告生成時間：* " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    report_content = "\n".join(report_lines)
    
    # Save to file
    if output_file:
        Path(output_file).write_text(report_content)
        logger.info(f"Report saved to {output_file}")
    
    return report_content


def main():
    parser = argparse.ArgumentParser(description='Generate daily stock report')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--format', choices=['markdown', 'text'], default='markdown')
    
    args = parser.parse_args()
    
    report = generate_report(args.output, args.format)
    
    if not args.output:
        print(report)


if __name__ == "__main__":
    main()
