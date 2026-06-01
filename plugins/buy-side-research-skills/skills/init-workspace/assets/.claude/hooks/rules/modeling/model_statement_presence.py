"""Check: xlsx must have IS, BS, CF sheet tabs."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload

IS_RE = re.compile(r'(?i)\b(is|p&l|income(?: statement)?)\b')
BS_RE = re.compile(r'(?i)\b(bs|balance(?: sheet)?)\b')
CF_RE = re.compile(r'(?i)\b(cf|cfs|cash ?flow(?: statement)?)\b')

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    if not any(IS_RE.search(n) or BS_RE.search(n) or CF_RE.search(n) for n in names):
        continue
    has_is = any(IS_RE.search(n) for n in names)
    has_bs = any(BS_RE.search(n) for n in names)
    has_cf = any(CF_RE.search(n) for n in names)
    if not (has_is and has_bs and has_cf):
        block(f"model_statement_presence: {t.get('display', 'xlsx')} must have IS, BS, and CF sheet tabs.")
sys.exit(0)
