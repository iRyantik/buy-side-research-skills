"""
Shared library for Python-based Codex/Claude hooks.
Drop-in equivalent of _hook_common.ps1 — loaded by individual hook scripts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Payload / I/O
# ---------------------------------------------------------------------------

def get_hook_payload(input_path: str | None = None) -> dict[str, Any] | None:
    raw = ""
    if input_path:
        raw = Path(input_path).read_text(encoding="utf-8")
    else:
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
    if not raw or not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_block(message: str, severity: str = "block") -> None:
    if severity == "warn":
        sys.stderr.write(f"HOOK WARNING: {message}\n")
        sys.exit(0)
    sys.stderr.write(f"{message}\n")
    sys.exit(2)


def write_warn(message: str) -> None:
    sys.stderr.write(f"HOOK WARNING: {message}\n")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------

def get_workspace_root(payload: dict) -> str:
    if "cwd" in payload and payload["cwd"]:
        return str(Path(payload["cwd"]).resolve())
    return str(Path.cwd().resolve())


def _to_workspace_path(workspace_root: str, path: str) -> str | None:
    clean = path.strip().strip('"').strip("'")
    if not clean:
        return None
    p = Path(clean)
    if p.is_absolute():
        return str(p.resolve())
    return str((Path(workspace_root) / clean).resolve())


def test_path_under(path: str, root: str) -> bool:
    try:
        return Path(path).resolve().as_posix().startswith(Path(root).resolve().as_posix() + "/")
    except Exception:
        return False


def get_relative_display_path(path: str, root: str) -> str:
    try:
        rel = Path(path).resolve().relative_to(Path(root).resolve())
        return rel.as_posix()
    except ValueError:
        return path


# ---------------------------------------------------------------------------
# Tool metadata
# ---------------------------------------------------------------------------

def get_tool_name(payload: dict) -> str:
    return str(payload.get("tool_name", ""))


def get_tool_input(payload: dict) -> dict:
    ti = payload.get("tool_input")
    if isinstance(ti, dict):
        return ti
    return {}


def get_last_assistant_message(payload: dict) -> str:
    return str(payload.get("last_assistant_message", ""))


# ---------------------------------------------------------------------------
# Path extraction
# ---------------------------------------------------------------------------

def get_candidate_paths(payload: dict) -> list[str]:
    """Extract file-system paths from a tool-use payload."""
    paths: list[str] = []
    workspace = get_workspace_root(payload)
    msg = get_last_assistant_message(payload)
    ti = get_tool_input(payload)

    for field in ("file_path", "path", "target_file", "destination", "output_path", "transcript_path"):
        v = ti.get(field) or payload.get(field)
        if v and isinstance(v, str) and v.strip():
            abs_path = _to_workspace_path(workspace, v)
            if abs_path:
                paths.append(abs_path)

    for field in ("file_path", "path", "output_path"):
        v = ti.get(field)
        if isinstance(v, dict) and v.get("path"):
            abs_path = _to_workspace_path(workspace, str(v["path"]))
            if abs_path:
                paths.append(abs_path)

    # Write command: parse the content block for file paths
    content = ti.get("content") or ti.get("file_text") or ""
    if isinstance(content, str):
        for m in re.finditer(r'(?m)^\*\*\*\s*(?:Add|Update)\s*(?:File|文件):\s*(.+?)\s*\*\*\*', content):
            abs_path = _to_workspace_path(workspace, m.group(1).strip())
            if abs_path:
                paths.append(abs_path)

    # Redirection patterns in command text
    cmd = _get_command_text(payload)
    for m in re.finditer(r'[>|]\s*(\S+\.(?:md|html|xlsx|xlsm))', cmd):
        abs_path = _to_workspace_path(workspace, m.group(1).strip())
        if abs_path:
            paths.append(abs_path)

    if msg:
        for m in re.finditer(r'\]\(([^)]+\.(?:md|html))\)', msg):
            abs_path = _to_workspace_path(workspace, m.group(1).strip())
            if abs_path:
                paths.append(abs_path)

    # Deduplicate
    seen: set[str] = set()
    unique: list[str] = []
    for p in paths:
        try:
            key = Path(p).resolve().as_posix()
        except Exception:
            key = p
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _get_command_text(payload: dict) -> str:
    cmd = payload.get("command") or payload.get("command_text") or ""
    if isinstance(cmd, str):
        return cmd
    return ""


# ---------------------------------------------------------------------------
# Markdown artifact detection
# ---------------------------------------------------------------------------

ANCHOR_CODE_PATTERN = re.compile(r'\[((?:S|P|I|LBG|R|SRC)\d+)(?:[^\]]*)\]\(([^)]+)\)')


def test_is_artifact_like_text(text: str) -> bool:
    if not text or not text.strip():
        return False
    has_heading = bool(re.search(r'(?m)^##\s+', text))
    if len(text) >= 1000 and has_heading:
        return True
    if has_heading and re.search(r'(?m)^\|\s*.+\s*\|$', text):
        return True
    return False


def test_is_casual_chat(payload: dict) -> bool:
    tool = get_tool_name(payload)
    if tool not in ("Write", "Edit", "MultiEdit"):
        return True
    candidates = get_candidate_paths(payload)
    if not candidates:
        return True
    for c in candidates:
        p = str(c)
        if re.search(r'topics[/\\]', p) or re.search(r'\.(?:xlsx|xlsm)$', p):
            return False
    return True


# ---------------------------------------------------------------------------
# Source contract helpers
# ---------------------------------------------------------------------------

def get_markdown_targets(payload: dict) -> list[dict]:
    targets: list[dict] = []
    workspace = get_workspace_root(payload)
    candidates = get_candidate_paths(payload)
    msg = get_last_assistant_message(payload)

    for p in candidates:
        if re.search(r'\.(?:md|html)$', str(p)):
            try:
                text = Path(p).read_text(encoding="utf-8")
            except Exception:
                text = ""
            targets.append({
                "kind": "file",
                "path": str(p),
                "display": get_relative_display_path(str(p), workspace),
                "text": text,
            })

    if msg:
        targets.append({
            "kind": "inline",
            "path": "",
            "display": "last_assistant_message",
            "text": msg,
        })

    return targets


def get_body_without_resources(text: str) -> str:
    return re.sub(r'(?is)^##\s*Resources\b.*$', '', text, flags=re.MULTILINE).strip()


def get_resources_section_text(text: str) -> str | None:
    m = re.search(r'(?is)^##\s*Resources\b(.*)$', text, flags=re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def get_short_anchor_matches(text: str) -> list[dict]:
    results: list[dict] = []
    for m in ANCHOR_CODE_PATTERN.finditer(text):
        results.append({
            "Code": m.group(1),
            "Target": m.group(2).strip(),
            "FullMatch": m.group(0),
        })
    return results


def get_resources_entries(text: str | None) -> list[dict]:
    if not text:
        return []
    results: list[dict] = []
    pattern_meta = re.compile(r'(?im)^\s*-\s*\[((?:S|P|I|LBG|R|SRC)\d+)(?:[^\]]*)\]\(([^)]+)\)\s*=\s*(.*)$')
    pattern_bare = re.compile(r'(?im)^\s*-\s*\[((?:S|P|I|LBG|R|SRC)\d+)(?:[^\]]*)\]\(([^)]+)\)\s*$')
    seen_codes: set[str] = set()

    for m in pattern_meta.finditer(text):
        results.append({
            "Code": m.group(1),
            "Target": m.group(2).strip(),
            "Metadata": m.group(3).strip(),
            "Line": m.group(0).strip(),
        })
        seen_codes.add(m.group(1))

    for m in pattern_bare.finditer(text):
        if m.group(1) not in seen_codes:
            results.append({
                "Code": m.group(1),
                "Target": m.group(2).strip(),
                "Metadata": "",
                "Line": m.group(0).strip(),
            })
            seen_codes.add(m.group(1))

    return results


def test_is_valid_source_target(target: str) -> bool:
    if not target or not target.strip():
        return False
    clean = target.strip()
    if clean.lower() in ("link", "url"):
        return False
    if clean.startswith("#"):
        return True
    if clean.startswith("?") or clean.startswith("&"):
        return False

    # Absolute URI
    if re.match(r'^[A-Za-z][A-Za-z0-9+.\-]*:', clean):
        return clean.lower().startswith(("http:", "https:"))

    # Absolute path
    if Path(clean).is_absolute():
        try:
            Path(clean).resolve()
            return True
        except Exception:
            return False

    # Looks like a relative path?
    if re.search(r'[\\/]', clean) or re.match(r'^[^\\/:*?"<>|]+\.[A-Za-z0-9]{1,10}$', clean) or re.match(r'^[.]{1,2}[\\/]', clean):
        try:
            (Path.cwd() / clean).resolve()
            return True
        except Exception:
            return False

    # Bare label (e.g. "S1", "data123") — accept
    if re.match(r'^[A-Za-z0-9_\-.]+$', clean):
        return True

    return False


def get_source_contract_state(text: str) -> dict:
    body = get_body_without_resources(text)
    resources = get_resources_section_text(text)
    body_anchors = get_short_anchor_matches(body)
    resource_entries = get_resources_entries(resources)
    resource_map: dict[str, list[dict]] = {}
    for entry in resource_entries:
        resource_map.setdefault(entry["Code"], []).append(entry)
    return {
        "Body": body,
        "Resources": resources or "",
        "BodyAnchors": body_anchors,
        "ResourceEntries": resource_entries,
        "ResourceMap": resource_map,
    }


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------

def test_is_markdown_table_separator_line(line: str) -> bool:
    return bool(re.match(r'^\s*\|?(?:\s*:?-{2,}:?\s*\|)+(?:\s*:?-{2,}:?\s*)\|?\s*$', line))


def get_markdown_table_column_count(line: str) -> int:
    clean = line.strip()
    if clean.startswith("|"):
        clean = clean[1:]
    if clean.endswith("|"):
        clean = clean[:-1]
    if not clean:
        return 0
    return len(re.split(r'(?<!\\)\|', clean))


def get_markdown_pipe_tables(text: str) -> list[dict]:
    tables: list[dict] = []
    if not text:
        return tables
    lines = text.splitlines()
    idx = 0
    in_fence = False
    while idx < len(lines) - 1:
        header = lines[idx]
        sep = lines[idx + 1]

        if header.strip().startswith("```"):
            in_fence = not in_fence
            idx += 1
            continue
        if in_fence:
            idx += 1
            continue

        if "|" in header and test_is_markdown_table_separator_line(sep):
            block_lines = [header, sep]
            cursor = idx + 2
            while cursor < len(lines):
                line = lines[cursor]
                if not line.strip():
                    break
                if "|" not in line:
                    break
                block_lines.append(line)
                cursor += 1
            tables.append({"StartLine": idx + 1, "Lines": block_lines})
            idx = cursor
            continue
        idx += 1
    return tables


# ---------------------------------------------------------------------------
# Topic artifact helpers
# ---------------------------------------------------------------------------

def test_is_topic_artifact_root_file(path: str, workspace_root: str) -> bool:
    try:
        rel = Path(path).resolve().relative_to(Path(workspace_root).resolve())
        parts = rel.parts
        return (
            len(parts) >= 2
            and parts[0] == "topics"
            and not any(p.startswith("_") for p in parts)
        )
    except (ValueError, OSError):
        return False


# ---------------------------------------------------------------------------
# Primary heading
# ---------------------------------------------------------------------------

def get_primary_heading(text: str) -> str | None:
    m = re.search(r'(?im)^#\s+(.+?)\s*$', text)
    if not m:
        return None
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# SHA256
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
