#!/usr/bin/env python3
"""
System Status Checker

Checks the status of all components:
- Data collector (yfinance)
- PTT scraper
- Database
- Technical indicators
- Correlation analysis

Usage:
    python check_status.py
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from config import STOCK_UNIVERSE, DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database():
    """Check database status."""
    print("\n" + "="*60)
    print("DATABASE STATUS")
    print("="*60)
    
    if not Path(DB_PATH).exists():
        print(f"✗ Database not found: {DB_PATH}")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {', '.join(tables)}")
        
        # Check data counts
        for table in ['stock_prices', 'sentiment_log', 'stock_indicators']:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} records")
            except:
                print(f"  - {table}: not found")
        
        # Check latest data date
        try:
            cursor.execute('''
                SELECT symbol, MAX(date), COUNT(*) 
                FROM stock_prices 
                GROUP BY symbol 
                LIMIT 5
            ''')
            latest = cursor.fetchall()
            print(f"\nLatest data by stock:")
            for symbol, date, count in latest:
                print(f"  {symbol}: {count} records, latest: {date}")
        except Exception as e:
            print(f"Error checking latest data: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()


def check_data_collector():
    """Check data collector (yfinance) status."""
    print("\n" + "="*60)
    print("DATA COLLECTOR (YFINANCE) STATUS")
    print("="*60)
    
    try:
        import yfinance as yf
        
        # Test fetch
        test_symbols = ['2330.TW', '2317.TW']
        
        for symbol in test_symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='5d')
                
                if not df.empty:
                    print(f"✓ {symbol}: OK ({len(df)} records)")
                    print(f"  Latest close: {df['Close'].iloc[-1]:.2f}")
                else:
                    print(f"⚠ {symbol}: No data returned")
                    
            except Exception as e:
                print(f"✗ {symbol}: {e}")
        
        return True
        
    except ImportError:
        print("✗ yfinance not installed")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_ptt_scraper():
    """Check PTT scraper status."""
    print("\n" + "="*60)
    print("PTT SCRAPER STATUS")
    print("="*60)
    
    try:
        from ptt_bus import fetch_ptt_posts, analyze_sentiment
        
        # Test fetch
        print("Fetching from PTT stock board...")
        posts = fetch_ptt_posts(limit=5)
        
        if posts:
            print(f"✓ Successfully fetched {len(posts)} posts")
            
            # Show sample
            print(f"\nLatest post:")
            post = posts[0]
            print(f"  Title: {post.title}")
            print(f"  Author: {post.author}")
            print(f"  Date: {post.date}")
            
            # Test sentiment
            print(f"\nSentiment analysis:")
            sentiment = analyze_sentiment(posts)
            print(f"  Bullish: {sentiment['bullish_count']}")
            print(f"  Bearish: {sentiment['bearish_count']}")
            print(f"  Neutral: {sentiment['neutral_count']}")
            print(f"  Score: {sentiment['sentiment_score']}")
        else:
            print("⚠ No posts fetched (might be rate limited)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_indicators():
    """Check technical indicators module."""
    print("\n" + "="*60)
    print("TECHNICAL INDICATORS STATUS")
    print("="*60)
    
    try:
        from indicators import add_indicators, get_indicator_columns
        import pandas as pd
        
        # Create test data
        test_data = pd.DataFrame({
            'open': range(100, 150),
            'high': range(101, 151),
            'low': range(99, 149),
            'close': range(100, 150),
            'volume': [1000000] * 50
        })
        
        # Test indicator calculation
        result = add_indicators(test_data)
        
        expected_cols = get_indicator_columns()
        actual_cols = [col for col in expected_cols if col in result.columns]
        
        print(f"✓ Indicators calculated successfully")
        print(f"  Available indicators: {len(actual_cols)}/{len(expected_cols)}")
        print(f"  Columns: {', '.join(actual_cols[:10])}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_correlation_analysis():
    """Check correlation analysis module."""
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS STATUS")
    print("="*60)
    
    try:
        # Just check if module loads
        import correlation_analysis
        print("✓ Correlation analysis module loaded")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_stock_universe():
    """Check stock universe configuration."""
    print("\n" + "="*60)
    print("STOCK UNIVERSE")
    print("="*60)
    
    from config import STOCK_UNIVERSE
    
    print(f"Total stocks tracked: {len(STOCK_UNIVERSE)}")
    
    # Group by sector (simple classification)
    sectors = {}
    for symbol, name in STOCK_UNIVERSE.items():
        if symbol in ['2330', '2317', '2454', '2308', '2353', '2357', '2395']:
            sector = 'Technology'
        elif symbol in ['2881', '2882', '2886', '2891', '2892']:
            sector = 'Finance'
        elif symbol in ['1301', '1303', '1326', '1101', '1102']:
            sector = 'Traditional'
        else:
            sector = 'Other'
        
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(f"{symbol} ({name})")
    
    for sector, stocks in sectors.items():
        print(f"\n{sector} ({len(stocks)}):")
        print(f"  {', '.join(stocks[:5])}")
        if len(stocks) > 5:
            print(f"  ... and {len(stocks)-5} more")


def main():
    print("\n" + "="*60)
    print("STOCK ANALYSIS PIPELINE - STATUS CHECK")
    print(f"Timestamp: {datetime.now()}")
    print("="*60)
    
    # Run all checks
    check_database()
    check_data_collector()
    check_ptt_scraper()
    check_indicators()
    check_correlation_analysis()
    check_stock_universe()
    
    print("\n" + "="*60)
    print("STATUS CHECK COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
