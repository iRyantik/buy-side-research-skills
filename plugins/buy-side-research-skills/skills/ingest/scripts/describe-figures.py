#!/usr/bin/env python3
"""Describe pending figures in cache markdown using a VLM API.

Usage:
  python describe-figures.py industry/<industry>/companies/<ticker>/_cache/source-file.md
  python describe-figures.py industry/<industry>/companies/<ticker>/_cache/ --recursive
  python describe-figures.py industry/<industry>/companies/<ticker>/_cache/source-file.md --api-url http://localhost:11434/v1 --model llava
  python describe-figures.py industry/<industry>/companies/<ticker>/_cache/source-file.md --print-pending  # just list pending figures

Environment variables:
  VLM_API_URL     Base URL for OpenAI-compatible VLM API (default: https://api.openai.com/v1)
  VLM_API_KEY     API key (default: none)
  VLM_MODEL       Model name (default: gpt-4o)
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path


FIGURE_BLOCK_RE = re.compile(
    r'<!-- FIGURE (?P<id>[^\s]+) \| page: (?P<page>[^\s|]+) \| classification: (?P<cls>[^|]+) \| confidence: (?P<conf>[^|]+) -->'
    r'\s*'
    r'!\[[^\]]*\]\((?P<img_path>[^)]+)\)'
    r'\s*'
    r'\*[^*]+\*'
    r'\s*'
    r'> (?P<desc>.*?)'
    r'\s*'
    r'<!-- /FIGURE -->',
    re.DOTALL,
)


def encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("utf-8")


def find_figures(text: str) -> list[dict]:
    figures = []
    for match in FIGURE_BLOCK_RE.finditer(text):
        desc = match.group("desc").strip()
        figures.append({
            "start": match.start(),
            "end": match.end(),
            "id": match.group("id"),
            "page": match.group("page"),
            "classification": match.group("cls").strip(),
            "confidence": match.group("conf").strip(),
            "img_path": match.group("img_path"),
            "pending": desc == "[Figure description pending]",
            "description": None if desc == "[Figure description pending]" else desc,
            "full_match": match.group(0),
        })
    return figures


def call_vlm(image_path: Path, api_url: str, api_key: str | None, model: str) -> str:
    """Call OpenAI-compatible VLM API to describe a figure."""
    import http.client as hc
    import urllib.parse

    b64 = encode_image(image_path)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are analyzing a figure from an equity research report. "
                            "Describe what this figure shows in 2-4 sentences. "
                            "Focus on: chart/diagram type, what data or relationships it displays, "
                            "key trends or takeaways visible. "
                            "If it's a diagram, describe the components and their relationships. "
                            "Output ONLY the description, no preamble."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    parsed = urllib.parse.urlparse(api_url)
    conn = hc.HTTPSConnection(parsed.netloc) if parsed.scheme == "https" else hc.HTTPConnection(parsed.netloc)
    path = f"{parsed.path}/chat/completions"
    body = json.dumps(payload).encode("utf-8")

    try:
        conn.request("POST", path, body=body, headers=headers)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"[VLM API error: {exc}]"


def describe_figures(md_path: Path, api_url: str, api_key: str | None, model: str, dry_run: bool) -> int:
    text = md_path.read_text(encoding="utf-8")
    figures = find_figures(text)
    pending = [f for f in figures if f["pending"]]
    described = [f for f in figures if not f["pending"]]

    print(f"File: {md_path}")
    print(f"  Total figures: {len(figures)}, pending: {len(pending)}, described: {described}")

    if not pending:
        return 0

    if dry_run:
        for f in pending:
            print(f"  [{f['id']}] p{f['page']} ({f['classification']}) -> pending")
        return 0

    cache_dir = md_path.parent
    results = []
    for fig in pending:
        img_rel = Path(fig["img_path"])
        img_path = cache_dir / img_rel
        if not img_path.exists():
            print(f"  [{fig['id']}] SKIP: image not found at {img_path}")
            results.append((fig, "[Image file not found]"))
            continue

        print(f"  [{fig['id']}] describing... ", end="", flush=True)
        desc = call_vlm(img_path, api_url, api_key, model)
        print(f"OK ({len(desc)} chars)")
        results.append((fig, desc))

    if results:
        lines = text.splitlines(keepends=True)
        offset = 0
        for fig, desc in results:
            old_block = fig["full_match"]
            new_desc_line = f"> **Figure Description:** {desc}"
            new_block = old_block.replace("> [Figure description pending]", new_desc_line)
            text = text.replace(old_block, new_block, 1)
        md_path.write_text(text, encoding="utf-8")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Describe pending figures in cache markdown using a VLM API.")
    parser.add_argument("source", help="Cache markdown file or directory.")
    parser.add_argument("--recursive", action="store_true", help="Recursively process markdown files.")
    parser.add_argument("--api-url", default=os.getenv("VLM_API_URL", "https://api.openai.com/v1"), help="VLM API base URL.")
    parser.add_argument("--api-key", default=os.getenv("VLM_API_KEY"), help="API key.")
    parser.add_argument("--model", default=os.getenv("VLM_MODEL", "gpt-4o"), help="VLM model name.")
    parser.add_argument("--dry-run", action="store_true", help="Only list pending figures, don't call API.")
    parser.add_argument("--print-pending", action="store_true", dest="dry_run", help="Alias for --dry-run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(json.dumps({"status": "failed", "error": f"Source not found: {source}"}))
        return 1

    files = []
    if source.is_file():
        if source.suffix.lower() == ".md":
            files.append(source)
    elif source.is_dir():
        pattern = "**/*.md" if args.recursive else "*.md"
        files = sorted(source.glob(pattern))

    if not files:
        print(json.dumps({"status": "failed", "error": "No markdown files found."}))
        return 1

    failed = 0
    for md_path in files:
        try:
            rc = describe_figures(md_path, args.api_url, args.api_key, args.model, args.dry_run)
            if rc:
                failed += 1
        except Exception as exc:
            print(f"ERROR: {md_path}: {exc}")
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
