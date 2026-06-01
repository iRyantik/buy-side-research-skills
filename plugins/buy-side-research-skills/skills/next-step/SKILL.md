---
name: next-step
description: Choose the highest-value next research question when a thread feels stuck or incomplete.
---

# Next Step

Choose the highest-value next research question when a thread feels stuck or incomplete.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

把当前研究卡点压缩成一个最高杠杆问题。**核心价值不是安排任务**，而是判断现在最可能改变业务实质、model driver、市场预期、peer framing 或研究优先级的那个问题是什么，并决定是直接追问，还是先 handoff 到上游 primitive。

如果输出变成长任务清单、泛泛说“看财报 / 看行业 / 看估值”，或者在 mechanism / driver gap 没拆清时硬给下一步，本 skill 就失败了。

## 心法

`next-step` 是研究瓶颈路由器，不是研究执行器。它服务 v3 核心循环里的 `Better AI Question`：把模糊的不对劲、卡住、想继续挖，变成 1 个能推进判断框架的问题。

最好的 next step 通常很小，但杠杆很高：它不是“再多收集信息”，而是能验证一个关键机制、driver、source、peer 口径或 consensus framing 是否被误读。默认只给一个问题，因为问题太多会把研究员重新推回信息淹没。


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
| **mechanism / know-how gap** | 行业机制、工程原理、设备链条、工艺流程、术语、value capture 不清 | 先 handoff `mechanism-insight` |
| **driver / disclosure gap** | revenue、margin、backlog、price-volume-mix、KPI 定义、reported bucket、披露口径不清 | 先 handoff `driver-map` |
| **company foundation / disclosure evolution gap** | 公司到底卖什么、业务边界如何演变、segment / KPI rename 或 recast 历史不清 | 先 handoff `company-history` |
| **source / claim gap** | 关键事实、客户关系、新闻、卖方观点、专家说法未验证 | 先 handoff `information-impact` |
| **field evidence / channel validation gap** | 关键假设需要 expert call、客户 / 供应商 channel check、survey 或 fieldwork 验证 | 先 handoff `primary-research-plan` |
| **peer comparability gap** | peer group、KPI 口径、业务机制或 value-capture 不可比 | 先 handoff `peer-deep-dive`，必要时先 `mechanism-insight` / `driver-map` |
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



## Artifact / 保存策略

对话输出。用户要求保存时写入 industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md。

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

## 篇幅基准

- Direction Coach：150-300 字；低于 100 字通常太泛，超过 400 字通常开始变成小计划。
- Research Audit：300-600 字；超过 700 字应删掉次要观察，只保留最强结论、最大怪异点、一个问题。
- Question Rewriter：150-350 字；默认 1-2 个问题。
- Primitive Handoff：150-350 字；只写阻塞点、污染风险、交给哪个 skill、需要补什么。
- 如果用户明确要求完整 plan，可以扩展，但要先说明这已经不是默认 next-step 输出。
