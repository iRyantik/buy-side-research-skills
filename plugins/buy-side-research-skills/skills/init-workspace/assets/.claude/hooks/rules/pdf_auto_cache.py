"""Hook: intercept PDF downloads from primary sources and auto-cache as markdown.

Detects PDFs written by Bash/browser_download, checks if they are primary-source
documents (IR/filing URL patterns or filename keywords), converts via to-markdown.py,
caches to a layered .cache/ tree, and deletes the original PDF.

Non-blocking — failures log warnings and preserve the PDF.
"""
import os
import re
import subprocess
import sys

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

# ── Source type inference from URL patterns ──
_SOURCE_TYPE_URL = [
    (re.compile(r"/annual[-_/]|/10-?[kK][/\.]|/20-?[fF][/\.]|annual.report|annual-report"),
     ("disclosure", "annual")),
    (re.compile(r"/quarterly[-_/]|/10-?[qQ][/\.]|q[1-4].*report|quarterly.report"),
     ("disclosure", "quarterly")),
    (re.compile(r"/transcript[s]?[/\.]|/earnings.call|/決算説明会|/earnings-call"),
     ("disclosure", "transcript")),
    (re.compile(r"/prospectus|/s-?1[/\.]|/ipo|/招股"),
     ("disclosure", "prospectus")),
    (re.compile(r"/8-?k[/\.]|/6-?k[/\.]|/filing|/sec-filing"),
     ("disclosure", "filing")),
]

_SOURCE_TYPE_FILENAME = [
    (re.compile(r"annual|10-?[kK]|20-?[fF]|fy\d|fiscal.year|年報|有価証券報告書"),
     ("disclosure", "annual")),
    (re.compile(r"quarterly|10-?[qQ]|q[1-4]|interim|半年報|四半期|half.year"),
     ("disclosure", "quarterly")),
    (re.compile(r"transcript|earnings.call|earnings-call|決算説明|説明会|conference.call"),
     ("disclosure", "transcript")),
    (re.compile(r"prospectus|s-?1|ipo|招股|目論見書"),
     ("disclosure", "prospectus")),
    (re.compile(r"8-?k|6-?k|filing|sec.filing|form.8|form.6"),
     ("disclosure", "filing")),
]


def _is_primary_source(url_hint: str, filename: str) -> bool:
    """Return True if this PDF is a primary-source regulatory/IR document."""
    if url_hint:
        for pattern in _PRIMARY_SOURCE_URLS:
            if re.search(pattern, url_hint, re.IGNORECASE):
                return True
    lower = filename.lower()
    for kw in _PRIMARY_KEYWORDS:
        if kw in lower:
            return True
    return False


def _extract_url_from_bash(cmd: str) -> str:
    """Extract likely source URL from a Bash command."""
    urls = _URL_RE.findall(cmd)
    return urls[0] if urls else ""


def _infer_source_type(url: str, filename: str) -> tuple:
    """Return (top_dir, sub_dir) for the cache file tree.

    Examples: ("disclosure", "annual"), ("disclosure", "quarterly"), ("inbox", "")
    """
    for pattern, result in _SOURCE_TYPE_URL:
        if pattern.search(url):
            return result
    for pattern, result in _SOURCE_TYPE_FILENAME:
        if pattern.search(filename, re.IGNORECASE):
            return result
    return ("inbox", "")


def _find_industry(workspace: str, ticker: str) -> str | None:
    """Find industry slug for a ticker by scanning industry/*/companies/<ticker>/."""
    industry_dir = os.path.join(workspace, "industry")
    if not os.path.isdir(industry_dir):
        return None
    for ind in os.listdir(industry_dir):
        if os.path.isdir(os.path.join(industry_dir, ind, "companies", ticker)):
            return ind
    return None


def _derive_ticker(workspace: str, pdf_path: str) -> str | None:
    """Derive ticker by matching path components against company directories."""
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
            if ticker.lower().replace(" ", "-").replace("_", "-") in pdf_lower:
                return ticker
    return None


def _build_filename(filename: str) -> str:
    """Build a clean cache filename from PDF basename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    name = re.sub(r'[^a-zA-Z0-9一-鿿_-]', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name[:80] if len(name) > 80 else name


def _resolve_cache_path(workspace: str, ticker: str | None, source_type: tuple,
                        pdf_path: str) -> str:
    """Compute the full cache path for a converted PDF."""
    top, sub = source_type
    stem = _build_filename(os.path.basename(pdf_path))
    filename = f"{stem}.md"

    if top == "disclosure":
        if ticker:
            ind = _find_industry(workspace, ticker)
            if ind:
                base = os.path.join(workspace, "industry", ind, "companies", ticker,
                                    ".cache", "disclosure", sub)
                os.makedirs(base, exist_ok=True)
                return os.path.join(base, filename)
        # Fallback: workspace-level .cache
        base = os.path.join(workspace, ".cache", "disclosure", sub)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    elif top in ("sell-side", "institution"):
        base = os.path.join(workspace, ".cache", top, sub)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    elif top == "primary":
        base = os.path.join(workspace, ".cache", "primary", sub)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    elif top == "web":
        if ticker:
            ind = _find_industry(workspace, ticker)
            if ind:
                base = os.path.join(workspace, "industry", ind, "companies", ticker,
                                    ".cache", "web")
                os.makedirs(base, exist_ok=True)
                return os.path.join(base, filename)
        base = os.path.join(workspace, ".cache", "web")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    else:  # inbox
        base = os.path.join(workspace, ".cache", "inbox")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)


def check(ctx):
    payload = ctx.get("raw_payload", {})
    root = ctx.get("cwd", "")
    ti = payload.get("tool_input") or payload.get("toolInput") or {}

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

        normalized_path = path.replace("\\", "/")
        if any(normalized_path.lower().startswith(p.lower().replace("\\", "/"))
               for p in _SKIP_PREFIXES):
            continue

        if not _is_primary_source(url_hint, filename):
            continue

        # ── Source type inference ──
        source_type = _infer_source_type(url_hint, filename)
        top = source_type[0]

        # ── Ticker derivation ──
        ticker = _derive_ticker(root, path)
        if not ticker and top == "disclosure":
            warn(f"pdf_auto_cache: cannot derive ticker for {filename}, caching to inbox")
            source_type = ("inbox", "")
            ticker = None

        # ── Resolve cache path ──
        cache_path = _resolve_cache_path(root, ticker, source_type, path)

        # Dedup: already cached?
        if os.path.exists(cache_path):
            try:
                os.remove(path)
                print(f"pdf_auto_cache: {filename} already cached at {cache_path}, "
                      f"deleted redundant PDF", file=sys.stderr)
            except OSError:
                pass
            continue

        # Convert + cache + delete
        to_md = os.path.join(root, ".scripts", "shared", "to-markdown.py")
        if not os.path.exists(to_md):
            warn(f"pdf_auto_cache: to-markdown.py not found, skipping {filename}")
            continue

        # Build to-markdown.py args with full output path + metadata
        cmd = [sys.executable, to_md, path,
               "--output", cache_path,
               "--source-type-top", top,
               "--source-type-sub", source_type[1] if source_type[1] else "",
               "--rm", "--auto"]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=root)
            if r.returncode != 0:
                warn(f"pdf_auto_cache: conversion failed for {filename}: {r.stderr[:200]}")
            elif r.stderr:
                for line in r.stderr.strip().split("\n"):
                    if line.strip():
                        print(f"pdf_auto_cache: {line.strip()}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            warn(f"pdf_auto_cache: timeout converting {filename} (>120s), PDF preserved")
        except Exception as e:
            warn(f"pdf_auto_cache: error processing {filename}: {e}")

    sys.exit(0)
