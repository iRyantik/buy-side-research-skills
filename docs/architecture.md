# 架构

本仓库是 buy-side research 插件的源码目录，不是 research workspace。

## 三棵树

```text
buy-side-research-skills/          # 插件源码仓库
release-package/                   # 生成的 zip 或市场分发包
Research-AI-Power/                 # 用户 research workspace，由 init 创建
```

## 源码仓库

仓库包含构建和验证插件所需的源文件：

```text
.claude-plugin/                    # Claude 插件清单
.codex-plugin/                     # Codex 插件清单
skills/                            # active 运行时 skills 和共享规则
scripts/                           # 维护者 validator 和 release 构建脚本
docs/                              # 用户和维护者文档
examples/                          # 示例 workspace，非运行时依赖
```

skill 需要调用的运行时资源放在该 skill 目录内部，例如 `skills/ingest/scripts/` 或 `skills/init-workspace/assets/`。root `scripts/` 仅用于源码仓库验证和 release 打包。

## Skill 分类

Active skills 平铺在 `skills/[skill-name]/SKILL.md` 下，不按 category 物理嵌套。

顶层分类：

- `research`：投研类 skill，必须携带 Global Rules Capsule 并设置 `research_layer`。
- `operations`：workspace、缓存、路径或 skill governance 工具，使用更轻量的执行结构。

Research 层级：

| 层级 | Skills |
|---|---|
| `triage` | `information-impact`、`candidate-screener`、`stock-quickread`、`next-step` |
| `foundation` | `company-primer`、`mechanism-map`、`driver-map`、`cross-market-compare` |
| `deep-work` | `peer-deep-dive`、`alpha-thesis`、`bear-pre-mortem`、`earnings-setup`、`pair-trade`、`financial-model` |
| `memory` | `research-journal` |

Operations skills：

```text
init
ingest
meta-skill
new-session
```

`meta-skill` 是创建、重写、审查和验证插件 skills 的 active 指南。`new-session` 创建或定位 topic session，解析标准保存路径，并轻量更新 topic `index.md`；不做研究，也不推荐下一研究步骤。

## Release 包

Release 包应包含插件清单、skills、用户文档、示例和 README。不得包含本地 agent 状态、私有机器配置、`.git/`、root `CLAUDE.md`、root `AGENTS.md` 或 root `scripts/`。

插件本身没有运行时 CLAUDE / AGENTS 文件。源码仓库有 root `CLAUDE.md` + `AGENTS.md` 仅供维护使用；`init-workspace` 将 workspace `CLAUDE.md` + pointer 版 `AGENTS.md` 安装到用户 research workspace。

## Research Workspace

Research workspace 是用户拥有的文件夹，由 `init-workspace` skill 创建或修复，应包含 workspace `CLAUDE.md`、pointer 版 `AGENTS.md`、`_inbox/`、`_raw/`、`_cache/`、`_models/`、`_scripts/` 和 `topics/`。原始材料由 `ingest` 转换为 `_cache/` markdown。Workspace 不等于本插件源码仓库。

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

`init-workspace` 不会运行 `git init`、安装依赖、ingest 原始文件或创建 topic 研究产物。它会复制 `_scripts/bootstrap-ingest-deps.ps1`、`_scripts/requirements-ingest.txt` 和 ingest 辅助脚本，让用户之后显式选择安装。`ingest` 只写操作类缓存文件，不创建 earned research memory。用户准备创建 topic session 或确定产物保存路径时使用 `new-session`。

## Artifact 保存策略

新研究产物应保存在 topic session 内：

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

公司基础类产物如 `company-primer.md` 遵循相同规则，仅在用户要求保存时创建。

若当前 topic session 不明确，写 artifact 前先走 `new-session`。`new-session` 可创建 session 文件夹并轻量更新 topic `index.md`，但不得写研究结论。

仅以下情况例外：仅对话类 skill（`information-impact`、`next-step`）、earned-memory 写入（`research-journal`）、外部 workbook（`financial-model`）。root 下的 `screens/`、`peers/`、`quickreads/`、`cross-market/` 为历史 / 示例目录，非 active 默认保存位置。

材料缓存产物位于：

```text
_cache/[bucket]/[source-filename].md
```

缓存文件是 source-tracked 的中间材料，既不是原始来源也不是 topic session 输出。

## Ingest 工具链

完整材料转换栈是本地方案：Docling 是主要 PDF / DOCX / PPTX 转换器，EdgarTools 用于 SEC filing 读取准备，openpyxl 处理 workbook 结构，python-pptx / python-docx 为备选提取器，PDFPlumber 交叉检查 PDF 表格数值，Tesseract 支持扫描件 OCR，MarkItDown 为旧格式的降级备选。

依赖安装是显式的：

```powershell
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
_scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

任何 skill 不得静默安装全局依赖。
