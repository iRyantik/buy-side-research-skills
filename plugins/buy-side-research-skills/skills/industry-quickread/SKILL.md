---
name: industry-quickread
description: Run a first pass on an industry theme value chain demand pocket or profit pool.
---

# Industry Quickread

Run a first pass on an industry theme value chain demand pocket or profit pool.

Deterministic binary guardrails for source legality, subagent boundary, narrative drift, and workspace safety are enforced through workspace hooks. If a hook and prose differ on a binary check, hook enforcement wins.

## Research Runtime Capsule

本 skill 独立运行时也必须遵守以下 runtime 规则；详细维护基线在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设会自动读取该文件，因此本 skill 自身必须携带可执行的规则摘要。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 inline clickable short source anchor 和例外状态。默认 `[S1](link)`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；完整 source metadata 不在表后展开，每篇 artifact 文末统一写 `## Resources`，用 `- [S1](link) = source type | source title/provider | as-of/filed | page/location | fallback reason` 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Source locality rule uses two tracks. Disclosure-fact fields follow `workspace-local > primary public > trusted third-party > web`; market-snapshot fields follow `workspace-local / financial-data > trusted third-party > web`. Within the same quality tier, prefer `home-market / local-language source`. News / event evidence should prefer local-language sources for the issuer, main listing venue, regulator, or operating country; market data should prefer the primary listing / trading-market source. Do not maintain market-specific provider whitelists in skill rules; if using a global, English, or non-home-market fallback, state the fallback reason in the final `## Resources` list.
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、industry routing、行业是否值得研究、anchor ranking、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Industry Quickread

在 30-45 分钟内把一个陌生行业 / 主题 / value chain 从噪音压缩成可研究的地图：这个行业靠什么赚钱、现在处于什么 regime、利润池在哪里、哪些 KPI 真能验证、下一步该看哪些公司或机制。

如果输出像行业入门科普、卖方 initiation 的行业章节、概念股列表，或者把行业层 driver 硬交给 `driver-map`，本 skill 就失败了。

## 心法

买方做行业 quickread 不是为了“懂行业全貌”，而是为了决定：这个行业是否值得继续花时间、应该沿哪条 profit pool / bottleneck / mispricing 路径切入、下一步是先看机制、筛 names、做 peers，还是直接放弃。

行业 first-pass 的核心不是罗列 value chain，而是找 **current regime**：供给短缺还是过剩、需求真实加速还是预期透支、价格由谁决定、利润留在 upstream / equipment / integrator / operator / distributor 哪一段。没有 regime 判断，就只是百科。

本 skill 只做到行业 triage。它不替代 `mechanism-map` 的工程 / 产业链机制拆解，不替代 `candidate-screener` 的系统找票，也不替代 `driver-map` 的公司 / segment / 披露口径到 model driver 映射。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（行业价格、库存、运价、板块表现、valuation anchor、供需事实）都必须紧跟 inline clickable short anchor，如 `[P1](link)` / `[I1](link)`。
- No Orphan Truth Claim：输出前检查行业事实、市场数据、priced-in clue、thematic claim 是否都有 anchor；internet chatter 不能写成行业事实。

全局 source / anti-hallucination 规则已内嵌在 `Research Runtime Capsule`。本节只补充 industry-quickread-specific 要求。

特别强调：
- **行业数据必须有 source / as-of**：市场规模、产能、价格、库存、订单、利用率、渗透率、装机量、出货量、TAM、政策补贴、进口 / 出口数据都必须有 source。
- **行业报告和卖方报告可作线索，不可替代一手或权威数据**：优先使用政府 / 监管数据、交易所公告、公司 filings / IR、协会数据、海关数据、权威行业机构。
- **概念股归类不是业务关联 source**：某公司被市场称为某主题受益股，不等于它真的捕获该行业利润池。
- **无法验证的行业数字必须标 `[需查证]` / `[来源待补]`**，不要为了让表格完整而编数字。
- **本 skill 只允许有限的 market-data fallback**：priced-in clue、anchor valuation、板块表现、公开行业价格 / 库存 / 运价等公开 web 数据，在本地缺失时可补 `internet source`，并在 `Ev` 使用 `[I1](link)`。 
- 对 market-snapshot 字段，默认顺序是先 `workspace-local / financial-data`，再 trusted third-party，最后才是 web fallback。若对象属于 A股 / 港股 / 美股，且本 skill 需要 `valuation_snapshot`、`price_action`、`fx_snapshot` 或 `adr_ah_premium`，可先调用 `trusted-market-bridge`；bridge 命中字段使用 `[LBG1](link)` 风格锚点，并在 `## Resources` 展开 `Longbridge Securities | domain | symbol.market | as-of | fallback reason`。这些字段只用于行业板块表现、valuation anchor、跨市场估值 framing 和 priced-in clue 的市场快照层。 
- `industry-quickread` 不消费 `market_screen`、`consensus`、`financial_snapshot`、`news` 或 `filings`。它仍然是行业 triage，不是 `candidate-screener`、`consensus-map` 或公司 truth 层的替代。 
- 如果 Longbridge 返回 `scope_restricted`、`unsupported_market`、`ambiguous` 或 `unavailable`，默认继续回退到既有 web / internet source；正文不需要展开解释，只在最终 `## Resources` 写清 fallback reason。只有用户明确要求 `longbridge_only` 时才不回退。 
- **不要把 internet chatter 写成行业事实**：theme buzz、媒体热词、论坛 / 社媒讨论不能替代行业事实、公司披露或 verified consensus。 
- 若首次使用 internet fallback，正文加一句：`以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。`
- **冲突 source 必须暴露**：例如协会出货量、公司 commentary、卖方供需模型相互冲突时，写出冲突而不是挑一个顺手数字。

- Locality-aware news / event evidence: at the same source-quality tier, prefer home-market / local-language sources for event claims; if using global or English fallback, state the fallback reason in the final `## Resources` list.
## Parallel Evidence Pass

本 skill 默认必须按行业 first-pass 的 source bucket 启动 sub-agent / delegate worker 并行取证；sub-agent 只能返回 evidence card：

- 可拆任务：industry regime、value pool、KPI / source map、anchor names、policy / macro / cycle evidence。
- sub-agent 不得写最终 industry routing、行业是否值得继续研究、anchor name priority、profit-pool conclusion 或 downstream skill decision；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一行业边界、数据 as-of、value-chain stage 和 source 冲突后再写 regime / routing。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| 行业边界模糊 | AI 容易把相邻产业链和下游应用混成一个市场 | 先定义行业边界：产品 / 客户 / 地域 / value chain stage |
| 最新供需数据滞后 | 产能、价格、库存和订单可能 1-2 个季度内大变 | 所有数据写 as-of；必要时标 `[需查证]` |
| 概念股记忆污染 | AI 容易把热门 names 当成真实 anchor | anchor names 只作定位，必须写 exposure 类型和 source 状态 |
| 行业机制幻觉 | 对工艺、设备链条、工程约束可能过度自信 | 遇到 know-how gap 交给 `mechanism-map` |
| 利润池误判 | 主题热不代表利润留在最直观环节 | 必须单独写 value capture 和 margin pressure |
| Consensus 模糊 | AI 不一定掌握最新卖方一致预期或仓位拥挤 | 只能写 clue；无 verified data 时标 `[需查证]` |

## 触发场景

使用本 skill 当用户问：
- “快速看一下这个行业 / 主题”
- “这个行业现在值不值得研究”
- “帮我做一个行业 quick read”
- “这个 value chain 利润在哪里”
- “这个行业现在处于什么周期”
- “这个主题该先看哪些 names”
- “AI data center power infrastructure / humanoid robotics / nuclear fuel cycle 这种主题先怎么切”

不要用于：
- 已经锁定某家公司，要看它卖什么、客户是谁、segment 怎么变：用 `company-primer`。
- 要解释工艺、设备链、工程原理、行业术语：用 `mechanism-map`。
- 要拆某家公司收入、margin、backlog、price/volume/mix、披露 bucket：用 `driver-map`。
- 要系统找一篮子 long / short candidates：用 `candidate-screener`。

## 输入澄清要求

如果用户给的行业 / 主题过宽，先快速补齐或声明默认假设，不要停在长问卷。

| 维度 | 含义 | 默认假设 |
|---|---|---|
| 行业边界 | 产品 / 服务 / value chain stage / 下游应用 | 按用户原词最窄可投边界定义 |
| 地域 | US / 大中华 / 全球 / 某单一市场 | 全球框架，优先标出用户常看市场的 anchor |
| 时间窗口 | 3M / 12M / 24M+ | 12M，可兼顾 3M catalyst |
| 研究目的 | 找票 / 建 thesis / 补机制 / 判断是否放弃 | 默认判断是否值得继续研究 |
| 方向 | Long / Short / Both | Both，保留 LS 视角 |
| 已知材料 | filings / sell-side / industry reports / dataset | 先查 topic `_cache/`，没有就用公开 source |

如果行业词本身可能有两种含义，先定义。例如 “nuclear” 可能指 uranium miners、conversion/enrichment、reactor operators、SMR equipment 或 utilities；必须先拆边界。

## Mode A: Standard Industry First-Pass

用于用户给出一个行业、主题或 value chain，希望快速判断研究入口。

### 输出结构

```markdown
## Verdict

[2-4 句结论先行：这个行业当前最重要的经济现实、是否值得继续研究、下一步最高杠杆动作]

## 1. 一句话行业经济现实

[谁付钱、买什么、为什么现在买、行业用什么方式变现、利润通常留在哪一段]

## 2. 当前 Regime / Cycle / Bottleneck

| 维度 | 当前判断 | Evidence | Ev |
|---|---|---|---|
| Demand | 加速 / 放缓 / 结构性替换 / 补库存 | [具体指标] | [S1](link) |

| Supply | 紧缺 / 过剩 / 长周期扩产 / 进口依赖 | [具体指标] | [source] |
| Pricing | 上行 / 下行 / 合同锁价 / spot 敏感 | [具体价格或 proxy] | [source] |
| Margin pressure | 原材料 / labor / mix / competition | [证据] | [source] |

**Takeaway**: [不是复述表格；写当前 regime 对可投资环节的含义]

## 3. Value Pool / Value Capture

| Value chain stage | 谁赚钱 | 利润来源 | 当前压力 | 可投资性 |
|---|---|---|---|---|
| Upstream / component / equipment / integrator / operator / distributor | [公司类型] | [pricing power / scarcity / installed base] | [压力] | High / Medium / Low |

**Takeaway**: [利润池是否在迁移；主题热度和利润捕获是否错位]

## 4. KPI / Source Map

| 要验证的问题 | KPI / proxy | 最好 source | 频率 | 为什么重要 |
|---|---|---|---|---|
| Demand 是否真实 | orders / backlog / shipment / utilization | [source type] | 月度 / 季度 | [投资含义] |
| Pricing 是否能传导 | ASP / contract price / spread | [source type] | [频率] | [投资含义] |

## 5. Demand / Supply / Pricing / Margin 压缩判断

- Demand: [1-2 句，必须有 evidence 或标 `[需查证]`]
- Supply: [1-2 句]
- Pricing: [1-2 句]
- Margin: [1-2 句]

## 6. Anchor Names（只作定位，不做个股 quickread）

| Name | Market | Value chain role | Exposure 类型 | 为什么是 anchor | Ev |
|---|---|---|---|---|---|
| [ticker/company] | [US/A/HK/etc.] | [stage] | direct / indirect / thematic / [需查证] | [定位作用] | [S1](link) 或 GAP |


**Discipline**: anchor names 最多 3-5 个；不要在这里写完整公司分析。

## 7. Priced-in / Consensus Clue

[当前市场可能在 price 什么：growth、margin、capacity tightness、policy、rate、cycle turn。没有 verified consensus / valuation 数据时，明确写 `[需查证]`。]

## 8. Routing

| 发现 | 下一步 |
|---|---|
| 行业机制 / 工程 / 设备链不清 | `mechanism-map` |
| 需要系统找 long / short names | `candidate-screener` |
| 已有 3-8 个核心公司要横向比较 | `peer-deep-dive` |
| 某个 anchor name 值得单独看 | `stock-quickread` |
| 行业 / 主题的 priced-in、buy-side bar 或 consensus debate 不清 | `consensus-map` |
| 某家公司 / segment / bucket 到 model driver 不清 | `driver-map` |

## 9. 下一步 5 个具体问题

1. [具体到某个 KPI / source / 文件 / 数据集能回答]
```

## Mode B: Tight Triage

用于用户只需要判断“值不值得继续看”。输出压缩为：
- Verdict
- 当前 regime
- value capture
- 3 个关键 KPI / source
- 3 个 anchor names
- 下一步最高杠杆动作

低于 600 字时必须牺牲细节但不能牺牲 source discipline；没有 source 就标 `[需查证]`。

## Mixed Mode

当用户同时问“行业怎么看 + 有哪些票”时，不要把本 skill 扩展成完整 screener。

处理顺序：
1. 先用 Industry First-Pass 定义行业经济现实、regime、value pool。
2. 只给 3-5 个 anchor names 作地图定位。
3. 如果用户要完整 candidate list，明确 handoff 到 `candidate-screener`。
4. 如果用户已经给了一组 companies，handoff 到 `peer-deep-dive`。

## Artifact / 保存策略

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-industry-quickread.md
```

本 skill 的 `artifact_policy.naming_mode = optional_qualifier`。topic 级 first-pass 默认继续使用 `YYYY-MM-DD-<artifact>.md`；如果这次只覆盖某个 demand pocket、value-chain slice 或子行业问题，则应改由 `new-session` 解析成 `YYYY-MM-DD-<artifact>-<qualifier>.md`。

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录，不要未解析路径就写入。

保存后的 `industry-quickread.md` 是 triage artifact，不是 earned memory。只有研究清楚、source-backed、会改变判断的认知增量，才进入 `research-journal`。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 行业 / 主题刚进入 radar，需要 first-pass | `industry-quickread` |
| 行业机制、工程原理、设备链、工艺、术语不清 | `mechanism-map` |
| 需要从行业逻辑找 long / short candidates | `candidate-screener` |
| 已有一组 anchor companies，需要横向比较 | `peer-deep-dive` |
| 单个公司值得快速判断 | `stock-quickread` |
| 行业 / 主题 market expectations、priced-in assumptions 或 variant gap 不清 | `consensus-map` |
| 公司业务基础、segment / KPI 演变不清 | `company-primer` |
| 公司 / segment / 产品线 / 披露 bucket 到 model driver 不清 | `driver-map` |
| 行业判断已经形成 thesis 差异 | `alpha-thesis` |
| 行业判断需要量化进模型 | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 行业 / 主题关键假设需要 expert call、channel check、survey 或 fieldwork 验证 | `primary-research-plan` |
| 形成可复用认知增量 | `research-journal` |

推荐行业路径：

```text
new-session -> ingest -> industry-quickread -> consensus-map -> mechanism-map
-> candidate-screener / peer-deep-dive -> stock-quickread
-> driver-map -> primary-research-plan
-> alpha-thesis / 3-statement-model / dcf-model / comps-analysis / model-update -> research-journal
```

## 反模式自查

写完必须自查，命中就重写：

- 只写行业科普、政策背景、历史沿革，没有 current regime。
- 把 value chain 画成列表，但不判断谁 capture profit。
- Demand / supply / pricing / margin 没有任何 source 或 `[需查证]` 标记。
- 数据表没有 takeaway，或 takeaway 只是复述表格。
- anchor names 超过 5 个，变成伪 `candidate-screener`。
- anchor names 没有 exposure 类型，导致 direct / indirect / thematic 混在一起。
- 把“行业 driver”泛化交给 `driver-map`；`driver-map` 只处理公司 / segment / 产品线 / 披露 bucket 到 model driver。
- 遇到工程机制、设备链条或工艺不清，还硬写行业解释；应触发 `mechanism-map`。
- 写 “长期受益 / 空间广阔 / 景气上行” 但没有 KPI。
- 写 “priced in / not priced” 但没有估值、consensus、股价反应或 `[需查证]`。
- 把卖方主题归类当作业务关联 source。
- 没有给下一步 5 个具体问题，导致研究员不知道怎么继续。

## 篇幅基准

| Mode | 篇幅 | 表格 |
|---|---|---|
| Standard Industry First-Pass | 1200-1800 字 | 3-4 张 |
| Tight Triage | 600-900 字 | 1-2 张 |
| Mixed Mode | 1500-2200 字 | 3-5 张 |

低于 600 字通常 source / regime / value pool 不足；超过 2200 字通常已经越界到 `mechanism-map`、`candidate-screener` 或 `peer-deep-dive`。

## 与相邻 skill 的边界

| Skill | 边界 |
|---|---|
| `mechanism-map` | 解释行业机制、工程原理、设备链条、工艺流程、术语和 value-capture 机制；本 skill 只识别是否需要它。 |
| `driver-map` | 处理公司 / segment / 产品线 / 披露 bucket 到 revenue、margin、backlog、price/volume/mix model driver；不是泛行业 driver 拆解。 |
| `candidate-screener` | 从 hypothesis / industry logic 系统找 long / short candidates；本 skill 只给 3-5 个 anchor names。 |
| `peer-deep-dive` | 对 3-8 家公司做横向深研、排序和 cross-cut insight；本 skill 不做完整 peer comparison。 |
| `stock-quickread` | 快速看单家公司；本 skill 只判断行业和 anchor。 |
| `consensus-map` | 系统拆行业 / 主题的 sell-side consensus、buy-side bar、priced-in assumptions 和 variant-view gap；本 skill 只给 clue。 |
| `company-primer` | 梳理单家公司业务基础、历史演变和 disclosure evolution；本 skill 不写公司基础研究。 |
| `alpha-thesis` | 写 variant view、catalyst、kill criteria；本 skill 只提供 thesis 起点。 |
| `primary-research-plan` | 设计合规 expert call、channel check、survey 和 fieldwork 计划；本 skill 只识别需要 primary evidence 的假设。 |
