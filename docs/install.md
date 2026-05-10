# Install

Repository: `iRyantik/buy-side-research-skills`

This plugin is designed for colleague self-installation through GitHub or a release zip. The first colleague-shareable baseline is `v3.3.1`; current `main` may contain `3.4.0-dev` work such as `init` and `ingest`.

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

For the stable baseline, download `buy-side-research-skills-3.3.1.zip` from the repo release artifact. For the current dev package, build it locally with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.4.0-dev
```

Extract the zip into the plugin location required by Claude or Codex, then confirm the plugin exposes the skills in `skills/`.

## First Use

Version `3.3.1` does not include `init` or `ingest`. In `3.4.0-dev`, users can run `init` to create or repair a research workspace scaffold, then run `ingest` to convert supported raw files into `_cache/` markdown. Formal `v3.4.0` still waits for release hardening.

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
