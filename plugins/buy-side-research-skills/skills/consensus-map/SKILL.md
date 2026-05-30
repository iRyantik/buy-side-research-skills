---
name: consensus-map
description: Map consensus buy-side bar priced-in assumptions revisions and variant-view gaps.
---

# Consensus Map

Map consensus buy-side bar priced-in assumptions revisions and variant-view gaps.

## Research Runtime Capsule


**三表数据前置（由 subagent 执行）：** 将 financial-data 获取委托给 subagent——1. subagent 检查 topics/company/<slug>/_cache/financial-data/internal/actuals-resolved.json 2. 不存在 → subagent 执行 /financial-data --lite <ticker>，写入后返回 3. 存在 → 主 agent 从 actuals 取所需科目。artifact 必须包含 financial-data 来源证据（source_layer 标记或 /financial-data 执行痕迹）
- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

把单股、peer cluster、行业或主题的市场预期摊开：sell-side numbers 是什么，buy-side bar 可能在哪里，价格已经隐含了什么，核心 debate 卡在哪些假设上，哪里才可能有真正的 variant view。

如果输出只是 broker rating / target price 汇总、"市场看多 / 看空"的流水账，或者直接跳成完整 long / short thesis，本 skill 就失败了。

## 心法

买方做 consensus map 不是为了知道"大家怎么想"，而是为了判断：还有没有可以赚钱的误差？误差在 revenue、margin、KPI、cycle timing、multiple、terminal value、还是 narrative framing？只有把共识拆成可验证假设，后面的 `alpha-thesis` 才不是凭感觉喊 variant view。

Consensus 不等于 sell-side EPS。真正会影响仓位的是三层东西：可见的 sell-side consensus、不可见但可推断的 buy-side bar、以及价格 / 估值 / 仓位已经隐含的 assumptions。三者不一致时，机会或风险通常就在缝里。

本 skill 是 foundation layer。它不替代 `stock-quickread` / `industry-quickread` 的 first-pass，不替代 `3-statement-model / dcf-model / comps-analysis / model-update` 的 reverse DCF 和详细建模，也不替代 `earnings-setup` 的 print-specific bar。它负责在 thesis 之前把"共识到底是什么"拆清楚。

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

## 2. 

### 预期差公式

| # | 计算 | 公式 | 输入来源 |
|---|---|---|---|
| 1 | Surprise | (Actual - Consensus) ÷ \|Consensus\| | FS, CON |
| 2 | Revision Breadth | (上调数 - 下调数) ÷ 总覆盖数 | CON |
| 3 | Implied Growth (from PE) | ROE × (1 - payout ratio) | DER |


Sell-Side Consensus Numbers

| Metric | Current consensus | 3M / 6M revision | Dispersion | Ev | Why it matters |
|---|---|---|---|---|---|
| Revenue / EBITDA / EPS / FCF / KPI | [number] | [up/down/flat] | [range/stdev if available] | [S1](./_cache/sources/consensus-pack.md) | [投资含义] |

正文 claim 示例：`Consensus FY26 EBITDA has moved down 6% over three months, while dispersion widened from 8% to 14%. [S1](./_cache/sources/consensus-pack.md)`

**Takeaway**: [市场数字共识到底集中在哪个 operating assumption]

## 3. Buy-Side / Market-Implied Bar

| Bar layer | Inference | Evidence | Confidence |
|---|---|---|---|
| Price reaction | [e.g. stock rallies despite inline prints] | [events + source] | High/Medium/Low |
| Multiple / valuation | [current multiple implies X] | [Bloomberg / CapIQ / 自算] | [confidence] |
| Options / short interest / crowding | [implied move / SI / flow clue] | [I4](https://example.com/options-and-si) | [confidence] |
| Narrative | [what holders likely need to believe] | [broker / calls / media] | [confidence] |

**Discipline**: buy-side bar 是推断，不要写成事实。

## 4. Narrative And Debate Map

| Debate | Consensus side | Skeptic / variant side | Evidence needed | Who has burden of proof |
|---|---|---|---|---|
| [debate 1] | [市场相信什么] | [反方说什么] | [KPI/source] | Bulls / Bears |

## 5. KPI / Driver Expectation Ladder

| Assumption ladder | What consensus needs | Observable KPI | Ev | Handoff if unclear |
|---|---|---|---|---|
| Revenue | [growth / orders / conversion] | [KPI] | [S1](./_cache/sources/consensus-pack.md) | `driver-map` if mapping unclear |
| Margin | [mix / pricing / utilization] | [KPI] | [S1](./_cache/sources/consensus-pack.md) | `driver-map` |

正文 claim 示例：`Market-implied expectations require backlog conversion to accelerate next year; if the observable KPI is unavailable, write [来源待补] rather than inventing it. [S1](./_cache/sources/consensus-pack.md)`
| Valuation | [multiple / terminal growth] | [multiple / FCF CAGR] | [I5](https://example.com/valuation-setup) | `3-statement-model / dcf-model / comps-analysis / model-update` |

## 6. Where Consensus Could Be Wrong

| Variant slot | Direction | Why it may be mispriced | Needed proof | Next source |
|---|---|---|---|---|
| [slot] | Long / Short | [reason] | [evidence] | [S3](./_cache/sources/variant-slot-note.md) / `next-step` |

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
| [name] | [stage] | [growth / margin / scarcity / policy] | [KPI] | [S1](./_cache/sources/consensus-pack.md) 或 GAP |

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

本 skill 的 `artifact_policy.naming_mode = optional_qualifier`。topic 总览默认继续使用 `YYYY-MM-DD-<artifact>.md`；如果这次只回答一个子问题、同日重复保存，或当前 topic 下已经堆了很多 `consensus-map`，则应改由 `new-session` 解析成 `YYYY-MM-DD-<artifact>-<qualifier>.md`。

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
