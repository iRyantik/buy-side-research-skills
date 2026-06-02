---
name: update-agent-runtime
description: Update the current host plugin runtime to the latest GitHub release and sync the current workspace scaffold.
---

# Update Agent Runtime

`update-agent-runtime` detects all installed hosts (Claude Code / Codex), updates each that is found, refreshes plugin caches and marketplace for every host, and syncs the current workspace to the latest runtime scaffold. One command, no manual host selection. It is an operations skill.

## Mental Model

Three things to keep in sync:

- the **host plugin runtime** (Claude Code / Codex)
- the **plugin cache and marketplace** for each host
- the **workspace-managed runtime assets** (hooks, adapters, `CLAUDE.md` / `AGENTS.md`)

`/update-agent-runtime` auto-detects which hosts are installed and updates everything it finds — no manual host selection needed. If only Claude Code is installed, only that gets updated. If both are installed, both get updated.

## Responsibilities

Responsible for:

- Auto-detecting all installed hosts (Claude Code / Codex).
- Updating every detected host's plugin to the latest GitHub release.
- Refreshing plugin cache and marketplace for every detected host.
- Syncing the current workspace runtime assets through the latest packaged `init-workspace` helper.
- Patching managed sections of workspace `CLAUDE.md` and `AGENTS.md` conservatively.

Not responsible for:

- Rewriting the whole workspace constitution from scratch.
- Creating dated topic artifacts.
- Editing research conclusions or topic files.
- Replacing `init-workspace`; it reuses `init-workspace`.

## Trigger And Input

Trigger phrases:

- "update-agent-runtime"
- "update plugin runtime"
- "upgrade buy-side plugin"
- "更新插件到最新版本"
- "更新当前宿主插件"
- "修复 workspace 运行时"

Inputs:

| Input | Purpose |
|---|---|
| `host` | Optional. `auto` by default. Allowed explicit overrides: `claude`, `codex`. |
| `workspace` | Optional. Defaults to the current workspace root. |

## Host Detection

Auto-detect all installed hosts:

1. Check `~/.claude/plugins/cache/buy-side-research-skills/` → Claude Code installed
2. Check `~/.codex/plugins/cache/buy-side-research-skills/` → Codex installed
3. Update every detected host. No manual selection needed.

## Update Path

For each detected host:

1. Update marketplace plugin to latest release
2. Create/populate plugin cache with latest version directory (copy marketplace skills)
3. **Update host runtime pointer to latest cache version**:
   - **Claude Code**: update `~/.claude/plugins/installed_plugins.json` → set `version` and `installPath` to latest cache dir
   - **Codex**: sync latest skills to `~/.codex/plugins/cache/buy-side-research-skills/skills/`
4. If current host: update via official CLI (`claude plugin update` / `codex plugin marketplace upgrade`)
5. Sync workspace runtime assets (hooks, `references/`, `CLAUDE.md`, `AGENTS.md`)

## Workspace Sync

After updating hosts, sync the current workspace — no release zip download needed; pull directly from marketplace plugin:

- copy `references/` to workspace root (policy + kpi-drivers)
- sync `.claude/hooks/` (hook_entry.py + rules/) and `.codex/hooks.json`
- patch managed sections of root `CLAUDE.md` and `AGENTS.md`
- refresh Codex cache: sync latest marketplace skills to `~/.codex/plugins/cache/buy-side-research-skills/skills/`

## File Safety

- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md`.
- Do not run workspace init inside the plugin dev repo or plugin install directories.

## Output Contract

After success:

```markdown
## Update Runtime Result

**结论先行**
已更新 X 个宿主 + workspace 运行时资产。

## Hosts
| Host | Status | Version |
|---|---|---|
| Claude Code | updated / not installed | vX.X.X |
| Codex | updated / not installed | vX.X.X |

## Cache
- marketplace: refreshed
- claude cache: refreshed / not found
- codex cache: refreshed / not found

## Workspace
- hooks: synced
- references/policy/: synced
- claude_md: updated / skipped
```

## Failure Handling

- No hosts detected: report and suggest manual install from GitHub.
- Official host CLI missing or unusable: report exact discovery failure for that host, continue with others.
- Workspace path points to a plugin repo or plugin install directory: stop and refuse repair there.

## Workflow Links

| Scenario | Handling |
|---|---|
| User just wants to scaffold a new workspace | Use `init-workspace` |
| User wants to repair hooks/settings only | Use `update-agent-runtime` |
| User wants to upgrade the current host plugin and sync templates | Use `update-agent-runtime` |
| User wants to author or review plugin governance | Use `meta-skill` |

Artifact policy:

- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`

## Safety Self-Check

- Updated only the selected host.
- Used official host plugin CLI commands.
- Used latest release zip for workspace truth.
- Reused packaged `init-workspace` scaffold logic.
- Patched managed workspace doc sections conservatively.
- Did not create research artifacts.
