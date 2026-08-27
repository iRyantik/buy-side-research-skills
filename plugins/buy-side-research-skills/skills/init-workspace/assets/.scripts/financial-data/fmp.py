#!/usr/bin/env python3
"""FMP stable-API client — single correct entry point for ad-hoc pulls.

Why this exists: FMP migrated its API after 2025-08-31. The legacy /api/v3/
endpoints now return HTTP 403 "Legacy Endpoint no longer supported", and the
same .env FMP_API_KEY must be used against /stable/ instead. Ad-hoc scripts and
curl one-liners kept hitting the legacy wall; this wraps the /stable/ base so
that never happens by mistake.

Reads FMP_API_KEY from the workspace .env (same key the pipeline's fmp_provider
uses). Importable (for scripts) and CLI-usable (for one-liners).

CLI:
    python .scripts/financial-data/fmp.py --check                  # verify key + base
    python .scripts/financial-data/fmp.py profile 2507.HK
    python .scripts/financial-data/fmp.py quote 2507.HK
    python .scripts/financial-data/fmp.py income 2507.HK --period annual --limit 5
    python .scripts/financial-data/fmp.py balance 2507.HK --period quarterly --limit 4
    python .scripts/financial-data/fmp.py cash 2507.HK
    python .scripts/financial-data/fmp.py ratios 2507.HK
    python .scripts/financial-data/fmp.py key-metrics 2507.HK
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


# Default base pinned to the new /stable/ API. Override via env FMP_BASE_URL.
BASE_URL = os.environ.get("FMP_BASE_URL", "https://financialmodelingprep.com/stable")


def _load_env() -> dict[str, str]:
    """Load workspace .env into os.environ (without clobbering existing vars)."""
    # Discover workspace root: walk up from cwd or this script to find .env.
    roots = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[2]]
    for root in roots:
        envp = root / ".env"
        if envp.is_file():
            for line in envp.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
            break
    return os.environ


def get_key() -> str:
    key = os.environ.get("FMP_API_KEY") or _load_env().get("FMP_API_KEY")
    if not key:
        raise RuntimeError("Missing FMP_API_KEY — set it in workspace .env")
    return key


def api(path: str, **params) -> Any:
    """GET {BASE_URL}{path} with the key. Returns parsed JSON."""
    params.setdefault("apikey", get_key())
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    req = urlopen(url, timeout=30)
    return json.loads(req.read().decode("utf-8"))


# --- typed convenience wraps -------------------------------------------------
def profile(sym: str) -> Any:  return api("/profile", symbol=sym)
def quote(sym: str) -> Any:     return api("/quote", symbol=sym)
def income_statement(sym: str, period: str = "annual", limit: int = 5) -> Any:
    return api("/income-statement", symbol=sym, period=period, limit=limit)
def balance_sheet(sym: str, period: str = "annual", limit: int = 5) -> Any:
    return api("/balance-sheet-statement", symbol=sym, period=period, limit=limit)
def cash_flow(sym: str, period: str = "annual", limit: int = 5) -> Any:
    return api("/cash-flow-statement", symbol=sym, period=period, limit=limit)
def ratios(sym: str, period: str = "annual", limit: int = 5) -> Any:
    return api("/ratios", symbol=sym, period=period, limit=limit)
def key_metrics(sym: str, period: str = "annual", limit: int = 5) -> Any:
    return api("/key-metrics", symbol=sym, period=period, limit=limit)


def check() -> dict[str, Any]:
    """Verify the key against a known ticker and report the active base URL."""
    from urllib.error import HTTPError
    try:
        data = profile("AAPL")
        ok = isinstance(data, list) and bool(data)
        return {"ok": ok, "base": BASE_URL, "key_len": len(get_key()),
                "sample": (data[0].get("companyName") if ok else None),
                "error": None}
    except HTTPError as e:
        return {"ok": False, "base": BASE_URL, "key_len": len(get_key()),
                "sample": None, "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"ok": False, "base": BASE_URL, "key_len": len(get_key()),
                "sample": None, "error": str(e)}


def _main() -> int:
    p = argparse.ArgumentParser(description="FMP /stable/ API client (workspace-scoped)")
    p.add_argument("--check", action="store_true", help="verify key + show base URL")
    p.add_argument("endpoint", nargs="?", help="profile|quote|income|balance|cash|ratios|key-metrics")
    p.add_argument("symbol", nargs="?", help="ticker symbol, e.g. 2507.HK")
    p.add_argument("--period", default="annual", help="annual|quarter")
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()

    if args.check:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
        return 0

    if not args.endpoint or not args.symbol:
        p.print_help()
        return 1

    fn = {
        "profile": profile, "quote": quote, "income": income_statement,
        "balance": balance_sheet, "cash": cash_flow,
        "ratios": ratios, "key-metrics": key_metrics,
    }.get(args.endpoint)
    if fn is None:
        p.error(f"unknown endpoint '{args.endpoint}'")

    data = fn(args.symbol, period=args.period, limit=args.limit) if args.endpoint in (
        "income", "balance", "cash", "ratios", "key-metrics") else fn(args.symbol)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
