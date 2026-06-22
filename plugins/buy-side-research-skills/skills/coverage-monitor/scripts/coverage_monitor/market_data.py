from __future__ import annotations

from datetime import date
from typing import Any

from .coverage import CoverageEntry
from .tickers import build_ticker_runtime


def _fetch_one_snapshot(entry: CoverageEntry, today: str | None) -> tuple[str, dict[str, Any], str]:
    import yfinance as yf
    ticker_runtime = build_ticker_runtime(entry.ticker, entry.company)
    key = entry.ticker or entry.company
    if not ticker_runtime.is_quoteable:
        return key, {"quote_status": "No Data"}, f"{entry.company}: {ticker_runtime.gap}"
    try:
        ticker = yf.Ticker(ticker_runtime.quote_ticker)
        history = ticker.history(period="1y", interval="1d", auto_adjust=False)
    except Exception as exc:
        return key, {"quote_status": "No Data"}, f"{entry.ticker}: quote_fetch_failed ({exc.__class__.__name__})"
    if history.empty:
        return key, {"quote_status": "No Data"}, f"{entry.ticker}: empty_quote_history"
    closes = history["Close"].dropna().tolist()
    last_price = float(closes[-1])
    previous_price = float(closes[-2]) if len(closes) >= 2 else last_price
    price_move_pct = 0.0 if previous_price == 0 else ((last_price - previous_price) / previous_price) * 100.0

    # Historical returns: 1m (~21d), YTD, 1y
    def _ret(baseline: float, current: float) -> float | None:
        if not baseline or baseline == 0:
            return None
        return round(((current - baseline) / baseline) * 100.0, 1)

    # 1m: ~21 trading days back (capped at available data)
    idx_1m = max(0, len(closes) - 22)
    ret_1m = _ret(float(closes[idx_1m]), last_price) if len(closes) >= 5 else None

    # YTD: first close on or after Jan 1 of current year (use index dates)
    import pandas as pd
    try:
        current_year = pd.Timestamp.now().year if today is None else int(today[:4])
        ytd_mask = history.index >= pd.Timestamp(f"{current_year}-01-01")
        ytd_closes = history.loc[ytd_mask, "Close"].dropna()
        ret_ytd = _ret(float(ytd_closes.iloc[0]), last_price) if len(ytd_closes) >= 2 else None
    except Exception:
        ret_ytd = None

    # 1y: earliest available close if we have >= 6 months of data
    ret_1y = _ret(float(closes[0]), last_price) if len(closes) >= 120 else None

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
        "ret_1m": ret_1m,
        "ret_ytd": ret_ytd,
        "ret_1y": ret_1y,
        "market_time": str(history.index[-1].date()),
    }
    gap = ""
    if len(closes) < 2 or volume_ratio == 0.0 or gap_pct == 0.0:
        snapshot["quote_status"] = "Partial"
        gap = f"{entry.ticker}: quote_status:Partial"
    if today:
        try:
            if (date.fromisoformat(today) - history.index[-1].date()).days > 5:
                snapshot["quote_status"] = "Stale"
                gap = f"{entry.ticker}: quote_status:Stale"
        except ValueError:
            pass
    try:
        news_items = getattr(ticker, "news", []) or []
    except Exception:
        news_items = []
    if news_items:
        first = news_items[0]
        snapshot["headline"] = first.get("title") or ""
        snapshot["url"] = first.get("link") or ""
        snapshot["published_at"] = str(first.get("providerPublishTime") or "")
    return key, snapshot, gap


def collect_snapshots(entries: list[CoverageEntry], today: str | None = None,
                      max_workers: int = 8) -> tuple[dict[str, dict[str, Any]], list[str]]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return {}, ["yfinance_unavailable"]

    snapshots: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    # Skip unlisted/IPO/private — yfinance hangs on them
    _SKIP_TICKER = {"ipo pending", "private", ""}
    targets = [e for e in entries
               if e.ticker and e.ticker.strip().lower() not in _SKIP_TICKER]

    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
        futures = {pool.submit(_fetch_one_snapshot, e, today): e for e in targets}
        for future in as_completed(futures):
            key, snapshot, gap = future.result()
            snapshots[key] = snapshot
            if gap:
                gaps.append(gap)
    return snapshots, sorted(set(gaps))
