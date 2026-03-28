#!/usr/bin/env python3
"""
Stock Analysis Pipeline - Main Runner

Orchestrates the complete stock analysis pipeline:
1. Fetch latest price data
2. Calculate technical indicators
3. Analyze sentiment
4. Update database
5. Generate alerts and reports

Usage:
    python run_pipeline.py --collect-data --analyze --report
    python run_pipeline.py --daily  # Full daily run
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import STOCK_UNIVERSE, ANALYSIS_CONFIG, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def collect_historical_data(days: int = 365):
    """
    Step 1: Collect historical data for all stocks.
    
    Parameters
    ----------
    days : int
        Number of days to collect
    """
    logger.info("="*60)
    logger.info("STEP 1: Collecting historical data")
    logger.info("="*60)
    
    from data_collector import collect_all_stocks
    collect_all_stocks(days)
    
    logger.info("Historical data collection complete")


def calculate_indicators():
    """
    Step 2: Calculate technical indicators for all stocks.
    """
    logger.info("="*60)
    logger.info("STEP 2: Calculating technical indicators")
    logger.info("="*60)
    
    # This is handled on-demand in trend_tracker
    # Could pre-calculate and store in database
    logger.info("Indicators will be calculated on-demand")


def analyze_sentiment():
    """
    Step 3: Analyze market sentiment from PTT.
    """
    logger.info("="*60)
    logger.info("STEP 3: Analyzing market sentiment")
    logger.info("="*60)
    
    from ptt_bus import fetch_ptt_posts, analyze_sentiment
    
    posts = fetch_ptt_posts(limit=50)
    if posts:
        sentiment = analyze_sentiment(posts)
        logger.info(f"Sentiment - Bullish: {sentiment['bullish_count']}, "
                   f"Bearish: {sentiment['bearish_count']}, "
                   f"Score: {sentiment['sentiment_score']}")
    else:
        logger.warning("No sentiment data available")


def generate_daily_report():
    """
    Step 4: Generate daily report.
    """
    logger.info("="*60)
    logger.info("STEP 4: Generating daily report")
    logger.info("="*60)
    
    from daily_report import generate_report
    
    # Create reports directory
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Generate report with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_file = reports_dir / f"daily_report_{timestamp}.md"
    
    report = generate_report(str(report_file))
    logger.info(f"Report generated: {report_file}")


def run_correlation_analysis():
    """
    Step 5: Analyze stock correlations.
    """
    logger.info("="*60)
    logger.info("STEP 5: Running correlation analysis")
    logger.info("="*60)
    
    from correlation_analysis import main as correlation_main
    correlation_main()


def main():
    parser = argparse.ArgumentParser(description='Stock analysis pipeline runner')
    parser.add_argument('--collect-data', action='store_true',
                       help='Collect historical data')
    parser.add_argument('--analyze', action='store_true',
                       help='Run trend analysis')
    parser.add_argument('--correlation', action='store_true',
                       help='Run correlation analysis')
    parser.add_argument('--report', action='store_true',
                       help='Generate daily report')
    parser.add_argument('--daily', action='store_true',
                       help='Run complete daily pipeline')
    parser.add_argument('--days', type=int, default=365,
                       help='Days of historical data to collect')
    
    args = parser.parse_args()
    
    logger.info("Starting stock analysis pipeline")
    logger.info(f"Timestamp: {datetime.now()}")
    
    try:
        if args.daily:
            # Full daily run
            collect_historical_data(days=365)
            calculate_indicators()
            analyze_sentiment()
            run_correlation_analysis()
            generate_daily_report()
        else:
            # Run specified steps
            if args.collect_data:
                collect_historical_data(days=args.days)
            
            if args.analyze:
                calculate_indicators()
            
            if args.correlation:
                run_correlation_analysis()
            
            if args.report:
                generate_daily_report()
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
