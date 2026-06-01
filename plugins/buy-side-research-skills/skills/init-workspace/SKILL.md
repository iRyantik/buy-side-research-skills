---
name: init-workspace
description: Initialize or repair a buy-side research workspace root scaffold and helper scripts.
---

# Init Workspace

`init-workspace` turns a normal folder into a usable buy-side research workspace. It creates or repairs the root scaffold, writes workspace `CLAUDE.md`, `AGENTS.md`, `.gitignore`, and `edge-radar.md`, copies ingest / financial-data helper scripts into `_scripts/`, and installs project-local Claude / Codex hook config so both hosts can load the same binary runtime guardrails.
It does not update the installed Claude Code or Codex plugin runtime itself; host/plugin upgrades and latest-release workspace sync belong to `update-agent-runtime`.

macOS support assumes PowerShell 7 (`pwsh`) is installed. Workspace hook adapters are rendered through a cross-platform launcher; `.ps1` helpers are not promised to run in pure zsh/bash without `pwsh`.

It is an operations skill, not a research skill. It does not research companies, ingest files, install dependencies, run `git init`, create topic artifacts, or create topic-level `_raw/`, `_cache/`, or `_models/` directories.

`init-workspace` is also the first-stop environment guide for the most common runtime requirements. It should tell users where to configure shared items such as `pwsh`, `EDGAR_IDENTITY`, `DART_API_KEY`, `EDINET_API_KEY`, `FINMIND_TOKEN`, `EDGAR_LOCAL_DATA_DIR`, optional `VLM_*`, and optional `HF_ENDPOINT`. It does not replace skill-local dependency or honest-fail documentation: `financial-data` remains the detailed source of truth for financial-data environment setup, while `ingest` and `reddit-sentiment` keep their own skill-local bootstrap instructions.

## Mental Model

The invariant is separation of concerns:

- `init-workspace` creates the root workspace shell.
- `new-session` creates or locates a topic root with `index.md` and `_inbox/`.
- `ingest` creates `_raw/<category>/` and `_cache/` only when material is converted.
- `financial-data`, `driver-map`, and modeling skills create their own cache/model folders when they run.

The default behavior must be conservative, idempotent, and repeatable. Existing root workspace documents are skipped, not overwritten; managed hook assets and host adapters are synced on repair.

## Responsibilities

Responsible for:

- Creating root `_inbox/`, `_scripts/`, and `topics/`.
- Writing missing root `CLAUDE.md`, `AGENTS.md`, `.gitignore`, and `edge-radar.md`.
- Copying a unified environment setup template into `_scripts/init-assets/` so users can discover common workspace, filing, and optional VLM environment variables from one place.
- Copying init assets, ingest scripts, ingest requirements, and ingest dependency bootstrap into `_scripts/`.
- Copying financial-data scripts, providers, requirements, and dependency bootstrap into `_scripts/financial-data/`.
- Copying shared workspace hook scripts into `.claude/hooks/` and host adapter config into `.claude/settings.json` and `.codex/hooks.json`.
- Repairing managed hook assets and hook adapters when the workspace already exists.

Not responsible for:

- Ingesting PDF / Excel / PPTX / DOCX materials.
- Installing Docling, EdgarTools, Tesseract, MarkItDown, or Python packages.
- Validating live credentials against provider APIs or silently persisting user secrets.
- Creating dated topic research artifacts.
- Creating topic roots; use `new-session`.
- Creating topic-level `_raw/`, `_cache/`, or `_models/`.
- Running `git init`.
- Initializing inside the plugin dev repo or plugin install directory.

## Trigger And Input

Trigger phrases:

- "init research workspace"
- "初始化研究工作区"
- "创建研究文件夹"
- "setup research"
- "bootstrap workspace"
- "补齐 research workspace"

Required input:

- `WorkspacePath`: an explicit user-owned research workspace path.
- The target path must not be the plugin repo, a plugin install directory, or any folder containing plugin markers such as `.claude-plugin/`, `.codex-plugin/`, or `skills/`.
- Existing `CLAUDE.md`, `AGENTS.md`, `.gitignore`, and root `edge-radar.md` must be skipped, not overwritten.
- Managed hook assets under `.claude/`, `.codex/`, and `_scripts/init-assets/` are treated as plugin-owned runtime files and may be updated during repair.

## Modes

### New Workspace Scaffold

When the target path does not exist or is empty, create the root scaffold, root templates, and `_scripts/` helper files.

### Repair Existing Workspace

When the target path already has content, only add missing root scaffold directories and missing core files. Do not repair topic-level `_raw/`, `_cache/`, or `_models/`; those are owned by downstream skills.

### Dry Explanation

When the user only asks what init will do or what the folder will look like, do not run the helper script. Explain the root scaffold and boundaries.

## Tool Resources

Use the helper script when mutating files:

- `skills/init-workspace/scripts/init-research-workspace.ps1`

Runtime assets copied by the helper:

- `skills/init-workspace/assets/CLAUDE.md.template`
- `skills/init-workspace/assets/AGENTS.md.template`
- `skills/init-workspace/assets/gitignore.template`
- `skills/init-workspace/assets/edge-radar.md`
- `skills/init-workspace/assets/env-setup.ps1.template`
- `skills/init-workspace/assets/.claude/settings.json`
- `skills/init-workspace/assets/.claude/hooks/`
- `skills/init-workspace/assets/.claude/hooks/hooks.registry.yaml`
- `skills/init-workspace/assets/.claude/hooks/run-hook.cmd`
- `skills/init-workspace/assets/.claude/hooks/run-hook.sh`
- `skills/init-workspace/assets/.codex/hooks.json`
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.ps1`
- `skills/ingest/scripts/bootstrap-ingest-deps.sh`
- `skills/ingest/assets/requirements-ingest.txt`
- `skills/financial-data/scripts/financial_data.py`
- `skills/financial-data/scripts/bootstrap-financial-data-deps.ps1`
- `skills/financial-data/scripts/providers/*.py`
- `skills/financial-data/assets/requirements-financial-data.txt`

Prefer the helper script over hand-written copy logic.

## Environment Entry Point

`init-workspace` should be the first place a user looks for shared runtime setup. The copied `_scripts/init-assets/env-setup.ps1.template` is the canonical entry point for common workspace-level environment guidance:

- Runtime / platform:
  - `pwsh` on macOS
- Filing / financial-data core:
  - `EDGAR_IDENTITY`
  - `DART_API_KEY`
  - `EDINET_API_KEY`
  - `FINMIND_TOKEN` (optional)
  - `EDGAR_LOCAL_DATA_DIR`
- Optional ingestion / figure description:
  - `VLM_API_URL`
  - `VLM_API_KEY`
  - `VLM_MODEL`
- Optional network mirror:
  - `HF_ENDPOINT`

This entry point is a navigation layer, not a replacement for skill-local detail:

- `financial-data` still owns provider-by-market credential and dependency detail
- `ingest` still owns converter dependency detail and SEC filing ingest caveats
- `reddit-sentiment` still owns its own bootstrap and dependency guidance

## File Safety

- Idempotent: reruns only add missing items.
- Never overwrite existing `CLAUDE.md`, `AGENTS.md`, `.gitignore`, or `edge-radar.md`.
- Never delete or move user files.
- Never initialize inside a plugin repo, plugin install directory, or any directory containing plugin manifests.
- Never treat `_raw/`, `_cache/`, `_models/`, or `_inbox/` as publishable research outputs.

## Output Contract

After success or repair:

```markdown
## Init Result

**结论先行**
已初始化 / 已补齐 research workspace：[path]

## Created
- [...]

## Skipped
- [...]

## Workspace Shape
[root scaffold tree]

## Environment Next Steps
- shared env template: `_scripts/init-assets/env-setup.ps1.template`
- workspace hooks on macOS require `pwsh`
- financial-data check:
  - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly`
  - macOS: `pwsh -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly`
- ingest check:
  - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly`
  - macOS: `pwsh -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly` or `_scripts/bootstrap-ingest-deps.sh --check-only`
- optional figure-description env:
  - `VLM_API_URL`
  - `VLM_API_KEY`
  - `VLM_MODEL`
```

When blocked:

```markdown
## Init Blocked

**结论先行**
不能在这个路径初始化 research workspace。
- path: [...]
- reason: [...]
- suggested_path: [...]
```

## Failure Handling

- Missing path: ask for an explicit `WorkspacePath`; do not guess.
- Plugin repo markers found: refuse and ask for a user-owned research workspace.
- Permission failure: name the exact path that failed; do not pretend success.
- Missing helper script: report that the plugin package is incomplete and ask the user to reinstall or repair the release package.

## Workflow Links

| Scenario | Handling |
|---|---|
| User just installed the plugin and does not know where to start | Use `init-workspace` to create the root workspace scaffold |
| Existing workspace is missing root scaffold files | Use `init-workspace` repair |
| User wants to start a company / industry / theme / pair topic | Hand off to `new-session` |
| User drops materials into a topic `_inbox/` | Hand off to `ingest` |
| User needs structured financial data | Hand off to `financial-data` |
| User wants to know which shared environment variables matter first | Use `init-workspace` as the unified entry point, then hand off to the specific skill for exact runtime detail |
| User needs to promote company workbench files from an industry/theme topic | Hand off to `promote-company` |
| User wants to merge whole topic directories | Hand off to `integrate` |
| User lacks ingest dependencies | Suggest Windows `powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly`; suggest macOS `pwsh -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly` or `_scripts/bootstrap-ingest-deps.sh --check-only`; run install variants only after explicit opt-in |
| User lacks financial-data dependencies | Suggest Windows `powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly`; suggest macOS `pwsh -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly`; run `-Yes` only after explicit opt-in |

Artifact policy:

- `save_policy`: `workspace_scaffold`
- `default_artifact`: `workspace scaffold`
- `canonical_location`: user-provided research workspace

## Safety Self-Check

- Did not initialize inside the plugin repo.
- Did not overwrite existing root files.
- Did not run `git init`.
- Did not ingest raw materials.
- Did not fetch financial data.
- Did not install dependencies.
- Did not create topic artifacts.
- Did not create topic-level `_raw/`, `_cache/`, or `_models/`.
- Did not recreate v2 state folders such as `coverage/`, `portfolio/`, or `pairs/`.
