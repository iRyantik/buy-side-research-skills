"""Check: 3-statement xlsx must have structured driver breakdown."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_shared_strings, get_all_cell_text

IDENTITY = re.compile(r"(?i)(3-?statement|revenue growth|drivers|price.?volume.?mix|segment driver)")
DRIVER_BLOCK = re.compile(r"(?i)(assumptions|inputs|drivers?)")
STRUCTURED = re.compile(r"(?i)(revenue growth|volume.?price.?mix|segment driver|driver block|assumption block|price.?mix|volume)")

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    if not IDENTITY.search(text):
        continue
    has_block = bool(DRIVER_BLOCK.search(text))
    has_structured = bool(STRUCTURED.search(text))
    if not (has_block and has_structured):
        block(f"three_statement_driver_floor: {t.get('display','xlsx')} must show a structured revenue/driver breakdown (assumption block, segment driver, or volume-price-mix style split), not only a single topline growth statement.")
