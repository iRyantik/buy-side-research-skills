"""Research Candidates：数据信号驱动的研究优先级推荐（纯函数，可单测）。

信号打分（总分 ≥ min_score 入选，Top N）：
  重要异动 ±8%                      +2
  普通异动 ±5%                      +1
  深度低估（任一估值 vs 5y 中位 ≤ -30%） +2
  深度贵（任一估值 vs 5y 中位 ≥ +30%）  +1
  财报 7 天内                        +1
  重大新闻（订单/并购/业绩标签）        +1
  放量 volume_ratio ≥ 2.0            +1

口径：深度低估/贵只用 TTM 静态倍数 vs 5y（pe_ttm_vs_5y 等——历史可重建）；
NTM 估值无历史 forward 数据，不参与对比，只显示当前值。
纯信号提醒，不含预测——只标"值得看一眼"，理由可追溯。
"""

from __future__ import annotations

from datetime import date as _date

# (估值字段, vs 5y 字段)——TTM 静态倍数才有历史 5y 基准
_VS_FIELDS = [
    ("pe_ttm", "pe_ttm_vs_5y"),
    ("ev_ttm", "ev_ttm_vs_5y"),
    ("ps", "ps_5y"),
    ("pb", "pb_5y"),
    ("pfcf", "pfcf_5y"),
]


def _news_lead(items: list) -> object | None:
    """第一条命中标签的新闻（订单/并购/业绩等），无则 None。"""
    from .news import tag_news_title
    for it in items or []:
        if tag_news_title(it.title):
            return it
    return None


def score_candidates(entries: list, snapshots: dict, news_map: dict,
                     today: str, top_n: int = 5, min_score: int = 3) -> list[dict]:
    """返回 [{entry, score, signals: [(score, text)], pct, news}]，按总分降序取 Top N。"""
    out: list[dict] = []
    try:
        _td = _date.fromisoformat(str(today)[:10])
    except Exception:
        _td = _date.today()

    for e in entries:
        ticker = e.ticker or e.company
        snap = snapshots.get(ticker, {})
        if snap.get("price_move_pct") is None:
            continue  # 无行情数据 → 无法判断，不推荐
        vrow = snap.get("valuation") or {}
        signals: list[tuple[int, str]] = []

        # 异动
        pct = snap.get("price_move_pct")
        if pct is not None:
            a = abs(float(pct))
            if a >= 8:
                signals.append((2, f"异动 {float(pct):+.1f}%"))
            elif a >= 5:
                signals.append((1, f"异动 {float(pct):+.1f}%"))

        # 深度低估 / 深度贵（TTM vs 5y，只取最强的一个）
        deep = None
        for field, vs_field in _VS_FIELDS:
            v = vrow.get(vs_field)
            if v is None:
                continue
            if float(v) <= -30:
                deep = (2, f"深度低估 {float(v):+.0f}% ({field})")
                break
            if float(v) >= 30:
                deep = (1, f"深度贵 {float(v):+.0f}% ({field})")
                break
        if deep:
            signals.append(deep)

        # 财报临近
        nd = snap.get("next_earnings")
        if nd:
            try:
                days = (_date.fromisoformat(str(nd)[:10]) - _td).days
                if 0 <= days <= 7:
                    signals.append((1, f"财报 {days} 天后"))
            except Exception:
                pass

        # 重大新闻
        lead = _news_lead(news_map.get(ticker, []))
        if lead:
            signals.append((1, "重大新闻"))

        # 放量
        vr = snap.get("volume_ratio")
        if vr is not None:
            try:
                if float(vr) >= 2.0:
                    signals.append((1, f"放量 {float(vr):.1f}x"))
            except Exception:
                pass

        total = sum(s for s, _ in signals)
        if total < min_score:
            continue
        signals.sort(key=lambda x: -x[0])  # 强信号在前
        out.append({
            "entry": e,
            "score": total,
            "signals": signals,
            "pct": float(pct) if pct is not None else 0.0,
            "news": lead,
        })

    out.sort(key=lambda x: (-x["score"], -abs(x["pct"])))
    return out[:top_n]
