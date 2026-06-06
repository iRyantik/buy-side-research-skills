---
name: init-workspace
description: Initialize or repair a research workspace using the manifest-managed runtime payload.
---

# Init Workspace

`init-workspace` is an operations skill. `runtime/managed-assets.json` in the plugin release is the only deployment list. Never scan or recursively copy `skills/*/scripts` or `skills/*/assets`.

## Execution Contract

1. Validate that the target is a user research workspace, not a plugin repo, cache, or install directory.
2. Run `python _scripts/runtime-manager.py init --workspace <path>`; if the public CLI is not installed yet, invoke the same CLI directly from the current plugin release `runtime/`.
3. Show the plan first. Stop on conflicts and never overwrite user modifications.
4. Apply through `stage → validate → backup → apply → verify → rollback`.
5. Run `python _scripts/runtime-manager.py verify --workspace <path>`.
6. Provider-secret setup is optional. Never overwrite existing `.env`, `.claude/mcp.json`, `.codex/config.toml`, or `COVERAGE.md`.

## Runtime Surface

- `_scripts/source-intake.py`
- `_scripts/financial-data.py`
- `_scripts/runtime-manager.py`
- `.research-runtime/packages/`
- `.research-runtime/installed-manifest.json`
- `.claude/hooks/hook_entry.py`

Legacy `_scripts/ingest.py`, `_scripts/shared/to-markdown.py`, and `_scripts/financial-data/financial_data.py` are one-version compatibility wrappers only.

## Safety

- Deploy only files explicitly listed in the manifest.
- Tests, fixtures, PDFs, DBs, temporary files, and `__pycache__` never enter the payload.
- Delete a stale file only when the installed manifest recorded it and its hash is unchanged.
- Preserve unknown files and user scripts.
- `verify` is read-only and does not install dependencies or modify the system.
