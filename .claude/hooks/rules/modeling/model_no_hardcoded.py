"""Check: projection/valuation sheets must use formulas."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload, get_formula_count

TGT = re.compile(r'(?i)(income|balance|cash flow|dcf|discount|valuation|sensitivity|forecast|projection)')
EXC = re.compile(r'(?i)(assump|input|raw|source|data|readme|cover|check|audit|validation)')

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    relevant = [n for n in names if TGT.search(n) and not EXC.search(n)]
    if not relevant: continue
    fc = get_formula_count(t)
    if fc < 10:
        block(f"model_no_hardcoded: {t.get('display', 'xlsx')} has only {fc} formulas in projection/valuation sheets. Use formulas, not hardcoded values.")
sys.exit(0)
