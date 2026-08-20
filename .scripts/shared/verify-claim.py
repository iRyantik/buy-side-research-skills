#!/usr/bin/env python3
"""verify-claim.py — unified source verification chain.

Orchestrates the Tier 1→2→3→4 fallback for any web claim URL.
Returns structured output so consuming skills don't need to
re-implement the chain.

Usage:
  python verify-claim.py <url>                    # auto-tier, plain text
  python verify-claim.py <url> --json             # structured JSON output
  python verify-claim.py <url> --tier 1           # HTTP only, no fallback
  python verify-claim.py <url> --json --ledger <artifact-or-dir> -t <TICKER>
                                                  # also stage the result for evidence ledger
                                                  # (.cache/evidence/<TICKER>.verify-staging.json)
  python verify-claim.py <url> --claim-text "<quote>" --ledger <dir> -t <TICKER> --apply
                                                  # require page text to substantiate the
                                                  # claim; apply-staging immediately after

Tier chain:
  Tier 1 — HTTP GET (urllib, no auth, 30s timeout)
  Tier 2 — browser-harness CDP (real Chrome, auto, bypasses Cloudflare/JS)
  Tier 3 — Playwright MCP required (script prints instruction for agent)
  Tier 4 — curl subprocess (last resort)
  Tier 5 — [UNVERIFIED] (nothing worked)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError


# Domains known to return HTTP 403 with anti-bot protection
# Tier 1 is skipped for these; verification routes directly to Tier 2 (CDP)
KNOWN_403_DOMAINS = {
    "marketscreener.com", "tipranks.com", "simplywall.st",
    "macrotrends.net", "stockanalysis.com", "financecharts.com",
    "finviz.com", "tradingview.com", "wsj.com",
    "perplexity.ai", "x.com", "twitter.com",
}


def _should_skip_tier1(url: str) -> bool:
    return any(d in url for d in KNOWN_403_DOMAINS)


# ── Tier 1: HTTP ────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Extract visible text from HTML, preserving paragraph breaks."""
    def __init__(self):
        super().__init__()
        self.text: list[str] = []
        self._block_tags = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                            "li", "tr", "br", "hr", "section", "article", "pre",
                            "table", "blockquote"}

    def handle_starttag(self, tag, attrs):
        if tag in self._block_tags:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in self._block_tags:
            self.text.append("\n")

    def handle_data(self, data):
        s = data.strip()
        if s:
            self.text.append(s + " ")

    def get_text(self) -> str:
        raw = "".join(self.text)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        # Remove script/style residue (belt-and-suspenders)
        raw = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r'<[^>]+>', '', raw)  # strip any remaining HTML tags
        return raw.strip()


def _text_matches(page_text: str, claim_text: str) -> bool:
    """Does the page text substantiate the claim?

    Whole-claim containment after normalization; for short claims fall back to
    token majority (≥60% of significant tokens present). Strip markdown noise
    from both sides so a claim copied from an artifact line still matches.
    """
    norm = lambda s: re.sub(r'\s+', ' ', re.sub(r'[#*_`>|\[\]()]', '', s or '')).lower()
    page, claim = norm(page_text), norm(claim_text)
    if not claim:
        return False
    if claim in page:
        return True
    tokens = [t for t in claim.split() if len(t) > 2]
    if not tokens:
        return False
    hits = sum(1 for t in tokens if t in page)
    return hits / len(tokens) >= 0.6


def _tier1_http(url: str) -> tuple[str | None, str | None]:
    """HTTP GET, extract visible text. Returns (text, error)."""
    try:
        req = Request(url, headers={"User-Agent": "verify-claim/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", content_type)
        if m:
            charset = m.group(1)
        html = data.decode(charset, errors="replace")

        # Check if it's HTML — if Content-Type says JSON/PDF/etc, return raw
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return html[:10000], None  # raw text, truncated

        extractor = _TextExtractor()
        extractor.feed(html)
        text = extractor.get_text()
        if len(text) < 100:
            return None, "Extracted text too short (<100 chars) — likely JS-rendered page"
        return text, None
    except URLError as e:
        return None, f"HTTP fetch failed: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ── Tier 2: browser-harness CDP ──────────────────────────

def _tier2_cdp(url: str) -> tuple[str | None, str | None]:
    """browser-harness CDP — connects to user's real Chrome.
    Bypasses Cloudflare, handles JS-rendered pages that Tier 1 misses.
    Runs automatically as a subprocess — no agent intervention needed."""
    script = Path(__file__).parent / "browser-cdp.py"
    if not script.exists():
        return None, "browser-cdp.py not found in shared scripts"

    try:
        r = subprocess.run(
            [sys.executable, str(script), "extract", url],
            capture_output=True, text=True, timeout=45,
            encoding="utf-8",
        )
        if r.returncode == 0 and len(r.stdout.strip()) > 100:
            return r.stdout.strip()[:10000], None
        err = r.stderr.strip() or r.stdout.strip()
        return None, f"CDP extraction failed: {err[:300]}"
    except subprocess.TimeoutExpired:
        return None, "CDP timed out after 45s"
    except Exception as e:
        return None, f"CDP error: {e}"


# ── Tier 3: Playwright MCP ─────────────────────────────

def _tier3_instruction(url: str) -> str:
    """Return the instruction for the agent to use Playwright MCP."""
    return (
        f"Tier 3 — Playwright MCP required:\n"
        f"  browser_navigate → {url}\n"
        f"  browser_snapshot → capture page text\n"
        f"  Feed the snapshot text back to: python verify-claim.py {url} --playwright-text \"<text>\""
    )


# ── Tier 4: curl ────────────────────────────────────────

def _tier4_curl(url: str) -> tuple[str | None, str | None]:
    """curl subprocess fallback. Returns (text, error)."""
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "30", "-A", "verify-claim/1.0", url],
            capture_output=True, text=True, timeout=35
        )
        if r.returncode != 0:
            return None, f"curl exited {r.returncode}: {r.stderr[:200]}"
        text = r.stdout.strip()
        if len(text) < 50:
            return None, "curl returned too little content"
        # Strip HTML tags for readability
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text[:10000], None
    except FileNotFoundError:
        return None, "curl not installed"
    except Exception as e:
        return None, f"curl error: {e}"


# ── Evidence ledger staging ─────────────────────────────

# Tier label → int (single int tier in the ledger; strings only in CLI output)
_TIER_INT = {"WebFetch": 1, "curl": 1, "browser-harness CDP": 2, "Playwright": 2}


def _resolve_staging_path(ledger_arg: str, ticker: str) -> "Path":
    """Resolve .cache/evidence/<TICKER>.verify-staging.json next to the ticker ledger.

    Reuses evidence_ledger._ticker_to_ledger_path's directory resolution so the
    staging file always lands in the same .cache/evidence/ dir as the ledger.
    """
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir.parent))
    from evidence_ledger import _ticker_to_ledger_path  # noqa: E402
    ledger_path = _ticker_to_ledger_path(ledger_arg, ticker)
    return ledger_path.with_name(ticker + ".verify-staging.json")


def stage_result(ledger_arg: str, ticker: str, result: dict) -> str:
    """Append/merge a verification result into the ticker's staging file.

    Dedups by URL — re-verifying the same URL replaces its staging entry.
    """
    staging_path = _resolve_staging_path(ledger_arg, ticker)
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging = {"schema": 2, "ticker": ticker, "entries": []}
    if staging_path.exists():
        try:
            with open(staging_path, "r", encoding="utf-8") as f:
                staging = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # corrupted staging — start fresh, honest rebuild
    entry = {
        "url": result.get("url", ""),
        "status": result.get("status", "unverified"),
        # schema 2: int tier + human label; schema 1 used the label as tier
        "tier": _TIER_INT.get(result.get("tier")),
        "method": result.get("tier") or "unknown",
        "matched": result.get("matched"),
        "text": (result.get("text") or "")[:2000],
        "error": (result.get("error") or result.get("next_action") or "")[:200],
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    staging["entries"] = [e for e in staging.get("entries", []) if e.get("url") != entry["url"]]
    staging["entries"].append(entry)
    with open(staging_path, "w", encoding="utf-8") as f:
        json.dump(staging, f, indent=2, ensure_ascii=False)
    return str(staging_path)


# ── main ────────────────────────────────────────────────

def _finish(result: dict, text: str, tier_label: str, claim_text: str | None):
    """Fill a successful tier result; with --claim-text verify substantiation."""
    result["status"] = "verified"
    result["tier"] = tier_label
    result["text"] = text[:10000]
    if claim_text:
        result["matched"] = _text_matches(text, claim_text)
        if not result["matched"]:
            # page reachable but claim not found — distinct from verified
            result["status"] = "reachable"
    return result


def verify(url: str, max_tier: int = 4,
           playwright_text: str | None = None,
           cdp_text: str | None = None,
           claim_text: str | None = None) -> dict:
    """Run the verification chain. Returns structured result.

    With claim_text, status is "verified" only when the page text substantiates
    the claim; a reachable page that does not is "reachable" (applied to the
    ledger as a non-matching attempt, never an upgrade).
    """
    result: dict = {
        "url": url,
        "status": "unverified",
        "tier": None,
        "text": None,
        "error": None,
        "next_action": None,
        "matched": None,
    }

    # If text was provided from a previous retry
    if playwright_text:
        return _finish(result, playwright_text, "Playwright", claim_text)

    if cdp_text:
        return _finish(result, cdp_text, "browser-harness CDP", claim_text)

    # Tier 1: HTTP (skip if known 403 domain)
    if max_tier >= 1:
        if _should_skip_tier1(url):
            result["tier1_error"] = "skipped — known 403 domain, routing to Tier 2"
        else:
            text, err = _tier1_http(url)
            if text:
                return _finish(result, text, "WebFetch", claim_text)
            result["tier1_error"] = err

    # Tier 2: browser-harness CDP (auto, no agent intervention needed)
    if max_tier >= 2:
        text, err = _tier2_cdp(url)
        if text:
            return _finish(result, text, "browser-harness CDP", claim_text)
        result["tier2_error"] = err

    # Tier 3: Playwright MCP (requires agent)
    if max_tier >= 3:
        result["next_action"] = _tier3_instruction(url)
        return result

    # Tier 4: curl
    if max_tier >= 4:
        text, err = _tier4_curl(url)
        if text:
            return _finish(result, text, "curl", claim_text)
        result["tier4_error"] = err

    # Tier 5: nothing worked
    result["status"] = "unverified"
    result["tier"] = None
    result["error"] = "All tiers exhausted"
    return result


def cli():
    parser = argparse.ArgumentParser(
        description="Unified source verification chain"
    )
    parser.add_argument("url", help="URL to verify")
    parser.add_argument("--tier", type=int, default=4,
                       help="Max tier (1=HTTP, 2=CDP, 3=Playwright, 4=curl, default: 4)")
    parser.add_argument("--json", action="store_true",
                       help="Output structured JSON")
    parser.add_argument("--playwright-text", default=None,
                       help="Playwright snapshot text (from Tier 3 retry)")
    parser.add_argument("--cdp-text", default=None,
                       help="browser-harness CDP extracted text (from Tier 2 retry)")
    parser.add_argument("--claim-text", default=None,
                       help="Expected claim text/quote — page text must contain "
                            "it to count as matched; reachable-but-not-matched "
                            "is reported as status 'reachable' (exit 1)")
    parser.add_argument("--ledger", default=None,
                       help="Evidence ledger target: artifact path or company dir. "
                            "Stages the result to .cache/evidence/<TICKER>.verify-staging.json")
    parser.add_argument("--apply", action="store_true",
                       help="With --ledger: run apply-staging immediately after staging")
    parser.add_argument("-t", "--ticker", default=None,
                       help="Ticker for ledger staging (required with --ledger)")
    args = parser.parse_args()

    if args.ledger and not args.ticker:
        print("ERROR: --ledger requires -t/--ticker", file=sys.stderr)
        sys.exit(1)

    result = verify(args.url, max_tier=args.tier,
                    playwright_text=args.playwright_text,
                    cdp_text=args.cdp_text,
                    claim_text=args.claim_text)

    if args.ledger:
        staging_path = stage_result(args.ledger, args.ticker, result)
        print(f"[staged] {staging_path}", file=sys.stderr)
        if args.apply:
            from evidence_ledger import cmd_apply_staging
            cmd_apply_staging(args.ledger, args.ticker)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "verified":
            ok = " ✅ matched claim" if args.claim_text and result.get("matched") else ""
            print(f"✅ Verified via {result['tier']}{ok}")
            print(f"---")
            print(result["text"])
        elif result["status"] == "reachable":
            print(f"⚠️  Page reachable via {result['tier']} but claim text NOT found "
                  f"(--claim-text). Check the quote or the URL — do NOT mark verified.")
        elif result.get("next_action"):
            print(f"⚠️  Tier 1-2 exhausted. {result['next_action']}")
        else:
            print(f"❌ [UNVERIFIED] All tiers exhausted. "
                  f"Tier 1: {result.get('tier1_error', 'N/A')}. "
                  f"Tier 2: {result.get('tier2_error', 'N/A')}. "
                  f"Tier 4: {result.get('tier4_error', 'N/A')}")

    sys.exit(0 if result["status"] == "verified" else 1)


if __name__ == "__main__":
    cli()
