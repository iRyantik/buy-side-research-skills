"""Check: non-information-impact disclosure-fact skills must not use internet/bridge fallback anchors for business truth."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn

FALLBACK_ANCHOR = re.compile(r'\[(?:I|LBG)\d+\]\([^)]+\)')
ALLOWED_II = re.compile(r'(?i)(market[_ -]?reaction|price[_ -]?action|share[_ -]?price|stock[_ -]?move|trading[_ -]?volume|implied[_ -]?move|gap[_ -]?up|gap[_ -]?down|股价|涨跌|跳空|成交量|隐含波动|价格反应)')
FORBIDDEN = re.compile(r'(?i)(company disclosed|management said|customer|supplier|segment|product|backlog|kpi|order|capacity|shipment|business model|project|contract|guidance wording)')
SKILL_FILE = re.compile(r'company-primer|mechanism-(?:map|insight)|driver-map|primary-research-plan|information-impact')
SKILL_HEADING = re.compile(r'(?im)^#\s*(Company Primer|Mechanism (?:Map|Insight)|Driver Map|Primary Research Plan|Information Impact)\b')

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

        is_ii = bool(re.search(r'(?im)^#\s*Information Impact\b', text))
        body = text.split("## Resources")[0] if "## Resources" in text else text
        if not FALLBACK_ANCHOR.search(body):
            continue

        for line in body.split("\n"):
            if not FALLBACK_ANCHOR.search(line):
                continue
            if is_ii and ALLOWED_II.search(line) and not FORBIDDEN.search(line):
                continue
            block(f"disclosure_fact_source_boundary: {t.get('display','?')} uses internet/bridge fallback in a disclosure-fact workflow.")
