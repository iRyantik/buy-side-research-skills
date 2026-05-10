# Install

Repository: `iRyantik/buy-side-research-skills`

This plugin is designed for colleague self-installation through GitHub or a release zip. The first colleague-shareable baseline is `v3.3.1`.

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

## Release Zip

Download `buy-side-research-skills-3.3.1.zip` from the repo release artifact or build it locally with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.3.1
```

Extract the zip into the plugin location required by Claude or Codex, then confirm the plugin exposes the skills in `skills/`.

## First Use

Version `3.3.1` does not include `init` or `ingest`. Users should open their own research workspace, install the plugin, and use `examples/workspaces/ai-data-center-power/` to see the intended artifact shape until the guided workspace setup batch lands.
