"""Rule 2: Source contract — anchor integrity, Resources section, orphan evidence.

== Agent Action Routing Table ==
| gate | action | agent fix |
|---|---|---|
| missing_resources | add_resources_section | Add `## Resources` section with all [S#]/[I#] listed |
| bare_anchors | fix_source_format | Add URLs to every bare [S#]/[I#]: `[S#](url)` |
| nonstandard_labels | fix_source_format | Replace descriptive labels with [S#] or [I#] codes |
| double_urls | fix_source_format | Remove concatenated second URL |
| nonstandard_inline | fix_source_format | Replace `[Label](url)` with `[S#](url)` or `[I#](url)` |
| nonstandard_resources | fix_source_format | Replace `[Label]` in Resources with `[S#]` or `[I#]` |
"""

import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    get_body_without_resources, get_resources_entries, get_short_anchor_matches,
    is_valid_source_target, block, warn,
)

_RESEARCH_ARTIFACT_RE = re.compile(r'^\d{8}-.+\.md$')

# Known source words — case-insensitive match for non-standard label detection
SOURCE_WORDS = {
    # Financial data providers
    'yfinance', 'yahoo', 'yahoo finance', 'google', 'google finance', 'bloomberg',
    'marketscreener', 'chartmill', 'stockanalysis', 'gurufocus', 'simplywall',
    'tipranks', 'investing', 'investing.com', 'coincentral', 'moneycheck',
    'blockonomi', 'valueinvesting', 'longbridge', 'bridge',
    # Banks / research
    'morgan stanley', 'morganstanley', 'bernstein', 'socgen', 'societe generale',
    'goldman', 'goldman sachs', 'jpmorgan', 'jpm', 'ubs', 'credit suisse',
    # Media / industry
    'bits&chips', 'bitsandchips', 'bits-chips', 'reuters', 'bloomberg',
    'nikkei', 'nikkei asia', 'digitimes', 'semiconductor today',
}

# Labels that are NOT sources — research annotations in Chinese/English
NON_SOURCE_LABELS = {
    '推算', '未披露', '缺图', '估算', '需查证', '来源待补', '来源待确认', 'UNVERIFIED',
    'actuals', 'actuals-source',
    'ND', 'NA', 'N/A', 'TBD', 'TODO',
    '待确认', '待补', '待查', '注', '注意', '重要',
    # Financial notation — not sources
    'E', '共识', 'A', 'LTM', 'NTM', 'FY', 'Q', 'H1', 'H2',
}

# Labels that are markdown/structural — never sources
STRUCTURAL_LABELS_RE = re.compile(
    r'^(\*\*?|__?|!|`|#|>|\||\+|-|—|…|\.{2,})$|'  # formatting chars
    r'^(S|I|P|LBG|R|SRC)\d+$|'  # already-standard anchor codes (caught by Rule 2a)
    r'^\d+$|'  # pure numbers
    r'^[xX✓✔✗✘]$'  # checkmarks
)

def _looks_like_source_label(label: str) -> bool:
    """Heuristic: does this bare [label] look like a source reference?"""
    label_clean = label.strip()
    if not label_clean:
        return False
    # Exclude structural / markdown
    if STRUCTURAL_LABELS_RE.match(label_clean):
        return False
    # Exclude known research annotations (exact match)
    if label_clean in NON_SOURCE_LABELS:
        return False
    # Exclude labels starting with research annotation prefixes
    # e.g. [ND——无 Q1 2025 可比 EBIT], [推算——基于订单 mix]
    for prefix in ('ND', '推算', '未披露', '缺图', '估算', '需查证', '来源待补', '来源待确认'):
        if label_clean.startswith(prefix):
            return False
    label_lower = label_clean.lower()
    # Direct match against known source words
    if label_lower in SOURCE_WORDS:
        return True
    # Substring match (e.g. "AGM 2026" inside "BESI AGM 2026")
    for sw in SOURCE_WORDS:
        if len(sw) >= 4 and sw in label_lower:
            return True
        # Also check if label contains a source word (for multi-word labels)
        if len(sw) >= 4 and label_lower in sw:
            return True
    # Heuristic: label contains a known source word fragment
    fragments = {'finance', 'investing', 'market', 'stock', 'analyst', 'earnings',
                 'report', 'annual', 'quarterly', 'presentation', 'agm', 'ir'}
    words_in_label = set(re.findall(r'[a-zA-Z]{3,}', label_lower))
    if words_in_label & fragments:
        return True
    # Heuristic: label starts with capital + doesn't look like normal prose
    if label_clean[0].isupper() and len(label_clean) >= 4:
        # Exclude if it's just common English words
        common_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have',
                        'been', 'were', 'they', 'will', 'would', 'could', 'should',
                        'about', 'after', 'before', 'during', 'since', 'while'}
        if all(w.lower() in common_words for w in label_clean.split()):
            return False
        # Has at least one proper-noun-like word (capitalized, not common)
        proper_words = [w for w in label_clean.split()
                        if w[0].isupper() and w.lower() not in common_words]
        if proper_words:
            return True
    return False


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (```...``` and ~~~...~~~) including Mermaid blocks.
    This prevents false positives from flowchart node labels like [TSMC/Intel]."""
    # Triple backtick blocks
    result = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
    # Tilde-fenced blocks
    result = re.sub(r'~~~[^\n]*\n.*?~~~', '', result, flags=re.DOTALL)
    return result


def _is_research_artifact(filepath: str) -> bool:
    """Only dated Markdown files (YYYYMMDD-*.md) are research artifacts
    requiring source contract enforcement. Skill files, config files, and
    structural navigation files are exempt."""
    return bool(_RESEARCH_ARTIFACT_RE.match(os.path.basename(filepath)))


def _check_double_urls(body: str, display: str):
    """Rule 2c: detect double-concatenated URLs like [I2](url1)(url2)."""
    double_urls = re.findall(r'\[([^\]]+)\]\([^)]+\)\((https?://[^)]+)\)', body)
    if double_urls:
        examples = [f"[{code}] has a second URL concatenated: {url2[:60]}..."
                    for code, url2 in double_urls[:3]]
        block(f"Blocked by source_contract: {display} has double-concatenated URLs. "
              f"Each source must have exactly one URL: {', '.join(examples)}")


def check(ctx: dict):
    """Check file targets for source contract violations.
    Only enforces on actual files (kind='file'), not inline/assistant messages —
    meta-discussion about source labels should not trigger the hook."""
    workspace_root = ctx.get("cwd", "")
    for target in ctx.get("targets", []):
        # Only enforce on actual files written to disk
        if target.get("kind") != "file":
            continue
        text = target.get("text", "")
        if not text:
            continue
        filepath = target.get("path", "")
        display = target.get("display", "unknown")
        # Skip files outside the current workspace (e.g., plugin repo, temp dirs)
        if workspace_root and filepath:
            if not os.path.abspath(filepath).startswith(os.path.abspath(workspace_root)):
                continue
        is_file = target.get("kind") == "file"
        is_artifact = is_file and _is_research_artifact(display)

        # --- Rule 1: ## Resources must exist (research artifacts only) ---
        resources_count = len(re.findall(r'(?m)^## Resources\b', text))
        if is_artifact and resources_count == 0:
            block(f"Blocked by source_contract: {display} must contain "
                  f"a '## Resources' section listing all sources.")
        if resources_count > 1:
            warn(f"source_contract: {display} has multiple '## Resources' sections; only the first was checked.")

        # --- Parse resources and anchors ---
        resources = get_resources_entries(text)
        resource_map = {}
        for entry in resources:
            resource_map.setdefault(entry["code"], []).append(entry)

        body = get_body_without_resources(text)
        body_no_code = _strip_code_blocks(body)  # for label-matching rules only
        body_anchors = get_short_anchor_matches(body)

        # Rules 2-2e only apply to research artifacts (YYYYMMDD-*.md)
        # Memory files, config, CLAUDE.md etc. are exempt from source contract
        if not is_artifact:
            continue

        # --- Rule 2: Resources entry target validity ---
        for entry in resources:
            if not is_valid_source_target(entry["target"]):
                block(f"Blocked by source_contract: {display} has invalid ## Resources target for [{entry['code']}] ({entry['target']}).")

        # --- Rule 2a: bare standard anchor codes without URL (e.g. [S1], [I2]) ---
        # Every [S#]/[I#] must have an inline URL: [S#](url). Bare anchors block.
        for line in body_no_code.split("\n"):
            bare = re.findall(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()', line)
            if bare:
                block(f"Blocked by source_contract: {display} has bare anchor codes without inline URLs: "
                      f"{', '.join(bare)}. Every [S#]/[I#] must be clickable: [S#](url).")

        # --- Rule 2a2: non-standard source labels without URLs ---
        # Catches lowercase (yfinance), CamelCase (MarketScreener), multi-word (Yahoo Finance),
        # and special-char labels (Bits&Chips, BESI AGM 2026)
        for line in body_no_code.split("\n"):
            # Find all [...text...] that are NOT followed by ( — i.e. bare labels
            bare_labels = re.findall(r'\[([^\]]+)\](?!\()', line)
            flagged = [lbl for lbl in bare_labels if _looks_like_source_label(lbl)]
            if flagged:
                block(f"Blocked by source_contract: {display} has non-standard source labels without URLs: "
                      f"{', '.join(f'[{n}]' for n in flagged)}. "
                      f"Use [S#](url) for disclosure sources or [I#](url) for internet sources.")

        # --- Rule 2b: inline anchor targets must be valid, no placeholders ---
        for anchor in body_anchors:
            if anchor["target"].lower() in ("link", "url"):
                block(f"Blocked by source_contract: {display} still contains placeholder citations like '(link)' or '(url)'.")
            if not is_valid_source_target(anchor["target"]):
                block(f"Blocked by source_contract: {display} uses invalid inline source target for [{anchor['code']}] ({anchor['target']}).")

        # --- Rule 2c: double-concatenated URLs ---
        _check_double_urls(body_no_code, display)

        # --- Rule 2d: non-standard inline anchor labels (have URL but wrong label format) ---
        # Catches [Yahoo Finance](url), [yfinance](url), [BESI AGM 2026](url) —
        # these must use [S#](url) or [I#](url) instead.
        STANDARD_CODE_RE = re.compile(r'^(?:S|P|I|LBG|R|SRC)\d+$|^actuals$|^actuals-source$')
        all_inline_anchors = re.findall(r'(!?)\[([^\]]+)\]\(([^)]+)\)', body_no_code)
        non_std_anchors = []
        for is_image, label, target in all_inline_anchors:
            if STANDARD_CODE_RE.match(label):
                continue
            # Skip markdown images (![...](...)), internal links, etc.
            if is_image or target.startswith('#'):
                continue
            if _looks_like_source_label(label):
                non_std_anchors.append(f'[{label}]({target[:50]}...)')
        if non_std_anchors:
            block(f"Blocked by source_contract: {display} has non-standard inline source labels: "
                  f"{', '.join(non_std_anchors[:3])}. "
                  f"All source references must use [S#](url) or [I#](url) format.")

        # --- Rule 2e: non-standard labels in Resources section itself ---
        # Catch [Bits&Chips], [BESI AGM 2026], etc. used as entry labels in Resources
        resources_raw = (re.search(r'(?ims)^##\s*Resources\b(.*)$', text) or
                         type('', (), {'group': lambda s, n: ''})())
        resources_text = resources_raw.group(1) if hasattr(resources_raw, 'group') else ''
        if resources_text:
            # Find all list-item labels in Resources: `- [LABEL] ...`
            res_labels = re.findall(r'(?im)^\s*-\s*\[([^\]]+)\]', resources_text)
            for lbl in res_labels:
                lbl_clean = lbl.strip()
                if STANDARD_CODE_RE.match(lbl_clean):
                    continue
                if lbl_clean in NON_SOURCE_LABELS:
                    continue
                if _looks_like_source_label(lbl_clean):
                    block(f"Blocked by source_contract: {display} has non-standard source label "
                          f"'[{lbl_clean}]' in ## Resources section. "
                          f"Use [S#] or [I#] format for all Resources entries.")

        # --- Rule 3: No duplicate codes in Resources, no inconsistent targets ---
        # Count raw occurrences of each standard code in Resources text (before parser dedup)
        resources_text_for_count = (
            re.search(r'(?ims)^##\s*Resources\b(.*)$', text) or
            type('', (), {'group': lambda s, n: ''})()
        )
        res_raw = resources_text_for_count.group(1) if hasattr(resources_text_for_count, 'group') else ''
        if res_raw:
            raw_codes = re.findall(r'(?im)^\s*-\s*\[([SPILBGR]+\d+)\]', res_raw)
            from collections import Counter
            raw_counts = Counter(raw_codes)
            for code, count in raw_counts.items():
                if count > 1:
                    block(f"Blocked by source_contract: {display} defines [{code}] {count} times "
                          f"in ## Resources. Each source must have a unique code — use different "
                          f"codes for different sources (e.g. [I4] and [I5]).")
        for code, entries in resource_map.items():
            distinct = {e["target"] for e in entries}
            if len(distinct) > 1:
                block(f"Blocked by source_contract: {display} defines [{code}] with inconsistent "
                      f"## Resources targets: {distinct}.")

        # --- Rule 4: Inline anchor ↔ Resources consistency ---
        for anchor in body_anchors:
            if anchor["code"] not in resource_map:
                block(f"Blocked by source_contract: {display} uses [{anchor['code']}] inline without a matching ## Resources entry.")
            resource_target = resource_map[anchor["code"]][0]["target"]
            if anchor["target"] != resource_target:
                block(f"Blocked by source_contract: {display} must keep inline [{anchor['code']}] target identical to its ## Resources target.")

    # All checks passed
