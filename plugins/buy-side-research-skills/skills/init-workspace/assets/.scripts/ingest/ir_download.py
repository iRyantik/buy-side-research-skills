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
        "filing_keywords": ["決算短信", "kessan", "tanshin", "financial results", "earnings"],
        "steps": [
            {
                "id": "tdnet_direct",
                "title": "TDnet/kabupro direct URL",
                "queries": [
                    "{ticker_number} 決算短信 TDnet PDF",
                    "kabupro {ticker_number} 決算短信",
                    "{ticker_number} 通期決算短信 site:ke.kabupro.jp",
                ],
                "url_patterns": [
                    "http://ke.kabupro.jp/tsp/*/1401{ticker_number}*.pdf",
                    "https://www.release.tdnet.info/inbs/*{ticker_number}*.pdf",
                ],
                "action": "WebSearch with queries above → find PDF URL matching url_patterns → download with curl/Python urllib",
                "note": "TDnet PDFs are publicly accessible at kabupro.jp. Search by ticker number (omit .T suffix).",
            },
            {
                "id": "company_ir_playwright",
                "title": "Company IR page (Playwright)",
                "queries": [
                    "{ticker_number} 投資家情報 IR 決算短信",
                    "{ticker_number} IR library 決算短信 PDF",
                ],
                "action": "WebSearch → find company IR page URL → Playwright navigate → look for links containing 決算短信 or 'financial results' → download PDF",
                "note": "Most JP companies host PDFs on their IR library page. Look for 決算短信 or IR資料 links.",
            },
            {
                "id": "edinet_api",
                "title": "EDINET API",
                "action": "Use edinet-tools or EDINET API to find filing docID → get PDF URL → download",
                "note": "Requires EDINET_API_KEY. Gets 有価証券報告書 (annual securities report), not 決算短信.",
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
        "filing_keywords": ["사업보고서", "분기보고서", "감사보고서", "annual", "quarterly"],
        "steps": [
            {
                "id": "dart_playwright",
                "title": "DART — Playwright search + download",
                "queries": [],
                "action": (
                    "Playwright navigate: https://dart.fss.or.kr/dsae001/main.do\n"
                    "  a. Find the search input field (기업명 = company name or 종목코드 = stock code)\n"
                    "  b. Enter '{ticker_number}' (ticker without .KS suffix) as stock code\n"
                    "  c. Click 검색 (search) button\n"
                    "  d. In results, filter: select 사업보고서 (annual) in the 보고서 type dropdown\n"
                    "  e. Click the company name link → document viewer opens\n"
                    "  f. In viewer: click 인쇄 (print) / 다운로드 (download) button → save PDF\n"
                    "  OR use direct URL pattern: https://dart.fss.or.kr/dsaf001/main.do?rcpNo=YYYYMMDDNNNNNN"
                ),
                "note": (
                    "DART is Korea's official disclosure system (like SEC EDGAR). "
                    "Search by 8-digit ticker (e.g. '000660' for SK Hynix, '012450' for Hanwha). "
                    "The 사업보고서 (annual business report) has the most complete financials + segment data."
                ),
            },
            {
                "id": "dart_api",
                "title": "DART API → viewer URL",
                "action": (
                    "Use DART_API_KEY (from .env) to search: "
                    "https://opendart.fss.or.kr/api/search.json?crtfc_key=KEY&crp_cd={ticker_number}&page_set=100\n"
                    "→ parse JSON for 사업보고서 rcp_no\n"
                    "→ construct viewer URL: https://dart.fss.or.kr/dsaf001/main.do?rcpNo=RCP_NO\n"
                    "→ Playwright navigate → click 다운로드 → save PDF"
                ),
                "note": "DART API returns ZIP with XML, not PDF. Use API only to find rcp_no, then Playwright to download.",
            },
            {
                "id": "company_ir",
                "title": "Company IR page",
                "queries": ["{ticker_number} IR 투자정보 실적발표", "{ticker_number} investor relations annual report"],
                "action": "WebSearch → Playwright company IR page → find PDF → download",
                "note": "Large KR companies may host English IR presentations. These have less detail than 사업보고서.",
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
        "filing_keywords": ["財務報告", "合併", "annual report", "financial statements", "年報"],
        "steps": [
            {
                "id": "mops_english",
                "title": "English MOPS — Playwright search + direct PDF download",
                "queries": [],
                "action": (
                    "Playwright navigate: https://emops.twse.com.tw/server-java/t58query\n"
                    "  a. Find search box 'Pls Input Company Name/Code' → enter '{ticker_number}' (4-digit TW code)\n"
                    "  b. Click search → company overview page opens\n"
                    "  c. Click 'Electronic Books' → document list page (doc.twse.com.tw)\n"
                    "  d. Find latest Q4/AIA PDF (e.g. 202504_{ticker_number}_AIA.pdf)\n"
                    "  e. Click PDF link → PDF opens in browser\n"
                    "  f. Python urllib download from the PDF URL\n"
                    "  OR construct download URL: https://doc.twse.com.tw/server-java/FileDownLoad?step=9&kind=A&co_id={ticker_number}&filename=202504_{ticker_number}_AIA.pdf"
                ),
                "note": (
                    "English MOPS (emops.twse.com.tw) is easier than Chinese MOPS. "
                    "The Electronic Books page lists quarterly AIA (individual) and AIC (consolidated) PDFs. "
                    "Use the JS readfile() function or construct the download URL with session cookies."
                ),
            },
            {
                "id": "mops_chinese",
                "title": "MOPS Chinese — Playwright form",
                "action": (
                    "Fallback: Playwright → mops.twse.com.tw → search '{ticker_number}' → "
                    "find 財務報告 PDF → download"
                ),
                "note": "Chinese MOPS actively blocks non-browser requests. Use English MOPS instead.",
            },
            {
                "id": "company_ir",
                "title": "Company IR page",
                "queries": ["{ticker_number} 投資人關係 財務報告 PDF", "{ticker_number} investor relations annual report"],
                "action": "WebSearch → Playwright company IR page → find PDF → download",
                "note": "Some TW companies host English financials on their IR pages. Yageo uses JS SPA with no direct PDF links.",
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
        "lite_files": ["Year-end report (annual report / bokslutskommunike / full-year results) — 20-40 pages"],
        "filing_keywords": ["annual report", "year-end report", "financial statements", "annual results", "full-year"],
        "steps": [
            {
                "id": "company_ir_playwright",
                "title": "Company IR page — Playwright",
                "queries": [
                    "{company_en} investor relations annual report",
                    "{company_en} annual report PDF site:ir",
                    "{ticker} financial results annual report",
                ],
                "action": (
                    "WebSearch with queries above → find company IR/reports page URL\n"
                    "→ Playwright navigate → look for PDF links with keywords: "
                    "'Annual Report', 'Year-End Report', 'Financial Statements', 'Årsredovisning' (SE), "
                    "'Geschäftsbericht' (DE), 'Rapport Annuel' (FR)\n"
                    "→ click/download the latest annual report PDF"
                ),
                "note": "EU companies almost always have English IR pages. Prefer annual report for full financials + segment.",
            },
            {
                "id": "websearch_direct",
                "title": "WebSearch direct PDF URL",
                "queries": [
                    "{ticker} annual report filetype:pdf",
                    "{company_en} annual report PDF",
                ],
                "action": "WebSearch → find direct PDF URL on cision.com, eqs-news.com, or company site → download with urllib",
                "note": "Some EU companies post PDFs to Cision/EQS news services with direct links.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic financials.",
            },
        ],
    },
    "hk": {
        "name": "Hong Kong",
        "lite_files": ["全年業績公告 (Annual Results Announcement) — 30-40 pages, IS/BS/CF + segment"],
        "full_files": ["全年業績公告 + 中期業績公告 × 2 — annual + H1 reports"],
        "filing_keywords": ["annual results", "業績公告", "interim report", "annual report"],
        "steps": [
            {
                "id": "company_ir_playwright",
                "title": "Company IR page — Playwright (primary)",
                "queries": [
                    "{ticker_number} HK annual results PDF investor relations",
                    "{ticker_number} 全年業績公告 PDF",
                    "{ticker_number} HKEX annual report",
                ],
                "action": (
                    "WebSearch with queries above → find company IR/reports page URL\n"
                    "→ Playwright navigate → look for PDF links with keywords:\n"
                    "  'Annual Results', '全年業績', 'Final Results', '年度業績'\n"
                    "→ click/download the latest annual results PDF"
                ),
                "note": (
                    "HK companies almost always host Annual Results PDFs on their own IR pages. "
                    "This is the easiest path — same pattern as JP TDnet and EU company IR. "
                    "The Results Announcement has full IFRS IS/BS/CF + HKFRS 8 segment breakdown."
                ),
            },
            {
                "id": "hkexnews_fallback",
                "title": "HKEXnews — Playwright form search (fallback)",
                "queries": [],
                "action": (
                    "⚠️ HKEXnews blocks direct URL access. Must use the JS search form.\n"
                    "Playwright → https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en\n"
                    "→ enter '{ticker_number}' in Stock Code combobox\n"
                    "→ select 'Annual Results' under Headline Category\n"
                    "→ click SEARCH → find filing → click to open PDF → download"
                ),
                "note": "Only use if company IR page doesn't have the PDF. HKEXnews has JS anti-scraping.",
            },
            {
                "id": "yfinance_fallback",
                "title": "yfinance (last resort)",
                "action": "No PDF — use yfinance for basic financials. No segment detail.",
            },
        ],
    },
    "us": {
        "name": "United States",
        "lite_files": ["10-K (annual) + latest 10-Q (quarterly) — XBRL via API, PDF optional for commentary"],
        "full_files": ["10-K + 10-Q × 3 — 5Y annual + 4Q data via API"],
        "filing_keywords": ["10-K", "10-Q", "earnings release", "annual report"],
        "steps": [
            {
                "id": "sec_edgar",
                "title": "SEC EDGAR — direct PDF",
                "queries": [],
                "action": (
                    "API already provides structured IS/BS/CF/segment from XBRL.\n"
                    "Only download PDF if management commentary/MD&A is needed.\n\n"
                    "EDGAR search: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K\n"
                    "Or construct URL: https://www.sec.gov/Archives/edgar/data/CIK/...\n\n"
                    "Simpler alternative: 8-K Exhibit 99.1 (Earnings Release)\n"
                    "  — 20-30 pages with IS/BS tables + segment + management commentary\n"
                    "  — Available on EDGAR under 8-K filings"
                ),
                "note": "SEC EDGAR XBRL via API is primary. PDF only for MD&A/commentary supplement.",
            },
            {
                "id": "company_ir",
                "title": "Company IR page",
                "queries": ["{ticker} investor relations earnings release PDF", "{ticker} annual report PDF"],
                "action": "WebSearch → Playwright company IR page → find PDF → download",
                "note": "US companies often host earnings releases and 10-K PDFs on their IR pages.",
            },
        ],
    },
    "cn": {
        "name": "China A-Share",
        "lite_files": ["年报 + 最新季报 — structured data via API, PDF optional for verification"],
        "full_files": ["年报 + 季报×3 + 半年报 — 5Y via API"],
        "filing_keywords": ["年报", "季报", "半年报", "年度报告"],
        "steps": [
            {
                "id": "cninfo_pdf",
                "title": "巨潮资讯网 (CNINFO) — official disclosure",
                "queries": [],
                "action": (
                    "API (AKShare) already provides full structured IS/BS/CF/segment.\n"
                    "PDF only for verification or management discussion.\n\n"
                    "CNINFO search: http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice\n"
                    "  Enter stock code '{ticker_number}' → filter 年度报告 / 季度报告\n"
                    "OR: http://static.cninfo.com.cn/ → construct URL from filing ID"
                ),
                "note": "AKShare structured data is comprehensive. PDF only for verification.",
            },
            {
                "id": "eastmoney_ir",
                "title": "东方财富 / Company IR",
                "queries": ["{ticker_number} 年报 PDF", "{ticker_number} 年度报告"],
                "action": "WebSearch → Playwright → find PDF → download",
                "note": "Eastmoney and Sina Finance host A-share annual reports.",
            },
        ],
    },
}

# EU sub-markets all use the same chain (deep copy)
EU_NAMES = {"se": "Sweden", "fr": "France", "de": "Germany", "uk": "UK",
            "sg": "Singapore", "my": "Malaysia", "in": "India", "au": "Australia"}
API_PDF_NAMES = {"hk": "Hong Kong (supplement)", "us": "United States (supplement)", "cn": "China A-Share (supplement)"}
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
        company_hint = args.ticker.split(".")[0]
        action = step["action"].replace("{ticker_number}", ticker_num).replace("{ticker}", args.ticker).replace("{company_en}", company_hint).replace("{name_ko}", "")
        print(f"  {action}")
        if step.get("note"):
            note = step["note"].replace("{ticker_number}", ticker_num).replace("{ticker}", args.ticker).replace("{company_en}", company_hint)
            print(f"  Note: {note}")
        if step.get("queries"):
            queries = [q.replace("{ticker_number}", ticker_num).replace("{ticker}", args.ticker).replace("{company_en}", company_hint) for q in step["queries"]]
            print(f"  Queries: {', '.join(queries)}")
        print()
    print("When PDFs are downloaded, run /financial-data to continue the chain.")
    print(f"  /financial-data {args.ticker} --market {args.market} --mode {args.mode} --company-slug <slug> --industry <industry>")


if __name__ == "__main__":
    main()
