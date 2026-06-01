"""Check: DCF xlsx must have 7 canonical slots."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_shared_strings, get_all_cell_text

REQUIRED = [
    ("Market Data & Key Inputs", r"(?i)(market data\s*(?:&|and)\s*key inputs|key inputs)"),
    ("Scenario Assumptions", r"(?i)(scenario assumptions|bear case|base case|bull case)"),
    ("Free Cash Flow", r"(?i)(free cash flow|\bfcf\b)"),
    ("WACC", r"(?i)\bwacc\b"),
    ("Terminal Value", r"(?i)(terminal value|terminal growth|exit multiple)"),
    ("Valuation Summary", r"(?i)(valuation summary|equity value|implied share price|price target)"),
    ("Sensitivity Analysis", r"(?i)(sensitivity analysis|sensitivity table)"),
]
IDENTITY = re.compile(r"(?i)(dcf|wacc|terminal value|sensitivity analysis)")

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    if not IDENTITY.search(text):
        continue
    missing = [label for label, pat in REQUIRED if not re.search(pat, text)]
    if missing:
        block(f"dcf_structure_floor: {t.get('display','xlsx')} missing canonical DCF slots: {', '.join(missing)}.")
