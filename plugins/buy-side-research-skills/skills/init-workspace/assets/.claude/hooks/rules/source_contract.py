"""Rule 2: Source contract — anchor integrity, Resources section, orphan evidence."""
import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    get_body_without_resources, get_resources_entries, get_short_anchor_matches,
    is_valid_source_target, block, warn,
)

_RESEARCH_ARTIFACT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')


def _is_research_artifact(filepath: str) -> bool:
    """Only dated Markdown files (YYYY-MM-DD-*.md) are research artifacts
    requiring source contract enforcement. Skill files, config files, and
    structural navigation files are exempt."""
    return bool(_RESEARCH_ARTIFACT_RE.match(os.path.basename(filepath)))


def check(ctx: dict):
    """Check file + inline targets for source contract violations."""
    for target in ctx.get("targets", []):
        text = target.get("text", "")
        if not text:
            continue
        display = target.get("display", "unknown")
        is_file = target.get("kind") == "file"
        is_artifact = is_file and _is_research_artifact(display)

        # --- Rule 1: ## Resources must exist (research artifacts only) ---
        resources_count = len(re.findall(r'(?m)^## Resources\b', text))
        if is_artifact and resources_count == 0:
            block(f"Blocked by source_contract: {display} must contain a '## Resources' section.")
        if resources_count > 1:
            warn(f"source_contract: {display} has multiple '## Resources' sections; only the first was checked.")

        # --- Parse resources and anchors ---
        resources = get_resources_entries(text)
        resource_map = {}
        for entry in resources:
            resource_map.setdefault(entry["code"], []).append(entry)

        body = get_body_without_resources(text)
        body_anchors = get_short_anchor_matches(body)

        # --- Rule 2: Resources entry target validity ---
        for entry in resources:
            if not is_valid_source_target(entry["target"]):
                block(f"Blocked by source_contract: {display} has invalid ## Resources target for [{entry['code']}] ({entry['target']}).")

        # --- Rule 2a: bare anchor codes without URL ---
    for line in body.split("\n"):
        bare = re.findall(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()', line)
        if bare:
            block(f"Blocked by source_contract: {display} has bare anchor codes without URLs: {', '.join(bare)}")

    # --- Rule 2b (inline): anchor targets must be valid, no placeholders ---
        for anchor in body_anchors:
            if anchor["target"].lower() in ("link", "url"):
                block(f"Blocked by source_contract: {display} still contains placeholder citations like '(link)' or '(url)'.")
            if not is_valid_source_target(anchor["target"]):
                block(f"Blocked by source_contract: {display} uses invalid inline source target for [{anchor['code']}] ({anchor['target']}).")

        # --- Rules 3-5: research artifacts only ---
        if not is_artifact:
            continue

        # --- Rule 3: Same code must not map to different targets in Resources ---
        for code, entries in resource_map.items():
            distinct = {e["target"] for e in entries}
            if len(distinct) > 1:
                block(f"Blocked by source_contract: {display} defines [{code}] with inconsistent ## Resources targets.")

        # --- Rule 4: Inline anchor ↔ Resources consistency ---
        for anchor in body_anchors:
            if anchor["code"] not in resource_map:
                block(f"Blocked by source_contract: {display} uses [{anchor['code']}] inline without a matching ## Resources entry.")
            resource_target = resource_map[anchor["code"]][0]["target"]
            if anchor["target"] != resource_target:
                block(f"Blocked by source_contract: {display} must keep inline [{anchor['code']}] target identical to its ## Resources target.")

    # All checks passed
