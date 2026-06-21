from __future__ import annotations

from typing import Any

from .coverage import CoverageEntry
from .tickers import build_ticker_runtime


def collect_snapshots(entries: list[CoverageEntry]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    snapshots: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return snapshots, ["yfinance_unavailable"]

    for entry in entries:
        ticker_runtime = build_ticker_runtime(entry.ticker, entry.company)
        key = entry.ticker or entry.company
        if not key:
            continue
        if not ticker_runtime.is_quoteable:
            gaps.append(f"{entry.company}: {ticker_runtime.gap}")
            continue
        try:
            ticker = yf.Ticker(ticker_runtime.quote_ticker)
            history = ticker.history(period="45d", interval="1d", auto_adjust=False)
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
        volumes = history.get("Volume")
        volume_ratio = 0.0
        if volumes is not None and len(volumes.dropna()) >= 2:
            volume_values = [float(item) for item in volumes.dropna().tolist()]
            trailing = volume_values[-21:-1] or volume_values[:-1]
            average_volume = sum(trailing) / len(trailing) if trailing else 0.0
            volume_ratio = 0.0 if average_volume == 0 else volume_values[-1] / average_volume
        opens = history.get("Open")
        gap_pct = 0.0
        if opens is not None and len(opens.dropna()) >= 1 and previous_price:
            gap_pct = ((float(opens.dropna().tolist()[-1]) - previous_price) / previous_price) * 100.0
        high_low_window = closes[-20:] if len(closes) >= 20 else closes
        near_high = bool(high_low_window and last_price >= max(high_low_window))
        near_low = bool(high_low_window and last_price <= min(high_low_window))
        snapshot: dict[str, Any] = {
            "provider": "yfinance",
            "quote_ticker": ticker_runtime.quote_ticker,
            "last_price": last_price,
            "price_move_pct": round(price_move_pct, 2),
            "volume_ratio": round(volume_ratio, 2),
            "gap_pct": round(gap_pct, 2),
            "near_20d_high": near_high,
            "near_20d_low": near_low,
            "market_time": str(history.index[-1].date()),
        }
        try:
            news_items = getattr(ticker, "news", []) or []
        except Exception:  # pragma: no cover - network/provider dependent
            news_items = []
        if news_items:
            first = news_items[0]
            snapshot["headline"] = first.get("title") or ""
            snapshot["url"] = first.get("link") or ""
            snapshot["published_at"] = str(first.get("providerPublishTime") or "")
        snapshots[key] = snapshot
    return snapshots, sorted(set(gaps))
