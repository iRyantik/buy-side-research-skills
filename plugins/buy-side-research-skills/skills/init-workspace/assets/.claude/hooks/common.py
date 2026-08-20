"""Shared library for all hooks — payload parsing, markdown tools, block/warn."""
import sys, os, json, re
from pathlib import Path
from typing import Any, Optional

ANCHOR_CODE_RE = re.compile(r'\[(?P<code>[SPILBGR]+\d+)(?:[^\]]*)\]\((?P<target>[^)]+)\)')

def load_stdin_payload() -> Optional[dict]:
    """Read and parse JSON payload from stdin."""
    try:
        raw = sys.stdin.read()
        if raw.strip():
            return json.loads(raw)
    except Exception:
        pass
    return None

def get_tool_name(payload: dict) -> str:
    return (payload.get("tool_name") or payload.get("toolName") or "")

def get_tool_input(payload: dict) -> dict:
    return (payload.get("tool_input") or payload.get("toolInput") or {})

def get_hook_event(payload: dict) -> str:
    return (payload.get("hook_event_name") or payload.get("event") or "")

def get_workspace_root(payload: dict) -> str:
    cwd = payload.get("cwd", "")
    if cwd:
        return str(Path(cwd).resolve())
    return str(Path.cwd().resolve())

def resolve_path(path: str, cwd: str) -> Optional[str]:
    """Resolve relative or absolute path to absolute."""
    if not path:
        return None
    clean = path.strip().strip('"').strip("'")
    if not clean:
        return None
    try:
        # Git Bash: /s/... → S:\... on Windows
        if sys.platform == "win32" and re.match(r'^/[a-zA-Z]/', clean):
            drive = clean[1] + ":"
            win_path = drive + clean[2:]
            return str(Path(win_path).resolve()) if os.path.exists(win_path) else str((Path(cwd) / clean.lstrip("/")).resolve())
        if os.path.isabs(clean):
            return str(Path(clean).resolve())
        return str((Path(cwd) / clean).resolve())
    except Exception:
        return None

def is_under(path: str, root: str) -> bool:
    try:
        return Path(path).resolve().as_posix().startswith(Path(root).resolve().as_posix() + "/")
    except Exception:
        return False

def get_relative_display(path: str, root: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except Exception:
        return path

def get_last_assistant_message(payload: dict) -> str:
    return (payload.get("last_assistant_message") or payload.get("lastAssistantMessage") or "")

def get_candidate_paths(payload: dict) -> list[str]:
    """Extract all file paths referenced in the payload."""
    paths = []
    root = get_workspace_root(payload)
    ti = get_tool_input(payload)

    # Direct file path fields
    for key in ("file_path", "path", "target_file", "destination", "output_path"):
        val = ti.get(key, "")
        if val:
            r = resolve_path(str(val), root)
            if r:
                paths.append(r)

    # browser_download: Playwright MCP download path
    for key in ("download_path", "suggestedFilename", "downloadPath"):
        val = ti.get(key, "")
        if val and val.lower().endswith(".pdf"):
            r = resolve_path(str(val), root)
            if r:
                paths.append(r)

    # Bash command: parse redirections and paths
    cmd = ti.get("command", "") or ti.get("text", "")
    if cmd:
        # Redirections: > file.md, >> file.md
        for m in re.finditer(r'(?:>|>>)\s*["\']?([^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):
            r = resolve_path(m.group(1), root)
            if r:
                paths.append(r)
        # Output flags: -o file, --output file
        for m in re.finditer(r'(?:^|\s)(?:-o|--output)\s+["\']?([^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):
            r = resolve_path(m.group(1), root)
            if r:
                paths.append(r)
        # Absolute Windows paths
        for m in re.finditer(r'["\']?([A-Z]:\\[^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):
            r = resolve_path(m.group(1), root)
            if r:
                paths.append(r)
        # Python/script write paths: r'path/file.md', 'path/file.md', open("file.md")
        for m in re.finditer(r'''(?:r)?["']([^"'\n]+?\.(?:md|html|xlsx|pdf))["']''', cmd):
            r = resolve_path(m.group(1), root)
            if r and os.path.isfile(r):
                paths.append(r)

    # Embedded artifact links in assistant message
    msg = get_last_assistant_message(payload)
    if msg:
        for m in re.finditer(r'\[[^\]]+\]\(([^)]+\.(?:md|html|xlsx))\)', msg):
            r = resolve_path(m.group(1), root)
            if r:
                paths.append(r)

    return list(dict.fromkeys(paths))  # dedupe, preserve order

def is_artifact_like(text: str) -> bool:
    """Heuristic: does this text look like a research artifact?"""
    if not text or len(text) < 1000:
        return False
    return bool(re.search(r'(?m)^##\s+', text))

def is_research_artifact(display_or_path: str) -> bool:
    """True only for dated research markdown under industry/ (research artifacts).
    Operations artifacts (daily/ briefs, reports/, root files) are exempt from
    research-only hooks (source_contract, evidence_ledger_floor, ...)."""
    rel = (display_or_path or "").replace("\\", "/")
    if not (rel.startswith("industry/") or "/industry/" in rel):
        return False
    leaf = rel.rsplit("/", 1)[-1]
    return bool(re.match(r'^\d{8}-.+\.md$', leaf))

def get_body_without_resources(text: str) -> str:
    """Remove ## Resources section and everything after."""
    m = re.search(r'(?im)^##\s*Resources\b.*', text)
    if m:
        return text[:m.start()].rstrip()
    return text

def get_resources_section_text(text: str) -> Optional[str]:
    m = re.search(r'(?ims)^##\s*Resources\b(.*)$', text)
    if m:
        return m.group(1).strip()
    return None

def get_resources_entries(text: str) -> list[dict]:
    """Parse Resources entries supporting 4 formats:
    1a. `- [S1](url) — metadata`  (URL in parens, dash-separated description)
    1b. `- [S1](url) metadata`    (URL in parens, space-separated description, no dash)
    2.  `- [S1](url)`             (bare: URL only, no description)
    3.  `- [S1] metadata — url`   (loose: URL at end, not in parens — legacy format)
    """
    entries = []
    resources = get_resources_section_text(text) or ""
    seen = set()

    # Format 1a: `- [S1](url) — metadata` (dash-separated description after URL)
    for m in re.finditer(
        r'(?im)^\s*-\s*\[(?P<code>[SPILBGR]+\d+)(?:[^\]]*)\]\((?P<target>[^)]+)\)\s*[—\-]\s*(?P<meta>.+)$',
        resources
    ):
        code = m.group("code")
        if code not in seen:
            entries.append({"code": code, "target": m.group("target").strip(),
                            "metadata": m.group("meta").strip()})
            seen.add(code)

    # Format 1b: `- [S1](url) metadata` (space-separated description, no dash)
    for m in re.finditer(
        r'(?im)^\s*-\s*\[(?P<code>[SPILBGR]+\d+)(?:[^\]]*)\]\((?P<target>[^)]+)\)\s+(?P<meta>[^\s].*)$',
        resources
    ):
        code = m.group("code")
        if code not in seen:
            entries.append({"code": code, "target": m.group("target").strip(),
                            "metadata": m.group("meta").strip()})
            seen.add(code)

    # Format 2: `- [S1](url)` (URL in parens, no metadata afterward)
    for m in re.finditer(
        r'(?im)^\s*-\s*\[(?P<code>[SPILBGR]+\d+)(?:[^\]]*)\]\((?P<target>[^)]+)\)\s*$',
        resources
    ):
        code = m.group("code")
        if code not in seen:
            entries.append({"code": code, "target": m.group("target").strip(), "metadata": ""})
            seen.add(code)

    # Format 3: `- [S1] metadata — url` (URL at end, not in parens — legacy/loose format)
    for m in re.finditer(
        r'(?im)^\s*-\s*\[(?P<code>[SPILBGR]+\d+)\]\s+(?P<meta>.+?)\s+[—\-]\s+(?P<target>https?://\S+)\s*$',
        resources
    ):
        code = m.group("code")
        if code not in seen:
            entries.append({"code": code, "target": m.group("target").strip(),
                            "metadata": m.group("meta").strip()})
            seen.add(code)

    return entries

def get_short_anchor_matches(text: str) -> list[dict]:
    """Find all [S1](url), [P2](path), [I3](url), [LBG1](url), [R1](url), [SRC1](url) inline anchors."""
    matches = []
    for m in ANCHOR_CODE_RE.finditer(text):
        matches.append({
            "code": m.group("code"),
            "label_suffix": m.group(0)[m.group(0).index(']') - len(m.group(0)) + m.end('code') - m.start():m.start('target') - m.start() - 1] if m.end('code') < m.start('target') else "",
            "target": m.group("target").strip(),
            "full_match": m.group(0),
        })
    return matches

def get_markdown_tables(text: str) -> list[dict]:
    """Parse GFM pipe tables, excluding code fences."""
    lines = text.split("\n")
    tables = []
    in_fence = False
    i = 0
    while i < len(lines) - 1:
        header = lines[i]
        sep = lines[i + 1]

        if header.lstrip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        if "|" not in header or not _is_separator(sep):
            i += 1
            continue

        block = [header, sep]
        j = i + 2
        while j < len(lines):
            line = lines[j]
            if not line.strip():
                break
            if "|" not in line:
                break
            block.append(line)
            j += 1
        tables.append({"start_line": i + 1, "lines": block})
        i = j
    return tables

def _is_separator(line: str) -> bool:
    return bool(re.match(r'^\s*\|?(?:\s*:?-{2,}:?\s*\|)+(?:\s*:?-{2,}:?\s*)\|?\s*$', line))

def count_pipe_columns(line: str) -> int:
    clean = line.strip()
    # Normalize double-pipe || → | (fixes fix-bare-anchors table corruption residue)
    while "||" in clean:
        clean = clean.replace("||", "|")
    if clean.startswith("|"):
        clean = clean[1:]
    if clean.endswith("|"):
        clean = clean[:-1]
    if not clean.strip():
        return 0
    return len(re.split(r'(?<!\\)\|', clean))

def is_valid_source_target(target: str) -> bool:
    """Check if target is a valid URL, file path, or #fragment."""
    if not target or not target.strip():
        return False
    t = target.strip()
    if t.lower() in ("link", "url"):
        return False
    if t.startswith("#"):
        return True
    if t.startswith("?") or t.startswith("&"):
        return False
    # Absolute URL
    if re.match(r'^https?://', t):
        return True
    # Other URI schemes
    if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', t):
        return True
    # Absolute path
    try:
        if os.path.isabs(t):
            Path(t)
            return True
    except Exception:
        pass
    # Looks like a relative path
    if re.search(r'[\\/]', t) or re.match(r'^[^.\\/\s]+\.[A-Za-z0-9]{1,10}$', t):
        try:
            Path(t)
            return True
        except Exception:
            pass
    return False

def is_topic_artifact_root_file(path: str, root: str) -> bool:
    """Check if file is at industry/{ind}/companies/{ticker}/file.md (5 levels) or industry/{ind}/file.md (3 levels)."""
    try:
        rel = Path(path).resolve().relative_to(Path(root).resolve())
        parts = rel.parts
        # Company artifact: industry/<ind>/companies/<ticker>/file.md (5 levels)
        if len(parts) == 5 and parts[0] == "industry" and parts[2] == "companies":
            return True
        # Industry artifact: industry/<ind>/file.md (3 levels)
        if len(parts) == 3 and parts[0] == "industry":
            return True
        return False
    except Exception:
        return False

def get_primary_heading(text: str) -> Optional[str]:
    m = re.search(r'(?im)^#\s+(.+?)\s*$', text)
    if m:
        return m.group(1).strip()
    return None

def get_markdown_targets(payload: dict) -> list[dict]:
    """Return file + inline targets for hook inspection."""
    targets = []
    root = get_workspace_root(payload)
    for path in get_candidate_paths(payload):
        if path and re.search(r'\.(md|html)$', path, re.IGNORECASE) and os.path.isfile(path):
            try:
                text = Path(path).read_text(encoding="utf-8")
            except Exception:
                continue
            targets.append({
                "kind": "file",
                "path": path,
                "display": get_relative_display(path, root),
                "text": text,
            })
    return targets



def scan_recent_mtime(workspace_root: str, since_seconds: float = 15.0) -> list[str]:
    """Scan workspace for files modified in the last N seconds.
    Only checks root level + industry/ tree (1 level deep for speed).
    Returns list of full paths."""
    import time, os
    root = Path(workspace_root)
    recent = []
    cutoff = time.time() - since_seconds
    try:
        for entry in os.scandir(str(root)):
            try:
                if entry.is_file() and entry.stat().st_mtime > cutoff:
                    recent.append(str(root / entry.name))
                elif entry.is_dir() and entry.name in ('industry', '.cache', '.scripts', '.references', '.claude', '.codex'):
                    for sub in os.scandir(entry.path):
                        try:
                            if sub.is_file() and sub.stat().st_mtime > cutoff:
                                recent.append(str(root / entry.name / sub.name))
                        except OSError:
                            pass
            except OSError:
                pass
    except OSError:
        pass
    return recent

def block(msg: str):
    sys.stderr.write(f"{msg}\n")
    sys.exit(2)

def warn(msg: str):
    sys.stderr.write(f"HOOK WARNING: {msg}\n")
    sys.exit(0)
