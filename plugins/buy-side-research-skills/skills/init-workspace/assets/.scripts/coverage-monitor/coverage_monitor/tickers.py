from __future__ import annotations

from dataclasses import dataclass
import re


NON_QUOTE_TOKENS = {
    "",
    "ipo pending",
    "private",
    "no listed ticker",
    "no ticker",
    "no-ticker",
    "n/a",
    "na",
}


@dataclass(frozen=True)
class TickerRuntime:
    display_ticker: str
    quote_ticker: str
    search_aliases: tuple[str, ...]
    is_quoteable: bool
    gap: str = ""


def _split_display_tickers(display_ticker: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\s*/\s*|[,;]", display_ticker.strip()) if part.strip()]
    return parts or [display_ticker.strip()]


def _convert_single_ticker(display_ticker: str) -> str:
    value = display_ticker.strip()
    if not value or value.lower() in NON_QUOTE_TOKENS:
        return ""
    compact = re.sub(r"\s+", " ", value.upper())
    if "." in compact and " " not in compact:
        return compact
    pieces = compact.split(" ")
    if len(pieces) == 1:
        return pieces[0]
    symbol = "".join(pieces[:-1])
    market = pieces[-1]
    suffix_by_market = {
        "US": "",
        "HK": ".HK",
        "JP": ".T",
        "KS": ".KS",
        "KQ": ".KQ",
        "TW": ".TW",
        "SS": ".ST",
        "SE": ".ST",
        "NA": ".AS",
        "NL": ".AS",
        "DE": ".DE",
        "LN": ".L",
        "L": ".L",
        "UK": ".L",
        "MK": ".KL",
        "MY": ".KL",
    }
    if market in {"CH", "CN"}:
        if symbol.startswith(("0", "2", "3")):
            return f"{symbol}.SZ"
        return f"{symbol}.SS"
    if market == "HK" and symbol.isdigit():
        symbol = symbol.zfill(4)
    suffix = suffix_by_market.get(market)
    if suffix is None:
        return compact.replace(" ", ".")
    return f"{symbol}{suffix}"


def build_ticker_runtime(display_ticker: str, company: str = "") -> TickerRuntime:
    display = display_ticker.strip()
    aliases = []
    for item in _split_display_tickers(display):
        if item and item.lower() not in NON_QUOTE_TOKENS:
            aliases.append(item)
    if company.strip():
        aliases.append(company.strip())
    primary_display = _split_display_tickers(display)[0].strip()
    quote = _convert_single_ticker(primary_display)
    if not quote:
        gap = "non_quote_ticker" if display else "missing_ticker"
        return TickerRuntime(display_ticker=display, quote_ticker="", search_aliases=tuple(dict.fromkeys(aliases)), is_quoteable=False, gap=gap)
    return TickerRuntime(display_ticker=display, quote_ticker=quote, search_aliases=tuple(dict.fromkeys(aliases)), is_quoteable=True)

