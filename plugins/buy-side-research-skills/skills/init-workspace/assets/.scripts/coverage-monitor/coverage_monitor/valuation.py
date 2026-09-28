"""估值纯函数：FMP 数据 → 日报估值表行。

估值表 4 列（每个口径单列）：
- PE_TTM：ratios priceToEarningsRatio（FMP 现成）+ vs 5y 中位（ratios 历史）
- PE_NTM：price ÷ consensus epsAvg；有用户 fwd 假设则并列显示
- EV/EBITDA_TTM：key-metrics evToEBITDATTM（现成）+ vs 5y 中位（ratios 历史）
- EV/EBITDA_NTM：EV（mcap+净债）÷ NTM EBITDA（estimates ebitdaAvg）

次要倍数（PS/PB/P-FCF 等）→ 详情卡片用，不在主表。
"""

from __future__ import annotations

import datetime
import json
import re
import statistics
from pathlib import Path
from typing import Any

from .coverage import CoverageEntry

# COVERAGE Val_Anchor 列格式：`15x PE @ 08-21` / `8.5x EV/EBITDA @ 08-19`（as_of = MM-DD）
_VAL_ANCHOR_RE = re.compile(
    r"(?P<multiple>\d+(?:\.\d+)?)\s*x\s*(?P<kind>PE|EV/EBITDA)\s*@\s*(?P<mm>\d{1,2})-(?P<dd>\d{1,2})",
    re.IGNORECASE,
)

# 锚过期阈值：>45 天视为 stale
VAL_ANCHOR_STALE_DAYS = 45


def _estimates_snapshot(ticker: str) -> tuple[float | None, float | None]:
    """从 estimates-resolved.json 取 (eps, ebitda)：L1 forward → L2 consensus 最近期。

    文件缺失/该公司无数据 → (None, None)。估值的 estimates 数据统一来自这里
    （integration plan §7：日报估值 = f(价格, forward 老数字)），不实时拉 analyst-estimates。
    """
    try:
        ws = Path(__file__).resolve().parents[3]  # workspace 根（同 market_data 推断）
        p = ws / ".cache" / "estimates" / "estimates-resolved.json"
        if not p.exists():
            return None, None
        entry = json.loads(p.read_text(encoding="utf-8")).get(ticker) or {}
    except Exception:
        return None, None
    fwd = (entry.get("forward") or {}).get("metrics") or {}
    if fwd.get("eps") is not None or fwd.get("ebitda") is not None:
        return fwd.get("eps"), fwd.get("ebitda")
    periods = (entry.get("consensus") or {}).get("periods") or []
    if periods:
        p0 = _pick_ntm_period(periods)
        if p0:
            return p0.get("eps_avg"), p0.get("ebitda_avg")
    return None, None


def _pick_ntm_period(periods: list[dict]) -> dict | None:
    """NTM 年度 = date ≥ 今天的最近未来财年；全部已过 → 取最近（最大 date）。

    FMP analyst-estimates 的 periods 曾按 2030→2027 倒序返回，无脑取 periods[0]
    会拿最远期年度的 EPS 算 PE_NTM（RHM 案例：€126 vs €54.5 → 9.1x 假象）。
    """
    today = datetime.date.today().isoformat()
    future = [p for p in periods if (p.get("date") or "") >= today]
    if future:
        future.sort(key=lambda p: p.get("date") or "")
        return future[0]
    past = [p for p in periods if p.get("date")]
    if past:
        past.sort(key=lambda p: p.get("date") or "")
        return past[-1]
    return None


def parse_val_anchor(text: str) -> tuple[str, float, datetime.date] | None:
    """解析 `15x PE @ 08-21` → ("PE", 15.0, date(2026,8,21))；不匹配返回 None。

    as_of 是 MM-DD：默认落在今年，若日期已越过今天则视为去年（跨年锚）。
    """
    if not text:
        return None
    m = _VAL_ANCHOR_RE.search(text)
    if not m:
        return None
    today = datetime.date.today()
    try:
        as_of = today.replace(month=int(m["mm"]), day=int(m["dd"]))
    except ValueError:
        return None
    if as_of > today:
        as_of = as_of.replace(year=as_of.year - 1)
    return m["kind"].upper(), float(m["multiple"]), as_of


def compute_valuation_row(entry: CoverageEntry, fr: dict[str, Any]) -> dict[str, Any]:
    md = fr.get("market_data", {})
    pc = fr.get("price_change", {})
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
        "pe_ntm": None, "pe_fwd": None, "pe_fwd_asof": None, "pe_fwd_stale": False,
        # EV/EBITDA
        "ev_ttm": None, "ev_ttm_vs_5y": None, "ev_5y_median": None,
        "ev_ntm": None, "ev_fwd": None, "ev_fwd_asof": None, "ev_fwd_stale": False,
        # 次要倍数（详情卡片）：PS/PB/P-FCF + 5y 中位
        "ps": None, "ps_5y": None,
        "pb": None, "pb_5y": None,
        "pfcf": None, "pfcf_5y": None,
        "pfcf_note": None,  # 口径注记：AKShare 兜底 = OCF（市值/经营现金流，非 FCF）
    }

    # ── PE TTM + 5y 中位（亏损公司 PE ≤ 0 无意义 → None → 渲染 NA）──
    if ratios:
        r0 = ratios[0]
        if r0.get("priceToEarningsRatio") and float(r0["priceToEarningsRatio"]) > 0:
            row["pe_ttm"] = round(float(r0["priceToEarningsRatio"]), 1)
        pes = [float(x["priceToEarningsRatio"]) for x in ratios if x.get("priceToEarningsRatio")]
        pes = [v for v in pes if v > 0]
        if len(pes) >= 3 and row["pe_ttm"] and row["pe_ttm"] > 0:
            row["pe_5y_median"] = round(statistics.median(pes), 1)
            row["pe_ttm_vs_5y"] = round((row["pe_ttm"] - row["pe_5y_median"]) / row["pe_5y_median"] * 100, 1)

    # ── 次要倍数（详情卡片）：PS/PB/P-FCF + 5y 中位 ──
    if ratios:
        r0 = ratios[0]
        for fld, key in (("priceToSalesRatio", "ps"),
                         ("priceToBookRatio", "pb"),
                         ("priceToFreeCashFlowRatio", "pfcf")):
            v = r0.get(fld)
            if v and float(v) > 0:  # ≤ 0（亏损/负净资产）倍数无意义 → None
                row[key] = round(float(v), 1)
            hist = [float(x.get(fld)) for x in ratios if x.get(fld)]
            hist = [h for h in hist if h > 0]
            if len(hist) >= 3:
                row[f"{key}_5y"] = round(statistics.median(hist), 1)

    # ── PE NTM（estimates 层：L1 forward → L2 consensus eps_avg）──
    eps_avg, _ebitda_l2 = _estimates_snapshot(entry.ticker)
    if price and eps_avg and float(eps_avg) > 0:  # 预期亏损 → PE_NTM 无意义 → None
        try:
            row["pe_ntm"] = round(float(price) / float(eps_avg), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # ── EV/EBITDA TTM + 5y 中位 ──
    ev_ttm = km.get("evToEBITDATTM")
    if ev_ttm and isinstance(ev_ttm, (int, float)) and float(ev_ttm) > 0:  # 负 EBITDA → 无意义 → None
        row["ev_ttm"] = round(float(ev_ttm), 1)
        evs = [float(x["enterpriseValueMultiple"]) for x in ratios if x.get("enterpriseValueMultiple")]
        evs = [v for v in evs if v > 0]
        if len(evs) >= 3:
            row["ev_5y_median"] = round(statistics.median(evs), 1)
            row["ev_ttm_vs_5y"] = round((row["ev_ttm"] - row["ev_5y_median"]) / row["ev_5y_median"] * 100, 1)

    # ── EV/EBITDA NTM：EV = mcap + 净债；NTM EBITDA = estimates 层（L1 forward → L2 consensus）──
    _eps_l1, ebitda_ntm = _estimates_snapshot(entry.ticker)
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

    # ── 研究 fwd 锚（COVERAGE Val_Anchor：`15x PE @ 08-21` / `8.5x EV/EBITDA @ 08-19`）──
    anchor = parse_val_anchor(entry.val_anchor)
    if anchor:
        kind, multiple, as_of = anchor
        stale = (datetime.date.today() - as_of).days > VAL_ANCHOR_STALE_DAYS
        if kind == "PE":
            row["pe_fwd"] = multiple
            row["pe_fwd_asof"] = as_of.isoformat()
            row["pe_fwd_stale"] = stale
        elif kind == "EV/EBITDA":
            row["ev_fwd"] = multiple
            row["ev_fwd_asof"] = as_of.isoformat()
            row["ev_fwd_stale"] = stale

    return row


def fwd_extra(row: dict[str, Any], kind: str) -> str | None:
    """Val_Anchor 的显示后缀：`fwd 15x`；锚过期（>45 天）→ `fwd 15x(旧)`；无锚 None。"""
    fld = "pe_fwd" if kind == "PE" else "ev_fwd"
    val = row.get(fld)
    if val is None:
        return None
    suffix = "(旧)" if row.get(f"{fld}_stale") else ""
    text = f"{val:g}" if float(val) == int(val) else f"{val}"
    return f"fwd {text}x{suffix}"


def fmt_cell(value: Any, vs: Any = None, extra: str | None = None) -> str:
    """单列格式：`58.2x (+36%)` / `22.4x fwd 15x` / `—`。

    consensus 缺失但有研究锚时，单独显示锚（`fwd 15x`），不丢信息。
    """
    if value is None:
        return extra if extra else "—"
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
