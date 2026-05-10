# Release

Release packages should be reproducible from the plugin dev repo and safe to share with colleagues. The current stable shareable baseline is `v3.4.0`, including `init`, `ingest`, and opt-in ingest dependency bootstrap.

## Include

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `scripts/`
- `docs/`
- `examples/`
- `archive/`
- `CLAUDE.md`
- `FRAMEWORK.md`
- `META-SKILL.md`
- `README.md`

The release builder intentionally excludes `AGENTS.md`; it is a local agent compatibility entry point, not part of the colleague-facing plugin package.

## Exclude

- `.git/`
- `.claude/`
- `RTK.md`
- local editor state
- caches
- `dist/`
- release archives

## Pre-Release Gates

Run all validators before producing a zip:

```powershell
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-global-rules.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-primitive-routing.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-structure.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-artifact-policy.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-company-primer.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-init-skill.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-ingest-skill.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.4.0
& 'C:\Users\M\.claude\rtk.exe' git diff --check
```

## Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.4.0
```

The build writes:

```text
dist/buy-side-research-skills-3.4.0.zip
```

The build script calls the release package validator after creating the zip.

## Ingest Runtime Assets

`3.4.0` release packages must include:

```text
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
```

The package should not preinstall Docling, EdgarTools, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running `_scripts/bootstrap-ingest-deps.ps1`.
