#!/bin/bash
# Email-Intelligence 每日 review 定时（macOS launchd）：09:30（欧美盘后邮件齐 + 晚间亚盘邮件到）
# 用法：bash install_launchd.sh
set -e

WS="$(cd "$(dirname "$0")/../../.." && pwd)"   # 自动推导（跨机不用改）
PY="/opt/homebrew/bin/python3.12"
SCRIPT="$WS/.scripts/email-intelligence/run_email_intel.py"
LA="$HOME/Library/LaunchAgents"
LOG_DIR="$WS/daily/logs"
mkdir -p "$LA" "$LOG_DIR"

plist="$LA/com.cc.email-intel-review.plist"
cat > "$plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.cc.email-intel-review</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$SCRIPT</string>
        <string>review</string>
        <string>--workspace</string><string>$WS</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>30</integer>
        <key>Weekday</key>
        <array>
            $(for w in 1 2 3 4 5 6; do echo "<integer>$w</integer>"; done)
        </array>
    </dict>
    <key>StandardOutPath</key><string>$LOG_DIR/email-intel-review.log</string>
    <key>StandardErrorPath</key><string>$LOG_DIR/email-intel-review.err</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
EOF
launchctl unload "$plist" 2>/dev/null || true
launchctl load "$plist"
echo "已安装 email-intel review（09:30，周一~六）→ $plist"
echo "日志：$LOG_DIR/email-intel-review.{log,err}"
