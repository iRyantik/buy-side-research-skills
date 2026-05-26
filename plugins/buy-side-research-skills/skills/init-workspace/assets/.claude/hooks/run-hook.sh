#!/bin/sh
set -eu

if [ "$#" -lt 1 ]; then
  printf '%s\n' "Blocked by hook launcher: missing target .ps1 path." >&2
  exit 64
fi

script_path=$1
shift

if command -v pwsh >/dev/null 2>&1; then
  exec pwsh -NoProfile -ExecutionPolicy Bypass -File "$script_path" "$@"
fi

printf '%s\n' "Blocked by hook launcher: unable to locate PowerShell 7 (pwsh). Install pwsh before using workspace hooks on macOS." >&2
exit 2
