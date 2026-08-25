#!/bin/bash
# Email-Intelligence 每日 review 定时（cron 备用）：09:30 周一~六
# 用法：bash install_cron.sh
set -e
WS="$(cd "$(dirname "$0")/../../.." && pwd)"   # 自动推导（跨机不用改）
PY="/opt/homebrew/bin/python3.12"
SCRIPT="$WS/.scripts/email-intelligence/run_email_intel.py"
LOG_DIR="$WS/daily/logs"
mkdir -p "$LOG_DIR"

crontab -l > /tmp/email_intel_cron_backup.txt 2>/dev/null || echo "# 无现有 crontab" > /tmp/email_intel_cron_backup.txt
crontab -l 2>/dev/null | grep -v "run_email_intel.py" > /tmp/email_intel_cron_filtered.txt || true
cat >> /tmp/email_intel_cron_filtered.txt << EOF
30 9 * * 1-6 cd "$WS" && $PY $SCRIPT review --workspace "$WS" >> "$LOG_DIR/email-intel-review.log" 2>&1
EOF
crontab /tmp/email_intel_cron_filtered.txt
echo "已安装 email-intel review（30 9 * * 1-6）"
echo "日志：$LOG_DIR/email-intel-review.log"
