#!/usr/bin/env python3
"""
Historical Data Collector

Fetches and stores historical stock data from public Taiwan exchange data.
Supports Taiwan Stock Exchange (TWSE) monthly price history.

Usage:
    python data_collector.py --symbols 2330,2317,2454 --days 365
    python data_collector.py --all-stocks --days 365
"""

import argparse
import logging
import sqlite3
import sys
from datetime import timezone
from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
import urllib3

from config import STOCK_UNIVERSE, ANALYSIS_CONFIG, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
        CREATE INDEX IF NOT EXISTS idx_prices_symbol_date 
        ON stock_prices(symbol, date)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def fetch_historical_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """
    Fetch historical stock data from the TWSE monthly API.
    
    Parameters
    ----------
    symbol : str
        Stock symbol (e.g., '2330.TW' for TSMC)
    days : int
        Number of days of historical data to fetch
    
    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data
    """
    try:
        logger.info(f"Fetching {days} days of data for {symbol} from TWSE API...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        rows = []
        month_cursor = datetime(end_date.year, end_date.month, 1)
        months_to_fetch = max(2, ceil(days / 20) + 1)

        for _ in range(months_to_fetch):
            response = requests.get(
                "https://www.twse.com.tw/rwd/en/afterTrading/STOCK_DAY",
                params={
                    "date": month_cursor.strftime("%Y%m%d"),
                    "stockNo": symbol,
                    "response": "json",
                },
                timeout=20,
                verify=False,
                headers={"User-Agent": "hello-bob-dashboard/1.0"},
            )
            response.raise_for_status()
            payload = response.json()

            if payload.get("stat") == "OK":
                rows.extend(payload.get("data", []))

            if month_cursor.month == 1:
                month_cursor = datetime(month_cursor.year - 1, 12, 1)
            else:
                month_cursor = datetime(month_cursor.year, month_cursor.month - 1, 1)

        if not rows:
            logger.warning(f"No data found for {symbol}")
            return None

        parsed_rows = []
        for row in rows:
            try:
                trade_date = pd.to_datetime(row[0], format="%Y/%m/%d")
                if trade_date < pd.Timestamp(start_date.date()):
                    continue

                open_price = float(row[3].replace(",", ""))
                high_price = float(row[4].replace(",", ""))
                low_price = float(row[5].replace(",", ""))
                close_price = float(row[6].replace(",", ""))
                volume = int(row[1].replace(",", ""))
            except (IndexError, ValueError):
                continue

            parsed_rows.append(
                {
                    "symbol": symbol,
                    "Date": trade_date,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "adj_close": close_price,
                    "volume": volume,
                }
            )

        df = pd.DataFrame(parsed_rows).drop_duplicates(subset=["Date"]).sort_values("Date")

        if df.empty:
            logger.warning(f"No valid rows found for {symbol}")
            return None

        logger.info(f"Fetched {len(df)} records for {symbol}")
        return df[["symbol", "Date", "open", "high", "low", "close", "adj_close", "volume"]]
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None


def store_prices(df: pd.DataFrame):
    """
    Store price data in database.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns: symbol, Date, open, high, low, close, adj_close, volume
    """
    if df is None or df.empty:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO stock_prices 
                (symbol, date, open, high, low, close, adj_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['symbol'],
                row['Date'].strftime('%Y-%m-%d'),
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row.get('adj_close', row['close']),
                row['volume']
            ))
        
        conn.commit()
        logger.info(f"Stored {len(df)} records in database")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_historical_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """
    Get historical data from database or fetch if not available.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
    days : int
        Number of days to retrieve
    
    Returns
    -------
    pd.DataFrame
        Historical price data
    """
    # Try to get from database first
    conn = sqlite3.connect(DB_PATH)
    
    query = '''
        SELECT date, open, high, low, close, adj_close, volume
        FROM stock_prices
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=[symbol, days])
    conn.close()
    
    if not df.empty and len(df) == days:
        logger.info(f"Retrieved {len(df)} records for {symbol} from database")
        return df
    
    # Fetch from remote market data API if not enough data
    logger.info("Insufficient data in database, fetching from remote market data API...")
    df = fetch_historical_data(symbol, days)
    
    if df is not None:
        store_prices(df)
    
    return df


def collect_all_stocks(days: int = 365):
    """
    Collect historical data for all stocks in the universe.
    
    Parameters
    ----------
    days : int
        Number of days of historical data to collect
    """
    logger.info(f"Collecting {days} days of data for {len(STOCK_UNIVERSE)} stocks...")
    
    successful = 0
    failed = 0
    
    for symbol, name in STOCK_UNIVERSE.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {symbol} - {name}")
        logger.info(f"{'='*60}")
        
        try:
            df = get_historical_data(symbol, days)
            if df is not None and not df.empty:
                successful += 1
                logger.info(f"✓ Success: {symbol} - {len(df)} records")
            else:
                failed += 1
                logger.warning(f"✗ No data: {symbol}")
        except Exception as e:
            failed += 1
            logger.error(f"✗ Error for {symbol}: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete: {successful} successful, {failed} failed")
    logger.info(f"{'='*60}")


def get_price_data_for_analysis() -> dict:
    """
    Get price data for all stocks in a format suitable for analysis.
    
    Returns
    -------
    dict
        Dictionary of symbol -> DataFrame with OHLCV data
    """
    result = {}
    
    for symbol in STOCK_UNIVERSE.keys():
        df = get_historical_data(symbol, ANALYSIS_CONFIG['history_days'])
        if df is not None and not df.empty:
            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df.sort_index()
            result[symbol] = df
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Collect historical stock data')
    parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols')
    parser.add_argument('--all-stocks', action='store_true', help='Collect for all stocks in universe')
    parser.add_argument('--days', type=int, default=365, help='Number of days of historical data')
    
    args = parser.parse_args()
    
    # Initialize database
    init_database()
    
    if args.all_stocks:
        collect_all_stocks(args.days)
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        for symbol in symbols:
            logger.info(f"Collecting data for {symbol}")
            df = get_historical_data(symbol, args.days)
            if df is not None:
                logger.info(f"Success: {len(df)} records")
    else:
        logger.info("Use --all-stocks or --symbols to specify which stocks to collect")


if __name__ == "__main__":
    main()
