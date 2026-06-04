#!/usr/bin/env python3
"""actuals-to-appendix — render actuals-resolved.json as sell-side appendix markdown.

Usage:
  python actuals-to-appendix.py <TICKER>              # single company
  python actuals-to-appendix.py --tickers T1,T2,T3    # multi-company peer comparison

Reads existing actuals-resolved.json from workspace cache. Does NOT fetch data.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
            if co_dir.name.lower() == ticker_lower and candidate.is_file():
                return candidate
    return None


def _load_actuals(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _extract_val(field):
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("value")
    if isinstance(field, (int, float)):
        return field
    return None


def _fmt_val(v, scale="m"):
    """Format a numeric value. Default scale = millions."""
    if v is None:
        return "-"
    if not isinstance(v, (int, float)):
        return str(v)[:80]
    if scale == "m":
        return f"{v/1e6:,.0f}"
    if scale == "raw":
        return f"{v:,.1f}"
    return f"{v:,.0f}"


def _fmt_mkt_val(key: str, v) -> str:
    """Format a market_data field value — field-aware formatting.

    Unlike _fmt_val which defaults to millions division, this uses the
    correct unit per field (price→2dp, market_cap→bn/m, ratios→1dp, etc.).
    """
    if v is None:
        return "-"
    if not isinstance(v, (int, float)):
        return str(v)[:80]
    if key == "price":
        return f"{v:,.2f}"
    if key == "market_cap":
        if v >= 1e9:
            return f"{v/1e9:,.1f}bn"
        return f"{v/1e6:,.0f}m"
    if key in ("pe_ttm", "pe_ntm", "pb", "ps_ttm", "ev_ebitda", "ev_sales"):
        return f"{v:,.1f}x"
    if key == "dividend_yield_pct":
        return f"{v:.2f}%"
    if key == "beta":
        return f"{v:.2f}"
    if key == "total_shares":
        return f"{v/1e6:,.0f}m"
    if key == "eps_ttm":
        return f"{v:,.2f}"
    return f"{v:,.1f}"


def _read_fy_periods(data: dict, section: str) -> list[str]:
    """Discover which period keys exist. Dedup fy_y0/latest_fy and sub_N."""
    section_data = data.get(section, {})
    fy_keys = [k for k in ["fy_y2", "fy_y1", "fy_y0"] if k in section_data]
    sub_raw = [k for k in ["sub_0", "sub_1", "sub_2", "sub_3"] if k in section_data]

    # Collect fy period dates for dedup
    fy_dates = set()
    for fk in fy_keys:
        pd = section_data.get(fk, {})
        if isinstance(pd, dict) and pd.get("period"):
            fy_dates.add(pd["period"])

    # Filter sub_keys: skip if same date as a fy key
    sub_keys = []
    for sk in sub_raw:
        sk_pd = section_data.get(sk, {})
        sk_period = sk_pd.get("period", "") if isinstance(sk_pd, dict) else ""
        if sk_period not in fy_dates:
            sub_keys.append(sk)

    # Add latest_fy only if not already covered
    if "latest_fy" in section_data:
        lfy_pd = section_data.get("latest_fy", {})
        lfy_period = lfy_pd.get("period", "") if isinstance(lfy_pd, dict) else ""
        if lfy_period not in fy_dates:
            fy_keys.append("latest_fy")

    # Add latest_quarter if not covered by sub_0 or fy
    if "latest_quarter" in section_data:
        lq_pd = section_data.get("latest_quarter", {})
        lq_period = lq_pd.get("period", "") if isinstance(lq_pd, dict) else ""
        sub_dates = set()
        for sk in sub_keys:
            sk_pd = section_data.get(sk, {})
            sp = sk_pd.get("period", "") if isinstance(sk_pd, dict) else ""
            if sp:
                sub_dates.add(sp)
        if lq_period not in sub_dates and lq_period not in fy_dates:
            sub_keys.append("latest_quarter")

    return fy_keys + sub_keys


def _period_label(data: dict, section: str, key: str) -> str:
    """Get compact human-readable period label."""
    period_data = data.get(section, {}).get(key, {})
    label = period_data.get("period", key) if isinstance(period_data, dict) else key
    if not isinstance(label, str):
        label = str(key)

    # "YYYY-MM-DD" — distinguish FY from sub-period by key prefix
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", label)
    if m:
        y, mo, _ = m.group(1), int(m.group(2)), m.group(3)
        if key.startswith("sub_"):
            # Quarterly: show Q + year
            q = (mo - 1) // 3 + 1
            return f"Q{q} {y}"
        return y

    # Already a period label like "Q1 FY2026", "H1 FY2025"
    return label if len(label) <= 14 else str(key)


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
                    title: str) -> str:
    """Render a multi-period financial statement table."""
    periods = _read_fy_periods(data, section)
    if not periods:
        return ""

    section_data = data.get(section, {})
    rows = []
    for key, label in fields:
        vals = {}
        has_any = False
        for p in periods:
            period_data = section_data.get(p, {})
            v = _extract_val(period_data.get(key))
            vals[p] = v
            if v is not None:
                has_any = True
        if has_any:
            rows.append((label, vals))

    if not rows:
        return ""

    lines = [f"### {title}", ""]
    header = "| Line Item | " + " | ".join(_period_label(data, section, p) for p in periods) + " |"
    sep = "|---|" + "|".join("---:" for _ in periods) + "|"
    lines.extend([header, sep])

    for label, vals in rows:
        cells = [_fmt_val(vals[p]) for p in periods]
        lines.append("| " + label + " | " + " | ".join(cells) + " |")

    lines.append("")
    return "\n".join(lines)


def _render_market_data(data: dict) -> str:
    """Render market data key-value."""
    md = data.get("market_data", {})
    if not md:
        return ""

    lines = ["### Market Data", "", "| Metric | Value | As-of |", "|---|---|---|"]
    for key, label in _MKT_FIELDS:
        v = md.get(key)
        if v is None:
            continue
        detail = ""
        if isinstance(v, dict):
            detail = v.get("source_detail", "")[:60]
            v = v.get("value")
        if v is None:
            continue
        if isinstance(v, (int, float)):
            if key == "dividend_yield_pct":
                v = f"{v:.2f}%"
            elif key == "beta":
                v = f"{v:.2f}"
            elif key == "total_shares":
                v = f"{v/1e6:,.0f}m"
            elif key == "price":
                v = f"{v:,.2f}"
            elif key == "market_cap":
                v = f"{v/1e9:,.1f}bn" if v >= 1e9 else f"{v/1e6:,.0f}m"
            else:
                v = f"{v:,.1f}"
        lines.append(f"| {label} | {v} | {detail} |")
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
        t = s.get("type") or "business_line"
        by_type.setdefault(t, []).append(s)

    for seg_type, items in by_type.items():
        type_label = {"business_line": "Business Line", "geography": "Geography",
                      "end_market": "End Market"}.get(seg_type, seg_type.title())
        lines.append(f"**{type_label}**")
        lines.append("")

        all_periods = set()
        for item in items:
            for p in item.get("periods", []):
                all_periods.add(p)
        period_labels = {}
        for p in sorted(all_periods):
            if p.startswith("fy_"):
                period_labels[p] = "FY" + p[3:]
            elif p.startswith("sub_"):
                period_labels[p] = p[4:].replace("q", "Q").replace("h", "H").replace("_", " ")
            elif p.startswith("q") and "_20" in p:
                # q2_2025 -> Q2 2025
                parts = p.split("_")
                period_labels[p] = parts[0].upper() + " " + parts[1]
            else:
                period_labels[p] = p
        periods = sorted(all_periods)

        if periods:
            header = "| Segment | " + " | ".join(period_labels[p] for p in periods) + " |"
            sep = "|---|" + "|".join("---:" for _ in periods) + "|"
            lines.extend([header, sep])
            for item in items:
                name = item.get("name", "?")
                rev = item.get("revenue", {})
                cells = []
                for p in periods:
                    v = _extract_val(rev.get(p)) if isinstance(rev, dict) else None
                    cells.append(_fmt_val(v))
                lines.append("| " + name + " | " + " | ".join(cells) + " |")
            lines.append("")
        else:
            for item in items:
                name = item.get("name", "?")
                desc = item.get("description", "")[:60]
                lines.append(f"- **{name}**: {desc}")
            lines.append("")

    return "\n".join(lines)


def _render_consensus(data: dict) -> str:
    """Render consensus estimates."""
    cons = data.get("consensus", {})
    if not cons:
        return ""

    lines = ["### Consensus", "", "| Metric | Value |", "|---|---|"]
    for key, label in _CONSENSUS_FIELDS:
        v = _extract_val(cons.get(key))
        if v is not None:
            if key in ("current_year_revenue",):
                lines.append(f"| {label} | {v/1e6:,.0f}m |")
            else:
                lines.append(f"| {label} | {v:,.2f} |")
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

    for key, _ in _MKT_FIELDS:
        v = _extract_val(data.get("market_data", {}).get(key))
        total += 1
        if v is not None:
            filled += 1
        else:
            missing_fields.append(f"market_data.{key}")

    if total == 0:
        return ""

    fill_pct = (filled / total * 100) if total > 0 else 0
    lines = [f"> Source: actuals-resolved.json | Fill: {filled}/{total} ({fill_pct:.0f}%)"]
    if missing_fields and len(missing_fields) <= 10:
        lines.append(f"> Missing: {', '.join(missing_fields)}")
    elif missing_fields:
        lines.append(f"> Missing: {len(missing_fields)} fields ({', '.join(missing_fields[:3])}...)")
    lines.append("")
    return "\n".join(lines)


# ── single ticker ───────────────────────────────────────

def render_single(workspace: Path, ticker: str) -> str:
    actuals_path = _find_actuals(workspace, ticker)
    if not actuals_path:
        return f"\n> Appendix skipped - no actuals-resolved.json found for {ticker}\n"

    d = _load_actuals(actuals_path)
    currency = d.get("currency", "")
    co_name = d.get("company", ticker)
    actual_ticker = d.get("ticker", ticker)

    lines = [f"\n## Appendix: Financial Data - {co_name} ({actual_ticker})", ""]

    unit_note = f" ({currency} m)" if currency else " (m)"

    is_t = _render_section(d, "income_statement", _IS_FIELDS, f"Income Statement{unit_note}")
    if is_t:
        lines.append(is_t)

    bs_t = _render_section(d, "balance_sheet", _BS_FIELDS, f"Balance Sheet{unit_note}")
    if bs_t:
        lines.append(bs_t)

    cf_t = _render_section(d, "cash_flow", _CF_FIELDS, f"Cash Flow{unit_note}")
    if cf_t:
        lines.append(cf_t)

    mkt_t = _render_market_data(d)
    if mkt_t:
        lines.append(mkt_t)

    seg_t = _render_segments(d)
    if seg_t:
        lines.append(seg_t)

    cons_t = _render_consensus(d)
    if cons_t:
        lines.append(cons_t)

    fr_t = _render_fill_rate(d)
    if fr_t:
        lines.append(fr_t)

    return "\n".join(lines)


# ── multi ticker ─────────────────────────────────────────

_KEY_METRICS_FIELDS = [
    ("market_cap", "Market Cap"),
    ("revenue", "Revenue (FY)"),
    ("gross_profit", "Gross Profit"),
    ("ebit", "EBIT"),
    ("net_income", "Net Income"),
]


def render_multi(workspace: Path, tickers: list[str]) -> str:
    lines = ["\n## Appendix: Comparative Financial Data", ""]

    data_map: dict[str, dict] = {}
    for t in tickers:
        p = _find_actuals(workspace, t)
        if p:
            data_map[t] = _load_actuals(p)

    if not data_map:
        return "\n> Appendix skipped - no actuals found for any ticker\n"

    lines.append("### Key Metrics - All Peers")
    lines.append("")
    lines.append("| Ticker | " + " | ".join(lbl for _, lbl in _KEY_METRICS_FIELDS) + " | EV/EBITDA | P/E (TTM) |")
    lines.append("|---|" + "|".join("---:" for _ in _KEY_METRICS_FIELDS) + "|---:| ---:|")

    for t, d in data_map.items():
        cells = []
        for key, _ in _KEY_METRICS_FIELDS:
            if key == "market_cap":
                v = _extract_val(d.get("market_data", {}).get(key))
            else:
                is_fy = d.get("income_statement", {}).get("latest_fy", {})
                v = _extract_val(is_fy.get(key))
            cells.append(_fmt_val(v) if v is not None else "-")

        ev_ebitda = _extract_val(d.get("market_data", {}).get("ev_ebitda"))
        pe_ttm = _extract_val(d.get("market_data", {}).get("pe_ttm"))
        cells.append(f"{ev_ebitda:,.1f}x" if ev_ebitda else "-")
        cells.append(f"{pe_ttm:,.1f}x" if pe_ttm else "-")
        lines.append("| " + t + " | " + " | ".join(cells) + " |")

    lines.append("")

    for t, d in data_map.items():
        currency = d.get("currency", "")
        unit_note = f" ({currency} m)" if currency else " (m)"
        is_t = _render_section(d, "income_statement", _IS_FIELDS, f"Income Statement - {t}{unit_note}")
        if is_t:
            lines.append(is_t)

    lines.append("### Market Data - All")
    lines.append("")
    mkt_header = "| Ticker | " + " | ".join(lbl for _, lbl in _MKT_FIELDS[:8]) + " |"
    mkt_sep = "|---|" + "|".join("---:" for _ in range(8)) + "|"
    lines.extend([mkt_header, mkt_sep])

    for t, d in data_map.items():
        md = d.get("market_data", {})
        cells = []
        for key, _ in _MKT_FIELDS[:8]:
            v = _extract_val(md.get(key))
            cells.append(_fmt_mkt_val(key, v) if v is not None else "-")
        lines.append("| " + t + " | " + " | ".join(cells) + " |")
    lines.append("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Render actuals-resolved.json as appendix markdown")
    parser.add_argument("ticker", nargs="?", help="Single ticker (e.g. MYCR.ST)")
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
