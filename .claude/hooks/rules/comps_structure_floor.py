"""Check: comps-analysis xlsx must have 5 canonical slots."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_shared_strings, get_all_cell_text

REQUIRED = [
    ("Header Block", r"(?i)(comparable company analysis|as of|all figures in)"),
    ("Operating Metrics", r"(?i)(operating metrics|operating statistics|financial metrics)"),
    ("Valuation Multiples", r"(?i)(valuation multiples|ev/ebitda|p/e|ev/sales)"),
    ("Statistics", r"(?i)(maximum|75th percentile|median|25th percentile|minimum|statistics)"),
    ("Notes / Methodology", r"(?i)(notes|methodology|source)"),
]
IDENTITY = re.compile(r"(?i)(comparable company analysis|valuation multiples|operating metrics|statistics)")

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    if not IDENTITY.search(text):
        continue
    missing = [label for label, pat in REQUIRED if not re.search(pat, text)]
    if missing:
        block(f"comps_structure_floor: {t.get('display','xlsx')} missing canonical comps slots: {', '.join(missing)}.")
