---
name: research-journal
description: Use when summarizing a completed research session, writing topic research notes, preserving solved research insights, or preparing a high-density Boss Brief for a PM or boss.
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

# Research Journal

把已经研究过、想清楚、能改变后续判断的认知增量沉淀成 topic memory。**核心价值不是记录过程**，而是把研究员已经赚到的判断、机制、driver、source map、open question 和 Boss-ready conclusion 留下来，方便未来继续研究或向 PM transfer。

如果输出变成 transcript、raw reminder、未验证灵感仓库，或者把未 source 的 driver / mechanism guess 写成 settled fact，本 skill 就失败了。

## 心法

`research-journal` 是 v3 journal-first 系统的 memory layer。它只接收已经完成一轮研究后的增量认知，不负责帮用户“想下一步”，也不把每个怪异点都存成状态。

Journal 的写法要像一个认真研究员给未来自己的笔记：结论先行、source 清楚、保留争议和未解决问题，但不复述聊天过程。Boss Brief 则是给 PM / boss 的高密度 transfer，不是 journal 的简略版，而是把最重要的判断压缩成可讨论的 memo。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 research-journal-specific 要求。

特别强调：
- Journal 里的事实、数字、KPI、管理层引语、行业数据、历史时间点必须有 source / as-of；没有 source 的事实必须标 `[来源待补]` 或不写入。
- Journal 可以记录研究员判断，但判断依据的事实必须有 source；不要把“我们觉得”包装成事实。
- `mechanism-map` / `driver-map` 的结果只有在 source 和逻辑被理解后才能吸收；否则写成 open question 或 handoff，不写成 settled insight。
- Boss Brief 可以牺牲细节，但不能牺牲关键 source、争议、风险和置信度。
- Topic `index.md` 只放演进地图和 session links，不放未验证事实堆积。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **transcript 压缩惯性** | AI 容易把对话顺序复述成 journal | 强制按研究问题和结论重组，不按聊天顺序写 |
| **灵感仓库化** | 未研究的怪异点被写成 journal，未来维护成本上升 | 先过 `Earned Insight Gate`，不达标就 handoff |
| **source 遗失** | 总结时丢掉 source / as-of，未来无法复查 | 关键事实必须保留 source / as-of |
| **把 guess 写成 fact** | driver / mechanism 推断被沉淀成确定结论 | 强制区分 settled insight、working hypothesis、open question |
| **Boss Brief 变摘要** | 给 PM 的版本只变短，没保留判断密度 | Boss Brief 必须保留核心结论、关键数据、debate 和 implication |
| **index 变状态库** | topic index 被写成 checklist / tracker | 只维护自然演进地图，不恢复 v2 state system |

## 触发场景

### Mode A: Private Research Journal

- "总结本轮研究"
- "总结本轮行业研究"
- "总结本轮 topic 研究"
- "写进 journal"
- "research journal"
- "整理这个 topic"
- "把这次公司 / 行业 / 主题研究沉淀一下"

### Mode B: Boss Brief

- "做一版给老板看的"
- "给 PM 的版本"
- "boss brief"
- "发给别人看的研究结论"
- "把这轮研究压成 memo"

### Mode C: Topic Index Update

- "更新 topic index"
- "把这次 session 加到 index"
- "整理这个 topic 的演进地图"
- "把已经研究过的问题串起来"

### 不应触发

- 用户只是问下一步怎么研究 → `next-step`。
- 用户只有一个未验证 claim、新闻、截图或卖方观点 → `information-impact`。
- 用户机制、工程原理、设备链条还没搞懂 → `mechanism-map`。
- 用户 revenue / margin / backlog / KPI 口径还没拆清 → `driver-map`。
- 用户要写完整 thesis / pair / model → 对应 `alpha-thesis`、`pair-trade`、`financial-model`。

## 输入澄清要求

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **topic path** | `topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/` | 用户未给路径时，建议路径，不擅自创建复杂目录 |
| **研究对象** | 主题 / 公司 / 事件 / peer set / thesis | 从上下文推断；不清楚时问 1 个澄清问题 |
| **写入目的** | journal / Boss Brief / index update | 默认 journal；用户提 PM / boss 时用 Boss Brief |
| **source 状态** | sourced / mixed / unsourced | mixed 时只写 sourced 结论，unsourced 留 open question |
| **研究成熟度** | noticed / researched / settled / disputed | 只有 researched 以上才能沉淀 |
| **上游产物** | mechanism-map / driver-map / next-step / peer / thesis / model | 先判断是否已消化，不机械粘贴 |

如果路径缺失但用户明确要求写文件，先给出建议路径并说明需要确认；如果用户只要对话总结，则不落盘。

## Earned Insight Gate

任何内容写进 journal 或 Boss Brief 前，都必须先过写入门槛。

| Gate | Hard standard | 不满足时 |
|---|---|---|
| **已研究** | 用户或上游 skill 已经完成一轮 source-backed research，不只是注意到异常 | 留在对话或交给 `next-step` |
| **可复述结论** | 能用 1-2 句话说清楚“现在我们相信什么 / 不相信什么” | 不写 settled insight，只写 open question |
| **关键事实有 source** | 支撑结论的数字、KPI、引语、事件、source conflict 有 source / as-of | 标 `[来源待补]` 或不写入 |
| **能改变判断** | 影响业务实质、model driver、market framing、peer group、估值框架或研究优先级 | 不写 journal，最多写 index session link |
| **剩余不确定性明确** | 知道哪些还没搞清楚，且不会污染结论 | 写入 `Unresolved / What would change our mind` |

### Handoff block

如果内容未过 Gate，不要硬写 journal。输出：

```markdown
**先不写进 journal，我建议先补 `[skill-name]`。**

阻塞点：
- [...]

为什么现在写入会污染记忆：
- [...]

交给 `[skill-name]` 的问题：
1. [...]
2. [...]
```

## Mode A: Private Research Journal

### Step 1: 写入判断

先给一张短确认表，避免把所有内容都写进去：

| 研究问题 / insight | 写入深度 | Value tags | Source 状态 | 判断理由 | 写入位置 |
|---|---|---|---|---|---|

Depth levels：
- `skim`：一句话结论 + 为什么暂时不深挖。
- `standard`：结论 + 关键 source / data + 研究含义。
- `deep`：机制、driver、source conflict、关键数据、剩余疑问都已研究清楚。

Value tags：
- `data-anchor`
- `glossary`
- `mechanism`
- `market-structure`
- `model-driver`
- `alpha-view`
- `source-map`
- `open-question`
- `research-edge`
- `disclosure-anomaly`
- `source-conflict`
- `know-how-gap`
- `market-misread`

### Step 2: 写 research-journal.md

写入路径：

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/research-journal.md
```

Journal 不用 rigid template，但必须包含：
- 本轮研究地图：研究了哪些问题，而不是聊了什么。
- 结论先行：每个 section 开头先给结论。
- Source anchors：关键事实、数字、KPI、引语的 source / as-of。
- 研究含义：它改变了什么业务理解、driver、market framing 或后续优先级。
- Unresolved：还没搞清楚但不污染当前结论的部分。

## Mode B: Boss Brief

Boss Brief 是给 PM / boss 的高密度 transfer，不是简略版。

写入路径：

```text
topics/[topic_type]/[topic-slug]/[YYYY-MM-DD]-[session-slug]/boss-brief.md
```

写前先确认或从材料中提取：
- 核心结论。
- 3-5 个 final takeaways。
- 必须保留的关键数据 / source / as-of。
- 最大 debate / variant view。
- 对 model、thesis、peer framing 或下一步研究优先级的 implication。

Boss Brief 可以使用这些 headings，但不要机械全塞：
- `Conclusion`
- `Takeaways`
- `Key Data`
- `Debate`
- `Implications`
- `What Would Change Our Mind`

## Mode C: Topic Index Update

Topic `index.md` 是演进式地图，不是状态库。只维护当前 topic 的研究脉络：
- 已研究问题。
- 每个 session link。
- 当前高置信结论。
- 尚未解决的 open questions。
- 哪些 session 产生了 Boss Brief 或 key driver / mechanism insight。

写入路径：

```text
topics/[topic_type]/[topic-slug]/index.md
```

不要补历史，不要强行重构所有旧 session；只更新本次 session 对 topic 地图的增量。

推荐结构：

```markdown
# [Topic]

## Current Map

- [当前最重要的 3-5 个研究判断 / open questions]

## Sessions

| Date | Session | What changed | Links |
|---|---|---|---|

## Open Questions

- [仍需研究的问题]
```

## Primitive Consumption Rules

### Consuming `mechanism-map`

只有当机制结论、关键术语、流程 / value-capture logic、source / as-of 和剩余不确定性都清楚时，才能写入 journal。

如果只是“看起来可能是某机制”，写成：
- `Working hypothesis`，并标 `[需查证]`；或
- handoff 回 `mechanism-map`。

### Consuming `driver-map`

只有当 reported bucket、business reality、model driver、KPI / source / as-of 和 confidence 都清楚时，才能写入 journal。

如果 driver 仍是 Low confidence、unknown、peer proxy 或 researcher assumption，不能写成 settled business reality；只能写成 open question、sensitivity 或 handoff 回 `driver-map`。

### Consuming `information-impact`

只有 `Confirmed`、`Likely` 或清楚标为 `Plausible but unconfirmed` 的 claim 才能进入 journal。`Unsupported` / `Contradicted` 可以写进 source-map 或 false lead，但不要继续扩写研究含义。

## 输出结构

### Private Research Journal

```markdown
# Research Journal — [topic / session]

## 本轮研究地图

- [研究问题 1] → [当前结论]
- [研究问题 2] → [当前结论 / open]

## [研究问题 / insight]

**结论先行**
[1-2 句话说清楚已经赚到的 insight]

**Source anchors**
- [source / as-of]

**为什么重要**
- [改变了什么业务实质 / driver / market framing / peer group / 研究优先级]

**Unresolved**
- [还没搞清楚但不污染当前结论的部分]
```

### Boss Brief

```markdown
# Boss Brief — [topic / session]

## Conclusion

[一句话核心判断]

## Takeaways

1. [...]
2. [...]
3. [...]

## Key Data / Source Anchors

- [...]

## Debate / Variant View

- [...]

## Implications

- [...]
```

### Topic Index Update

```markdown
## Sessions

| Date | Session | What changed | Links |
|---|---|---|---|

## Open Questions

- [...]
```

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 研究只发现了疑点，还没形成问题 | `next-step` |
| source / claim 未验证 | `information-impact` |
| 机制、工程原理、设备链条或术语未搞清 | `mechanism-map` |
| revenue / margin / backlog / KPI / disclosure driver 未搞清 | `driver-map` |
| Journal 暴露出可写成 thesis 的 variant view | `alpha-thesis` |
| Journal 暴露出 thesis 关键反方风险 | `bear-pre-mortem` |
| Journal 需要横向比较 peer 或重排研究优先级 | `peer-deep-dive` |
| Journal 需要量化到 model / valuation | `financial-model` |
| 已有完整研究，需要给 PM / boss transfer | Boss Brief mode |
| 需要把本次 session 放进 topic 演进地图 | Topic Index Update mode |

## 反模式自查

### 写入门槛类
- ❌ 把“刚注意到的怪异点”写进 journal，而不是先交给 `next-step`。
- ❌ 把未验证的 source / claim 写成事实。
- ❌ 把 Low confidence driver 写成 settled business reality。
- ❌ 把 mechanism guess 写成 settled know-how。
- ❌ 不能用 1-2 句话复述结论，却强行写入。

### Journal 质量类
- ❌ 按聊天顺序复述，变成 transcript。
- ❌ 只写“我们看了 X / Y / Z”，没有说明判断改变了什么。
- ❌ 数据表没有 takeaway，或 takeaway 复述表格。
- ❌ Journal 里出现公司历史、管理层履历、通用 SWOT、行业入门。
- ❌ 所有内容都写成 `deep`，没有区分 skim / standard / deep。

### Boss Brief 类
- ❌ 把 Boss Brief 叫“简略版”或“轻量摘要”。
- ❌ 删除 debate / variant view，只留下单边结论。
- ❌ 删除关键 source / as-of，让 PM 无法复查。
- ❌ Takeaways 超过 5 条，或者每条都是背景介绍。

### Index / Workflow 类
- ❌ `index.md` 变成任务 checklist、coverage tracker、decision-journal 或 thesis-tracker。
- ❌ 补历史 topic index，超出本次 session 增量。
- ❌ 写入新文件却不更新 session link。
- ❌ 未过 Gate 的内容仍然写入，只在末尾标“待验证”。
- ❌ 恢复 v2 state files、standalone next-step、portfolio tracker 或 pair spread-log。

## 篇幅基准

- 写入判断表：100-250 字 + 1 张表。
- Private Research Journal：800-1800 字；低于 500 字通常没有沉淀足够 source / implication，超过 2200 字通常变成 transcript。
- Boss Brief：500-1200 字；低于 400 字通常只是摘要，超过 1500 字通常失去 PM transfer 密度。
- Topic Index Update：100-500 字；超过 700 字通常说明把 journal 内容塞进 index。
- Handoff block：150-350 字；只说明为什么现在不能沉淀，以及该交给哪个 skill。

## 与相邻 skill 的边界

- `next-step` 负责把未解决疑点变成更好的问题；本 skill 只沉淀已研究过的 insight。
- `mechanism-map` 解释行业机制、工程原理、设备链条和术语；本 skill 只消费已经想清楚的机制结论。
- `driver-map` 拆业务实质和 model driver；本 skill 只记录已验证或清楚标注置信度的 driver insight。
- `information-impact` 验证消息和 claim；本 skill 不做 claim check。
- `alpha-thesis` / `bear-pre-mortem` / `financial-model` 负责继续研究、压测和量化；本 skill 不替代这些研究动作。
- Topic `index.md` 是研究地图，不是 v2 state system；不要维护 coverage、portfolio、decision journal 或交易状态。
