#!/usr/bin/env python3
"""Unified data routing for buy-side research.

Resolves capability → source chain from capability-matrix.json.
Returns the full fallback chain so the agent executes in order
without needing to re-query on failure.

Usage:
    python .scripts/shared/route.py AAPL.US valuation_snapshot
    python .scripts/shared/route.py 700.HK consensus --skip longbridge_mcp
    python .scripts/shared/route.py TSLA.US market_quote --json
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Workspace discovery（复用 financial_data.py 逻辑）
# ---------------------------------------------------------------------------

def discover_workspace(source: Path | None = None) -> Path:
    candidates = [source or Path.cwd(), Path.cwd()]
    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in [current, *current.parents]:
            if (parent / "industry").is_dir():
                return parent
    return None  # route.py returns None instead of raising — caller handles


# ---------------------------------------------------------------------------
# Matrix loading
# ---------------------------------------------------------------------------

def load_matrix(workspace: Path) -> dict:
    """Load capability-matrix.json from workspace references."""
    matrix_path = workspace / ".references" / "routing" / "capability-matrix.json"
    if not matrix_path.exists():
        return _default_matrix()
    with open(matrix_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _default_matrix() -> dict:
    """Minimal fallback matrix if workspace file is missing."""
    return {
        "sources": {
            "actuals_cache": {"type": "local", "markets": ["*"], "check": "file_exists"},
            "longbridge_mcp": {"type": "mcp", "markets": ["US", "HK", "SH", "SZ", "SG"]},
            "yfinance": {"type": "python_lib", "markets": ["*"]},
            "web_search": {"type": "tool", "markets": ["*"]},
        },
        "chains": {
            "market_quote": ["actuals_cache", "longbridge_mcp", "yfinance", "web_search"],
            "default": ["longbridge_mcp", "yfinance", "web_search"],
        },
        "tool_map": {},
    }


# ---------------------------------------------------------------------------
# Source availability checks
# ---------------------------------------------------------------------------

def find_actuals_path(workspace: Path, ticker: str) -> Path | None:
    """Find actuals-resolved.json for a ticker across all industries."""
    industry_dir = workspace / "industry"
    if not industry_dir.is_dir():
        return None
    # Strip market suffix if present (e.g. AAPL.US → AAPL)
    slug = ticker.split(".")[0].lower()
    for ind in industry_dir.iterdir():
        if not ind.is_dir():
            continue
        candidate = ind / "companies" / slug / "_cache" / "financial-data" / "actuals-resolved.json"
        if candidate.exists():
            return candidate
        # Also try uppercase slug
        slug_upper = ticker.split(".")[0].upper().lower()
        candidate2 = ind / "companies" / slug_upper / "_cache" / "financial-data" / "actuals-resolved.json"
        if candidate2.exists():
            return candidate2
    return None


def check_actuals_fresh(actuals_path: Path, max_age_days: int = 180) -> bool:
    """Check if actuals market_data is fresh."""
    try:
        with open(actuals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        md = data.get("market_data", {})
        ts = md.get("as_of") or md.get("fetched_at") or ""
        if ts:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - dt
            return age.days < max_age_days
    except Exception:
        pass
    # If no timestamp, assume stale
    return False


def actuals_has_capability(actuals_path: Path, capability: str) -> bool:
    """Check if actuals-resolved.json has data for a given capability."""
    try:
        with open(actuals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False

    # Structured financial statements
    statements = data.get("statements", {})
    if capability in ("income_statement", "balance_sheet", "cash_flow", "revenue_split"):
        return bool(statements.get(capability))

    # Market data
    md = data.get("market_data", {})
    cap_map = {
        "market_quote": ["last_price", "close", "previous_close"],
        "valuation_snapshot": ["pe", "pb", "ps"],
        "valuation_history": ["pe_history"],
        "dividend": ["dividend_yield", "dividend_rate"],
        "market_cap": ["market_cap"],
        "pe": ["pe"],
        "pb": ["pb"],
        "ps": ["ps"],
        "ev_ebitda": ["ev_ebitda"],
        "financial_snapshot": ["revenue", "net_income", "eps"],
    }
    required = cap_map.get(capability, [])
    if not required:
        return False
    return any(md.get(k) is not None for k in required)


def check_mcp_available() -> bool:
    """Quick check if Longbridge MCP tools are available.
    We do a lightweight env check rather than calling an MCP tool
    (which would add latency). The agent confirms MCP at session start.
    """
    # Check for common MCP auth file or env var
    if os.environ.get("LONGBRIDGE_MCP_AVAILABLE"):
        return True
    # Default to True — agent handles actual failure
    return True


def source_supported_market(source: dict, market: str) -> bool:
    """Check if a source supports a given market."""
    markets = source.get("markets", [])
    return market in markets or "*" in markets


# ---------------------------------------------------------------------------
# Main routing logic
# ---------------------------------------------------------------------------

def route(
    capability: str,
    market: str,
    ticker: str,
    skip_sources: list[str] | None = None,
    workspace: Path | None = None,
) -> dict:
    """Resolve the best source chain for a capability+market+ticker.

    Returns:
        dict with:
        - chain: list of {source, tool, params, available, reason}
        - capability, market, ticker
        - matrix_version
        - routing_time_ms
    """
    t0 = time.time()
    skip_sources = skip_sources or []

    ws = workspace or discover_workspace()
    if ws is None:
        return {
            "chain": [{"source": "web_search", "tool": "WebSearch",
                        "params": None, "available": True,
                        "reason": "workspace not found — web search only"}],
            "capability": capability,
            "market": market,
            "ticker": ticker,
            "error": "workspace_not_found",
            "routing_time_ms": 0,
        }

    matrix = load_matrix(ws)
    sources = matrix.get("sources", {})
    chains = matrix.get("chains", {})
    tool_map = matrix.get("tool_map", {})

    # Get chain order for this capability, fall back to "default"
    chain_sources = chains.get(capability, chains.get("default", []))
    if not chain_sources:
        chain_sources = ["web_search"]

    # Filter out skipped sources
    chain_sources = [s for s in chain_sources if s not in skip_sources]

    # Build the resolved chain
    resolved_chain = []
    for source_name in chain_sources:
        src = sources.get(source_name)
        if src is None:
            continue

        available = True
        reason = "ok"
        tool = None
        params = None

        # --- actuals_cache check ---
        if source_name == "actuals_cache":
            if not source_supported_market(src, market):
                available = False
                reason = f"actuals_cache not available for market {market}"
            else:
                actuals_path = find_actuals_path(ws, ticker)
                if actuals_path is None:
                    available = False
                    reason = "actuals-resolved.json not found for this ticker"
                elif not actuals_has_capability(actuals_path, capability):
                    available = False
                    reason = f"actuals has no data for capability '{capability}'"
                else:
                    # For market snapshot caps, also check freshness
                    market_snap_caps = {"market_quote", "valuation_snapshot", "dividend",
                                         "market_cap", "pe", "pb", "ps", "ev_ebitda"}
                    if capability in market_snap_caps:
                        if not check_actuals_fresh(actuals_path):
                            available = False
                            reason = "actuals market_data stale (>180 days)"
                    tool = "Read"
                    params = {"file_path": str(actuals_path)}

        # --- longbridge_mcp check ---
        elif source_name == "longbridge_mcp":
            if not source_supported_market(src, market):
                available = False
                reason = f"Longbridge MCP does not cover market {market}"
            elif not check_mcp_available():
                available = False
                reason = "Longbridge MCP not connected"
            else:
                # Map capability → MCP tool
                mcp_tools = tool_map.get("longbridge_mcp", {})
                tool_name = mcp_tools.get(capability)
                if tool_name is None:
                    available = False
                    reason = f"no Longbridge MCP tool for capability '{capability}'"
                else:
                    tool = tool_name
                    # Build tool params based on tool
                    params = build_mcp_params(capability, tool_name, market, ticker)

        # --- yfinance ---
        elif source_name == "yfinance":
            if not source_supported_market(src, market):
                available = False
                reason = f"yfinance may not cover market {market} well"
            else:
                yf_map = tool_map.get("yfinance", {})
                tool_method = yf_map.get(capability, "yfinance.Ticker")
                tool = "Bash"
                clean_ticker = ticker.split(".")[0] if "." in ticker else ticker
                if market in ("HK", "SH", "SZ"):
                    # Map to yfinance suffix if needed
                    params = {"command": f"python -c \"import yfinance as yf; t=yf.Ticker('{clean_ticker}.{map_yf_suffix(market)}'); print(t.info.get('trailingPE','N/A'))\""}
                else:
                    params = {"command": f"python -c \"import yfinance as yf; import json; t=yf.Ticker('{clean_ticker}'); print(json.dumps(t.info, default=str))\""}

        # --- financial_data_cli ---
        elif source_name == "financial_data_cli":
            if not source_supported_market(src, market):
                available = False
                reason = f"financial-data CLI does not support market {market}"
            else:
                tool = "Skill:financial-data"
                clean_id = ticker.split(".")[0] if "." in ticker else ticker
                params = {"command": f"/financial-data --lite --market {market} --identifier {clean_id}"}

        # --- web_search ---
        elif source_name == "web_search":
            tool = "WebSearch"
            params = {"query": f"{ticker} {capability.replace('_', ' ')} data"}

        resolved_chain.append({
            "source": source_name,
            "tool": tool,
            "params": params,
            "available": available,
            "reason": reason,
        })

    routing_time_ms = int((time.time() - t0) * 1000)

    return {
        "chain": resolved_chain,
        "capability": capability,
        "market": market,
        "ticker": ticker,
        "matrix_version": matrix.get("_meta", {}).get("version", "unknown"),
        "routing_time_ms": routing_time_ms,
    }


def build_mcp_params(capability: str, tool_name: str, market: str, ticker: str) -> dict:
    """Build MCP tool parameters based on capability and ticker format."""
    # Normalize ticker format
    if "." not in ticker:
        if market in ("US",):
            ticker = f"{ticker}.US"
        elif market in ("HK",):
            ticker = f"{ticker}.HK"
        elif market in ("SH",):
            ticker = f"{ticker}.SH"
        elif market in ("SZ",):
            ticker = f"{ticker}.SZ"

    # Tools that use 'symbols' (array)
    multi_symbol_tools = {"mcp__longbridge__quote", "mcp__longbridge__exchange_rate"}
    if tool_name in multi_symbol_tools:
        return {"symbols": [ticker]}

    # Tools that use 'category' + 'market' + date range
    if tool_name == "mcp__longbridge__finance_calendar":
        return {"category": "report", "market": market, "start": "today", "end": "+14d"}

    # Tools that need kind + report
    if tool_name in ("mcp__longbridge__financial_statement", "mcp__longbridge__financial_report"):
        return {"symbol": ticker, "kind": "ALL", "report": "af"}

    # Tools that need report + fiscal year
    if tool_name == "mcp__longbridge__financial_report_snapshot":
        return {"symbol": ticker, "report": "qf"}

    # Market-level tools
    if tool_name in ("mcp__longbridge__market_temperature", "mcp__longbridge__market_status",
                     "mcp__longbridge__trading_session"):
        return {"market": market}

    if tool_name == "mcp__longbridge__top_movers":
        return {"markets": market, "limit": 20}

    # valuation_comparison needs currency
    if tool_name == "mcp__longbridge__valuation_comparison":
        currency_map = {"US": "USD", "HK": "HKD", "SH": "CNY", "SZ": "CNY"}
        return {"symbol": ticker, "currency": currency_map.get(market, "USD")}

    # Default: single symbol param
    return {"symbol": ticker}


def map_yf_suffix(market: str) -> str:
    """Map internal market codes to yfinance ticker suffixes."""
    suffix_map = {
        "HK": "HK",
        "SH": "SS",
        "SZ": "SZ",
        "JP": "T",
        "KR": "KS",
        "TW": "TW",
        "EU": "",  # varies by country
        "SG": "SI",
        "GB": "L",
        "CA": "TO",
        "AU": "AX",
    }
    return suffix_map.get(market, "")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Unified data routing for buy-side research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python .scripts/shared/route.py AAPL.US valuation_snapshot
  python .scripts/shared/route.py 700.HK consensus --skip longbridge_mcp
  python .scripts/shared/route.py TSLA.US market_quote --json
        """,
    )
    parser.add_argument("ticker", help="Ticker with market suffix, e.g. AAPL.US, 700.HK")
    parser.add_argument("capability", help="Capability name, e.g. valuation_snapshot, consensus")
    parser.add_argument("--skip", nargs="*", default=[],
                        dest="skip_sources", help="Sources to skip, e.g. longbridge_mcp")
    parser.add_argument("--workspace", type=Path, default=None,
                        help="Workspace path (auto-discovered if not provided)")
    parser.add_argument("--json", action="store_true", default=True,
                        help="Output JSON (default)")
    args = parser.parse_args()

    # Parse market from ticker
    if "." in args.ticker:
        market = args.ticker.split(".")[-1]
        if market in ("US", "HK", "SH", "SZ", "SG", "CN", "JP", "KR", "TW", "EU"):
            pass
        else:
            market = "US"  # fallback
    else:
        market = "US"

    result = route(
        capability=args.capability,
        market=market,
        ticker=args.ticker,
        skip_sources=args.skip_sources,
        workspace=args.workspace,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
