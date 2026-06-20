from __future__ import annotations

from typing import Any

from .coverage import CoverageEntry


def collect_snapshots(entries: list[CoverageEntry]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    snapshots: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return snapshots, ["yfinance_unavailable"]

    for entry in entries:
        key = entry.ticker or entry.company
        if not key:
            continue
        if not entry.ticker:
            gaps.append(f"{entry.company}: missing_ticker")
            continue
        try:
            history = yf.Ticker(entry.ticker).history(period="5d", interval="1d", auto_adjust=False)
        except Exception as exc:  # pragma: no cover - network/provider dependent
            gaps.append(f"{entry.ticker}: quote_fetch_failed ({exc.__class__.__name__})")
            continue
        if history.empty:
            gaps.append(f"{entry.ticker}: empty_quote_history")
            continue
        closes = history["Close"].dropna().tolist()
        last_price = float(closes[-1])
        previous_price = float(closes[-2]) if len(closes) >= 2 else last_price
        price_move_pct = 0.0 if previous_price == 0 else ((last_price - previous_price) / previous_price) * 100.0
        snapshot: dict[str, Any] = {
            "provider": "yfinance",
            "last_price": last_price,
            "price_move_pct": round(price_move_pct, 2),
            "market_time": str(history.index[-1].date()),
        }
        try:
            news_items = getattr(yf.Ticker(entry.ticker), "news", []) or []
        except Exception:  # pragma: no cover - network/provider dependent
            news_items = []
        if news_items:
            first = news_items[0]
            snapshot["headline"] = first.get("title") or ""
            snapshot["url"] = first.get("link") or ""
            snapshot["published_at"] = str(first.get("providerPublishTime") or "")
        snapshots[key] = snapshot
    return snapshots, sorted(set(gaps))
