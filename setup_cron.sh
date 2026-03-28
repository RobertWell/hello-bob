#!/bin/bash
# Setup cron jobs for complete stock analysis pipeline

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

echo "Setting up cron jobs for stock analysis pipeline..."
echo "Script directory: $SCRIPT_DIR"

# Create necessary directories
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/reports"
mkdir -p "$SCRIPT_DIR/data"

# Show current crontab
echo ""
echo "Current crontab:"
crontab -l 2>/dev/null || echo "(no existing crontab)"

# Define cron jobs
CRON_JOBS="
# Stock Analysis Pipeline - Auto-generated $(date +%Y-%m-%d)
# Complete daily schedule for Taiwan stock market analysis

# 6:00 AM - Morning routine (data collection & morning report)
0 6 * * * cd $SCRIPT_DIR && $PYTHON_CMD daily_schedule.py --morning >> logs/cron.log 2>&1

# 9:00 AM - Market open check
0 9 * * 1-5 cd $SCRIPT_DIR && $PYTHON_CMD daily_schedule.py --market-open >> logs/cron.log 2>&1

# 12:00 PM - Midday sentiment update
0 12 * * 1-5 cd $SCRIPT_DIR && $PYTHON_CMD daily_schedule.py --midday >> logs/cron.log 2>&1

# 6:00 PM - Market close (EOD report)
0 18 * * 1-5 cd $SCRIPT_DIR && $PYTHON_CMD daily_schedule.py --market-close >> logs/cron.log 2>&1

# 10:00 PM - Evening correlation analysis
0 22 * * * cd $SCRIPT_DIR && $PYTHON_CMD daily_schedule.py --evening >> logs/cron.log 2>&1

# Every hour - Quick data refresh
0 * * * * cd $SCRIPT_DIR && $PYTHON_CMD data_collector.py --all-stocks --days 1 >> logs/cron.log 2>&1

# Sunday 10:00 AM - Full historical data update (365 days)
0 10 * * 0 cd $SCRIPT_DIR && $PYTHON_CMD data_collector.py --all-stocks --days 365 >> logs/cron.log 2>&1

# Daily 11:00 PM - System health check
0 23 * * * cd $SCRIPT_DIR && $PYTHON_CMD check_status.py >> logs/cron.log 2>&1
"

echo ""
echo "Installing the following cron jobs:"
echo "$CRON_JOBS"
echo ""
echo -n "Proceed with installation? (y/n): "
read -r response
if [[ $response == "y" || $response == "Y" ]]; then
    # Backup existing crontab
    crontab -l > "$SCRIPT_DIR/crontab.backup.$(date +%Y%m%d%H%M%S)" 2>/dev/null
    
    # Install new crontab
    (crontab -l 2>/dev/null | grep -v "Stock Analysis Pipeline"; echo "$CRON_JOBS") | crontab -
    
    echo ""
    echo "✓ Cron jobs installed successfully!"
    echo ""
    echo "View with: crontab -l"
    echo "Edit with: crontab -e"
    echo "Remove with: crontab -e (delete lines)"
    echo ""
    echo "Logs will be in: $SCRIPT_DIR/logs/"
else
    echo "Installation cancelled."
fi
