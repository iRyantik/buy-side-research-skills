"""Check: DCF/comps/model-update output must state valuation basis."""
import re, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block

payload = {}
try: payload = json.load(sys.stdin)
except: pass

DCF = re.compile(r'(?im)^#\s*DCF')
COMPS = re.compile(r'(?im)^#\s*Comps? Analysis|Comparable')
UPDATE = re.compile(r'(?im)^#\s*Model Update')
VAL = re.compile(r'(?i)(price target|fair value|valuation|target multiple)')
WACC = re.compile(r'(?i)\bWACC\b')
TERM = re.compile(r'(?i)(terminal value|terminal growth|exit multiple)')
MULT = re.compile(r'(?i)(EV/EBITDA|P/E|EV/Sales|multiple|peer)')
ASOF = re.compile(r'(?i)(as of|as-of|updated|collected on)')
NORM = re.compile(r'(?i)(currency|fx|USD|fiscal|calendarized|LTM|NTM|normalization)')

for t in payload.get('targets', []):
    if t.get('kind') != 'file': continue
    text = t.get('text', '')
    leaf = os.path.basename(t.get('path', '') or '')
    if ('dcf-model' in leaf or DCF.search(text)) and VAL.search(text):
        if not (WACC.search(text) and TERM.search(text)):
            block(f"valuation_basis: {t.get('display', leaf)} DCF must state WACC and terminal value basis.")
    elif ('comps' in leaf or COMPS.search(text)):
        if not (MULT.search(text) and ASOF.search(text) and NORM.search(text)):
            block(f"valuation_basis: {t.get('display', leaf)} Comps must state multiples, as-of, and normalization basis.")
    elif ('model-update' in leaf or UPDATE.search(text)) and VAL.search(text):
        has_dcf = WACC.search(text) and TERM.search(text)
        has_comps = MULT.search(text) and ASOF.search(text) and NORM.search(text)
        if not (has_dcf or has_comps):
            block(f"valuation_basis: {t.get('display', leaf)} Updated valuation without DCF or comps basis.")
sys.exit(0)
