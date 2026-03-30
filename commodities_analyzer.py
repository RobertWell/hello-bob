#!/usr/bin/env python3
"""
Commodities & Global Futures Analyzer
- 原物料期貨：黃金、白銀、原油、天然氣、銅
- 全球股市期貨：S&P 500、Nasdaq、Dow Jones、台股期
- 關聯性分析
- 資金流向指標
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 商品期貨代碼 (Yahoo Finance)
COMMODITIES = {
    '黃金': 'GC=F',      # Gold Futures
    '白銀': 'SI=F',      # Silver Futures
    '原油': 'CL=F',      # Crude Oil WTI
    '布侖特原油': 'BZ=F',  # Brent Crude
    '天然氣': 'NG=F',    # Natural Gas
    '銅': 'HG=F',        # Copper
    '小麥': 'ZW=F',      # Wheat
    '玉米': 'ZC=F',      # Corn
    '黃豆': 'ZS=F',      # Soybeans
}

# 全球股市期貨
GLOBAL_FUTURES = {
    'S&P 500': 'ES=F',        # E-mini S&P 500
    'Nasdaq 100': 'NQ=F',     # E-mini Nasdaq 100
    'Dow Jones': 'YM=F',      # E-mini Dow Jones
    '台股期': 'TXF=TWO',      # Taiwan Futures (TWSE)
    '日經 225': 'NKD=F',      # Nikkei 225 Futures
    '德國 DAX': 'FDAX=F',     # DAX Futures
    '英國 FTSE': 'FFI=F',     # FTSE 100 Futures
}

# 相關 ETF (用於期貨分析)
FUTURE_PROXIES = {
    'S&P 500': 'SPY',
    'Nasdaq 100': 'QQQ',
    'Dow Jones': 'DIA',
    '台股': '0050.TW',
    '日經 225': 'EWJ',
    '德國 DAX': 'EWG',
    '英國 FTSE': 'EWU',
    '黃金': 'GLD',
    '白銀': 'SLV',
    '原油': 'USO',
    '天然氣': 'UNG',
    '銅': 'COPX',
}

def fetch_commodity_data(symbol: str, days: int = 90) -> Optional[pd.DataFrame]:
    """抓取商品期貨數據"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        if df.empty:
            logger.warning(f"{symbol} 無資料")
            return None
        
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        df = df.ffill().bfill()
        return df
    except Exception as e:
        logger.error(f"抓取 {symbol} 失敗：{e}")
        return None

def fetch_future_data(name: str, days: int = 90) -> Optional[pd.DataFrame]:
    """抓全球期貨數據 (使用 ETF 代理)"""
    try:
        # 優先使用期貨代碼
        if name in GLOBAL_FUTURES:
            symbol = GLOBAL_FUTURES[name]
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
            if not df.empty:
                df = df.reset_index()
                df = df.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                df = df.ffill().bfill()
                return df
        
        # 使用 ETF 代理
        if name in FUTURE_PROXIES:
            symbol = FUTURE_PROXIES[name]
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")
            if not df.empty:
                df = df.reset_index()
                df = df.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                df = df.ffill().bfill()
                return df
        
        return None
    except Exception as e:
        logger.error(f"抓取 {name} 失敗：{e}")
        return None

def get_all_commodities_data(days: int = 90) -> Dict:
    """獲取所有商品數據"""
    result = {}
    for name, symbol in COMMODITIES.items():
        logger.info(f"抓取 {name} ({symbol})...")
        df = fetch_commodity_data(symbol, days)
        if df is not None and not df.empty:
            latest_row = df.iloc[-1]
            latest_price = float(latest_row['close'])
            change = 0
            if len(df) > 1:
                prev_close = float(df.iloc[-2]['close'])
                change = (latest_price - prev_close) / prev_close * 100
            result[name] = {
                'symbol': symbol,
                'data': df,
                'latest': latest_price,
                'change': change
            }
    return result

def get_all_futures_data(days: int = 90) -> Dict:
    """獲取所有期貨數據"""
    result = {}
    for name in GLOBAL_FUTURES.keys():
        logger.info(f"抓取 {name}...")
        df = fetch_future_data(name, days)
        if df is not None and not df.empty:
            latest_row = df.iloc[-1]
            latest_price = float(latest_row['close'])
            change = 0
            if len(df) > 1:
                prev_close = float(df.iloc[-2]['close'])
                change = (latest_price - prev_close) / prev_close * 100
            result[name] = {
                'data': df,
                'latest': latest_price,
                'change': change
            }
    return result

def calculate_correlation(commodity_data: Dict, future_data: Dict, days: int = 60) -> pd.DataFrame:
    """計算商品與期貨的相關性"""
    try:
        # 取得共同日期範圍
        all_data = {}
        
        for name, info in commodity_data.items():
            if info['data'] is not None:
                df = info['data'].set_index('date')['close']
                df = df.pct_change().dropna()
                all_data[f"商品_{name}"] = df
        
        for name, info in future_data.items():
            if info['data'] is not None:
                df = info['data'].set_index('date')['close']
                df = df.pct_change().dropna()
                all_data[f"期貨_{name}"] = df
        
        if not all_data:
            return pd.DataFrame()
        
        # 建立關聯性矩陣
        corr_df = pd.DataFrame(all_data)
        corr_df = corr_df.dropna(axis=1, how='all')
        
        if len(corr_df) < 10:
            return pd.DataFrame()
        
        # 計算相關性 (取最近 N 天)
        corr_matrix = corr_df.tail(days).corr()
        return corr_matrix
    except Exception as e:
        logger.error(f"計算相關性失敗：{e}")
        return pd.DataFrame()

def generate_commodities_summary(commodities: Dict) -> str:
    """生成商品摘要"""
    summary = []
    summary.append("## 📦 原物料期貨")
    summary.append("")
    
    if not commodities:
        summary.append("*目前無資料*")
        return "\n".join(summary)
    
    # 依漲幅排序
    sorted_items = sorted(commodities.items(), key=lambda x: x[1]['change'], reverse=True)
    
    for name, info in sorted_items:
        change = info['change']
        icon = "🟢" if change > 0 else ("🔴" if change < 0 else "🟡")
        latest = info['latest']
        if latest is not None:
            summary.append(f"- {icon} **{name}**: {latest:.2f} ({change:+.2f}%)")
    
    return "\n".join(summary)

def generate_futures_summary(futures: Dict) -> str:
    """生成期貨摘要"""
    summary = []
    summary.append("## 🌍 全球股市期貨")
    summary.append("")
    
    if not futures:
        summary.append("*目前無資料*")
        return "\n".join(summary)
    
    # 依漲幅排序
    sorted_items = sorted(futures.items(), key=lambda x: x[1]['change'], reverse=True)
    
    for name, info in sorted_items:
        change = info['change']
        icon = "🟢" if change > 0 else ("🔴" if change < 0 else "🟡")
        latest = info['latest']
        if latest is not None:
            summary.append(f"- {icon} **{name}**: {latest:.2f} ({change:+.2f}%)")
    
    return "\n".join(summary)

if __name__ == "__main__":
    # 測試
    print("抓取原物料數據...")
    commodities = get_all_commodities_data(days=30)
    print(f"取得 {len(commodities)} 項商品數據")
    
    print("\n抓取全球期貨數據...")
    futures = get_all_futures_data(days=30)
    print(f"取得 {len(futures)} 項期貨數據")
    
    print("\n" + "="*50)
    print(generate_commodities_summary(commodities))
    print("\n" + "="*50)
    print(generate_futures_summary(futures))
    print("="*50)
