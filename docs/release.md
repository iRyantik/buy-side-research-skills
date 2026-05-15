# Release

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

Current release version: `3.8.0`.

## Release Package Contents

Release zip includes only runtime/install materials:

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `README.md`

Release zip must not include source-repo maintenance files:

- root `CLAUDE.md`
- root `AGENTS.md`
- root `scripts/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- local editor or agent state

Release zip must include skill-owned runtime resources, especially:

```text
skills/init-workspace/assets/CLAUDE.md.template
skills/init-workspace/assets/AGENTS.md.template
skills/init-workspace/scripts/init-research-workspace.ps1
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/ingest.py
skills/ingest/scripts/ingest_xlsx.py
skills/ingest/scripts/ingest_table_crosscheck.py
skills/financial-data/assets/requirements-financial-data.txt
skills/financial-data/scripts/financial_data.py
skills/financial-data/scripts/bootstrap-financial-data-deps.ps1
skills/financial-data/scripts/providers/*.py
```

## Validator Policy

Release packaging does not require the full validator suite. Full-suite validation is expensive and should not run for routine commit / release work.

Run validators only after creating, rewriting, or materially changing a skill, and then run only the targeted validator(s) that cover that skill or governance surface. If the user explicitly asks to skip validators, do not run validators.

When changing the modeling sub-agent protocol for `3-statement-model`, `dcf-model`, `comps-analysis`, or `model-update`, run:

```powershell
rtk powershell -NoProfile -ExecutionPolicy Bypass -File scripts\validate-model-sub-agent-protocol.ps1
```

## Build

```powershell
rtk powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.8.0
```

Build artifact:

```text
dist/buy-side-research-skills-3.8.0.zip
```

The build script only stages and zips release contents. It does not run validators automatically.

## Dependency Policy

The package should not preinstall Docling, EdgarTools, AKShare, edinet-tools, dart-fss, openesef, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running `_scripts/bootstrap-ingest-deps.ps1` or `_scripts/financial-data/bootstrap-financial-data-deps.ps1`.
