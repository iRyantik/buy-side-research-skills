#!/usr/bin/env python3
"""actuals-to-appendix — render actuals-resolved.json as sell-side appendix markdown.

Usage:
  python actuals-to-appendix.py <TICKER>              # single company
  python actuals-to-appendix.py --tickers T1,T2,T3    # multi-company peer comparison

Reads actuals-resolved.json from workspace cache. Renders ALL available fields.
Field rendering order from .references/policy/statement-line-items.md registry.
"""
from __future__ import annotations

import argparse, json, re, sys
from pathlib import Path


# ── Concept mapping — uses financial_data.py's _map_concept + _FIELD_ALIASES ──

_MAP_CONCEPT = None

def _display_name(row: dict) -> str:
    """Get best display name using existing concept mapping infrastructure."""
    global _MAP_CONCEPT
    if _MAP_CONCEPT is None:
        try:
            import importlib.util, sys
            fd_path = Path(__file__).resolve().parent / "financial_data.py"
            spec = importlib.util.spec_from_file_location("financial_data", fd_path)
            fd = importlib.util.module_from_spec(spec)
            sys.modules["financial_data"] = fd
            spec.loader.exec_module(fd)
            _MAP_CONCEPT = fd._map_concept
            _CONCEPT_MAP = fd._load_concept_map()
        except Exception:
            _MAP_CONCEPT = lambda x, m=None: x

    concept = (row.get("concept") or "").strip()
    label = (row.get("label") or "").strip()

    # Try concept via full mapping
    std = _MAP_CONCEPT(concept) if concept else ""
    if std and std != concept and not std.startswith("is-") and not std.startswith("bs-") and not std.startswith("cf-"):
        return std.replace("_", " ").title()
    # Try label via full mapping
    if label:
        std = _MAP_CONCEPT(label)
        if std and std != label and not std.startswith("is-") and not std.startswith("bs-") and not std.startswith("cf-"):
            return std.replace("_", " ").title()
    # Fallback: snake_case concept
    if concept and concept != label:
        return concept.replace("_", " ").title()
    if label:
        return label
    return (row.get("concept") or "?")

# ── Sort hint: known concepts appear first ─────────────────

_KNOWN_CONCEPTS = {
    "revenue", "cogs", "gross_profit", "sg_and_a", "r_and_d",
    "operating_income", "ebit", "ebitda", "pretax_income", "income_tax",
    "net_income", "net_income_parent", "eps_basic", "eps_diluted", "dps",
    "cash", "receivables", "inventories", "current_assets", "ppe",
    "goodwill", "intangible_assets", "total_assets",
    "payables", "short_term_debt", "long_term_debt", "total_debt",
    "current_liabilities", "total_liabilities",
    "total_equity", "total_equity_parent",
    "operating_cf", "investing_cf", "financing_cf", "capex", "depreciation",
    "amortization", "dividends_paid", "buybacks",
}


# ── Helpers ─────────────────────────────────────────────────

def _find_actuals(workspace: Path, ticker: str) -> Path | None:
    """Walk industry/ tree to find actuals-resolved.json for a ticker."""
    industry_root = workspace / "industry"
    if not industry_root.is_dir():
        return None
    ticker_lower = ticker.lower().replace(".", "").replace("-", "")
    for industry_dir in industry_root.iterdir():
        if not industry_dir.is_dir():
            continue
        companies_dir = industry_dir / "companies"
        if not companies_dir.is_dir():
            continue
        for co_dir in companies_dir.iterdir():
            if not co_dir.is_dir():
                continue
            actuals_path = co_dir / ".cache" / "financial-data" / "actuals-resolved.json"
            if not actuals_path.is_file():
                continue
            try:
                d = json.loads(actuals_path.read_text(encoding="utf-8"))
                stored = (d.get("identity", {}).get("ticker", "") or d.get("ticker", "")).lower()
                if stored.replace(".", "").replace("-", "") == ticker_lower:
                    return actuals_path
                if ticker_lower in co_dir.name.lower().replace(".", "").replace("-", ""):
                    return actuals_path
            except Exception:
                continue
    return None


def _discover_periods(statements: dict) -> list[str]:
    """Discover all unique period labels across all statements."""
    periods = set()
    for stmt_name in ["income_statement", "balance_sheet", "cash_flow"]:
        for row in statements.get(stmt_name, []):
            for p in (row.get("values") or {}).keys():
                periods.add(str(p))
    # Sort: FY first (descending), then Q/H (descending)
    def _sort_key(p):
        m = re.match(r'(?:FY)?(\d{4})', p)
        year = int(m.group(1)) if m else 0
        if p.startswith("FY") or re.match(r'^\d{4}$', p):
            return (0, -year)
        if "Q1" in p or "H1" in p:
            return (1, -year, 1)
        if "Q2" in p:
            return (1, -year, 2)
        if "Q3" in p:
            return (1, -year, 3)
        if "Q4" in p or "H2" in p:
            return (1, -year, 4)
        return (2, -year)
    return sorted(periods, key=_sort_key)


def _format_value(v, unit_hint: str = "") -> str:
    """Format a numeric value for appendix display."""
    if v is None:
        return "-"
    if isinstance(v, str):
        return v[:60]
    if isinstance(v, float):
        if abs(v) < 1 and v != 0:
            return f"{v:.4f}"
        if abs(v) < 1000:
            return f"{v:,.1f}"
        return f"{v:,.0f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def _short_period(p: str) -> str:
    """Compact period label for table header."""
    return p.replace("FY", "").strip() if len(p) <= 10 else p[:10]


# ── Renderers ───────────────────────────────────────────────

def _render_statement(statements: dict, stmt_name: str, title: str, periods: list[str]) -> str:
    """Render ALL rows from actuals — no filtering. Sort: known concepts first, then alphabetical."""
    rows = statements.get(stmt_name, [])
    if not rows:
        return ""

    # Separate known from unknown, build display rows
    known_rows = []
    unknown_rows = []
    for row in rows:
        concept = row.get("concept", "")
        display = _display_name(row)
        values = {str(k): v for k, v in (row.get("values") or {}).items()}
        if not values:
            continue
        cells = [_format_value(values.get(p)) for p in periods]
        if concept in _KNOWN_CONCEPTS:
            known_rows.append((concept, display, cells))
        else:
            unknown_rows.append((concept, display, cells))

    # Sort: known by concept name, unknown alphabetically by concept
    known_rows.sort(key=lambda x: x[0])
    unknown_rows.sort(key=lambda x: x[0])
    all_rows = known_rows + unknown_rows

    # Dedup: same display name → keep first
    seen = set()
    deduped = []
    for concept, display, cells in all_rows:
        if display not in seen:
            seen.add(display)
            deduped.append((concept, display, cells))
    all_rows = deduped

    if not all_rows:
        return ""

    lines = [f"### {title}", ""]
    header = "| Line Item | " + " | ".join(_short_period(p) for p in periods) + " |"
    sep = "|---|" + "|".join("---:" for _ in periods) + "|"
    lines.extend([header, sep])

    for concept, display, cells in all_rows:
        lines.append("| " + display + " | " + " | ".join(cells) + " |")

    lines.append("")
    return "\n".join(lines)


def _render_segments(statements: dict, periods: list[str]) -> str:
    """Render revenue_split as segment table."""
    segs = statements.get("revenue_split", [])
    if not segs:
        return ""

    lines = ["### Segments", ""]

    # Revenue table
    seg_periods = set()
    for seg in segs:
        for p in (seg.get("revenue") or {}).keys():
            seg_periods.add(str(p))
    seg_periods_sorted = sorted(seg_periods, reverse=True)

    if seg_periods_sorted:
        lines.append("**Revenue by Segment**")
        lines.append("")
        header = "| Segment | Type | " + " | ".join(_short_period(p) for p in seg_periods_sorted) + " |"
        sep = "|---:|---|" + "|".join("---:" for _ in seg_periods_sorted) + "|"
        lines.extend([header, sep])
        for seg in segs:
            name = seg.get("segment", seg.get("label_ja", seg.get("label_ko", "?")))
            stype = seg.get("type", "business")
            rev = seg.get("revenue", {})
            cells = [_format_value(rev.get(p)) for p in seg_periods_sorted]
            lines.append(f"| {name} | {stype} | " + " | ".join(cells) + " |")
        lines.append("")

    # Operating profit table (if available)
    has_op = any(seg.get("operating_profit") or seg.get("core_op") or seg.get("ebit")
                 for seg in segs)
    if has_op:
        op_key = None
        for seg in segs:
            if seg.get("operating_profit"):
                op_key = "operating_profit"; break
            if seg.get("core_op"):
                op_key = "core_op"; break
            if seg.get("ebit"):
                op_key = "ebit"; break

        op_periods = set()
        for seg in segs:
            for p in (seg.get(op_key) or {}).keys():
                op_periods.add(str(p))
        op_periods_sorted = sorted(op_periods, reverse=True)

        lines.append(f"**Segment {op_key.replace('_', ' ').title()}**")
        lines.append("")
        header = "| Segment | " + " | ".join(_short_period(p) for p in op_periods_sorted) + " |"
        sep = "|---:|---:|" + "|".join("---:" for _ in range(len(op_periods_sorted)-1))
        lines.extend([header, sep])
        for seg in segs:
            name = seg.get("segment", "?")
            op = seg.get(op_key, {})
            cells = [_format_value(op.get(p)) for p in op_periods_sorted]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        lines.append("")

    return "\n".join(lines)


def _render_market_data(data: dict) -> str:
    """Render market data key-value pairs."""
    md = data.get("market_data", {})
    if not md:
        return ""

    fields = [
        ("price", "Share Price"), ("market_cap", "Market Cap"),
        ("pe_ttm", "P/E (TTM)"), ("pe_ntm", "P/E (NTM)"),
        ("pb", "P/B"), ("ps_ttm", "P/S (TTM)"),
        ("ev_ebitda", "EV/EBITDA"), ("ev_sales", "EV/Sales"),
        ("dividend_yield_pct", "Dividend Yield"), ("beta", "Beta"),
    ]

    lines = ["### Market Data", ""]
    for key, label in fields:
        v = md.get(key)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            if key == "price":
                v = f"{v:,.2f}"
            elif key == "market_cap":
                v = f"{v/1e9:,.1f}bn" if abs(v) >= 1e9 else f"{v/1e6:,.0f}m"
            elif "yield" in key:
                v = f"{v:.2f}%"
            elif key == "beta":
                v = f"{v:.2f}"
            else:
                v = f"{v:,.1f}x"
        lines.append(f"- **{label}**: {v}")
    lines.append("")
    return "\n".join(lines)


def _render_commentary(data: dict) -> str:
    """Render commentary and outlook if present."""
    lines = []
    commentary = data.get("commentary", "")
    if commentary and isinstance(commentary, str) and len(commentary) > 5:
        lines.append("### Management Commentary")
        lines.append("")
        lines.append(commentary)
        lines.append("")

    outlook = data.get("outlook", {})
    if outlook and isinstance(outlook, dict):
        lines.append("### Outlook / Guidance")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(outlook, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


# ── Single ticker ───────────────────────────────────────────

def render_single(workspace: Path, ticker: str) -> str:
    actuals_path = _find_actuals(workspace, ticker)
    if not actuals_path:
        return f"\n> Appendix skipped — no actuals-resolved.json found for {ticker}\n"

    d = json.loads(actuals_path.read_text(encoding="utf-8"))
    stmts = d.get("statements", {})
    identity = d.get("identity", {})
    co_name = identity.get("name_en", ticker)
    actual_ticker = identity.get("ticker", ticker)
    currency = d.get("market_data", {}).get("currency", "")

    periods = _discover_periods(stmts)
    if not periods:
        return f"\n> Appendix skipped — no period data in actuals for {ticker}\n"

    lines = [f"\n## Appendix: Financial Data — {co_name} ({actual_ticker})", ""]
    unit_note = f" ({currency})" if currency else ""

    # Segments first — most important for quickread
    seg_t = _render_segments(stmts, periods)
    if seg_t:
        lines.append(seg_t)

    # Income Statement
    is_t = _render_statement(stmts, "income_statement",
                             f"Income Statement{unit_note}", periods)
    if is_t:
        lines.append(is_t)

    # Balance Sheet
    bs_t = _render_statement(stmts, "balance_sheet",
                             f"Balance Sheet{unit_note}", periods)
    if bs_t:
        lines.append(bs_t)

    # Cash Flow
    cf_t = _render_statement(stmts, "cash_flow",
                             f"Cash Flow{unit_note}", periods)
    if cf_t:
        lines.append(cf_t)

    # Market Data
    mkt_t = _render_market_data(d)
    if mkt_t:
        lines.append(mkt_t)

    # Commentary & Outlook
    comm_t = _render_commentary(d)
    if comm_t:
        lines.append(comm_t)

    return "\n".join(lines)


# ── Multi ticker ────────────────────────────────────────────

_PEER_KEY_METRICS = [
    ("market_cap", "Market Cap"),
    ("revenue", "Revenue"),
    ("gross_profit", "Gross Profit"),
    ("operating_income", "EBIT"),
    ("net_income", "Net Income"),
]


def render_multi(workspace: Path, tickers: list[str]) -> str:
    data_map = {}
    for t in tickers:
        p = _find_actuals(workspace, t)
        if p:
            data_map[t] = json.loads(p.read_text(encoding="utf-8"))

    if not data_map:
        return "\n> Appendix skipped — no actuals found for any ticker\n"

    lines = ["\n## Appendix: Comparative Financial Data", ""]

    # Key metrics table
    lines.append("### Key Metrics — All Peers")
    lines.append("")
    headers = ["Ticker"] + [lbl for _, lbl in _PEER_KEY_METRICS] + ["EV/EBITDA", "P/E (TTM)"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|---|" + "|".join("---:" for _ in range(len(headers)-1)) + "|")

    for t, d in data_map.items():
        cells = []
        md = d.get("market_data", {})
        is_rows = d.get("statements", {}).get("income_statement", [])

        for key, _ in _PEER_KEY_METRICS:
            if key == "market_cap":
                v = md.get(key)
                cells.append(f"{v/1e9:,.1f}bn" if v and abs(v) >= 1e9 else f"{v/1e6:,.0f}m" if v else "-")
            else:
                # Find the concept row and get the latest FY value
                v = None
                for row in is_rows:
                    if row.get("concept") == key:
                        vals = row.get("values", {})
                        # Take the latest FY period
                        fy_keys = sorted([k for k in vals if "FY" in str(k) or re.match(r'^\d{4}$', str(k))], reverse=True)
                        if fy_keys:
                            v = vals[fy_keys[0]]
                        elif vals:
                            v = list(vals.values())[-1]
                        break
                cells.append(_format_value(v))

        ev_ebitda = md.get("ev_ebitda")
        pe_ttm = md.get("pe_ttm")
        cells.append(f"{ev_ebitda:,.1f}x" if ev_ebitda else "-")
        cells.append(f"{pe_ttm:,.1f}x" if pe_ttm else "-")
        lines.append("| " + t + " | " + " | ".join(cells) + " |")

    lines.append("")

    # Individual statements
    for t, d in data_map.items():
        stmts = d.get("statements", {})
        currency = d.get("market_data", {}).get("currency", "")
        unit_note = f" ({currency})" if currency else ""
        periods = _discover_periods(stmts)

        seg_t = _render_segments(stmts, periods)
        if seg_t:
            lines.append(seg_t)

        is_t = _render_statement(stmts, "income_statement",
                                 f"Income Statement — {t}{unit_note}", periods)
        if is_t:
            lines.append(is_t)

        bs_t = _render_statement(stmts, "balance_sheet",
                                 f"Balance Sheet — {t}{unit_note}", periods)
        if bs_t:
            lines.append(bs_t)

        cf_t = _render_statement(stmts, "cash_flow",
                                 f"Cash Flow — {t}{unit_note}", periods)
        if cf_t:
            lines.append(cf_t)

    # Market data comparison
    mkt_fields = [
        ("price", "Price"), ("pe_ntm", "P/E NTM"), ("pb", "P/B"),
        ("ev_ebitda", "EV/EBITDA"), ("dividend_yield_pct", "Div Yield"),
    ]
    lines.append("### Market Data — All")
    lines.append("")
    lines.append("| Ticker | " + " | ".join(lbl for _, lbl in mkt_fields) + " |")
    lines.append("|---|" + "|".join("---:" for _ in mkt_fields) + "|")
    for t, d in data_map.items():
        md = d.get("market_data", {})
        cells = []
        for key, _ in mkt_fields:
            v = md.get(key)
            if v is None:
                cells.append("-")
            elif key == "price":
                cells.append(f"{v:,.2f}")
            elif key == "dividend_yield_pct":
                cells.append(f"{v:.2f}%")
            else:
                cells.append(f"{v:,.1f}x" if isinstance(v, (int, float)) else str(v))
        lines.append("| " + t + " | " + " | ".join(cells) + " |")
    lines.append("")

    # Commentary & Outlook (first ticker only)
    first = list(data_map.values())[0] if data_map else {}
    comm_t = _render_commentary(first)
    if comm_t:
        lines.append(comm_t)

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Render actuals-resolved.json as appendix markdown")
    parser.add_argument("ticker", nargs="?", help="Single ticker (e.g. MYCR.ST)")
    parser.add_argument("--tickers", help="Comma-separated multi-ticker (e.g. 4183.T,2327.TW)")
    parser.add_argument("--workspace", help="Workspace root path (default: cwd)")
    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else Path.cwd()

    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
        if args.ticker:
            tickers.insert(0, args.ticker.strip())
        print(render_multi(workspace, tickers))
    elif args.ticker:
        print(render_single(workspace, args.ticker.strip()))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
