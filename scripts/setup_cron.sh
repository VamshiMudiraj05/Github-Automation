#!/usr/bin/env bash
# Cron setup script for Linux / macOS always-on workers
# Configures crontab to run daily at 00:00 IST (12:00 AM midnight Asia/Kolkata)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(which python3 || which python)"

echo "Setting up crontab for Autonomous 30-Day Project Agent..."
echo "Project Directory: $PROJECT_DIR"
echo "Python Binary: $PYTHON_BIN"

# Check if crontab entry already exists
CRON_CMD="0 0 * * * cd $PROJECT_DIR && $PYTHON_BIN main.py run >> logs/cron.log 2>&1"

(crontab -l 2>/dev/null | grep -v "main.py run" ; echo "$CRON_CMD") | crontab -

echo "✅ Crontab entry registered successfully!"
echo "Schedule: 0 0 * * * (Daily at 12:00 AM midnight local time)"
crontab -l | grep "main.py run"
