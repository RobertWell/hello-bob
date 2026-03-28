#!/bin/bash
# Setup cron jobs for stock analysis pipeline

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

echo "Setting up cron jobs for stock analysis pipeline..."
echo "Script directory: $SCRIPT_DIR"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/reports"

# Current cron jobs
echo ""
echo "Current crontab:"
crontab -l 2>/dev/null || echo "(no existing crontab)"

# Add to crontab
CRON_JOBS="
# Stock Analysis Pipeline - Auto-generated
# Collect data every day at 6:00 AM
0 6 * * * cd $SCRIPT_DIR && $PYTHON_CMD run_pipeline.py --collect-data --days 1 >> logs/cron.log 2>&1

# Generate daily report at 8:00 AM (market open)
0 8 * * 1-5 cd $SCRIPT_DIR && $PYTHON_CMD run_pipeline.py --report >> logs/cron.log 2>&1

# Run correlation analysis every Sunday at 10:00 AM
0 10 * * 0 cd $SCRIPT_DIR && $PYTHON_CMD correlation_analysis.py >> logs/cron.log 2>&1
"

echo ""
echo "Adding the following cron jobs:"
echo "$CRON_JOBS"
echo ""
echo -n "Proceed with installation? (y/n): "
read -r response
if [[ $response == "y" ]]; then
    (crontab -l 2>/dev/null | grep -v "Stock Analysis Pipeline"; echo "$CRON_JOBS") | crontab -
    echo "Cron jobs installed successfully!"
    echo ""
    echo "View with: crontab -l"
    echo "Remove with: crontab -e"
else
    echo "Installation cancelled."
fi
