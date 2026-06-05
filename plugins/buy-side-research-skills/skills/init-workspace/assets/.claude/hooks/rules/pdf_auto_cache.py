"""Hook: intercept PDF downloads from primary sources and auto-cache as markdown.

Detects PDFs written by Bash/browser_download, checks if they are primary-source
documents (IR/filing URL patterns or filename keywords), converts via to-markdown.py,
caches to _cache/, and deletes the original PDF.

Non-blocking — failures log warnings and preserve the PDF.
"""
import os
import re
import subprocess
import sys
from glob import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import warn

# ── A track — multi-market regulatory filing / IR URL patterns ──
_PRIMARY_SOURCE_URLS = [
    # Company IR
    r"ir\.[a-z0-9-]+\.(?:com|co\.\w{2,3})",
    r"investor[s]?\.[a-z0-9-]+\.(?:com|co\.\w{2,3})",
    r"/ir/", r"/investor[s]?/",
    # US (SEC/EDGAR)
    r"sec\.gov", r"data\.sec\.gov",
    # HK (HKEX)
    r"hkexnews\.hk", r"\.hkex\.com\.hk",
    # JP (TDNET/EDINET)
    r"tdnet\.", r"disclosure\.tdnet", r"disclosure2\.",
    r"edinet-fsa\.go\.jp", r"disclosure\.edinet",
    # KR (DART/KIND)
    r"dart\.fss\.or\.kr", r"kind\.krx\.co\.kr",
    # CN (巨潮/上交所/深交所)
    r"cninfo\.com\.cn", r"sse\.com\.cn", r"szse\.cn",
    # TW (MOPS)
    r"mops\.twse\.com\.tw", r"emops\.twse\.com\.tw",
    # EU / UK / CA
    r"companieshouse\.gov\.uk", r"bundesanzeiger\.de",
    r"sedar\.com", r"\.europa\.eu/",
    # Generic filing/disclosure paths
    r"/annual[-_]", r"/quarterly[-_]", r"/earnings[-_]",
    r"/transcript[s]?", r"/prospectus",
    r"/s-?1[/\.]", r"/10-?[kq][/\.]", r"/20-?f[/\.]",
    r"/8-?k[/\.]", r"/6-?k[/\.]",
]

# ── B track — filename keywords ──
_PRIMARY_KEYWORDS = [
    "annual", "quarterly", "earnings", "transcript",
    "prospectus", "filing", "ir-", "fy", "1q", "2q", "3q", "4q",
    "10-k", "10-q", "20-f", "8-k", "6-k", "s-1", "s1",
    "招股", "年报", "季报", "半年报", "中期报告",
    "決算", "有価証券報告書", "四半期",
]

# Temp paths we should not try to derive ticker from
_SKIP_PREFIXES = ("/tmp/", "/temp/", "/var/", "C:\\Windows\\Temp", "Downloads\\")

_URL_RE = re.compile(r'https?://[^\s"\'<>]+', re.IGNORECASE)


def _is_primary_source(url_hint: str, filename: str) -> bool:
    """Return True if this PDF is a primary-source regulatory/IR document."""
    # A track: URL pattern
    if url_hint:
        for pattern in _PRIMARY_SOURCE_URLS:
            if re.search(pattern, url_hint, re.IGNORECASE):
                return True
    # B track: filename keywords
    lower = filename.lower()
    for kw in _PRIMARY_KEYWORDS:
        if kw in lower:
            return True
    return False


def _extract_url_from_bash(cmd: str) -> str:
    """Extract likely source URL from a Bash command."""
    urls = _URL_RE.findall(cmd)
    return urls[0] if urls else ""


def _derive_ticker(workspace: str, pdf_path: str) -> str | None:
    """Derive ticker by searching industry/*/companies/ for matching directory."""
    industry_dir = os.path.join(workspace, "industry")
    if not os.path.isdir(industry_dir):
        return None
    pdf_lower = pdf_path.lower()
    for ind in os.listdir(industry_dir):
        ind_path = os.path.join(industry_dir, ind)
        if not os.path.isdir(ind_path):
            continue
        comp_dir = os.path.join(ind_path, "companies")
        if not os.path.isdir(comp_dir):
            continue
        for ticker in os.listdir(comp_dir):
            ticker_lower = ticker.lower().replace(" ", "-").replace("_", "-")
            if ticker_lower in pdf_lower:
                return ticker
    return None


def _derive_desc(filename: str) -> str:
    """Derive a short cache description from PDF filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Clean: replace spaces, underscores, special chars with hyphens
    name = re.sub(r'[^a-zA-Z0-9一-鿿぀-ゟ゠-ヿ가-힯-]', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-').lower()
    # Truncate
    return name[:60] if len(name) > 60 else name


def _is_already_cached(workspace: str, ticker: str, desc: str) -> bool:
    """Check if a cached markdown already exists for this ticker + desc."""
    pattern = os.path.join(workspace, "industry", "*", "companies", ticker,
                           "_cache", f"{ticker}-{desc}.md")
    matches = glob(pattern)
    return len(matches) > 0


def check(ctx):
    payload = ctx.get("raw_payload", {})
    root = ctx.get("cwd", "")
    ti = payload.get("tool_input") or payload.get("toolInput") or {}

    # Collect source URL hints
    url_hint = ti.get("url", "") or ""
    if not url_hint:
        cmd = ti.get("command", "") or ""
        url_hint = _extract_url_from_bash(cmd)

    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path", "")
        if not path.lower().endswith(".pdf"):
            continue

        filename = os.path.basename(path)

        # Skip temp/download paths (can't derive ticker)
        normalized_path = path.replace("\\", "/")
        if any(normalized_path.lower().startswith(p.lower().replace("\\", "/"))
               for p in _SKIP_PREFIXES):
            continue

        # Gate: is this a primary-source document?
        if not _is_primary_source(url_hint, filename):
            continue

        # Derive ticker
        ticker = _derive_ticker(root, path)
        if not ticker:
            warn(f"pdf_auto_cache: cannot derive ticker for {filename}, skipping")
            continue

        desc = _derive_desc(filename)

        # Already cached? Delete redundant PDF and move on
        if _is_already_cached(root, ticker, desc):
            try:
                os.remove(path)
                print(f"pdf_auto_cache: {filename} already cached, deleted redundant PDF",
                      file=sys.stderr)
            except OSError:
                pass
            continue

        # Convert + cache + delete
        to_md = os.path.join(root, "_scripts", "shared", "to-markdown.py")
        if not os.path.exists(to_md):
            warn(f"pdf_auto_cache: to-markdown.py not found, skipping {filename}")
            continue

        try:
            r = subprocess.run(
                [sys.executable, to_md, path, "--cache", ticker, desc, "--rm", "--auto"],
                capture_output=True, text=True, timeout=120,
                cwd=root,
            )
            if r.returncode != 0:
                warn(f"pdf_auto_cache: conversion failed for {filename}: {r.stderr[:200]}")
            elif r.stderr:
                # Log what to-markdown printed (cache path, delete confirmation)
                for line in r.stderr.strip().split("\n"):
                    if line.strip():
                        print(f"pdf_auto_cache: {line.strip()}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            warn(f"pdf_auto_cache: timeout converting {filename} (>120s), PDF preserved")
        except Exception as e:
            warn(f"pdf_auto_cache: error processing {filename}: {e}")

    sys.exit(0)
