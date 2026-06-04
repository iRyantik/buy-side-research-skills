---
name: information-impact
description: Check whether a news claim rumor note or data point is credible and research-relevant.
---

# Information Impact

Check whether a news claim rumor note or data point is credible and research-relevant.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — 数据获取链、来源验证链、证据协议、产出合约、保存合约。
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## 心法

先验真伪，再判断研究价值。传闻、标题党、卖方转述、社媒截图和专家片段都可能有线索价值，但在找到可靠 source 前不能当作事实。

本 skill 的工作逻辑是 **claim decomposition + evidence grading + research relevance**：
- 先把模糊消息拆成可验证 claim。
- 再给 source quality 和 verdict。
- 只有 verdict 至少达到 `Plausible but unconfirmed`，才判断是否值得继续研究。

**最重要的纪律**：`product can be used`、`theme association`、`tier-2 supplier` 不能写成 `direct supplier`。

## 触发场景

### Mode A 触发（Claim Check）
- "这个消息靠谱吗"
- "这个 claim 能不能信"
- "有没有 source"
- "某公司是不是进了某客户供应链"
- "这条供应链传闻有没有 source"
- "这个客户关系是真的吗"
- "这张截图能不能信"

### Mode B 触发（Research Relevance）
- "这条新闻值得继续看吗"
- "这件事对研究有什么增量"
- "这个数据点下一步该问什么"

## 输入澄清要求（必填 6 维度）

如果用户给的是一句模糊传闻，先把缺失维度补齐或标未知：

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **Claim 原文** | 用户听到的完整说法 | 原样引用，不自行加强 |
| **Company** | 主体公司 | 未知则问，不猜 |
| **Counterparty / program** | 客户、项目、供应链、政策、数据源 | 未知标 `[需查证]` |
| **Product / role** | 产品、服务、部件、关系角色 | 拆成 claim piece |
| **Timeframe** | 发生时间 / 生效时间 / source 时间 | 没有就写 `timeframe unknown` |
| **User intent** | 只查真假 / 判断研究价值 / 批量过滤 | 默认先查真假 |

如果 claim 本身会因为少一个字段而变形，先问清楚。例如"进了某客户供应链"必须区分是 direct supplier、tier-2、产品可用于某应用，还是市场主题联想。

## Mode A: Claim Check

### A.1 推理路径（必须显式）

**Step 1: 拆 claim**

| Claim piece | 要验证的问题 |
|---|---|
| company | 谁是主语 |
| customer / program | 对方是谁 / 哪个项目 |
| product_or_role | 供应什么 / 提供什么服务 |
| relationship_type | direct / tier-2 / product can be used / theme association |
| timeframe | 什么时候发生 |
| magnitude | 收入、订单、产能、利润或出货量级 |

**Step 2: 找 evidence**

按 source quality 分级：

| Level | 类型 | 可支持什么 |
|---|---|---|
| 1 | Filing、交易所公告、公司 IR、earnings call、监管 / 政府数据、客户官方公告、采购 / 合同文件 | 可支持 `Confirmed` |
| 2 | Transcript 数据库、Bloomberg / FactSet / CapIQ / Visible Alpha、行业研究机构、专家访谈平台 | 可支持 `Likely` |
| 3 | Reuters / Bloomberg News / FT / WSJ、行业媒体、公司新闻稿、卖方报告 | 需要拆 fact vs opinion |
| 4 | 社媒、论坛、聊天记录、传闻截图、个人博客、券商转述 | 只能作线索 |

**Step 3: 给 verdict**

| Verdict | 含义 | 后续 |
|---|---|---|
| `Confirmed` | 一手 source 或客户 / 公司 / 监管文件直接证实 | 可进入 Research Relevance |
| `Likely` | 多个较可靠 source 一致，但缺直接一手证据 | 可进入 Research Relevance |
| `Plausible but unconfirmed` | 有线索或单一 source，但证据不足 | 只做弱相关性判断 |
| `Unsupported` | 只有低质量来源，找不到可靠佐证 | `Drop` |
| `Contradicted` | 已有可靠 source 反向证明 | `Drop` |

### A.2 供应链 claim 硬分类

这四类必须分清：

- **direct supplier**：有一手合同、客户公告或公司确认。
- **tier-2 / indirect supplier**：通过上游或下游间接暴露，关系强度低很多。
- **product can be used**：产品理论上可用于某场景，不等于已经采购。
- **theme association**：市场把公司归进主题，但没有业务关系证据。

"X 进某客户供应链"如果只是 `product can be used` 或 `theme association`，不能写成 direct supplier。

### A.3 输出结构

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

## Batch Mode

用于早报或多条信息快速过滤。输出只保留过滤价值，不写状态文件：

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

## Artifact / 保存策略

对话输出。用户要求保存时写入 industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md。

## Source Contract

信息冲击分析处理的是"刚刚发生的事"，source freshness 比 source depth 更重要。

**密度表**：

| Section | 强制标 source | 豁免 |
|---|---|---|
| 事件定性 | 事件来源（filing URL/新闻 URL/IR PDF）+时间 | 研究员判断 |
| 价格反应 | price move % + time window → `[I#](url)` 行情源 | — |
| Consensus delta | revised consensus vs pre-event → 每个数字有 provider+date | — |
| Peer spillover | peer 价格变动的 source | — |

**完成 Gate**：写完扫 → 每个事件有 source link → 每个 price move 有行情源 → `[待查]` ≤2 → Resources 展开。

## 反模式自查

### Source 类
- ❌ 把新闻标题当 source。
- ❌ 把卖方观点当事实。
- ❌ 把社媒截图 / 聊天记录当 confirmed evidence。
- ❌ 多篇转载同一低质量来源，却当成多 source corroboration。

### Claim 类
- ❌ 混淆 direct supplier、tier-2、product can be used、theme association。
- ❌ 对 `Plausible but unconfirmed` 做强结论外推。
- ❌ 不写 timeframe，导致旧关系看起来像新关系。
- ❌ 没有拆 claim piece，直接给大结论。

### Workflow 类
- ❌ 因为一个消息"看起来重要"就写长篇 thesis。
- ❌ 对 `Unsupported` / `Contradicted` 继续扩写研究价值。
- ❌ 把每条早报都变成 follow-up，制造信息噪音。

## 篇幅基准

- Unsupported / Contradicted：100-250 字。
- 单条 Claim Check：300-700 字 + 1 张 evidence 表。
- Batch Mode：每条 1 行，最多只展开 top 1-3 条。
- 超过 900 字通常说明已经不是 filtering，应 handoff 到其他研究 skill。

