#!/usr/bin/env python3
"""ir_download.py — Download IR filings from company investor relations pages.

Usage:
    python ir_download.py --ticker 5334.T --market jp --mode lite
    python ir_download.py --ticker MILDEF.ST --market se --mode lite

Flow:
    1. Print market-specific search queries for WebSearch
    2. Print IR page URL discovery instructions for Playwright
    3. Download PDFs when --url is provided (agent-extracted links)

Design:
    - Agent does WebSearch + Playwright (browser interaction)
    - This script handles search strategy, file naming, and downloads
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

# ── Market config ─────────────────────────────────────────────

MARKET_CONFIG = {
    "jp": {
        "name": "Japan",
        "language": "ja",
        "prefer_english": False,
        "lite_files": [
            {"type": "annual", "keywords": ["決算短信", "kessan tanshin", "financial results"], "format": "FY{year}-annual-tanshin.pdf"},
            {"type": "quarterly", "keywords": ["四半期決算短信", "quarterly", "Q1", "Q2", "Q3"], "format": "Q{quarter}-FY{year}-tanshin.pdf"},
        ],
        "full_extra": [
            {"type": "annual_report", "keywords": ["有価証券報告書", "annual securities report"], "format": "FY{year}-annual-securities-report.pdf"},
        ],
        "search_queries": [
            "{company_ja} IRライブラリ 決算短信",
            "{company_en} investor relations financial results",
        ],
        "ir_url_hints": ["/ir/library/", "/ir/financial/", "/investors/"],
    },
    "kr": {
        "name": "Korea",
        "language": "ko",
        "prefer_english": False,
        "lite_files": [
            {"type": "annual", "keywords": ["사업보고서", "business report", "annual report", "감사보고서"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["분기보고서", "quarterly", "IR자료"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_ko} IR 자료 사업보고서",
            "{company_en} investor relations annual report",
        ],
        "ir_url_hints": ["/ir/", "/investors/", "dart.fss.or.kr"],
        "fallback": "dart.fss.or.kr",
    },
    "tw": {
        "name": "Taiwan",
        "language": "zh",
        "prefer_english": False,
        "lite_files": [
            {"type": "annual", "keywords": ["合併財務報告", "年報", "annual report", "財務報告"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["季報", "quarterly", "合併季報"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_zh} 投資人關係 財務報告 年報",
            "{company_en} investor relations annual report",
        ],
        "ir_url_hints": ["/invest/", "/investor/", "mops.twse.com.tw"],
        "fallback": "mops.twse.com.tw",
    },
    "se": {
        "name": "Sweden",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["bokslutskommuniké", "year-end report", "full-year report", "Q4 report"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["delårsrapport", "interim report", "quarterly report", "Q1", "Q2", "Q3"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} year-end report 2025 PDF",
            "{company_en} bokslutskommuniké helår 2025",
        ],
        "ir_url_hints": ["/investors/", "/ir/", "/financial-reports/"],
    },
    "fr": {
        "name": "France",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["full-year results", "résultats annuels", "annual results", "year-end results"], "format": "FY{year}-annual-results.pdf"},
            {"type": "quarterly", "keywords": ["half-year results", "semestriel", "quarterly", "Q1", "Q2"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} full-year results 2025 PDF",
            "{company_en} résultats annuels 2025 PDF",
        ],
        "ir_url_hints": ["/investors/", "/finance/", "/publications/"],
    },
    "de": {
        "name": "Germany",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["annual report", "annual financial report", "Jahresabschluss", "Geschäftsbericht"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["quarterly statement", "half-year report", "Q1", "Q2", "Q3", "Quartalsmitteilung"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} annual report 2025 PDF",
            "{company_en} Geschäftsbericht 2025 PDF",
        ],
        "ir_url_hints": ["/investors/", "/investor-relations/", "/financial-reports/"],
    },
    "uk": {
        "name": "United Kingdom",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["preliminary results", "final results", "annual report", "full-year results"], "format": "FY{year}-annual-results.pdf"},
            {"type": "quarterly", "keywords": ["interim results", "half-year report", "trading update"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} preliminary results annual report 2025 PDF",
            "{company_en} final results 2025 PDF",
        ],
        "ir_url_hints": ["/investors/", "/results-reports/", "/financial-information/"],
    },
    "sg": {
        "name": "Singapore",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["annual report", "results announcement", "full-year results"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["quarterly", "half-year", "Q1", "Q2", "Q3"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} annual report FY2025 PDF Singapore",
            "{company_en} results announcement 2025",
        ],
        "ir_url_hints": ["/investors/", "links.sgx.com", "listedcompany.com"],
    },
    "my": {
        "name": "Malaysia",
        "language": "en",
        "prefer_english": True,
        "lite_files": [
            {"type": "annual", "keywords": ["annual report", "year ended", "financial statements"], "format": "FY{year}-annual-report.pdf"},
            {"type": "quarterly", "keywords": ["quarterly report", "quarterly results", "Q1", "Q2", "Q3"], "format": "Q{quarter}-FY{year}-report.pdf"},
        ],
        "search_queries": [
            "{company_en} annual report 2025 PDF",
            "{company_en} Bursa Malaysia annual report",
        ],
        "ir_url_hints": ["/investor-relations/", "disclosure.bursamalaysia.com"],
    },
}


def get_config(market: str) -> dict:
    cfg = MARKET_CONFIG.get(market)
    if not cfg:
        print(f"ERROR: unsupported market '{market}'. Supported: {list(MARKET_CONFIG)}", file=sys.stderr)
        sys.exit(1)
    return cfg


def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF from URL to dest. Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ir_download/1.0 (buy-side-research)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  FAIL download: {e}", file=sys.stderr)
        return False

    # Verify it's actually a PDF
    if not data[:4] == b"%PDF":
        print(f"  WARN: not a PDF ({len(data)} bytes, starts with {data[:50]!r})", file=sys.stderr)
        return False

    dest.write_bytes(data)
    mb = len(data) / (1024 * 1024)
    print(f"  OK  {mb:.1f}MB -> {dest}")
    return True


def cmd_search(args):
    """Print WebSearch queries and Playwright instructions for finding PDF links."""
    cfg = get_config(args.market)

    print(f"=== IR Download Plan: {args.ticker} ({cfg['name']}) ===\n")

    lang_hint = "English" if cfg["prefer_english"] else cfg["language"]
    print(f"Language preference: {lang_hint}\n")

    print("## Step 1: Search for IR page")
    for q in cfg["search_queries"]:
        print(f"  WebSearch: \"{q}\"")

    print(f"\n  URL hints to look for: {cfg['ir_url_hints']}")
    if cfg.get("fallback"):
        print(f"  Fallback: {cfg['fallback']}")

    print(f"\n## Step 2: Playwright navigate IR page -> find PDF links")
    print(f"  Look for filenames containing:")
    for f in cfg["lite_files"]:
        print(f"    [{f['type']}] keywords: {f['keywords']}")

    print(f"\n## Step 3: Download PDFs with --url")
    print(f"  For each PDF link found, run:")
    for f in cfg["lite_files"]:
        print(f"  python ir_download.py --ticker {args.ticker} --market {args.market} --url \"<PDF_URL>\" --type {f['type']} --dest-dir <path>")


def main():
    parser = argparse.ArgumentParser(description="IR filing downloader for buy-side-research-skills")
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g. 5334.T, MILDEF.ST)")
    parser.add_argument("--market", required=True, help="Market code: jp, kr, tw, se, fr, de, uk, sg, my")
    parser.add_argument("--mode", default="lite", choices=["lite", "full"], help="Lite=1 annual+1 quarterly, Full=5 annual+4 quarterly")
    parser.add_argument("--url", help="PDF download URL (from agent-extracted links)")
    parser.add_argument("--type", help="Filing type: annual, quarterly")
    parser.add_argument("--dest-dir", help="Destination directory for downloaded PDF")
    args = parser.parse_args()

    cfg = get_config(args.market)

    # --url mode: download a single PDF
    if args.url:
        if not args.dest_dir:
            print("ERROR: --dest-dir required with --url", file=sys.stderr)
            sys.exit(1)
        dest_dir = Path(args.dest_dir)
        ftype = args.type or "filing"
        ticker_slug = args.ticker.replace(".", "-").replace(":", "-").lower()
        dest = dest_dir / f"20260717-{ftype}-{ticker_slug}.pdf"
        ok = download_pdf(args.url, dest)
        sys.exit(0 if ok else 1)

    # Search mode: print plan
    cmd_search(args)


if __name__ == "__main__":
    main()
