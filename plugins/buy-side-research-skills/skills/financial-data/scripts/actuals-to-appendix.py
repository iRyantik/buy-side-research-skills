#!/usr/bin/env python3
"""actuals-to-appendix — render actuals-resolved.json as sell-side appendix markdown.

Usage:
  # Single ticker
  python actuals-to-appendix.py BESI.NA

  # Multi ticker (peer comparison)
  python actuals-to-appendix.py --tickers BESI.NA,ASML.NA,MYCR.ST

Reads existing actuals-resolved.json from workspace cache, renders human-readable
financial tables. Does NOT fetch data — actuals must already exist.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ── helpers ────────────────────────────────────────────

def _find_actuals(workspace: Path, ticker: str) -> Path | None:
    """Walk industry/ tree to find actuals-resolved.json for a ticker."""
    industry_root = workspace / "industry"
    if not industry_root.is_dir():
        return None
    ticker_lower = ticker.lower()
    for industry_dir in industry_root.iterdir():
        if not industry_dir.is_dir():
            continue
        companies_dir = industry_dir / "companies"
        if not companies_dir.is_dir():
            continue
        for co_dir in companies_dir.iterdir():
            if not co_dir.is_dir():
                continue
            candidate = co_dir / "_cache" / "financial-data" / "internal" / "actuals-resolved.json"
            if candidate.is_file():
                try:
                    with open(candidate, encoding="utf-8") as f:
                        d = json.load(f)
                    if d.get("ticker", "").lower() == ticker_lower:
                        return candidate
                except Exception:
                    continue
            # Also check by directory name
            if co_dir.name.lower() == ticker_lower:
                return candidate if candidate.is_file() else None
    return None


def _load_actuals(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _fmt_val(v, currency="") -> str:
    """Format a numeric value with magnitude scaling."""
    if v is None:
        return "—"
    if isinstance(v, dict):
        v = v.get("value", v)
    if not isinstance(v, (int, float)):
        return str(v)[:80]
    absv = abs(v)
    if absv >= 1e9:
        return f"{v/1e9:,.1f}"
    if absv >= 1e6:
        return f"{v/1e6:,.1f}"
    if absv >= 1e4:
        return f"{v/1e3:,.0f}"
    if absv >= 1:
        return f"{v:,.1f}"
    return f"{v:.2f}"


def _extract_val(field) -> float | None:
    """Extract numeric value from {value, source_layer, source_detail} or raw number."""
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("value")
    if isinstance(field, (int, float)):
        return field
    return None


def _read_fy_periods(data: dict, section: str) -> list[str]:
    """Discover which period keys exist for a section. Returns ordered list."""
    section_data = data.get(section, {})
    # 3Y mode: fy_y2, fy_y1, fy_y0 + sub_0, sub_1, ...
    fy_keys = [k for k in ["fy_y2", "fy_y1", "fy_y0"] if k in section_data]
    sub_keys = [k for k in ["sub_0", "sub_1", "sub_2", "sub_3"] if k in section_data]
    # Latest mode: latest_fy, latest_quarter (always present)
    if "latest_fy" in section_data and "latest_fy" not in fy_keys:
        fy_keys.append("latest_fy")
    if "latest_quarter" in section_data and "latest_quarter" not in sub_keys:
        sub_keys.append("latest_quarter")
    # Sort Fy chronologically, sub chronologically
    return fy_keys + sub_keys


def _period_label(data: dict, section: str, key: str) -> str:
    """Get human-readable period label."""
    period_data = data.get(section, {}).get(key, {})
    if isinstance(period_data, dict):
        label = period_data.get("period", key)
        # Map internal keys to labels
        key_labels = {
            "fy_y2": "FY-2", "fy_y1": "FY-1", "fy_y0": "FY0",
            "sub_0": "Q/H0", "sub_1": "Q/H1", "sub_2": "Q/H2", "sub_3": "Q/H3",
            "latest_fy": "FY", "latest_quarter": "Q/H",
        }
        if key in key_labels:
            return f"{key_labels[key]} ({label})" if label else key_labels[key]
        return str(label)
    return key


def _currency_unit(currency: str) -> str:
    """Scale unit based on typical magnitudes."""
    return currency or ""


# ── table renderers ─────────────────────────────────────

_IS_FIELDS = [
    ("revenue", "Revenue"),
    ("cost_of_revenue", "Cost of Revenue"),
    ("gross_profit", "Gross Profit"),
    ("sg_and_a", "SG&A"),
    ("r_and_d", "R&D"),
    ("operating_income", "Operating Income"),
    ("ebit", "EBIT"),
    ("interest_expense", "Interest Expense"),
    ("income_tax", "Income Tax"),
    ("net_income", "Net Income"),
]

_BS_FIELDS = [
    ("cash", "Cash & Equivalents"),
    ("accounts_receivable", "Accounts Receivable"),
    ("inventory", "Inventory"),
    ("total_assets", "Total Assets"),
    ("total_equity_parent", "Total Equity (Parent)"),
    ("goodwill", "Goodwill"),
    ("long_term_debt", "Long-Term Debt"),
    ("current_liabilities", "Current Liabilities"),
    ("short_term_debt", "Short-Term Debt"),
]

_CF_FIELDS = [
    ("operating_cf", "Operating Cash Flow"),
    ("capex", "CapEx"),
    ("d_and_a", "D&A"),
    ("dividends_paid", "Dividends Paid"),
    ("share_buybacks", "Share Buybacks"),
]

_MKT_FIELDS = [
    ("price", "Share Price"),
    ("market_cap", "Market Cap"),
    ("pe_ttm", "P/E (TTM)"),
    ("pe_ntm", "P/E (NTM)"),
    ("pb", "P/B"),
    ("ps_ttm", "P/S (TTM)"),
    ("ev_ebitda", "EV/EBITDA"),
    ("ev_sales", "EV/Sales"),
    ("dividend_yield_pct", "Dividend Yield %"),
    ("beta", "Beta"),
    ("eps_ttm", "EPS (TTM)"),
    ("total_shares", "Shares Outstanding"),
]

_CONSENSUS_FIELDS = [
    ("current_year_eps", "EPS (FY0E)"),
    ("next_year_eps", "EPS (FY1E)"),
    ("current_year_revenue", "Revenue (FY0E)"),
]


def _render_section(data: dict, section: str, fields: list[tuple[str, str]],
                    currency: str, table_title: str) -> str:
    """Render a multi-period financial statement table."""
    periods = _read_fy_periods(data, section)
    if not periods:
        return ""

    # Collect field values per period
    section_data = data.get(section, {})
    rows = []
    for key, label in fields:
        vals = {}
        has_any = False
        for p in periods:
            period_data = section_data.get(p, {})
            field = period_data.get(key)
            v = _extract_val(field)
            vals[p] = v
            if v is not None:
                has_any = True
        if has_any:
            rows.append((label, vals))

    if not rows:
        return ""

    lines = [f"### {table_title} ({currency + ' m' if currency else 'm'})", ""]
    # Header
    header = "| Line Item | " + " | ".join(_period_label(data, section, p) for p in periods) + " |"
    sep = "|---|" + "|".join("---:" for _ in periods) + "|"
    lines.extend([header, sep])

    for label, vals in rows:
        cells = [_fmt_val(vals[p]) for p in periods]
        lines.append("| " + label + " | " + " | ".join(cells) + " |")

    lines.append("")
    return "\n".join(lines)


def _render_market_data(data: dict, currency: str) -> str:
    """Render market data key-value."""
    md = data.get("market_data", {})
    if not md:
        return ""

    lines = ["### Market Data", "", "| Metric | Value | As-of |", "|---|---|---|"]
    for key, label in _MKT_FIELDS:
        v = md.get(key)
        if v is None:
            continue
        if isinstance(v, dict):
            val = v.get("value", "—")
            detail = v.get("source_detail", "")[:60]
        else:
            val = v
            detail = ""
        if val is None:
            continue
        if isinstance(val, float):
            if key in ("dividend_yield_pct",):
                val = f"{val:.2f}%"
            elif key in ("beta",):
                val = f"{val:.2f}"
            elif key in ("total_shares",):
                val = f"{val:,.0f}"
            elif key == "price":
                val = f"{val:,.2f}"
            else:
                val = f"{val:,.1f}" if val < 1e12 else f"{val/1e9:,.1f} bn"
        lines.append(f"| {label} | {val} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _render_segments(data: dict) -> str:
    """Render segment breakdown tables."""
    segments = data.get("segments", {}).get("segments", [])
    if not segments:
        return ""

    lines = ["### Segments", ""]
    by_type: dict[str, list] = {}
    for s in segments:
        t = s.get("type", "unknown")
        by_type.setdefault(t, []).append(s)

    for seg_type, items in by_type.items():
        type_label = {"business_line": "Business Line", "geography": "Geography",
                      "end_market": "End Market"}.get(seg_type, seg_type.title())
        lines.append(f"**{type_label}**")
        lines.append("")

        # Collect periods from segments
        all_periods = set()
        for item in items:
            for p in item.get("periods", []):
                all_periods.add(p)
        periods = sorted(all_periods)

        if periods:
            header = "| Segment | " + " | ".join(periods) + " |"
            sep = "|---|" + "|".join("---:" for _ in periods) + "|"
            lines.extend([header, sep])
            for item in items:
                name = item.get("name", "?")
                rev = item.get("revenue", {})
                if isinstance(rev, dict):
                    cells = [_fmt_val(rev.get(p)) for p in periods]
                else:
                    cells = [_fmt_val(rev) if p == periods[0] else "—" for p in periods]
                lines.append("| " + name + " | " + " | ".join(cells) + " |")
            lines.append("")
        else:
            for item in items:
                name = item.get("name", "?")
                rev = item.get("revenue", "—")
                pct = item.get("pct_of_total", "—")
                desc = item.get("description", "")[:60]
                lines.append(f"- **{name}**: Revenue {rev}, {pct}% of total. {desc}")
            lines.append("")

    return "\n".join(lines)


def _render_consensus(data: dict) -> str:
    """Render consensus estimates."""
    cons = data.get("consensus", {})
    if not cons:
        return ""

    lines = ["### Consensus", "", "| Metric | Value |", "|---|---|"]
    for key, label in _CONSENSUS_FIELDS:
        v = cons.get(key)
        if v is None:
            continue
        if isinstance(v, dict):
            val = v.get("value")
        else:
            val = v
        if val is not None:
            lines.append(f"| {label} | {val:,.2f} |")
    lines.append("")
    return "\n".join(lines)


def _render_fill_rate(data: dict) -> str:
    """Render fill rate summary."""
    total = 0
    filled = 0
    missing_fields = []

    for section in ["income_statement", "balance_sheet", "cash_flow"]:
        section_data = data.get(section, {})
        periods = _read_fy_periods(data, section)
        for p in periods:
            pdata = section_data.get(p, {})
            for key in pdata:
                if key == "period":
                    continue
                total += 1
                v = _extract_val(pdata.get(key))
                if v is not None:
                    filled += 1
                else:
                    missing_fields.append(f"{section}.{p}.{key}")

    for key in _MKT_FIELDS:
        v = _extract_val(data.get("market_data", {}).get(key[0]))
        total += 1
        if v is not None:
            filled += 1
        else:
            missing_fields.append(f"market_data.{key[0]}")

    if total == 0:
        return ""

    fill_pct = (filled / total * 100) if total > 0 else 0
    lines = [f"> Source: actuals-resolved.json | Fill: {filled}/{total} ({fill_pct:.0f}%)"]
    if missing_fields and len(missing_fields) <= 10:
        lines.append(f"> Missing: {', '.join(missing_fields)}")
    elif missing_fields:
        lines.append(f"> Missing: {len(missing_fields)} fields ({missing_fields[0]}, {missing_fields[1]}, ...)")
    lines.append("")
    return "\n".join(lines)


# ── single ticker appendix ──────────────────────────────

def render_single(workspace: Path, ticker: str) -> str:
    actuals_path = _find_actuals(workspace, ticker)
    if not actuals_path:
        return f"\n> ⚠ Appendix skipped — no actuals-resolved.json found for {ticker}\n"

    d = _load_actuals(actuals_path)
    currency = d.get("currency", "")
    unit = _currency_unit(currency)
    co_name = d.get("company", ticker)
    actual_ticker = d.get("ticker", ticker)

    lines = [
        f"\n## Appendix: Financial Data — {co_name} ({actual_ticker})",
        "",
    ]

    # Income Statement
    is_t = _render_section(d, "income_statement", _IS_FIELDS, unit, f"Income Statement ({currency} m)")
    if is_t:
        lines.append(is_t)

    # Balance Sheet
    bs_t = _render_section(d, "balance_sheet", _BS_FIELDS, unit, f"Balance Sheet ({currency} m)")
    if bs_t:
        lines.append(bs_t)

    # Cash Flow
    cf_t = _render_section(d, "cash_flow", _CF_FIELDS, unit, f"Cash Flow ({currency} m)")
    if cf_t:
        lines.append(cf_t)

    # Market Data
    mkt_t = _render_market_data(d, currency)
    if mkt_t:
        lines.append(mkt_t)

    # Segments
    seg_t = _render_segments(d)
    if seg_t:
        lines.append(seg_t)

    # Consensus
    cons_t = _render_consensus(d)
    if cons_t:
        lines.append(cons_t)

    # Fill Rate
    fr_t = _render_fill_rate(d)
    if fr_t:
        lines.append(fr_t)

    return "\n".join(lines)


# ── multi ticker appendix ───────────────────────────────

_KEY_METRICS_FIELDS = [
    ("market_cap", "Market Cap"),
    ("revenue", "Revenue (FY)"),
    ("gross_profit", "Gross Profit"),
    ("ebit", "EBIT"),
    ("net_income", "Net Income"),
]


def render_multi(workspace: Path, tickers: list[str]) -> str:
    lines = ["\n## Appendix: Comparative Financial Data", ""]

    # Collect all ticker data
    data_map: dict[str, dict] = {}
    for t in tickers:
        p = _find_actuals(workspace, t)
        if p:
            data_map[t] = _load_actuals(p)

    if not data_map:
        return "\n> ⚠ Appendix skipped — no actuals found for any ticker\n"

    # ── Key Metrics cross-comparison ──
    lines.append("### Key Metrics — All Peers")
    lines.append("")
    lines.append("| Ticker | " + " | ".join(lbl for _, lbl in _KEY_METRICS_FIELDS) + " | EV/EBITDA | P/E (TTM) |")
    lines.append("|---|" + "|".join("---:" for _ in _KEY_METRICS_FIELDS) + "|---:| ---:|")

    for t, d in data_map.items():
        cells = []
        for key, _ in _KEY_METRICS_FIELDS:
            if key == "market_cap":
                v = _extract_val(d.get("market_data", {}).get(key))
            else:
                # revenue/ebit/net_income from latest_fy
                is_fy = d.get("income_statement", {}).get("latest_fy", {})
                v = _extract_val(is_fy.get(key)) if key != "market_cap" else None
            cells.append(_fmt_val(v) if v is not None else "—")

        ev_ebitda = _extract_val(d.get("market_data", {}).get("ev_ebitda"))
        pe_ttm = _extract_val(d.get("market_data", {}).get("pe_ttm"))
        cells.append(_fmt_val(ev_ebitda) if ev_ebitda else "—")
        cells.append(_fmt_val(pe_ttm) if pe_ttm else "—")
        lines.append("| " + t + " | " + " | ".join(cells) + " |")

    lines.append("")

    # ── Per-ticker IS ──
    for t, d in data_map.items():
        currency = d.get("currency", "")
        is_t = _render_section(d, "income_statement", _IS_FIELDS, currency,
                               f"Income Statement — {t} ({currency} m)")
        if is_t:
            lines.append(is_t)

    # ── Market Data All ──
    lines.append("### Market Data — All")
    lines.append("")
    mkt_header = "| Ticker | " + " | ".join(lbl for _, lbl in _MKT_FIELDS[:8]) + " |"
    mkt_sep = "|---|" + "|".join("---:" for _ in range(8)) + "|"
    lines.extend([mkt_header, mkt_sep])

    for t, d in data_map.items():
        md = d.get("market_data", {})
        cells = []
        for key, _ in _MKT_FIELDS[:8]:
            v = _extract_val(md.get(key))
            cells.append(_fmt_val(v) if v is not None else "—")
        lines.append("| " + t + " | " + " | ".join(cells) + " |")
    lines.append("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Render actuals-resolved.json as appendix markdown")
    parser.add_argument("ticker", nargs="?", help="Single ticker (e.g. BESI.NA)")
    parser.add_argument("--tickers", help="Comma-separated multi-ticker (e.g. BESI.NA,ASML.NA)")
    parser.add_argument("--workspace", default=None, help="Workspace root path (default: cwd)")
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
