from __future__ import annotations

from datetime import date
from typing import Any

from .coverage import CoverageEntry
from .tickers import build_ticker_runtime


def _market_session(ticker: str):
    """该 ticker 所属市场的 (tz_name, open_h, close_h)；未知市场 → None。"""
    from .news import _market_session_for

    return _market_session_for(ticker)


def _bar_date(ts, tz_name: str):
    """K 线时间戳 → 该市场本地日期（分钟线 index 带 tz）。"""
    from zoneinfo import ZoneInfo

    try:
        if getattr(ts, "tzinfo", None) is not None:
            return ts.tz_convert(ZoneInfo(tz_name)).date()
    except Exception:
        pass
    try:
        return ts.date()
    except Exception:
        return None


def _live_intraday_snapshot(quote_ticker: str, ticker: str, daily_history, now=None) -> dict[str, Any] | None:
    """日线还没有"今天"这根时（盘初/数据源滞后），用分钟线补出当天实时涨跌幅。

    只在市场**正在交易**时使用：非交易时段不存在"实时价"，硬取分钟线只会拿到上一
    交易日的数据，那就又变成推旧数据了（这正是 2026-09-28 修的那个 bug）。
    拿不到当天分钟线 → None（调用方保留日线结果，再由提醒端判断是否够新）。

    now: 注入"当前时间"（测试用）；None = 真实当前时间。
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    import yfinance as yf

    session = _market_session(ticker)
    if not session:
        return None
    tz_name, open_h, close_h = session
    try:
        now_local = now.astimezone(ZoneInfo(tz_name)) if now is not None else datetime.now(ZoneInfo(tz_name))
    except Exception:
        return None
    if now_local.weekday() >= 5:
        return None
    hh = now_local.hour + now_local.minute / 60.0
    if not (open_h <= hh < close_h):
        return None  # 非交易时段：没有实时价可取
    market_today = now_local.date()

    # 上一交易日收盘 = 日线里最后一根早于该市场今天的收盘
    prev_close = None
    try:
        for ts, row in daily_history.iloc[::-1].iterrows():
            d = _bar_date(ts, tz_name)
            if d is not None and d < market_today:
                prev_close = float(row["Close"])
                break
    except Exception:
        return None
    if not prev_close:
        return None

    for interval in ("1m", "5m"):
        try:
            bars = yf.Ticker(quote_ticker).history(period="1d", interval=interval, auto_adjust=False)
        except Exception:
            continue
        if bars is None or bars.empty or "Close" not in bars:
            continue
        today_bars = bars[[_bar_date(ts, tz_name) == market_today for ts in bars.index]]
        if today_bars.empty:
            continue
        closes_live = today_bars["Close"].dropna()
        if closes_live.empty:
            continue
        live = float(closes_live.iloc[-1])
        opens_live = today_bars["Open"].dropna()
        # 日内累计量 / 20 日均量：盘初天然偏低（当日未走完），仅作参考；
        # A 股分钟线 Volume 常为 0 → 返回 None，调用方保留日线口径
        volume_ratio = None
        try:
            volumes_live = today_bars["Volume"].dropna()
            daily_vol = daily_history["Volume"].dropna().tolist()[-21:-1]
            intraday_vol = float(volumes_live.sum()) if not volumes_live.empty else 0.0
            if intraday_vol > 0 and daily_vol:
                avg_vol = sum(float(v) for v in daily_vol) / len(daily_vol)
                if avg_vol > 0:
                    volume_ratio = round(intraday_vol / avg_vol, 2)
        except Exception:
            volume_ratio = None
        return {
            "last_price": live,
            "price_move_pct": round((live - prev_close) / prev_close * 100.0, 2),
            "gap_pct": round((float(opens_live.iloc[0]) - prev_close) / prev_close * 100.0, 2)
                       if not opens_live.empty else 0.0,
            "volume_ratio": volume_ratio,
            "market_time": market_today.isoformat(),
            "prev_close": prev_close,
            "interval": interval,
        }
    return None


def _load_fmp():
    """Load financial-data fmp_provider (reused for quote/price_change/news).

    fmp_provider reads FMP_API_KEY from os.environ only — the workspace .env
    must be loaded here or every FMP call fails and everything degrades to
    yfinance (quote ok, valuation empty).
    """
    import importlib
    import os
    import sys
    from pathlib import Path
    _load_workspace_env()
    pdir = Path(__file__).resolve().parents[2] / "financial-data" / "providers"
    if str(pdir) not in sys.path:
        sys.path.insert(0, str(pdir))
    return importlib.import_module("fmp_provider")


def _load_workspace_env() -> None:
    """Load workspace root .env into os.environ (setdefault — never override real env)."""
    import os
    from pathlib import Path
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _fetch_fmp_snapshot(entry: CoverageEntry, today: str | None) -> dict[str, Any] | None:
    """FMP-first quote: price/1D/1M/ytd/1Y/cap/pe + 美股 news headline.

    Returns None on any failure → caller falls back to yfinance.
    """
    try:
        fmp = _load_fmp()
        r = fmp.fetch({"identifier": entry.ticker, "name": entry.company,
                       "items": ["market_data", "price_change", "historical_price", "news",
                                 "key_metrics", "ratios", "earnings_calendar"],
                       "periods": "latest"})
        md = r.get("market_data", {})
        if not md.get("price"):
            return None
        pc = r.get("price_change", {})
        hist = r.get("historical_price", [])
        # FMP 对 A股 盘中行情有更新延迟：今日价未同步时 price 仍 == 最近一个已收盘价(昨收)，
        # 此时 /stock-price-change 的 1D 实际是"昨收 vs 前收"(如 300285.SZ 9.19% vs 真实 +2.66%)，
        # 会被 assess_snapshot 误判 +8% 重要异动。检测到"价=昨收(历史最新一根)"视为 stale，
        # return None 回退 yfinance 自算(实时)，避免盘初误报。
        if hist and md.get("price") is not None:
            try:
                last_hist_price = float(hist[0]["price"])  # historical_price 降序：最新在前=昨收
                if last_hist_price and abs(float(md["price"]) - last_hist_price) < 1e-6:
                    return None
            except Exception:
                pass
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
            "quote_time": md.get("as_of"),  # FMP quote 行情时间戳（精确到时分）
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
        # 估值 + 下次财报（日报估值表原料）
        try:
            from .valuation import compute_valuation_row
            snap["valuation"] = compute_valuation_row(entry, r)
        except Exception:
            pass
        snap["next_earnings"] = r.get("next_earnings_date")
        snap["quote_status"] = "OK"
        return snap
    except Exception:
        return None


def _fetch_one_snapshot(entry: CoverageEntry, today: str | None, live_intraday: bool = False) -> tuple[str, dict[str, Any], str]:
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
    # ── 盘初/数据源滞后：日线还没有"今天"这根 → 用分钟线补当天实时涨跌幅 ──
    # 只在盘中调用方（intraday 扫描）开启：盘后日报要的是"该交易日的收盘"，不该拿实时价。
    market_time = str(history.index[-1].date())
    intraday_live = None
    if live_intraday:
        intraday_live = _live_intraday_snapshot(ticker_runtime.quote_ticker, entry.ticker, history)
    if intraday_live:
        last_price = intraday_live["last_price"]
        price_move_pct = intraday_live["price_move_pct"]
        gap_pct = intraday_live["gap_pct"]
        if intraday_live.get("volume_ratio") is not None:
            volume_ratio = intraday_live["volume_ratio"]
        market_time = intraday_live["market_time"]

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
        "market_time": market_time,
        "market_cap": None,
        "pe_trailing": None,
    }
    if intraday_live:
        # 留痕：这根涨跌幅来自分钟线（日线还没今天），便于事后核对口径
        snapshot["intraday_source"] = intraday_live["interval"]
        snapshot["prev_close"] = intraday_live["prev_close"]
    # Fetch market cap + PE (lightweight info call)
    try:
        info = ticker.info
        if info.get("marketCap"):
            snapshot["market_cap"] = info["marketCap"]
        if info.get("trailingPE"):
            snapshot["pe_trailing"] = round(float(info["trailingPE"]), 1)
    except Exception:
        pass
    # Valuation row for FMP-blind tickers: only ret fields are available here
    # (PE/EV need FMP ratios/estimates). Build the same row shape so the brief
    # renderer reads one consistent structure.
    from .valuation import compute_valuation_row
    val_row = compute_valuation_row(entry, {})
    val_row.update({
        "today": round(price_move_pct, 1),
        "ret_1m": ret_1m,
        "ret_ytd": ret_ytd,
        "ret_1y": ret_1y,
    })
    snapshot["valuation"] = val_row
    # AKShare 兜底（best-effort）：FMP 盲区 A 股（2023 年科创板批次）补
    # PE_TTM + 5y 中位；失败静默，仅 gap 里留痕，不阻塞行情
    ak_gap = ""
    try:
        from .akshare_valuation import enrich_valuation_row
        ak_gap = enrich_valuation_row(entry, val_row)
    except Exception:
        pass
    gap = ak_gap
    if len(closes) < 2 or volume_ratio == 0.0 or gap_pct == 0.0:
        snapshot["quote_status"] = "Partial"
        gap = f"{entry.ticker}: quote_status:Partial" + (f"; {ak_gap}" if ak_gap else "")
    if today:
        try:
            # 用 market_time（可能已被分钟线补成今天）而非日线末根，否则补过的实时行情被误标 Stale
            if (date.fromisoformat(today) - date.fromisoformat(market_time)).days > 5:
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
                      max_workers: int = 16,
                      live_intraday: bool = False) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """抓快照。live_intraday=True（盘中扫描用）时，日线还没今天的票会用分钟线补实时。"""
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

    # 空 targets 时 ThreadPoolExecutor(max_workers=0) 会抛 ValueError，把整轮 intraday
    # 打挂（2026-09-29 起实测：只开欧盘时 scan=0 → 每 5 分钟崩一次，告警全失效）。
    if not targets:
        return {}, sorted(set(gaps))

    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
        futures = {pool.submit(_fetch_one_snapshot, e, today, live_intraday): e for e in targets}
        for future in as_completed(futures):
            key, snapshot, gap = future.result()
            snapshots[key] = snapshot
            if gap:
                gaps.append(gap)
    return snapshots, sorted(set(gaps))
