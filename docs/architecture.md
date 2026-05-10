# Architecture

This repository is the development home for the buy-side research plugin. It is not a research workspace.

## Three Trees

```text
buy-side-research-skills/          # plugin dev repo, managed with git
release-package/                   # generated zip or marketplace payload
Research-AI-Power/                 # user research workspace, created by init
```

## Plugin Dev Repo

The repo contains source files needed to build and validate the plugin:

```text
.claude-plugin/                    # Claude plugin manifest
.codex-plugin/                     # Codex plugin manifest
skills/                            # active runtime skills and shared rules
scripts/                           # development and validation scripts
docs/                              # human documentation
examples/                          # example workspaces, not runtime dependencies
archive/                           # historical v2 reference material
```

Runtime resources that a skill must call should live inside that skill directory, for example `skills/ingest/scripts/` or `skills/init/assets/`. Root `scripts/` is for development validation and release packaging only.

## Release Package

A release package should include the plugin manifests, skills, docs, examples, and validation/release scripts. It must not include local agent state, private machine config, or `.git/`.

## Research Workspace

Research workspaces are user-owned folders. They are created or repaired by the `init` skill and should contain `_inbox/`, `_raw/`, `_cache/`, `_models/`, `_scripts/`, and `topics/`. Raw materials are converted by `ingest` into `_cache/` markdown. Workspaces are not the same thing as this plugin dev repo.

```text
[research-workspace]/
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

`init` does not run `git init`, ingest raw files, or create topic research artifacts. `ingest` writes operational cache files only; it does not create earned research memory.

## Artifact Save Policy

New research artifacts should live inside topic sessions:

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

Company foundation artifacts such as `company-primer.md` follow the same topic-session rule and are saved only when the user asks to preserve them.

The only exceptions are conversation-only skills (`information-impact`, `next-step`), earned-memory writes (`research-journal`), and external workbooks (`financial-model`). Root folders such as `screens/`, `peers/`, `quickreads/`, and `cross-market/` are legacy/example shapes, not active default save locations.

Material cache artifacts live under:

```text
_cache/[bucket]/[source-filename].md
```

Cache files are source-tracked intermediate material, not original source and not topic-session output.
