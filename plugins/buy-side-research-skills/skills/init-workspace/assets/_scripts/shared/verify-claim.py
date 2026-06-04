#!/usr/bin/env python3
"""verify-claim.py — unified source verification chain.

Orchestrates the Tier 1→2→3 fallback for any web claim URL.
Returns structured output so consuming skills don't need to
re-implement the chain.

Usage:
  python verify-claim.py <url>                    # auto-tier, plain text
  python verify-claim.py <url> --json             # structured JSON output
  python verify-claim.py <url> --tier 1           # HTTP only, no fallback

Tier chain:
  Tier 1 — HTTP GET (urllib, no auth, 30s timeout)
  Tier 2 — Playwright MCP required (script prints instruction for agent)
  Tier 3 — curl subprocess (last resort)
  Tier 4 — [UNVERIFIED] (nothing worked)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError


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


# ── Tier 2: Playwright MCP ─────────────────────────────

def _tier2_instruction(url: str) -> str:
    """Return the instruction for the agent to use Playwright MCP."""
    return (
        f"Tier 2 — Playwright MCP required:\n"
        f"  browser_navigate → {url}\n"
        f"  browser_snapshot → capture page text\n"
        f"  Feed the snapshot text back to: python verify-claim.py {url} --playwright-text \"<text>\""
    )


# ── Tier 3: curl ────────────────────────────────────────

def _tier3_curl(url: str) -> tuple[str | None, str | None]:
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

def verify(url: str, max_tier: int = 3,
           playwright_text: str | None = None) -> dict:
    """Run the verification chain. Returns structured result."""
    result: dict = {
        "url": url,
        "status": "unverified",
        "tier": None,
        "text": None,
        "error": None,
        "next_action": None,
    }

    # If Playwright text was provided from a previous run
    if playwright_text:
        result["status"] = "verified"
        result["tier"] = "Playwright"
        result["text"] = playwright_text[:10000]
        return result

    # Tier 1: HTTP
    if max_tier >= 1:
        text, err = _tier1_http(url)
        if text:
            result["status"] = "verified"
            result["tier"] = "WebFetch"
            result["text"] = text[:10000]
            return result
        result["tier1_error"] = err

    # Tier 2: Playwright MCP (requires agent)
    if max_tier >= 2:
        result["next_action"] = _tier2_instruction(url)
        # Don't fall to Tier 3 yet — let agent handle Tier 2 first
        return result

    # Tier 3: curl
    if max_tier >= 3:
        text, err = _tier3_curl(url)
        if text:
            result["status"] = "verified"
            result["tier"] = "curl"
            result["text"] = text[:10000]
            return result
        result["tier3_error"] = err

    # Tier 4: nothing worked
    result["status"] = "unverified"
    result["tier"] = None
    result["error"] = "All tiers exhausted"
    return result


def cli():
    parser = argparse.ArgumentParser(
        description="Unified source verification chain"
    )
    parser.add_argument("url", help="URL to verify")
    parser.add_argument("--tier", type=int, default=3,
                       help="Max tier to attempt (1=HTTP, 2=Playwright, 3=curl, default: 3)")
    parser.add_argument("--json", action="store_true",
                       help="Output structured JSON")
    parser.add_argument("--playwright-text", default=None,
                       help="Playwright snapshot text (from Tier 2 retry)")
    args = parser.parse_args()

    result = verify(args.url, max_tier=args.tier,
                    playwright_text=args.playwright_text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "verified":
            print(f"✅ Verified via {result['tier']}")
            print(f"---")
            print(result["text"])
        elif result.get("next_action"):
            print(f"⚠️  Tier 1 failed. {result['next_action']}")
        else:
            print(f"❌ [UNVERIFIED] All tiers exhausted. "
                  f"Tier 1: {result.get('tier1_error', 'N/A')}. "
                  f"Tier 3: {result.get('tier3_error', 'N/A')}")

    sys.exit(0 if result["status"] == "verified" else 1)


if __name__ == "__main__":
    cli()
