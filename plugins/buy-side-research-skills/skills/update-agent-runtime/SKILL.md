---
name: update-agent-runtime
description: Update the current host plugin runtime to the latest GitHub release and sync the current workspace scaffold.
---

# Update Agent Runtime

`update-agent-runtime` updates the buy-side plugin in the **current host** and then syncs the **current workspace** to the latest runtime scaffold. It is an operations skill. It does not write research artifacts, and it does not update both Claude Code and Codex by default.

## Mental Model

There are two different things to update:

- the **host plugin runtime** that Claude Code or Codex loads
- the **workspace-managed runtime assets** such as hooks, host adapters, and managed `CLAUDE.md` / `AGENTS.md` sections

This skill updates the current host first, then repairs the workspace using the **latest GitHub release zip** as the source of truth. It does not trust whatever older plugin version is currently installed to be the correct template source.

## Responsibilities

Responsible for:

- Detecting whether the current execution context is Claude Code or Codex.
- Updating only that host by default.
- Switching Claude installs to the GitHub `buy-side-research-skills` marketplace channel when needed.
- Refreshing Codex marketplace snapshots and reinstalling the plugin from the official marketplace snapshot.
- Repairing current workspace runtime assets through the latest packaged `init-workspace` helper.
- Patching managed sections of workspace `CLAUDE.md` and `AGENTS.md` conservatively.

Not responsible for:

- Updating both hosts by default.
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

## Host Selection

Default is `host=auto`.

Resolution order:

1. Explicit `host=claude` or `host=codex`
2. Current script install path under `.claude/plugins/...` or `.codex/plugins/cache/...`
3. Runtime environment such as `CODEX_HOME`, `CODEX_THREAD_ID`, or Claude runtime env
4. If still ambiguous, stop and ask for an explicit host

When `host=auto`, update only the current host. Do not scan and mutate the other host.

## Update Path By Host

### Claude Code

Use the official `claude plugin` CLI only:

- ensure marketplace `buy-side-research-skills`
- install or update `buy-side-research-skills@buy-side-research-skills`
- if the current install is `buy-side-research-skills@local-desktop-app-uploads`, move it to the GitHub marketplace channel
- verify `.claude/plugins/installed_plugins.json` and enabled plugin state

### Codex

Use the official Codex plugin CLI only:

- ensure marketplace `buy-side-research-skills`
- `plugin marketplace upgrade buy-side-research-skills`
- `plugin add buy-side-research-skills@buy-side-research-skills`
- verify `.codex/config.toml` and the latest cache directory

Codex does not have a `plugin update` subcommand. The official update path is marketplace refresh plus plugin add.

## Workspace Sync

Workspace sync must use the latest release zip as the source of truth.

The script must:

- refresh the local plugin cache (create latest version directory and copy skills from marketplace)

- download the latest release zip
- call packaged `skills/init-workspace/scripts/init-research-workspace.ps1`
- patch managed sections of root `CLAUDE.md`
- patch the managed body of root `AGENTS.md`

Managed docs are patched conservatively. They must not be overwritten wholesale.

On macOS, workspace repair and runtime `.ps1` helpers require PowerShell 7 (`pwsh`). This skill does not promise a pure shell-only repair path.

## Tool Resources

Use the helper script when mutating files:

- `skills/update-agent-runtime/scripts/update_agent_runtime.py`

The helper script is responsible for host detection, release download, host update, workspace repair, managed doc patching, and local cache version refresh.

## File Safety

- Do not update both hosts by default.
- Do not write directly into guessed cache paths without first detecting the current host.
- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md`.
- Do not use an old installed plugin copy as the workspace template source.
- Do not run workspace init inside the plugin dev repo or plugin install directories.

## Output Contract

After success:

```markdown
## Update Runtime Result

**结论先行**
已更新当前宿主插件并同步当前 workspace 运行时资产。

## Host
- host: [...]
- previous_version: [...]
- current_version: [...]

## Workspace
- workspace: [...]
- scaffold_repaired: yes/no
- claude_md: updated / manual_merge_required / skipped
- agents_md: updated / manual_merge_required / skipped

## Notes
- [...]
```

When blocked:

```markdown
## Update Runtime Blocked

**结论先行**
未执行更新。

- host: [...]
- reason: [...]
- action_required: [...]
```

## Failure Handling

- Host cannot be detected: require explicit `host`.
- Latest release zip not found: stop and report the release lookup failure.
- Official host CLI missing or unusable: report exact discovery failure.
- Workspace doc anchors missing: continue other work and mark `manual_merge_required`.
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
