#!/usr/bin/env python3
"""
Stock Analysis Worker - Background monitoring and auto-update service
Monitors stock prices and triggers updates when needed.
"""

import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_market_hours():
    """Check if currently within market hours (9:00-13:30 TW time)"""
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    # Weekend check
    if weekday >= 5:
        return False
    
    # Market hours: 9:00 - 13:30
    if hour < 9 or hour > 13:
        return False
    if hour == 13 and minute > 30:
        return False
    
    return True

def main():
    logger.info("🚀 Stock Worker started")
    logger.info("Monitoring interval: 60 seconds")
    logger.info("Market hours: Mon-Fri 9:00-13:30 TWT")
    
    last_update = None
    update_interval = timedelta(hours=1)  # Update every hour during market hours
    
    while True:
        try:
            now = datetime.now()
            
            # Check if within market hours
            if check_market_hours():
                # During market hours - update hourly
                if last_update is None or (now - last_update) >= update_interval:
                    logger.info("📊 Running scheduled update...")
                    # Trigger update via daily_schedule
                    import subprocess
                    result = subprocess.run(
                        ['python3', 'daily_schedule.py', '--run-heartbeat'],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        logger.info("✅ Update completed successfully")
                    else:
                        logger.error(f"❌ Update failed: {result.stderr}")
                    last_update = now
            else:
                # Outside market hours - just log status
                if now.hour == 0 and now.minute < 5 and last_update is None or \
                   (last_update and last_update.date() != now.date()):
                    logger.info("🌙 Outside market hours - no updates needed")
            
            # Sleep for 60 seconds
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
