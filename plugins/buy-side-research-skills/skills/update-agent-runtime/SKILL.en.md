---
name: update-agent-runtime
description: Update the current host plugin runtime to the latest GitHub release and sync the current workspace scaffold.
---

# Update Agent Runtime

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

`update-agent-runtime` detects all installed hosts (Claude Code / Codex), updates each that is found, refreshes plugin caches and marketplace for every host, and syncs the current workspace to the latest runtime scaffold. One command, no manual host selection. It is an operations skill.

## Mental Model

Three things to keep in sync:

- the **host plugin runtime** (Claude Code / Codex)
- the **plugin cache and marketplace** for each host
- the **workspace-managed runtime assets** (hooks, adapters, settings, utility scripts, `references/`, `CLAUDE.md` / `AGENTS.md`)

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
   - **`.agents` marketplace**: update `~/.agents/plugins/marketplace.json` → set `path` to latest Codex cache dir
4. If current host: update via official CLI (`claude plugin update` / `codex plugin marketplace upgrade`)
5. Sync workspace runtime assets (see Workspace Sync below)
6. **Check for new system dependencies** in the updated version (compare `init-workspace/assets/` requirements). If new deps found → auto-install (winget/brew), fail → print manual command + **BLOCK**
7. **Ensure `.claude/mcp.json` has playwright key** (merge strategy, same as `/init-workspace` Step 4)
8. **Run `python _scripts/verify-runtime.py`** — 12 checks, all must pass. Any ❌ → auto-install → re-check → fail → **BLOCK**
9. **Print change summary**: what files were updated, what dependencies were added/removed, any breaking changes from release notes

## Workspace Sync

After updating hosts, sync the current workspace — no release zip download needed; pull directly from the latest cache's `init-workspace/assets/`:

### A. Hook infrastructure (`.claude/hooks/` — full tree)

Copy the **entire** `.claude/hooks/` directory from init-workspace assets to workspace. This includes:

- `hook_entry.py` — unified entry point
- `common.py` — shared utilities (block/warn, markdown parsing, Resources parsing)
- `fill_gaps.py` — financial-data gap-filling engine
- `_excel_bridge.py` — Excel formula bridge
- `hooks.registry.yaml` — hook rule registry
- `adapters/claude.py`, `adapters/codex.py` — host adapters
- `config/required_sections.yaml` — skill structure contract config
- `rules/` — all hook rules (source_contract, table_render_integrity, modeling/, provider/, viz/)

**Safety**: overwrite all `.py` files and `.yaml` configs. These are owned by the plugin — workspace-local edits are not supported.

### B. Host configs

- **`.claude/settings.json`** — hook configuration (PostToolUse / Stop triggers). Overwrite — this is plugin-owned and must match the current hook rule set.
- **`.claude/mcp.json`** — MCP server config. Copy only if workspace file is missing (user may have customized).
- **`.codex/hooks.json`** — Codex hook config. Overwrite — plugin-owned.
- **`.codex/mcp.example.json`** — Codex MCP example. Always sync (never customized directly).

### C. Utility scripts (`_scripts/`)

**C1 — Platform-owned** (from `init-workspace/assets/_scripts/`):
- `download-product-image.js` — Playwright image-download helper

**C2 — Skill workspace assets** (auto-discovered; formal spec in `meta-skill` Skill Directory Spec):

```
for each skill_dir in skills/*/:
    if .platform exists → skip (platform skill, deployed by C1/Class A)

    dst = _scripts/<skill-name>/

    if scripts/ exists:
        cp -r scripts/* → dst/

    if assets/ exists:
        for each file in assets/ (recursive):
            if file is under assets/templates/:
                cp → dst/  (copy if missing)
            else:
                cp → dst/  (overwrite)

    # references/ and examples/ are NOT deployed.
```

> Adding a file to a skill's `scripts/` or `assets/` → automatically deployed. Zero changes to this skill.

**Safety**: Overwrite all C1 and C2 files (canonical plugin versions). User-added scripts in `_scripts/` that are not in the source lists are left untouched.

### D. References

- `references/policy/` — research-policy-baseline.md, statement-line-items.md
- `references/kpi-drivers/` — 7 business-model templates

Overwrite all reference files. These are the canonical versions from the plugin.

### E. Root documents

- **`CLAUDE.md`**: patch managed sections only. Do not overwrite the entire file — the user's workspace constitution lives here. Managed sections are the RTK block and the plugin-loaded marker.
- **`AGENTS.md`**: same conservative patch approach.
- **`edge-radar.md`**: overwrite (plugin-owned reference doc).
- **`COVERAGE.md`**: if missing, copy from `coverage.md.template`. If present, skip — user has customized.

### F. Codex cache

Refresh `~/.codex/plugins/cache/buy-side-research-skills/skills/` from the latest marketplace plugin skills.

## File Safety

- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md` — patch managed sections only.
- Do not overwrite `_scripts/` files that don't exist in the source assets.
- Do not overwrite `.claude/mcp.json` if already present (user customization).
- Do not overwrite `.codex/config.toml` (user customization).
- Do not overwrite `COVERAGE.md` if already present.
- Do not run workspace init inside the plugin dev repo or plugin install directories.

## Output Contract

After success:

```markdown
## Update Runtime Result

**Conclusion-First**
Updated X host(s) + workspace runtime assets.

## Hosts
| Host | Status | Version |
|---|---|---|
| Claude Code | updated / not installed | vX.X.X |
| Codex | updated / not installed | vX.X.X |

## Cache
- marketplace: refreshed
- claude cache: refreshed / not found
- codex cache: refreshed / not found
- .agents marketplace: updated / skipped

## Workspace
- hooks: synced (full .claude/hooks/ tree)
- settings: synced (.claude/settings.json)
- scripts: synced (_scripts/)
- references/: synced (policy + kpi-drivers)
- .codex/: synced (hooks.json + mcp.example.json)
- claude_md: updated / skipped
- mcp.json: playwright key ensured (merge)

## Verification
- verify-runtime.py: 12/12 ✅ / ❌ (N failures)
- new dependencies: none / installed: X, Y, Z
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
- Did not overwrite user-customized `.claude/mcp.json`, `.codex/config.toml`, or `COVERAGE.md`.
