# Buy-Side Research Skills

面向买方股票研究的 Claude / Codex 插件。它把常见研究动作拆成可复用的 skills：材料 ingest、结构化财务数据拉取、driver 拆解、三表 / DCF / comps / model update、公司和行业研究、thesis、earnings、pair、research memory。

当前版本：`3.7.0`

仓库地址：`iRyantik/buy-side-research-skills`

## 核心工作流

现在的公司建模主线是：

```text
financial-data -> driver-map -> 3-statement-model / dcf-model / comps-analysis / model-update
```

三个外显产物类别：

```text
financial-data-summary.md
driver-map.md
<model-artifact>.xlsx
```

`<model-artifact>.xlsx` 可以是：

- `<ticker>-3statement-model.xlsx`
- `<ticker>-3statement-dcf-model.xlsx`
- `<ticker>-comps-analysis.xlsx`
- `<ticker>-model-update.xlsx`

JSON、full filing、source-map、completeness、raw evidence、debug 文件默认都放在 `internal/`，不作为用户和 LLM 的默认阅读入口。

## 适合做什么

- 快速判断一家公司、行业、主题或消息是否值得继续研究。
- 把 sell-side consensus、buy-side bar、priced-in assumptions 和 variant-view gap 摊开。
- 把公司业务、segment、KPI 口径、并购 / recast / disclosure evolution 梳理清楚。
- 遇到行业机制、工程原理、工艺流程或设备链条不清时，用 `mechanism-map`。
- 遇到 revenue、margin、backlog、price-volume-mix、KPI 口径不清时，用 `driver-map`。
- 按 market + identifier 拉取结构化财务数据时，用 `financial-data`。
- 搭三表、DCF、comps，或更新已有 model。
- 把 source-backed、会改变判断的认知增量沉淀成 `research-journal` 或 Boss Brief。

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

如果你的环境使用本地插件目录，也可以从 GitHub Release 下载 `buy-side-research-skills-3.7.0.zip`，解压到 Claude 或 Codex 指定插件位置。

更多安装说明见 [docs/install.md](docs/install.md)。

## 环境配置

研究类 skill 走 Claude / Codex 自身能力，通常零配置。需要本地工具链的是 `ingest` 和 `financial-data`。

基础要求：

- 美股 SEC / EdgarTools 需要 `EDGAR_IDENTITY`，格式为 `"姓名 email@domain.com"`，无需注册账号，SEC 只是要求访问者自报身份。
- 结构化财务数据依赖需要在 workspace 里显式安装：`_scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly` 后再按需 `-Yes`。

按需获取 API key：

| 市场 | Provider / route | 需要什么 | 获取方式 | 默认可信度 |
|---|---|---|---|---|
| US | SEC / EdgarTools | `EDGAR_IDENTITY` | 自己填写姓名 + 邮箱 | 官方源，三表可 model-ready |
| CN | AKShare | 无 key | 免费 Python 包 | 第三方 normalized，默认 review |
| HK | AKShare | 无 key | 免费 Python 包 | 第三方 normalized，默认 review |
| JP | EDINET | `EDINET_API_KEY` | https://disclosure2.edinet-fsa.go.jp/ 注册 / 申请 | 官方源，字段覆盖可能 partial |
| KR | OpenDART / dart-fss | `DART_API_KEY` | https://opendart.fss.or.kr/ 注册即可 | 官方源，缺 key hard fail |
| EU | openesef | 通常无 key | filing URL 或 local ESEF package | 官方 filing parser；ticker-only experimental |

把这些信息告诉 Claude / Codex，让它帮你写入 workspace 的 `_scripts/env-setup.ps1`。更多细节见 [docs/install.md](docs/install.md)。

## 第一次使用

1. 新建一个普通文件夹作为 research workspace，不要直接在本插件仓库里做日常研究。
2. 使用 `init-workspace` 初始化 workspace。它会创建 `_inbox/`、`_scripts/`、`topics/`、`edge-radar.md`，并写入 workspace `CLAUDE.md` 和 pointer 版 `AGENTS.md`。
3. 使用 `new-session` 创建 company / industry / theme / pair topic scaffold。
4. 本地 PDF、XLSX、PPTX、DOCX、CSV 等材料放入 `topics/<topic>/_inbox/`，再用 `ingest` 转成 source-tracked markdown cache。
5. 需要结构化财务数据时，用 `financial-data` 按 market + identifier 拉取。
6. 需要建模时，先用 `driver-map` 拆业务 driver，再进入 `3-statement-model`、`dcf-model`、`comps-analysis` 或 `model-update`。

## Workspace 结构

```text
[research-workspace]/
├── CLAUDE.md
├── AGENTS.md
├── _inbox/
├── _scripts/
├── edge-radar.md
└── topics/
    └── <namespace>/<topic-slug>/      # company / industry / theme / pair
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

Company topic 的 data / driver / model 输出收口：

```text
topics/company/<company-slug>/
├── _cache/
│   ├── financial-data/
│   │   ├── financial-data-summary.md
│   │   └── internal/
│   │       ├── evidence-pack.json
│   │       ├── actuals-resolved.json
│   │       ├── full-filing.md
│   │       ├── completeness.json
│   │       └── source-map.json
│   └── driver-map/
│       ├── driver-map.md
│       └── internal/
│           └── driver-map.json
└── _models/
    ├── <ticker>-3statement-model.xlsx
    ├── <ticker>-3statement-dcf-model.xlsx
    ├── <ticker>-comps-analysis.xlsx
    └── <ticker>-model-update.xlsx / <ticker>-update-map.md
```

Non-company topic 不保存 company canonical financial-data，只保存 snapshot、links 或 aggregation。

## Skills

Operations skills：

| Skill | 用途 |
|---|---|
| `init-workspace` | 创建或修复 research workspace scaffold |
| `new-session` | 创建 / 定位 topic session，解析 artifact 保存路径，轻量更新 `index.md` |
| `ingest` | 把 raw materials 转成 source-tracked markdown cache |
| `financial-data` | 按 market + identifier 拉取或解析结构化公司财务数据 evidence pack |
| `integrate` | 将子 topic 合并到父 topic 下，形成层级结构 |
| `meta-skill` | 维护本插件 skills、metadata、validators 和 governance |

Research skills：

| 层级 | Skills | 用途 |
|---|---|---|
| `triage` | `information-impact`, `candidate-screener`, `industry-quickread`, `stock-quickread`, `next-step` | 过滤信息、找候选、行业 first-pass、快速判断、识别最高杠杆下一问 |
| `foundation` | `company-primer`, `consensus-map`, `mechanism-map`, `driver-map`, `cross-market-compare` | 公司基础、预期地图、行业机制、model drivers、跨市场比较 |
| `deep-work` | `peer-deep-dive`, `primary-research-plan`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `3-statement-model`, `dcf-model`, `comps-analysis`, `model-update` | 深度研究、primary research、thesis、pre-mortem、财报、pair、建模 |
| `memory` | `research-journal` | 沉淀 earned insight 和 Boss Brief |

## 推荐研究流

行业 / 主题 first-pass：

```text
new-session -> ingest -> industry-quickread -> consensus-map -> mechanism-map
     -> candidate-screener / peer-deep-dive
     -> stock-quickread -> driver-map -> primary-research-plan
     -> alpha-thesis / model work
     -> research-journal
```

公司建模：

```text
new-session -> financial-data -> driver-map
     -> 3-statement-model
     -> dcf-model / comps-analysis
     -> model-update
```

单公司研究：

```text
new-session -> ingest / financial-data -> stock-quickread -> consensus-map
     -> company-primer / mechanism-map / driver-map
     -> peer-deep-dive / primary-research-plan
     -> alpha-thesis / model work
     -> bear-pre-mortem / earnings-setup
     -> research-journal
```

## 示例

示例文件位于：

```text
examples/
```

RKLB example 展示当前 data / driver / model 三类外显产物：

```text
examples/financial-data-pull/us/rklb/
  financial-data-summary.md
  driver-map.md
  rklb-3statement-dcf-model.xlsx
  internal/
```

示例只用于参考 artifact 形状，不是插件运行时依赖。

## 维护者说明

- Release packaging 不再默认跑全量 validators。
- 只有新增、重写或重大修改 skill 时，才跑本次相关 targeted validator。
- 用户明确说“不跑 validator”时，不跑 validator。
- `build-release.ps1` 只负责打包，不自动调用 release validator。

## 重要边界

- 插件不会替你做最终投资决策。
- `financial-data` 是 data evidence pack，不是研究结论；默认先看 `financial-data-summary.md`。
- `driver-map` 是业务 driver / model treatment，不做估值结论。
- `3-statement-model`、`dcf-model`、`comps-analysis`、`model-update` 是独立 modeling skills；不再使用旧 `financial-model`。
- JSON / full filing / source-map / completeness 默认放 `internal/`，不作为外显阅读入口。
- `research-journal` 只写已经研究清楚、关键事实有 source、会改变判断的认知增量。
- root `CLAUDE.md` / `AGENTS.md` 只服务本源码仓库维护；用户 workspace 会由 `init-workspace` 生成自己的 `CLAUDE.md` / `AGENTS.md`。
