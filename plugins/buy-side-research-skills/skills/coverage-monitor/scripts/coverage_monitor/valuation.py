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
        "pe_ttm": md.get("pe_ttm"),
        "ev_ebitda_ttm": km.get("evToEBITDATTM"),
        "pe_ntm": None,
        "fwd_multiple": None,   # 用户 fwd 假设（COVERAGE Val_Anchor，预留）
        "fwd_multiple_type": None,
        # 5y 中位 + vs
        "val_5y_median": None,
        "val_vs_5y": None,
    }

    eps_avg = est[0].get("epsAvg") if est and isinstance(est[0], dict) else None
    if price and eps_avg:
        try:
            row["pe_ntm"] = round(float(price) / float(eps_avg), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # vs 5y 中位：只对 EV/EBITDA（ratios 历史 enterpriseValueMultiple 剔负）。
    # PE 不配 vs 5y——FMP 无 5y PE 历史，PE vs EV/EBITDA 中位是口径错误。
    if row["ev_ebitda_ttm"] and isinstance(row["ev_ebitda_ttm"], (int, float)):
        evs = [float(x.get("enterpriseValueMultiple")) for x in ratios
               if x.get("enterpriseValueMultiple")]
        evs = [v for v in evs if v > 0]
        if len(evs) >= 3:
            row["val_5y_median"] = round(statistics.median(evs), 1)
            row["val_vs_5y"] = round((float(row["ev_ebitda_ttm"]) - row["val_5y_median"]) / row["val_5y_median"] * 100, 1)

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
        parts.append(f"TTM {round(float(row['pe_ttm']), 1)}x P/E")
    if row.get("pe_ntm"):
        parts.append(f"NTM {row['pe_ntm']}x P/E")
    if row.get("ev_ebitda_ttm"):
        ev_text = f"EV/EBITDA {round(float(row['ev_ebitda_ttm']), 1)}x"
        if row.get("val_vs_5y") is not None:
            ev_text += f" (+{row['val_vs_5y']:.0f}% vs 中位 {row['val_5y_median']})" if row['val_vs_5y'] > 0 else f" ({row['val_vs_5y']:.0f}% vs 中位 {row['val_5y_median']})"
        parts.append(ev_text)
    if row.get("fwd_multiple"):
        parts.append(f"fwd {row['fwd_multiple']}x {row['fwd_multiple_type'] or ''}".rstrip())
    if not parts:
        return "—"
    return " · ".join(parts)


def valuation_class(row: dict[str, Any]) -> str:
    vs = row.get("val_vs_5y")
    if vs is None:
        return ""
    if vs > 30:
        return "rich"
    if vs < -30:
        return "cheap"
    return ""
