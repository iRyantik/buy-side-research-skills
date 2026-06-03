# AGENTS.md — Codex Dev Entry Point

> This file is only a compatibility entry point for Codex / agents in the plugin source repo wrapper root. It is not an independent constitution, and it does not ship in user install packages.
> The source of truth for development and maintenance in this directory is [`CLAUDE.md`](CLAUDE.md).

## Required Workflow

- Before working in this directory or subdirectories, read and obey root `CLAUDE.md`.
- If `AGENTS.md`, `CLAUDE.md`, any `SKILL.md`, or other local instructions conflict, root `CLAUDE.md` takes precedence.
- Do not replicate source policy, anti-sell-side rules, skill trigger tables, or file organization details here; those rules are maintained separately in root `CLAUDE.md`, `plugins/buy-side-research-skills/skills/_shared/research-policy-baseline.md`, each `SKILL.md`, and workspace `CLAUDE.md.template`.

## Boundary

- This file only serves the plugin source repo wrapper root.
- The canonical plugin payload root is `plugins/buy-side-research-skills/`.
- User research workspaces are installed by `init-workspace` with their own `CLAUDE.md` and a pointer-type `AGENTS.md`.
- Plugin release packages must not include root `AGENTS.md`.
