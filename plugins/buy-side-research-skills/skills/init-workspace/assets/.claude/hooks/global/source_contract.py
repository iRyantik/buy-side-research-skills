"""source_contract hook — Python edition.
Verifies every research artifact has a valid ## Resources section with inline anchors.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Load shared library from parent directory
_hook_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_hook_dir))
import _hook_common as H  # noqa: E402


def test_factual_line(line: str) -> bool:
    if not line or not line.strip():
        return False
    if re.match(r'^\s*#', line):
        return False
    if re.match(r'^\s*[-*]\s+', line):
        return False
    if re.match(r'^\s*>', line):
        return False
    if re.match(r'^\s*\|(?:\s*-+\s*\|)+\s*$', line):
        return False
    if not re.search(r'\d', line):
        return False
    # Exclude structural lines
    if re.match(r'^\s*(\d+[.)]\s+|第\d+[步节章]|step\s*\d+|section\s*\d+)', line):
        return False
    if re.search(r'\b(?:19|20)\d{2}年\b', line):
        return False
    if re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', line):
        return False
    if re.search(r'\bv?\d+\.\d+(?:\.\d+)?\b', line) and not re.search(r'[%$]', line):
        return False
    if re.search(r'第\s*\d+\s*页|page\s*\d+', line):
        return False
    return True


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", dest="input_path", default=None)
    args = parser.parse_args()

    payload = H.get_hook_payload(args.input_path)
    if payload is None:
        sys.exit(0)

    if H.test_is_casual_chat(payload):
        sys.exit(0)

    for target in H.get_markdown_targets(payload):
        text = str(target.get("text", ""))
        display = target.get("display", "unknown")

        if target.get("kind") == "inline" and not H.test_is_artifact_like_text(text):
            continue

        # Count ## Resources sections
        resources_matches = list(re.finditer(r'(?m)^## Resources\b', text))
        if len(resources_matches) == 0:
            H.write_block(
                f"Blocked by source_contract: {display} must contain a '## Resources' section."
            )
        if len(resources_matches) > 1:
            H.write_warn(
                f"source_contract: {display} has multiple '## Resources' sections; only the first was checked for consistency."
            )

        contract = H.get_source_contract_state(text)
        body = str(contract["Body"])
        resource_entries = list(contract["ResourceEntries"])
        resource_map = contract["ResourceMap"]
        body_anchors = list(contract["BodyAnchors"])

        # Validate resource entry targets
        for entry in resource_entries:
            if not H.test_is_valid_source_target(entry["Target"]):
                H.write_block(
                    f"Blocked by source_contract: {display} has an invalid ## Resources target "
                    f"for [{entry['Code']}] ({entry['Target']})."
                )

        # Check for duplicate codes with inconsistent targets
        for code, entries in resource_map.items():
            if len(entries) > 1:
                distinct_targets = list({e["Target"] for e in entries})
                if len(distinct_targets) != 1:
                    H.write_block(
                        f"Blocked by source_contract: {display} defines [{code}] more than once "
                        f"with inconsistent ## Resources targets."
                    )

        # Check inline anchors
        for anchor in body_anchors:
            if anchor["Target"].lower() in ("link", "url"):
                H.write_block(
                    f"Blocked by source_contract: {display} still contains placeholder citations "
                    f"such as '(link)' or '(url)'."
                )
            if not H.test_is_valid_source_target(anchor["Target"]):
                H.write_block(
                    f"Blocked by source_contract: {display} uses an invalid inline source target "
                    f"for [{anchor['Code']}] ({anchor['Target']})."
                )
            if anchor["Code"] not in resource_map:
                H.write_block(
                    f"Blocked by source_contract: {display} uses [{anchor['Code']}] inline "
                    f"without a matching ## Resources entry."
                )
            else:
                resource_entry = resource_map[anchor["Code"]][0]
                if anchor["Target"] != resource_entry["Target"]:
                    H.write_block(
                        f"Blocked by source_contract: {display} must keep inline [{anchor['Code']}] "
                        f"target identical to its ## Resources target."
                    )

        # Check factual lines without anchors
        numeric_lines_no_anchors = []
        anchor_pat = re.compile(r'\[(?:S|P|I|LBG|R|SRC)\d+[^\]]*\]\([^)]+\)')
        for line in body.splitlines():
            if not test_factual_line(line):
                continue
            if anchor_pat.search(line):
                continue
            numeric_lines_no_anchors.append(line.strip())

        if len(body_anchors) == 0 and len(numeric_lines_no_anchors) >= 2:
            H.write_block(
                f"Blocked by source_contract: {display} contains factual-looking lines "
                f"without inline anchors."
            )

        # Check table rows for evidence anchors
        table_rows_no_evidence = []
        for line in body.splitlines():
            if not re.match(r'^\s*\|', line):
                continue
            if test_is_table_sep(line):
                continue
            if not re.search(r'\d|%|bps|x\b', line):
                continue
            if anchor_pat.search(line):
                continue
            table_rows_no_evidence.append(line.strip())

        if len(table_rows_no_evidence) >= 2:
            H.write_block(
                f"Blocked by source_contract: {display} has table rows with factual data "
                f"but no evidence anchors."
            )

    sys.exit(0)


def test_is_table_sep(line: str) -> bool:
    return bool(re.match(r'^\s*\|(?:\s*-+\s*\|)+\s*$', line))


if __name__ == "__main__":
    main()
