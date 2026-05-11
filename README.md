# Buy-Side Research Skills

一个面向买方股票研究的 Claude / Codex 插件。它把常见研究动作拆成可复用的 skills：快速判断、公司基础研究、行业机制拆解、model driver 拆解、同业比较、thesis / pre-mortem / earnings 工作、研究记忆沉淀，以及 workspace 初始化和材料 ingest。

当前版本：`3.7.0`

仓库地址：`iRyantik/buy-side-research-skills`

## 适合做什么

- 快速判断一家公司或一条信息是否值得继续研究。
- 快速判断一个行业 / 主题 / value chain 是否值得继续研究，并找到下一步研究入口。
- 把 sell-side consensus、buy-side bar、priced-in assumptions 和 variant-view gap 摊开，判断市场到底在信什么。
- 把 thesis / driver gap 变成合规的 expert call、channel check、survey 和 fieldwork 计划。
- 把公司历史、业务构成、segment / KPI 口径变化梳理清楚。
- 遇到行业机制、工程原理、工艺流程或设备链条不清时，触发 `mechanism-map`。
- 遇到公司 / segment / 产品线 / 披露 bucket 的 revenue、margin、backlog、price-volume-mix、KPI 口径不清时，触发 `driver-map`。
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

如果你的环境使用本地插件目录，也可以从 GitHub Release 下载 `buy-side-research-skills-3.7.0.zip`，解压到 Claude 或 Codex 指定的插件位置。

更多安装说明见 [docs/install.md](docs/install.md)。

## 环境配置

研究类 skill 走 Claude 自身能力，**零配置**。

只有 `ingest` 转换美股 SEC filing 时需要提供 **EDGAR_IDENTITY**（格式 `"姓名 email@domain.com"`，无需注册账号，SEC 只是要求访问者自报身份）。

**按需获取**：

| 市场 | 需要什么 | 在哪获取 |
|---|---|---|
| 韩国 | DART API Key（免费） | https://opendart.fss.or.kr/ 注册即可 |

把上面的信息告诉 Claude，让它帮忙配。更多细节见 [docs/install.md](docs/install.md)。

## 第一次使用

1. 新建一个普通文件夹作为 research workspace，不要直接在本插件仓库里做研究。
2. 使用 `init-workspace` 初始化 workspace。它会创建 `_inbox/`、`_scripts/`、`topics/` 和 `edge-radar.md`，并写入 workspace `CLAUDE.md` 和 pointer 版 `AGENTS.md`。
3. 如需转换本地材料，先在 workspace 中运行 `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly` 查看依赖状态，再按需显式运行 `-Yes` 安装 ingest 依赖。
4. 使用 `new-session` 创建 topic scaffold（含 `_inbox/`、`_raw/{filings,transcripts,sellside,industry,irdecks,datasets}/`、`_cache/`、`_models/`），再让研究类 skill 保存 artifact。
5. 把 raw materials 放入 `topics/<topic>/_inbox/`，用 `ingest` 转成 `topics/<topic>/_cache/` markdown；`_cache/` 是中间材料，不是研究结论。

标准 workspace 形状：

```text
[research-workspace]/
├── CLAUDE.md
├── AGENTS.md
├── _inbox/
├── _scripts/
├── edge-radar.md
└── topics/
    └── <topic-slug>/
        ├── index.md
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
        └── <YYYY-MM-DD>-<session>/
```

topic session 形状：

```text
topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/
```

## Skill 分类

Operations skills：

| Skill | 用途 |
|---|---|
| `init-workspace` | 创建或修复 research workspace scaffold |
| `ingest` | 把 raw materials 转成 source-tracked markdown 到 `topics/<topic>/_cache/` |
| `new-session` | 创建 / 定位 topic session，解析 artifact 保存路径，轻量更新 topic `index.md` |
| `integrate` | 将子 topic 合并到父 topic 下，形成层级结构 |
| `meta-skill` | 维护本插件的 skills、metadata、validators 和 governance |

Research skills：

| 层级 | Skills | 用途 |
|---|---|---|
| `triage` | `information-impact`, `candidate-screener`, `industry-quickread`, `stock-quickread`, `next-step` | 过滤信息、找候选、行业 first-pass、快速判断、识别最高杠杆下一问 |
| `foundation` | `company-primer`, `consensus-map`, `mechanism-map`, `driver-map`, `cross-market-compare` | 公司基础、预期地图、行业机制、model drivers、跨市场比较 |
| `deep-work` | `peer-deep-dive`, `primary-research-plan`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | 深度研究、primary research、thesis、pre-mortem、财报、pair、建模 |
| `memory` | `research-journal` | 沉淀 earned insight 和 Boss Brief |

## 推荐研究流

行业 / 主题 first-pass：

```text
new-session -> ingest -> industry-quickread -> consensus-map -> mechanism-map
     -> candidate-screener / peer-deep-dive
     -> stock-quickread -> driver-map -> primary-research-plan
     -> alpha-thesis / financial-model -> research-journal / Boss Brief
```

新股 / 单公司 first-pass：

```text
new-session -> ingest -> stock-quickread -> consensus-map
     -> company-primer / mechanism-map / driver-map
     -> peer-deep-dive / primary-research-plan
     -> alpha-thesis / financial-model / bear-pre-mortem / earnings-setup
     -> research-journal / Boss Brief
```

遇到保存路径不清，先用 `new-session`。遇到行业 / 主题 first-pass，先用 `industry-quickread`。遇到市场预期、buy-side bar、priced-in assumptions 或 variant-view gap 不清，先用 `consensus-map`。遇到机制不清，先用 `mechanism-map`。遇到公司、segment、产品线或披露 bucket 到 model driver 的映射不清，才用 `driver-map`；`driver-map` 不是泛行业 driver skill。遇到需要 expert call、customer / supplier channel check、survey 或 fieldwork 验证关键假设，用 `primary-research-plan`。不要把未经验证的疑点直接写进 `research-journal`。

## 示例

示例 workspace 位于：

```text
examples/workspaces/ai-data-center-power/
```

示例只用于参考 artifact 形状，不是插件运行时依赖。

## 重要边界

- 插件不会替你做最终投资决策。
- `init-workspace` 只创建 workspace 根级 scaffold；topic 完整骨架由 `new-session` 创建。
- `ingest` 前必须 `new-session` 创建 topic；文件放入 `topics/<topic>/_inbox/`，ingest 后归类到 `_raw/<category>/`。
- `research-journal` 只写已经研究清楚、关键事实有 source、会改变判断的认知增量。
- root `CLAUDE.md` / `AGENTS.md` 只服务本源码仓库维护；用户 workspace 会由 `init-workspace` 生成自己的 `CLAUDE.md` / `AGENTS.md`。
