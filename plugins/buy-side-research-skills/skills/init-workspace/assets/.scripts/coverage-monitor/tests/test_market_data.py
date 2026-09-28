"""盘中实时补充（分钟线补当天）的回归测试。

背景（2026-09-28 bug）：日线还没有"今天"这根时，快照给的是上一交易日收盘，
涨跌幅就是上一交易日的——涨停股 ≈+10% 越过 8% 阈值，导致每个交易日早上重复
推送昨天的涨停。修法：盘中用分钟线补出当天实时涨跌幅。
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from coverage_monitor import market_data


def _daily_frame(dates: list[str], closes: list[float], volumes: list[float]):
    return pd.DataFrame(
        {"Close": closes, "Volume": volumes},
        index=pd.DatetimeIndex([pd.Timestamp(d) for d in dates]),
    )


class _FakeTicker:
    """最小 yfinance.Ticker 替身：history() 返回预设的分钟线。"""

    def __init__(self, bars_by_interval):
        self._bars = bars_by_interval

    def history(self, period=None, interval=None, auto_adjust=False):
        return self._bars.get(interval, pd.DataFrame())


def _minute_frame(day: str, closes: list[float], tz="Asia/Shanghai", start_hour=9, start_min=30):
    idx = pd.DatetimeIndex(
        [pd.Timestamp(f"{day} {start_hour:02d}:{start_min + i:02d}:00").tz_localize(tz) for i in range(len(closes))]
    )
    return pd.DataFrame(
        {"Open": [closes[0]] * len(closes), "Close": closes, "Volume": [0.0] * len(closes)},
        index=idx,
    )


def _patch_yf(monkeypatch, bars_by_interval):
    import yfinance as yf

    monkeypatch.setattr(yf, "Ticker", lambda _sym: _FakeTicker(bars_by_interval))


# 2026-09-28 是周一；上一交易日 09-24（09-25 中秋休市、09-26/27 周末）
MONDAY_10AM_SH = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_live_intraday_computes_move_against_previous_session_close(monkeypatch):
    """分钟线补当天：涨跌幅 = (今天实时价 - 上一交易日收盘) / 上一交易日收盘。"""
    daily = _daily_frame(["2026-09-23", "2026-09-24"], [100.0, 110.0], [1000.0, 1000.0])
    _patch_yf(monkeypatch, {"1m": _minute_frame("2026-09-28", [115.5, 121.0])})

    out = market_data._live_intraday_snapshot("603067.SS", "603067.SS", daily, now=MONDAY_10AM_SH)

    assert out is not None
    assert out["market_time"] == "2026-09-28"
    assert out["prev_close"] == 110.0
    assert out["last_price"] == 121.0
    assert out["price_move_pct"] == pytest.approx(10.0, abs=0.01)  # 121/110 - 1


def test_live_intraday_skips_when_market_not_in_session(monkeypatch):
    """非交易时段没有"实时价"，不能拿上一交易日的分钟线冒充当天。"""
    daily = _daily_frame(["2026-09-23", "2026-09-24"], [100.0, 110.0], [1000.0, 1000.0])
    _patch_yf(monkeypatch, {"1m": _minute_frame("2026-09-28", [115.5, 121.0])})

    after_close = datetime(2026, 9, 28, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert market_data._live_intraday_snapshot("603067.SS", "603067.SS", daily, now=after_close) is None

    weekend = datetime(2026, 9, 26, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert market_data._live_intraday_snapshot("603067.SS", "603067.SS", daily, now=weekend) is None


def test_live_intraday_returns_none_when_no_bars_for_today(monkeypatch):
    """分钟线里没有今天（如台股休市/数据源断）→ None，不拿旧 bar 冒充。"""
    daily = _daily_frame(["2026-09-23", "2026-09-24"], [100.0, 110.0], [1000.0, 1000.0])
    _patch_yf(monkeypatch, {"1m": _minute_frame("2026-09-24", [115.5, 121.0]), "5m": pd.DataFrame()})

    assert market_data._live_intraday_snapshot("6213.TW", "6213.TW", daily, now=MONDAY_10AM_SH) is None


def test_live_intraday_falls_back_to_5m_when_1m_empty(monkeypatch):
    daily = _daily_frame(["2026-09-23", "2026-09-24"], [100.0, 110.0], [1000.0, 1000.0])
    _patch_yf(monkeypatch, {"1m": pd.DataFrame(), "5m": _minute_frame("2026-09-28", [110.0, 99.0])})

    out = market_data._live_intraday_snapshot("603067.SS", "603067.SS", daily, now=MONDAY_10AM_SH)

    assert out is not None
    assert out["interval"] == "5m"
    assert out["price_move_pct"] == pytest.approx(-10.0, abs=0.01)  # 99/110 - 1


def test_live_intraday_unknown_market_returns_none(monkeypatch):
    """未知市场（无法确定交易时段/时区）→ 不补，保持旧行为。"""
    daily = _daily_frame(["2026-09-23", "2026-09-24"], [100.0, 110.0], [1000.0, 1000.0])
    _patch_yf(monkeypatch, {"1m": _minute_frame("2026-09-28", [121.0])})

    assert market_data._live_intraday_snapshot("MYCR SS", "MYCR SS", daily, now=MONDAY_10AM_SH) is None
