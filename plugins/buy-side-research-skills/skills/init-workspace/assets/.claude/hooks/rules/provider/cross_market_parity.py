"""Warn: cross-market compare outputs must state listing identity, currency basis, and as-of timestamp."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

COMPARISON = re.compile(r'(?i)(premium|discount|spread|valuation|liquidity|multiple|EV/EBITDA|P/E|P/B|basis)')
LISTING = re.compile(r'(?i)(ADR|A-share|H-share|ordinary share|primary listing|secondary listing|dual-listed|listing identity|listing venue|venue basis|NYSE|NASDAQ|HKEX|SSE|SZSE)')
CURRENCY = re.compile(r'(?i)(USD|HKD|CNY|RMB|JPY|KRW|EUR|currency basis|FX|translated at|converted at)')
AS_OF = re.compile(r'(?i)(as of|timestamp|close as of|market close|updated|collected on)')
SKILL_FILE = re.compile(r'cross-market-compare')

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        is_target = (t.get("kind") == "file" and bool(SKILL_FILE.search(leaf))) or bool(re.search(r'(?im)^#\s*Cross-Market Compare\b', text))
        if not is_target:
            continue
        if not COMPARISON.search(text):
            continue
        d = t.get('display', '?')
        if not LISTING.search(text):
            warn(f"cross_market_parity: {d} must explicitly state listing identity or venue basis for cross-market comparison.")
        if not CURRENCY.search(text):
            warn(f"cross_market_parity: {d} must explicitly state currency basis or FX translation basis for cross-market comparison.")
        if not AS_OF.search(text):
            warn(f"cross_market_parity: {d} must explicitly state as-of date or timestamp basis for cross-market comparison.")
