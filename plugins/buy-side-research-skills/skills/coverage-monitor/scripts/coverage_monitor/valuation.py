"""估值纯函数：FMP 数据 → 日报估值表行。

估值表 4 列（每个口径单列）：
- PE_TTM：ratios priceToEarningsRatio（FMP 现成）+ vs 5y 中位（ratios 历史）
- PE_NTM：price ÷ consensus epsAvg；有用户 fwd 假设则并列显示
- EV/EBITDA_TTM：key-metrics evToEBITDATTM（现成）+ vs 5y 中位（ratios 历史）
- EV/EBITDA_NTM：EV（mcap+净债）÷ NTM EBITDA（estimates ebitdaAvg）

次要倍数（PS/PB/P-FCF 等）→ 详情卡片用，不在主表。
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
    mcap = md.get("market_cap")

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
        # PE
        "pe_ttm": None, "pe_ttm_vs_5y": None, "pe_5y_median": None,
        "pe_ntm": None, "pe_fwd": None,          # pe_fwd = 用户研究 fwd（COVERAGE Val_Anchor 预留）
        # EV/EBITDA
        "ev_ttm": None, "ev_ttm_vs_5y": None, "ev_5y_median": None,
        "ev_ntm": None,
    }

    # ── PE TTM + 5y 中位 ──
    if ratios:
        r0 = ratios[0]
        if r0.get("priceToEarningsRatio"):
            row["pe_ttm"] = round(float(r0["priceToEarningsRatio"]), 1)
        pes = [float(x["priceToEarningsRatio"]) for x in ratios if x.get("priceToEarningsRatio")]
        pes = [v for v in pes if v > 0]
        if len(pes) >= 3 and row["pe_ttm"]:
            row["pe_5y_median"] = round(statistics.median(pes), 1)
            row["pe_ttm_vs_5y"] = round((row["pe_ttm"] - row["pe_5y_median"]) / row["pe_5y_median"] * 100, 1)

    # ── PE NTM（consensus fwd）──
    eps_avg = est[0].get("epsAvg") if est and isinstance(est[0], dict) else None
    if price and eps_avg:
        try:
            row["pe_ntm"] = round(float(price) / float(eps_avg), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # ── EV/EBITDA TTM + 5y 中位 ──
    ev_ttm = km.get("evToEBITDATTM")
    if ev_ttm and isinstance(ev_ttm, (int, float)):
        row["ev_ttm"] = round(float(ev_ttm), 1)
        evs = [float(x["enterpriseValueMultiple"]) for x in ratios if x.get("enterpriseValueMultiple")]
        evs = [v for v in evs if v > 0]
        if len(evs) >= 3:
            row["ev_5y_median"] = round(statistics.median(evs), 1)
            row["ev_ttm_vs_5y"] = round((row["ev_ttm"] - row["ev_5y_median"]) / row["ev_5y_median"] * 100, 1)

    # ── EV/EBITDA NTM：EV = mcap + 净债；NTM EBITDA = estimates ebitdaAvg ──
    ebitda_ntm = est[0].get("ebitdaAvg") if est and isinstance(est[0], dict) else None
    if mcap and ebitda_ntm:
        try:
            ebitda_ntm_f = float(ebitda_ntm)
            if ebitda_ntm_f > 0:
                nd_ratio = km.get("netDebtToEBITDATTM")
                if nd_ratio and row["ev_ttm"]:
                    ebitda_ttm = float(mcap) / float(row["ev_ttm"])
                    net_debt = float(nd_ratio) * ebitda_ttm
                else:
                    net_debt = 0.0
                row["ev_ntm"] = round((float(mcap) + net_debt) / ebitda_ntm_f, 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    return row


def fmt_cell(value: Any, vs: Any = None, extra: str | None = None) -> str:
    """单列格式：`58.2x (+36%)` / `22.4x (你 15x)` / `—`。"""
    if value is None:
        return "—"
    text = f"{value}x"
    if extra:
        text += f" {extra}"
    elif vs is not None:
        text += f" ({vs:+.0f}%)"
    return text


def rich_class(vs: Any) -> str:
    """贵/便宜染色：vs 5y 中位 ±30% → 贵红便宜绿。"""
    if vs is None:
        return ""
    if vs > 30:
        return "rich"
    if vs < -30:
        return "cheap"
    return ""
