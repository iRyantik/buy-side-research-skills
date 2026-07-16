#!/usr/bin/env python3
"""setup.py — Cross-platform session sync one-click setup.

Sets up a symlink (macOS) or junction (Windows) from every
Claude Code project hash directory to the OneDrive .sessions/ directory,
so all machines share the same session files with zero ongoing maintenance.

Usage:
    python3 setup.py          # auto-detect everything
    python3 setup.py --dry-run  # show what would be done, don't do it
"""

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path


# ── CLI ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Claude Code session sync setup")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    parser.add_argument("--sessions-dir", help="Override .sessions/ path")
    args = parser.parse_args()

    print("=" * 48)
    print("  Claude Code Session Sync Setup")
    print("=" * 48)
    print(f"  OS      : {platform.system()} {platform.release()}")
    print(f"  Machine : {platform.node()}")
    print()

    # 1. Find .sessions/
    sessions = args.sessions_dir or find_sessions_dir()
    if not sessions:
        print("[FAIL] Cannot find .sessions/ directory.")
        print("       Make sure OneDrive is set up and the CC research workspace is synced.")
        sys.exit(1)
    sessions = Path(sessions).resolve()
    print(f"[ OK ] .sessions/ = {sessions}")
    print()

    # 2. Find all CC project hash directories pointing to this workspace
    workspace_root = find_workspace_root(sessions)
    if not workspace_root:
        print("[FAIL] Cannot determine workspace root from .sessions/ path.")
        sys.exit(1)
    print(f"[ OK ] Workspace   = {workspace_root}")

    hash_dirs = find_hash_dirs(workspace_root, sessions)
    if not hash_dirs:
        print("[ OK ] No hash dirs to set up (already done or no CC projects yet)")
    else:
        print(f"[ OK ] Hash dirs to link:")
        for hd in hash_dirs:
            print(f"         {hd.name}  ->  {sessions}")

    print()

    # 3. Clean up old sync infrastructure (Windows)
    if platform.system() == "Windows":
        cleanup_windows()

    # 4. Find/create .sessions-manifests/ for manifest sync
    manifests_dir = workspace_root / ".sessions-manifests"
    manifests_dir.mkdir(exist_ok=True)
    print(f"[ OK ] .sessions-manifests/ = {manifests_dir}")
    print()

    # 5. Create links
    if args.dry_run:
        print("[DRY RUN] Would create junctions/symlinks. No changes made.")
        return

    for hd in hash_dirs:
        create_link(hd, sessions, workspace_root)

    # 6. Manifest sync: junction ~/.claude/sessions/ -> .sessions-manifests/
    print("Manifest sync...")
    claude_sessions = Path.home() / ".claude" / "sessions"
    setup_manifest_sync(claude_sessions, manifests_dir)

    # 7. Verify
    print()
    print("Verifying...")
    ok, msg = verify(sessions, hash_dirs)
    print(f"  {msg}")
    if not ok:
        print("  Some hash dirs may need manual attention.")
        sys.exit(1)

    print()
    print("=" * 48)
    print("  Setup Complete")
    print("=" * 48)
    print()
    print("All machines now share the same sessions via OneDrive.")
    print("To sync a new machine, run this script on it.")
    print("To clean up conflict copies (rare), Stop hook runs automatically.")


# ── Detection ────────────────────────────────────────────
def find_sessions_dir():
    """Locate the .sessions/ directory inside the CC research workspace."""
    candidates = []

    system = platform.system()
    home = str(Path.home())

    if system == "Windows":
        # Try S: drive first
        s_sessions = Path(workspace_root) / ".sessions"
        if s_sessions.is_dir():
            return str(s_sessions)

        # Try OneDrive known paths
        onedrive_base = os.environ.get("OneDriveCommercial", "")
        if not onedrive_base:
            onedrive_base = os.environ.get("OneDrive", "")
        if not onedrive_base:
            # Default pattern
            candidates.extend([
                Path(home) / "OneDrive - Hel Ved Capital Management Limited",
                Path(home) / "OneDrive",
                Path(home) / "OneDrive - Personal",
            ])
        else:
            candidates.append(Path(onedrive_base))

        for base in candidates:
            if base.is_dir():
                # Search for CC research workspace
                for pattern in ["CC research workspace", "*research*workspace*"]:
                    for found in base.glob(pattern):
                        p = found / ".sessions"
                        if p.is_dir():
                            return str(p)

    elif system == "Darwin":
        # macOS — OneDrive in ~/Library/CloudStorage
        cloud_base = Path(home) / "Library" / "CloudStorage"
        if cloud_base.is_dir():
            for od_dir in cloud_base.glob("OneDrive*"):
                for ws_dir in od_dir.glob("*research*workspace*"):
                    p = ws_dir / ".sessions"
                    if p.is_dir():
                        return str(p)
        # Fallback: ~/OneDrive
        for od_dir in Path(home).glob("OneDrive*"):
            for ws_dir in od_dir.glob("*research*workspace*"):
                p = ws_dir / ".sessions"
                if p.is_dir():
                    return str(p)

    else:
        # Linux — this is a stretch, but try common mounts
        for base in [Path("/mnt/c/Users"), Path.home() / "OneDrive"]:
            for pattern in ["*research*workspace*", "*CC research*"]:
                for found in base.glob(pattern):
                    p = found / ".sessions"
                    if p.is_dir():
                        return str(p)

    return None


def find_workspace_root(sessions_path):
    """The workspace is the parent of .sessions/."""
    return sessions_path.parent


def find_hash_dirs(workspace_root, sessions_path):
    """Find all ~/.claude/projects/* directories that belong to this workspace.

    A hash dir belongs to this workspace if:
    - It IS already a link to sessions_path (already set up) → skip
    - It contains .jsonl files that match sessions_path .jsonl filenames
    - OR its name encodes the workspace path (e.g. s--, c--Users-xxx-...)
    """
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return []

    # Get the set of session filenames in .sessions/ for matching
    session_files = set()
    try:
        for f in sessions_path.glob("*.jsonl"):
            session_files.add(f.name)
    except (OSError, PermissionError):
        pass

    # Also collect known partial-filename signatures
    session_signatures = set()
    for f in session_files:
        # First 8 chars of a UUID for quick matching
        if len(f) >= 8:
            session_signatures.add(f[:8])

    workspace_path_str = str(workspace_root).lower().replace("\\", "/").replace(":", "")

    result = []
    for hd in sorted(projects.iterdir()):
        if not hd.is_dir():
            continue

        # Skip if already a symlink/junction
        if hd.is_symlink() or is_junction(hd):
            continue

        # Skip common non-project dirs
        if hd.name.startswith(".") or hd.name in ("memory", "_restore_temp"):
            continue

        # Method 1: name encodes the workspace path
        normalized = hd.name.lower().replace("-", "")
        if _hash_matches_workspace(normalized, workspace_path_str):
            result.append(hd)
            continue

        # Method 2: session files match
        try:
            hd_jsonl = set(f.name for f in hd.glob("*.jsonl"))
            if hd_jsonl and session_files and hd_jsonl & session_files:
                result.append(hd)
                continue
        except (OSError, PermissionError):
            pass

        # Method 3: subdirectories match (truncated UUIDs seen on Windows)
        try:
            hd_dirs = set(d.name for d in hd.iterdir() if d.is_dir() and not d.name.startswith("."))
            sessions_dirs = set(d.name for d in sessions_path.iterdir()
                              if d.is_dir() and not d.name.startswith("."))
            if hd_dirs and sessions_dirs and hd_dirs & sessions_dirs:
                result.append(hd)
        except (OSError, PermissionError):
            pass

    return result


def _hash_matches_workspace(hash_name, workspace_path_str):
    """Check if a CC project hash directory name matches the workspace path.

    CC encodes the project path as: replace non-alnum with -, lowercase.
    E.g. "C:/Users/M/OneDrive/.../CC research workspace" might become:
    "c--users-m-onedrive---hel-ved-capital-management-limited-cc-research-workspace"
    or simply "s--" (from S:/).
    """
    # Try stripping the hash_name back: remove leading char + first two --
    # Common patterns: "c--users-yuzhe-..." or "s--"
    parts = hash_name.split("--", 1)
    if len(parts) == 2:
        # Has format like "c--users-yuzhe-..."
        suffix = parts[1].replace("-", "")
        ws_suffix = workspace_path_str.replace(" ", "").replace("-", "")
        # Check if the suffix is a substring match
        if suffix and ws_suffix and (suffix in ws_suffix or ws_suffix in suffix):
            return True

    # Direct match of key path components
    key_parts = [p for p in workspace_path_str.replace(" ", "").split("\\")
                 if p and p not in ("\\", "/")]
    # Check if the hash_name contains enough identifying path parts
    match_count = 0
    for part in key_parts:
        if len(part) > 4 and part in hash_name:
            match_count += 1
    return match_count >= 2


def is_junction(path):
    """Check if a path is a Windows junction (reparse point)."""
    if platform.system() != "Windows":
        return False
    try:
        attrs = path.stat().st_file_attributes
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


# ── Cleanup ──────────────────────────────────────────────
def cleanup_windows():
    """Remove old sync scheduled tasks and startup scripts."""
    print("Cleaning up old sync infrastructure...")

    # Kill scheduled task
    for task_name in ("ClaudeCodeAutoSync", "ClaudeCodePeriodicSync"):
        try:
            subprocess.run(
                ["schtasks", "/delete", "/tn", task_name, "/f"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass
    print("  Scheduled tasks: cleared")

    # Remove startup script
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / \
              "Start Menu" / "Programs" / "Startup" / "ClaudeSync.cmd"
    if startup.exists():
        try:
            startup.unlink()
        except Exception:
            pass
    print("  Startup scripts: cleared")
    print()


# ── Manifest Sync ─────────────────────────────────────────
def setup_manifest_sync(claude_sessions, manifests_dir):
    """Junction ~/.claude/sessions/ -> .sessions-manifests/ for cross-machine sync.

    When manifests are shared via OneDrive, deleting a session on one machine
    removes the manifest everywhere. The orphan cleanup hook can then safely
    delete transcript .jsonl files knowing they are genuinely abandoned.
    """
    system = platform.system()

    # Already set up?
    if claude_sessions.exists():
        if is_junction(claude_sessions):
            resolved = claude_sessions.resolve()
            if resolved == manifests_dir.resolve():
                print(f"  [ OK ] Manifest sync already active")
                return
            else:
                print(f"  [WARN] sessions/ is a junction pointing elsewhere: {resolved}")
                return
        # Not a junction — migrate
        print(f"  Migrating existing manifests to OneDrive...")
        try:
            for mf in claude_sessions.glob("*.json"):
                shutil.copy2(mf, manifests_dir / mf.name)
        except Exception as e:
            print(f"  [WARN] Copy error: {e}")
        print(f"  Removing local sessions/ directory...")
        shutil.rmtree(claude_sessions, ignore_errors=True)

    # Create junction
    if system == "Windows":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J",
             str(claude_sessions), str(manifests_dir)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            print(f"  [WARN] Junction creation failed: {result.stderr.strip()}")
            print(f"  Manually: mklink /J {claude_sessions} {manifests_dir}")
        else:
            print(f"  [ OK ] Manifest sync: {claude_sessions} -> {manifests_dir}")
    else:
        try:
            claude_sessions.symlink_to(manifests_dir, target_is_directory=True)
            print(f"  [ OK ] Manifest sync: {claude_sessions} -> {manifests_dir}")
        except Exception as e:
            print(f"  [WARN] Symlink failed: {e}")
def create_link(hash_dir, sessions_path, workspace_root):
    """Replace hash_dir with a symlink/junction to sessions_path."""
    system = platform.system()

    # Backup
    backup_dir = hash_dir.with_name(hash_dir.name + ".backup")
    if backup_dir.exists():
        print(f"  Removing old backup: {backup_dir}")
        shutil.rmtree(backup_dir, ignore_errors=True)

    print(f"  Backing up: {hash_dir} -> {backup_dir.name}")
    try:
        hash_dir.rename(backup_dir)
    except OSError as e:
        print(f"  [WARN] Could not back up {hash_dir}: {e}")
        return

    # Create link
    print(f"  Creating link: {hash_dir} -> {sessions_path}")
    try:
        if system == "Windows":
            # mklink /J — junction, no admin required
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J",
                 str(hash_dir), str(sessions_path)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                raise OSError(result.stderr.strip())
        else:
            # macOS / Linux — symlink
            hash_dir.symlink_to(sessions_path, target_is_directory=True)

        print(f"  [ OK ] Link created")
    except Exception as e:
        print(f"  [FAIL] {e}")
        # Restore backup
        if backup_dir.exists():
            print(f"  Restoring backup...")
            try:
                backup_dir.rename(hash_dir)
            except Exception:
                pass


# ── Verify ────────────────────────────────────────────────
def verify(sessions_path, hash_dirs):
    """Check that each hash dir now mirrors .sessions/."""
    try:
        sessions_jsonl = set(f.name for f in sessions_path.glob("*.jsonl"))
    except Exception:
        return False, "Cannot read .sessions/"

    for hd in hash_dirs:
        if not hd.exists():
            return False, f"Missing: {hd}"
        try:
            hd_jsonl = set(f.name for f in hd.glob("*.jsonl"))
        except Exception:
            return False, f"Cannot read: {hd}"

        if sessions_jsonl != hd_jsonl:
            missing = sessions_jsonl - hd_jsonl
            extra = hd_jsonl - sessions_jsonl
            details = []
            if missing:
                details.append(f"missing {len(missing)} files")
            if extra:
                details.append(f"extra {len(extra)} files")
            return False, f"Mismatch in {hd.name}: {', '.join(details)}"

    return True, f"All {len(hash_dirs)} hash dir(s) match .sessions/ ({len(sessions_jsonl)} files)"


if __name__ == "__main__":
    main()
