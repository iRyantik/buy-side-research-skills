"""Check: model-update must document what changed."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload, search_all_text

payload = load_payload()
for t in get_xlsx_targets(payload):
    leaf = os.path.basename(t.get('path', '') or '')
    if 'model-update' not in leaf and 'model_update' not in leaf: continue
    has = any(re.search(r'(?i)(change|update|revision|delta|version|what.changed)', n) for n in get_sheet_names_from_payload(t))
    has = has or search_all_text(t, r'(?i)(change|update|revision|delta)')
    if not has:
        block(f"model_update_change_map: {t.get('display', 'xlsx')} must document what changed since prior version.")
sys.exit(0)
