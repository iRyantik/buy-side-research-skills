"""估值纯函数：FMP 数据 → 日报估值表行。

三口径：
- **TTM**（trailing）：quote.pe_ttm + key-metrics evToEBITDATTM
- **NTM**（consensus）：price ÷ analyst-estimates epsAvg（fwd 12 个月）
- **fwd 用户假设**：COVERAGE Val_Anchor（driver-map/quickread 研究产出），预留字段
主倍数优先序：用户 fwd > NTM > TTM。vs 5y 中位来自 ratios 历史（剔负）。
"""

from __future__ import annotations

import statistics
from typing import Any

from .coverage import CoverageEntry


def compute_valuation_row(entry: CoverageEntry, fr: dict[str, Any]) -> dict[str, Any]:
    md = fr.get("market_data", {})
    pc = fr.get("price_change", {})
    est = fr.get("estimates", [])
    km = fr.get("key_metrics", {})
    ratios = fr.get("ratios", [])
    price = md.get("price")

    row: dict[str, Any] = {
        "ticker": entry.ticker,
        "company": entry.company,
        "industry": entry.industry,
        "today": pc.get("1D"),
        "ret_1m": pc.get("1M"),
        "ret_ytd": pc.get("ytd"),
        "ret_1y": pc.get("1Y"),
        "next_call": fr.get("next_earnings_date"),
        "status": entry.coverage_status or entry.monitor_status or "",
        # 三口径
        "pe_ttm": md.get("pe_ttm"),          # fallback：4 季度 EPS 反推
        "pe_ttm_ratio": None,                # FMP ratios priceToEarningsRatio（现成）
        "ev_ebitda_ttm": km.get("evToEBITDATTM"),
        "pe_ntm": None,
        "fwd_multiple": None,   # 用户 fwd 假设（COVERAGE Val_Anchor，预留）
        "fwd_multiple_type": None,
        # 5y 中位 + vs（各自口径）
        "pe_5y_median": None,
        "pe_vs_5y": None,
        "ev_5y_median": None,
        "ev_vs_5y": None,
    }

    # FMP ratios 现成 PE（priceToEarningsRatio）+ 5y PE 中位
    if ratios:
        row["pe_ttm_ratio"] = ratios[0].get("priceToEarningsRatio")
        if row["pe_ttm_ratio"]:
            row["pe_ttm"] = round(float(row["pe_ttm_ratio"]), 1)
        pes = [float(x.get("priceToEarningsRatio")) for x in ratios
               if x.get("priceToEarningsRatio")]
        pes = [v for v in pes if v > 0]
        if len(pes) >= 3:
            row["pe_5y_median"] = round(statistics.median(pes), 1)
            if row["pe_ttm"]:
                row["pe_vs_5y"] = round((row["pe_ttm"] - row["pe_5y_median"]) / row["pe_5y_median"] * 100, 1)

    eps_avg = est[0].get("epsAvg") if est and isinstance(est[0], dict) else None
    if price and eps_avg:
        try:
            row["pe_ntm"] = round(float(price) / float(eps_avg), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # EV/EBITDA 5y 中位（enterpriseValueMultiple 剔负）
    if row["ev_ebitda_ttm"] and isinstance(row["ev_ebitda_ttm"], (int, float)):
        evs = [float(x.get("enterpriseValueMultiple")) for x in ratios
               if x.get("enterpriseValueMultiple")]
        evs = [v for v in evs if v > 0]
        if len(evs) >= 3:
            row["ev_5y_median"] = round(statistics.median(evs), 1)
            row["ev_vs_5y"] = round((float(row["ev_ebitda_ttm"]) - row["ev_5y_median"]) / row["ev_5y_median"] * 100, 1)

    # 主倍数：fwd > NTM > TTM EV/EBITDA > TTM PE
    if row["fwd_multiple"]:
        row["val_multiple"] = f"fwd {row['fwd_multiple_type']}"
        row["valuation"] = row["fwd_multiple"]
    elif row["pe_ntm"]:
        row["val_multiple"] = "P/E NTM"
        row["valuation"] = row["pe_ntm"]
    elif row["ev_ebitda_ttm"]:
        row["val_multiple"] = "EV/EBITDA TTM"
        row["valuation"] = round(float(row["ev_ebitda_ttm"]), 1)
    elif row["pe_ttm"]:
        row["val_multiple"] = "P/E TTM"
        row["valuation"] = round(float(row["pe_ttm"]), 1)
    else:
        row["valuation"] = None

    return row


def format_valuation_cell(row: dict[str, Any]) -> str:
    """估值列：多口径列出，主倍数 vs 5y。

    `TTM 18.2x P/E · NTM 15.3x · fwd 12.5x (vs 中位 +22%)`
    """
    parts = []
    if row.get("pe_ttm"):
        pe_text = f"TTM {row['pe_ttm']}x P/E"
        if row.get("pe_vs_5y") is not None:
            pe_text += f" ({row['pe_vs_5y']:+.0f}% vs 中位 {row['pe_5y_median']})"
        parts.append(pe_text)
    if row.get("pe_ntm"):
        parts.append(f"NTM {row['pe_ntm']}x P/E")
    if row.get("ev_ebitda_ttm"):
        ev_text = f"EV/EBITDA {round(float(row['ev_ebitda_ttm']), 1)}x"
        if row.get("ev_vs_5y") is not None:
            ev_text += f" ({row['ev_vs_5y']:+.0f}% vs 中位 {row['ev_5y_median']})"
        parts.append(ev_text)
    if row.get("fwd_multiple"):
        parts.append(f"fwd {row['fwd_multiple']}x {row['fwd_multiple_type'] or ''}".rstrip())
    if not parts:
        return "—"
    return " · ".join(parts)


def valuation_class(row: dict[str, Any]) -> str:
    vs = row.get("pe_vs_5y")
    if vs is None:
        vs = row.get("ev_vs_5y")
    if vs is None:
        return ""
    if vs > 30:
        return "rich"
    if vs < -30:
        return "cheap"
    return ""
