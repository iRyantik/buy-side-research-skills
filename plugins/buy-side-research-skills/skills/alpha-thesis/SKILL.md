---
name: alpha-thesis
description: Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.
---

# Alpha Thesis

Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.

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
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、thesis、variant-view judgment、position / sizing、ranking、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Alpha Thesis

产出**不是**股票研究报告，而是一份**可以拿去 pitch 给 PM、能让 PM 判断要不要建仓**的单股投资逻辑。

本 skill 只处理单股 `Long-only` 或 `Short-only` thesis。任何 Long X + Short Y、hedge candidate、"X 用什么对冲"、pair trade、hedged structure 都交给 `pair-trade`。

## 心法

卖方报告和买方 thesis 最根本的区别：**买方的逻辑必须包含"为什么这个机会还存在"**。如果一个机会人人都能看到、人人都同意，那它已经被 priced in 了，不存在 alpha。所以 thesis 的核心是 **variant view**——你和 consensus 哪里不一样、为什么这个差异存在、什么会让市场逐步同意你。

没有 variant view 的"多头逻辑"不是 thesis，是叙事。叙事不赚钱。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（scenario 输入、catalyst、valuation input、priced-in、crowding、业务事实）都必须紧跟 inline clickable short anchor，如 `[S1](link)` / `[I1](link)`。
- No Orphan Truth Claim：输出前检查 thesis fact、market expectation、management / company disclosed claim、kill criteria 依据是否都有 anchor；没有就补 source、降级为 gap，或删除。

全局 source / anti-hallucination 规则已内嵌在 `Research Runtime Capsule`。本节只补充 thesis-specific 要求。

快速提醒：
- 每条事实、数字、引语、consensus 数字必须贴可点击 source；没有可靠 source 就标记 `[需查证]` / `[来源待补]`。
- 估值、priced-in、crowding、borrow、scenario 输入里的市场端数据，若本地缺失，可补公开网页 `internet source`，但必须写 provider、as-of、URL / source location，并在 `Ev` 使用 `[I1](link)`。 
- 对 market-snapshot 字段，默认顺序是先 `workspace-local / financial-data`，再 trusted third-party，最后才是 web fallback。若对象属于 A股 / 港股 / 美股，且 thesis 需要 `market_quote`、`valuation_snapshot`、`price_action` 或 `consensus`，可先调用 `trusted-market-bridge`；bridge 命中字段使用 `[LBG1](link)` 风格锚点，并在 `## Resources` 展开 `Longbridge Securities | domain | symbol.market | as-of | fallback reason`。这仍然只是 provider-derived market evidence，不升级为 company-disclosed fact。 
- `trusted-market-bridge` 在本 skill 里只服务 thesis 的市场定价层：`variant view vs consensus`、`priced-in / valuation anchor`、`price-action / crowding-like market context`。业务事实、管理层原话、客户 / 项目事实、披露 wording 仍走原有高等级 source；若 thesis 关键逻辑依赖 `driver-map`、`company-primer` 或 `mechanism-map`，继续按原路由 handoff。 
- 如果 Longbridge 返回 `scope_restricted`、`unsupported_market`、`ambiguous` 或 `unavailable`，默认继续回退到既有 web / internet source；正文不需要展开解释，只在最终 `## Resources` 写清 fallback reason。只有用户明确要求 `longbridge_only` 时才不回退。 
- 核心 thesis business fact、未披露 driver、管理层原话、客户 / 项目事实不允许自动 internet fallback；缺口继续老实标 `[需查证]` / `[来源待补]` / `not disclosed`。 
- 若首次使用 internet fallback，正文加一句：`以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。`
- Catalyst 事件、kill criteria 基线、scenario 假设依赖的事实都必须给 source；研究员概率和判断本身不需要 source。
- 不确定 URL 是否存在时写 `[link 待补]`，不得编造；sub-agent URL 抽查匹配后才可使用。

- Locality-aware market data: valuation, liquidity, price action, borrow, FX, consensus, and cross-market fields should prefer the primary listing / trading-market source at the same quality tier; global or non-home-market fallback requires a reason in the final `## Resources` list.
## Parallel Evidence Pass

只有在用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，本 skill 才按相同的 evidence bucket 启动 sub-agent / delegate worker 并行取证；sub-agent 只能返回 evidence card：

- 可拆任务：variant-view evidence、consensus / priced-in evidence、driver / catalyst evidence、kill-criteria evidence、valuation / scenario inputs。
- sub-agent 不得写最终 thesis、variant-view conclusion、trade structure、position / sizing、bull/base/bear judgment 或 PM pitch；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一 consensus gap、driver evidence、scenario inputs、catalyst timing 和 kill criteria 后再写 thesis。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## 必填章节（缺一不可，缺一项就重写）

### Primitive Preflight（先判断能不能直接写 thesis）

在写 Variant View、Bull / Base / Bear、Kill Criteria 之前，先判断 thesis 依赖的关键 driver 是否已经拆清楚。不要因为用户要求"写 thesis"就跳过这个检查。

| 检查项 | 通过标准 | 不通过时动作 |
|---|---|---|
| Revenue driver | 收入增长能拆到 price / volume / mix、backlog conversion、segment mix 或可观察 KPI | 先 handoff 到 `driver-map` |
| Margin driver | gross / EBITDA margin 的变化来源能拆到成本、mix、利用率、pricing 或 operating leverage | 先 handoff 到 `driver-map` |
| Backlog / orders | backlog、orders、book-to-bill 与收入确认的关系清楚 | 先 handoff 到 `driver-map` |
| Disclosure bucket | reported segment / revenue bucket 能对应真实业务和 model line | 先 handoff 到 `driver-map` |

若任一项不通过，不要硬写完整 thesis。先输出最小 handoff block：

```markdown
## Primitive Handoff Required

- Blocker: [哪个 driver / 披露口径没拆清]
- Why it blocks thesis: [它会影响 variant view / scenario / kill criteria 的哪一节]
- Handoff: `driver-map`
- Inputs needed: [需要补的 filing / call / KPI / segment data]
```

### 0. Trade Structure（决定后续所有节的视角）

LS 基金不预设 long-only。第一步必须明确这是哪种单股 trade，因为后续每节的写法都依赖于此。

| Structure | 说明 | Thesis 重心 | Bull/Base/Bear 含义 | Kill 形式 |
|---|---|---|---|---|
| **Long-only** | 单边做多 | 多头 thesis、上行 catalyst | 股价 + 回报 % | 基本面恶化 / valuation 击穿 |
| **Short-only** | 单边做空 | 空头 thesis、下行 catalyst | 股价 - 回报 %（Bull = 跌深、Bear = 涨） | 上行 catalyst / squeeze 风险 |

**强制约束**：
- **如果用户给出 Long X + Short Y，停止使用本 skill，改用 `pair-trade`**。
- **如果用户问 "X 用什么对冲" / "找 hedge candidate"，停止使用本 skill，改用 `pair-trade`**。
- **Short-only 的 kill criteria 写法和 Long-only 反过来**——多头担心下跌击穿，空头担心上涨 squeeze。

**Variant View 双向化**（适用所有单股 thesis）：

不只问 "vs long consensus 差多少"，要双向问：
- **vs long consensus**（多头方向）：你的数字 / view 比看多者更乐观还是更悲观？
- **vs short consensus**（空头方向）：你的数字 / view 比看空者更乐观还是更悲观？

这能防止多头 thesis 忽略聪明空头的问题，也能防止空头 thesis 只是在复述市场已经知道的坏消息。

### 1. The Trade in One Sentence

一句话讲清楚：trade structure（来自 §0）+ 标的 + 时间窗口 + 大致回报区间。

按 structure 分例：
- **Long-only**："Long XOM，未来 12-18 个月，目标 +35%（vs 隐含下行 -15%）"
- **Short-only**："Short ARKK，未来 6-9 个月，目标 -25%（vs 隐含上行 +10%）"

反例：
- "看好 X 的长期前景"——这不是 trade，是观点。
- "Long X / Short Y"——这是 pair，不是 alpha-thesis，改用 `pair-trade`。

### 2. Variant View（量化，必须有数字）

明确说出：你的关键预测和 consensus 数字差多少？

- 例："Consensus 2026 EBITDA $4.2B，我的 base case 是 $4.8B（+14%），核心差异在 [假设 X]"
- 反例："我比市场更乐观"——零信息。

如果你的核心数字和 consensus 一致，**那你没有 variant view，你只是同意 consensus**——这种情况下不存在 alpha，要么放弃这单 trade，要么重新想哪里其实不一致。

### 3. Why the Gap Exists（这是最重要的一节）

机会为什么还在那里没被收割？分类思考：

- **Information edge**：你知道一些别人不知道的事？（注意：这通常很难真正存在，且要合规）
- **Time horizon arbitrage**：市场在 punish 短期数据、忽略 2-3 年后的结构性变化？
- **Complexity / accounting**：业务复杂、报表有误读、分类错误（被当成周期股，实际是成长股；被当成成长股，实际是 melting ice cube）？
- **Behavioral / sentiment**：被讨厌、被遗忘、刚出过黑天鹅、ESG 不待见、太小没人看？
- **Structural flow**：被动资金 / 指数除名 / 大股东减持等技术性压力？

**如果你说不出 why the gap exists，停下来重新审视 variant view**——通常意味着你的 view 实际上和 consensus 一致，只是用了不同 wording。

### 4. 三个 Catalyst（每个都要具体、可定时）

什么事件会让市场开始同意你？时间？概率？事件本身要给 source；概率是研究员判断不需要 source。

按 trade structure 调整 catalyst 视角：
- **Long-only**：上行 catalyst（财报 beat、产能爬坡、capital return、监管利好）。
- **Short-only**：下行 catalyst（财报 miss、guidance cut、负面监管、debt 到期）。

例（Long-only）：
  - "Q3 财报（11 月 [公司 IR 财报日历](url)）：管理层若给出 2026 capex 指引 < $2B [当前 capex 来自 Q2 2024 call](url)，将证伪 capital cycle bear thesis（概率 60%）"
  - "OPEC+ 12 月会议 [OPEC official calendar](url)：减产延长将支撑油价 base case > $75（概率 70%）"

反例："长期来看市场会认识到价值"——这不是 catalyst，是 hope。

### 5. Bull / Base / Bear（每个都要有具体回报数字 + 概率）

按 trade structure 调整含义：

**Long-only**：
| Scenario | 关键假设 | 12-18M 回报 | 概率 | Ev |
|---|---|---|---|---|
| Bull | ... | +60% | 25% | ... |

| Base | ... | +35% | 50% | ... |
| Bear | ... | -20% | 25% | ... |

**Short-only**（数字反向：Bull = 跌深、Bear = 涨被 squeeze）：
| Scenario | 关键假设 | 12-18M 回报 | 概率 | Ev |
|---|---|---|---|---|
| Bull (空头胜) | 业绩崩 / guidance cut | -45% | 30% | ... |

| Base | 慢漏气 | -20% | 50% | ... |
| Bear (空头败) | Squeeze / 业绩好转 | +25% | 20% | ... |

**Scenario 本身（数字、概率）是研究员判断**，不需要 source。但**假设依赖的事实**（当前基线数字、历史类比案例、行业可比）必须有 source——否则假设是凭空的。

概率加权回报必须明显 > 0，且 bull/base 之间的差距、base/bear 之间的差距要符合现实。如果 bear 比 bull 还容易发生但你设了对称概率，那是自我欺骗。

### 6. Kill Criteria（具体到数字 / 事件，不允许空泛）

按 trade structure 调整 kill 形式：

**Long-only**：基本面恶化触发
- 例："若 2024Q4 单井产量下降幅度 > 18%（vs. 当前 12% [Q3 2024 10-Q](url)），decline 加速 thesis 失效"

**Short-only**：上行 catalyst 出现 / squeeze 风险
- 例："若 short interest 升至 30%+ 且 days-to-cover > 5（[FINRA SI data](url) 当前 18% / 3.2 天），squeeze 风险升温必须减仓"
- 例："若公司宣布 strategic review / activist 介入（[历史 13D 通常引发 30%+ rally](url)），空头 thesis 失效"

反例："如果基本面恶化"——空话，什么都没说。

### 7. Sizing 逻辑

基于以上的 asymmetry 和 kill criteria 的清晰程度，这个 position 应该多大？什么情况下加仓？什么情况下减仓？

通用原则：
- Kill criteria 非常明确、信号容易观察 → 可以更大仓位（风险可控）。
- Thesis 依赖 5 个连续假设都对 → 仓位要小（path 太长）。
- Catalyst 集中在某一时点 → 考虑用期权而不是正股，捕捉非对称性。
- **Short-only**：borrow availability + cost + crowded short 风险都进 sizing 考量。Single-name short 最大 sizing 应低于同 conviction 的 long（asymmetric loss）。

### 8. Key Assumptions Checklist

明确写出 thesis 依赖的关键假设。后续每个季度回来检查这些假设是否还成立。这是 thesis 的**维护手册**，也是 pre-mortem 的输入。

必填：
- 3-5 条最关键假设。
- 每条假设的当前证据 / source。
- 每条假设的反证信号。
- 哪些假设应在下一次财报或行业数据更新时复查。

## 反模式自查

- ❌ 第 0 节没明确 trade structure → 整个 thesis 模糊，重写。
- ❌ 用户说 Long X / Short Y 还继续写 alpha-thesis → 触发错 skill，改用 `pair-trade`。
- ❌ 用户问 "X 用什么对冲" 还继续写 alpha-thesis → 触发错 skill，改用 `pair-trade`。
- ❌ Variant view、scenario 或 kill criteria 依赖 revenue / margin / backlog / price-volume-mix driver，但没有先做 Primitive Preflight → 先触发 `driver-map`。
- ❌ Variant view 只 vs long consensus，没 vs short consensus → LS 视角缺失。
- ❌ Short-only 但 kill criteria 写法和 long 一样 → 没考虑 squeeze 风险。
- ❌ 第 2 节是定性的、没有具体数字 → variant view 不存在，重写。
- ❌ 第 3 节写不出来 → thesis 大概率有问题，先想清楚再继续。
- ❌ Catalyst 都是"长期"——没有具体时间 → 实际上没有 catalyst，重列。
- ❌ Bear case 回报是 -2% → bear 太弱，没认真想 bear 怎么发生。
- ❌ Kill criteria 是"如果错了我就退" → 没有可观察的具体信号，等于没有。
- ❌ 章节里大段复述业务模式 / 行业背景 → 那是 quickread 的活儿，这里只放和 thesis 直接相关的东西。

**Source 专项**
- ❌ Variant view 引用 consensus 数字但无 source → 标记或补。
- ❌ Catalyst 提到的事件（财报、监管会议、investor day）无具体日期 source → 补。
- ❌ Kill criteria 引用了"当前 X 是 Y"但 Y 没有 source → 补。
- ❌ Bull/Bear 假设引用了类比案例（"上次类似情况股票跌 30%"）但无 source → 补。
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删。
- ❌ Source 是"据报道""有传言""有人说" → 不是 source，找出处或删。
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装。

## 篇幅基准

完整产出 **800-1500 字**。这是要拿去 pitch 的东西，必须密度高、可执行。

## Journal-First Handoff

本 skill 默认产出研究观点，不再写交易状态文件。若用户要求保存，把 thesis 作为当前日期化保存路径的研究材料保存为：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-alpha-thesis.md
```

本 skill 的 `artifact_policy.naming_mode = plain`。默认继续使用 `YYYY-MM-DD-<artifact>.md`；只有文件名冲突时才交给 `new-session` 追加 `-2 / -3` 兜底，不把 qualifier 当 thesis 默认命名。

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

`research-journal` 只在 thesis 已被研究清楚、形成可复用认知增量后再吸收，不要把未验证 thesis 直接写成 memory。

如果 thesis 中出现披露口径、业务实质、model driver、source 冲突等高价值疑点，直接触发 `Research Runtime Capsule` 的 Senior Analyst Radar 提醒。若问题是 revenue / margin / backlog / price-volume-mix driver 没拆清楚，先用 `driver-map`；若问题是研究方向本身不清，再用 `next-step`。

## Workflow 联动

- 在 `stock-quickread` 之后用——quickread 帮你判断这家公司值不值得花时间，alpha-thesis 是真正建立单股观点。
- 如果 sell-side consensus、buy-side bar、priced-in assumptions 或 variant-view gap 还没有拆清，先用 `consensus-map`，不要在 thesis 里临时补一张粗糙预期表。
- 如果 variant view、scenario 或 kill criteria 依赖某个 revenue / margin driver，但该 driver 尚未拆清楚，先触发 `driver-map`，再继续写 thesis。
- 如果关键假设需要 expert call、customer / supplier channel check、survey 或 fieldwork 验证，先用 `primary-research-plan` 设计合规验证计划；不要把未执行访谈写成 evidence。
- 写完之后用 `bear-pre-mortem` 做空头压力测试。
- 第 8 节的假设清单是 `earnings-setup` 中 thesis 假设核对的输入。
- 如果用户要求 Long X + Short Y、hedge candidate、pair monitor，改用 `pair-trade`。
- 若本轮研究已经形成可复用认知增量，后续用 `research-journal` 沉淀；若仍有高价值疑点，用 `next-step` 生成下一轮研究问题。
