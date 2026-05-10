# Architecture

This repository is the source home for the buy-side research plugin. It is not a research workspace.

## Three Trees

```text
buy-side-research-skills/          # plugin source repo
release-package/                   # generated zip or marketplace payload
Research-AI-Power/                 # user research workspace, created by init
```

## Source Repo

The repo contains source files needed to build and validate the plugin:

```text
.claude-plugin/                    # Claude plugin manifest
.codex-plugin/                     # Codex plugin manifest
skills/                            # active runtime skills and shared rules
scripts/                           # maintainer validators and release build scripts
docs/                              # user and maintainer documentation
examples/                          # example workspaces, not runtime dependencies
```

Runtime resources that a skill must call live inside that skill directory, for example `skills/ingest/scripts/` or `skills/init/assets/`. Root `scripts/` is for source-repo validation and release packaging only.

## Skill Taxonomy

Active skills stay flat under `skills/[skill-name]/SKILL.md`; the repo does not physically nest skills by category.

Top-level categories:

- `research`: investment research skills that must carry the Global Rules Capsule and a `research_layer`.
- `operations`: workspace, cache, path, or skill-governance tools that use a lighter execution structure.

Research layers:

| Layer | Skills |
|---|---|
| `triage` | `information-impact`, `candidate-screener`, `stock-quickread`, `next-step` |
| `foundation` | `company-primer`, `mechanism-map`, `driver-map`, `cross-market-compare` |
| `deep-work` | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` |
| `memory` | `research-journal` |

Operations skills:

```text
init
ingest
meta-skill
new-session
```

`meta-skill` is the active guide for creating, rewriting, reviewing, and validating plugin skills. `new-session` creates or locates topic sessions, resolves canonical save paths, and lightly updates topic `index.md`; it does not do research or recommend the next research skill.

## Release Package

A release package should include plugin manifests, skills, user docs, examples, and README. It must not include local agent state, private machine config, `.git/`, root `CLAUDE.md`, root `AGENTS.md`, or root `scripts/`.

There is no plugin-level CLAUDE / AGENTS runtime file. The source repo has root `CLAUDE.md` + `AGENTS.md` for maintenance only; `init` installs workspace `CLAUDE.md` + pointer `AGENTS.md` into user research workspaces.

## Research Workspace

Research workspaces are user-owned folders. They are created or repaired by the `init` skill and should contain workspace `CLAUDE.md`, pointer `AGENTS.md`, `_inbox/`, `_raw/`, `_cache/`, `_models/`, `_scripts/`, and `topics/`. Raw materials are converted by `ingest` into `_cache/` markdown. Workspaces are not the same thing as this plugin source repo.

```text
[research-workspace]/
├── CLAUDE.md
├── AGENTS.md
├── _inbox/
├── _raw/
│   ├── filings/
│   ├── transcripts/
│   ├── sellside/
│   ├── industry/
│   ├── irdecks/
│   └── datasets/
├── _cache/
├── _models/
├── _scripts/
└── topics/
    ├── _meta/
    │   └── edge-radar.md
    ├── company/
    ├── theme/
    └── event/
```

`init` does not run `git init`, install dependencies, ingest raw files, or create topic research artifacts. It copies `_scripts/bootstrap-ingest-deps.ps1`, `_scripts/requirements-ingest.txt`, and ingest helper scripts so the user can explicitly opt in later. `ingest` writes operational cache files only; it does not create earned research memory. Use `new-session` when the user is ready to create a topic session or resolve where an artifact should be saved.

## Artifact Save Policy

New research artifacts should live inside topic sessions:

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

Company foundation artifacts such as `company-primer.md` follow the same topic-session rule and are saved only when the user asks to preserve them.

If the current topic session is unclear, route to `new-session` before writing the artifact. `new-session` may create the session folder and lightly touch topic `index.md`, but it must not write research conclusions.

The only exceptions are conversation-only skills (`information-impact`, `next-step`), earned-memory writes (`research-journal`), and external workbooks (`financial-model`). Root folders such as `screens/`, `peers/`, `quickreads/`, and `cross-market/` are legacy/example shapes, not active default save locations.

Material cache artifacts live under:

```text
_cache/[bucket]/[source-filename].md
```

Cache files are source-tracked intermediate material, not original source and not topic-session output.

## Ingest Toolchain

The full material conversion stack is local-first: Docling is the primary PDF / DOCX / PPTX converter, EdgarTools is required for SEC filing readiness, openpyxl handles workbook structure, python-pptx / python-docx are fallback extractors, PDFPlumber cross-checks PDF table numerics, Tesseract supports scanned PDF OCR, and MarkItDown is a degraded fallback for legacy formats.

Dependency installation is explicit:

```powershell
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
_scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

No skill should silently install global dependencies.
