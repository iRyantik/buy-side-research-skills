#!/usr/bin/env bash
set -euo pipefail

CHECK_ONLY=0
YES=0

for arg in "$@"; do
  case "$arg" in
    --check-only) CHECK_ONLY=1 ;;
    --yes) YES=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 64 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REQ="$SKILL_ROOT/assets/requirements-reddit-sentiment.txt"

echo "== reddit-sentiment dependency check =="

if ! command -v python >/dev/null 2>&1; then
  echo "python is not available on PATH. Install Python 3.12+ or activate the intended environment first." >&2
  exit 2
fi

echo "python: $(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"

if command -v scrapi-reddit >/dev/null 2>&1; then
  echo "scrapi-reddit: available"
  exit 0
fi

echo "scrapi-reddit: missing"

if [ "$CHECK_ONLY" -eq 1 ]; then
  exit 2
fi

if [ "$YES" -ne 1 ]; then
  echo "Pass --yes to install reddit-sentiment dependencies from $REQ." >&2
  exit 2
fi

python -m pip install -r "$REQ"

if ! command -v scrapi-reddit >/dev/null 2>&1; then
  echo "Install completed, but scrapi-reddit is still not available on PATH. Restart the shell or check the Python Scripts directory." >&2
  exit 2
fi

echo "reddit-sentiment dependencies are ready."
