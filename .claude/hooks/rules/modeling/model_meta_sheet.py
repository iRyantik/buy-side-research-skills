"""Check: every model xlsx must have a _meta sheet with ticker, artifact, actuals_run_id, as_of."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload

META_SKILL = re.compile(r'(3-statement-model|dcf-model|comps-analysis|model-update)')
REQUIRED = ["ticker", "artifact", "actuals_run_id", "as_of"]

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    if "_meta" not in names:
        block(f"meta_sheet_presence: {t.get('display','xlsx')} is missing a '_meta' sheet with ticker/artifact/actuals_run_id/as_of.")
        continue

    import openpyxl
    wb = openpyxl.load_workbook(t["path"], read_only=True)
    ws = wb["_meta"]
    meta = {}
    for row in ws.iter_rows(min_row=1, max_col=2, values_only=True):
        if row[0] and row[1]:
            meta[str(row[0]).strip().lower().replace(" ", "_")] = str(row[1]).strip()
    wb.close()

    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        block(f"meta_sheet_presence: {t.get('display','xlsx')} _meta sheet missing fields: {missing}.")

    if "artifact" in meta and not META_SKILL.search(meta["artifact"]):
        block(f"meta_sheet_presence: {t.get('display','xlsx')} _meta.artifact must be one of 3-statement-model/dcf-model/comps-analysis/model-update.")
sys.exit(0)
