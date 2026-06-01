"""Check: historical actuals must use sourced data, not placeholders."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload, get_all_cell_text

STMT = re.compile(r'(?i)\b(is|p&l|income(?: statement)?)\b|\b(bs|balance(?: sheet)?)\b|\b(cf|cash ?flow)\b')
BLOCKED = re.compile(r'(?i)(provider-gap|unavailable|failed|review-only|needs.mapping|llm-extracted|partial-review|unreconciled|not-disclosed|source.pending)')

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    if not any(STMT.search(n) for n in names): continue
    text = get_all_cell_text(t)
    if not text: continue
    if re.search(r'(?i)(actual|historical|fy\s*20)', text) and BLOCKED.search(text):
        matches = set(BLOCKED.findall(text))
        block(f"model_historical_actuals: {t.get('display', 'xlsx')} has unresolved actuals: {matches}. Label gaps.")
sys.exit(0)
