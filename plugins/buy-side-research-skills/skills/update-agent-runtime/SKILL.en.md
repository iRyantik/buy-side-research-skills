---
name: update-agent-runtime
description: Update installed host runtimes from a packaged release payload and transactionally sync the current workspace.
---

# Update Agent Runtime

`update-agent-runtime` is the only user-facing update entrypoint. It must not perform manual `cp -r` updates, and it no longer recursively discovers deployable files from `init-workspace/assets` or `skills/*/scripts`. Host and workspace updates must come from a packaged release payload and its `runtime/managed-assets.json`.

> Terminology: CPR means the final `commit -> push -> release` closeout flow. It does not mean a local payload directory. This skill consumes a release payload.

## Source Of Truth

- Default source: a local release payload directory, for example `_dist/buy-side-research-skills/6.0.0-rc.1/`.
- Post-release compatibility source: latest GitHub release, but the downloaded/unpacked payload must still pass `runtime-manager verify-release` first.
- Release payload may only contain `.claude-plugin/`, `.codex-plugin/`, `skills/`, `runtime/`, `README.md`, manifest/hash/report files.
- Tests, fixtures, PDFs, DB files, temporary files, and `__pycache__` must not ship in release payload.

## Execution Contract

1. Resolve the release payload source and runtime version. If no source is explicitly provided, prefer the latest `_dist/buy-side-research-skills/<version>/` in the current dev repo.
2. Run `python _scripts/runtime-manager.py verify-release --source <release-payload>`; stop on failure.
3. Run `python _scripts/runtime-manager.py update-hosts --source <release-payload>`. By default this updates every installed host:
   - Claude Code cache version directory and `installed_plugins.json` pointer.
   - Codex version directory, flat `~/.codex/plugins/cache/buy-side-research-skills/skills/`, and plugin metadata.
   - `.agents/plugins/marketplace.json` local path.
4. In the current workspace, run:
   - `python _scripts/runtime-manager.py plan --runtime-root <release-payload>/runtime`
   - If plugin-owned conflicts exist, run `adopt` only for explicit targets. Never use a global force option.
   - `python _scripts/runtime-manager.py update --runtime-root <release-payload>/runtime`
   - `python _scripts/runtime-manager.py verify`
5. Run runtime dependency checks:
   - `python _scripts/financial-data.py check-deps`
   - `python _scripts/source-intake.py check-deps`
6. Print a host/cache/workspace/verification summary and explicitly tell the user to restart the current Codex/Claude session so skill discovery reloads the new version.

## File Safety

- The installed manifest defines managed workspace files.
- Delete only stale files recorded in the old installed manifest whose hash has not been user-modified.
- Preserve `.claude/mcp.json`, `.codex/config.toml`, `COVERAGE.md`, and unknown user scripts in `_scripts/` by default.
- `adopt` may only take over active plan conflicts by explicit `--target`; it must back up and hash each target before adoption.
- Source Intake, Financial Data, hooks, and providers run from `.research-runtime/packages/`; `_scripts/` only exposes stable CLIs and compatibility wrappers.

## Output Contract

After success or partial success, output:

```markdown
## Update Runtime Result

**Conclusion first**
Updated host caches from release payload `<version>` and synced the workspace runtime. Restart the current session before expecting skill discovery to load the new version.

## Hosts
| Host | Status | Version |
|---|---|---|
| Claude Code | updated / not installed / failed | 6.0.0-rc.1 |
| Codex | updated / not installed / failed | 6.0.0-rc.1 |
| .agents marketplace | updated / skipped / failed | 6.0.0-rc.1 |

## Workspace
- plan: clean / conflicts
- adopted: explicit targets only / none
- update: ok / conflicts preserved / failed
- verify: ok / failed

## Verification
- verify-release: ok / failed
- financial-data check-deps: ok / failed
- source-intake check-deps: ok / failed
- restart_required: yes
```

## Failure Handling

- Release payload verification failure: stop before updating host or workspace.
- Missing host: mark `not installed` and continue with other hosts.
- Workspace points at a plugin repo or plugin install/cache directory: stop workspace sync to avoid polluting dev repos or host caches.
- Conflicts remain after update: preserve user files and print target list; never globally overwrite.

Artifact policy:

- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`
