"""Check: DCF xlsx must include WACC, TV, bridge, sensitivity, no placeholders."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_shared_strings, get_all_cell_text

IDENTITY = re.compile(r"(?i)(dcf|wacc|terminal value|sensitivity analysis)")
BRIDGE = re.compile(r"(?i)(valuation summary|equity value|equity bridge|implied share price|per share)")
SENSITIVITY = re.compile(r"(?i)(sensitivity analysis|wacc\s*vs|terminal growth|beta\s*vs|revenue growth\s*vs|ebit margin)")
PLACEHOLDER = re.compile(r"(?i)(todo|placeholder|manual step|use excel.?s data table feature|what-if analysis)")

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    if not IDENTITY.search(text):
        continue
    if not re.search(r'\bWACC\b', text) or not re.search(r'(?i)(terminal value|terminal growth|exit multiple)', text):
        block(f"dcf_audit_floor: {t.get('display','xlsx')} must include explicit WACC and terminal value basis.")
    if not BRIDGE.search(text):
        block(f"dcf_audit_floor: {t.get('display','xlsx')} must include a visible valuation bridge or valuation summary.")
    if not SENSITIVITY.search(text):
        block(f"dcf_audit_floor: {t.get('display','xlsx')} must include visible sensitivity table evidence.")
    if PLACEHOLDER.search(text):
        block(f"dcf_audit_floor: {t.get('display','xlsx')} still shows placeholder or manual-step language in DCF delivery.")
