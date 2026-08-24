"""Hook: auto-resolve session transcript conflicts on Stop.

Triggers on Claude Code Stop event. Pure Python, no external dependencies —
works on Windows, macOS, Linux.

Detects conflict copies by both naming schemes:
  <BASE>.sync-conflict-YYYYMMDD-HHMMSS-<DEVICE>.jsonl  (Syncthing)
  <BASE>-<MACHINE_NAME>[-<N>].jsonl                    (OneDrive-style, legacy)

Resolution rule — subsumption-first, so the common case never pays for a full
merge (2026-08-21: rewritten for Syncthing naming + fast path;
2026-08-24: size threshold removed — huge transcripts merge too):
  1. copy rows ⊆ base rows  → delete the copy          (~instant, lossless)
  2. base rows ⊂ copy rows  → copy is FULLER (Syncthing picked the wrong
                              winner): replace base with copy
  3. both have unique rows  → full merge (timestamp-sorted, uuid-dedup) —
                              any size (no threshold; merge is atomic
                              via tmp + os.replace, so a hook timeout can
                              never corrupt the base)
Active sessions (listed in .sessions-manifests/) — the base is being written
live, so it is NEVER rewritten; a subset copy is still safe to delete
(doesn't touch base), a non-subset copy is left until the session ends.
Best-effort: never raises, never blocks the CLI.

Rows are compared by (sha256, length) — collision-safe for transcript lines,
with no need to hold file contents in memory. Lines that fail JSON parsing
(truncated by an in-flight sync) are ignored, so a torn tail line can never
make us think a copy holds unique content.
"""

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

SYNC_CONFLICT_RE = re.compile(
    r"^(?P<base>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"\.sync-conflict-\d{8}-\d{6}-[A-Za-z0-9]{7}\.jsonl$"
)
# OneDrive-style: <uuid>-<MACHINE>[-<N>].jsonl (legacy; machine names may
# be mixed-case, e.g. "MacBook-Pro-1" — a suffix on a uuid is never a legit
# transcript name, so this can't false-positive)
MACHINE_SUFFIX_RE = re.compile(
    r"^(?P<base>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"-[A-Za-z0-9][A-Za-z0-9-]*(?:-\d+)?\.jsonl$"
)
def find_sessions_dir():
    """Locate .sessions/ via the project hash directory junction/symlink."""
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return None

    # First try: check known hash dirs linked to .sessions/
    for hd_name in ("s--",):
        hd = projects / hd_name
        if hd.is_dir():
            if hd.is_symlink() or _is_junction(hd):
                return hd.resolve()
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


# ── row comparison ──────────────────────────────────────────────

def _row_key(line: str) -> bytes:
    """Stable key for a transcript row: (sha256, length)."""
    return hashlib.sha256(line.encode("utf-8", "replace")).digest() + b"\x00" + str(len(line)).encode()


def _build_index(path: Path) -> set:
    """Row-hash set of a JSONL file. Torn lines (invalid JSON) are skipped."""
    idx = set()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except Exception:
                    continue  # truncated tail line — ignore
                idx.add(_row_key(line))
    except OSError:
        pass
    return idx


def _classify(base: Path, copy: Path):
    """Return action: 'delete-copy' | 'replace-base' | 'merge' | 'skip'."""
    idx_base = _build_index(base)
    if not idx_base:
        return "skip"  # base unreadable/empty — leave to manual fix
    idx_copy = _build_index(copy)
    if idx_copy <= idx_base:
        return "delete-copy"
    if idx_base <= idx_copy:
        return "replace-base"
    return "merge"  # mutual-unique — any size, merge is atomic


# ── full merge (rare path, small files only) ───────────────────

def _read_rows(path: Path) -> list:
    """Read JSONL rows into [(line, ts, uuid)] preserving order (tuple, low mem)."""
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                ts, uuid = "", None
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        ts = obj.get("timestamp") or ""
                        uuid = obj.get("uuid")
                except Exception:
                    pass
                out.append((line, ts, uuid))
    except OSError:
        pass
    return out


def _merge_rows(base_rows: list, copy_rows: list) -> list:
    """Union rows, dedup by uuid (fallback exact-line), sorted by timestamp."""
    merged = list(base_rows)
    seen = {r[2] for r in merged if r[2]}
    for r in copy_rows:
        if r[2]:
            if r[2] in seen:
                continue
            seen.add(r[2])
        else:
            if any(o[0] == r[0] for o in merged):
                continue
        merged.append(r)
    merged.sort(key=lambda r: (r[1] or "￿",))
    return merged


def _merge_into(base: Path, copy: Path) -> None:
    """Merge copy rows into base (timestamp-sorted, uuid-dedup), atomic write."""
    merged = _merge_rows(_read_rows(base), _read_rows(copy))
    tmp = base.with_name(base.name + ".se-clean-tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            for r in merged:
                fh.write(r[0] + "\n")
        os.replace(tmp, base)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# ── active-session guard ────────────────────────────────────────

def _active_session_ids(manifests_dir: Path) -> set:
    """sessionIds currently registered in .sessions-manifests/."""
    active = set()
    if not manifests_dir.is_dir():
        return active
    for mf in manifests_dir.glob("*.json"):
        if mf.name.startswith(".") or ".sync-conflict-" in mf.name:
            continue
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        sid = data.get("sessionId") or ""
        if sid:
            active.add(sid)
    return active


# ── main sweep ──────────────────────────────────────────────────

def process_sessions(sessions_dir: Path, manifests_dir: Path, log=None) -> dict:
    """Scan and auto-resolve conflicts. Returns {'deleted':n, 'replaced':n, 'merged':n, 'skipped':n}."""
    out = {"deleted": 0, "replaced": 0, "merged": 0, "skipped": 0}
    active = _active_session_ids(manifests_dir)

    conflicts = []
    try:
        for f in sorted(sessions_dir.glob("*.jsonl")):
            m = SYNC_CONFLICT_RE.match(f.name) or MACHINE_SUFFIX_RE.match(f.name)
            if m:
                conflicts.append((sessions_dir / (m.group("base") + ".jsonl"), f))
    except OSError:
        return out

    for base, copy in conflicts:
        if not base.is_file():
            continue  # orphan — left for session-sync.py fix
        if base.name[:-len(".jsonl")] in active:
            # Active session: base is being written live — never rewrite it.
            # A subset copy is still safe to delete (base untouched, lossless);
            # a non-subset copy is left until the session ends.
            try:
                if _classify(base, copy) == "delete-copy":
                    copy.unlink()
                    out["deleted"] += 1
                    if log:
                        log(f"[session_conflict_clean] delete-copy (active): {copy.name}")
            except Exception:
                pass
            continue
        try:
            action = _classify(base, copy)
        except Exception:
            action = "skip"
        try:
            if action == "delete-copy":
                copy.unlink()
                out["deleted"] += 1
            elif action == "replace-base":
                os.replace(copy, base)
                out["replaced"] += 1
            elif action == "merge":
                _merge_into(base, copy)
                copy.unlink()
                out["merged"] += 1
            else:
                out["skipped"] += 1
        except OSError:
            out["skipped"] += 1
        if log:
            log(f"[session_conflict_clean] {action}: {copy.name}")
    return out


def check(ctx):
    """Hook entry point. Best-effort: never raise."""
    sessions_dir = find_sessions_dir()
    if sessions_dir is None:
        return
    manifests_dir = sessions_dir.parent / ".sessions-manifests"
    try:
        process_sessions(sessions_dir, manifests_dir)
    except Exception:
        pass


# ── legacy OneDrive deleted-session cleanup (kept for compatibility) ──

def _clean_deleted_sessions(sessions_dir):
    """Delete .jsonl files listed in .sessions/deleted.json (OneDrive era)."""
    deleted_file = sessions_dir / "deleted.json"
    if not deleted_file.is_file():
        return
    try:
        data = json.loads(deleted_file.read_text(encoding="utf-8"))
        deleted_ids = {item["sessionId"] for item in data.get("deleted", [])}
    except (json.JSONDecodeError, KeyError, OSError):
        return
    if not deleted_ids:
        return
    cleaned = []
    for sid in deleted_ids:
        jsonl = sessions_dir / f"{sid}.jsonl"
        subdir = sessions_dir / sid
        removed = False
        try:
            if jsonl.is_file():
                jsonl.unlink()
                removed = True
        except OSError:
            pass
        try:
            if subdir.is_dir():
                shutil.rmtree(subdir, ignore_errors=True)
                removed = True
        except OSError:
            pass
        if removed:
            cleaned.append(sid)
    remaining = [item for item in data.get("deleted", [])
                 if item["sessionId"] not in cleaned]
    if remaining:
        data["deleted"] = remaining
        try:
            deleted_file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
        except OSError:
            pass
    else:
        try:
            deleted_file.unlink()
        except OSError:
            pass
