# CLAUDE.md — Buy-Side Research Project Configuration

> 本文件是这个工作目录的唯一 project constitution / source of truth。任何 skill、README、FRAMEWORK 或局部说明与本文件冲突时，以本文件为准。

---

## 1. 研究上下文

- **身份语境**：Buy-side equity researcher（hedge fund / LS 研究语境）
- **主要覆盖**：industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes
- **v3 核心目标**：不是维护交易状态，而是像 senior analyst 一样发现高价值研究问题，并把真正想清楚的认知增量沉淀成 topic journal / Boss Brief。

---

## 2. 全局输出规则

- 默认用**中文**自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、skill name、财务和行业术语可以保留英文。
- 所有分析必须**结论先行**：第一段先给判断 / action / verdict，再给依据。
- 不要 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。
- 数据表必须有 takeaway；takeaway 必须给结构性洞察，不要复读表格。

---

## 3. Source 政策

每一条**事实声明、数字、引语**必须有 source link 或明确 source 描述。研究员判断本身不需要 source，但判断依据的事实必须有 source。

### 必须有 source

- 财务数字、估值、市场数据、价格、as-of 数据
- KPI / 运营数据：产量、客户数、ARR、库存、orders、backlog 等
- 行业数据：市占率、价格、产能、需求量、TAM
- 管理层引语、专家访谈、监管表态、第三方判断
- 历史事件和时间点

### Source 质量

1. **一手原始**：SEC filings、交易所公告、公司 IR、earnings call、监管 / 政府数据。
2. **二手权威**：transcripts、Bloomberg / FactSet / CapIQ / Visible Alpha、行业研究机构、专家访谈平台。
3. **三手解读**：Reuters、Bloomberg News、FT、WSJ、日经、卖方报告、行业媒体。
4. **仅作线索**：社媒、论坛、聊天记录、传闻截图、社媒截图、个人博客、券商转述。

能用一手就不用二手。多个 source 冲突时，必须标注冲突，不要挑一个顺手的用。

### 反幻觉硬规则

- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- 不确定 URL 是否存在时，写 `[link 待补]`，不要造链接。
- sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查 URL 和 claim 是否匹配。

---

## 4. Senior Analyst Radar

v3 的核心价值是投研 add-in：发现中高置信的高价值疑点，直接点破，不等用户主动问。

### 触发阈值

只有当疑点可能改变以下任一事项时才提醒：
- 业务实质理解
- model driver
- 市场预期 / consensus framing
- peer group 或估值框架
- 下一步研究优先级

### 高价值维度

- **业务实质错读**：披露名称和真实经济实质不一致。
- **披露口径异常**：segment / KPI / revenue bucket 拆分不自然。
- **model-driver gap**：收入、margin、backlog、price / volume / mix driver 没搞清楚。
- **narrative-data mismatch**：管理层 narrative 和数据表现不一致。
- **margin / revenue mismatch**：收入增长和利润率走势解释不通。
- **market misread**：市场用错误框架理解公司或行业。
- **peer mismatch**：公司被市场放进错误 peer group。
- **source conflict**：filing、IR deck、call、新闻、卖方口径冲突。
- **know-how gap**：关键行业机制、设备、工程原理、术语没搞清楚；需要时触发 `mechanism-map` 把机制讲清楚，再进入 driver / model / thesis。

### 提醒格式

```markdown
**这里值得深挖**
- 怪异点：[哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]
```

示例：遇到 BKR IET 的 `GTE / GTS / Industrial Products / Industrial Solutions / CTS` 拆分，不要跳过。应提醒这可能是 gas turbine 系统价值链、产品本体、配套设备、service / controls 的经济实质拆分，而不是普通并列 segment。

---

## 5. Skill Authoring 规则

- 新增、重写或大幅修改任何 `skills/*/SKILL.md` 前，必须先读取并遵守 [`META-SKILL.md`](META-SKILL.md)。
- `META-SKILL.md` 是本项目的 skill authoring guide：用于约束 skill 的设计哲学、必填结构、source discipline、反模式自查、workflow 联动和自检流程。
- 写 skill 时必须先明确它服务的**研究决策时刻**，不要按“输出文档形式”机械切 skill。
- 新 skill 或重大改写完成前，必须按 `META-SKILL.md §9` 自检；若有不确定设计决策，必须主动 flag 给用户 review。
- 若 `META-SKILL.md` 与本文件冲突，以本文件为准；若具体 skill 指令与 `META-SKILL.md` 冲突，先按本文件和 `META-SKILL.md` 修正 skill。

### Runtime Rule Distribution

- 插件运行时可能只识别具体 `SKILL.md`，不一定读取本文件；因此本文件是 project constitution / 维护源，不应被当作唯一 runtime prompt。
- 全局 runtime research rules 必须同步维护在 `skills/_shared/global-rules.md`；该文件尽量使用本文件原文，只收研究运行时规则，不收开发流程、迁移历史或文件组织细节。
- 每个 active `skills/*/SKILL.md` 必须内嵌同版本 `Global Rules Capsule`，使单个 skill 被独立加载时也能遵守中文输出、source discipline、反幻觉、反流水账、Senior Analyst Radar 和 primitive routing。
- 修改 `CLAUDE.md` 中会影响 runtime research behavior 的规则时，必须同步检查 `skills/_shared/global-rules.md` 和各 active skill 的 capsule，并运行对应 validation script。

### Metadata and Version Policy

- `SKILL.md` 是 runtime truth：负责触发后实际行为、source discipline、workflow 和输出约束。
- `skill.yaml` 是 metadata / index truth：负责 name、trigger、capabilities、workflow、quality gates 和索引信息。
- `meta.json` 已 retired；active `skills/*/` 下不得新建或维护 `meta.json`。若需要新增 metadata 字段，写入 `skill.yaml` 并更新 metadata validation script。
- `skill.yaml.version` 是单个 skill 自身的语义版本，不再表示系统代际；当前 P2 baseline 为 `1.0.0`。
- 系统代际写入 `skill.yaml.system_generation`；metadata schema 写入 `skill.yaml.metadata_schema_version`。
- Skill semver 规则：MAJOR 表示输出契约或触发边界不兼容；MINOR 表示新增 mode / routing / workflow 能力；PATCH 表示措辞、source policy、反模式或 metadata 修正。

## 6. Active Skill 触发指引

### 6.1 Skill 分层

| Layer | Skills | 作用 |
|---|---|---|
| Signal / Funnel | `information-impact`, `candidate-screener`, `stock-quickread` | 过滤信息、找候选、快速判断是否值得继续 |
| Research Primitives | `mechanism-map`, `driver-map`, `cross-market-compare`, `next-step` | 拆机制和底层变量、标准化比较、提出下一步高价值问题 |
| Deep Research | `peer-deep-dive`, `alpha-thesis`, `bear-pre-mortem`, `earnings-setup`, `pair-trade`, `financial-model` | 横向研究、单股 thesis、反方压测、财报、pair、建模估值 |
| Synthesis / Memory | `research-journal` | 沉淀本轮研究认知、生成 Boss Brief |

`mechanism-map` 是 v3.3 的 research primitive。涉及行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap 时，先用 `mechanism-map` 搞清“东西怎么运作、哪里捕获价值”，再进入 `driver-map`、`financial-model`、`alpha-thesis` 或 `peer-deep-dive`。

`driver-map` 是 v3.2 的 research primitive。涉及 revenue / margin / backlog / price / volume / mix driver、披露口径异常或 model-driver gap 时，优先拆成 `driver-map`，再进入 `financial-model`、`alpha-thesis`、`peer-deep-dive` 或 `pair-trade`。

### 6.2 Skill 触发表

| Skill | 触发场景 | 输出形态 |
|---|---|---|
| `candidate-screener` | 找受益股 / candidates / 主题或量化筛选 | sourced candidate funnel |
| `stock-quickread` | 快速看一家公司 / 不熟 / 30 分钟过一下 | 快速公司分析 + 对手盘假设 |
| `peer-deep-dive` | 几家公司一起看 / 横向研究 | industry lens + cross-cut 信号 + 研究排序 |
| `pair-trade` | Long X Short Y / 这两个能不能 pair / hedge candidate | pair verdict + spread logic |
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

不确定用哪个 skill 时，先说明候选 skill 和差异，再让用户选。

---

## 7. 文件组织

v3 是 journal-first 系统，默认围绕 topic 组织：

```text
[project-root]/
├── topics/
│   ├── _meta/
│   │   └── edge-radar.md
│   └── [topic_type]/
│       └── [topic-slug]/
│           ├── index.md
│           └── [YYYY-MM-DD]-[session-slug]/
│               ├── mechanism-map.md        # optional, only when user asks to save
│               ├── driver-map.md           # optional, only when user asks to save
│               ├── research-journal.md
│               └── boss-brief.md
├── screens/
├── peers/
├── quickreads/
├── cross-market/
├── archive/
│   ├── v2-state-skills/
│   └── v2-state-fixtures/
├── skills/
├── CLAUDE.md
├── AGENTS.md
├── FRAMEWORK.md
└── README.md
```

- `research-journal.md` 只沉淀真正研究过、想清楚的认知增量。
- `boss-brief.md` 是给老板 / PM 的高密度研究输出，不是简略版。
- `topics/_meta/edge-radar.md` 是识别信号和 AI 问法手册，不是状态库。
- 不维护 topic-level edge signal 文件，也不生成 standalone next-step 文件。

---

**版本**：v3.3.0
**最后更新**：2026-05-09
