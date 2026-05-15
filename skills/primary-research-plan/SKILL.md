---
name: primary-research-plan
description: Use when designing a compliant primary research, expert call, channel check, fieldwork, survey, customer, supplier, competitor, or ex-employee interview plan to validate thesis, consensus, model-driver, or industry assumptions.
---

## Global Rules Capsule (v1)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Sub-Agent Evidence Protocol：研究运行时可以用 sub-agent 并行查 source，但 sub-agent 只能返回 evidence card，不得写最终结论、ranking、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Primary Research Plan

把一个投资假设转成合规、可执行、可三角验证的 primary research plan：找谁问、问什么、不能问什么、用什么 public / non-confidential proxy 替代敏感问题，以及什么结果会改变 thesis、model 或 consensus framing。

如果输出像泛泛的访谈提纲、暗示去问 MNPI、生成虚假的专家反馈，或者没有 decision gates，本 skill 就失败了。

## 心法

Primary research 的价值不是"多问几个人"，而是把 desk research 里最关键、最脆弱、最可能改变判断的假设拿到现实世界里验证。一个好计划必须先说明它会改变哪条 thesis / model line，否则访谈越多越容易变成确认偏误。

合规边界是本 skill 的第一优先级。不能问 non-public orders、客户名单、未公开价格、未公开 contract terms、未来 guidance、内部财务、未披露产能、confidential pipeline、尚未公开的采购计划或任何 MNPI。敏感问题必须被改写成 public / historical / aggregated / directional / process proxy。

本 skill 只设计计划，不执行访谈，不编访谈结果，不把 primary research 当成已经发生的 evidence。真正的访谈、专家平台流程、compliance approval 和记录保存必须按用户机构制度执行。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 primary-research-plan-specific 要求。

特别强调：
- **计划前提必须标 source 状态**：hypothesis 来自 `consensus-map`、`driver-map`、`alpha-thesis`、filing、call、dataset 还是用户 unsourced claim，都要写清楚。
- **primary research 还没发生时不能写成 evidence**：只能写 planned source、target persona、expected evidence、decision gate。
- **专家或渠道反馈需要 provenance**：真正访谈后引用时必须记录 date、persona、source type、compliance status、是否可引用、是否匿名。
- **不提供法律意见**：只给通用 compliance guardrails；遇到敏感问题，要求先走机构 compliance / expert-network protocol。
- **不要用单一专家替代事实**：expert call 是 evidence piece，不是最终事实；必须设计 triangulation。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| 合规语境不可见 | AI 不知道用户机构具体 restricted list / wall-crossing / expert-network rules | 明确写通用红线，并要求用户遵守内部 compliance |
| 容易写 leading questions | 问题诱导专家确认 thesis | 问题先问 process / base rate / range，再问当前变化 |
| 容易追逐 anecdotes | 小样本专家反馈被过度外推 | 设计 triangulation 和 decision gates |
| 容易把敏感问题包装成正常问题 | 订单、价格、客户 pipeline 等可能触及 confidential info | 每个 persona 都列 red-line questions 和 compliant rewrite |
| 无法确认专家身份 | AI 不能验证 respondent 是否真实合适 | 输出 persona criteria，不编具体人名 |
| 易生成假结果 | 访谈计划被误写成访谈纪要 | 严禁编造 expert feedback；未执行的都标 planned |

## 触发场景

使用本 skill 当用户问：
- "这个假设应该找哪些人验证？"
- "帮我设计专家访谈计划"
- "这个 data center orders / margin gap 应该问谁"
- "怎么做 channel check"
- "怎么问客户 / 供应商 / competitor 才合规"
- "帮我写 expert call guide"
- "这个 thesis 哪些部分需要 primary research"
- "设计 survey / fieldwork / interview plan"

不要用于：
- 判断一条新闻、传闻、供应链 claim 是否可信：用 `information-impact`。
- 系统拆市场预期和 priced-in assumptions：用 `consensus-map`。
- 拆 revenue / margin / backlog / KPI 到 model driver：用 `driver-map`。
- 解释行业机制、设备链、工艺、术语：用 `mechanism-map`。
- 写完整 long / short thesis：用 `alpha-thesis`。
- 生成实际访谈纪要、专家观点或 channel check 结果：本 skill 不做。

## 输入澄清要求

如果用户没有给完整信息，先快速声明默认假设；只有研究对象、假设或合规边界完全不明时才追问。

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 研究对象 | ticker / 公司 / 行业 / 主题 / segment / KPI | 按用户原词，必要时限定到最窄可验证对象 |
| 要验证的假设 | consensus gap / driver gap / thesis assumption / mechanism gap | 从上下文抽取；无上下文则先列 hypothesis candidates |
| 决策影响 | thesis / model / earnings setup / candidate selection / abandon | 默认影响 thesis 和 model |
| 时间窗口 | next print / 3M / 12M / 2-3Y | 默认 12M，若是 channel check 则加 3M |
| 受访对象 | expert / customer / supplier / competitor / ex-employee / distributor / recruiter / dataset | 默认多 persona triangulation |
| 合规约束 | 内部 restricted list / expert network protocol / no-contact list | 默认未知，必须写 "follow firm compliance" |
| 保存需求 | 对话 / dated topic research artifact | 默认对话；用户要求保存时写 `primary-research-plan.md` |

## Mode A: Standard Primary Research Plan

用于把多个关键假设转成完整 fieldwork / expert-call / channel-check 计划。

### 输出结构

```markdown
## Verdict

[2-4 句结论先行：最值得做 primary research 的假设是什么，为什么它会改变 decision，建议先找哪类 respondent]

## 1. Research Objective / Decision Impact

一句话说明：
- 要验证的核心问题：[...]
- 会改变的决策：[alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update / sizing / abandon / candidate ranking]
- 不做 primary research 的风险：[...]

## 2. Hypothesis Register

| Hypothesis | Current evidence | Source gap | Decision impact | Priority |
|---|---|---|---|---|
| [要验证的假设] | [已有 source / 需查证] | [缺什么 evidence] | [影响 model / thesis 哪一行] | High / Medium / Low |

**Takeaway**: [哪 1-2 个假设最值得先验证]

## 3. Respondent / Source Map

| Persona / source | Why this source helps | What they can know | What they cannot be asked | Target count |
|---|---|---|---|---|
| Customer / supplier / competitor / ex-employee / expert / distributor / dataset / survey | [验证什么] | [可问的 process / historical / directional info] | [MNPI / confidential red lines] | [n] |

## 4. Compliance Guardrails

**Do not ask**
- [non-public order / customer / contract / pricing / financial / production / guidance / procurement specifics]

**Compliant rewrites**
| Sensitive question | Why risky | Safer proxy |
|---|---|---|
| [不要问客户下季度订单是多少] | non-public / confidential order info | [问采购周期是否拉长、公开项目 pipeline 是否转化、历史交付 lead time 是否变化] |

## 5. Interview / Channel-Check Guide

### Persona A: [name]

Must-ask:
1. [open-ended, non-leading, non-confidential question]
2. [...]

Nice-to-have:
1. [...]

Red-line questions:
- [不能问什么]

### Persona B: [name]

[同上]

## 6. Triangulation Plan

| Claim to verify | Source 1 | Source 2 | Source 3 | What would count as confirmation |
|---|---|---|---|---|
| [claim] | [persona / dataset] | [filing / public data] | [peer call / industry data] | [observable threshold] |

## 7. Decision Gates

| Result | Interpretation | Action |
|---|---|---|
| Confirm | [什么结果确认假设] | [advance thesis / model update] |
| Mixed | [什么结果要求继续查] | [next call / dataset / driver-map] |
| Weaken | [什么结果削弱假设] | [lower conviction / revise model] |
| Kill | [什么结果直接推翻] | [drop thesis / revisit consensus-map] |

## 8. Routing

| Finding | Next step |
|---|---|
| Primary evidence confirms variant gap | `alpha-thesis` |
| Evidence changes revenue / margin / KPI assumptions | `3-statement-model / dcf-model / comps-analysis / model-update` / `driver-map` |
| Evidence says market bar was misread | `consensus-map` |
| Evidence is a claim needing verification | `information-impact` |
| Evidence becomes earned insight | `research-journal` |

## 9. 下一步 5 个具体 follow-up questions

1. [具体到 persona / source / KPI / decision gate]
```

## Mode B: Expert Call Guide

用于单次或少量 expert calls。输出压缩成：
- objective / decision impact
- expert profile criteria
- must-ask questions
- compliant rewrites
- post-call interpretation grid

必须包含 red-line questions；不能只给问题清单。

## Mode C: Channel Check / Survey Plan

用于客户、供应商、分销商、招聘、价格、库存、lead time、采购周期、implementation backlog 等验证。

必须包含：
- sample plan：目标样本数、persona split、地域 / end-market split。
- proxy design：用 public / non-confidential proxy 替代敏感订单或客户信息。
- bias controls：避免只问 happy customers、recent buyers、single geography。
- aggregation rule：小样本只作 directional evidence，不当事实。
- decision gates：什么样的 directional evidence 足够改变模型。

## Artifact / 保存策略

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-primary-research-plan.md
```

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录，不要未解析路径就写入。

保存后的 `primary-research-plan.md` 是 research plan，不是 primary evidence，不是 earned memory。只有调研完成后形成 source-backed、合规、会改变判断的认知增量，才进入 `research-journal`。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| `consensus-map` 发现 variant gap 需要 field evidence | `primary-research-plan` |
| `driver-map` 发现 revenue / margin / KPI 假设需要客户 / 供应商验证 | `primary-research-plan` |
| `alpha-thesis` 的关键假设需要 expert / channel validation | `primary-research-plan` |
| 用户只有一条未经验证的 claim | 先 `information-impact` |
| 调研问题实际是机制 / 工程 / 设备链不清 | 先 `mechanism-map` |
| 调研问题实际是 model-driver mapping 不清 | 先 `driver-map` |
| 计划执行后需要更新数字 | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 计划执行后证据足以形成 thesis | `alpha-thesis` |
| 形成 earned insight | `research-journal` |

推荐路径：

```text
stock-quickread / industry-quickread -> consensus-map
-> mechanism-map / driver-map -> primary-research-plan
-> alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update -> research-journal
```

## 反模式自查

写完必须自查，命中就重写：

- 问题清单没有 research objective 或 decision impact。
- 没有 hypothesis register，不知道每个访谈问题验证什么。
- 没有 compliance guardrails 或 red-line questions。
- 问题暗示去问 MNPI、confidential order、客户名单、未公开价格、合同条款、未来 guidance、内部财务或采购计划。
- 敏感问题没有改写成 public / historical / aggregated / directional proxy。
- 把 planned call 写成 actual expert feedback。
- 编造具体专家姓名、公司、访谈日期或 quote。
- 只找一种 respondent，没有 triangulation。
- 用 small-N anecdote 直接推翻或确认 thesis，没有 decision gate。
- 问题是 leading question，只是在诱导专家同意 thesis。
- 没有区分 must-ask、nice-to-have、red-line questions。
- 把 primary research plan 直接写进 `research-journal` 当 earned insight。

## 篇幅基准

| Mode | 篇幅 | 表格 |
|---|---|---|
| Standard Primary Research Plan | 1200-2000 字 | 4-6 张 |
| Expert Call Guide | 700-1200 字 | 2-3 张 |
| Channel Check / Survey Plan | 1000-1800 字 | 3-5 张 |

低于 700 字通常没有足够 compliance / decision gates；超过 2200 字通常开始写 execution handbook，应压缩到最高优先级假设。

## 与相邻 skill 的边界

| Skill | 边界 |
|---|---|
| `consensus-map` | 拆市场预期和 variant gap；本 skill 只在需要 primary evidence 时设计验证计划。 |
| `driver-map` | 拆 model driver；本 skill 设计如何用客户 / 供应商 / expert / dataset 验证 driver 假设。 |
| `alpha-thesis` | 写投资观点；本 skill 不写 thesis，只验证 thesis 关键假设。 |
| `information-impact` | 先验证单条 claim 可信度；本 skill 不做 source hunting。 |
| `mechanism-map` | 解释机制和设备链；本 skill 不替代机制学习。 |
| `3-statement-model / dcf-model / comps-analysis / model-update` | 更新模型数字；本 skill 只定义什么证据会改变模型。 |
| `research-journal` | 沉淀已验证 insight；本 skill 的计划不是 earned memory。 |
