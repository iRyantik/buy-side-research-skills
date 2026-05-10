# Install

Repository: `iRyantik/buy-side-research-skills`

This plugin is designed for colleague self-installation through GitHub or a release zip.

## Claude

Preferred path after marketplace setup:

```powershell
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

If marketplace setup is not available, download the release zip, extract it, and install it through Claude Code's local plugin flow.

## Codex

Codex support is provided through `.codex-plugin/plugin.json` and the same `skills/` directory.

```powershell
codex plugin marketplace add iRyantik/buy-side-research-skills
```

If your Codex environment uses local plugins instead of marketplace install, extract the release zip into the configured plugin location and confirm the plugin exposes the skills in this repo.

## First Use

Batch 1 only prepares the plugin package skeleton. The later `init` batch will add a guided workspace setup skill. Until then, users can inspect `examples/workspaces/ai-data-center-power/` to see the intended research workspace shape.
