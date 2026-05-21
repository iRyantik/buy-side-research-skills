---
name: mechanism-map
description: Explain industry mechanisms engineering principles equipment chains and process flows.
---

## Global Rules Capsule (v2)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 source、时间点和例外状态。默认 `S1@FY25`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；表后用 `S1 = source title, as-of/filed, link` registry 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、mechanism implication、value-capture conclusion、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Mechanism Map

把行业机制、工程原理、设备链条和关键术语翻译成投研含义。**核心价值不是写科普**，而是防止研究员和 AI 在没搞懂“东西怎么运作”的情况下，直接跳到 driver、model、thesis 或 peer compare。

如果输出只是百科解释，或者讲完以后不能说明它会改变什么研究判断，本 skill 就失败了。

## 心法

很多工业、能源、核电、航天和先进制造研究的真正 edge，不在“知道一个名词”，而在知道这个名词背后的系统怎么工作、瓶颈在哪里、谁捕获价值、哪些环节会传导到 revenue / margin / backlog driver。`mechanism-map` 的工作是把 know-how gap 变成可研究、可追问、可沉淀的结构。

本 skill 是 `driver-map` 的上游补充：`mechanism-map` 解释“机制怎么运作、价值在哪里捕获”；`driver-map` 再解释“这些机制如何进入收入、利润率、backlog、price / volume / mix driver”。不要用机制解释替代 driver-map，也不要在本 skill 里直接做 DCF、comps、workbook 或完整 thesis。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v2)`。本节只补充 mechanism-map-specific 要求。

特别强调：
- **工程机制、设备功能、工艺流程**可以使用公司技术白皮书、工程资料、监管/行业机构资料、教材型资料或明确 source；如果不确定，标 `[需查证]`。
- **产能、成本、效率、订单、价格、客户、装机量、市场规模、项目时间表**必须有 source / as-of。
- **“可以用于某场景”不等于“已经被某客户采用”**；任何客户、供应链、项目落地 claim 必须回到 `information-impact` 或可靠 source。
- **行业常识可以作为解释背景，但不能冒充公司事实**。把 mechanism read-through 写成 researcher inference，而不是 company disclosure。

## Parallel Evidence Pass

本 skill 默认必须按机制证据 bucket 启动 sub-agent / delegate worker 并行取证；sub-agent 只能返回 evidence card：

- 可拆任务：technical mechanism source、equipment / process flow、control point / value capture、company read-through evidence。
- sub-agent 不得写最终 mechanism implication、value-capture conclusion、driver-map handoff、thesis implication 或 model treatment；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一术语边界、流程图、capability vs adoption、company read-through 和 source 冲突后再写机制判断。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **相似术语混淆** | AI 容易把 train、turbine、compressor、generator、controls、service 等概念混在一起 | 强制做 `Terms that matter`，逐一说明 plain meaning 和边界 |
| **流程过度简化** | 复杂系统被压成一句“设备驱动增长”，丢掉瓶颈和价值捕获点 | 必须画轻量流程图 / 链条图 |
| **把 capability 写成 adoption** | “产品可以用于 LNG / data center / nuclear” 被误写成已经供货 | 客户 / 项目 / 供应链 claim 必须标 source 或 `[需查证]` |
| **技术事实过时** | 工艺路线、设备方案、监管要求可能变化 | 涉及最新项目、标准、装机、成本时标 as-of |
| **百科化** | 输出变成泛科普，不服务投资判断 | 每个机制解释必须落到 value capture / driver / thesis read-through |

## 触发场景

### Mode A: Mechanism Explainer
- "这个行业术语到底是什么意思"
- "这个设备链条是怎么连接的"
- "这个设备链条为什么这样设计"
- "这个工艺流程怎么运作"
- "为什么这个系统要这样设计"
- "瓶颈 / control point 在哪里"
- "这个 process step 在系统里做什么"
- "这个机制为什么重要"

### Mode B: Mechanism-to-Research Map
- "这个机制对哪些公司有价值"
- "这个工程约束会怎么影响 revenue driver"
- "为什么这个设备链条会影响 margin / service mix"
- "这个 know-how gap 会不会影响 thesis"
- "这个机制能不能解释 peer 估值差"

### Mixed Mode
- "这个业务 bucket 背后的机制是什么，为什么这么拆"
- "先讲清楚这个机制，再告诉我哪些公司类型可能受益"
- "这个设备链条怎么运作，哪些环节最可能捕获价值"

### 不应触发
- "这家公司收入 driver 是什么" → `driver-map`。
- "帮我搭 model / DCF / comps" → `3-statement-model / dcf-model / comps-analysis / model-update`，必要时先消费本 skill。
- "这个公司是不是进了某客户供应链" → `information-impact`。
- "下一步怎么研究这个问题" → `next-step`。
- "写 long / short thesis" → `alpha-thesis`。

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **对象** | 术语 / 设备 / 工艺 / 系统 / value chain | 用户给具体名词时按单一机制；给主题时先缩到最关键机制 |
| **研究目的** | 理解机制 / feed driver-map / feed model / feed thesis / peer compare | 默认服务后续 driver-map 和 thesis |
| **技术深度** | 直觉解释 / 工程链条 / 商业约束 | 默认用研究员能建模和问问题的深度，不写教材 |
| **行业范围** | 用户指定的行业 / 设备链 / 工艺链 | 按用户覆盖行业，不扩展到无关行业 |
| **source 要求** | 是否需要 web/source-backed deep dive | 默认关键事实和数字必须 source；纯机制解释可标 `[需查证]` |
| **保存需求** | 只在对话输出 / 写入 topic root 日期文件 | 默认对话；用户要求保存时写 `mechanism-map.md` |

如果用户只给一个很泛的主题，先把机制范围缩成 1-2 个最可能有投研价值的系统链条，不要展开成行业百科。

## Mode A: Mechanism Explainer

### Step 1: Mechanism in one sentence

用一句话讲清楚这个机制是什么，以及它为什么值得研究。句子必须同时包含：
- 对象是什么
- 它在系统里做什么
- 它可能影响哪个投研变量

### Step 2: Terms that matter

| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |
|---|---|---|---|---|
| [term] | [一句话解释] | [容易混淆对象] | [投研意义] | S1@latest 或 GAP |

Sources: `S1 = [source title], as-of/filed [date], [link]`.

### Step 3: How it works

默认用轻量流程图 / 链条图：

```text
input / fuel / feedstock -> core equipment/process -> output -> bottleneck / control point
```

随后用 3-6 个步骤解释，不要超过机制本身所需的深度。

### Step 4: Bottleneck and control point

明确系统中哪里最可能决定：
- capacity / throughput
- uptime / reliability
- efficiency
- capex intensity
- service intensity
- regulatory / safety constraint

## Mode B: Mechanism-to-Research Map

### Step 1: Where value is captured

| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |
|---|---|---|---|---|
| [equipment / service / controls / integration] | [company type] | [equipment sale / service / parts / software / EPC] | High / Medium / Low | [why it matters] |

### Step 2: Mechanism → Driver-map bridge

| Mechanism implication | Driver-map link | Model / thesis implication | Confidence |
|---|---|---|---|
| [机制含义] | [revenue / margin / backlog / price-volume-mix] | [后续怎么研究] | High / Medium / Low |

### Step 3: Driver-map handoff

机制解释完后，必须明确交给 `driver-map` 验证什么。不要只说"这个机制可能影响收入"；要指出收入或 margin 假设需要哪类披露、proxy 或后续验证。

| Mechanism conclusion | Possible revenue/margin driver | What driver-map must verify | Evidence status |
|---|---|---|---|
| [机制结论] | [可能进入的 revenue / margin / backlog driver] | [下一步必须验证的公司披露 / KPI / proxy] | disclosed / implied / proxy / unknown |

Rating hard standards:

| Rating | Hard standard |
|---|---|
| **High** | 有一手或权威 source 支持机制、商业关系和关键数据，且可直接映射到 driver |
| **Medium** | 机制和商业关系合理，但公司层面披露不完整，需要 peer / industry proxy |
| **Low** | 主要是研究员推断或主题关联，必须标 `[来源待补]` / `[需查证]` |

### Step 4: What not to infer

列出不能从该机制外推的东西。尤其要区分：
- `product can be used` vs `customer adopted`
- `equipment exposure` vs `recurring service exposure`
- `industry bottleneck` vs `company-specific revenue driver`
- `technical importance` vs `pricing power`

## 输出结构

```markdown
## Mechanism Map

**结论先行**
[一句话说明这个机制最重要的投研含义]

## Mechanism in one sentence

[这个机制是什么 + 在系统里做什么 + 影响哪个投研变量]

## Terms that matter

| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |
|---|---|---|---|---|

Sources: `S1 = [source title], as-of/filed [date], [link]`.

## How it works

`input / fuel / feedstock -> core equipment/process -> output -> bottleneck / control point`

[3-6 步解释]

## Where value is captured

| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |
|---|---|---|---|---|

## Research read-through

| Mechanism implication | Driver-map link | Model / thesis / peer implication | Confidence |
|---|---|---|---|

## Driver-map handoff

| Mechanism conclusion | Possible revenue/margin driver | What driver-map must verify | Evidence status |
|---|---|---|---|

## What not to infer

- [不能外推的结论]

## 可以问 AI

- [1-2 个下一步问题]
```

## 可选保存

默认只输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-mechanism-map.md
```

如果当前没有 dated result path，先 handoff 到 `new-session` 创建 / 解析路径，不要自行创建一堆目录。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 机制已经讲清，需要拆收入 / margin / backlog driver | `driver-map` |
| 机制影响 operating model、DCF、comps 或 workbook update | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 机制暴露高价值疑点但还不知道怎么问 | `next-step` |
| 机制解释了 peer 差异或 KPI 不可比 | `peer-deep-dive` |
| 两家公司是否受同一机制驱动 | `pair-trade` |
| 技术 / 客户 / 供应链 claim 需要先验真 | `information-impact` |
| 已经研究清楚，值得沉淀 | `research-journal` |
| 机制形成 long / short variant view | `alpha-thesis` |

## 反模式自查

### Source 类
- ❌ 产能、成本、效率、订单、价格、客户、装机量或项目时间表没有 source / as-of。
- ❌ 用社媒、论坛、聊天截图或卖方转述证明客户采用。
- ❌ 把行业常识写成公司披露事实。
- ❌ 多个 source 对工艺、设备或项目口径冲突但不标冲突。

### Logic 类
- ❌ 只写百科解释，没有 value capture 或 research read-through。
- ❌ 把 `product can be used` 写成 `customer adopted`。
- ❌ 把技术重要性直接外推成 pricing power。
- ❌ 没画流程图 / 链条图，导致系统关系不清。
- ❌ 解释了设备功能，但没说瓶颈、control point 或 service intensity。
- ❌ 解释完机制，但没有指出 `driver-map` 下一步必须验证什么。
- ❌ 遇到 BKR IET、LNG Train、燃机-压缩机这类机制型问题，却直接跳到 driver 或 thesis。

### Workflow 类
- ❌ 用户只是问机制，却输出 DCF / comps / price target。
- ❌ 机制已经解释清楚，却没有 handoff 到 `driver-map` 或 `3-statement-model / dcf-model / comps-analysis / model-update`。
- ❌ 机制仍是 Low confidence，却被后续 thesis 当作核心事实。
- ❌ 形成清楚认知后没有建议 `research-journal` 沉淀。

## 篇幅基准

- Quick mechanism check：500-900 字 + 1 张流程图 / 表。
- Full mechanism map：1000-1800 字 + 2-4 张表。
- 超过 2000 字通常说明范围过大，应拆成多个机制，或转入 `peer-deep-dive` / `3-statement-model / dcf-model / comps-analysis / model-update`。

## 与相邻 skill 的边界

- `driver-map` 处理 `Business Reality → Model Driver`；本 skill 处理机制、设备链条、术语和 know-how。
- `3-statement-model / dcf-model / comps-analysis / model-update` 做 operating model、DCF、comps、reverse DCF 和 workbook update；本 skill只提供机制到模型变量的桥。
- `information-impact` 验证 claim 真假；本 skill解释 claim 若成立会如何进入技术链条或商业机制。
- `next-step` 提出 1-2 个下一步问题；本 skill可以给问题，但不生成完整研究任务清单。
- `research-journal` 沉淀已研究清楚的机制认知；本 skill不默认落盘。
