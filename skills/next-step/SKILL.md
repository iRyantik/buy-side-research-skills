---
name: next-step
description: Use when the user asks what to research next, says a research thread feels off, wants a senior-analyst review, or asks how to keep digging after a research session.
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
- 研究启动时先检查 `_cache/<topic-slug>/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Next Step

把当前研究卡点压缩成一个最高杠杆问题。**核心价值不是安排任务**，而是判断现在最可能改变业务实质、model driver、市场预期、peer framing 或研究优先级的那个问题是什么，并决定是直接追问，还是先 handoff 到上游 primitive。

如果输出变成长任务清单、泛泛说“看财报 / 看行业 / 看估值”，或者在 mechanism / driver gap 没拆清时硬给下一步，本 skill 就失败了。

## 心法

`next-step` 是研究瓶颈路由器，不是研究执行器。它服务 v3 核心循环里的 `Better AI Question`：把模糊的不对劲、卡住、想继续挖，变成 1 个能推进判断框架的问题。

最好的 next step 通常很小，但杠杆很高：它不是“再多收集信息”，而是能验证一个关键机制、driver、source、peer 口径或 consensus framing 是否被误读。默认只给一个问题，因为问题太多会把研究员重新推回信息淹没。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 next-step-specific 要求。

特别强调：
- 本 skill 默认不新增事实，只基于用户给的材料诊断下一步；若必须引用事实、数字、KPI、新闻或管理层说法，必须有 source 或标 `[来源待补]`。
- 用户给的 unsourced claim 不能被当成事实；写成“如果这个 claim 成立”或标 `[需查证]`。
- 生成 AI 问题时，不要把未验证事实写进问题前提；应把验证动作写进问题本身。
- 不确定 link 是否存在时写 `[link 待补]`，不要为了让 prompt 看起来完整而造链接。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **任务清单惯性** | AI 容易输出 5-10 个 generic next steps | 强制选 1 个最高杠杆问题，除非用户明确要 plan |
| **把 interesting 当成 important** | 怪异点很多，但不一定改变投资判断 | 只保留能影响业务实质、driver、市场预期、peer framing 或研究优先级的问题 |
| **机制 / driver gap 下硬推进** | 还没搞懂机制或 driver 就写 thesis、model、peer compare | 先触发 `mechanism-map` 或 `driver-map` |
| **source gap 被忽略** | 把传闻、卖方转述或未验证 claim 当作研究起点 | 先触发 `information-impact` 或在问题中要求 source 验证 |
| **问题太宽** | “研究一下行业”无法执行，也无法判断答案质量 | 问题必须指向一个可验证对象、口径或假设 |
| **过度落盘** | 把未研究的灵感写进 journal，制造维护负担 | 本 skill 不默认创建文件；只有研究清楚后才交给 `research-journal` |

## 触发场景

### Mode A: Direction Coach

- "下一步怎么研究"
- "怎么继续挖"
- "next step"
- "我卡住了"
- "这里最值得追什么"
- "这个问题怎么变成更好的 AI 问题"

### Mode B: Research Audit

- "这段哪里不对劲"
- "这段研究哪里不对劲"
- "帮我回溯一下"
- "帮我 audit 一下这个研究"
- "这段结论最弱的地方在哪"

### Mode C: Question Rewriter

- "这个问题该怎么问"
- "帮我改成可以问 AI 的问题"
- "帮我把这个 vague idea 改尖"
- "我要问 mechanism / driver / source，怎么问"

### 不应触发

- 用户要验证一条新闻、供应链 claim、卖方观点或截图真假 → `information-impact`。
- 用户要解释行业机制、工程原理、设备链条、工艺流程或术语 → `mechanism-map`。
- 用户要拆 revenue、margin、backlog、price / volume / mix、KPI 或披露口径 → `driver-map`。
- 用户要写完整 long / short thesis → `alpha-thesis`，但若 driver 未拆清，先 `driver-map`。
- 用户要沉淀已经研究清楚的认知 → `research-journal`。

## 输入澄清要求

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **研究对象** | ticker / 公司 / 行业机制 / 事件 / 一段研究材料 | 用户没给对象且无法从上下文判断时，先问 1 个澄清问题 |
| **当前产物** | quickread / thesis draft / peer compare / earnings note / raw idea | 默认把它当作还未完成的研究片段 |
| **用户目标** | 继续挖 / audit / 改写 AI 问题 / 选择 skill route | 默认输出一个最高价值问题 |
| **事实质量** | sourced / unsourced / mixed / stale | unsourced 事实只作假设，不写成事实 |
| **疑点类型** | mechanism / driver / source / peer / market framing / catalyst | 先分类，再决定是否 handoff |
| **保存需求** | 对话输出 / handoff `research-journal` | 默认不保存、不创建文件 |

如果缺少的信息不会改变下一步判断，不要追问；直接给出最小 next-step，并把不确定处标出。

## Primitive Preflight

正式输出前先做内部分类。只要当前瓶颈属于下表的硬触发，就不要硬写普通 next step。

| 瓶颈类型 | 判断标准 | 下一步 |
|---|---|---|
| **mechanism / know-how gap** | 行业机制、工程原理、设备链条、工艺流程、术语、value capture 不清 | 先 handoff `mechanism-map` |
| **driver / disclosure gap** | revenue、margin、backlog、price-volume-mix、KPI 定义、reported bucket、披露口径不清 | 先 handoff `driver-map` |
| **company foundation / disclosure evolution gap** | 公司到底卖什么、业务边界如何演变、segment / KPI rename 或 recast 历史不清 | 先 handoff `company-primer` |
| **source / claim gap** | 关键事实、客户关系、新闻、卖方观点、专家说法未验证 | 先 handoff `information-impact` |
| **peer comparability gap** | peer group、KPI 口径、业务机制或 value-capture 不可比 | 先 handoff `peer-deep-dive`，必要时先 `mechanism-map` / `driver-map` |
| **thesis assembly gap** | driver 已拆清，variant view、catalyst、kill criteria 需要成稿 | handoff `alpha-thesis` |
| **journal-ready insight** | 已研究过、想清楚、能改变后续判断 | handoff `research-journal` |

Weird disclosure bucket / KPI bucket 的规则：遇到 `Other / Solutions / Systems / Industrial / Services / CTS` 这类不自然 bucket，或类似 `GTE / GTS / Industrial Products / Industrial Solutions` 的拆分，不要写成单一公司专项测试；先判断这是 mechanism gap、driver gap 还是 KPI 口径 gap，再触发对应 primitive。

## Mode A: Direction Coach

### Step 1: 找研究瓶颈

先判断用户真正卡在哪里：
- 不知道业务怎么运作 → mechanism gap。
- 不知道什么 driver 进 model → driver gap。
- 不知道消息能不能信 → source gap。
- 不知道几家公司是否可比 → peer comparability gap。
- 已经有材料但不知道哪一点最有 edge → next-step 本体。

### Step 2: 选择一个最高杠杆问题

候选问题必须至少满足以下一条：
- 可能改变业务实质理解。
- 可能改变 revenue / margin / backlog / price-volume-mix driver。
- 可能改变市场预期或 consensus framing。
- 可能改变 peer group / valuation framework。
- 可能改变下一步研究优先级。

如果一个问题只会带来更多背景知识，但不改变上述任何一项，默认不选。

### Step 3: 输出短答案

只输出一个问题和 1-2 个 AI 问法。不要把所有候选问题都列出来，除非用户要求比较多个方向。

## Mode B: Research Audit

用于用户给了一段研究、memo、thread、模型思路或 post-print 笔记，要求判断哪里不对劲。

工作流：
1. 先找已经赚到的最强结论。
2. 再找最大未解释怪异点。
3. 判断怪异点属于 mechanism、driver、source、peer、market framing 还是 thesis gap。
4. 如果是 primitive gap，输出 handoff block；否则输出一个 next-step 问题。

Research Audit 不是 copy edit，也不是完整 review；不要逐段改写用户材料。

## Mode C: Question Rewriter

用于把模糊问题改成更适合 AI 或下游 skill 的问题。

改写标准：
- 问题必须包含研究对象。
- 问题必须说明要验证的假设或缺口。
- 问题必须要求 source / as-of，除非是纯机制解释。
- 问题不能把未验证前提写成事实。
- 默认只给 1-2 个问题，不给 prompt pack。

## 输出结构

### Default: Direction Coach

```markdown
**我建议先追这个问题：[一个问题]**

为什么它可能改变判断：
- [说明它会影响业务实质 / model driver / 市场预期 / peer framing / 研究优先级]

可以这样问 AI：
1. [...]
2. [...]
```

### Research Audit

```markdown
**我建议下一步先补：[一个问题或 primitive handoff]**

已经赚到的结论：
- [...]

最大未解释怪异点：
- [...]

为什么这个问题优先：
- [...]

可以这样问 AI：
1. [...]
2. [...]
```

### Question Rewriter

```markdown
**可以改成这样问：**
1. [...]
2. [...]

为什么这样更好：
- [...]
```

### Primitive Handoff

```markdown
**先别继续写 [thesis/model/peer compare]，我建议先触发 `[skill-name]`。**

阻塞点：
- [...]

为什么会污染后续判断：
- [...]

交给 `[skill-name]` 的问题：
1. [...]
2. [...]

需要补的 source / data：
- [...]
```

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 高价值疑点是行业机制、工程原理、设备链条、工艺流程或术语 | `mechanism-map` |
| 高价值疑点是 revenue / margin / backlog / price-volume-mix 或 KPI 口径 | `driver-map` |
| 高价值疑点是公司业务基础、业务演变、segment / KPI rename 或 disclosure evolution | `company-primer` |
| 高价值疑点依赖一条 claim、新闻、供应链关系或卖方观点真假 | `information-impact` |
| 下一步是横向比较多家公司，且需要比较机制或 KPI 可比性 | `peer-deep-dive` |
| driver 已清楚，下一步要写 variant view、catalyst、kill criteria | `alpha-thesis` |
| 要压测现有 thesis 的隐含假设 | `bear-pre-mortem` |
| 下一步是财报前后需要看什么 | `earnings-setup` |
| 已经形成清楚认知增量，值得沉淀 | `research-journal` |
| 用户只是卡住，不知道怎么问 | 留在本 skill，输出 1 个问题 |

## 反模式自查

### Output 类
- ❌ 输出 5-10 个 generic tasks，而不是 1 个最高杠杆问题。
- ❌ 用“看财报 / 看行业 / 看估值 / 看新闻”当 next step。
- ❌ 默认给 prompt pack、研究计划或 checklist，超过用户需要。
- ❌ 问题没有研究对象，或对象大到无法执行。

### Logic / Routing 类
- ❌ 看到 mechanism / know-how gap，却继续写 thesis、model 或 peer compare。
- ❌ 看到 driver / KPI / disclosure gap，却给泛泛任务清单，不触发 `driver-map`。
- ❌ 看到 source gap，却把 claim 当事实继续推演。
- ❌ 看到 weird disclosure bucket / KPI bucket，却不问它对应的经济实质。
- ❌ 把“有趣的异常”当成“必须追的异常”，没有说明它会改变什么判断。
- ❌ 把尚未研究的灵感写进 `research-journal`。

### Source 类
- ❌ 在 AI 问题里塞入未验证事实，让后续回答默认接受该前提。
- ❌ 对用户给的 unsourced 数字、KPI、客户关系不标 `[需查证]`。
- ❌ 编造 URL、页码、引语或 source title 来让问题看起来完整。

### Workflow 类
- ❌ 用户要 next-step，却输出完整 research report。
- ❌ 用户要 audit 研究卡点，却逐段润色文本。
- ❌ primitive handoff 后又继续给普通 next-step，削弱阻塞判断。
- ❌ 创建 standalone next-step 文件或恢复 v2 state tracker。

## 篇幅基准

- Direction Coach：150-300 字；低于 100 字通常太泛，超过 400 字通常开始变成小计划。
- Research Audit：300-600 字；超过 700 字应删掉次要观察，只保留最强结论、最大怪异点、一个问题。
- Question Rewriter：150-350 字；默认 1-2 个问题。
- Primitive Handoff：150-350 字；只写阻塞点、污染风险、交给哪个 skill、需要补什么。
- 如果用户明确要求完整 plan，可以扩展，但要先说明这已经不是默认 next-step 输出。

## 与相邻 skill 的边界

- `mechanism-map` 解释机制、设备链条、工程原理、工艺流程和 know-how；本 skill 只判断是否应该先交给它。
- `driver-map` 拆 revenue、margin、backlog、price-volume-mix、KPI 和披露口径；本 skill 只识别 driver gap。
- `company-primer` 打牢公司业务基础、业务演变和披露口径历史；本 skill 只识别是否需要先补公司地基。
- `information-impact` 验证 claim 可信度；本 skill 不做 source hunting。
- `peer-deep-dive` 做横向研究和排序；本 skill 不替代 peer compare。
- `alpha-thesis` 写 variant view、catalyst、kill criteria；本 skill 不写完整 thesis。
- `research-journal` 沉淀已经研究清楚的认知；本 skill 不默认落盘。
