---
name: information-impact
description: Use when checking whether a news item, rumor, supply-chain claim, sell-side note, data point, or expert comment is credible and worth follow-up research.
---

# Information Impact

结论先行：这个 skill 在 v3 里只做两件事：判断信息能不能信，以及它是否产生值得继续研究的问题。它不是组合影响工具，不维护状态文件，也不把无关信息落盘。

## Core Principle

先验真伪，再判断研究价值。传闻、标题党、卖方转述、社媒截图和专家片段都可能有线索价值，但在找到可靠 source 前不能当作事实。

默认遵守 `CLAUDE.md §3`。本 skill 不维护独立 source policy；任何事实、数字、客户关系、订单、合同、数据点、管理层表述都必须有 source / as-of。卖方报告是观点和线索，不是事实锚点。

## When To Use

- "这个消息靠谱吗"
- "这条新闻怎么看"
- "这个 claim 能不能信"
- "有没有 source"
- "X 公司是不是进了 SpaceX 供应链"
- "这条供应链传闻有没有 source"
- "Goldman / Morgan Stanley 这份报告关键点是什么，哪些需要验证"
- "刚出的 EIA / PMI / CPI 数据值得继续看什么"
- "今天早报过一遍"

不要用于深度 thesis、建模、财报 setup、peer 横向比较或研究总结。若信息已经变成一个值得深挖的问题，交给 `next-step`；若研究后形成认知增量，交给 `research-journal`。

## Source Quality

直接使用 `CLAUDE.md §3` 的 1-4 级 source 质量框架：

| Level | 类型 | 用法 |
|---|---|---|
| 1 | Filing、交易所公告、公司 IR、earnings call、监管 / 政府数据、客户官方公告、采购 / 合同文件 | 可以支撑 `Confirmed`，但仍要标日期 / as-of |
| 2 | Transcript 数据库、Bloomberg / FactSet / CapIQ / Visible Alpha、行业研究机构、专家访谈平台 | 可支撑 `Likely`，注意口径和样本偏差 |
| 3 | Reuters / Bloomberg News / FT / WSJ、行业媒体、卖方报告、公司新闻稿 | 需要拆分 fact vs opinion；通常不能单独支撑强 claim |
| 4 | 社媒、论坛、聊天记录、传闻截图、社媒截图、个人博客、券商转述 | 只能作线索，不能作事实依据 |

## Mode A: Claim Check

目标是把一句模糊消息拆成可验证 claim，并给出 verdict。没有可靠 source 时，宁可说 `[来源待补]`，不要把线索升格成事实。

### Verdict

| Verdict | 含义 | 后续 |
|---|---|---|
| `Confirmed` | 一手 source 或客户 / 公司 / 监管文件直接证实 | 可进入 Research Relevance |
| `Likely` | 多个较可靠 source 一致，但缺直接一手证据 | 可进入 Research Relevance |
| `Plausible but unconfirmed` | 有线索或单一 source，但证据不足 | 只做弱相关性判断，避免外推 |
| `Unsupported` | 只有低质量来源，找不到可靠佐证 | `Drop` |
| `Contradicted` | 已有可靠 source 反向证明 | `Drop` |

### Claim Pieces

把 claim 拆成这些字段：

| Field | Meaning |
|---|---|
| `company` | 主语公司 |
| `customer / program` | 客户、项目、平台或 counterparty |
| `product_or_role` | 产品、服务、部件或角色 |
| `relationship_type` | 直接、间接、tier-N、技术适配、主题联想 |
| `timeframe` | 时间窗口 |
| `magnitude` | 收入、订单、产能、利润、出货量等量级 |

供应链 claim 必须区分：

- **direct supplier**：有一手合同、客户公告或公司确认。
- **tier-2 / indirect supplier**：通过上游或下游间接暴露，关系强度低很多。
- **product can be used**：产品理论上可用于某场景，不等于已经采购。
- **theme association**：市场把公司归进主题，但没有业务关系证据。

这四类不能混用。"X 进 SpaceX 供应链"如果只是 `product can be used` 或 `theme association`，不能写成 direct supplier。

## Mode B: Research Relevance

只有 Mode A verdict 至少达到 `Plausible but unconfirmed`，才判断是否值得继续研究。

判断标准不是"有没有新闻价值"，而是它是否可能改变：

- 业务实质理解
- revenue / margin / backlog / price-volume-mix driver
- 市场预期或 consensus framing
- peer group / valuation framework
- 研究优先级
- 一个 `Senior Analyst Radar` 识别出的怪异点

如果有高价值疑点，输出 1-2 个最值得问 AI 的问题，并建议触发 `next-step`。如果只是确认了一个事实但没有研究增量，可以结束，不要强行扩展。

## Single Claim Output

```markdown
## Claim Check

**Verdict**: Confirmed / Likely / Plausible but unconfirmed / Unsupported / Contradicted
**Bottom line**: [一句话判断，直接说能不能信]

| Claim piece | Evidence found | Source quality | Read-through |
|---|---|---|---|
| [claim 拆分项] | [证据摘要 + source / as-of] | 1 / 2 / 3 / 4 | direct / indirect / not proven |

**What not to infer**
- [不能从该消息外推出什么]

**Research relevance**
- 是否值得继续研究：Yes / No
- 为什么：[一句话]
- 可以问 AI：[1-2 个问题]
```

若 verdict 为 `Unsupported` 或 `Contradicted`，默认短输出：

```markdown
**Verdict**: Unsupported / Contradicted
**Bottom line**: [为什么不能信，或被什么 source 反驳]
**Action**: Drop
```

## Batch Mode

用于"今天早报过一遍"、"批量看这些新闻"、"这几条信息帮我筛一下"。

输出只保留过滤价值，不写状态文件：

```markdown
## Information Filter

| Title | Source quality | Verdict | Research relevance | Action |
|---|---|---|---|---|
| [标题] | 1 / 2 / 3 / 4 | [verdict] | [Yes / No + 一句话] | Drop / Ask 1-2 AI questions / Trigger next-step / Save later via research-journal |
```

Action 只能是：

- `Drop`
- `Ask 1-2 AI questions`
- `Trigger next-step`
- `Save later via research-journal`

`Unsupported` / `Contradicted` 默认 `Drop`。除非用户明确要求审计轨迹，否则不保存。

## Common Mistakes

- 把卖方观点当作事实：`Goldman thinks X` 只是观点，里面的 fact 需要单独验证。
- 把单一新闻标题当作 confirmed claim：标题不是 source，必须追到原始材料。
- 混淆 direct supplier、tier-2、product can be used、theme association。
- 对 `Plausible but unconfirmed` 的 claim 做强结论外推。
- 因为一个消息"看起来重要"就写长篇分析。本 skill 只负责过滤；深挖交给 `next-step` 或其他研究 skill。
- 找不到 source 却不标 `[来源待补]`。
