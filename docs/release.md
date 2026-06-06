# Release

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

Current release version: `6.0.0-rc.2`.

## Source And Runtime Shape

The source repo is a wrapper. The canonical plugin payload is:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/
  .claude-plugin/
  .codex-plugin/
  skills/
  runtime/
```

Release zip files stay flat for installation:

```text
.claude-plugin/
.codex-plugin/
skills/
runtime/
README.md
release-manifest.json
payload-pollution-report.json
hashes.sha256
```

`runtime/managed-assets.json` is the only workspace deployment manifest. Do not rebuild recursive deployment from `init-workspace/assets` or `skills/*/scripts`.

## Release Package Contents

Release zip includes only runtime/install materials copied from the canonical payload plus root README:

- `plugins/buy-side-research-skills/.claude-plugin/` -> `.claude-plugin/`
- `plugins/buy-side-research-skills/.codex-plugin/` -> `.codex-plugin/`
- `plugins/buy-side-research-skills/skills/` -> `skills/`
- `plugins/buy-side-research-skills/runtime/` -> `runtime/`
- `README.md`

Release zip must not include source-repo maintenance files:

- root `CLAUDE.md` / `AGENTS.md`
- `docs/`
- `examples/`
- `.git/`
- `.claude/`
- root marketplace wrapper files
- source repo `plugins/` wrapper directory
- test fixtures, PDFs, DBs, temp files, or `__pycache__`

The release payload must include runtime governance files:

```text
runtime/managed-assets.json
runtime/buy_side_research_runtime/
runtime/workspace_payload/_scripts/source-intake.py
runtime/workspace_payload/_scripts/financial-data.py
runtime/workspace_payload/_scripts/runtime-manager.py
runtime/workspace_payload/.claude/hooks/
runtime/workspace_payload/.claude/settings.json
runtime/workspace_payload/.codex/hooks.json
runtime/workspace_payload/references/policy/
runtime/workspace_payload/references/kpi-drivers/
```

`ingest` is no longer an active skill. Source Intake is runtime infrastructure. `actuals-resolved.json` is a generated read-only compatibility view; canonical financial facts live in `facts-store.json`.

## Tooling Policy

Root `scripts/` has been removed from this source layout. Do not restore stale root validators.

Release payload creation is handled by:

```powershell
python plugins/buy-side-research-skills/runtime/workspace_payload/_scripts/runtime-manager.py build-release --plugin-root plugins/buy-side-research-skills --version X.X.X
python plugins/buy-side-research-skills/runtime/workspace_payload/_scripts/runtime-manager.py verify-release --source plugins/buy-side-research-skills/_dist/buy-side-research-skills/X.X.X
```

`build-release` produces:

```text
plugins/buy-side-research-skills/_dist/buy-side-research-skills/X.X.X/
plugins/buy-side-research-skills/_dist/buy-side-research-skills/X.X.X.zip
```

Before publishing a marketplace/plugin manifest change, confirm these JSON files parse without a UTF-8 BOM and start with `{`:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/.codex-plugin/plugin.json
plugins/buy-side-research-skills/.claude-plugin/plugin.json
```

Before publishing skill card changes, treat `SKILL.md` frontmatter `description` as the canonical card UI description. Every active skill should keep that field as a short one-line plain text English summary. Do not use `description: |`, Markdown, bullets, or long trigger/workflow paragraphs in frontmatter; put long behavior details in the body and `skill.yaml`.

Before packaging, confirm every active `skill.yaml` `description` matches the corresponding `SKILL.md` frontmatter description exactly, that frontmatter is followed by a top-level `# ...` heading before any runtime capsule, and that both `SKILL.md` and `skill.yaml` are saved as UTF-8 without BOM.

Suggested validation checks:

```powershell
rtk rg -n '^description:' plugins/buy-side-research-skills/skills -g SKILL.md
rtk rg -n '^summary:|^description:' plugins/buy-side-research-skills/skills -g skill.yaml
rtk rg -n '^(# |## Research Runtime Capsule|## Modeling Runtime Capsule)' plugins/buy-side-research-skills/skills -g SKILL.md
```

## Dependency Policy

The package should not preinstall Docling, EdgarTools, AKShare, edinet-tools, dart-fss, openesef, Tesseract, MarkItDown, or other parser/provider extras.

- Core runtime dependencies may be installed by init/update.
- Provider, Docling, OCR, and vision extras are installed by group on first use.
- System dependencies are check-only; do not silently modify the system.

## Update-Agent-Runtime Sync

`/update-agent-runtime` consumes a release payload or latest GitHub release. It does not recursively copy `skills/*/scripts` and does not use `init-workspace/assets` as the deployment source.

### Claude Code

1. Create the latest version cache directory from the release payload.
2. Update `~/.claude/plugins/installed_plugins.json` `version` and `installPath`.
3. Restart Claude Code session.

### Codex

1. Create the latest version cache directory from the release payload.
2. Refresh flat `~/.codex/plugins/cache/buy-side-research-skills/skills/`.
3. Refresh local plugin metadata.
4. Restart Codex session.

### `.agents` Marketplace

Update `.agents/plugins/marketplace.json` path to the latest Codex cache version directory.

### Workspace

Run workspace sync through the packaged runtime manager:

```powershell
python _scripts/runtime-manager.py plan --runtime-root <release-payload>/runtime
python _scripts/runtime-manager.py update --runtime-root <release-payload>/runtime
python _scripts/runtime-manager.py verify
```

Conflicts must be preserved. Adopt only explicit plugin-owned targets:

```powershell
python _scripts/runtime-manager.py adopt --runtime-root <release-payload>/runtime --target <path>
```

## CPR: Commit, Push, Release

CPR means the final `commit -> push -> release` sequence. It is not the release payload directory.

Do CPR only after code tests, instance tests, release payload verification, host dry-run, and workspace dry-run pass.

### Pre-CPR Version Audit

All listed files must match `X.X.X` before publishing:

```text
1. plugins/buy-side-research-skills/.claude-plugin/plugin.json  -> "version": "X.X.X"
2. plugins/buy-side-research-skills/.codex-plugin/plugin.json   -> "version": "X.X.X"
3. .claude-plugin/marketplace.json                              -> "version": "X.X.X" (top-level + plugins[0].version)
4. .agents/plugins/marketplace.json                             -> "version": "X.X.X" (top-level + plugins[0].version)
5. docs/release.md                                              -> Current release version: `X.X.X`
6. README.md                                                    -> > vX.X.X
7. git tag                                                      -> vX.X.X
```

### CPR Commands

```powershell
git status --short
git add <changed-files>
git commit -m "feat: refactor research runtime pipeline"
git push origin <branch>
gh release create vX.X.X plugins/buy-side-research-skills/_dist/buy-side-research-skills/X.X.X.zip --title "vX.X.X" --notes-file <release-notes.md>
```

If `gh` is unavailable, create the GitHub Release manually after push and upload the zip produced by `build-release`.
