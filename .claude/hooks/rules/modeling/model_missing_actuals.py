"""Check: missing actuals must be labeled, not zero-filled."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_all_cell_text

BLOCKED = re.compile(r'(?i)(provider-gap|unavailable|failed|review-only|needs.mapping|source.pending)')

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_all_cell_text(t)
    if not text: continue
    if re.search(r'(?i)(3-statement|historical|actuals)', text) and '0' in text:
        if not BLOCKED.search(text):
            block(f"model_missing_actuals: {t.get('display', 'xlsx')} may have missing actuals filled as zero. Label gaps.")
sys.exit(0)
