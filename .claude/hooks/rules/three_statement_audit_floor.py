"""Check: 3-statement xlsx audit — BS balance, CF tie-out, retained earnings, master check, debt/equity ties."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block
from rules.modeling._common import load_payload, get_xlsx_targets, get_shared_strings, get_all_cell_text

IDENTITY = re.compile(r"(?i)(3-?statement|all checks pass|balance sheet balance|retained earnings)")
BALANCE = re.compile(r"(?i)(balance sheet balance|assets?\s*-\s*liabilit(?:y|ies)\s*-\s*equity|assets?\s*=\s*liabilit(?:y|ies)\s*\+\s*equity)")
CASH_TIE = re.compile(r"(?i)(cash tie-?out|ending cash.{0,50}(balance sheet|bs cash)|cf ending cash.{0,50}bs cash)")
RETAINED = re.compile(r"(?i)(retained earnings roll-?forward|retained earnings|ni[- /]?dividend)")
MASTER_CHECK = re.compile(r"(?i)(master check|all checks pass|errors detected)")
DEBT_PRESENCE = re.compile(r"(?i)(debt schedule|total debt|debt balance|debt maturity)")
DEBT_TIE = re.compile(r"(?i)(debt tie-?out|debt balance tie|debt roll-?forward)")
EQUITY_PRESENCE = re.compile(r"(?i)(equity issuance|apic|common stock|share issuance)")
EQUITY_TIE = re.compile(r"(?i)(equity raise tie-?out|common stock/apic|equity issuance tie)")

payload = load_payload()
for t in get_xlsx_targets(payload):
    text = get_shared_strings(t) + "\n" + get_all_cell_text(t)
    if not IDENTITY.search(text):
        continue
    d = t.get('display', 'xlsx')
    if not BALANCE.search(text):
        block(f"three_statement_audit_floor: {d} must include a Balance Sheet Balance audit row showing Assets - Liabilities - Equity = 0.")
    if not CASH_TIE.search(text):
        block(f"three_statement_audit_floor: {d} must include an explicit CF ending cash to BS cash tie-out.")
    if not RETAINED.search(text):
        block(f"three_statement_audit_floor: {d} must include a retained earnings roll-forward or NI-dividend linkage audit row.")
    if not MASTER_CHECK.search(text):
        block(f"three_statement_audit_floor: {d} must include a master check with explicit pass/fail status.")
    if DEBT_PRESENCE.search(text) and not DEBT_TIE.search(text):
        block(f"three_statement_audit_floor: {d} shows debt schedule content but no explicit Debt Tie-Out.")
    if EQUITY_PRESENCE.search(text) and not EQUITY_TIE.search(text):
        block(f"three_statement_audit_floor: {d} shows equity issuance/APIC content but no explicit Equity Raise Tie-Out.")
