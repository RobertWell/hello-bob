#!/usr/bin/env python3
"""
Market Sentiment Update Script

Combines PTT stock sentiment analysis with technical indicators.
This script:
1. Fetches PTT stock board posts
2. Calculates technical indicators
3. Updates market sentiment database
4. Logs results

Usage:
    python update_market_sentiment.py [--no-push]
    
Environment:
    Requires: pandas, pandas-ta, requests, beautifulsoup4
    Install: pip install pandas pandas-ta requests beautifulsoup4
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sentiment_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def fetch_ptt_sentiment():
    """
    Fetch and analyze PTT stock board sentiment.
    
    Returns
    -------
    dict
        Sentiment analysis results
    """
    from ptt_bus import fetch_ptt_posts, analyze_sentiment
    
    logger.info("Fetching PTT posts...")
    posts = fetch_ptt_posts(limit=50)
    
    if not posts:
        logger.warning("No posts fetched from PTT")
        return None
    
    logger.info(f"Fetched {len(posts)} posts")
    
    # Analyze sentiment
    sentiment_result = analyze_sentiment(posts)
    
    logger.info(f"Sentiment analysis complete:")
    logger.info(f"  - Bullish: {sentiment_result.get('bullish_count', 0)}")
    logger.info(f"  - Bearish: {sentiment_result.get('bearish_count', 0)}")
    logger.info(f"  - Neutral: {sentiment_result.get('neutral_count', 0)}")
    
    return sentiment_result


def calculate_indicators_for_stocks(stock_data: dict) -> dict:
    """
    Calculate technical indicators for stock data.
    
    Parameters
    ----------
    stock_data : dict
        Dictionary of stock symbols and their OHLCV data
    
    Returns
    -------
    dict
        Updated stock data with indicators
    """
    from indicators import add_indicators, validate_dataframe
    
    result = {}
    
    for symbol, df in stock_data.items():
        if not validate_dataframe(df):
            logger.warning(f"Invalid data for {symbol}, skipping indicators")
            result[symbol] = df
            continue
        
        try:
            df_with_indicators = add_indicators(df)
            result[symbol] = df_with_indicators
            logger.info(f"Added indicators for {symbol}")
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            result[symbol] = df
    
    return result


def update_database(sentiment_data: dict, indicator_data: dict):
    """
    Update sentiment and indicator database.
    
    Parameters
    ----------
    sentiment_data : dict
        Sentiment analysis results
    indicator_data : dict
        Technical indicator data
    """
    import sqlite3
    from pathlib import Path
    
    db_path = Path('stock_data.db')
    
    logger.info(f"Updating database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Create tables if not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                bullish_count INTEGER,
                bearish_count INTEGER,
                neutral_count INTEGER,
                sentiment_score REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                indicator_type TEXT,
                value REAL
            )
        ''')
        
        # Insert sentiment data
        if sentiment_data:
            cursor.execute('''
                INSERT INTO sentiment_log 
                (bullish_count, bearish_count, neutral_count, sentiment_score)
                VALUES (?, ?, ?, ?)
            ''', (
                sentiment_data.get('bullish_count', 0),
                sentiment_data.get('bearish_count', 0),
                sentiment_data.get('neutral_count', 0),
                sentiment_data.get('sentiment_score', 0.0)
            ))
        
        # Insert indicator data
        for symbol, df in indicator_data.items():
            if not df.empty:
                latest = df.iloc[-1]
                indicators = [
                    ('sma_20', latest.get('sma_20')),
                    ('ema_20', latest.get('ema_20')),
                    ('rsi_14', latest.get('rsi_14')),
                    ('macd', latest.get('macd')),
                    ('bb_position', latest.get('bb_position'))
                ]
                
                for indicator_type, value in indicators:
                    if value is not None and not pd.isna(value):
                        cursor.execute('''
                            INSERT INTO stock_indicators (symbol, indicator_type, value)
                            VALUES (?, ?, ?)
                        ''', (symbol, indicator_type, float(value)))
        
        conn.commit()
        logger.info("Database updated successfully")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting market sentiment update")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Fetch PTT sentiment
        sentiment_data = fetch_ptt_sentiment()
        
        # Step 2: Calculate indicators (if stock data available)
        # This would typically fetch from Yahoo Finance or similar
        # For now, we'll skip this step or implement later
        indicator_data = {}
        
        # Step 3: Update database
        if sentiment_data:
            update_database(sentiment_data, indicator_data)
        
        # Log completion
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info(f"Update completed in {duration:.2f}s")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
