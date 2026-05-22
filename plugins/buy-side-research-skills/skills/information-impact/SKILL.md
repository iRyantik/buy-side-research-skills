---
name: information-impact
description: Check whether a news claim rumor note or data point is credible and research-relevant.
---

## Global Rules Capsule (v2)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 source、时间点和例外状态。默认 `[S1]`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；表后用 `[S1] = source title, as-of/filed; reference link` registry 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Source locality rule: use source quality first (`workspace-local > primary public > reputable provider/news > internet market source`), then prefer `home-market / local-language source` within the same quality tier. News / event evidence should prefer local-language sources for the issuer, main listing venue, regulator, or operating country; market data should prefer the primary listing / trading-market source. Do not maintain market-specific provider whitelists in skill rules; if using a global, English, or non-home-market fallback, state the fallback reason in `Sources:`.
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、claim impact verdict、可信度裁决、research relevance conclusion、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Information Impact

判断一条信息能不能信，以及它是否产生值得继续研究的问题。**核心价值不是写新闻解读**，而是在信息淹没时快速过滤：哪些是事实、哪些只是线索、哪些值得继续问。

如果输出把传闻当事实，或者把每条新闻都扩写成分析，本 skill 就失败了。

## 心法

先验真伪，再判断研究价值。传闻、标题党、卖方转述、社媒截图和专家片段都可能有线索价值，但在找到可靠 source 前不能当作事实。

本 skill 的工作逻辑是 **claim decomposition + evidence grading + research relevance**：
- 先把模糊消息拆成可验证 claim。
- 再给 source quality 和 verdict。
- 只有 verdict 至少达到 `Plausible but unconfirmed`，才判断是否值得继续研究。

**最重要的纪律**：`product can be used`、`theme association`、`tier-2 supplier` 不能写成 `direct supplier`。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（新闻事实、时间点、原始说法、市场反应、公司 / 监管回应）都必须紧跟可点击短 anchor，如 `[P1]` / `[I1]`。
- No Orphan Truth Claim：输出前检查 claim、source provenance、market reaction、management / company disclosed 表述是否都有 anchor；传闻只能标为 rumor / unverified。

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v2)`。本节只补充 information-impact-specific 要求。

特别强调：
- **每个事实、数字、客户关系、订单、合同、数据点必须有 source / as-of**。
- **卖方报告是观点和线索，不是事实锚点**；报告里的 fact 要单独验证。
- **社媒、论坛、聊天记录、传闻截图、社媒截图只能作线索**。
- **标题不是 source**；必须追到原文、公告、filing、transcript 或可靠报道。
- **多个 source 冲突时必须标注冲突**，不要挑一个顺手的用。

- Locality-aware news / event evidence: at the same source-quality tier, prefer home-market / local-language sources for event claims; if using global or English fallback, state the fallback reason in `Sources:`.
## Parallel Evidence Pass

只有在用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，本 skill 才按相同的 evidence bucket 启动 sub-agent / delegate worker 并行取证；sub-agent 只能返回 evidence card：

- 可拆任务：original claim source、affected company / segment exposure、financial materiality、market reaction、disconfirming evidence。
- sub-agent 不得写最终 claim impact verdict、可信度裁决、research relevance conclusion、position implication 或 next-step priority；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一 original source、source quality、direct vs indirect exposure、timeframe 和反证后再写 verdict。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## AI 的局限（必读，前置警告）

这个 skill 很容易在供应链和新闻标题上出错：

| 局限 | 影响 | Mitigation |
|---|---|---|
| **标题党误导** | 标题把弱 claim 写成强事实 | 必须追原文，不用标题做 evidence |
| **供应链关系幻觉** | AI 会把"产品可用"写成"已供货" | 强制区分 direct / tier-2 / product can be used / theme association |
| **卖方转述污染** | 卖方把 market rumor 写成行业观点 | 把 sell-side 观点和 fact 分开 |
| **时间点错配** | 老合同 / 老客户被误当成最新关系 | 所有关系写 timeframe / as-of |
| **低质量 source 放大** | 社媒截图被反复转载，看起来像多 source | 判断 source 原始性，不按转发数量加权 |
| **宏观数据过度外推** | 单个数据点被写成趋势 | 数据点只说明它能说明的范围 |

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
- "某卖方报告哪些点需要验证"
- "刚出的行业 / 宏观数据值得继续看什么"

### Batch Mode 触发
- "今天早报过一遍"
- "这几条新闻帮我筛一下"
- "把这些信息按可信度和研究价值过一下"

不要用于深度 thesis、建模、财报 setup、peer 横向比较或研究总结。若信息已经变成一个值得深挖的问题，交给 `next-step`；若研究后形成认知增量，交给 `research-journal`。

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

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| Claim 本身不可信 | Drop |
| Claim 可信但没有研究增量 | 结束，不强行扩展 |
| Claim 暴露高价值疑点 | `next-step` |
| Claim 需要建模验证影响量级 | `3-statement-model / dcf-model / comps-analysis / model-update` |
| Claim 可信且可能改变收入 / margin / backlog driver | `driver-map` |
| Claim 可信但首先需要理解技术链条、设备关系或行业机制 | `mechanism-map` |
| Claim 涉及一组潜在受益 / 受损公司 | `candidate-screener` |
| Claim 研究后形成认知增量 | `research-journal` |

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

## 与相邻 skill 的边界

- `candidate-screener` 是 outbound hypothesis → candidates；本 skill 是 inbound claim → verdict。
- `driver-map` 研究可信 claim 对 revenue / margin / backlog driver 的影响；本 skill 只先判断 claim 是否可信、是否值得继续问。
- `mechanism-map` 研究可信 claim 背后的技术链条、设备关系或行业机制；本 skill 不替代机制解释。
- `next-step` 负责把可信疑点变成更好的问题；本 skill 只判断是否值得问。
- `research-journal` 只沉淀研究过、想清楚的认知增量；本 skill 不负责沉淀。
- `3-statement-model / dcf-model / comps-analysis / model-update` 处理量级和 driver；本 skill 只判断信息是否可信及是否值得建模验证。
