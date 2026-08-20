"""Check: disclosure-fact artifacts must not source business facts to internet/bridge fallback anchors.

Optimized 2026-08-20 mirroring market_snapshot_source_boundary's rewrite
(same false-positive class — URL pollution, mixed claims, no line numbers):
  1. anchor URLs are stripped before keyword matching (URL text never counts as content)
  2. keyword matching runs on blank-line-separated paragraphs (context window,
     multi-line claims no longer split by per-line scans)
  3. three enforcement tracks:
     - strict (named disclosure-fact skills: driver-map / mechanism-* /
       company-primer / primary-research-plan): business-fact keyword in an
       anchored paragraph → BLOCK. No market rescue — these workflows must
       source business truth from company disclosure ([S#]) only. Tech/industry
       context paragraphs (NVIDIA engineering blogs, papers) pass.
     - information-impact: business-fact keyword blocked UNLESS the paragraph
       also carries a market-reaction keyword (mixed claims pass — the anchor
       plausibly serves the price part)
     - backstop (dated artifact with an unregistered skill token — the rename
       dodge: [driver-map] → [market-scan]): business-fact keyword + no market
       keyword in the paragraph → BLOCK. Mirrors the market hook's vocabulary
       so legit market-context artifacts pass while renamed dodgers get caught.
  4. every block message carries line number + content snippet
  5. fallback-disclosure / Resources checks downgraded to warn (format-only;
     Resources presence is enforced by global source_contract rules)
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

ANCHOR_FALLBACK = re.compile(r'\[(?:I|LBG)\d+\]\([^)]+\)')
_ANCHOR_ANY = re.compile(r'\[[A-Z]+\d+\]\([^)]*\)')

# Business-fact vocabulary (strict + II tracks). Tech/mechanism context that does
# NOT match these may use internet anchors (engineering blogs, papers, product
# pages describing the mechanism — not the company's business truth).
FORBIDDEN_D = re.compile(r'(?i)(company disclosed|management said|customer|supplier|segment|product|backlog|\border\b|capacity|shipment|business model|project|contract|guidance wording|客户|客戶|供应商|供應商|分部|产品|產品|订单|訂單|积压|積壓|产能|產能|出货|出貨|合同|合约|合約|项目|項目|营收|營收|收入|毛利率|利润率|利潤率|市占率|市佔率|份额|份額|指引|披露)')
# Market-reaction vocabulary (II track + backstop rescue).
ALLOWED_II = re.compile(r'(?i)(market[_ -]?reaction|price[_ -]?action|share[_ -]?price|stock[_ -]?move|trading[_ -]?volume|implied[_ -]?move|gap[_ -]?up|gap[_ -]?down|股价|股價|涨跌|漲跌|跳空|成交量|市值|涨幅|漲幅|跌幅|单日|單日|盘中|盤中|收盘|收盤|涨停|漲停|跌停|指数|指數|板块|板塊|新高|回落|反弹|反彈|预期|一致预期|溢价|折价|折價|倍数|倍數|估值|市盈率|本益比|ETF|\+\s?\d+(?:\.\d+)?%|-\s?\d+(?:\.\d+)?%|\d+(?:\.\d+)?\s*[xX]|\d+(?:\.\d+)?\s*倍)')
# Backstop vocabulary mirrors market_snapshot_source_boundary (keep in sync with
# that file when either changes — the backstop is the market-track semantics for
# unregistered tokens).
FORBIDDEN_M = re.compile(r'(?i)(business description|segment economics|customer|product|backlog|company disclosed|management said|disclosure wording|业务描述|分部经济|客户|产品|积压订单|积压|公司披露|管层表示|披露口径)')
ALLOWED_M = re.compile(r'(?i)(market[_ -]?quote|valuation[_ -]?snapshot|price[_ -]?action|consensus|financial[_ -]?snapshot|liquidity|borrow|short interest|implied move|fx|premium|discount|spread|multiple|p/e|p/b|ev/ebitda|ev/sales|fcf yield|market multiple|crowding|\bpe\b|市盈率|市值|market cap|股价|估值|流动性|借券|做空|隐含波动|预期|一致预期|溢价|折价|点差|倍数|汇率|\b\d+(?:\.\d+)?\s*x\b)')

SKILL_FILE = re.compile(r'company-primer|mechanism-(?:map|insight)|driver-map|primary-research-plan|information-impact')
SKILL_HEADING = re.compile(r'(?im)^#\s*(Company Primer|Mechanism (?:Map|Insight)|Driver Map|Primary Research Plan|Information Impact)\b')
# Registered artifact tokens the disclosure track does NOT police: market-track
# skills (policed by market_snapshot_source_boundary) and other registered types
# (teach-in, meeting-minutes, ...) where internet context anchors are standard.
SKIP_TOKENS = {
    "stock-quickread", "consensus-map", "earnings-setup", "pair-trade",
    "pair-note", "alpha-thesis", "bear-pre-mortem", "peer-deep-dive",
    "industry-quickread", "industry-landscape", "candidate-screener",
    "cross-market-compare", "driver-model", "catalyst-map", "scenario-model",
    "moat-analysis", "company-history", "boss-brief", "market-sizing",
    "earnings-call", "management-commentary", "quarterly-tracker",
    "research-note", "meeting-minutes", "teach-in", "capital-allocation",
    "model-update", "post-earnings-quick",
}
DATED_FILE = re.compile(r'^\d{8}-')
TOKEN_RE = re.compile(r'^\d{8}-(?:\[([^\]]+)\]|([a-z0-9][a-z0-9.-]*))-')


def _strip_anchors(text: str) -> str:
    """Remove [X#](url|path) markdown so URL/path text never pollutes keyword matching."""
    return _ANCHOR_ANY.sub('', text)


def _paragraphs(body: str):
    """Split body into claim windows.

    Prose: blank-line-separated paragraphs. Markdown tables: each ROW is its own
    window — a table block is a series of independent claims with their own
    anchors, and one row's [I#] anchor must not be judged against another row's
    business words (those rows carry their own [S#]/[P#] anchors).
    """
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

    out = []
    for para in paras:
        if any(line.lstrip().startswith("|") for _, line in para) and all(
                "|" in line for _, line in para):
            out.extend([[p] for p in para])  # table block → per-row windows
        else:
            out.append(para)
    return out


def _block_at(display: str, para, reason: str):
    """Block on the first anchored line of the paragraph, with line number + snippet."""
    for lineno, line in para:
        if ANCHOR_FALLBACK.search(line):
            snippet = _strip_anchors(line).strip()
            block(f"disclosure_fact_source_boundary: {display} L{lineno} {reason}: {snippet[:120]}")
            return


def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        is_ii = bool(re.search(r'information-impact', leaf)) or bool(re.search(r'(?im)^#\s*Information Impact\b', text))
        named = bool(SKILL_FILE.search(leaf)) or bool(SKILL_HEADING.search(text))
        token = None
        if DATED_FILE.match(leaf):
            m = TOKEN_RE.match(leaf)
            if m:
                token = (m.group(1) or m.group(2)).lower()
        if is_ii:
            track = "ii"
        elif named:
            track = "strict"
        elif token and token not in SKIP_TOKENS:
            track = "backstop"  # unregistered token — content backstop against rename dodges
        else:
            continue

        display = t.get('display', '?')
        body = text.split("## Resources")[0] if "## Resources" in text else text
        resources = text.split("## Resources")[1] if "## Resources" in text else ""
        if not ANCHOR_FALLBACK.search(body):
            continue

        for para in _paragraphs(body):
            orig = "\n".join(line for _, line in para)
            if not ANCHOR_FALLBACK.search(orig):
                continue
            stripped = _strip_anchors(orig)
            if track == "strict":
                if FORBIDDEN_D.search(stripped):
                    _block_at(display, para, "business-fact claim uses fallback anchor in disclosure-fact workflow")
            elif track == "ii":
                if ALLOWED_II.search(stripped):
                    continue
                if FORBIDDEN_D.search(stripped):
                    _block_at(display, para, "business-fact claim uses fallback anchor without market-reaction context")
            else:  # backstop
                if not FORBIDDEN_M.search(stripped):
                    continue
                if ALLOWED_M.search(stripped):
                    continue  # market context — anchor plausibly serves the market part
                _block_at(display, para, f'unregistered skill token "{token}" — business-fact claim uses fallback anchor (no market keyword in paragraph)')

        # Format-level requirements — warn only. Source integrity is the block above.
        if not re.search(r'(?i)(internet source|trusted-market-bridge)', body) or not re.search(r'(?i)fallback', body):
            warn(f"disclosure_fact_source_boundary: {display} uses fallback anchors without required fallback disclosure.")
        if "## Resources" not in text or not resources.strip():
            warn(f"disclosure_fact_source_boundary: {display} uses fallback anchors but missing ## Resources section.")
