# Release

Release packages should be reproducible from the plugin dev repo and safe to share with colleagues. The first stable shareable baseline is `v3.3.1`. Current `main` may build `3.4.0-dev` packages with `init` and `ingest`; formal `v3.4.0` waits for release hardening.

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
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.4.0-dev
& 'C:\Users\M\.claude\rtk.exe' git diff --check
```

## Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.4.0-dev
```

The build writes:

```text
dist/buy-side-research-skills-3.4.0-dev.zip
```

The build script calls the release package validator after creating the zip.
