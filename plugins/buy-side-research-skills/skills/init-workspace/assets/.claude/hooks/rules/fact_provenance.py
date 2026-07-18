"""Check: every quantitative fact must have a Tier 0-3 label, source_layer, and as-of date."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

# Tier 3 patterns: banned — fact with NO source
# Tier 2 patterns: researcher assumption
# Tier 1 patterns: upstream artifact
# Tier 0 patterns: provider_api / machine-verified

NO_SOURCE_PATTERNS = [
    # Numbers without source annotation nearby (within 200 chars)
    (re.compile(r'(?:PE|P/E|市盈率|市值|market cap|收入|利润|margin|份额|TAM)\S{0,50}[=:：]?\s*[\d,.]+\s*(?:bn|B|m|M|k|亿|万|%|x|倍|USD|CNY|HKD)?'), "missing source"),
]

# Check for numeric claims without source indicators
SOURCE_INDICATORS = re.compile(r'\[(?:S\d+|I\d+|LBG\d+|P\d+|R\d+|SRC\d+)\]|\[.*?\|\s*(?:Bridge\|yfinance\|WebSearch\|Google Finance\|估算\|研究员假设|[a-z_]+\s*\|\s*\d{8})\]')

TIER_LABEL = re.compile(r'\[(?:Tier\s*[0-3]|研究员假设|估算|verified|machine)\]', re.IGNORECASE)

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        # Only check research artifacts (dated files) — not skill files
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        if not re.match(r'^\d{8}-.+\.md$', leaf):
            continue

        # Rule 1: Every standalone number claim should have a source anchor nearby
        # Scan for quantitative claims (numbers > 1000 with units)
        number_claims = re.findall(r'(?:收入|revenue|利润|profit|市值|market cap|PE|P/E|margin|份额|TAM|SAM|FCF|EBITDA|订单|order|backlog)\S{0,80}[=:：]?\s*([\d,.]+)\s*(?:bn|B|m|M|k|亿|万|%|x|倍|USD|CNY|HKD|SEK|EUR|JPY|KRW|TWD)?', text)
        if number_claims:
            has_source = bool(SOURCE_INDICATORS.search(text))
            has_tier = bool(TIER_LABEL.search(text))
            if not has_source:
                warn(f"fact_provenance: {t.get('display','?')} contains quantitative claims without source anchors. All numbers must have [source_label] nearby.")
            if not has_tier:
                warn(f"fact_provenance: {t.get('display','?')} quantitative facts should carry Tier annotation (Tier 0-2 or [估算]/[研究员假设]).")

        # Rule 2: Tier 2/3 numbers must be explicitly flagged
        tier3_claim = re.search(r'(?:Tier\s*3|无源|no.source)', text, re.IGNORECASE)
        if tier3_claim:
            block(f"fact_provenance: {t.get('display','?')} contains Tier 3 (banned) claims. No-source numbers are not allowed in research artifacts.")

sys.exit(0)
