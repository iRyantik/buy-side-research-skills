from coverage_monitor.tickers import build_ticker_runtime


def test_display_ticker_to_yfinance_quote_ticker():
    cases = {
        "SPCX US": "SPCX",
        "0522 HK": "0522.HK",
        "6777 JP": "6777.T",
        "012450 KS": "012450.KS",
        "688097 CH": "688097.SS",
        "2305 TW": "2305.TW",
        "MYCR SS": "MYCR.ST",
        "BESI NA": "BESI.AS",
    }
    for display, expected in cases.items():
        assert build_ticker_runtime(display, "Company").quote_ticker == expected


def test_multi_ticker_uses_first_for_quote_and_all_for_search():
    runtime = build_ticker_runtime("002487 CH / 1081 HK", "Dajin")
    assert runtime.quote_ticker == "002487.SZ"
    assert runtime.search_aliases == ("002487 CH", "1081 HK", "Dajin")


def test_ipo_pending_is_not_quoteable():
    runtime = build_ticker_runtime("IPO pending", "Lieqi")
    assert not runtime.is_quoteable
    assert runtime.gap == "non_quote_ticker"

