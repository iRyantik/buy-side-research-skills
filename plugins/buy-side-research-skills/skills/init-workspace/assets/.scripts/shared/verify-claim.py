#!/usr/bin/env python3
"""verify-claim.py — unified source verification chain.

Orchestrates the Tier 1→2→3→4 fallback for any web claim URL.
Returns structured output so consuming skills don't need to
re-implement the chain.

Usage:
  python verify-claim.py <url>                    # auto-tier, plain text
  python verify-claim.py <url> --json             # structured JSON output
  python verify-claim.py <url> --tier 1           # HTTP only, no fallback

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


# ── main ────────────────────────────────────────────────

def verify(url: str, max_tier: int = 4,
           playwright_text: str | None = None,
           cdp_text: str | None = None) -> dict:
    """Run the verification chain. Returns structured result."""
    result: dict = {
        "url": url,
        "status": "unverified",
        "tier": None,
        "text": None,
        "error": None,
        "next_action": None,
    }

    # If text was provided from a previous retry
    if playwright_text:
        result["status"] = "verified"
        result["tier"] = "Playwright"
        result["text"] = playwright_text[:10000]
        return result

    if cdp_text:
        result["status"] = "verified"
        result["tier"] = "browser-harness CDP"
        result["text"] = cdp_text[:10000]
        return result

    # Tier 1: HTTP (skip if known 403 domain)
    if max_tier >= 1:
        if _should_skip_tier1(url):
            result["tier1_error"] = "skipped — known 403 domain, routing to Tier 2"
        else:
            text, err = _tier1_http(url)
            if text:
                result["status"] = "verified"
                result["tier"] = "WebFetch"
                result["text"] = text[:10000]
                return result
            result["tier1_error"] = err

    # Tier 2: browser-harness CDP (auto, no agent intervention needed)
    if max_tier >= 2:
        text, err = _tier2_cdp(url)
        if text:
            result["status"] = "verified"
            result["tier"] = "browser-harness CDP"
            result["text"] = text[:10000]
            return result
        result["tier2_error"] = err

    # Tier 3: Playwright MCP (requires agent)
    if max_tier >= 3:
        result["next_action"] = _tier3_instruction(url)
        return result

    # Tier 4: curl
    if max_tier >= 4:
        text, err = _tier4_curl(url)
        if text:
            result["status"] = "verified"
            result["tier"] = "curl"
            result["text"] = text[:10000]
            return result
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
    args = parser.parse_args()

    result = verify(args.url, max_tier=args.tier,
                    playwright_text=args.playwright_text,
                    cdp_text=args.cdp_text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "verified":
            print(f"✅ Verified via {result['tier']}")
            print(f"---")
            print(result["text"])
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
