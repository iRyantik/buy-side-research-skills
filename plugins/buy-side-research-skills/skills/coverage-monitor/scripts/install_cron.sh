#!/bin/bash
# 日报两时点自动触发：07:45 欧美盘后(us=美+欧) / 16:15 亚盘盘后(asia)
# 欧盘异动并入次早 us 邮件（23:45 eu 时点已废弃）
# 用法：bash install_cron.sh   （会覆盖同名 cron 条目，先备份现有 crontab）

set -e
WS="/Users/ryanxing/CC Research Workspace"
PY="/opt/homebrew/bin/python3.12"
SCRIPT="$WS/.scripts/coverage-monitor/run_coverage_monitor.py"
LOG_DIR="$WS/reports/coverage-monitor"
mkdir -p "$LOG_DIR"

# 备份现有 crontab
crontab -l > /tmp/coverage_cron_backup.txt 2>/dev/null || echo "# 无现有 crontab" > /tmp/coverage_cron_backup.txt
echo "现有 crontab 已备份到 /tmp/coverage_cron_backup.txt"

# 去掉旧的 coverage-monitor 条目（如果重复安装）
crontab -l 2>/dev/null | grep -v "run_coverage_monitor.py" > /tmp/cron_filtered.txt || true

# 追加两时点
cat >> /tmp/cron_filtered.txt << EOF
45 7 * * * cd "$WS" && $PY $SCRIPT daily --report-type us --workspace "$WS" >> "$LOG_DIR/cron-us.log" 2>&1
15 16 * * * cd "$WS" && $PY $SCRIPT daily --report-type asia --workspace "$WS" >> "$LOG_DIR/cron-asia.log" 2>&1
EOF

crontab /tmp/cron_filtered.txt
echo "已安装 2 条 cron："
crontab -l | grep run_coverage_monitor
echo ""
echo "日志：$LOG_DIR/cron-*.log"
