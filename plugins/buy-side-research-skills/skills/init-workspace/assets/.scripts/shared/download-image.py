#!/usr/bin/env python3
"""download-image.py — download product/equipment images from URLs, with cache.

Usage:
  python download-image.py <url> --output <slug>            # download + cache
  python download-image.py <url> --output <slug> --base64   # from base64 (Tier 2)
  python download-image.py --check <slug>                    # check cache only

Cache: workspace _cache/images/ + .cache.json index. Cross-skill shared.
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

CACHE_DIR = "_cache/images"
CACHE_INDEX = f"{CACHE_DIR}/.cache.json"


def _load_cache(workspace: Path) -> dict:
    idx = workspace / CACHE_INDEX
    if idx.is_file():
        with open(idx, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(workspace: Path, cache: dict):
    (workspace / CACHE_DIR).mkdir(parents=True, exist_ok=True)
    with open(workspace / CACHE_INDEX, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _cache_hit(workspace: Path, key: str) -> Path | None:
    cache = _load_cache(workspace)
    entry = cache.get(key)
    if entry:
        fpath = workspace / CACHE_DIR / entry["file"]
        if fpath.is_file():
            return fpath
    return None


def _cache_save(workspace: Path, key: str, filename: str, url: str, size: int):
    cache = _load_cache(workspace)
    cache[key] = {"file": filename, "url": url, "size": size}
    _save_cache(workspace, cache)


def _guess_ext(url_or_data: str | bytes) -> str:
    if isinstance(url_or_data, bytes):
        data = url_or_data
        if data[:4] == b"\x89PNG": return "png"
        if data[:2] == b"\xff\xd8": return "jpg"
        if data[:3] == b"GIF": return "gif"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP": return "webp"
        if data[:4] == b"<svg": return "svg"
        return "png"
    m = re.search(r"\.(png|jpg|jpeg|svg|webp|ico|gif)(?:\?|$)", url_or_data, re.IGNORECASE)
    if m:
        ext = m.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    return "png"


def download(url: str, output: str, workspace: Path) -> dict:
    """Download image from URL → _cache/images/<output>.<ext>. Returns result dict."""
    # Check cache
    cached = _cache_hit(workspace, output)
    if cached:
        return {"status": "cached", "key": output, "filename": cached.name, "path": str(cached)}

    try:
        req = Request(url, headers={"User-Agent": "download-image/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except URLError as e:
        return {"status": "error", "key": output, "error": f"HTTP: {e}", "next": "Try Playwright browser_navigate"}

    # Detect CDN anti-hotlink: content is HTML/JSON, not an actual image
    preview = data[:200].lstrip()
    if preview and (preview[:1] == b"<" or preview[:1] == b"{"):
        return {"status": "error", "key": output,
                "error": "CDN returned HTML/JSON (anti-hotlink), not an image",
                "next": "Try Playwright Tier 2: browser_navigate → browser_evaluate → fetch image → --base64"}

    ext = _guess_ext(data)
    filename = f"{output}.{ext}"
    fpath = workspace / CACHE_DIR / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(data)

    _cache_save(workspace, output, filename, url, len(data))
    return {"status": "downloaded", "key": output, "filename": filename, "path": str(fpath), "size": len(data)}


def download_base64(b64: str, output: str, workspace: Path) -> dict:
    """Download image from base64 string (Playwright Tier 2 fallback)."""
    import base64 as b64mod
    try:
        data = b64mod.b64decode(b64)
    except Exception as e:
        return {"status": "error", "key": output, "error": f"Base64: {e}"}

    ext = _guess_ext(data)
    filename = f"{output}.{ext}"
    fpath = workspace / CACHE_DIR / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(data)

    _cache_save(workspace, output, filename, "base64://", len(data))
    return {"status": "downloaded", "key": output, "filename": filename, "path": str(fpath), "size": len(data)}


def check(output: str, workspace: Path) -> dict:
    cached = _cache_hit(workspace, output)
    if cached:
        return {"status": "cached", "key": output, "filename": cached.name, "path": str(cached)}
    return {"status": "not_cached", "key": output}


def _find_industry_root(start: Path) -> Path | None:
    """Walk up from start to find nearest industry/<slug>/ directory."""
    for parent in [start.resolve(), *start.resolve().parents]:
        if parent.parent and parent.parent.name == "industry" and parent.name not in ("companies", "_cache", "_inbox"):
            return parent
    return None


def _image_cache_dir(industry_root: Path, topic: str = "", company: str = "") -> Path:
    """Resolve image cache directory for topic-level or company-level images."""
    if company:
        d = industry_root / "companies" / company / "_cache" / "images"
    elif topic:
        d = industry_root / "_cache" / "images" / topic
    else:
        d = industry_root / "_cache" / "images"
    d.mkdir(parents=True, exist_ok=True)
    return d


def main():
    p = argparse.ArgumentParser(description="Download product/equipment images with cache")
    p.add_argument("url", nargs="?", help="Image URL")
    p.add_argument("--output", required=True, help="Output slug (e.g. 'my-product')")
    p.add_argument("--topic", help="Industry topic subdirectory (e.g. 'teach-in')")
    p.add_argument("--company", help="Company ticker slug (e.g. 'santec')")
    p.add_argument("--base64", help="Base64 image data (Tier 2 fallback)")
    p.add_argument("--check", action="store_true", help="Check cache only")
    args = p.parse_args()

    start = Path.cwd()
    industry_root = _find_industry_root(start)
    if not industry_root:
        # Fallback: use workspace root _cache
        ws = start.resolve()
        for parent in [ws, *ws.parents]:
            if (parent / "industry").is_dir() and (parent / "CLAUDE.md").is_file():
                ws = parent
                break
        cache_dir = ws / "_cache" / "images"
        cache_dir.mkdir(parents=True, exist_ok=True)
    else:
        cache_dir = _image_cache_dir(industry_root,
                                      topic=args.topic or "",
                                      company=args.company or "")

    if args.check:
        result = check(args.output, cache_dir)
    elif args.base64:
        result = download_base64(args.base64, args.output, cache_dir)
    elif args.url:
        result = download(args.url, args.output, cache_dir)
    else:
        print("ERROR: url or --base64 required", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
