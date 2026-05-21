---
name: consensus-map
description: Map consensus buy-side bar priced-in assumptions revisions and variant-view gaps.
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
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、consensus conclusion、variant-view judgment、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Consensus Map

把单股、peer cluster、行业或主题的市场预期摊开：sell-side numbers 是什么，buy-side bar 可能在哪里，价格已经隐含了什么，核心 debate 卡在哪些假设上，哪里才可能有真正的 variant view。

如果输出只是 broker rating / target price 汇总、"市场看多 / 看空"的流水账，或者直接跳成完整 long / short thesis，本 skill 就失败了。

## 心法

买方做 consensus map 不是为了知道"大家怎么想"，而是为了判断：还有没有可以赚钱的误差？误差在 revenue、margin、KPI、cycle timing、multiple、terminal value、还是 narrative framing？只有把共识拆成可验证假设，后面的 `alpha-thesis` 才不是凭感觉喊 variant view。

Consensus 不等于 sell-side EPS。真正会影响仓位的是三层东西：可见的 sell-side consensus、不可见但可推断的 buy-side bar、以及价格 / 估值 / 仓位已经隐含的 assumptions。三者不一致时，机会或风险通常就在缝里。

本 skill 是 foundation layer。它不替代 `stock-quickread` / `industry-quickread` 的 first-pass，不替代 `3-statement-model / dcf-model / comps-analysis / model-update` 的 reverse DCF 和详细建模，也不替代 `earnings-setup` 的 print-specific bar。它负责在 thesis 之前把"共识到底是什么"拆清楚。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v2)`。本节只补充 consensus-map-specific 要求。

特别强调：
- **consensus 数字必须写 provider / as-of / metric definition**：例如 Visible Alpha、FactSet、Bloomberg、CapIQ、company-collected consensus；没有可靠 provider 时写 `[需查证]`，不要估。
- **broker notes 只能证明 narrative，不等于 consensus dataset**：可以引用为"某类多空论点"，但不能用 2-3 篇报告冒充市场一致预期。
- **buy-side bar 必须标为推断**：用 price reaction、revision breadth、multiple expansion、options implied move、short interest、crowding、call transcript Q&A 等推断时，必须写"推断依据"和不确定性。
- **market-implied assumptions 必须说明方法**：倍数反推、reverse DCF、required CAGR、implied margin、bear-implied downside 不能只给结论；如果没有模型支撑，写成 clue 并 handoff 到 `3-statement-model / dcf-model / comps-analysis / model-update`。
- **revision direction 要有时间窗**：3M / 6M / since last print / since investor day，不要写"最近上修"却没有 as-of。
- **没有数据时不要假装完整**：表格允许出现 `[需查证]`、`[来源待补]`、`not disclosed`，但不能填 AI 猜测。

## Parallel Evidence Pass

只有在用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，本 skill 才按相同的 evidence bucket 启动 sub-agent / delegate worker 并行取证；sub-agent 只能返回 evidence card：

- 可拆任务：consensus numbers / as-of、revision direction、buy-side bar evidence、market-implied assumption inputs、debate map sources。
- sub-agent 不得写最终 consensus conclusion、priced-in verdict、variant-view gap、thesis handoff 或 earnings setup decision；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一 provider、metric definition、as-of、time window 和 inference label 后再写 conclusion。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| 最新 consensus 可能不可得 | VA / FactSet / Bloomberg 数据变化快，AI 记忆滞后 | 所有 consensus 数字标 provider 和 as-of；缺失写 `[需查证]` |
| buy-side bar 不可直接观测 | 容易把 sell-side consensus 当真实市场预期 | 明确区分 observed consensus 和 inferred bar |
| 价格隐含假设需要模型 | AI 容易凭倍数喊 expensive / cheap | 只做轻量反推；详细量化交给 `3-statement-model / dcf-model / comps-analysis / model-update` |
| 行业 / 主题 consensus 分散 | 没有统一 EPS consensus，容易写成叙事汇总 | 用 KPI、anchor names、basket / peer multiple 和 debate map 代替伪精确 |
| Narrative 容易受热门主题污染 | 市场热词不代表真正 priced-in | 必须回到 KPI、revision、multiple、price reaction 和 source |
| Consensus 和 thesis 容易混在一起 | 输出会过早站队 | 只定位 gap，不写完整投资结论 |

## 触发场景

使用本 skill 当用户问：
- "NVDA / ETN / GE 现在市场到底 priced in 什么？"
- "这个行业 consensus 在哪里？"
- "buy-side bar 和 sell-side consensus 差在哪？"
- "市场现在在 debate 什么？"
- "我和 consensus 的差异怎么定位？"
- "这条主题是不是已经 crowded / priced in？"
- "帮我做一个 consensus map / expectations map / variant view setup"

不要用于：
- 只是陌生公司 first-pass：先用 `stock-quickread`。
- 只是陌生行业 / 主题 first-pass：先用 `industry-quickread`。
- 要写完整 long / short thesis、catalyst、kill criteria：用 `alpha-thesis`。
- 要做财报前后 print bar、implied move、beat / miss setup：用 `earnings-setup`。
- 要量化 reverse DCF、三表、comps、scenario valuation：用 `3-statement-model / dcf-model / comps-analysis / model-update`。
- 要拆公司 / segment / disclosed KPI 到 revenue / margin driver：用 `driver-map`。

## 输入澄清要求

如果用户没有给完整信息，先快速补齐默认假设；只有对象或时间窗完全不清时才追问。

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 对象 | 单股 / peer set / 行业 / 主题 | 按用户原词；ticker 优先单股，行业词优先 industry/theme |
| 时间窗 | 3M / 6M / 12M / next print / 2-3Y | 12M，用 3M revision 观察边际 |
| 方向 | Long / Short / Both | Both，保留 LS 视角 |
| 数据源 | VA / FactSet / Bloomberg / CapIQ / broker / filings / price data | 优先 topic `_cache/`，否则标 source need |
| 共识层级 | sell-side numbers / buy-side bar / market-implied / narrative | 默认三层都拆 |
| 输出深度 | quick map / standard map / thesis handoff | 默认 standard map |

若用户给的是行业 / 主题，不要强行制造 EPS consensus；用 KPI consensus、basket / anchor names、peer valuation、revision breadth 和 narrative debate 组成 map。

## Mode A: Single-Name Consensus Map

用于单家公司、单个 ticker 或已锁定的 stock idea。

### 输出结构

```markdown
## Verdict

[2-4 句结论先行：当前 consensus / buy-side bar / market-implied 假设在哪里；最大的 variant slot 是什么；是否足够进入 alpha-thesis / model]

## 1. Scope / As-of / Source Quality

| Item | Current setting |
|---|---|
| Object | [ticker / company] |
| Time window | [3M / 6M / 12M / next print] |
| Consensus source | [provider + as-of / 需查证] |
| Market data source | [price / multiple / options / short interest source] |
| Confidence | High / Medium / Low |

**Takeaway**: [本 map 最可靠和最薄弱的地方]

## 2. Sell-Side Consensus Numbers

| Metric | Current consensus | 3M / 6M revision | Dispersion | Ev | Why it matters |
|---|---|---|---|---|---|
| Revenue / EBITDA / EPS / FCF / KPI | [number] | [up/down/flat] | [range/stdev if available] | S1@[date] | [投资含义] |

Sources: `S1 = [provider/source title], as-of [date], [link/location]`.

**Takeaway**: [市场数字共识到底集中在哪个 operating assumption]

## 3. Buy-Side / Market-Implied Bar

| Bar layer | Inference | Evidence | Confidence |
|---|---|---|---|
| Price reaction | [e.g. stock rallies despite inline prints] | [events + source] | High/Medium/Low |
| Multiple / valuation | [current multiple implies X] | [Bloomberg / CapIQ / 自算] | [confidence] |
| Options / short interest / crowding | [implied move / SI / flow clue] | [source] | [confidence] |
| Narrative | [what holders likely need to believe] | [broker / calls / media] | [confidence] |

**Discipline**: buy-side bar 是推断，不要写成事实。

## 4. Narrative And Debate Map

| Debate | Consensus side | Skeptic / variant side | Evidence needed | Who has burden of proof |
|---|---|---|---|---|
| [debate 1] | [市场相信什么] | [反方说什么] | [KPI/source] | Bulls / Bears |

## 5. KPI / Driver Expectation Ladder

| Assumption ladder | What consensus needs | Observable KPI | Ev | Handoff if unclear |
|---|---|---|---|---|
| Revenue | [growth / orders / conversion] | [KPI] | S1@latest | `driver-map` if mapping unclear |
| Margin | [mix / pricing / utilization] | [KPI] | S1@latest | `driver-map` |

Sources: `S1 = [source title/provider], as-of [date], [link/location]`.
| Valuation | [multiple / terminal growth] | [multiple / FCF CAGR] | [source] | `3-statement-model / dcf-model / comps-analysis / model-update` |

## 6. Where Consensus Could Be Wrong

| Variant slot | Direction | Why it may be mispriced | Needed proof | Next source |
|---|---|---|---|---|
| [slot] | Long / Short | [reason] | [evidence] | [source/action] |

## 7. What Would Change Consensus

- [Catalyst / data point / competitor print / company disclosure that would force revisions]
- [What would change sell-side numbers]
- [What would change buy-side bar]
- [What would change market-implied assumptions]

## 8. Routing

| Finding | Next step |
|---|---|
| Variant gap is clear and driver support exists | `alpha-thesis` |
| Price-implied assumptions need quantification | `3-statement-model / dcf-model / comps-analysis / model-update` |
| Next print bar / implied move matters | `earnings-setup` |
| Revenue / margin / KPI mapping unclear | `driver-map` |
| Mechanism / value-capture premise unclear | `mechanism-map` |
| Need field checks / channel work | `primary-research-plan` |

## 9. 下一步 5 个具体问题

1. [具体到 metric / provider / filing / dataset / call transcript 能回答]
```

## Mode B: Industry / Theme Consensus Map

用于行业、主题、value chain 或 demand pocket 的共识地图。不要伪造单一 EPS consensus；用可观察 KPI 和 anchor-name expectation 来替代。

### 输出结构差异

在 Standard 结构基础上做以下替换：

| Single-name section | Industry/theme 替换 |
|---|---|
| Sell-side numbers | KPI consensus / demand forecast / capacity / pricing / order trend / policy expectation |
| Buy-side bar | Theme crowding、basket performance、anchor multiple expansion、revision breadth、fundamental debate |
| KPI ladder | Demand / supply / pricing / margin pressure ladder |
| Variant slots | 哪个 value-chain stage 或 anchor group 的预期最可能错 |

必须包含 3-5 个 anchor names，但只用于定位 consensus，不做完整个股 quickread。

```markdown
## Anchor Expectation Table

| Anchor | Role in theme | What market seems to price | Key KPI | Ev |
|---|---|---|---|---|
| [name] | [stage] | [growth / margin / scarcity / policy] | [KPI] | S1@latest 或 GAP |

Sources: `S1 = [source title/provider], as-of [date], [link/location]`.
```

## Mode C: Tight Expectations Check

用于用户只问"是不是 priced in"或"bar 高不高"。

输出压缩为：
- Verdict
- 3 层 expectations：sell-side / buy-side inferred / market-implied
- 2-3 个核心 debate
- 3 个会改变 consensus 的数据点
- 下一步 routing

600-900 字；低于 600 字通常不能同时覆盖 source、bar 和 routing。

## Artifact / 保存策略

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-consensus-map.md
```

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录，不要未解析路径就写入。

保存后的 `consensus-map.md` 是 foundation artifact，不是 earned memory。只有研究清楚、source-backed、会改变判断的认知增量，才进入 `research-journal`。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 公司或行业 first-pass 只给了 consensus clue，需要系统摊开预期 | `consensus-map` |
| 需要快速判断陌生公司是否值得看 | `stock-quickread` |
| 需要快速判断行业 / 主题是否值得看 | `industry-quickread` |
| consensus gap 已清楚且 driver 已拆清 | `alpha-thesis` |
| market-implied assumptions 需要模型量化 | `3-statement-model / dcf-model / comps-analysis / model-update` |
| print-specific bar、implied move 或 post-print read-through 是核心问题 | `earnings-setup` |
| company / segment / disclosed KPI 到 model driver 不清 | `driver-map` |
| 行业机制、工程原理、设备链、工艺或 value-capture 机制不清 | `mechanism-map` |
| 需要专家访谈、客户 / 供应链验证或渠道检查 | `primary-research-plan` |
| 形成可复用认知增量 | `research-journal` |

推荐单股路径：

```text
new-session -> ingest -> stock-quickread -> consensus-map
-> company-primer / mechanism-map / driver-map
-> primary-research-plan / peer-deep-dive
-> alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update -> research-journal
```

推荐行业 / 主题路径：

```text
new-session -> ingest -> industry-quickread -> consensus-map
-> mechanism-map / candidate-screener / peer-deep-dive
-> stock-quickread -> driver-map -> primary-research-plan
-> alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update
-> research-journal
```

## 反模式自查

写完必须自查，命中就重写：

- 只汇总 broker ratings / target prices，没有拆 assumptions。
- 把 sell-side EPS 当成完整 market consensus，没有 buy-side bar 或 market-implied layer。
- Consensus 数字没有 provider、as-of 或 metric definition。
- 写 "priced in / not priced in" 但没有 valuation、price reaction、revision、options、short interest、crowding 或 `[需查证]`。
- buy-side bar 推断没有标为推断。
- 行业 / 主题模式伪造统一 consensus number，而不是用 KPI / anchor / basket / debate。
- 没有区分 long consensus 和 short / skeptic view。
- Debate map 是通用 SWOT，不是当前市场实际争论的 KPI / event / assumption。
- 直接写成完整 `alpha-thesis`，包含 position sizing、kill criteria 或 scenario returns。
- print-specific bar 明显是核心问题却不路由 `earnings-setup`。
- reverse DCF / implied CAGR 需要模型却硬算成精确结论；应 handoff `3-statement-model / dcf-model / comps-analysis / model-update`。
- revenue / margin / backlog / KPI 到 model driver 不清，却不 handoff `driver-map`。
- 表格没有 takeaway，或 takeaway 复述表格。
- 下一步问题空泛，不能被具体 source / dataset / filing 回答。

## 篇幅基准

| Mode | 篇幅 | 表格 |
|---|---|---|
| Single-Name Consensus Map | 1200-1800 字 | 4-6 张 |
| Industry / Theme Consensus Map | 1300-2000 字 | 4-6 张 |
| Tight Expectations Check | 600-900 字 | 1-2 张 |

低于 600 字通常 source、bar、debate 或 routing 不足；超过 2200 字通常已经越界到 `alpha-thesis`、`3-statement-model / dcf-model / comps-analysis / model-update`、`earnings-setup` 或 `peer-deep-dive`。

## 与相邻 skill 的边界

| Skill | 边界 |
|---|---|
| `stock-quickread` | 给单家公司 first-pass 和简版 consensus clue；本 skill 系统拆 expectations stack。 |
| `industry-quickread` | 给行业 first-pass 和 priced-in clue；本 skill 深拆行业 / 主题 consensus、bar 和 debate。 |
| `alpha-thesis` | 形成 long / short variant view、catalyst、scenario、kill criteria；本 skill 只定位 gap 和 proof burden。 |
| `3-statement-model / dcf-model / comps-analysis / model-update` | 量化 reverse DCF、三表、scenario valuation 和 sensitivity；本 skill 只做轻量 market-implied framing。 |
| `earnings-setup` | 处理 next print / post-print 的 bar、implied move 和 setup；本 skill 处理非 print-specific 的共识地图。 |
| `driver-map` | 处理公司 / segment / 产品线 / 披露 bucket 到 revenue、margin、backlog、price/volume/mix model driver；本 skill 不重写 driver 拆解。 |
| `mechanism-map` | 解释行业机制、工程原理、设备链条、工艺流程和 value-capture 机制；本 skill 只标出机制 gap。 |
| `peer-deep-dive` | 对多家公司做横向深研和排序；本 skill 只在需要时比较 peer consensus / revision / valuation expectations。 |
| `research-journal` | 只吸收已经验证、会改变判断的 earned insight；本 skill 的 map 本身不是 memory。 |
