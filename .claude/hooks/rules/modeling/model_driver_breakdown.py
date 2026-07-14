"""Check: driver sheets must not contain blocked status markers."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload, get_all_cell_text

IS_PAT = re.compile(r'(?i)\b(is|income(?: statement)?|p&l)\b')
DRV_PAT = re.compile(r'(?i)\b(assumptions|inputs|drivers?)\b')
BAD = re.compile(r'(?i)(not-disclosed|review-only|unresolved|placeholder|needs.mapping|source.pending|pending)')

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    has_is = any(IS_PAT.search(n) for n in names)
    has_drv = any(DRV_PAT.search(n) for n in names)
    if not (has_is and has_drv): continue
    text = get_all_cell_text(t)
    if BAD.search(text):
        matches = set(BAD.findall(text))
        block(f"model_driver_breakdown: {t.get('display', 'xlsx')} has unresolved driver markers: {matches}. Resolve before finalizing.")
sys.exit(0)
