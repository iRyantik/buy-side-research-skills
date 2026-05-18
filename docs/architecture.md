# Architecture

This repo is the plugin source. Runtime research work happens in a user-owned research workspace created by `init-workspace`.

## Active Skill Layout

Active skills remain flat:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/skill.yaml
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

`integrate` keeps its legacy meaning: whole-topic directory merge. `promote-company` is separate: promote company-scoped files from an industry/theme workbench into `topics/company/<company-slug>/`.

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

## Research File Names

Company canonical topic:

```text
topics/company/rklb/2026-05-18-stock-quickread.md
topics/company/rklb/2026-05-18-driver-map.md
```

Industry/theme topic research about the topic itself:

```text
topics/industry/space-launch/2026-05-18-industry-quickread.md
topics/industry/space-launch/2026-05-18-peer-deep-dive.md
```

Industry/theme workbench research about one company:

```text
topics/industry/space-launch/2026-05-18-rklb-stock-quickread.md
topics/industry/space-launch/2026-05-18-rklb-driver-map.md
```

Collision handling:

```text
2026-05-18-rklb-driver-map.md
2026-05-18-rklb-driver-map-2.md
2026-05-18-rklb-driver-map-3.md
```

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

Release packages contain:

```text
.claude-plugin/
.codex-plugin/
skills/
README.md
```

Release packages must not contain root `CLAUDE.md`, root `AGENTS.md`, root `scripts/`, `docs/`, `examples/`, `.git/`, or local machine state.
