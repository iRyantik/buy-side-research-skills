# Architecture

This repository is the development home for the buy-side research plugin. It is not a research workspace.

## Three Trees

```text
buy-side-research-skills/          # plugin dev repo, managed with git
release-package/                   # generated zip or marketplace payload
Research-AI-Power/                 # user research workspace, created later by init
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

Research workspaces are user-owned folders. They will be created by the future `init` skill and should contain `_inbox/`, `_raw/`, `_cache/`, `_models/`, and `topics/`. They are not the same thing as this plugin dev repo.
