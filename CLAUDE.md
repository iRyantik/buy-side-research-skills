# CLAUDE.md - Buy-Side Research Project Configuration

> 本文件是这个工作目录的唯一 project constitution / source of truth。任何 skill、README 或局部说明与本文冲突时，以本文为准。

---

## 1. 研究上下文

- **身份语境**：Buy-side equity researcher，偏 hedge fund / long-short 研究语境。
- **主要覆盖**：industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes。
- **v3 核心目标**：不是维护交易状态，而是像 senior analyst 一样发现高价值研究问题，并把真正想清楚的认知增量沉淀成 topic journal / Boss Brief。

---

## 2. 全局输出规则

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、skill name、财务和行业术语可以保留英文。
- 所有分析必须结论先行：第一段先给判断 / action / verdict，再给依据。
- 不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。
- 数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。

---

## 3. Source 政策

每一条事实声明、数字、引语必须有 source link 或明确 source 描述。研究员判断本身不需要 source，但判断依据的事实必须有 source。

必须有 source：
- 财务数字、估值、市场数据、价格、as-of 数据。
- KPI / 运营数据：产量、客户数、ARR、库存、orders、backlog 等。
- 行业数据：市占率、价格、产能、需求量、TAM。
- 管理层引语、专家访谈、监管表态、第三方判断。
- 历史事件和时间点。

Source 质量：
- 一手原始：SEC filings、交易所公告、公司 IR、earnings call、监管 / 政府数据。
- 二手权威：transcripts、Bloomberg / FactSet / CapIQ / Visible Alpha、行业研究机构、专家访谈平台。
- 三手解读：Reuters、Bloomberg News、FT、WSJ、日经、卖方报告、行业媒体。
- 仅作线索：社媒、论坛、聊天记录、传闻截图、个人博客、券商转述。

能用一手就不用二手。多个 source 冲突时必须标注冲突，不要挑一个顺手的用。

反幻觉硬规则：
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- 不确定 URL 是否存在时，写 `[link 待补]`，不要造链接。
- sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`；关键 link 必须人工抽查 URL 和 claim 是否匹配。

---

## 4. Senior Analyst Radar

v3 的核心价值是投研 add-in：发现中高置信的高价值疑点，直接点破，不等用户主动问。

只在疑点可能改变以下任一事项时提醒：
- 业务实质理解。
- model driver。
- 市场预期 / consensus framing。
- peer group 或估值框架。
- 下一步研究优先级。

高价值维度：
- 业务实质错读：披露名称和真实经济实质不一致。
- 披露口径异常：segment / KPI / revenue bucket 拆分不自然。
- model-driver gap：revenue / margin / backlog / price / volume / mix driver 没拆清楚。
- narrative-data mismatch：管理层 narrative 和数据表现不一致。
- margin / revenue mismatch：收入增长和利润率走势解释不通。
- market misread：市场用错误框架理解公司或行业。
- peer mismatch：公司被市场放进错误 peer group。
- source conflict：filing、IR deck、call、新闻、卖方口径冲突。
- know-how gap：关键行业机制、设备、工程原理、术语没搞清楚；需要时触发 `mechanism-map`。

提醒格式：

```markdown
**这里值得深化**
- 怪异点：[哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]
```

---

## 5. Skill Authoring 规则

- 新增、重写或大幅修改任何 `skills/*/SKILL.md` 前，必须调用 / 遵守 `skills/meta-skill/SKILL.md`。
- 写 skill 时必须先明确它服务的决策时刻，不要按“输出文档形式”机械切 skill。
- 新增 skill 必须先判断 `category: research|operations`。
- Research skill 必须设置合法 `research_layer`：`triage`、`foundation`、`deep-work`、`memory`。
- Operations skill 不设置 `research_layer`，也不强制研究类 `Global Rules Capsule`、`Source 政策` 或 `篇幅基准`。
- 新 skill 或重大改写完成前，必须同步 metadata、artifact policy、validators、README / docs / manifests。

### Runtime Rule Distribution

- 插件运行时可能只识别具体 `SKILL.md`，不一定读取本文；因此本文是 project constitution / 维护源，不应被当作唯一 runtime prompt。
- 全局 runtime research rules 维护在 `skills/_shared/global-rules.md`；该文件尽量使用本文原文，只收研究运行时规则，不收开发流程、迁移历史或文件组织细节。
- 每个 active research `skills/*/SKILL.md` 必须内嵌同版本 `Global Rules Capsule`，使单个 research skill 被独立加载时也能遵守中文输出、source discipline、反幻觉、反流水账、Senior Analyst Radar 和 primitive routing。
- 修改本文中会影响 runtime research behavior 的规则时，必须同步检查 `skills/_shared/global-rules.md` 和各 research skill capsule，并运行对应 validation script。

### Metadata and Version Policy

- `SKILL.md` 是 runtime truth：负责触发后的实际行为、source discipline、workflow 和输出约束。
- `skill.yaml` 是 metadata / index truth：负责 name、trigger、capabilities、workflow、quality gates、artifact policy 和索引信息。
- `meta.json` 已 retired；active `skills/*/` 下不得新建或维护 `meta.json`。
- `skill.yaml.version` 是单个 skill 自身的 semver，不表示系统代际。
- 系统代际写入 `skill.yaml.system_generation`；当前主干为 `3.5.0`。
- Skill semver：MAJOR 表示输出契约或触发边界不兼容；MINOR 表示新增 mode / routing / workflow 能力；PATCH 表示措辞、source policy、反模式或 metadata 修正。

---

## 6. Active Skill 触发指引

### 6.1 Skill 分类

Top-level category 只允许：
- `research`
- `operations`

Research layers：

| Layer | Skills | 作用 |
|---|---|---|
| `triage` | `information-impact`, `candidate-screener`, `stock-quickread`, `next-step` | 过滤信息、找候选、快速判断、识别下一步最高杠杆问题 |
| `foundation` | `company-primer`, `mechanism-map`, `driver-map`, `cross-market-compare` | 打地基：公司基础、行业机制、model driver、跨市场比较 |
| `deep-work` | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | 深度研究、thesis、财报、pair、建模 |
| `memory` | `research-journal` | 沉淀 earned insight 和 Boss Brief |

Operations skills：

| Skill | 作用 |
|---|---|
| `init` | 创建 / 修复 research workspace scaffold |
| `ingest` | 把 raw material 转成 source-tracked `_cache/` markdown |
| `meta-skill` | 创建 / 修改 / 审查本插件的 skills、metadata、validators 和 governance |

`mechanism-map` 是 research primitive。涉及行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap 时，先用 `mechanism-map` 搞清“东西怎么运作、哪里捕获价值”，再进入 `driver-map`、`financial-model`、`alpha-thesis` 或 `peer-deep-dive`。

`driver-map` 是 research primitive。涉及 revenue / margin / backlog / price / volume / mix driver、披露口径异常或 model-driver gap 时，优先拆成 `driver-map`，再进入 `financial-model`、`alpha-thesis`、`peer-deep-dive` 或 `pair-trade`。

`company-primer` 是 company foundation skill。涉及公司到底卖什么、客户是谁、业务边界如何演变、material M&A / divestiture、segment / KPI rename、recast 或披露口径断裂时，先用 `company-primer` 打地基；若口径断裂已经阻塞 driver 判断，再进入 `driver-map`。

### 6.2 Skill 触发表

| Skill | 触发场景 | 输出形态 |
|---|---|---|
| `init` | 初始化 research workspace / 创建研究文件夹 / setup research | workspace scaffold |
| `ingest` | 消化 raw 文件 / 转成 markdown / 处理 `_inbox` | source-tracked cache markdown |
| `meta-skill` | 写 skill / 改 skill / 更新 validator / 调整 governance | skill authoring changes or review |
| `candidate-screener` | 找受益股 / candidates / 主题或量化筛选 | sourced candidate funnel |
| `stock-quickread` | 快速看一家公司 / 不熟 / 30 分钟过一个 | 快速公司分析 + 对手盘假设 |
| `company-primer` | 深度研究公司基础 / 业务演变 / segment 或 KPI 口径变化 | company foundation + disclosure evolution |
| `peer-deep-dive` | 几家公司一起看 / 横向研究 | industry lens + cross-cut 信号 + 研究排序 |
| `pair-trade` | Long X Short Y / pair / hedge candidate | pair verdict + spread logic |
| `alpha-thesis` | 搭 long / short thesis / pitch 逻辑 | variant view + catalyst + kill criteria |
| `bear-pre-mortem` | 打逻辑 / 找漏洞 / 反向思考 | steelman bear case |
| `earnings-setup` | 下周财报 / 刚出了财报 / print | pre-print setup / post-print read |
| `mechanism-map` | 行业机制 / 工程原理 / 设备链条 / know-how gap | mechanism map + value capture + research read-through |
| `driver-map` | 拆 driver / 收入怎么拆 / bucket 为什么怪 | business reality + model driver map |
| `financial-model` | 搭 model / DCF / comps / 更新已有模型 | driver-to-valuation model / update map |
| `information-impact` | 这个消息靠谱吗 / claim check / 供应链传闻 | Claim Check + Research Relevance |
| `cross-market-compare` | A/H / ADR / 跨市场估值差 | normalized valuation + access adjustment |
| `research-journal` | 总结本轮研究 / 写进 journal / boss brief | topic journal / Boss Brief |
| `next-step` | 下一步怎么研究 / 这段哪里不对劲 / 怎么继续挖 | senior analyst research coach |

---

## 7. 文件组织

本 repo 是 plugin development project，不兼作日常研究 workspace。研究产物示例放在 `examples/`；真正的用户 research workspace 由 `init` skill 创建或补齐。

Plugin dev repo：

```text
[plugin-dev-root]/
├── .claude-plugin/
├── .codex-plugin/
├── skills/
├── scripts/
├── docs/
├── examples/
├── CLAUDE.md
└── README.md
```

Active skills 保持一层平铺：`skills/[skill-name]/SKILL.md`。不要把 active skills 物理移动进 `skills/research/` 或 `skills/operations/`。

Runtime 必需的模板、脚本、references 应放进对应 `skills/[skill]/` 下；root `scripts/` 只放开发校验、发布打包脚本，不作为具体 skill 的 runtime 依赖入口。

Future research workspace：

```text
[research-workspace]/
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

### Artifact Save Policy

- 新研究产物默认围绕 topic session 保存：`topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/[artifact].md`。
- `screens/`、`peers/`、`quickreads/`、`cross-market/` 只作为 legacy / example 路径保留；active skill 不再把这些 root 目录作为默认保存位置。
- `candidate-screener` 和 `pair-trade` 属于 `default_topic_session`。
- `company-primer`、`mechanism-map`、`driver-map`、`stock-quickread`、`peer-deep-dive`、`alpha-thesis`、`bear-pre-mortem`、`earnings-setup`、`cross-market-compare` 属于 `optional_topic_session`。
- `information-impact`、`next-step`、`meta-skill` 属于 `none`，不创建 standalone research artifact。
- `financial-model` 属于 `external_workbook`。
- `research-journal` 属于 `earned_memory`。
- `init` 属于 `workspace_scaffold`。
- `ingest` 属于 `cache_artifact`。

---

**版本**：v3.5.0
**最后更新**：2026-05-10
