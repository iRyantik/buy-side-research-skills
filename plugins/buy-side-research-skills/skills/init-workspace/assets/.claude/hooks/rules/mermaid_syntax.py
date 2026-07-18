"""Rule: Mermaid syntax validation — block invalid diagram types before write.

Checks every ```mermaid code block in the target artifact. Blocks on:
- Invalid diagram type (not in the Mermaid supported type set)
- Missing diagram type (empty first line after fence)
"""
import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

# Mermaid supported diagram types as of Mermaid v11.x
# Source: https://mermaid.js.org/intro/
VALID_MERMAID_TYPES = {
    # Core flow/graph
    "graph",          # legacy, but still widely supported
    "flowchart",      # modern replacement for graph
    # Sequence & class
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",   # also: stateDiagram-v2
    "stateDiagram-v2",
    # Entity relationship
    "erDiagram",
    # Project/planning
    "gantt",
    "pie",
    # Quadrant / chart
    "quadrantChart",
    "xy-chart",       # Mermaid v11+
    "block",          # block diagram (beta)
    "block-beta",
    # Mindmap / timeline
    "mindmap",
    "timeline",
    # Flow
    "sankey",
    "gitGraph",       # also: gitgraph, gitGraph, git-graph
    "gitgraph",
    # Architecture
    "c4",             # C4 context/container/component/dynamic/deployment
    "c4context",
    "c4container",
    "c4component",
    "c4dynamic",
    "c4deployment",
    # Requirements
    "requirementDiagram",
    # User journey
    "journey",
    # ZenUML
    "zenuml",
}

# Type aliases / common misspellings → correct type (warn, don't block)
TYPE_ALIASES = {
    "scatter": "quadrantChart",
    "scatterchart": "quadrantChart",
    "scatter chart": "quadrantChart",
    "waterfall": "flowchart TD",
    "radar": None,           # No Mermaid equivalent — use research-viz
    "bar": "xy-chart",
    "bar chart": "xy-chart",
    "line": "xy-chart",
    "line chart": "xy-chart",
}


def _extract_mermaid_blocks(text: str) -> list[dict]:
    """Extract all ```mermaid code blocks with their line numbers."""
    blocks = []
    lines = text.split("\n")
    in_mermaid = False
    fence_line = 0
    block_lines = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("```mermaid") or stripped == "```mermaid":
            in_mermaid = True
            fence_line = i
            block_lines = []
            continue

        if in_mermaid and stripped == "```":
            in_mermaid = False
            blocks.append({
                "start_line": fence_line,
                "end_line": i,
                "lines": block_lines,
            })
            continue

        if in_mermaid:
            block_lines.append(line)

    return blocks


def _get_diagram_type(first_line: str) -> str | None:
    """Extract diagram type from the first content line of a mermaid block.

    Handles:
    - Simple: 'flowchart TD' → 'flowchart'
    - Directional: 'graph LR' → 'graph'
    - C4 detail: 'c4context' → 'c4context'
    - Class directives: 'classDiagram\nclass User {' → 'classDiagram'
    """
    stripped = first_line.strip()
    if not stripped:
        return None

    # Split on whitespace, take first token as type
    token = stripped.split()[0]

    # Normalize: remove any trailing non-alphanumeric
    token = re.sub(r'[^a-zA-Z0-9_-]+$', '', token)

    return token if token else None


def check(ctx: dict):
    for target in ctx.get("targets", []):
        if target.get("kind") != "file":
            continue
        display = target.get("display", "unknown")
        if not re.match(r'^\d{8}-.+\.md$', os.path.basename(display)):
            continue

        text = target.get("text", "")
        if not text:
            continue

        mermaid_blocks = _extract_mermaid_blocks(text)
        if not mermaid_blocks:
            continue

        for mb in mermaid_blocks:
            start = mb["start_line"]
            lines = mb["lines"]

            if not lines or not lines[0].strip():
                block(
                    f"Blocked by mermaid_syntax: {display} has a mermaid block "
                    f"near line {start} with no diagram type on the first line. "
                    f"Add a valid diagram type (e.g., 'flowchart TD', 'quadrantChart')."
                )

            diag_type = _get_diagram_type(lines[0])

            if diag_type is None:
                block(
                    f"Blocked by mermaid_syntax: {display} mermaid block near "
                    f"line {start} — cannot parse diagram type from first line: "
                    f"'{lines[0].strip()[:60]}'. Valid types: {', '.join(sorted(VALID_MERMAID_TYPES)[:10])}..."
                )

            diag_lower = diag_type.lower()

            # Check for known aliases → correct type
            alias_key = diag_lower
            if alias_key in TYPE_ALIASES:
                suggestion = TYPE_ALIASES[alias_key]
                if suggestion:
                    block(
                        f"Blocked by mermaid_syntax: {display} mermaid block near "
                        f"line {start} uses '{diag_type}' which is NOT a valid Mermaid diagram type. "
                        f"Use '{suggestion}' instead. "
                        f"'{diag_type}' is not supported by any Mermaid renderer."
                    )
                else:
                    block(
                        f"Blocked by mermaid_syntax: {display} mermaid block near "
                        f"line {start} uses '{diag_type}' which has NO Mermaid equivalent. "
                        f"Use research-viz for this chart type, or switch to a supported diagram type: "
                        f"{', '.join(sorted(v for v in VALID_MERMAID_TYPES if not v.startswith('c4'))[:8])}..."
                    )

            # Check against valid types (case-insensitive for common variants)
            if diag_type not in VALID_MERMAID_TYPES and diag_lower not in VALID_MERMAID_TYPES:
                # Some types have case variations — normalize and check again
                normalized = diag_type.lower()
                valid_lower = {t.lower(): t for t in VALID_MERMAID_TYPES}
                if normalized in valid_lower:
                    warn(
                        f"Mermaid syntax warning: {display} near line {start} uses "
                        f"'{diag_type}' — correct casing is '{valid_lower[normalized]}'. "
                        f"Auto-accepting with corrected casing."
                    )
                else:
                    block(
                        f"Blocked by mermaid_syntax: {display} mermaid block near "
                        f"line {start} uses '{diag_type}' which is NOT a recognized "
                        f"Mermaid diagram type. Valid types include: "
                        f"flowchart, sequenceDiagram, classDiagram, stateDiagram, "
                        f"erDiagram, gantt, pie, quadrantChart, xy-chart, mindmap, "
                        f"timeline, sankey, gitGraph, c4, requirementDiagram, journey."
                    )
