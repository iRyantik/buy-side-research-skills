"""Rule 4: Subagent protocol — subagent evidence requirements."""
import re, sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import get_primary_heading, block

_RESEARCH_ARTIFACT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')

def _is_research_artifact(filepath: str) -> bool:
    return bool(_RESEARCH_ARTIFACT_RE.match(os.path.basename(filepath)))

# 4 default-parallel skills — must have evidence cards
DEFAULT_PARALLEL = {
    "peer-deep-dive", "candidate-screener", "pair-trade", "comps-analysis",
}

# 8 company-level finance skills — must have financial-data subagent evidence
COMPANY_FINANCE_SKILLS = {
    "stock-quickread", "company-history", "driver-map",
    "alpha-thesis", "consensus-map", "earnings-setup",
    "bear-pre-mortem", "comps-analysis",
}

# Evidence that financial-data was sourced by subagent
FINANCE_DATA_EVIDENCE = re.compile(
    r'(?i)(?:source_layer[:\s]*(?:yfinance|local_web|provider_api)|'
    r'source[:\s]*yfinance|'
    r'/financial-data\s*--lite|'
    r'actuals-resolved\.json)'
)

EVIDENCE_CARD_RE = re.compile(r'(?:claim|evidence|source)\s*:', re.IGNORECASE)
DOWNGRADE_RE = re.compile(
    r'(?:subagent\s+unavailable|single[.\-]thread|单线程|降级)',
    re.IGNORECASE
)


def _match_skill(leaf_norm: str, h1_norm: str, skill_set: set) -> bool:
    for skill in skill_set:
        skill_norm = re.sub(r'[-_]', ' ', skill.lower())
        if skill_norm in leaf_norm or skill_norm in h1_norm:
            return True
    return False


def check(ctx: dict):
    for target in ctx.get("targets", []):
        if target.get("kind") != "file":
            continue
        path = target.get("path") or ""
        text = target.get("text", "")
        display = target.get("display", "unknown")

        # Only check research artifacts, not skill definition files
        if not _is_research_artifact(display):
            continue

        leaf_norm = re.sub(r'[-_]', ' ', Path(path).stem.lower())
        h1_norm = re.sub(r'[-_]', ' ', (get_primary_heading(text) or "").lower())

        # --- Check 1: default-parallel skills need evidence cards ---
        if _match_skill(leaf_norm, h1_norm, DEFAULT_PARALLEL):
            evidence_cards = len(re.findall(r'(?im)^\s*(?:claim|evidence|source)\s*:', text))
            evidence_triples = evidence_cards // 3
            has_downgrade = bool(DOWNGRADE_RE.search(text))

            if evidence_triples < 1 and not has_downgrade:
                block(
                    f"Blocked by subagent_protocol: {display} is a default-parallel skill artifact "
                    f"but has no evidence cards and no subagent-unavailable declaration. "
                    f"Add at least one evidence card or declare downgrade reason."
                )
            continue

        # --- Check 2: company-level finance skills need financial-data evidence ---
        if _match_skill(leaf_norm, h1_norm, COMPANY_FINANCE_SKILLS):
            has_finance_data = bool(FINANCE_DATA_EVIDENCE.search(text))
            has_downgrade = bool(DOWNGRADE_RE.search(text))

            if not has_finance_data and not has_downgrade:
                block(
                    f"Blocked by subagent_protocol: {display} is a company-level skill artifact "
                    f"but has no financial-data subagent evidence "
                    f"(no source_layer, no /financial-data --lite trace, no actuals-resolved.json reference). "
                    f"Delegate financial-data fetching to a subagent, or declare downgrade reason."
                )
