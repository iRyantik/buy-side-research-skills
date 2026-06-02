"""Pre-Write Gate: run source_contract + claim_proximity + ledger_floor
before Write/Edit tool executes. Block before the file is written, not after.

Reuses the same check logic as PostToolUse hooks but reads content from
tool_input (content / new_string) rather than from disk.
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
    r'(?:EUR|USD|CNY)\s*[\d,.]+[bmk]?|'
    r'\b(?:TSMC|Intel|Samsung|NVIDIA|ASML|BESI|ASMPT|AMAT|Hanwha)\b)'
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
    """Extract file_path and text content from Write/Edit/Bash tool_input."""
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
        # Bash: try to parse output redirection
        cmd = ti.get("command", "")
        return path, None  # Can't intercept bash content
    return None, None


def _check_content(path: str, text: str, display: str):
    """Run all source checks on pre-write content."""
    if not text or len(text) < 100:
        return

    # --- CHECK 1: Bare anchors ---
    body = get_body_without_resources(text)
    body = re.sub(r'```[^\n]*\n.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)
    body = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', body)  # strip images

    for line in body.split("\n"):
        bare = ANCHOR_CODE_RE.findall(line)
        if bare:
            block(f"Blocked by pre_write_gate: {display} has bare anchor codes "
                  f"without URLs: {', '.join(bare)}. "
                  f"Every [S#]/[I#] must have a URL: [S#](url). Fix before writing.")

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
            non_std.append(f'[{label}]({target[:40]}...)')
    if non_std:
        block(f"Blocked by pre_write_gate: {display} has non-standard inline source labels: "
              f"{', '.join(non_std[:3])}. Use [S#](url) or [I#](url) format. Fix before writing.")

    # --- CHECK 4: Resources section format ---
    resources = get_resources_entries(text)
    res_raw = text[text.find('## Resources'):] if '## Resources' in text else ''
    if res_raw:
        res_labels = re.findall(r'(?im)^\s*-\s*\[([^\]]+)\]', res_raw)
        for lbl in res_labels:
            if not STANDARD_CODE_RE.match(lbl.strip()):
                block(f"Blocked by pre_write_gate: {display} has non-standard label "
                      f"'[{lbl}]' in Resources. Use [S#] or [I#]. Fix before writing.")

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


def main():
    payload = load_stdin_payload()
    if not payload:
        sys.exit(0)

    tool = get_tool_name(payload)
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    path, content = _extract_write_content(payload)
    if not path or not content:
        sys.exit(0)

    _check_content(path, content, os.path.basename(path))
    sys.exit(0)


if __name__ == "__main__":
    main()
