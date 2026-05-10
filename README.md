# Buy-Side Research Skills

一个面向买方股票研究的 Claude / Codex 插件。它把常见研究动作拆成可复用的 skills：快速判断、公司基础研究、行业机制拆解、model driver 拆解、同业比较、thesis / pre-mortem / earnings 工作、研究记忆沉淀，以及 workspace 初始化和材料 ingest。

当前开发线：`3.5.0-dev`

稳定发布基线：`v3.4.0`

仓库地址：`iRyantik/buy-side-research-skills`

## 适合做什么

- 快速判断一家公司或一条信息是否值得继续研究。
- 把公司历史、业务构成、segment / KPI 口径变化梳理清楚。
- 遇到行业机制、工程原理、工艺流程或设备链条不清时，触发 `mechanism-map`。
- 遇到 revenue、margin、backlog、price-volume-mix、KPI 披露口径不清时，触发 `driver-map`。
- 做 peer deep dive、alpha thesis、bear pre-mortem、earnings setup、pair trade 和 financial model。
- 把已经研究过、source-backed、会改变判断的认知增量沉淀成 `research-journal` 或 Boss Brief。

## 安装

Claude 插件市场可用时：

```powershell
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

Codex 插件市场可用时：

```powershell
codex plugin marketplace add iRyantik/buy-side-research-skills
```

如果你的环境使用本地插件目录，也可以从 GitHub Release 下载 `buy-side-research-skills-3.4.0.zip`，解压到 Claude 或 Codex 指定的插件位置。

更多安装说明见 [docs/install.md](docs/install.md)。

## 第一次使用

1. 新建一个普通文件夹作为 research workspace，不要直接在本插件仓库里做研究。
2. 使用 `init` 初始化 workspace。它会创建 `_inbox/`、`_raw/`、`_cache/`、`_models/`、`_scripts/`、`topics/`，并写入 workspace `CLAUDE.md` 和 pointer 版 `AGENTS.md`。
3. 如需转换本地材料，先在 workspace 中运行 `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly` 查看依赖状态，再按需显式运行 `-Yes` 安装 ingest 依赖。
4. 使用 `new-session` 创建或定位 topic session，再让研究类 skill 保存 artifact。
5. 把 raw materials 放入 `_raw/` 或 `_inbox/`，用 `ingest` 转成 `_cache/` markdown；`_cache/` 是中间材料，不是研究结论。

标准 workspace 形状：

```text
[research-workspace]/
├── CLAUDE.md
├── AGENTS.md
├── _inbox/
├── _raw/
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

topic session 形状：

```text
topics/[company|theme|event]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/
```

## Skill 分类

Operations skills：

| Skill | 用途 |
|---|---|
| `init` | 创建或修复 research workspace scaffold |
| `ingest` | 把 raw materials 转成 source-tracked `_cache/` markdown |
| `new-session` | 创建 / 定位 topic session，解析 artifact 保存路径，轻量更新 topic `index.md` |
| `meta-skill` | 维护本插件的 skills、metadata、validators 和 governance |

Research skills：

| 层级 | Skills | 用途 |
|---|---|---|
| `triage` | `information-impact`, `candidate-screener`, `stock-quickread`, `next-step` | 过滤信息、找候选、快速判断、识别最高杠杆下一问 |
| `foundation` | `company-primer`, `mechanism-map`, `driver-map`, `cross-market-compare` | 公司基础、行业机制、model drivers、跨市场比较 |
| `deep-work` | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | 深度研究、thesis、pre-mortem、财报、pair、建模 |
| `memory` | `research-journal` | 沉淀 earned insight 和 Boss Brief |

## 推荐研究流

```text
init -> ingest -> new-session -> stock-quickread / company-primer
     -> mechanism-map / driver-map
     -> peer-deep-dive / alpha-thesis / bear-pre-mortem / earnings-setup
     -> research-journal / Boss Brief
```

遇到保存路径不清，先用 `new-session`。遇到机制不清，先用 `mechanism-map`。遇到 driver 或披露口径不清，先用 `driver-map`。不要把未经验证的疑点直接写进 `research-journal`。

## 示例

示例 workspace 位于：

```text
examples/workspaces/ai-data-center-power/
```

示例只用于参考 artifact 形状，不是插件运行时依赖。

## 重要边界

- 插件不会替你做最终投资决策。
- `init` 不会运行 `git init`、不会安装依赖、不会 ingest 文件、不会写研究结论。
- `ingest` 只写 `_cache/` 中间材料，不写 thesis 或 journal。
- `research-journal` 只写已经研究清楚、关键事实有 source、会改变判断的认知增量。
- root `CLAUDE.md` / `AGENTS.md` 只服务本源码仓库维护；用户 workspace 会由 `init` 生成自己的 `CLAUDE.md` / `AGENTS.md`。
