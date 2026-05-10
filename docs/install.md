# Install

Repository: `iRyantik/buy-side-research-skills`

This plugin can be installed through a plugin marketplace flow when available, or from a release zip.

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

For the stable baseline, download `buy-side-research-skills-3.4.0.zip` from the GitHub Release artifact.

Extract the zip into the plugin location required by Claude or Codex, then confirm the plugin exposes the skills in `skills/`.

## First Use

Run `init` to create or repair a research workspace scaffold. In `3.5.0`, `init` installs workspace `CLAUDE.md` plus a pointer `AGENTS.md` for Codex / agents.

Use `new-session` after `init` when you want to create or locate a topic session before saving research artifacts. `new-session` resolves paths and lightly updates topic `index.md`; it does not write research conclusions.

## Ingest Dependencies

`init` copies ingest helpers into the research workspace `_scripts/` folder. First check dependencies:

```powershell
python _scripts/ingest.py --check-deps
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

If the output looks right, opt in to installation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

Python packages install to the current user by default. Tesseract is a system binary; the bootstrap tries `winget` first and otherwise prints Chocolatey / UB Mannheim fallback instructions. The script does not run during `init`.
