#!/usr/bin/env python3
"""
Historical Data Collector using yfinance
Fetches and stores historical stock data from Yahoo Finance.
Supports Taiwan stocks (.TW suffix).

Usage:
    python data_collector_yf.py --symbols 2330,2317,2454 --days 365
    python data_collector_yf.py --all-stocks --days 365
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yfinance as yf
from config import STOCK_UNIVERSE, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Historical price data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume INTEGER,
            UNIQUE(symbol, date)
        )
    ''')
    
    # Index on symbol and date for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON stock_prices(symbol, date)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def fetch_historical_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data from Yahoo Finance.
    
    Parameters
    ----------
    symbol : str
        Stock symbol (e.g., '2330' for TSMC, will be converted to '2330.TW')
    days : int
        Number of days of historical data to fetch
    
    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data
    """
    try:
        # Add .TW suffix for Taiwan stocks if not present
        if not symbol.endswith('.TW'):
            ticker_symbol = f"{symbol}.TW"
        else:
            ticker_symbol = symbol
        
        logger.info(f"Fetching {days} days of data for {symbol} from Yahoo Finance...")
        
        # Fetch data using yfinance
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=f"{days}d")
        
        if hist.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
        
        # Reset index to get date as column
        hist = hist.reset_index()
        
        # Rename columns to match our expected format
        hist = hist.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        })
        
        # Ensure date is datetime
        if 'date' in hist.columns:
            hist['date'] = pd.to_datetime(hist['date'])
        
        logger.info(f"✓ Fetched {len(hist)} rows for {symbol}")
        return hist
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def store_data(df: pd.DataFrame, symbol: str):
    """Store data in database."""
    if df is None or df.empty:
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    for _, row in df.iterrows():
        try:
            conn.execute('''
                INSERT OR REPLACE INTO stock_prices 
                (symbol, date, open, high, low, close, adj_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row.get('adj_close', row['close']),
                row['volume']
            ))
        except Exception as e:
            logger.debug(f"Error storing row: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"✓ Stored {len(df)} records for {symbol}")

def fetch_all_stocks(days: int = 365):
    """Fetch data for all stocks in the universe."""
    logger.info(f"Fetching data for {len(STOCK_UNIVERSE)} stocks...")
    
    success_count = 0
    for symbol in STOCK_UNIVERSE:
        df = fetch_historical_data(symbol, days)
        if df is not None and not df.empty:
            store_data(df, symbol)
            success_count += 1
    
    logger.info(f"Completed: {success_count}/{len(STOCK_UNIVERSE)} stocks fetched")

def collect_all_stocks(days: int = 365):
    """Alias for fetch_all_stocks - compatibility with existing code."""
    fetch_all_stocks(days)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch historical stock data')
    parser.add_argument('--symbols', type=str, help='Comma-separated stock symbols')
    parser.add_argument('--all-stocks', action='store_true', help='Fetch all stocks in universe')
    parser.add_argument('--days', type=int, default=365, help='Days of historical data')
    
    args = parser.parse_args()
    
    init_database()
    
    if args.all_stocks:
        fetch_all_stocks(args.days)
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        for symbol in symbols:
            df = fetch_historical_data(symbol, args.days)
            if df is not None:
                store_data(df, symbol)
    else:
        parser.print_help()
        sys.exit(1)
