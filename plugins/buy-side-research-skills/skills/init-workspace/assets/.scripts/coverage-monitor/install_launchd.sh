#!/bin/bash
# 日报三时点自动触发（macOS launchd）：07:45 盘前 / 16:15 亚盘 / 23:45 欧盘
# 用法：bash install_launchd.sh
set -e

WS="/Users/ryanxing/CC Research Workspace"
PY="/opt/homebrew/bin/python3.12"
SCRIPT="$WS/.scripts/coverage-monitor/run_coverage_monitor.py"
LA="$HOME/Library/LaunchAgents"
LOG_DIR="$WS/reports/coverage-monitor"
mkdir -p "$LA" "$LOG_DIR"

install_one() {
    local rt="$1" H="$2" M="$3"
    local plist="$LA/com.cc.daily-brief-$rt.plist"
    cat > "$plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.cc.daily-brief-$rt</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$SCRIPT</string>
        <string>daily</string>
        <string>--report-type</string><string>$rt</string>
        <string>--workspace</string><string>$WS</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>$H</integer>
        <key>Minute</key><integer>$M</integer>
        <key>Weekday</key>
        <array>
            <integer>1</integer><integer>2</integer><integer>3</integer><integer>4</integer><integer>5</integer>
        </array>
    </dict>
    <key>StandardOutPath</key><string>$LOG_DIR/cron-$rt.log</string>
    <key>StandardErrorPath</key><string>$LOG_DIR/cron-$rt.err</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
EOF
    launchctl unload "$plist" 2>/dev/null || true
    launchctl load "$plist"
    echo "已安装 $rt（${H}:${M}）→ $plist"
}

install_one us 7 45
install_one asia 16 15
install_one eu 23 45
echo ""
echo "日志：$LOG_DIR/cron-*.log"
