"""AKShare 估值兜底：FMP 盲区 A 股补 PE_TTM / PB + 5y 中位。

背景：FMP 对 2023 年上市批次的科创板（688146 中船特气 / 688531 日联 /
688603 天承 / 688295 中复神鹰等）key-metrics / ratios / estimates 为空
→ 日报估值表 4 列全空。行情已由 yfinance 兜底，估值靠本模块补齐。

数据源：AKShare `stock_zh_valuation_baidu`（百度股市通，个股日序列）：
- 市盈率(TTM) → pe_ttm + pe_5y_median + pe_ttm_vs_5y（估值表主列）
- 市净率 → pb + pb_5y（次要倍数，详情卡片用）

局限（honest gap，不编造）：
- PE_NTM / EV/EBITDA（consensus 口径）AKShare 无 → 保持 None，表内显示 —
- 序列长度 = 上市以来（不足 5y 时 "5y 中位" 即上市以来中位）

仅对 `.SS` / `.SZ` 触发；任何失败返回 gap 描述、不阻塞行情。
"""

from __future__ import annotations

import statistics
from typing import Any

from .coverage import CoverageEntry

_PERIOD = "近五年"


def _is_a_share(ticker: str) -> bool:
    t = (ticker or "").strip().lower()
    return t.endswith(".ss") or t.endswith(".sz")


def _code_of(ticker: str) -> str | None:
    code = (ticker or "").split(".")[0].strip()
    if code.isdigit() and len(code) == 6:
        return code
    return None


def _fetch_series(code: str, indicator: str) -> list[float] | None:
    """单 indicator 日序列（正数过滤）。网络失败 / 空数据 → None。"""
    try:
        import akshare as ak
        df = ak.stock_zh_valuation_baidu(symbol=code, indicator=indicator, period=_PERIOD)
    except Exception:
        return None
    if df is None or df.empty or "value" not in df:
        return None
    out: list[float] = []
    for v in df["value"].dropna().tolist():
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f > 0 and f == f:
            out.append(f)
    return out or None


def _median_positive(vals: list[float]) -> float | None:
    if len(vals) < 3:
        return None
    return round(statistics.median(vals), 1)


def enrich_valuation_row(entry: CoverageEntry, row: dict[str, Any]) -> str:
    """补估值字段。返回 gap 描述（"" = 成功或不适用）。"""
    if not _is_a_share(entry.ticker or ""):
        return ""
    code = _code_of(entry.ticker or "")
    if not code:
        return ""

    gap_parts: list[str] = []

    # 主表：PE_TTM + vs 5y 中位
    pes = _fetch_series(code, "市盈率(TTM)")
    if pes:
        pe = round(pes[-1], 1)
        row["pe_ttm"] = pe
        med = _median_positive(pes)
        if med:
            row["pe_5y_median"] = med
            row["pe_ttm_vs_5y"] = round((pe - med) / med * 100, 1)
    else:
        gap_parts.append("akshare pe_ttm unavailable")

    # 次要倍数：PB + 5y 中位（详情卡片）
    pbs = _fetch_series(code, "市净率")
    if pbs:
        row["pb"] = round(pbs[-1], 1)
        med = _median_positive(pbs)
        if med:
            row["pb_5y"] = med
    else:
        gap_parts.append("akshare pb unavailable")

    # P/FCF 近似：百度"市现率"（市值÷经营现金流）——无真 FCF 源，标 [OCF]
    pcs = _fetch_series(code, "市现率")
    if pcs:
        row["pfcf"] = round(pcs[-1], 1)
        med = _median_positive(pcs)
        if med:
            row["pfcf_5y"] = med
        row["pfcf_note"] = "OCF"
    else:
        gap_parts.append("akshare p/ocf unavailable")

    return f"{entry.ticker}: {'; '.join(gap_parts)}" if gap_parts else ""
