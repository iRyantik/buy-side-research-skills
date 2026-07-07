#!/usr/bin/env python3
"""download-image.py — download product/equipment images from URLs, with cache.

Usage:
  python download-image.py <url> --output <slug>            # download + cache
  python download-image.py <url> --output <slug> --base64   # from base64 (Tier 2)
  python download-image.py --check <slug>                    # check cache only

Cache: workspace .cache/images/ + .cache.json index. Cross-skill shared.
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

CACHE_DIR = ".cache/images"
CACHE_INDEX = f"{CACHE_DIR}/.cache.json"


def _load.cache(workspace: Path) -> dict:
    idx = workspace / CACHE_INDEX
    if idx.is_file():
        with open(idx, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save.cache(workspace: Path, cache: dict):
    (workspace / CACHE_DIR).mkdir(parents=True, exist_ok=True)
    with open(workspace / CACHE_INDEX, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _cache_hit(workspace: Path, key: str) -> Path | None:
    cache = _load.cache(workspace)
    entry = cache.get(key)
    if entry:
        fpath = workspace / CACHE_DIR / entry["file"]
        if fpath.is_file():
            return fpath
    return None


def _cache_save(workspace: Path, key: str, filename: str, url: str, size: int):
    cache = _load.cache(workspace)
    cache[key] = {"file": filename, "url": url, "size": size}
    _save.cache(workspace, cache)


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
    """Download image from URL → .cache/images/<output>.<ext>. Returns result dict."""
    # Check cache
    cached = _cache_hit(workspace, output)
    if cached:
        ref_path = f"{CACHE_DIR}/{cached.name}"
        return {"status": "cached", "key": output, "filename": cached.name, "path": str(cached), "ref": ref_path}

    try:
        req = Request(url, headers={"User-Agent": "download-image/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except URLError as e:
        return {"status": "error", "key": output, "error": f"HTTP: {e}", "next": "Try Playwright browser_navigate"}

    ext = _guess_ext(data)
    filename = f"{output}.{ext}"
    fpath = workspace / CACHE_DIR / filename
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(data)

    _cache_save(workspace, output, filename, url, len(data))
    ref_path = f"{CACHE_DIR}/{filename}"
    return {"status": "downloaded", "key": output, "filename": filename, "path": str(fpath), "size": len(data), "ref": ref_path}


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
        ref_path = f"{CACHE_DIR}/{cached.name}"
        return {"status": "cached", "key": output, "filename": cached.name, "path": str(cached), "ref": ref_path}
    return {"status": "not_cached", "key": output}


def main():
    p = argparse.ArgumentParser(description="Download product/equipment images with cache")
    p.add_argument("url", nargs="?", help="Image URL")
    p.add_argument("--output", required=True, help="Output slug (e.g. 'my-product')")
    p.add_argument("--base64", help="Base64 image data (Tier 2 fallback)")
    p.add_argument("--check", action="store_true", help="Check cache only")
    p.add_argument("--workspace", help="Workspace path (default: auto-detect)")
    args = p.parse_args()

    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    # Walk up to find workspace root
    for parent in [workspace, *workspace.parents]:
        if (parent / "industry").is_dir() and (parent / "CLAUDE.md").is_file():
            workspace = parent
            break

    if args.check:
        result = check(args.output, workspace)
    elif args.base64:
        result = download_base64(args.base64, args.output, workspace)
    elif args.url:
        result = download(args.url, args.output, workspace)
    else:
        print("ERROR: url or --base64 required", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    ref = result.get("ref", "")
    if ref and result["status"] in ("downloaded", "cached"):
        print(f"\nArtifact 引用: ![描述]({ref})")
    return 0 if result["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
