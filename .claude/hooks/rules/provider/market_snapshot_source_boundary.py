"""Check: internet source or Bridge anchors in market-snapshot skills must have fallback disclosure, Resources entry, and correct field scope.

Optimized 2026-08: the old per-line scan produced false positives and expensive fix loops —
URL text polluted keyword matching, claims split across lines were mis-flagged, and block
messages carried no line number. Now:
  1. anchor URLs are stripped before keyword matching (URL text never counts as content)
  2. keyword matching runs on blank-line-separated paragraphs (context window)
  3. block ONLY when an anchored paragraph carries business-fact keywords and NO
     market/valuation keyword anywhere in the same paragraph (mixed claims pass)
  4. fallback-disclosure / Resources checks downgraded to warn (format-only;
     Resources presence is enforced by global source_contract rules)
  5. every block message carries line number + content snippet
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

ANCHOR_INTERNET = re.compile(r'\[I\d+\]\(https?://[^)]+\)')
ANCHOR_BRIDGE = re.compile(r'\[LBG\d+\]\(https?://[^)]+\)')
ANCHOR_INTERNET_LOCAL = re.compile(r'\[I\d+\]\((?:\.\.?/|/[^)]+\))')
LBG_LOCAL = re.compile(r'\[LBG\d+\]\((?:\.\.?/|/[^)]+\))')
ALLOWED_FIELD = re.compile(r'(?i)(market[_ -]?quote|valuation[_ -]?snapshot|price[_ -]?action|consensus|financial[_ -]?snapshot|liquidity|borrow|short interest|implied move|fx|premium|discount|spread|multiple|p/e|p/b|ev/ebitda|ev/sales|fcf yield|market multiple|crowding|\bpe\b|市盈率|市值|market cap|股价|估值|流动性|借券|做空|隐含波动|预期|一致预期|溢价|折价|点差|倍数|汇率|\b\d+(?:\.\d+)?\s*x\b)')
FORBIDDEN_FIELD = re.compile(r'(?i)(business description|segment economics|customer|product|backlog|company disclosed|management said|disclosure wording|业务描述|分部经济|客户|产品|积压订单|积压|公司披露|管层表示|披露口径)')
SKILL_FILE = re.compile(r'stock-quickread|consensus-map|earnings-setup|pair-trade|pair-note|alpha-thesis|bear-pre-mortem|peer-deep-dive|industry-(?:quickread|landscape)|candidate-screener|information-impact')
SKILL_HEADING = re.compile(r'(?im)^#\s*(Stock Quickread|Consensus Map|Earnings Setup|Pair Trade|Pair Snapshot|Pair Note|Alpha Thesis|Bear Pre-Mortem|Peer Deep Dive|Industry (?:Quickread|Landscape)|Cross-Market Compare|Candidate Screener|Information Impact)\b')

_ANCHOR_ANY = re.compile(r'\[[A-Z]+\d+\]\([^)]*\)')


def _strip_anchors(text: str) -> str:
    """Remove [X#](url|path) markdown so URL/path text never pollutes keyword matching."""
    return _ANCHOR_ANY.sub('', text)


def _paragraphs(body: str):
    """Split body into paragraphs (blank-line separated), each a list of (lineno, line)."""
    paras, current = [], []
    for lineno, line in enumerate(body.split("\n"), 1):
        if not line.strip():
            if current:
                paras.append(current)
                current = []
            continue
        current.append((lineno, line))
    if current:
        paras.append(current)
    return paras


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

        display = t.get('display', '?')
        body = text.split("## Resources")[0] if "## Resources" in text else text
        resources = text.split("## Resources")[1] if "## Resources" in text else ""

        # Field-scope check on paragraph windows: block only when an anchored
        # paragraph carries business-fact keywords and NO market keyword.
        # Runs FIRST: warn() below exits 0, which would mask a real violation.
        for para in _paragraphs(body):
            orig = "\n".join(line for _, line in para)
            if not (ANCHOR_INTERNET.search(orig) or ANCHOR_BRIDGE.search(orig)):
                continue
            stripped = _strip_anchors(orig)
            if not FORBIDDEN_FIELD.search(stripped):
                continue
            if ALLOWED_FIELD.search(stripped):
                continue  # mixed claim — anchor plausibly serves the market part
            for lineno, line in para:
                if ANCHOR_INTERNET.search(line) or ANCHOR_BRIDGE.search(line):
                    snippet = _strip_anchors(line).strip()
                    block(f"market_snapshot_source_boundary: {display} L{lineno} uses fallback anchor in business-fact context (no market keyword in paragraph): {snippet[:120]}")

        # Format-level requirements — warn only. Source integrity is the block above.
        if not re.search(r'(?i)(internet source|trusted-market-bridge)', body) or not re.search(r'(?i)fallback', body):
            warn(f"market_snapshot_source_boundary: {display} uses internet/bridge anchors without required fallback disclosure.")
        if "## Resources" not in text or not resources.strip():
            warn(f"market_snapshot_source_boundary: {display} uses fallback market-snapshot anchors but missing ## Resources section.")
