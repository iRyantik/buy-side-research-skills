"""Check: internet source or Bridge anchors in market-snapshot skills must have fallback disclosure, Resources entry, and correct field scope."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

ANCHOR_INTERNET = re.compile(r'\[I\d+\]\(https?://[^)]+\)')
ANCHOR_BRIDGE = re.compile(r'\[LBG\d+\]\(https?://[^)]+\)')
ANCHOR_INTERNET_LOCAL = re.compile(r'\[I\d+\]\((?:\.\.?/|/[^)]+\))')
LBG_LOCAL = re.compile(r'\[LBG\d+\]\((?:\.\.?/|/[^)]+\))')
ALLOWED_FIELD = re.compile(r'(?i)(market[_ -]?quote|valuation[_ -]?snapshot|price[_ -]?action|consensus|financial[_ -]?snapshot|liquidity|borrow|short interest|implied move|fx|premium|discount|spread|multiple|p/e|p/b|ev/ebitda|ev/sales|fcf yield|market multiple|crowding|股价|估值|流动性|借券|做空|隐含波动|预期|一致预期|溢价|折价|点差|倍数|汇率)')
FORBIDDEN_FIELD = re.compile(r'(?i)(business description|segment economics|customer|product|backlog|company disclosed|management said|disclosure wording|业务描述|分部经济|客户|产品|积压订单|积压|公司披露|管层表示|披露口径)')
SKILL_FILE = re.compile(r'stock-quickread|consensus-map|earnings-setup|pair-trade|pair-note|alpha-thesis|bear-pre-mortem|peer-deep-dive|industry-(?:quickread|landscape)|candidate-screener|information-impact')
SKILL_HEADING = re.compile(r'(?im)^#\s*(Stock Quickread|Consensus Map|Earnings Setup|Pair Trade|Pair Snapshot|Pair Note|Alpha Thesis|Bear Pre-Mortem|Peer Deep Dive|Industry (?:Quickread|Landscape)|Cross-Market Compare|Candidate Screener|Information Impact)\b')

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        is_target = (t.get("kind") == "file" and bool(SKILL_FILE.search(leaf))) or bool(SKILL_HEADING.search(text))
        if not is_target:
            continue

        has_internet = bool(ANCHOR_INTERNET.search(text))
        has_bridge = bool(ANCHOR_BRIDGE.search(text))
        if not has_internet and not has_bridge:
            continue

        body = text.split("## Resources")[0] if "## Resources" in text else text
        resources = text.split("## Resources")[1] if "## Resources" in text else ""

        if not re.search(r'(?i)(internet source|trusted-market-bridge)', body) or not re.search(r'(?i)fallback', body):
            block(f"market_snapshot_source_boundary: {t.get('display','?')} uses internet/bridge anchors without required fallback disclosure.")

        if "## Resources" not in text or not resources.strip():
            block(f"market_snapshot_source_boundary: {t.get('display','?')} uses fallback market-snapshot anchors but missing ## Resources section.")

        for line in body.split("\n"):
            matched = ANCHOR_INTERNET.search(line) or ANCHOR_BRIDGE.search(line)
            if not matched:
                continue
            if FORBIDDEN_FIELD.search(line):
                block(f"market_snapshot_source_boundary: {t.get('display','?')} uses fallback anchors in business-fact/disclosure-truth context.")
            if not ALLOWED_FIELD.search(line):
                block(f"market_snapshot_source_boundary: {t.get('display','?')} uses fallback anchors outside allowed market/valuation/consensus/liquidity/price-action fields.")
