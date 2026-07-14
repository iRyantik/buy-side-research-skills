"""Hook: merge OneDrive session conflict copies on Stop.

Triggers on Claude Code Stop event.
Pure Python, no external dependencies — works on Windows, macOS, Linux.

Detects OneDrive conflict copies by the pattern:
  <BASE>-<MACHINE_NAME>.jsonl  or  <BASE>-<MACHINE_NAME>-<N>.jsonl
where <BASE> is an existing file or directory in .sessions/.

Merge logic: union of all unique non-empty lines from all copies into the
base file, then delete the conflict copies.
"""

import os
from pathlib import Path


def find_sessions_dir():
    """Locate .sessions/ via the project hash directory symlink."""
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return None

    # First try: check known hash dirs linked to .sessions/
    for hd_name in ("s--",):
        hd = projects / hd_name
        if hd.is_dir():
            # If it's a symlink/junction, follow it
            if hd.is_symlink() or _is_junction(hd):
                return hd.resolve()
            # Otherwise check if it looks like .sessions/
            if (hd / "tool-results").is_dir() or list(hd.glob("*.jsonl")):
                return hd

    # Second try: find any hash dir linked to a .sessions-like path
    for hd in projects.iterdir():
        if not hd.is_dir():
            continue
        if hd.is_symlink() or _is_junction(hd):
            resolved = hd.resolve()
            if resolved.name == ".sessions" or (resolved / "tool-results").is_dir():
                return resolved

    return None


def _is_junction(path):
    """Windows junction detection."""
    import platform
    if platform.system() != "Windows":
        return False
    try:
        import stat
        attrs = path.stat().st_file_attributes
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


def _iter_conflicts(sessions_dir):
    """Yield (conflict_path, base_path) for each OneDrive conflict copy."""
    conflict_patterns = []

    # Collect all .jsonl files and directories for base-name matching
    files_and_dirs = {}
    try:
        for entry in sessions_dir.iterdir():
            files_and_dirs[entry.name] = entry
    except (OSError, PermissionError):
        return

    for f in sorted(sessions_dir.glob("*.jsonl")):
        base_name = _find_base(f.name, files_and_dirs)
        if base_name:
            base_path = sessions_dir / base_name
            yield f, base_path


def _find_base(filename, files_and_dirs):
    """Try stripping -suffixes from filename to find an existing base.

    E.g. "abc123-DEREK-2.jsonl" -> strip "-2" -> "abc123-DEREK.jsonl"
         -> strip "-DEREK" -> "abc123.jsonl" (exists in files_and_dirs)
    Returns base_name or None.
    """
    stem = filename.rsplit(".", 1)[0]  # Remove .jsonl
    # Try up to 5 levels of suffix stripping
    for _ in range(5):
        last_dash = stem.rfind("-")
        if last_dash <= 0:
            return None
        stem = stem[:last_dash]
        # Check if this stem exists as .jsonl file
        jsonl_name = stem + ".jsonl"
        if jsonl_name in files_and_dirs:
            return jsonl_name
        # Check if this stem exists as a directory
        if stem in files_and_dirs and files_and_dirs[stem].is_dir():
            return jsonl_name
    return None


def _union_merge(base_path, conflict_path):
    """Read both files, union-merge unique non-empty lines, write to base."""
    lines = []

    for path in (base_path, conflict_path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    stripped = line.rstrip("\n\r")
                    if stripped:
                        lines.append(stripped)
        except (OSError, UnicodeDecodeError):
            continue

    # Preserve order within each source: seen set
    seen = set()
    deduped = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            deduped.append(line)

    if deduped:
        try:
            with open(base_path, "w", encoding="utf-8", newline="\n") as fh:
                for line in deduped:
                    fh.write(line + "\n")
        except OSError:
            pass


def _clean_orphan_transcripts(sessions_dir):
    """Delete .jsonl transcript files whose sessionId has no manifest.

    When user deletes a session in CC UI, the manifest file in
    ~/.claude/sessions/<PID>.json is removed, but the transcript .jsonl
    remains on disk. CC rescans .jsonl files on restart and recreates
    manifests, causing deleted sessions to reappear.

    This removes .jsonl files with no matching manifest, but ONLY if the
    .jsonl is older than 7 days (safety: prevent deleting sessions from
    another machine that hasn't synced manifests recently).
    """
    import time
    import json

    manifests_dir = Path.home() / ".claude" / "sessions"
    if not manifests_dir.is_dir():
        return

    # Collect active sessionIds from all manifests
    active_ids = set()
    for mf in manifests_dir.glob("*.json"):
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            sid = data.get("sessionId")
            if sid:
                active_ids.add(sid)
        except (json.JSONDecodeError, OSError):
            continue

    if not active_ids:
        return  # No manifests at all — don't clean, safety first

    cutoff = time.time() - 7 * 86400  # 7 days ago

    for f in sessions_dir.glob("*.jsonl"):
        # Skip conflict copies (handled by _iter_conflicts)
        if "-" in f.stem and _find_base(f.name, {}):
            continue

        sid = f.stem  # filename = sessionId
        if sid in active_ids:
            continue

        # Check age
        try:
            mtime = f.stat().st_mtime
            if mtime < cutoff:
                f.unlink()
        except OSError:
            continue


def check(ctx):
    """Hook entry point. Best-effort: never raise."""
    sessions_dir = find_sessions_dir()
    if sessions_dir is None:
        return

    try:
        for conflict_path, base_path in _iter_conflicts(sessions_dir):
            try:
                _union_merge(base_path, conflict_path)
                conflict_path.unlink()
            except Exception:
                continue
    except Exception:
        pass

    # Clean orphan transcripts (deleted sessions)
    try:
        _clean_orphan_transcripts(sessions_dir)
    except Exception:
        pass
