"""Rule: Data-claim cross-check — §2/§3 numbers must exist in actuals-resolved.json."""
import re, sys, os, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn
import os as _os
_ARTIFACT_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
def _is_artifact(fp): return bool(_ARTIFACT_RE.match(_os.path.basename(fp)))

# Only capture raw financial amounts: $1.23B, HK$45M, ¥500bn, HK$550M, 73.80亿, etc.
# Exclude ratios (37.8%, 0.71x), stock codes (0522), small numbers
NUM_RE = re.compile(
    r'(?:[$¥€£₩]|USD|HKD|CNY|JPY|KRW|EUR|HK\$|￥)\s*[\d,]+\.?\d*\s*[BMKbnmktn万亿亿万千百]?|'
    r'\b[\d,]+\.?\d+\s*(?:bn|B|million|M|亿|万)\b'
)
# Exclude patterns: ratios, percentages, stock codes
SKIP_RE = re.compile(r'^[\d,]+\.?\d*\s*(%|x|bps|pp)\b|^\d{4,6}$')

# 8 company-level skills
COMPANY_SKILLS = {
    "stock-quickread", "company-history", "driver-map",
    "alpha-thesis", "consensus-map", "earnings-setup",
    "bear-pre-mortem", "comps-analysis",
}
SLUG_RE = re.compile(
    r'^\d{4}-\d{2}-\d{2}-(?:' +
    '|'.join(s.replace('-', r'\-') for s in COMPANY_SKILLS) +
    r')-([a-z0-9][a-z0-9\-]*)\.md$', re.IGNORECASE
)


def _extract_numeric_claims(text: str) -> list[str]:
    """Extract unique numeric claims from §2 and §3 sections."""
    claims = set()
    # Find §2 and §3 in markdown
    for section_start in ['## 2.', '### 2.', '## 3.', '### 3.', '## 2 ', '## 3 ']:
        idx = text.find(section_start)
        if idx < 0:
            continue
        section_text = text[idx:idx + 3000]

        # Extract table rows and bullet points with numbers
        for line in section_text.split('\n'):
            matches = NUM_RE.findall(line)
            for m in matches:
                if SKIP_RE.match(m):
                    continue
                n = m.strip().replace(',', '').replace(' ', '')
                if len(n) >= 3:
                    claims.add(n)

    return sorted(claims)


def _normalize_num(s: str) -> float:
    """Try to parse a number string with unit suffix to raw float."""
    s = s.strip().replace(',', '').replace(' ', '')
    # Remove currency prefix
    for prefix in ['$', '¥', '€', '£', '₩', 'USD', 'HKD', 'CNY', 'JPY', 'KRW', 'EUR', 'HK$', '￥']:
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    # Extract unit multiplier
    multiplier = 1
    for pattern, mult in [('bn', 1e9), ('b', 1e9), ('million', 1e6), ('mil', 1e6),
                           ('M', 1e6), ('k', 1e3), ('万', 1e4), ('億', 1e8), ('亿', 1e8)]:
        if s.endswith(pattern):
            s = s[:-len(pattern)]
            multiplier = mult
            break
    # Remove % suffix (ratios — should be filtered but safety)
    if s.endswith('%'):
        s = s[:-1]
    try:
        return float(s) * multiplier
    except ValueError:
        return None


def _extract_values(obj, values: set):
    """Recursively collect all numeric values from data-field dicts (handles v2.2 period wrapper)."""
    if isinstance(obj, dict):
        if 'value' in obj and 'source_layer' in obj:
            val = obj.get('value')
            if val is not None and isinstance(val, (int, float)):
                values.add(float(val))
                values.add(round(val, 1))
                values.add(round(val, 2))
            return
        for k, v in obj.items():
            if k.startswith('_'):
                continue
            _extract_values(v, values)
    elif isinstance(obj, list):
        for item in obj:
            _extract_values(item, values)


def _collect_actuals_values(data: dict) -> set[float]:
    """Collect all numeric values from actuals-resolved.json (v2.2 dual-period aware)."""
    values = set()
    for section in ['income_statement', 'balance_sheet', 'cash_flow', 'market_data']:
        _extract_values(data.get(section, {}), values)
    # Segment data
    for seg in data.get('segments', {}).get('segments', []):
        for k in ['revenue', 'profit']:
            if k in seg and seg[k] is not None:
                values.add(float(seg[k]))
    return values


def check(ctx: dict):
    if ctx.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        return

    for target in ctx.get("targets", []):
        if target.get("kind") != "file":
            continue
        path = target.get("path") or ""
        text = target.get("text", "")
        display = target.get("display", "unknown")
        leaf = Path(path).name

        m = SLUG_RE.match(leaf)
        if not m:
            continue

        company_slug = m.group(1).lower()
        root = ctx.get("cwd", "")
        financial_data_path = os.path.join(
            root, "topics", "company", company_slug,
            "_cache", "financial-data", "internal", "actuals-resolved.json"
        )
        if not os.path.isfile(financial_data_path):
            continue  # financial_data_gate handles this

        try:
            with open(financial_data_path, 'r', encoding='utf-8') as fh:
                actuals = json.load(fh)
        except Exception:
            continue

        actuals_values = _collect_actuals_values(actuals)
        claims = _extract_numeric_claims(text)
        if not claims:
            continue

        unmatched = []
        for claim in claims[:30]:  # check first 30 unique claims
            n = _normalize_num(claim)
            if n is None:
                continue
            # Tolerance: numbers with unit suffix (rounded) → 2%; raw numbers → 0.5%
            is_rounded = bool(re.search(r'[MKB億万千]', claim, re.IGNORECASE)) and claim.endswith(('M','B','K','亿','万','bn'))
            tolerance = 0.02 if is_rounded else 0.005
            matched = False
            n_abs = abs(n)
            for av in actuals_values:
                av_abs = abs(av)
                if av_abs == 0 and n_abs == 0:
                    matched = True; break
                if av_abs != 0 and abs(n_abs - av_abs) / max(n_abs, av_abs) < tolerance:
                    matched = True; break
                # Also check: is claim a derived ratio? (n% = a/b?)
                # Skip if it looks like a calculated percentage
            if not matched:
                unmatched.append(claim)

        if len(unmatched) >= 3:
            block(
                f"Blocked by data_claim_cross_check: {display} has {len(unmatched)} numeric claims "
                f"not found in actuals-resolved.json for '{company_slug}': {', '.join(unmatched[:5])}. "
                f"Run /financial-data --fill-gaps {company_slug} to fill missing data OR "
                f"add [ND] / [推算] markers with source annotations."
            )
