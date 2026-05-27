#!/bin/sh
set -eu

if [ "$#" -lt 1 ]; then
  printf '%s\n' "Blocked by hook launcher: missing target hook path." >&2
  exit 64
fi

script_path=$1
shift

# Prefer Python version if available (cross-platform, no pwsh dependency)
py_path="${script_path%.ps1}.py"
if [ -f "$py_path" ] && command -v python3 >/dev/null 2>&1; then
  exec python3 "$py_path" "$@"
fi

# Fallback: PowerShell (requires pwsh on macOS, built-in on Windows)
if command -v pwsh >/dev/null 2>&1; then
  exec pwsh -NoProfile -ExecutionPolicy Bypass -File "$script_path" "$@"
fi

printf '%s\n' "Blocked by hook launcher: unable to locate python3 or pwsh. Install Python 3.10+ or PowerShell 7 to enable workspace hooks." >&2
exit 2
