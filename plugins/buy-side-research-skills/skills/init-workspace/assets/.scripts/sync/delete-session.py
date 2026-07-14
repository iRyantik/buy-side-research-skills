#!/usr/bin/env python3
"""delete-session.py — Permanently delete Claude Code sessions.

Interactive mode (default): numbered list, select by number.
Also supports --delete <id> for direct deletion.

Shared via OneDrive — both machines see the same deleted.json.
Transcript files deleted on next CC exit by Stop hook.

Usage:
    python delete-session.py              # interactive: pick from list
    python delete-session.py --delete <id> # direct delete by sessionId/prefix
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ──

def find_sessions_dir():
    projects = Path.home() / ".claude" / "projects"
    if not projects.is_dir():
        return None
    for hd in projects.iterdir():
        if not hd.is_dir():
            continue
        if hd.is_symlink():
            try:
                resolved = hd.resolve()
            except Exception:
                continue
        else:
            resolved = hd
        if (resolved / "tool-results").is_dir() or list(resolved.glob("*.jsonl")):
            return resolved
    return None


def get_title(jsonl_path, max_lines=80):
    try:
        with open(jsonl_path, encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if i > max_lines:
                    return ""
                if not line.strip():
                    continue
                try:
                    d = json.loads(line.strip())
                    msg = d.get("message", {})
                    if isinstance(msg, dict):
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user" and isinstance(content, str) and len(content) > 5:
                            return content[:120].replace("\n", " ")
                        if role == "user" and isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("text"):
                                    return c["text"][:120].replace("\n", " ")
                except (json.JSONDecodeError, KeyError):
                    continue
    except (OSError, UnicodeDecodeError):
        pass
    return ""


def fmt_age(mtime):
    days = (datetime.now().timestamp() - mtime) / 86400
    if days < 1:
        return f"{days*24:.0f}h ago"
    elif days < 30:
        return f"{days:.0f}d ago"
    else:
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def fmt_size(size_bytes):
    kb = size_bytes / 1024
    if kb > 1024:
        return f"{kb/1024:.0f}MB"
    return f"{kb:.0f}KB"


# ── list ──

def list_sessions(sessions_dir):
    jsonl_files = sorted(sessions_dir.glob("*.jsonl"),
                         key=lambda f: f.stat().st_mtime, reverse=True)
    if not jsonl_files:
        print("No sessions found.")
        return []

    print(f"\n{'#':>3}  {'ID':<12}  {'Age':<10}  {'Size':>6}  Title")
    print(f"{'':->3}  {'':-<12}  {'':-<10}  {'':->6}  {'':-<60}")
    for n, f in enumerate(jsonl_files, 1):
        title = get_title(f)
        age = fmt_age(f.stat().st_mtime)
        size = fmt_size(f.stat().st_size)
        print(f"{n:>3}  {f.stem[:11]:<12}  {age:<10}  {size:>6}  {title}")

    print()
    return jsonl_files


# ── delete ──

def queue_deletion(sessions_dir, sid, title=""):
    deleted_file = sessions_dir / "deleted.json"
    if deleted_file.is_file():
        try:
            data = json.loads(deleted_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"deleted": []}
    else:
        data = {"deleted": []}

    for item in data["deleted"]:
        if item["sessionId"] == sid:
            print(f"  Already queued: {sid[:16]}...")
            return

    data["deleted"].append({
        "sessionId": sid,
        "deletedAt": datetime.now(timezone.utc).isoformat(),
        "title": title[:80],
    })

    deleted_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Queued: {title[:80] if title else sid[:16]}")
    print(f"  Transcript deleted on next CC exit.")


# ── main ──

def main():
    parser = argparse.ArgumentParser(description="Permanently delete CC sessions")
    parser.add_argument("--delete", "-d", help="Session ID or prefix to delete")
    args = parser.parse_args()

    sessions_dir = find_sessions_dir()
    if sessions_dir is None:
        print("Cannot find .sessions/ directory.")
        sys.exit(1)

    # Direct delete mode
    if args.delete:
        matches = [f.stem for f in sessions_dir.glob("*.jsonl")
                   if args.delete.lower() in f.stem.lower()]
        if not matches:
            print(f"No session matching '{args.delete}'")
            sys.exit(1)
        if len(matches) > 1:
            print(f"Multiple matches ({len(matches)}):")
            for m in matches:
                print(f"  {m}")
            print("\nUse full ID or unique prefix.")
            sys.exit(1)
        sid = matches[0]
        title = get_title(sessions_dir / f"{sid}.jsonl")
        queue_deletion(sessions_dir, sid, title)
        return

    # Interactive mode — list all, select by number
    files = list_sessions(sessions_dir)
    if not files:
        return

    print("Enter numbers to delete (space-separated), or 'q' to quit.")
    print("Example: 1 3 5-7")
    try:
        raw = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if raw.lower() == 'q':
        return

    if not raw:
        print("No selection.")
        return

    # Parse: "1 3 5-7 10" → {0, 2, 4, 5, 6, 9}
    selected = set()
    for part in raw.split():
        if '-' in part:
            try:
                a, b = part.split('-', 1)
                for n in range(int(a), int(b) + 1):
                    selected.add(n - 1)
            except ValueError:
                print(f"  Invalid range: {part}")
                return
        else:
            try:
                selected.add(int(part) - 1)
            except ValueError:
                print(f"  Invalid number: {part}")
                return

    for n in sorted(selected):
        if n < 0 or n >= len(files):
            print(f"  Out of range: {n + 1}")
            return

    if not selected:
        return

    print(f"\nDeleting {len(selected)} session(s):")
    for n in sorted(selected):
        f = files[n]
        title = get_title(f)
        queue_deletion(sessions_dir, f.stem, title)

    print(f"\nDone. Transcripts deleted on next CC exit.")


if __name__ == "__main__":
    main()
