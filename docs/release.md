# Release

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

Current release version: `3.10.7`.

## Source And Runtime Shape

The source repo is a wrapper. The canonical plugin payload is:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/
  .claude-plugin/
    plugin.json
  .codex-plugin/
    plugin.json
  skills/
```

Release zip files stay flat for installation:

```text
.claude-plugin/
.codex-plugin/
skills/
README.md
```

## Release Package Contents

Release zip includes only runtime/install materials copied from the payload plus root README:

- `plugins/buy-side-research-skills/.claude-plugin/` -> `.claude-plugin/`
- `plugins/buy-side-research-skills/.codex-plugin/` -> `.codex-plugin/`
- `plugins/buy-side-research-skills/skills/` -> `skills/`
- `README.md`

Release zip must not include source-repo maintenance files:

- `plugins/`
- root `CLAUDE.md`
- root `AGENTS.md`
- `docs/`
- `examples/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- local editor or agent state
- root marketplace wrapper files

`docs/beginner-skill-map.html` is a repository documentation asset for beginner reading from GitHub. Keep it tracked in the source repo and linked from `README.md`, but do not copy it into the runtime release zip.

Release zip must include skill-owned runtime resources, especially:

```text
skills/init-workspace/assets/CLAUDE.md.template
skills/init-workspace/assets/AGENTS.md.template
skills/init-workspace/scripts/init-research-workspace.ps1
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/ingest.py
skills/ingest/scripts/ingest_xlsx.py
skills/ingest/scripts/ingest_table_crosscheck.py
skills/financial-data/assets/requirements-financial-data.txt
skills/financial-data/scripts/financial_data.py
skills/financial-data/scripts/bootstrap-financial-data-deps.ps1
skills/financial-data/scripts/providers/*.py
skills/reddit-sentiment/assets/requirements-reddit-sentiment.txt
skills/reddit-sentiment/assets/default-clusters.json
skills/reddit-sentiment/scripts/reddit_label.py
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh
skills/promote-company/SKILL.md
skills/promote-company/skill.yaml
skills/promote-company/scripts/promote_company.py
```

## Tooling Policy

Root `scripts/` has been removed from this source layout. Do not reference the old validator or build-release commands in maintenance instructions.

Packaging for this release is assembled manually from the payload into `dist/buy-side-research-skills-3.10.7.zip`. If future releases need automation again, design that tooling in a separate change rather than restoring stale root scripts.

Before publishing a marketplace/plugin manifest change, confirm these JSON files parse without a UTF-8 BOM and start with `{`:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/.codex-plugin/plugin.json
plugins/buy-side-research-skills/.claude-plugin/plugin.json
```

Before publishing skill card changes, treat `SKILL.md` frontmatter `description` as the canonical card UI description. Every active skill should keep that field as a short one-line plain text English summary. Do not use `description: |`, Markdown, bullets, or long trigger/workflow paragraphs in frontmatter; put long behavior details in the body and `skill.yaml`.

Before packaging, also confirm every active `skill.yaml` `description` matches the corresponding `SKILL.md` frontmatter description exactly, and that both `SKILL.md` and `skill.yaml` are saved as UTF-8 without BOM using a stable newline convention.

Suggested validation checks:

```powershell
rtk rg -n '^description:' plugins/buy-side-research-skills/skills -g SKILL.md
rtk rg -n '^summary:|^description:' plugins/buy-side-research-skills/skills -g skill.yaml
```

## Dependency Policy

The package should not preinstall Docling, EdgarTools, AKShare, edinet-tools, dart-fss, openesef, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running `_scripts/bootstrap-ingest-deps.ps1` or `_scripts/financial-data/bootstrap-financial-data-deps.ps1`.
