#!/usr/bin/env python3
"""
Daily Schedule Runner

Runs the complete stock analysis pipeline on a daily schedule:
- 6:00 AM: Collect latest data
- 8:00 AM: Generate daily report
- 12:00 PM: Midday update
- 6:00 PM: End of day analysis
- 10:00 PM: Correlation analysis

Usage:
    python daily_schedule.py --run-all
    python daily_schedule.py --collect
    python daily_schedule.py --report
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import STOCK_UNIVERSE, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/schedule.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_morning_routine():
    """
    Morning routine (6:00 AM - Market open prep)
    - Collect overnight data
    - Update sentiment
    - Generate morning report
    """
    logger.info("="*60)
    logger.info("MORNING ROUTINE (6:00 AM)")
    logger.info("="*60)
    
    try:
        # Collect latest data
        from data_collector import collect_all_stocks
        logger.info("Collecting overnight data...")
        collect_all_stocks(days=1)  # Just latest day
        
        # Generate morning report
        from daily_report import generate_report
        logger.info("Generating morning report...")
        report = generate_report()
        
        logger.info("Morning routine complete")
        return True
        
    except Exception as e:
        logger.error(f"Morning routine failed: {e}", exc_info=True)
        return False


def run_market_open_routine():
    """
    Market open routine (9:00 AM)
    - Final pre-market check
    - Send alerts
    """
    logger.info("="*60)
    logger.info("MARKET OPEN ROUTINE (9:00 AM)")
    logger.info("="*60)
    
    try:
        from trend_tracker import analyze_all_stocks
        
        # Analyze top stocks
        top_stocks = ['2330', '2317', '2454', '2881', '1301']
        results = analyze_all_stocks(top_stocks)
        
        # Generate alerts
        alerts = []
        for symbol, data in results.items():
            if 'alerts' in data and data['alerts']:
                alerts.extend(data['alerts'])
        
        if alerts:
            logger.info(f"Generated {len(alerts)} alerts")
            for alert in alerts:
                logger.info(f"  - {alert}")
        
        return True
        
    except Exception as e:
        logger.error(f"Market open routine failed: {e}", exc_info=True)
        return False


def run_midday_routine():
    """
    Midday routine (12:00 PM)
    - Quick market check
    - Update sentiment
    """
    logger.info("="*60)
    logger.info("MIDDAY ROUTINE (12:00 PM)")
    logger.info("="*60)
    
    try:
        from ptt_bus import fetch_ptt_posts, analyze_sentiment
        
        # Quick sentiment check
        posts = fetch_ptt_posts(limit=20)
        if posts:
            sentiment = analyze_sentiment(posts)
            logger.info(f"Midday sentiment - Score: {sentiment['sentiment_score']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Midday routine failed: {e}", exc_info=True)
        return False


def run_market_close_routine():
    """
    Market close routine (6:00 PM)
    - Full day analysis
    - Update all indicators
    - Generate EOD report
    """
    logger.info("="*60)
    logger.info("MARKET CLOSE ROUTINE (6:00 PM)")
    logger.info("="*60)
    
    try:
        # Collect final data
        from data_collector import collect_all_stocks
        logger.info("Collecting final EOD data...")
        collect_all_stocks(days=1)
        
        # Generate EOD report
        from daily_report import generate_report
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        report_file = reports_dir / f"eod_report_{timestamp}.md"
        
        logger.info("Generating EOD report...")
        generate_report(str(report_file))
        
        return True
        
    except Exception as e:
        logger.error(f"Market close routine failed: {e}", exc_info=True)
        return False


def run_evening_analysis():
    """
    Evening analysis (10:00 PM)
    - Correlation analysis
    - Trend analysis
    - Prepare for next day
    """
    logger.info("="*60)
    logger.info("EVENING ANALYSIS (10:00 PM)")
    logger.info("="*60)
    
    try:
        # Correlation analysis
        from correlation_analysis import main as correlation_main
        logger.info("Running correlation analysis...")
        correlation_main()
        
        return True
        
    except Exception as e:
        logger.error(f"Evening analysis failed: {e}", exc_info=True)
        return False


def run_all():
    """Run complete daily schedule."""
    logger.info("="*60)
    logger.info("RUNNING COMPLETE DAILY SCHEDULE")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*60)
    
    results = {
        'morning': run_morning_routine(),
        'market_open': run_market_open_routine(),
        'midday': run_midday_routine(),
        'market_close': run_market_close_routine(),
        'evening': run_evening_analysis()
    }
    
    success_count = sum(results.values())
    total_count = len(results)
    
    logger.info("="*60)
    logger.info(f"Schedule complete: {success_count}/{total_count} successful")
    logger.info("="*60)
    
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description='Daily schedule runner')
    parser.add_argument('--run-all', action='store_true', help='Run complete schedule')
    parser.add_argument('--morning', action='store_true', help='Run morning routine')
    parser.add_argument('--market-open', action='store_true', help='Run market open routine')
    parser.add_argument('--midday', action='store_true', help='Run midday routine')
    parser.add_argument('--market-close', action='store_true', help='Run market close routine')
    parser.add_argument('--evening', action='store_true', help='Run evening analysis')
    parser.add_argument('--collect', action='store_true', help='Collect data only')
    parser.add_argument('--report', action='store_true', help='Generate report only')
    
    args = parser.parse_args()
    
    if args.run_all:
        success = run_all()
    elif args.morning:
        success = run_morning_routine()
    elif args.market_open:
        success = run_market_open_routine()
    elif args.midday:
        success = run_midday_routine()
    elif args.market_close:
        success = run_market_close_routine()
    elif args.evening:
        success = run_evening_analysis()
    elif args.collect:
        from data_collector import collect_all_stocks
        collect_all_stocks(days=1)
        success = True
    elif args.report:
        from daily_report import generate_report
        generate_report()
        success = True
    else:
        parser.print_help()
        success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
