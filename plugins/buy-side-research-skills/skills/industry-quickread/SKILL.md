---
name: industry-quickread
description: Run a first pass on an industry theme value chain demand pocket or profit pool.
---

# Industry Quickread

Run a first pass on an industry theme value chain demand pocket or profit pool.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

在 30-45 分钟内把一个陌生行业 / 主题 / value chain 从噪音压缩成可研究的地图：这个行业靠什么赚钱、现在处于什么 regime、利润池在哪里、哪些 KPI 真能验证、下一步该看哪些公司或机制。

如果输出像行业入门科普、卖方 initiation 的行业章节、概念股列表，或者把行业层 driver 硬交给 `driver-map`，本 skill 就失败了。

## 心法

买方做行业 quickread 不是为了“懂行业全貌”，而是为了决定：这个行业是否值得继续花时间、应该沿哪条 profit pool / bottleneck / mispricing 路径切入、下一步是先看机制、筛 names、做 peers，还是直接放弃。

行业 first-pass 的核心不是罗列 value chain，而是找 **current regime**：供给短缺还是过剩、需求真实加速还是预期透支、价格由谁决定、利润留在 upstream / equipment / integrator / operator / distributor 哪一段。没有 regime 判断，就只是百科。

本 skill 只做到行业 triage。它不替代 `mechanism-map` 的工程 / 产业链机制拆解，不替代 `candidate-screener` 的系统找票，也不替代 `driver-map` 的公司 / segment / 披露口径到 model driver 映射。

## 触发场景

使用本 skill 当用户问：
- “快速看一下这个行业 / 主题”
- “这个行业现在值不值得研究”
- “帮我做一个行业 quick read”
- “这个 value chain 利润在哪里”
- “这个行业现在处于什么周期”
- “这个主题该先看哪些 names”
- “AI data center power infrastructure / humanoid robotics / nuclear fuel cycle 这种主题先怎么切”

不要用于：
- 已经锁定某家公司，要看它卖什么、客户是谁、segment 怎么变：用 `company-primer`。
- 要解释工艺、设备链、工程原理、行业术语：用 `mechanism-map`。
- 要拆某家公司收入、margin、backlog、price/volume/mix、披露 bucket：用 `driver-map`。
- 要系统找一篮子 long / short candidates：用 `candidate-screener`。

## 输入澄清要求

如果用户给的行业 / 主题过宽，先快速补齐或声明默认假设，不要停在长问卷。

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 行业边界 | 产品 / 服务 / value chain stage / 下游应用 | 按用户原词最窄可投边界定义 |
| 地域 | US / 大中华 / 全球 / 某单一市场 | 全球框架，优先标出用户常看市场的 anchor |
| 时间窗口 | 3M / 12M / 24M+ | 12M，可兼顾 3M catalyst |
| 研究目的 | 找票 / 建 thesis / 补机制 / 判断是否放弃 | 默认判断是否值得继续研究 |
| 方向 | Long / Short / Both | Both，保留 LS 视角 |
| 已知材料 | filings / sell-side / industry reports / dataset | 先查 topic `_cache/`，没有就用公开 source |

如果行业词本身可能有两种含义，先定义。例如 “nuclear” 可能指 uranium miners、conversion/enrichment、reactor operators、SMR equipment 或 utilities；必须先拆边界。

## 使用方式

用于用户给出一个行业、主题或 value chain，希望快速判断研究入口。

### 输出结构

```markdown
## Verdict

[2-4 句结论先行：这个行业当前最重要的经济现实、是否值得继续研究、下一步最高杠杆动作]

## 1. 这个行业是什么

3-5 句大白话。不需要行业知识就能懂——谁在卖、谁在买、钱的流向。像跟朋友解释一样。

#### 产业链长这样

Mermaid 4-6 个节点，把主要环节标出来。不是公司列表——是行业的结构骨架。

```mermaid
flowchart LR
    A[<原材料/技术>] --> B[<加工/制造>] --> C[<核心组件>] --> D[<集成/组装>] --> E[<终端应用>]
```

> 用日常词汇。每个节点一句话描述——"谁在卖什么给谁"。

#### 长这样

1 张行业代表性产品/设备图。不是具体某家公司的产品——是这个行业在造的东西。

| ![行业图](_cache/images/<topic>-product.png) |
|---|
| *<产品/设备名> — <功能（≤15字）>* |

> ① web search "<行业关键词> product photo" → ② 搜不到就不放。下载到 `_cache/images/<topic>-product.png`。

## 2. 当前 Regime / Cycle / Bottleneck

| 维度 | 当前判断 | Evidence | Ev |
|---|---|---|---|
| Demand | 加速 / 放缓 / 结构性替换 / 补库存 | [具体指标] | [S1](./_cache/sources/industry-demand-pack.md) |

| Supply | 紧缺 / 过剩 / 长周期扩产 / 进口依赖 | [具体指标] | [S1](./_cache/sources/supply-note.md) |
| Pricing | 上行 / 下行 / 合同锁价 / spot 敏感 | [具体价格或 proxy] | [I1](https://example.com/pricing-proxy) |
| Margin pressure | 原材料 / labor / mix / competition | [证据] | [S2](./_cache/sources/margin-pressure-note.md) |

**Takeaway**: [不是复述表格；写当前 regime 对可投资环节的含义]

## 3. Value Pool / Value Capture

| Value chain stage | 谁赚钱 | 利润来源 | 当前压力 | 可投资性 |
|---|---|---|---|---|
| Upstream / component / equipment / integrator / operator / distributor | [公司类型] | [pricing power / scarcity / installed base] | [压力] | High / Medium / Low |

**Takeaway**: [利润池是否在迁移；主题热度和利润捕获是否错位]

## 4. KPI / Source Map

| 要验证的问题 | KPI / proxy | 最好 source | 频率 | 为什么重要 |
|---|---|---|---|---|
| Demand 是否真实 | orders / backlog / shipment / utilization | [source type] | 月度 / 季度 | [投资含义] |
| Pricing 是否能传导 | ASP / contract price / spread | [source type] | [频率] | [投资含义] |

## 5. Demand / Supply / Pricing / Margin 压缩判断

- Demand: [1-2 句，必须有 evidence 或标 `[需查证]`]
- Supply: [1-2 句]
- Pricing: [1-2 句]
- Margin: [1-2 句]

## 6. Anchor Names（只作定位，不做个股 quickread）

| Name | Market | Value chain role | Exposure 类型 | 为什么是 anchor | Ev |
|---|---|---|---|---|---|
| [ticker/company] | [US/A/HK/etc.] | [stage] | direct / indirect / thematic / [需查证] | [定位作用] | [S1](./_cache/sources/industry-demand-pack.md) 或 GAP |

**Discipline**: anchor names 最多 3-5 个；不要在这里写完整公司分析。每个 anchor 的 market cap 和 PE 通过 yfinance .info 获取，标注 as-of。可选加公司 logo（15px 小图）——搜得到就放，搜不到算了。logo 下载到 `_cache/images/<ticker>-logo.png`。

## 7. Priced-in / Consensus Clue

[当前市场可能在 price 什么：growth、margin、capacity tightness、policy、rate、cycle turn。没有 verified consensus / valuation 数据时，明确写 `[需查证]`。]

## 8. 不懂的词先看这

| 术语 | 大白话 |
|---|---|
| <术语> | <一句话> |

> 最多 5-8 个。不是词典，是聊天时怎么讲。

## 9. Routing

| 发现 | 下一步 |
|---|---|
| 行业机制 / 工程 / 设备链不清 | `mechanism-map` |
| 需要系统找 long / short names | `candidate-screener` |
| 已有 3-8 个核心公司要横向比较 | `peer-deep-dive` |
| 某个 anchor name 值得单独看 | `stock-quickread` |
| 行业 / 主题的 priced-in、buy-side bar 或 consensus debate 不清 | `consensus-map` |
| 某家公司 / segment / bucket 到 model driver 不清 | `driver-map` |

## 10. 下一步 5 个具体问题

1. [具体到某个 KPI / source / 文件 / 数据集能回答]
```

## Artifact / 保存策略

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-industry-quickread.md
```

本 skill 的 `artifact_policy.naming_mode = optional_qualifier`。topic 级 first-pass 默认继续使用 `YYYY-MM-DD-<artifact>.md`；如果这次只覆盖某个 demand pocket、value-chain slice 或子行业问题，则应改由 `new-session` 解析成 `YYYY-MM-DD-<artifact>-<qualifier>.md`。

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录，不要未解析路径就写入。

保存后的 `industry-quickread.md` 是 triage artifact，不是 earned memory。只有研究清楚、source-backed、会改变判断的认知增量，才进入 `research-journal`。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 行业 / 主题刚进入 radar，需要 first-pass | `industry-quickread` |
| 行业机制、工程原理、设备链、工艺、术语不清 | `mechanism-map` |
| 需要从行业逻辑找 long / short candidates | `candidate-screener` |
| 已有一组 anchor companies，需要横向比较 | `peer-deep-dive` |
| 单个公司值得快速判断 | `stock-quickread` |
| 行业 / 主题 market expectations、priced-in assumptions 或 variant gap 不清 | `consensus-map` |
| 公司业务基础、segment / KPI 演变不清 | `company-primer` |
| 公司 / segment / 产品线 / 披露 bucket 到 model driver 不清 | `driver-map` |
| 行业判断已经形成 thesis 差异 | `alpha-thesis` |
| 行业判断需要量化进模型 | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 行业 / 主题关键假设需要 expert call、channel check、survey 或 fieldwork 验证 | `primary-research-plan` |
| 形成可复用认知增量 | `research-journal` |

推荐行业路径：

```text
new-session -> ingest -> industry-quickread -> consensus-map -> mechanism-map
-> candidate-screener / peer-deep-dive -> stock-quickread
-> driver-map -> primary-research-plan
-> alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update -> research-journal
```

## 反模式自查

写完必须自查，命中就重写：

- 只写行业科普、政策背景、历史沿革，没有 current regime。
- 把 value chain 画成列表，但不判断谁 capture profit。
- Demand / supply / pricing / margin 没有任何 source 或 `[需查证]` 标记。
- 数据表没有 takeaway，或 takeaway 只是复述表格。
- anchor names 超过 5 个，变成伪 `candidate-screener`。
- anchor names 没有 exposure 类型，导致 direct / indirect / thematic 混在一起。
- 把“行业 driver”泛化交给 `driver-map`；`driver-map` 只处理公司 / segment / 产品线 / 披露 bucket 到 model driver。
- 遇到工程机制、设备链条或工艺不清，还硬写行业解释；应触发 `mechanism-map`。
- 写 “长期受益 / 空间广阔 / 景气上行” 但没有 KPI。
- 写 “priced in / not priced” 但没有估值、consensus、股价反应或 `[需查证]`。
- 把卖方主题归类当作业务关联 source。
- 没有给下一步 5 个具体问题，导致研究员不知道怎么继续。

## 篇幅基准

标准 1200-1800 字，3-4 张表格。低于 600 字通常 source / regime / value pool 不全。

低于 600 字通常 source / regime / value pool 不足；超过 2200 字通常已经越界到 `mechanism-map`、`candidate-screener` 或 `peer-deep-dive`。

## 与相邻 skill 的边界

| Skill | 边界 |
|---|---|
| `mechanism-map` | 解释行业机制、工程原理、设备链条、工艺流程、术语和 value-capture 机制；本 skill 只识别是否需要它。 |
| `driver-map` | 处理公司 / segment / 产品线 / 披露 bucket 到 revenue、margin、backlog、price/volume/mix model driver；不是泛行业 driver 拆解。 |
| `candidate-screener` | 从 hypothesis / industry logic 系统找 long / short candidates；本 skill 只给 3-5 个 anchor names。 |
| `peer-deep-dive` | 对 3-8 家公司做横向深研、排序和 cross-cut insight；本 skill 不做完整 peer comparison。 |
| `stock-quickread` | 快速看单家公司；本 skill 只判断行业和 anchor。 |
| `consensus-map` | 系统拆行业 / 主题的 sell-side consensus、buy-side bar、priced-in assumptions 和 variant-view gap；本 skill 只给 clue。 |
| `company-primer` | 梳理单家公司业务基础、历史演变和 disclosure evolution；本 skill 不写公司基础研究。 |
| `alpha-thesis` | 写 variant view、catalyst、kill criteria；本 skill 只提供 thesis 起点。 |
| `primary-research-plan` | 设计合规 expert call、channel check、survey 和 fieldwork 计划；本 skill 只识别需要 primary evidence 的假设。 |
