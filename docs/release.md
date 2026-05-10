# Release

Release packages should be reproducible from the plugin dev repo and safe to share with colleagues.

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
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
& 'C:\Users\M\.claude\rtk.exe' git diff --check
```

The release zip builder will be added in a later batch.
