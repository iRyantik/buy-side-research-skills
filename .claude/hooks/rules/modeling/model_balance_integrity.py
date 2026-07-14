"""Check: model must have balance check trace and cash tie-out."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload, get_all_cell_text, get_shared_strings

CHECK_RE = re.compile(r'(?i)(check|audit|validation|control)')
BAL_RE = re.compile(r'(?i)(balance check|assets?.{0,40}liabilit(?:y|ies).{0,40}equity|a\s*=\s*l\s*\+\s*e)')
TIE_RE = re.compile(r'(?i)(cash tie|tie-?out|ending cash.{0,40}(balance sheet|bs cash)|cash balance check)')

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    if not any(re.search(r'(?i)(is|income|p&l|bs|balance|cf|cash flow)', n) for n in names):
        continue
    search = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    has_check = any(CHECK_RE.search(n) for n in names)
    has_bal = bool(BAL_RE.search(search))
    has_tie = bool(TIE_RE.search(search))
    if not (has_check or has_bal):
        block(f"model_balance_integrity: {t.get('display', 'xlsx')} must have balance check area or A=L+E trace.")
    if not has_tie:
        block(f"model_balance_integrity: {t.get('display', 'xlsx')} must have ending-cash tie-out trace.")
sys.exit(0)
