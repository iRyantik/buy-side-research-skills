"""Check: check/audit cells must all = 0 (pass). Uses Excel COM for live calculation."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import block, warn
from rules.modeling._common import load_payload, get_xlsx_targets, get_sheet_names_from_payload

CHECK_RE = re.compile(r'(?i)(check|audit|validation|control|balance.check|integrity)')
TOLERANCE = 1e-6

payload = load_payload()
for t in get_xlsx_targets(payload):
    names = get_sheet_names_from_payload(t)
    check_sheets = [n for n in names if CHECK_RE.search(n)]
    if not check_sheets:
        continue

    path = t.get("path", "")
    if not path or not os.path.exists(path):
        continue

    try:
        from _excel_bridge import get_workbook_data
        data = get_workbook_data(path)
    except ImportError as e:
        warn(f"model_checks_result: cannot load Excel bridge ({e}). pip install pywin32 (Windows) or ensure Excel is available (macOS).")
        continue
    except Exception as e:
        warn(f"model_checks_result: Excel open failed for {t.get('display', path)}: {e}")
        continue

    failures = []
    for sn in check_sheets:
        sheet_data = data.get("sheets", {}).get(sn, {})
        cells = sheet_data.get("cells", [])
        for r_idx, row in enumerate(cells):
            for c_idx, (val, formula) in enumerate(row):
                if val is None:
                    continue
                try:
                    v = float(val)
                    if abs(v) > TOLERANCE:
                        col_letter = chr(65 + c_idx) if c_idx < 26 else f"C{c_idx+1}"
                        failures.append(f"{sn}!{col_letter}{r_idx+1}={v}")
                except (ValueError, TypeError):
                    pass

    if failures:
        block(
            f"model_checks_result: {t.get('display', 'xlsx')} has {len(failures)} failed checks. "
            f"All check cells must = 0. Failures: {', '.join(failures[:10])}"
            + ("..." if len(failures) > 10 else "")
        )
sys.exit(0)
