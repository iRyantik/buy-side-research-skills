"""Pre-Write Gate: run source_contract + claim_proximity + ledger_floor
before Write/Edit tool executes. Block before the file is written, not after.

Reads content from tool_input (content / new_string) rather than from disk.

When a CHECK blocks, the agent reads the message and knows what to fix:
- "Go back to Step 5 and download" → step_5_download
- "Go back to Step 4 and verify" → step_4_verify
- "Re-run financial-data --lite" → rerun_financial_data
- "Fix source format" → fix_source_format
- "Fix the Pipeline header" → fix_pipeline_header
"""
import re, sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    block, warn, load_stdin_payload, get_tool_name, get_tool_input,
    get_body_without_resources, get_resources_entries, get_short_anchor_matches,
    is_valid_source_target,
)

_ARTIFACT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')
ANCHOR_CODE_RE = re.compile(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()')
SOURCE_ANCHOR_RE = re.compile(r'\[(?:S\d+|I\d+|LBG\d+|P\d+|SRC\d+)\]')
FACTUAL_MARKERS_RE = re.compile(
    r'(?:(?<!\w)[\d,.]+%|(?<!\w)[\d,.]+x(?![/\w])|(?<!\w)\$[\d,.]+[bmk]|'
    r'(?:EUR|USD|CNY)\s*[\d,.]+[bmk]?)'
)

STANDARD_CODE_RE = re.compile(r'^(?:S|P|I|LBG|R|SRC)\d+$')
SOURCE_WORDS = {
    'yfinance', 'yahoo', 'yahoo finance', 'google', 'google finance', 'bloomberg',
    'marketscreener', 'chartmill', 'stockanalysis', 'gurufocus', 'simplywall',
    'tipranks', 'investing', 'investing.com', 'morgan stanley', 'bernstein',
    'socgen', 'bits&chips', 'reuters', 'digitimes',
}
NON_SOURCE_LABELS = {
    '推算', '未披露', '缺图', '估算', '需查证', '来源待补', '来源待确认',
    'ND', 'NA', 'N/A', 'TBD', 'TODO', 'E', '共识', 'A', 'LTM', 'NTM',
}
ANNOTATION_PREFIXES = ('ND', '推算', '未披露', '缺图', '估算', '需查证', '来源待补', '来源待确认')


def _is_artifact_path(filepath: str) -> bool:
    leaf = os.path.basename(filepath) if filepath else ""
    return bool(_ARTIFACT_RE.match(leaf))


def _extract_write_content(payload: dict) -> tuple:
    tool = get_tool_name(payload)
    ti = get_tool_input(payload)
    path = ti.get("file_path", "") or ti.get("target_file", "") or ""
    if not _is_artifact_path(path):
        return None, None
    if tool == "Write":
        return path, ti.get("content", "")
    elif tool in ("Edit", "MultiEdit"):
        return path, ti.get("new_string", "")
    elif tool == "Bash":
        return path, None
    return None, None


def _find_ledger_for_artifact(artifact_path: str) -> str | None:
    artifact_dir = os.path.dirname(artifact_path) if artifact_path else "."
    candidates = [
        os.path.join(artifact_dir, "_cache", "evidence"),
        os.path.join(artifact_dir, "..", "_cache", "evidence"),
    ]
    for base in candidates:
        if os.path.isdir(base):
            for f in os.listdir(base):
                if f.endswith(".evidence.json"):
                    return os.path.join(base, f)
    return None


def _check_content(path: str, text: str, display: str):
    if not text or len(text) < 100:
        return

    # --- CHECK 1: Bare anchors ---
    body = get_body_without_resources(text)
    body = re.sub(r'```[^\n]*\n.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)
    body = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', body)

    for line in body.split("\n"):
        bare = ANCHOR_CODE_RE.findall(line)
        if bare:
            block(f"Blocked by pre_write_gate: {display} has bare anchor codes "
                  f"without URLs: {', '.join(bare)}. "
                  f"Every [S#]/[I#] must have a URL. Fix before writing.")

    # --- CHECK 2: Double URLs ---
    doubles = re.findall(r'\[([^\]]+)\]\([^)]+\)\((https?://[^)]+)\)', body)
    if doubles:
        block(f"Blocked by pre_write_gate: {display} has double-concatenated URLs. "
              f"Fix before writing.")

    # --- CHECK 3: Non-standard inline labels ---
    all_anchors = re.findall(r'(!?)\[([^\]]+)\]\(([^)]+)\)', body)
    non_std = []
    for is_img, label, target in all_anchors:
        if STANDARD_CODE_RE.match(label):
            continue
        if is_img or target.startswith('#'):
            continue
        if target.endswith(('.jpg', '.png', '.webp', '.svg', '.gif')):
            continue
        if '_cache/' in target or target.startswith('./'):
            continue
        label_lower = label.lower()
        if label in NON_SOURCE_LABELS:
            continue
        if any(label.startswith(p) for p in ANNOTATION_PREFIXES):
            continue
        if label_lower in SOURCE_WORDS or any(
            sw in label_lower for sw in SOURCE_WORDS if len(sw) >= 4
        ):
            non_std.append(label)
    if non_std:
        block(f"Blocked by pre_write_gate: {display} has non-standard inline source labels: "
              f"{', '.join(f'[{n}]' for n in non_std[:3])}. "
              f"Use [S#](url) or [I#](url) format. Fix before writing.")

    # --- CHECK 4: Resources section format ---
    resources = get_resources_entries(text)
    res_raw = text[text.find('## Resources'):] if '## Resources' in text else ''
    if res_raw:
        res_labels = re.findall(r'(?im)^\s*-\s*\[([^\]]+)\]', res_raw)
        bad = [lbl.strip() for lbl in res_labels if not STANDARD_CODE_RE.match(lbl.strip())]
        if bad:
            block(f"Blocked by pre_write_gate: {display} has non-standard label(s) "
                  f"in Resources: {', '.join(f'[{l}]' for l in bad[:3])}. "
                  f"Use [S#] or [I#] format. Fix before writing.")

    # --- CHECK 5: Paragraph source density ---
    body_paras = [p for p in body.split('\n\n') if len(p) > 150]
    for para in body_paras[:10]:
        facts = len(FACTUAL_MARKERS_RE.findall(para))
        if facts < 3:
            continue
        sources = len(SOURCE_ANCHOR_RE.findall(para))
        if sources == 0:
            preview = para[:100].replace('\n', ' ')
            block(f"Blocked by pre_write_gate: {display} has a paragraph with "
                  f"{facts} factual markers but ZERO source anchors: '{preview}...'. "
                  f"Add [S#](url) or [I#](url) before writing.")

    # --- CHECK 6: Image file existence ---
    IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
    artifact_dir = os.path.dirname(path) if path else "."
    missing_images = []
    for img in IMG_RE.findall(text):
        if not img.startswith("_cache/images/") and not img.startswith("./_cache/"):
            continue
        img_path = os.path.join(artifact_dir, img)
        if not os.path.exists(img_path):
            missing_images.append(img)
    if missing_images:
        block(f"Blocked by pre_write_gate: {display} references "
              f"{len(missing_images)} image(s) not on disk: "
              f"{', '.join(missing_images[:3])}. "
              f"Go back to Step 5 and download them before writing.")

    # --- CHECK 7: [缺图] must have download attempt ---
    QUE_TU_RE = re.compile(r'\[缺图\]')
    if QUE_TU_RE.search(text):
        ledger_path = _find_ledger_for_artifact(path)
        has_attempt = False
        if ledger_path:
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
                for claim in ledger.get("claims", {}).values():
                    for a in claim.get("attempts", []):
                        if a.get("method") in ("Playwright", "curl"):
                            desc = a.get("description", "")
                            if "image" in desc.lower() or "img" in desc.lower() or "图" in desc:
                                has_attempt = True
                                break
                        if has_attempt:
                            break
            except Exception:
                pass
        if not has_attempt:
            block(f"Blocked by pre_write_gate: {display} uses [缺图] but "
                  f"no image download attempt found in evidence ledger. "
                  f"Go back to Step 5 and try Playwright/curl download first.")

    # --- CHECK 8: [需查证] count limit ---
    XU_CHA_ZHENG_RE = re.compile(r'\[需查证\]')
    xu_count = len(XU_CHA_ZHENG_RE.findall(body))
    MAX_XU = 8
    if xu_count > MAX_XU:
        block(f"Blocked by pre_write_gate: {display} has {xu_count} "
              f"[需查证] markers (max {MAX_XU} allowed). "
              f"Go back to Step 4 and verify more claims before writing.")

    # --- CHECK 9: Pipeline header accuracy ---
    PIPELINE_RE = re.compile(
        r'>\s*Pipeline:\s*'
        r'actuals\s*(?P<actuals>[✅❌])?\s*\|?\s*'
        r'(?:WebFetch\s*\d+/\d+\s*\|?\s*)?'
        r'(?:Playwright\s*\d+/\d+\s*\|?\s*)?'
        r'\[需查证\]\s*(?P<xu_reported>\d+)\s*\|?\s*'
        r'images\s*(?P<images>[✅❌])?\s*\|?\s*'
        r'lint\s*(?P<lint>[✅❌])?\s*\|?\s*'
        r'coverage\s*(?P<cov>\d+)%'
    )
    pm = PIPELINE_RE.search(text)
    if pm:
        reported_xu = int(pm.group("xu_reported"))
        if reported_xu != xu_count:
            block(f"Blocked by pre_write_gate: {display} Pipeline header "
                  f"reports [需查证] {reported_xu} but body has {xu_count}. "
                  f"Fix the Pipeline header.")

        img_reported_ok = pm.group("images") == "✅"
        IMG_BODY_RE = re.compile(r'!\[[^\]]*\]\(_cache/images/')
        img_count = len(IMG_BODY_RE.findall(text))
        if img_reported_ok and img_count == 0:
            block(f"Blocked by pre_write_gate: {display} Pipeline header "
                  f"says images ✅ but no image references found. "
                  f"Fix the header or go back to Step 5.")

        lint_ok = pm.group("lint") == "✅"
        if lint_ok and ANCHOR_CODE_RE.findall(body):
            block(f"Blocked by pre_write_gate: {display} Pipeline header "
                  f"says lint ✅ but bare anchors found. Fix before writing.")

    # --- CHECK 10: actuals freshness ---
    ACTUALS_REL = re.compile(
        r'(industry/[^/]+/companies/[^/]+)/\d{4}-\d{2}-\d{2}-.+\.md$')
    m = ACTUALS_REL.search(path) if path else None
    if m:
        actuals_path = os.path.join(
            os.path.dirname(path).split('industry')[0] if 'industry' in path else ".",
            m.group(1), "_cache", "financial-data", "internal", "actuals-resolved.json")
        if os.path.exists(actuals_path):
            try:
                with open(actuals_path, "r", encoding="utf-8") as f:
                    actuals = json.load(f)
                lq = actuals.get("latest_quarter_period") or actuals.get("latest_fy_period", "")
                if lq:
                    from datetime import datetime
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(lq))
                    if date_match:
                        actuals_date = datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3)))
                        age_days = (datetime.now() - actuals_date).days
                        MAX_AGE_DAYS = 180
                        if age_days > MAX_AGE_DAYS:
                            block(f"Blocked by pre_write_gate: {display} actuals "
                                  f"from {lq} are {age_days} days old (max {MAX_AGE_DAYS}). "
                                  f"Re-run financial-data --lite first.")
            except Exception:
                pass

    # --- CHECK 11: Evidence verification coverage ---
    I_ANCHOR_RE = re.compile(r'\[I\d+\]\([^)]+\)')
    i_anchors = len(set(I_ANCHOR_RE.findall(body)))
    if i_anchors > 0:
        ledger_path = _find_ledger_for_artifact(path)
        if ledger_path:
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
                claims = ledger.get("claims", {})
                verified = 0
                total = 0
                unverified_codes = []
                for code, c in claims.items():
                    total += 1
                    attempts = c.get("attempts", [])
                    methods = {a.get("method") for a in attempts}
                    if methods & {"WebFetch", "Playwright", "curl", "actuals"}:
                        verified += 1
                    else:
                        unverified_codes.append(code)
                if total > 0:
                    coverage = verified / total
                    MIN_COVERAGE = 0.80
                    if coverage < MIN_COVERAGE:
                        block(f"Blocked by pre_write_gate: {display} evidence "
                              f"coverage is {coverage:.0%} (min {MIN_COVERAGE:.0%}). "
                              f"{verified}/{total} verified. "
                              f"Unverified: {', '.join(unverified_codes[:5])}. "
                              f"Go back to Step 4 and verify them.")
            except Exception:
                pass


def main():
    payload = load_stdin_payload()
    if not payload:
        sys.exit(0)
    tool = get_tool_name(payload)
    if tool not in ("Write", "Edit", "MultiEdit", "apply_patch", "write_file"):
        sys.exit(0)
    path, content = _extract_write_content(payload)
    if not path or not content:
        sys.exit(0)
    _check_content(path, content, os.path.basename(path))
    sys.exit(0)


if __name__ == "__main__":
    main()
