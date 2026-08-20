from __future__ import annotations

from datetime import date
from typing import Any

from .coverage import CoverageEntry
from .tickers import build_ticker_runtime


def _load_fmp():
    """Load financial-data fmp_provider (reused for quote/price_change/news)."""
    import importlib
    import sys
    from pathlib import Path
    pdir = Path(__file__).resolve().parents[2] / "financial-data" / "providers"
    if str(pdir) not in sys.path:
        sys.path.insert(0, str(pdir))
    return importlib.import_module("fmp_provider")


def _fetch_fmp_snapshot(entry: CoverageEntry, today: str | None) -> dict[str, Any] | None:
    """FMP-first quote: price/1D/1M/ytd/1Y/cap/pe + 美股 news headline.

    Returns None on any failure → caller falls back to yfinance.
    """
    try:
        fmp = _load_fmp()
        r = fmp.fetch({"identifier": entry.ticker,
                       "items": ["market_data", "price_change", "historical_price", "news"],
                       "periods": "latest"})
        md = r.get("market_data", {})
        if not md.get("price"):
            return None
        pc = r.get("price_change", {})
        hist = r.get("historical_price", [])
        snap: dict[str, Any] = {
            "provider": "fmp",
            "quote_ticker": r.get("fmp_ticker"),
            "last_price": md["price"],
            "price_move_pct": pc.get("1D"),
            "ret_1m": pc.get("1M"),
            "ret_ytd": pc.get("ytd"),
            "ret_1y": pc.get("1Y"),
            "market_cap": md.get("market_cap"),
            "pe_trailing": md.get("pe_ttm"),
            "market_time": today or str(date.today()),
            "volume_ratio": None,
            "gap_pct": None,
            "near_20d_high": None,
            "near_20d_low": None,
        }
        # 20 日均量 + 20d 高低（从历史价 light 算）
        if len(hist) >= 5:
            try:
                prices = [float(h["price"]) for h in hist[:20] if h.get("price")]
                volumes = [float(h["volume"]) for h in hist[:20] if h.get("volume")]
                if prices:
                    snap["near_20d_high"] = snap["last_price"] >= max(prices)
                    snap["near_20d_low"] = snap["last_price"] <= min(prices)
                if volumes and len(volumes) >= 2:
                    snap["volume_ratio"] = round(volumes[0] / (sum(volumes[1:]) / max(len(volumes) - 1, 1)), 2)
            except Exception:
                pass
        nw = r.get("news", [])
        if nw:
            snap["headline"] = nw[0].get("title") or ""
            snap["url"] = nw[0].get("url") or nw[0].get("site") or ""
            snap["published_at"] = str(nw[0].get("publishedDate") or "")
        snap["quote_status"] = "OK"
        return snap
    except Exception:
        return None


def _fetch_one_snapshot(entry: CoverageEntry, today: str | None) -> tuple[str, dict[str, Any], str]:
    key = entry.ticker or entry.company
    # FMP 优先：行情/涨跌/市值/PE/新闻 headline
    fmp_snap = _fetch_fmp_snapshot(entry, today)
    if fmp_snap is not None:
        return key, fmp_snap, ""
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

    # Historical returns — use Date index, not list index
    import pandas as pd

    def _ret(baseline: float, current: float) -> float | None:
        if not baseline or baseline == 0:
            return None
        return round(((current - baseline) / baseline) * 100.0, 1)

    def _return_since(history, lookback_days: int) -> float | None:
        """Return pct change from ~lookback calendar days ago to last close."""
        if len(history) < 5:
            return None
        try:
            last_date = history.index[-1]
            target_date = last_date - pd.Timedelta(days=lookback_days)
            # Handle tz-aware vs tz-naive
            if hasattr(last_date, 'tz') and last_date.tz is not None:
                if target_date.tz is None:
                    target_date = target_date.tz_localize(last_date.tz)
            mask = history.index >= target_date
            window = history.loc[mask, "Close"].dropna()
            if len(window) >= 2:
                return _ret(float(window.iloc[0]), last_price)
        except Exception:
            pass
        return None

    ret_1m = _return_since(history, 30)
    ret_1y = _return_since(history, 365)

    # YTD: first close on or after Jan 1 of current year
    ret_ytd = None
    try:
        last_date = history.index[-1]
        current_year = pd.Timestamp.now().year if today is None else int(today[:4])
        ytd_ts = pd.Timestamp(f"{current_year}-01-01")
        if hasattr(last_date, 'tz') and last_date.tz is not None and ytd_ts.tz is None:
            ytd_ts = ytd_ts.tz_localize(last_date.tz)
        ytd_mask = history.index >= ytd_ts
        ytd_closes = history.loc[ytd_mask, "Close"].dropna()
        if len(ytd_closes) >= 2:
            ret_ytd = _ret(float(ytd_closes.iloc[0]), last_price)
    except Exception:
        pass

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
        "market_cap": None,
        "pe_trailing": None,
    }
    # Fetch market cap + PE (lightweight info call)
    try:
        info = ticker.info
        if info.get("marketCap"):
            snapshot["market_cap"] = info["marketCap"]
        if info.get("trailingPE"):
            snapshot["pe_trailing"] = round(float(info["trailingPE"]), 1)
    except Exception:
        pass
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
