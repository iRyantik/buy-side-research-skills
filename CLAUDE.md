# CLAUDE.md - Buy-Side Research Plugin Dev Constitution

> 本文件只服务这个 plugin source repo。它不是 plugin runtime prompt，也不进入用户安装包。
> Runtime 行为由各 `SKILL.md`、`skill.yaml`、`skills/_shared/global-rules.md`、research skill capsule 和 workspace templates 承担。
> 用户 research workspace 的本地规则由 `init` 生成的 workspace `CLAUDE.md` 承担。

## 1. Repository Role

本 repo 是 `buy-side-research-skills` 插件源码项目，用于开发、验证、打包和发布 skills。

它不是日常 research workspace。不要在 repo root 创建 topic sessions、research artifacts、raw material cache、models 或用户研究材料。

三棵树：

```text
buy-side-research-skills/          # plugin source repo, managed with git
release-package/                   # generated zip / marketplace payload
Research-AI-Power/                 # user-owned research workspace created by init
```

## 2. Dev Source Of Truth

- `SKILL.md` 是 runtime truth：触发后实际行为、边界、workflow、输出契约。
- `skill.yaml` 是 metadata / index truth：name、category、research_layer、artifact_policy、capabilities、workflow。
- `skills/_shared/global-rules.md` 是 runtime research global rules 的维护源。
- `skills/meta-skill/SKILL.md` 是唯一 active skill-authoring guide。
- `meta.json` 已 retired；active skill 目录下不得新建或恢复。

Root `CLAUDE.md` 和 root `AGENTS.md` 只服务开发维护，不作为 plugin runtime 或 research workspace runtime。

## 3. Skill Authoring Rules

新增、重写或大幅修改任何 `skills/*/SKILL.md` 前，必须遵守 `skills/meta-skill/SKILL.md`。

新增 skill 必须先判断：

- `category: research` 或 `category: operations`
- research skill 必须设置合法 `research_layer`: `triage`、`foundation`、`deep-work`、`memory`
- operations skill 不设置 `research_layer`，不强制 research capsule / Source 政策 / 篇幅基准

Active skills 保持一层平铺：`skills/[skill-name]/SKILL.md`。不要物理移动进 `skills/research/` 或 `skills/operations/`。

修改 skill governance 时必须同步：

- `skill.yaml`
- relevant validators in `scripts/validate-*.ps1`
- README / docs
- plugin manifests
- release package validator

## 4. Runtime Rule Distribution

插件运行时可能只加载具体 `SKILL.md`，不一定读取 root `CLAUDE.md`。

因此：

- research runtime global rules 必须在 `skills/_shared/global-rules.md` 维护，并内嵌到每个 active research `SKILL.md` 的 `Global Rules Capsule`。
- skill-specific Source 政策只写增量规则，不依赖 root `CLAUDE.md`。
- operations skills 使用 operations 结构，不强制 research capsule。
- workspace runtime rules 由 `skills/init/assets/CLAUDE.md.template` 生成到用户 research workspace。

## 5. Artifact And Workspace Policy

新研究产物默认进入用户 workspace 的 topic session：

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

如果 topic session / save path 不明确，先用 `new-session` 创建或解析路径。

Policy classes:

- `none`: conversation-only
- `optional_topic_session`: 用户要求时保存到当前 topic session
- `default_topic_session`: 默认保存到当前 topic session，路径不清先确认
- `earned_memory`: 只保存已研究清楚的 journal / Boss Brief / index update
- `external_workbook`: 写入用户 workbook 或 `_models/`
- `workspace_scaffold`: 创建 / 修复 research workspace
- `cache_artifact`: 写入 `_cache/` operational markdown
- `topic_session_scaffold`: 创建 / 定位 topic session 和轻量更新 `index.md`

不要恢复 root `screens/`、`peers/`、`quickreads/`、`cross-market/` 作为 active artifact 默认路径。

## 6. Release Policy

Release package 应包含用户安装和 runtime 必需材料：

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `README.md`

Release package 不包含：

- root `CLAUDE.md`
- root `AGENTS.md`
- root `scripts/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- local editor / agent state

注意：release package 必须包含 `skills/init/assets/CLAUDE.md.template` 和 `skills/init/assets/AGENTS.md.template`，因为它们用于初始化用户 research workspace。也必须包含 skill 内部 runtime scripts，例如 `skills/init/scripts/` 和 `skills/ingest/scripts/`。

## 7. Validation

提交或发布前至少运行相关 gates：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-global-rules.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-primitive-routing.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-structure.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-artifact-policy.ps1
git diff --check
```

如果修改了 release package 规则，必须运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.5.0
```

## Version

- Version: v3.5.0
- Last updated: 2026-05-10
