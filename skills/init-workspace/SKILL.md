---
name: init-workspace
description: Use when setting up or repairing a buy-side research workspace folder before research begins, especially when the user asks to initialize, scaffold, bootstrap, or create the standard workspace layout.
---

# Init

`init-workspace` 把一个普通文件夹变成可用的 buy-side research workspace。它创建或修复目录 scaffold，写入 workspace `CLAUDE.md`、`.gitignore` 和 `edge-radar.md`，并复制 ingest / financial-data helper scripts，帮助用户在正确位置开始研究。

它是 operations skill，不是研究 skill。它不研究公司、不 ingest 文件、不安装依赖、不运行 `git init`、不创建 topic artifact，也不应该把 workspace scaffold 写进当前 plugin repo。

## 心法

`init-workspace` 的核心 invariant 是防止 workspace 污染：plugin dev repo、raw material、cache、models 和可沉淀的 research memory 必须分开。一个干净 workspace 比一份更长说明文档更有用。

默认行为必须保守、幂等、可重复运行。已有核心文件不覆盖，缺什么补什么；复制 helper scripts 可以，但执行 ingest 或安装依赖不可以。

## 职责边界

负责：
- 创建 `_inbox/`、`_scripts/`、`topics/` scaffold。
- 写入缺失的 workspace `CLAUDE.md`、`.gitignore`、`edge-radar.md`。
- 复制 `init-research-workspace.ps1`、init assets（含 `env-setup.ps1.template`）、ingest scripts、`bootstrap-ingest-deps.ps1` 和 `requirements-ingest.txt` 到 `_scripts/`。
- 复制 `financial-data` helper scripts、providers、`bootstrap-financial-data-deps.ps1` 和 `requirements-financial-data.txt` 到 `_scripts/financial-data/`。

不负责：
- 不 ingest PDF / Excel / PPTX / DOCX。
- 不安装 Docling、EdgarTools、Tesseract、MarkItDown 或 Python packages。
- 不创建 dated topic research artifact、`research-journal.md` 或 `boss-brief.md`。
- 不运行 `git init`。
- 不在 plugin dev repo 或 plugin install directory 内初始化 workspace。

## 触发与输入

触发语：
- “init research workspace”
- “初始化研究工作区”
- “创建研究文件夹”
- “setup research”
- “bootstrap workspace”
- “补齐 research workspace”

必须确认：
- `WorkspacePath`：用户明确给出的 research workspace 路径。
- 目标路径不是当前 plugin repo、`.claude/plugins/...` install directory，且不包含 `.claude-plugin/`、`.codex-plugin/`、`skills/` 这类 plugin repo 标志。
- 已有 `CLAUDE.md`、`.gitignore`、`topics/_meta/edge-radar.md` 时只 skip，不覆盖。

## 执行模式

### New Workspace Scaffold

目标路径不存在或为空时，创建完整 scaffold、核心模板和 `_scripts/` helper files。

### Repair Existing Workspace

目标路径已有内容时，只补缺失目录和缺失核心文件。已有文件一律 skipped。

### Dry Explanation

用户只问“最终文件夹长什么样”或“init 会做什么”时，不运行脚本，只解释目录树和边界。

## 工具资源

本 skill 使用：
- `skills/init-workspace/scripts/init-research-workspace.ps1`
- `skills/init-workspace/assets/CLAUDE.md.template`
- `skills/init-workspace/assets/AGENTS.md.template`
- `skills/init-workspace/assets/gitignore.template`
- `skills/init-workspace/assets/edge-radar.md`
- `skills/init-workspace/assets/env-setup.ps1.template`
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.ps1`
- `skills/ingest/assets/requirements-ingest.txt`
- `skills/financial-data/scripts/financial_data.py`
- `skills/financial-data/scripts/bootstrap-financial-data-deps.ps1`
- `skills/financial-data/scripts/providers/*.py`
- `skills/financial-data/assets/requirements-financial-data.txt`

优先调用 helper script，不要手写复制逻辑。

## 文件安全

- 幂等：重复运行只补缺失项。
- 不覆盖已有 `CLAUDE.md`、`.gitignore`、`topics/_meta/edge-radar.md`。
- 不删除、不移动用户已有文件。
- 不在 plugin repo、plugin install directory 或任何包含 plugin manifest 的目录内执行。
- 不把 `_raw/`、`_cache/`、`_models/` 当作可提交研究成果。

## 运行输出契约

成功或 repair 后输出：

```markdown
## Init Result

**结论先行**
已初始化 / 已补齐 research workspace：[path]

## Created
- [...]

## Skipped
- [...]

## Workspace Shape
[目录树]
```

被阻止时输出：

```markdown
## Init Blocked

**结论先行**
不能在这个路径初始化 research workspace。
- path: [...]
- reason: [...]
- suggested_path: [...]
```

## 失败处理

- 路径不明确：先要求明确 `WorkspacePath`，不要猜。
- 命中 plugin repo 标志：拒绝并要求换一个 user-owned research workspace。
- 文件权限不足：说明哪个路径失败，不要继续假装成功。
- helper script 缺失：报告 plugin package 不完整，要求修复安装或重新安装 release zip。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| 用户刚装好插件，不知道从哪里开始 | `init-workspace` 创建 workspace scaffold |
| 用户已有 workspace 但缺 `_raw/`、`_cache/`、`topics/_meta/` | `init-workspace` repair missing scaffold |
| workspace 已建好，用户要开始某个 company / theme / event research | handoff 到 `new-session` 创建 topic root |
| 用户把材料放进 `_inbox/` 后想转换 | handoff 到 `ingest` |
| 用户缺 Docling / EdgarTools / Tesseract / MarkItDown | 提示 `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly`，用户确认后才 `-Yes` |
| 用户缺 SEC / AKShare / EDINET / DART / openesef 财务数据依赖 | 提示 `_scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly`，用户确认后才 `-Yes` |
| 用户要研究公司 | handoff 到 `company-primer` 或 `stock-quickread` |

Artifact policy：
- `save_policy`: `workspace_scaffold`
- `default_artifact`: `workspace scaffold`
- `canonical_location`: 用户指定 research workspace

## 安全自查

- ❌ 在 plugin repo 内初始化 workspace。
- ❌ 覆盖已有 `CLAUDE.md`、`.gitignore` 或 `edge-radar.md`。
- ❌ 自动 `git init`。
- ❌ 自动 ingest raw materials。
- ❌ 自动拉取 financial-data 或安装 financial-data dependencies。
- ❌ 自动安装 dependencies。
- ❌ 创建 topic artifact、`research-journal.md` 或 `boss-brief.md`。
- ❌ 生成 v2 state folders，如 `coverage/`、`portfolio/`、`pairs/`。
