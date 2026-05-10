---
name: driver-map
description: Use when decomposing revenue drivers, segment buckets, margin drivers, backlog conversion, price/volume/mix, or weird disclosure into business reality before modeling or thesis work.
---

## Global Rules Capsule (v1)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查 URL 和 claim 是否匹配。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。

# Driver Map

把公司披露口径翻译成真实业务和可建模 driver。**核心价值不是写一个收入拆分表**，而是防止研究员和 AI 把会计 segment、管理层 narrative、卖方分类或概念股标签误当成经济实质。

如果输出只是在复述公司 segment 名称，或者把未披露的 driver 编成事实，本 skill 就失败了。

## 心法

很多投研错误不是发生在 DCF、comps 或 thesis 结论，而是发生在更前面：你以为你知道这家公司靠什么增长，但其实只是接受了公司给的 bucket 名称。`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。

本 skill 复用 `financial-model` 的 `Reported segment → Business reality → Model driver` 逻辑，也复用 `Global Rules Capsule (v1)` 的 Senior Analyst Radar。它是研究原语：后续可以 feed `financial-model`、`alpha-thesis`、`peer-deep-dive`、`pair-trade` 和 `research-journal`，但它自己不做估值、不写完整 thesis。

**最重要的纪律**：不披露的 driver 不能编；只能写成 `[来源待补]`、`[需查证]` 或 researcher assumption。没有 source 的 driver map 是假精确。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 driver-map-specific 要求。

特别强调：
- **每个 reported bucket、segment revenue、KPI、orders、backlog、margin、price / volume / mix 判断都必须有 source / as-of**。
- **未披露 driver 只能写成 proxy 或 assumption**，必须标 `[来源待补]` / `[需查证]`，不能写成 company fact。
- **卖方拆分、行业图谱、专家访谈可以作线索**，但关键 driver 仍要回到 filing、IR、earnings call、transcript、监管文件或明确数据源。
- **多个 source 冲突时必须标冲突**，尤其是 10-K vs IR deck、press release vs call、公司口径 vs peer 口径。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **披露名称诱导** | AI 会把 `Solutions`、`Systems`、`Industrial` 这类名称当成真实业务 | 强制做 `Reported Bucket → Business Reality`，不让 bucket 名称直接进入模型 |
| **未披露 driver 编造** | AI 容易把行业常识写成公司披露事实 | 未披露一律标 proxy / assumption / `[来源待补]` |
| **KPI 口径错配** | orders、backlog、book-to-bill、installed base 在不同行业含义不同 | 每个 KPI 写 source、definition、as-of |
| **peer 类比过度** | 同业有 driver 不代表目标公司也披露或适用 | peer driver 只能作假设，不可替代公司 source |
| **概念暴露误读** | 主题相关不等于 revenue driver | 区分 direct revenue driver、indirect proxy、theme association |

## 触发场景

- "帮我拆一下这家公司 revenue driver"
- "这家公司收入怎么拆"
- "这个 segment / bucket 到底是什么业务"
- "某业务 bucket 为什么这么拆"
- "这个 reported bucket 对应什么业务实质"
- "这家公司靠什么增长"
- "为什么收入涨了但 margin 没涨"
- "backlog / orders 怎么进收入"
- "price / volume / mix 哪个在驱动"
- "这个业务口径是不是有点怪"

### 不应触发

- "帮我搭 model / 做 DCF / comps" → `financial-model`，但它应消费或先产出 driver-map。
- "这家公司到底做什么 / 业务怎么演变 / segment 或 KPI 历史口径怎么变" → `company-primer`，先打牢公司基础和 disclosure evolution。
- "这个设备链条 / 工艺流程怎么连接" → `mechanism-map`，先搞清机制再拆 driver。
- "快速看一家公司值不值得研究" → `stock-quickread`，若 driver 不清再进入本 skill。
- "几家公司一起看、排序" → `peer-deep-dive`，若 KPI 口径不可比再引用本 skill。
- "写 long / short thesis" → `alpha-thesis`，若 thesis 依赖未拆清的 driver 再回到本 skill。

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **对象** | 公司 / segment / 产品线 / 行业 bucket | 用户给 ticker 时按公司；给业务名时按 segment |
| **研究目的** | model / thesis / peer compare / earnings / journal | 默认服务 model 和 thesis |
| **时间口径** | 最新年报、最新季度、过去 3-5 年趋势 | 最新可验证披露 + 必要历史对比 |
| **driver 范围** | revenue / margin / backlog / price-volume-mix / installed base | revenue-first，必要时扩到 margin |
| **source cutoff** | 使用哪份 filing / call / IR deck | 最新可验证 source；不确定标 `[来源待补]` |
| **保存需求** | 只在对话输出 / 写入 topic session | 默认对话；用户要求保存时写 `driver-map.md` |

如果用户只说"拆 driver"，至少确认公司 / 业务范围；如果用户明确给出业务 bucket，则直接开始拆，不要把问题扩大成完整公司研究。

## 工作流

### Step 1: Reported Bucket → Business Reality

先把公司披露的 bucket 翻译成真实业务，不要直接接受命名。

| Reported bucket | Business reality | End-market / customer | Source / as-of | Gap |
|---|---|---|---|---|
| [segment / product] | [实际卖什么 / 做什么] | [客户或应用] | [source] | [缺口] |

遇到 `GTE / GTS / Industrial Products / Industrial Solutions / CTS` 这类拆分时，要直接触发 Senior Analyst Radar：这可能不是普通并列 segment，而是 gas turbine 系统价值链、产品本体、配套设备、service、controls 或 end-market 维度的混合拆分。

### Step 2: Business Reality → Model Driver

把每个业务 bucket 映射到可观察 driver。

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| Equipment | units / MW / MTPA / orders | price / mix | orders, backlog, shipments | High / Medium / Low |
| Services | installed base | utilization / attach rate | service revenue, fleet hours | High / Medium / Low |

常用 driver library：
- **Volume**：unit shipment、capacity、MTPA、MW、rig count、installed base、customer count。
- **Price**：ASP、contract escalation、commodity pass-through、pricing index。
- **Mix**：equipment vs services、newbuild vs aftermarket、large frame vs aero-derivative、project vs recurring。
- **Backlog / orders**：order intake、book-to-bill、backlog conversion、project timing。
- **Utilization**：fleet utilization、factory load、service hours、capacity factor。
- **Installed base / attach**：service attach rate、replacement cycle、parts intensity。
- **End-market proxy**：LNG FID、data center power demand、aerospace build rate、grid capex。

### Step 3: Driver Quality

每个 driver 必须评级，但评级不能凭感觉：

| Rating | Hard standard |
|---|---|
| **High** | 公司直接披露 KPI / bucket revenue / backlog / margin，且定义清楚、可跟踪 |
| **Medium** | 公司部分披露，需用 peer / industry proxy 补足，但方向可验证 |
| **Low** | 主要靠推断、卖方拆分或主题关联，必须标 `[来源待补]` / `[需查证]` |

### Step 4: Disclosure vs Inference / Proxy Strategy

每个关键 driver claim 都必须标清证据状态。合理推断可以写，但不能写成公司事实；proxy 可以用，但必须说明 proxy 风险和模型处理方式。

Evidence status 只能用：
- `company disclosed`：公司直接披露该 driver / KPI / bucket。
- `company implied`：公司语言或披露结构暗示该 driver，但没有完整 KPI。
- `peer proxy`：用同业或行业 proxy 近似。
- `researcher assumption`：研究员假设，必须可被后续验证。
- `unknown`：还不知道，不能进入 base-case model。

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| [driver 判断] | company disclosed / company implied / peer proxy / researcher assumption / unknown | [proxy or none] | [proxy 可能误导之处] | base case / sensitivity / scenario only / exclude |

Hard rule：`Low` confidence 或 `unknown` driver 不能进入单一 base case；只能进入 sensitivity、scenario 或标 `[来源待补]`，直到有更强 source。

### Step 5: Implications

说明这个 driver map 如何影响后续研究：
- 对 `financial-model`：哪些 line item 应该按 driver 建模。
- 对 `alpha-thesis`：variant view 应该落在哪个 driver。
- 对 `peer-deep-dive`：哪些 KPI 才可比，哪些不可比。
- 对 `pair-trade`：两腿是否受同一 driver 驱动，还是只是主题相似。
- 对 `research-journal`：哪些认知已经想清楚、值得沉淀。

## 输出结构

```markdown
## Driver Map

**结论先行**
[一句话说明这家公司 / 业务最应该按什么 driver 理解，最大披露缺口在哪里]

## Reported Bucket → Business Reality

| Reported bucket | Business reality | End-market / customer | Source / as-of | Gap |
|---|---|---|---|---|

## Business Reality → Model Driver

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|

## Driver Quality

| Driver | Rating | Why | Source / as-of | What would improve confidence |
|---|---|---|---|---|

## Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|

## Weird Buckets / Senior Analyst Radar

**这里值得深挖**
- 怪异点：[披露 / bucket / KPI 哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]

## Implications for model / thesis

- [这个 driver map 会如何改变 model / thesis / peer compare]

## 可以问 AI

- [1-2 个下一步问题]
```

## 可选保存

默认只输出到对话。用户明确要求保存时，写入当前 topic session：

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/driver-map.md
```

如果当前没有 topic session，先 handoff 到 `new-session` 创建 / 解析路径，不要自行发明大量目录。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 用户要继续搭 operating model / DCF / comps | `financial-model` |
| driver work 发现公司业务边界、segment rename、KPI recast 或 material M&A 历史不清 | `company-primer` |
| driver map 暴露 variant view | `alpha-thesis` |
| 多家公司 driver 需要横向比较 | `peer-deep-dive` |
| 两家公司是否受同一 driver 驱动 | `pair-trade` |
| driver 质量低或 bucket 怪，需要更好问题 | `next-step` |
| 已经研究清楚，想沉淀认知 | `research-journal` |
| 供应链 / 客户 claim 影响收入 driver | 先 `information-impact`，再回到本 skill |
| 业务 bucket 背后涉及工程机制 / 设备链条 / know-how gap | 先 `mechanism-map`，再回到本 skill |

## 反模式自查

### Source 类
- ❌ Reported bucket、segment revenue、orders、backlog、margin 没有 source / as-of。
- ❌ 用卖方拆分替代公司披露，却没标注为 assumption。
- ❌ 把合理推断、peer proxy 或 researcher assumption 写成 company disclosed fact。
- ❌ 多个 source 口径冲突但只挑一个顺手的用。
- ❌ 把 workbook 里的旧数字当 source。

### Logic 类
- ❌ 只复述 segment 名称，没有翻译 business reality。
- ❌ 只写 revenue driver，不问 margin driver 是否不同。
- ❌ Low confidence driver 没有进入 sensitivity / scenario，却直接进入 base case。
- ❌ 把 theme association 写成 direct revenue driver。
- ❌ 用历史 CAGR 代替 driver。
- ❌ 看到 `Other / Solutions / Systems / Industrial` 这种 bucket 不追问。

### Workflow 类
- ❌ 用户只是要 driver-map，却输出完整 DCF / comps。
- ❌ 用户要搭 model，却停在 driver-map，不 handoff 到 `financial-model`。
- ❌ driver confidence 是 Low，却被后续 thesis 当作核心事实。
- ❌ 形成清楚认知后没有建议 `research-journal` 沉淀。

## 篇幅基准

- Quick driver check：400-700 字 + 1-2 张表。
- Full company / segment driver-map：900-1600 字 + 3-4 张表。
- 超过 1800 字通常说明范围过大，应拆成 `peer-deep-dive`、`financial-model` 或多个 segment。

## 与相邻 skill 的边界

- `financial-model` 做 operating model、DCF、comps、workbook update；本 skill 只做 driver-map。
- `company-primer` 处理公司业务基础、业务演变和 disclosure evolution；本 skill 在这些基础清楚后才把 bucket 映射成 model driver。
- `stock-quickread` 快速判断是否值得继续看；本 skill 深挖 revenue / margin driver。
- `peer-deep-dive` 做横向排序和 cross-cut insight；本 skill 提供可比较的 driver 口径。
- `mechanism-map` 处理行业 know-how、工程机制、设备链条、工艺流程和术语；本 skill 只处理公司业务到 model driver 的映射。
