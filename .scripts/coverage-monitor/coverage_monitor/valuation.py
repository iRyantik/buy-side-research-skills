"""估值纯函数：FMP 数据 → 日报估值表行。

纯函数：任何一天同一输入 → 同一输出（估值 = f(价格, forward, 估值锚))。
主倍数 EV/EBITDA（key-metrics-ttm）优先，PE_NTM（analyst-estimates）其次；
vs 5y 中位来自 ratios 历史 enterpriseValueMultiple（剔负）。
"""

from __future__ import annotations

import statistics
from typing import Any

from .coverage import CoverageEntry


def compute_valuation_row(entry: CoverageEntry, fr: dict[str, Any]) -> dict[str, Any]:
    """从 FMP fetch 结果算一家估值行。"""
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
        "valuation": None,
        "val_multiple": None,
        "val_5y_median": None,
        "val_vs_5y": None,
    }

    ev_ebitda = km.get("evToEBITDATTM")
    eps_avg = est[0].get("epsAvg") if est and isinstance(est[0], dict) else None
    pe_ntm = (price / eps_avg) if (price and eps_avg) else None

    if ev_ebitda and isinstance(ev_ebitda, (int, float)):
        row["val_multiple"] = "EV/EBITDA"
        row["valuation"] = round(float(ev_ebitda), 1)
        evs = [float(x.get("enterpriseValueMultiple")) for x in ratios
               if x.get("enterpriseValueMultiple")]
        evs = [v for v in evs if v > 0]
        if len(evs) >= 3:
            median = statistics.median(evs)
            row["val_5y_median"] = round(median, 1)
            row["val_vs_5y"] = round((row["valuation"] - median) / median * 100, 1)
    elif pe_ntm and isinstance(pe_ntm, (int, float)):
        row["val_multiple"] = "P/E fwd"
        row["valuation"] = round(float(pe_ntm), 1)

    return row


def format_valuation_cell(row: dict[str, Any]) -> str:
    """估值列展示：`12.3x EV/EBITDA (vs 中位 +122%)`；无假设 → `—`。"""
    if not row.get("valuation") or not row.get("val_multiple"):
        return "—"
    text = f"{row['valuation']}x {row['val_multiple']}"
    if row.get("val_vs_5y") is not None:
        vs = row["val_vs_5y"]
        text += f" (vs 中位 {vs:+.0f}%)"
    else:
        text += " [无历史]"
    return text


def valuation_class(row: dict[str, Any]) -> str:
    """贵/便宜染色：vs 5y 中位 ±30% → 贵红便宜绿。"""
    vs = row.get("val_vs_5y")
    if vs is None:
        return ""
    if vs > 30:
        return "rich"
    if vs < -30:
        return "cheap"
    return ""
