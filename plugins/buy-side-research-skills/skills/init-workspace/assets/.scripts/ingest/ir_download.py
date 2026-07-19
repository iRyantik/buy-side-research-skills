#!/usr/bin/env python3
"""ir_download.py — Download IR filings with market-specific fallback chains.

Usage:
    python ir_download.py --ticker 6777.T --market jp --mode lite   (prints plan)
    python ir_download.py --ticker 6777.T --market jp --url <URL> --type annual --dest-dir <path>
    python ir_download.py --ticker 6777.T --market jp --status        (check progress)

The script prints a numbered checklist for the agent. Each market has a chain of
strategies tried in order until PDFs are obtained. Agent reports success/failure
after each step.
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Market chains ─────────────────────────────────────────────

CHAINS = {
    "jp": {
        "name": "Japan",
        "lite_files": ["決算短信 (kessan tanshin) — ~20 pages, concise"],
        "full_files": ["決算短信 + 有価証券報告書 — annual + quarterly"],
        "steps": [
            {
                "id": "tdnet_direct",
                "title": "TDnet/kabupro direct URL",
                "action": "WebSearch '{ticker_number} 決算短信 TDnet PDF' → find PDF URL → download with curl/Python",
                "note": "TDnet PDFs are publicly accessible. If URL found, use --url to download.",
            },
            {
                "id": "company_ir_playwright",
                "title": "Company IR page (Playwright)",
                "action": "WebSearch company IR page → Playwright navigate → find 決算短信 PDF link → download",
                "note": "Many JP companies host PDFs on their IR library page.",
            },
            {
                "id": "edinet_api",
                "title": "EDINET API",
                "action": "Use edinet-tools or EDINET API to find filing → get URL → download",
                "note": "Requires EDINET_API_KEY. Gets 有価証券報告書 not 決算短信.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic market data + financials",
                "note": "No segment detail. Mark source_layer=yfinance.",
            },
        ],
    },
    "kr": {
        "name": "Korea",
        "lite_files": ["분기보고서 (quarterly) — ~40 pages", "사업보고서 (annual) — ~100 pages"],
        "full_files": ["사업보고서 + 분기보고서 × 4"],
        "steps": [
            {
                "id": "dart_playwright",
                "title": "DART — Playwright search",
                "action": "Playwright → dart.fss.or.kr → search '{ticker_number}' or '{name_ko}' → filter 사업보고서/분기보고서 → click download",
                "note": "DART is the official disclosure system. Search by ticker (e.g. '000660') not company name.",
            },
            {
                "id": "dart_api",
                "title": "DART API fallback",
                "action": "Use DART_API_KEY to find filing rcp_no → Playwright viewer → download PDF",
                "note": "DART API returns ZIP with XML, not PDF. Need viewer for actual PDF.",
            },
            {
                "id": "company_ir",
                "title": "Company IR page",
                "action": "WebSearch → Playwright company IR page → find PDF",
                "note": "Large KR companies may have IR pages with presentations.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic financials. No segment detail.",
            },
        ],
    },
    "tw": {
        "name": "Taiwan",
        "lite_files": ["合併財務報告 — quarterly/annual financial report"],
        "steps": [
            {
                "id": "mops_playwright",
                "title": "MOPS — Playwright search",
                "action": "Playwright → mops.twse.com.tw → search '{ticker_number}' → find 財務報告 PDF → download",
                "note": "MOPS is the official TW disclosure platform.",
            },
            {
                "id": "company_ir",
                "title": "Company IR page",
                "action": "WebSearch company IR page → Playwright → find PDF → download",
                "note": "Some TW companies host PDFs on their own IR pages.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic financials.",
            },
        ],
    },
    "eu": {
        "name": "Europe",
        "lite_files": ["Year-end report (bokslutskommunike / full-year results / annual report) — 20-40 pages"],
        "steps": [
            {
                "id": "company_ir_playwright",
                "title": "Company IR page — Playwright (English)",
                "action": "WebSearch '{company_en} investor relations annual report' → Playwright → find English PDF → download",
                "note": "EU companies almost always have English IR pages. Prefer year-end report over full annual report.",
            },
            {
                "id": "websearch_direct",
                "title": "WebSearch direct PDF URL",
                "action": "WebSearch '{ticker} annual report PDF filetype:pdf' → find direct URL → download",
                "note": "Some EU companies post PDFs to Cision/EQS with direct links.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic financials.",
            },
        ],
    },
}

# EU sub-markets all use the same chain (deep copy)
EU_NAMES = {"se": "Sweden", "fr": "France", "de": "Germany", "uk": "UK",
            "sg": "Singapore", "my": "Malaysia", "in": "India", "au": "Australia"}
for m in EU_NAMES:
    import copy
    CHAINS[m] = copy.deepcopy(CHAINS["eu"])
    CHAINS[m]["name"] = EU_NAMES[m]


# ── Download ──────────────────────────────────────────────────

def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF from URL to dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ir_download/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  FAIL: {e}", file=sys.stderr)
        return False
    if not data[:4] == b"%PDF":
        print(f"  WARN: not a PDF ({len(data)} bytes)", file=sys.stderr)
        return False
    dest.write_bytes(data)
    print(f"  OK {len(data)/1024/1024:.1f}MB -> {dest}")
    return True


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="IR filing downloader")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--market", required=True, choices=sorted(CHAINS.keys()))
    parser.add_argument("--mode", default="lite", choices=["lite", "full"])
    parser.add_argument("--url", help="Direct PDF URL to download")
    parser.add_argument("--type", help="Filing type for --url: annual, quarterly")
    parser.add_argument("--dest-dir", help="Destination directory for --url download")
    parser.add_argument("--status", action="store_true", help="Check what PDFs exist")
    args = parser.parse_args()

    chain = CHAINS[args.market]
    ticker_num = args.ticker.split(".")[0]

    # --url mode: download a single PDF
    if args.url:
        if not args.dest_dir:
            print("ERROR: --dest-dir required with --url", file=sys.stderr)
            sys.exit(1)
        ftype = args.type or "filing"
        dest = Path(args.dest_dir) / f"20260719-{ftype}-{ticker_num}.pdf"
        ok = download_pdf(args.url, dest)
        sys.exit(0 if ok else 1)

    # --status mode: check existing PDFs
    if args.status:
        if not args.dest_dir:
            print("ERROR: --dest-dir required with --status", file=sys.stderr)
            sys.exit(1)
        pdfs = sorted(Path(args.dest_dir).glob("*.pdf"))
        print(f"PDFs: {len(pdfs)}")
        for p in pdfs:
            print(f"  {p.name} ({p.stat().st_size/1024:.0f}KB)")
        sys.exit(0 if pdfs else 1)

    # Plan mode: print chain
    print(f"=== IR Download: {args.ticker} ({chain['name']}, {args.mode}) ===")
    print()
    print(f"Target files ({args.mode}):")
    for f in chain[args.mode + "_files"]:
        print(f"  - {f}")
    print()
    print("## Download chain")
    print("  Try each step in order. Stop when PDFs are obtained.")
    print()
    for i, step in enumerate(chain["steps"], 1):
        print(f"### Step {i}: {step['title']}")
        action = step["action"].replace("{ticker_number}", ticker_num).replace("{ticker}", args.ticker)
        print(f"  {action}")
        print(f"  Note: {step['note']}")
        print()
    print("When PDFs are downloaded, run /financial-data to continue the chain.")
    print(f"  /financial-data {args.ticker} --market {args.market} --mode {args.mode} --company-slug <slug> --industry <industry>")


if __name__ == "__main__":
    main()
