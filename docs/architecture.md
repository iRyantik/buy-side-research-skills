# Architecture

This repo is the source wrapper for the `buy-side-research-skills` plugin. Runtime research work happens in a user-owned research workspace created by `init-workspace`.

## Source Layout

The canonical plugin payload lives under `plugins/buy-side-research-skills/`:

```text
repo-root/
  .claude-plugin/
    marketplace.json
  plugins/
    buy-side-research-skills/
      .claude-plugin/
        plugin.json
      .codex-plugin/
        plugin.json
      skills/
        <skill-name>/
          SKILL.md
          skill.yaml
  docs/
  examples/
  CLAUDE.md
  AGENTS.md
  README.md
```

Root `scripts/` and root `skills/` are not part of the current source layout. Do not restore the old root-level runtime manifests or validator/build scripts unless the tooling is redesigned in a separate change.

## Active Skill Layout

Active skills remain flat inside the payload:

```text
plugins/buy-side-research-skills/skills/<skill-name>/SKILL.md
plugins/buy-side-research-skills/skills/<skill-name>/skill.yaml
```

Do not move active skills into `skills/research/` or `skills/operations/`.

Operations skills:

```text
init-workspace
new-session
ingest
financial-data
integrate
promote-company
meta-skill
```

`integrate` keeps its legacy meaning: whole-topic directory merge. `promote-company` is separate: it promotes company-scoped files from an industry/theme workbench into `topics/company/<company-slug>/`.

## Workspace Shape

`init-workspace` creates the workspace shell. `new-session` creates lightweight topic roots. `ingest`, `financial-data`, `driver-map`, and modeling skills create operational folders only when needed.

```text
research-workspace/
  CLAUDE.md
  AGENTS.md
  _inbox/
  _scripts/
  edge-radar.md
  topics/
    industry/<industry-slug>/
      index.md
      _inbox/
      2026-05-18-industry-quickread.md
      2026-05-18-peer-deep-dive.md
      2026-05-18-rklb-stock-quickread.md
      2026-05-18-rklb-driver-map.md

    company/<company-slug>/
      index.md
      _inbox/
      2026-05-18-stock-quickread.md
      _raw/       # on demand by ingest
      _cache/     # on demand by ingest / financial-data / driver-map
      _models/    # on demand by modeling skills
```

Rules:
- `new-session` creates only `index.md` and `_inbox/`.
- `new-session` does not create `_raw/`, `_cache/`, or `_models/`.
- `ingest` requires the topic root to exist and creates `_raw/<category>/` and `_cache/` on first conversion.
- Industry and theme topics do not get `_models/` by default.
- Company canonical topics are the durable home for company financial data, canonical driver maps, and model workbooks.

## Company Promotion

Use `promote-company` when a company first researched inside an industry/theme workbench deserves a canonical company topic.

Default behavior:
- create or locate `topics/company/<company-slug>/index.md` and `_inbox/`
- move root Markdown matching `YYYY-MM-DD-<company-slug>-*.md`
- remove the company prefix after moving
- move clearly attributable `_inbox`, `_raw`, and `_cache` files
- leave mixed peer/industry files in the source topic and backlink them
- update both indexes with provenance

Example:

```text
topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md
-> topics/company/rklb/2026-05-18-stock-quickread.md
```

Do not use `promote-company` for whole-topic directory merges; use `integrate`.

## Cache And Modeling Inputs

`ingest` cache:

```text
topics/<namespace>/<topic-slug>/_cache/<source-filename>.md
```

`financial-data` canonical company cache:

```text
topics/company/<company-slug>/_cache/financial-data/
  financial-data-summary.md
  internal/
    actuals-resolved.json
    evidence-pack.json
    source-map.json
    completeness.json
```

`driver-map` canonical company cache:

```text
topics/company/<company-slug>/_cache/driver-map/
  driver-map.md
  internal/
    driver-map.json
```

Model workbooks:

```text
topics/company/<company-slug>/_models/
  <ticker>-3statement-model.xlsx
  <ticker>-3statement-dcf-model.xlsx
  <ticker>-comps-analysis.xlsx
  <ticker>-model-update.xlsx
```

Modeling skills must not coerce missing or unmapped actuals to zero.

## Release Package

Release packages remain flat even though the source repo is nested:

```text
.claude-plugin/
.codex-plugin/
skills/
README.md
```

Release packages must not contain `plugins/`, root `CLAUDE.md`, root `AGENTS.md`, `docs/`, `examples/`, `.git/`, `dist/`, or local machine state.
