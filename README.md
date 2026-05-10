# Buy-Side Research Skills v3.3.1

Journal-first buy-side equity research skill suite for Claude and Codex. The system helps a researcher find high-value questions, route mechanism / driver gaps to the right primitive, and turn researched insight into topic journals or Boss Briefs.

Repository: `iRyantik/buy-side-research-skills`

## Quick Start

1. Install the plugin from GitHub or a release zip.
2. Open a research workspace, not this plugin repo.
3. Use the active skills to screen, quickread, build company foundations, compare, map mechanisms, map drivers, build theses, and write earned research memory.
4. Use `examples/workspaces/ai-data-center-power/` as a compact reference for how research artifacts should look.

Version `3.3.1` is the first colleague-shareable baseline. Guided workspace creation and raw material ingestion will arrive in later `init` / `ingest` batches.

## Install

Claude and Codex installation notes live in [docs/install.md](docs/install.md).

The repo includes both plugin manifests:

```text
.claude-plugin/plugin.json
.codex-plugin/plugin.json
```

## Project Layout

This repository is the plugin development project. It is managed with git and should not be used as the day-to-day research workspace.

```text
.claude-plugin/                    # Claude plugin manifest
.codex-plugin/                     # Codex plugin manifest
skills/                            # active runtime skills and shared rules
scripts/                           # development validators and release scripts
docs/                              # install, architecture, release docs
examples/                          # example workspaces, not runtime dependencies
archive/                           # historical v2 reference material
```

Runtime files needed by a skill should live inside that skill directory. Root `scripts/` is for development and release validation only.

## Active Skills

| Layer | Skills | Purpose |
|---|---|---|
| Signal / Funnel | `information-impact`, `candidate-screener`, `stock-quickread` | Filter information, find candidates, and decide whether to continue. |
| Company Foundation | `company-primer` | Map what a company sells, how the business evolved, and where disclosure history breaks comparability. |
| Research Primitives | `mechanism-map`, `driver-map`, `cross-market-compare`, `next-step` | Map mechanisms, model drivers, cross-market valuation, and the next highest-value question. |
| Deep Research | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | Run peer work, thesis work, pre-mortems, earnings setup, pair research, and model work. |
| Synthesis / Memory | `research-journal` | Save researched insight and Boss Briefs. |

## Core Loop

```text
Senior Analyst Radar -> better AI questions -> research -> research-journal -> Boss Brief
```

- `Senior Analyst Radar` flags issues that may change business understanding, model drivers, market framing, peer groups, or research priority.
- `company-primer` handles company foundations, business evolution, segment / KPI rename, recast, and disclosure history before driver or thesis work.
- `mechanism-map` handles industry mechanisms, engineering principles, equipment chains, process flows, terminology, and know-how gaps.
- `driver-map` handles revenue, margin, backlog, price / volume / mix, disclosure buckets, KPI oddities, and model-driver gaps.
- `research-journal` saves only researched, source-backed insight. It is not a transcript or idea dump.

## Examples

Examples are stored under [examples/](examples/) and are safe to inspect or copy. They are not loaded by the plugin at runtime.

Current example workspace:

```text
examples/workspaces/ai-data-center-power/
```

## Validation

Run the standard gates before release:

```powershell
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-global-rules.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-structure.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-artifact-policy.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-company-primer.ps1
& 'C:\Users\M\.claude\rtk.exe' powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.3.1
& 'C:\Users\M\.claude\rtk.exe' git diff --check
```

## Version Notes

### v3.3.1

- Hardened release packaging for colleague distribution.
- Added reproducible release zip generation and validation.
- Kept `init` / `ingest` out of scope for a future v3.4.0 release.

### v3.3.0

- Added `company-primer` as the 15th active company foundation skill.
- Added `mechanism-map` as the 14th active research primitive.
- Added formal routing between mechanism / know-how work and driver / model / thesis work.
- Added runtime global rules capsules and canonical `skill.yaml` metadata.

### v3.2.0

- Added `driver-map`.
- Re-layered active skills into Signal / Funnel, Research Primitives, Deep Research, and Synthesis / Memory.
- Expanded `financial-model` into driver-to-valuation workflow.

### v3.1.0

- Restored `pair-trade` as a journal-first active skill.

### v3.0.0

- Pivoted to journal-first research.
- Added `research-journal`, `next-step`, and Senior Analyst Radar.
- Archived v2 state workflow skills and fixtures.
