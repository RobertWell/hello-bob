#!/usr/bin/env python3
"""
Market Dashboard - 大盤趨勢分析
- 加權指數追蹤
- 市場寬度指標
- 成交量分析
- 產業別表現
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 大盤指標股 (加權指數主要成分股)
MARKET_BENCHMARKS = {
    '0050.TW': '台灣50',
    '006208.TW': '期加權',
    '^TWII': '加權指數'
}

# 產業分類 (精選代表股)
SECTOR_MAP = {
    '金融': ['2881', '2882', '2883', '2884', '2885', '2886', '2890', '2891'],
    '電子': ['2330', '2317', '2454', '2303', '2395', '2357', '2353', '2324'],
    '傳產': ['1301', '1303', '1304', '1101', '1102', '1902', '2002'],
    '半導體': ['2330', '2353', '2303', '2395', '2324', '2342', '2357', '2375'],
    'AI 概念': ['2330', '2317', '2353', '2395', '2324', '2357']
}

def get_market_data(days=90):
    """獲取大盤指數數據"""
    market_data = {}
    
    for symbol, name in MARKET_BENCHMARKS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            if not hist.empty:
                hist = hist.reset_index()
                hist['Date'] = pd.to_datetime(hist['Date'])
                market_data[symbol] = {
                    'name': name,
                    'data': hist,
                    'latest': hist.iloc[-1] if not hist.empty else None,
                    'change': 0 if len(hist) < 2 else (hist.iloc[-1]['Close'] - hist.iloc[-2]['Close']) / hist.iloc[-2]['Close'] * 100
                }
                logger.info(f"✓ 取得 {name} ({symbol}) - {len(hist)} 筆資料")
        except Exception as e:
            logger.error(f"取得 {symbol} 失敗：{e}")
    
    return market_data

def calculate_market_breadth(db_path='stock_data.db'):
    """計算市場寬度指標 (漲跌家數比)"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 取得所有股票最新一日的漲跌
        query = """
        SELECT 
            symbol,
            date,
            close,
            LAG(close) OVER (PARTITION BY symbol ORDER BY date) as prev_close
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return None
        
        # 計算漲跌
        df['change_pct'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
        df['status'] = df['change_pct'].apply(lambda x: 'up' if x > 0 else ('down' if x < 0 else 'flat'))
        
        # 統計
        up_count = len(df[df['status'] == 'up'])
        down_count = len(df[df['status'] == 'down'])
        flat_count = len(df[df['status'] == 'flat'])
        total = len(df)
        
        return {
            'up': up_count,
            'down': down_count,
            'flat': flat_count,
            'total': total,
            'ratio': up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5,
            'advance_decline': up_count - down_count
        }
    except Exception as e:
        logger.error(f"計算市場寬度失敗：{e}")
        return None

def get_sector_performance(db_path='stock_data.db'):
    """計算各產業別表現"""
    try:
        conn = sqlite3.connect(db_path)
        
        sector_perf = {}
        for sector, stocks in SECTOR_MAP.items():
            stock_list = "','".join(stocks)
            query = f"""
            SELECT 
                symbol,
                date,
                close,
                LAG(close) OVER (PARTITION BY symbol ORDER BY date) as prev_close
            FROM stock_prices
            WHERE symbol IN ('{stock_list}')
            AND date = (SELECT MAX(date) FROM stock_prices)
            """
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                df['change_pct'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
                avg_change = df['change_pct'].mean()
                sector_perf[sector] = {
                    'avg_change': avg_change,
                    'stock_count': len(df),
                    'stocks': df.to_dict('records')
                }
        
        conn.close()
        return sector_perf
    except Exception as e:
        logger.error(f"計算產業表現失敗：{e}")
        return {}

def generate_market_summary(market_data, breadth, sector_perf):
    """生成大盤摘要"""
    summary = []
    
    # 大盤走勢
    if '0050.TW' in market_data:
        data = market_data['0050.TW']
        latest = data['latest']
        if latest is not None:
            summary.append(f"📊 **台灣 50**: {latest['Close']:.2f} ({data['change']:+.2f}%)")
    
    # 市場寬度
    if breadth:
        summary.append(f"📈 **漲跌比**: {breadth['up']}家漲 / {breadth['down']}家跌 (比價：{breadth['ratio']:.2f})")
        summary.append(f"📉 **漲跌差**: {breadth['advance_decline']:+d} 家")
    
    # 產業表現
    if sector_perf:
        summary.append("\n**產業表現**:")
        sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1]['avg_change'], reverse=True)
        for sector, perf in sorted_sectors:
            summary.append(f"- {sector}: {perf['avg_change']:+.2f}% ({perf['stock_count']}檔)")
    
    return "\n".join(summary)

if __name__ == "__main__":
    # 測試
    print("取得大盤數據...")
    market_data = get_market_data()
    
    print("\n計算市場寬度...")
    breadth = calculate_market_breadth()
    
    print("\n計算產業表現...")
    sector_perf = get_sector_performance()
    
    print("\n" + "="*50)
    print(generate_market_summary(market_data, breadth, sector_perf))
    print("="*50)
