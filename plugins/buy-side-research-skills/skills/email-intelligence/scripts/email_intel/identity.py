"""Canonical identity helpers shared by classification, merging and rendering.

Tickers follow the workspace FMP passthrough convention (see CLAUDE.md 3.2):
``.SS`` / ``.SZ`` for China, ``.T`` for Japan, ``.L`` for London, ``.PA`` for
Paris, ``.OL`` for Oslo, etc.  Historical/sell-side variants (``.CH``, ``.JP``,
``.LN``, ``.FP``, ``.NO``, ``.SH``) are normalised to the canonical suffix.
"""

from __future__ import annotations

import re


def _norm_ascii(value: object) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").casefold())


def normalize_ticker(value: object) -> str:
    """Return the FMP-style canonical ticker (``300316.CH`` -> ``300316.SZ``)."""
    raw = re.sub(r"\s+", "", str(value or "")).upper()
    if not raw:
        return ""
    base = raw
    suffix = ""
    m = re.match(r"^([A-Z0-9.-]+?)(\.[A-Z]{1,3})$", raw)
    if m:
        base, suffix = m.group(1), m.group(2)
    alias = {
        ".CH": None,  # resolved from the numeric prefix below
        ".JP": ".T",
        ".LN": ".L",
        ".FP": ".PA",
        ".NO": ".OL",
        ".SH": ".SS",
    }.get(suffix, suffix)
    if suffix == ".CH" and base.isdigit():
        alias = ".SS" if base.startswith("6") else (".SZ" if base.startswith(("0", "3")) else ".CH")
    return f"{base}{alias}" if alias else base


def company_key(value: object) -> str:
    return _norm_ascii(value)


def industry_key(value: object) -> str:
    return _norm_ascii(value)


def industry_label(value: object, covered_industries: list | None = None) -> str:
    """Prefer the COVERAGE.md spelling when it matches the value's identity."""
    raw = str(value or "").strip() or "Other"
    identity = industry_key(raw)
    if not identity:
        return raw
    for covered in covered_industries or []:
        label = str(covered or "").strip()
        if label and industry_key(label) == identity:
            return label
    return raw


def normalize_related(values: list | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        raw = str(value or "").strip()
        if not raw:
            continue
        ticker = normalize_ticker(raw)
        out.append(ticker or company_key(raw))
    return out
