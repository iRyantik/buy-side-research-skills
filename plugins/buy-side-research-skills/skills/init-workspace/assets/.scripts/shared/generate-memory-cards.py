#!/usr/bin/env python3
"""Generate thin CC memory cards from RESEARCH.md files.

Scans industry/*/RESEARCH.md and industry/*/companies/*/RESEARCH.md,
extracts key fields, writes memory/research/<entity>.md (≤500 words each).
"""
from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import os
import re

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDUSTRY_DIR = os.path.join(WORKSPACE, "industry")
MEMORY_DIR = os.path.join(WORKSPACE, "memory", "research")

# ── helpers ──────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    """Extract YAML-like frontmatter from markdown."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).strip().split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            fm[k.strip()] = v.strip()
    return fm


def _extract_section(text: str, heading: str) -> str:
    """Extract content between a heading and the next heading of same or higher level."""
    pattern = rf'(?:^|\n)## {re.escape(heading)}\s*\n(.*?)(?=\n## |\n# |\Z)'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def _extract_subheading(text: str, heading: str) -> str:
    """Extract content after a ### subheading within already-extracted section text."""
    pattern = rf'### {re.escape(heading)}\s*\n(.*?)(?=\n### |\n## |\n# |\Z)'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return text
    return m.group(1).strip()


def _count_words(text: str) -> int:
    return len(text.split())


def _trim_to_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return ' '.join(words[:limit]) + '...'


# ── card generators ──────────────────────────────────────

def _generate_industry_card(text: str, slug: str) -> str:
    """Generate thin card for an industry RESEARCH.md."""
    fm = _parse_frontmatter(text)
    companies = _extract_section(text, "1. 覆盖公司")
    cycle = _extract_section(text, "4. 行业 Thesis")
    trail = _extract_section(text, "6. 研究轨迹")

    # Extract just the table rows from companies, not the header or separator
    rows = [l for l in companies.split('\n') if l.startswith('|') and not l.startswith('| 公司') and not l.startswith('|-')]

    # Extract actual cycle judgment content from within the section
    cycle_content = _extract_subheading(cycle, "周期判断") if cycle else "?"

    card = f"""---
industry: {slug}
stage: {fm.get('stage', '?')}
updated: {fm.get('updated', '?')}
---

# {slug} — 行业速览

## 覆盖公司
{'| 公司 | Ticker | Thesis 阶段 | 优先级 |'}
{'|---|---|---|---|'}
{chr(10).join(rows[:15])}

## 周期判断
{_trim_to_words(cycle_content, 100)}

## 上次读到哪
{_trim_to_words(trail, 150) if trail else '?'}
"""
    return _trim_to_words(card, 500)


def _generate_company_card(text: str, ticker: str) -> str:
    """Generate thin card for a company RESEARCH.md."""
    fm = _parse_frontmatter(text)
    thesis = _extract_section(text, "2. Thesis 状态")
    speed = _extract_section(text, "3. 事实基线")
    trail = _extract_section(text, "4. 研究轨迹")

    # Extract specific sub-sections
    current_lean = _extract_subheading(thesis, "当前倾向") if thesis else "?"
    speed_card = _extract_subheading(speed, "速查卡") if speed else "?"

    card = f"""---
ticker: {ticker}
industry: {fm.get('industry', '?')}
stage: {fm.get('stage', '?')}
conviction: {fm.get('conviction', '?')}
updated: {fm.get('updated', '?')}
---

# {ticker} — 研究速览

## 当前倾向
{_trim_to_words(current_lean, 150)}

## 速查卡
{_trim_to_words(speed_card, 200) if speed_card else '?'}

## 上次读到哪
{_trim_to_words(trail, 200) if trail else '?'}
"""
    return _trim_to_words(card, 500)


# ── main ─────────────────────────────────────────────────

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python generate-memory-cards.py [--ticker TICKER] [--industry SLUG]")
        print("Scans RESEARCH.md files and generates CC memory cards.")
        print("Without args, generates cards for all companies with RESEARCH.md.")
        return
    os.makedirs(MEMORY_DIR, exist_ok=True)

    count = 0

    # Industry cards
    if os.path.isdir(INDUSTRY_DIR):
        for slug in sorted(os.listdir(INDUSTRY_DIR)):
            indir = os.path.join(INDUSTRY_DIR, slug)
            if not os.path.isdir(indir):
                continue
            rm_path = os.path.join(indir, "RESEARCH.md")
            if not os.path.exists(rm_path):
                continue
            with open(rm_path, "r", encoding="utf-8") as f:
                text = f.read()
            card = _generate_industry_card(text, slug)
            out = os.path.join(MEMORY_DIR, f"{slug}.md")
            with open(out, "w", encoding="utf-8") as f:
                f.write(card)
            count += 1

            # Company cards within this industry
            comp_dir = os.path.join(indir, "companies")
            if not os.path.isdir(comp_dir):
                continue
            for ticker in sorted(os.listdir(comp_dir)):
                crm = os.path.join(comp_dir, ticker, "RESEARCH.md")
                if not os.path.exists(crm):
                    continue
                with open(crm, "r", encoding="utf-8") as f:
                    text = f.read()
                card = _generate_company_card(text, ticker)
                out = os.path.join(MEMORY_DIR, f"{ticker}.md")
                with open(out, "w", encoding="utf-8") as f:
                    f.write(card)
                count += 1

    print(f"Generated {count} memory cards -> {MEMORY_DIR}")


if __name__ == "__main__":
    main()
