# Release

This document is for maintainers of the plugin source repo. It is not required for day-to-day plugin use.

The current release version is `3.5.0`. Formal stable releases should be tagged and published through GitHub Releases.

## Release Package Surface

The release zip should include only user installation and runtime material:

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `docs/install.md`
- `docs/architecture.md`
- `examples/`
- `README.md`

The release zip must exclude source-repo maintenance files:

- root `CLAUDE.md`
- root `AGENTS.md`
- root `scripts/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- local editor or agent state

The release zip must still include skill-local runtime resources, especially:

```text
skills/init/assets/CLAUDE.md.template
skills/init/assets/AGENTS.md.template
skills/init/scripts/init-research-workspace.ps1
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/ingest.py
skills/ingest/scripts/ingest_xlsx.py
skills/ingest/scripts/ingest_table_crosscheck.py
```

## Pre-Release Gates

Run all validators before producing a zip:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-global-rules.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-primitive-routing.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-structure.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-artifact-policy.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-company-primer.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-init-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-ingest-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-meta-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-new-session-skill.ps1
git diff --check
```

## Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.5.0
```

The build writes:

```text
dist/buy-side-research-skills-3.5.0.zip
```

The build script calls the release package validator after creating the zip.

## Dependency Policy

The package should not preinstall Docling, EdgarTools, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running `_scripts/bootstrap-ingest-deps.ps1`.
