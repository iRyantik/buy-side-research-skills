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

skill 需要调用的运行时资源放在该 skill 目录内部，例如 `skills/ingest/scripts/`、`skills/financial-data/scripts/` 或 `skills/init-workspace/assets/`。root `scripts/` 仅用于源码仓库验证和 release 打包。

## Skill 分类

Active skills 平铺在 `skills/[skill-name]/SKILL.md` 下，不按 category 物理嵌套。

顶层分类：

- `research`：投研类 skill，必须携带 Global Rules Capsule 并设置 `research_layer`。
- `operations`：workspace、缓存、路径或 skill governance 工具，使用更轻量的执行结构。

Research 层级：

| 层级 | Skills |
|---|---|
| `triage` | `information-impact`、`candidate-screener`、`industry-quickread`、`stock-quickread`、`next-step` |
| `foundation` | `company-primer`、`consensus-map`、`mechanism-map`、`driver-map`、`cross-market-compare` |
| `deep-work` | `peer-deep-dive`、`primary-research-plan`、`alpha-thesis`、`bear-pre-mortem`、`earnings-setup`、`pair-trade`、`3-statement-model`、`dcf-model`、`comps-analysis`、`model-update` |
| `memory` | `research-journal` |

Operations skills：

```text
init
ingest
financial-data
meta-skill
new-session
integrate
```

`meta-skill` 是创建、重写、审查和验证插件 skills 的 active 指南。`industry-quickread` 是行业 / 主题 first-pass triage，用来判断 current regime、value capture、KPI/source map、anchor names 和下一步路由；不替代 `mechanism-map`，也不把 `driver-map` 泛化成行业 driver 拆解。`consensus-map` 是 expectations foundation，用来拆 sell-side consensus、buy-side bar、priced-in assumptions 和 variant-view gap；不替代 `alpha-thesis`、`3-statement-model / dcf-model / comps-analysis / model-update` 或 `earnings-setup`。`primary-research-plan` 设计合规 expert call、channel check、survey 和 fieldwork 计划；不执行访谈、不生成假反馈、不替代 compliance 流程。`new-session` 创建或定位 topic session，解析标准保存路径，并轻量更新 topic `index.md`；不做研究，也不推荐下一研究步骤。

## Release 包

Release 包实际只包含 `.claude-plugin/`、`.codex-plugin/`、`skills/` 和 `README.md`。不得包含 `docs/`、`examples/`、本地 agent 状态、私有机器配置、`.git/`、root `CLAUDE.md`、root `AGENTS.md` 或 root `scripts/`。

插件本身没有运行时 CLAUDE / AGENTS 文件。源码仓库有 root `CLAUDE.md` + `AGENTS.md` 仅供维护使用；`init-workspace` 将 workspace `CLAUDE.md` + pointer 版 `AGENTS.md` 安装到用户 research workspace。

## Research Workspace

Research workspace 是用户拥有的文件夹，由 `init-workspace` skill 创建或修复，应包含 workspace `CLAUDE.md`、pointer 版 `AGENTS.md`、`_inbox/`、`_scripts/`、`edge-radar.md` 和 `topics/`。`_raw/`、`_cache/`、`_models/` 现在属于 `topics/<namespace>/<topic-slug>/` 内部，不再作为 workspace root 目录。原始材料由 `ingest` 转换为 topic `_cache/` markdown；结构化财务数据由 `financial-data` 写为 company canonical evidence pack。Workspace 不等于本插件源码仓库。

```text
[research-workspace]/
├── CLAUDE.md
├── AGENTS.md
├── _inbox/                          # 暂存区（支持 <topic>/ 子目录）
├── _scripts/                        # 辅助脚本
├── edge-radar.md                    # 跨主题雷达
└── topics/
    └── <namespace>/<topic-slug>/    # company / industry / theme / pair
        ├── index.md
        ├── _inbox/                  # topic 专属暂存
        ├── _raw/                    # 原始源文件
        │   ├── filings/
        │   ├── transcripts/
        │   ├── sellside/
        │   ├── industry/
        │   ├── irdecks/
        │   └── datasets/
        ├── _cache/                  # 转换后 markdown / financial-data evidence packs
        ├── _models/                 # 财务模型
        └── <YYYY-MM-DD>-<session>/  # 研究 session
```

`init-workspace` 不会运行 `git init`、安装依赖、ingest 原始文件、拉取 financial-data 或创建 topic 研究产物。它会复制 ingest 和 financial-data 辅助脚本，让用户之后显式选择安装。`new-session` 创建 topic scaffold（含 `_inbox/`、`_raw/{filings,transcripts,sellside,industry,irdecks,datasets}/`、`_cache/`、`_models/`）并轻量更新 topic `index.md`。`ingest` 从 `topics/<topic>/_inbox/` 读取文件，转换后自动移至 `topics/<topic>/_raw/<category>/`，按文档类别组织，不创建 earned research memory。`financial-data` 默认写入 `topics/company/<company-slug>/_cache/datasets/financial-data/`，theme / industry topic 只保存 snapshot 或 links。用户准备创建 topic session 或确定产物保存路径时使用 `new-session`。

Company topic 的 modeling input 收口为：

```text
topics/company/<company-slug>/
  _cache/
    financial-data/
      financial-data-summary.md
      internal/
        evidence-pack.json
        actuals-resolved.json
        full-filing.md
    driver-map/
      driver-map.md
      internal/
        driver-map.json
  _models/
    <ticker>-3statement-model.xlsx
    <ticker>-3statement-dcf-model.xlsx
    <ticker>-comps-analysis.xlsx
    <ticker>-model-update.xlsx / <ticker>-update-map.md
```

Non-company topic 不保存 company canonical financial-data，只保存 snapshot、links 或 aggregation。

## Artifact 保存策略

新研究产物应保存在 topic session 内：

```text
topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md
```

行业、公司、预期地图和 primary research 计划产物如 `industry-quickread.md`、`company-primer.md`、`consensus-map.md`、`primary-research-plan.md` 遵循相同规则，仅在用户要求保存时创建。

若当前 topic session 不明确，写 artifact 前先走 `new-session`。`new-session` 可创建 session 文件夹并轻量更新 topic `index.md`，但不得写研究结论。

仅以下情况例外：仅对话类 skill（`information-impact`、`next-step`）、earned-memory 写入（`research-journal`）、外部 workbook / update map（`3-statement-model`、`dcf-model`、`comps-analysis`、`model-update`）。root 下的 `screens/`、`peers/`、`quickreads/`、`cross-market/` 为历史 / 示例目录，非 active 默认保存位置。

材料缓存产物位于：

```text
topics/<topic-slug>/_cache/[source-filename].md
```

缓存文件是 source-tracked 的中间材料，既不是原始来源也不是 topic session 输出。

结构化财务数据缓存位于：

```text
topics/company/<company-slug>/_cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/
```

必须包含 `manifest.json`、`financials.md`、`financials.normalized.json`、`completeness.json` 和 `source-map.json`。`3-statement-model / dcf-model / comps-analysis / model-update` 使用前必须检查 completeness 和 source map。

建模入口同时提供稳定短路径。外显层只放 Markdown summary，机器输入和审计索引进入 `internal/`：

```text
topics/company/<company-slug>/_cache/financial-data/
  financial-data-summary.md
  internal/
    evidence-pack.json
    actuals-resolved.json
    full-filing.md
    completeness.json
    source-map.json
```

`financial-data-summary.md` 是人和 LLM 默认入口；`internal/actuals-resolved.json` 是 modeling skills 读取 historical actuals 的推荐机器入口；missing / unmapped 字段不得写成 0。`driver-map` 同样外显 `driver-map.md`，机器 JSON 放 `internal/driver-map.json`。

## Ingest 工具链

PDF 双层路由：**PyMuPDF4LLM**（CPU 即可，10-50x 速度，适合文字为主文档）和 **docling**（258M VLM，MIT 许可证，适合表格密集型文档）。SEC filing 走 EdgarTools + docling。扫描件走 docling → PyMuPDF4LLM fallback，标注 Claude Vision review caveat。Excel 用 openpyxl 双加载。PPTX / DOCX 优先 docling，python-pptx / python-docx 为备选提取器。PDFPlumber 交叉检查 PDF 表格数值。旧格式 .xls 需用户先转为 .xlsx。

按市场结构化财务数据不属于 `ingest`；使用 `financial-data`。V1 provider route 包括 SEC/EdgarTools、AKShare、EDINET、DART 和 openesef/ESEF，其中欧洲 ticker-only discovery 标 experimental，可靠路线是 filing URL 或 local ESEF package。

已移除：Tesseract（OCR 由 Claude Vision 覆盖）、MarkItDown[all]（太重，无价值 extras）。

依赖安装是显式的：

```powershell
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
_scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

结构化财务数据依赖安装也是显式的：

```powershell
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes
```

任何 skill 不得静默安装全局依赖。
