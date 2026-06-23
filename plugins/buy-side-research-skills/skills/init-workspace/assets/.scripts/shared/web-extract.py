#!/usr/bin/env python3
"""web-extract — fetch a URL and extract clean body text from HTML.

Usage:
  python web-extract.py <url>              # plain text body
  python web-extract.py <url> --html       # cleaned HTML fragment
  python web-extract.py <url> --markdown   # markdown (requires html2text)

Replaces the Tier 3 curl fallback in the source verification chain.
Removes nav, header, footer, sidebar, scripts, styles.
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from urllib.request import Request, urlopen


# ── fetch ────────────────────────────────────────────────

def _fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "web-extract/1.0"})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    # Detect encoding
    content_type = resp.headers.get("Content-Type", "")
    charset = "utf-8"
    m = re.search(r"charset=([\w-]+)", content_type)
    if m:
        charset = m.group(1)
    return data.decode(charset, errors="replace")


# ── strip boilerplate ────────────────────────────────────

_STRIP_TAGS = re.compile(
    r"</?(?:script|style|nav|header|footer|aside|noscript|"
    r"form|select|button|input|textarea|iframe|svg|canvas|"
    r"video|audio|source|embed|object|link|meta|"
    r"template)\b[^>]*>",
    re.IGNORECASE | re.DOTALL,
)

_STRIP_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
_STRIP_ATTRS = re.compile(r'\s(?:class|style|id|data-\w+|aria-\w+|role|tabindex|on\w+)\s*=\s*"[^"]*"', re.IGNORECASE)
_STRIP_EMPTY_TAGS = re.compile(r"<(div|span|p|li|td|th|tr|section|article|ul|ol|dl|blockquote)\b[^>]*>\s*</\1>", re.IGNORECASE)


def _clean_html(html: str) -> str:
    """Remove boilerplate tags, scripts, styles, empty wrappers."""
    html = _STRIP_COMMENTS.sub("", html)
    html = _STRIP_TAGS.sub("", html)
    # Remove attributes from remaining tags
    html = _STRIP_ATTRS.sub("", html)
    # Remove empty wrapper tags
    for _ in range(3):
        prev = html
        html = _STRIP_EMPTY_TAGS.sub("", html)
        # Collapse whitespace
        html = re.sub(r"\n{3,}", "\n\n", html)
        html = re.sub(r" {2,}", " ", html)
        if html == prev:
            break
    return html


class _TextExtractor(HTMLParser):
    """Extract visible text, preserving paragraph breaks."""
    def __init__(self):
        super().__init__()
        self.text = []
        self._skip = False
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
        # Collapse runs of newlines
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        # Collapse spaces
        raw = re.sub(r" {2,}", " ", raw)
        return raw.strip()


def _html_to_text(html: str) -> str:
    cleaned = _clean_html(html)
    e = _TextExtractor()
    e.feed(cleaned)
    return e.get_text()


def _html_to_markdown(html: str, url: str) -> str:
    try:
        import html2text
    except ImportError:
        return _html_to_text(html)
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    cleaned = _clean_html(html)
    return h.handle(cleaned)


# ── main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract clean text from web page")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--html", action="store_true", help="Output cleaned HTML fragment")
    parser.add_argument("--markdown", action="store_true", help="Output markdown (requires html2text)")
    args = parser.parse_args()

    try:
        html = _fetch(args.url)
    except Exception as e:
        print(f"fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.markdown:
        print(_html_to_markdown(html, args.url))
    elif args.html:
        print(_clean_html(html))
    else:
        print(_html_to_text(html))


if __name__ == "__main__":
    main()
