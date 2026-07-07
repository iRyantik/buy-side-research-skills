---
name: session-sync-setup
description: Set up automatic Claude Code session sync across machines via OneDrive
---

# Session Sync Setup

Set up automatic session syncing so all machines share the same Claude Code
conversation history without any manual steps. Works on Windows and macOS.

## What it does

1. Detects your OS, OneDrive path, and Claude Code project hash directories
2. Replaces each hash directory with a symlink/junction pointing to `.sessions/`
3. Cleans up old sync scheduled tasks and startup scripts (Windows)
4. Verifies everything is connected

After setup, Claude Code reads/writes sessions directly to OneDrive.
Switching machines is instant — no sync scripts, no manual steps.

## How to use

```
/session-sync-setup
```

Or run manually:

```
python3 .scripts/sync/setup.py
```

Add `--dry-run` to preview without making changes.

## What happens after

- **Daily use**: Nothing. Just open Claude Code. Sessions are already there.
- **Switch machines**: Wait for OneDrive to finish syncing (icon stops spinning), then open Claude Code.
- **Conflict copies** (rare, only if two machines have CC open simultaneously): Automatically merged and cleaned on Stop.

## Files involved

| File | Purpose |
|------|---------|
| `.scripts/sync/setup.py` | One-click cross-platform setup |
| `.claude/hooks/rules/session_conflict_clean.py` | Auto-clean OneDrive conflict copies on Stop |
| `.claude/hooks/hook_entry.py` | Registers the cleanup hook |
