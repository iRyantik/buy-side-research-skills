#!/usr/bin/env python3
"""delete-session.py — Permanently delete a Claude Code session.

Lists all sessions with titles, or deletes by sessionId.
Shared via OneDrive — both machines see the same deleted.json.

Usage:
    python delete-session.py                     # list all sessions
    python delete-session.py --delete <id>        # delete by sessionId
    python delete-session.py --delete <prefix>    # delete by partial ID match
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def get_title(jsonl_path, max_lines=50):
    """Extract first user message from a .jsonl transcript."""
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


def list_sessions(sessions_dir):
    """Display all sessions with ID and title."""
    jsonl_files = sorted(sessions_dir.glob("*.jsonl"),
                         key=lambda f: f.stat().st_mtime, reverse=True)
    print(f"Sessions: {len(jsonl_files)}\n")

    for f in jsonl_files:
        sid = f.stem
        title = get_title(f)
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        size = f.stat().st_size / 1024
        print(f"  {sid[:8]}  {mtime}  {size:5.0f}KB  {title}")


def delete_session(sessions_dir, match):
    """Add session to deleted.json by sessionId or partial ID."""
    # Find matching sessions
    matches = []
    match_lower = match.lower()
    for f in sessions_dir.glob("*.jsonl"):
        if match_lower in f.stem.lower():
            matches.append(f.stem)

    if not matches:
        print(f"No session matching '{match}'")
        sys.exit(1)

    if len(matches) > 1:
        print(f"Multiple matches ({len(matches)}):")
        for m in matches:
            print(f"  {m}")
        print("\nUse full ID to select one.")
        sys.exit(1)

    sid = matches[0]
    title = get_title(sessions_dir / f"{sid}.jsonl")

    # Read existing deleted.json
    deleted_file = sessions_dir / "deleted.json"
    if deleted_file.is_file():
        try:
            data = json.loads(deleted_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"deleted": []}
    else:
        data = {"deleted": []}

    # Check duplicate
    for item in data["deleted"]:
        if item["sessionId"] == sid:
            print(f"Already queued: {sid}")
            return

    data["deleted"].append({
        "sessionId": sid,
        "deletedAt": datetime.now(timezone.utc).isoformat(),
        "title": title[:80],
    })

    deleted_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Queued for deletion: {sid[:32]}...")
    print(f"Title: {title[:100]}")
    print(f"\nTranscript will be deleted on next CC exit (Stop hook).")


def main():
    parser = argparse.ArgumentParser(description="Permanently delete CC sessions")
    parser.add_argument("--delete", "-d", help="Session ID or prefix to delete")
    args = parser.parse_args()

    sessions_dir = find_sessions_dir()
    if sessions_dir is None:
        print("Cannot find .sessions/ directory.")
        sys.exit(1)

    if args.delete:
        delete_session(sessions_dir, args.delete)
    else:
        list_sessions(sessions_dir)


if __name__ == "__main__":
    main()
