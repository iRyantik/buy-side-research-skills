"""Check: 3SM, DCF, Comps structural requirements."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    all_n = ' '.join(names)
    leaf = os.path.basename(t.get('path', '') or '')

    if re.search(r'(?i)(3-statement|three.statement)', leaf):
        ok = all(re.search(p, all_n) for p in [r'\b(is|income|p&l)\b', r'\b(bs|balance)\b', r'\b(cf|cash.flow)\b', r'(?i)(assump|input|driver)'])
        if not ok:
            block(f"model_statement_structure: {t.get('display', 'xlsx')} 3SM must have IS, BS, CF, and assumptions sheets.")
    if re.search(r'(?i)(dcf|discount)', leaf):
        if not (re.search(r'(?i)(projection|forecast)', all_n) and re.search(r'(?i)(valuation|dcf|discount)', all_n)):
            block(f"model_statement_structure: {t.get('display', 'xlsx')} DCF must have projection and valuation sheets.")
    if re.search(r'(?i)(comps?|comparable)', leaf):
        if not re.search(r'(?i)(comps?|comparable|peer)', all_n):
            block(f"model_statement_structure: {t.get('display', 'xlsx')} Comps must have peer comparison sheet.")
sys.exit(0)
