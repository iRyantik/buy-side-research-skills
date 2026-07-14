"""Rule 6: Skill structure contract — fatal section presence check."""
import re, sys, os, yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import get_primary_heading, block

_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "required_sections.yaml")


def _load_config() -> dict:
    try:
        with open(_YAML_PATH, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}


def check(ctx: dict):
    config = _load_config()
    if not config:
        return

    for target in ctx.get("targets", []):
        if target.get("kind") != "file":
            continue
        path = target.get("path") or ""
        text = target.get("text", "")
        display = target.get("display", "unknown")

        leaf = Path(path).stem  # filename without extension
        h1 = (get_primary_heading(text) or "").lower()

        # Normalize: remove dashes/underscores for fuzzy matching
        leaf_norm = re.sub(r'[-_]', ' ', leaf.lower())
        h1_norm = re.sub(r'[-_]', ' ', h1)
        # Identify skill
        matched_skill = None
        for skill in config:
            skill_norm = re.sub(r'[-_]', ' ', skill.lower())
            if skill_norm in leaf_norm or skill_norm in h1_norm:
                matched_skill = skill
                break

        if not matched_skill:
            continue

        skill_config = config[matched_skill]
        required_patterns = skill_config.get("block", [])

        for pattern in required_patterns:
            if not re.search(pattern, text, re.IGNORECASE):
                block(
                    f"Blocked by skill_structure_contract: {display} "
                    f"is missing required section matching '{pattern}' "
                    f"(required by {matched_skill})."
                )
