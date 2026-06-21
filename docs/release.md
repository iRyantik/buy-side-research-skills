# Release

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

Current release version: `6.0.0`.

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

Longbridge market data is now accessed via MCP (v5.15.0+). Install the Longbridge MCP server globally instead of the legacy plugin zip: `claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp`.

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

`skills/_shared/research-policy-baseline.md` is a repository-side authoring baseline. It helps preserve canonical research rules and sync capsules, but it is not a runtime authority layer.

Chinese or multilingual text assets in this repo should be maintained as UTF-8 without BOM, especially governance docs, templates, and skill markdown.

Release zip must include skill-owned runtime resources, especially:

```text
skills/init-workspace/assets/CLAUDE.md.template
skills/init-workspace/assets/AGENTS.md.template
skills/init-workspace/scripts/init-research-workspace.ps1
skills/init-workspace/assets/.claude/hooks/run-hook.cmd
skills/init-workspace/assets/.claude/hooks/run-hook.sh
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/bootstrap-ingest-deps.sh
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
skills/research-viz/SKILL.md
skills/research-viz/skill.yaml
skills/research-viz/assets/template.html
skills/research-viz/assets/template-interactive.html
skills/research-viz/references/*.md
skills/research-viz/examples/*.html
skills/coverage-monitor/SKILL.md
skills/coverage-monitor/SKILL.en.md
skills/coverage-monitor/skill.yaml
skills/coverage-monitor/scripts/**/*.py
skills/update-agent-runtime/SKILL.md
skills/update-agent-runtime/skill.yaml
skills/update-agent-runtime/scripts/update_agent_runtime.py
skills/promote-company/SKILL.md
skills/promote-company/skill.yaml
skills/promote-company/scripts/promote_company.py
```

## Tooling Policy

Root `scripts/` has been removed from this source layout. Do not reference the old validator or build-release commands in maintenance instructions.

Packaging for this release is assembled manually from the payload into `dist/buy-side-research-skills-4.6.2.zip`. If future releases need automation again, design that tooling in a separate change rather than restoring stale root scripts.

Before publishing a marketplace/plugin manifest change, confirm these JSON files parse without a UTF-8 BOM and start with `{`:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/buy-side-research-skills/.codex-plugin/plugin.json
plugins/buy-side-research-skills/.claude-plugin/plugin.json
```

Before publishing skill card changes, treat `SKILL.md` frontmatter `description` as the canonical card UI description. Every active skill should keep that field as a short one-line plain text English summary. Do not use `description: |`, Markdown, bullets, or long trigger/workflow paragraphs in frontmatter; put long behavior details in the body and `skill.yaml`.

Before packaging, also confirm every active `skill.yaml` `description` matches the corresponding `SKILL.md` frontmatter description exactly, that frontmatter is followed by a top-level `# ...` heading before any `## Research Runtime Capsule` / `## Modeling Runtime Capsule`, and that both `SKILL.md` and `skill.yaml` are saved as UTF-8 without BOM using a stable newline convention.

Suggested validation checks:

```powershell
rtk rg -n '^description:' plugins/buy-side-research-skills/skills -g SKILL.md
rtk rg -n '^summary:|^description:' plugins/buy-side-research-skills/skills -g skill.yaml
rtk rg -n '^(# |## Research Runtime Capsule|## Modeling Runtime Capsule)' plugins/buy-side-research-skills/skills -g SKILL.md
```

## Dependency Policy

The package should not preinstall Docling, EdgarTools, AKShare, edinet-tools, dart-fss, openesef, Tesseract, MarkItDown, or other parsers. Users opt in from their research workspace by running the platform-appropriate bootstrap helpers: Windows may use `powershell ... .ps1`, while macOS requires `pwsh` for `.ps1` helpers and may use `_scripts/bootstrap-ingest-deps.sh` where that shell helper exists.

## Auto Cache Sync (v5.0.8+)

`/update-agent-runtime` 运行后自动同步双宿主 cache：

### Claude Code
1. 创建最新版本缓存目录（如 `5.6.0/`），从 marketplace 复制 skills
2. 更新 `~/.claude/plugins/installed_plugins.json` 的 `version` 和 `installPath` 指向最新缓存
3. 重开 Claude Code session 生效

### Codex
1. 刷新 `~/.codex/plugins/cache/buy-side-research-skills/skills/` 为最新 marketplace skills
2. 重开 Codex session 生效

### Workspace
- 同步 `.claude/hooks/`（hook_entry.py + rules/）
- 同步 `references/`（policy + kpi-drivers）
- 同步 `.codex/hooks.json`
- 同步 `.claude/settings.json`

### 版本号清单
每次发版必须同步更新以下文件：
- `.claude-plugin/plugin.json` → `version`
- `.codex-plugin/plugin.json` → `version`
- `docs/release.md` → `Current release version`
- `README.md` → 版本历史

## Pre-Release Version Audit

每次 CPR 之前执行，全部 7 处通过才允许发布：

```
1. .claude-plugin/plugin.json          → "version": "X.X.X"
2. .codex-plugin/plugin.json           → "version": "X.X.X"
3. .claude-plugin/marketplace.json     → "version": "X.X.X"（顶层 + plugins[0].version 双写）
4. .agents/plugins/marketplace.json    → "version": "X.X.X"（顶层 + plugins[0].version 双写）
5. docs/release.md                     → Current release version: `X.X.X`
6. README.md                           → > vX.X.X
7. git tag                             → vX.X.X
8. GitHub Release                       → gh release create vX.X.X
```
