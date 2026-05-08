---
name: alpha-thesis
description: Use when building or refining a buy-side long, short, pair, or hedged investment thesis that needs a variant view, catalysts, kill criteria, scenarios, and sizing logic.
---

# Alpha Thesis

产出**不是**股票研究报告，而是一份**可以拿去 pitch 给 PM、能让 PM 判断要不要建仓**的投资逻辑。

## 心法

卖方报告和买方 thesis 最根本的区别：**买方的逻辑必须包含"为什么这个机会还存在"**。如果一个机会人人都能看到、人人都同意，那它已经被 priced in 了，不存在 alpha。所以 thesis 的核心是 **variant view**——你和 consensus 哪里不一样、为什么这个差异存在、什么会让市场逐步同意你。

没有 variant view 的"多头逻辑"不是 thesis，是叙事。叙事不赚钱。

## Source 政策

本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

快速提醒：
- 每条事实、数字、引语、consensus 数字必须贴可点击 source；没有可靠 source 就标记 `[需查证]` / `[来源待补]`。
- Catalyst 事件、kill criteria 基线、scenario 假设依赖的事实都必须给 source；研究员概率和判断本身不需要 source。
- 不确定 URL 是否存在时写 `[link 待补]`，不得编造；sub-agent URL 抽查匹配后才可使用。

## 必填章节（缺一不可，缺一项就重写）

### 0. Trade Structure（决定后续所有节的视角）

LS 基金不预设 long-only。第一步必须明确这是哪种 trade，因为后续每节的写法都依赖于此。

| Structure | 说明 | Thesis 重心 | Bull/Base/Bear 含义 | Kill 形式 |
|---|---|---|---|---|
| **Long-only** | 单边做多 | 多头 thesis、上行 catalyst | 股价 + 回报 % | 基本面恶化 / valuation 击穿 |
| **Short-only** | 单边做空 | 空头 thesis、下行 catalyst | 股价 - 回报 %（Bull = 跌深、Bear = 涨） | 上行 catalyst / squeeze 风险 |
| **Pair** | Long X + Short Y | Spread 收敛 thesis、相对论点 | Spread converge / unchanged / diverge | Spread 反向、单边公司事件 |
| **Long with hedge** | 主仓 + 对冲（option / index ETF / 单股 short） | 主仓 thesis + hedge 经济性 | 单股回报 + hedge 拖累净化后 | 主仓被砍 + hedge 失效（worst case） |

**强制约束**：
- **Pair 必须 spec 配对标的**——不能含糊"找个相关公司对冲"。明确 Long X / Short Y 的 ticker 和合理 weight（通常 dollar-neutral 或 beta-adjusted）
- **Long with hedge 必须 spec hedge 工具**——具体哪个 ETF、option strike + expiry、单股 short 的 ticker
- **Short-only 的 kill criteria 写法和 Long-only 反过来**——多头担心下跌击穿，空头担心上涨 squeeze

**Variant View 双向化**（适用所有 trade structure）：

不只问 "vs long consensus 差多少"，要双向问：
- **vs long consensus**（多头方向）：你的数字 / view 比看多者更乐观还是更悲观？
- **vs short consensus**（空头方向）：你的数字 / view 比看空者更乐观还是更悲观？

Pair 和 hedge trade 尤其重要——你的 long leg 论点 vs 多头 consensus、short leg 论点 vs 空头 consensus 必须**各自独立 sound**。Pair 不是"两边都看一下"，是"两边都有 thesis"。

### 1. The Trade in One Sentence

一句话讲清楚：trade structure（来自 §0）+ 标的 + 时间窗口 + 大致回报区间。

按 structure 分例：
- **Long-only**："Long XOM，未来 12-18 个月，目标 +35%（vs 隐含下行 -15%）"
- **Short-only**："Short ARKK，未来 6-9 个月，目标 -25%（vs 隐含上行 +10%）"
- **Pair**："Long ASML / Short AMAT，未来 12 个月，spread 收敛 15%（spread 当前 -2σ vs 5Y mean，论点：ASML EUV monopoly margin re-rating vs AMAT memory cycle drag）"
- **Long with hedge**："Long NVDA + 25% notional QQQ put（3M ATM），未来 6 个月，单股目标 +30%，hedge 锁定下行 -8%（vs 裸多头 -25%）"

反例："看好 X 的长期前景"——这不是 trade，是观点。

### 2. Variant View（量化，必须有数字）
明确说出：你的关键预测和 consensus 数字差多少？
- 例："Consensus 2026 EBITDA $4.2B，我的 base case 是 $4.8B（+14%），核心差异在 [假设 X]"
- 反例："我比市场更乐观"——零信息

如果你的核心数字和 consensus 一致，**那你没有 variant view，你只是同意 consensus**——这种情况下不存在 alpha，要么放弃这单 trade，要么重新想哪里其实不一致。

### 3. Why the Gap Exists（这是最重要的一节）
机会为什么还在那里没被收割？分类思考：
- **Information edge**：你知道一些别人不知道的事？（注意：这通常很难真正存在，且要合规）
- **Time horizon arbitrage**：市场在 punish 短期数据、忽略 2-3 年后的结构性变化？
- **Complexity / accounting**：业务复杂、报表有误读、分类错误（被当成周期股，实际是成长股；被当成成长股，实际是 melting ice cube）？
- **Behavioral / sentiment**：被讨厌、被遗忘、刚出过黑天鹅、ESG 不待见、太小没人看？
- **Structural flow**：被动资金 / 指数除名 / 大股东减持等技术性压力？

**如果说不出 why the gap exists，你的 variant view 大概率是错的**——共识那么多聪明人一致看错通常是有原因的，找不到原因说明你还没找到真正的差异点。

### 4. 三个 Catalyst（每个都要具体、可定时）
什么事件会让市场开始同意你？时间？概率？事件本身要给 source；概率是研究员判断不需要 source。

按 trade structure 调整 catalyst 视角：
- **Long-only**: 上行 catalyst（财报 beat、产能爬坡、capital return、监管利好）
- **Short-only**: 下行 catalyst（财报 miss、guidance cut、负面监管、debt 到期）
- **Pair**: spread 收敛 catalyst（long leg 业绩好转 + short leg 业绩恶化、相对估值修复事件）
- **Long with hedge**: 主仓 catalyst + hedge 失效场景（hedge 是保险，思考它可能 expire worthless 的概率）

例（Long-only）：
  - "Q3 财报（11 月 [公司 IR 财报日历](url)）：管理层若给出 2026 capex 指引 < $2B [当前 capex 来自 Q2 2024 call](url)，将证伪 capital cycle bear thesis（概率 60%）"
  - "OPEC+ 12 月会议 [OPEC official calendar](url)：减产延长将支撑油价 base case > $75（概率 70%）"

例（Pair）：
  - "Long ASML / Short AMAT pair: ASML Q3 EUV bookings > $4B [ASML guidance](url) + AMAT 储存器收入 YoY -20%，spread 收敛 8%（概率 55%）"

反例："长期来看市场会认识到价值"——这不是 catalyst，是 hope。

### 5. Bull / Base / Bear（每个都要有具体回报数字 + 概率）

按 trade structure 调整含义：

**Long-only / Long with hedge**：
| Scenario | 关键假设 | 12-18M 回报 | 概率 | 假设的事实依据（Source） |
|---|---|---|---|---|
| Bull | ... | +60% | 25% | ... |
| Base | ... | +35% | 50% | ... |
| Bear | ... | -20% | 25% | ... |

**Short-only**（数字反向：Bull = 跌深、Bear = 涨被 squeeze）：
| Scenario | 关键假设 | 12-18M 回报 | 概率 | Source |
|---|---|---|---|---|
| Bull (空头胜) | 业绩崩 / guidance cut | -45% | 30% | ... |
| Base | 慢漏气 | -20% | 50% | ... |
| Bear (空头败) | Squeeze / 业绩好转 | +25% | 20% | ... |

**Pair**（替换为 spread converge / unchanged / diverge）：
| Scenario | 关键假设 | Spread Δ | Pair 回报 | 概率 | Source |
|---|---|---|---|---|---|
| Converge | Long 跑赢 Short | -200bps | +12% | 50% | ... |
| Unchanged | Spread 不动 | 0 | 0% (carry only) | 25% | ... |
| Diverge | Pair 失效 | +300bps | -15% | 25% | ... |

**Scenario 本身（数字、概率）是研究员判断**，不需要 source。但**假设依赖的事实**（当前基线数字、历史类比案例、行业可比）必须有 source——否则假设是凭空的。

概率加权回报必须明显 > 0，且 bull/base 之间的差距、base/bear 之间的差距要符合现实。如果 bear 比 bull 还容易发生但你设了对称概率，那是自我欺骗。

### 6. Kill Criteria（具体到数字 / 事件，不允许空泛）

按 trade structure 调整 kill 形式：

**Long-only**: 基本面恶化触发
- 例："若 2024Q4 单井产量下降幅度 > 18%（vs. 当前 12% [Q3 2024 10-Q](url)），decline 加速 thesis 失效"

**Short-only**: 上行 catalyst 出现 / squeeze 风险
- 例："若 short interest 升至 30%+ 且 days-to-cover > 5（[FINRA SI data](url) 当前 18% / 3.2 天），squeeze 风险升温必须减仓"
- 例："若公司宣布 strategic review / activist 介入（[历史 13D 通常引发 30%+ rally](url)），空头 thesis 失效"

**Pair**: spread 反向、单边公司事件
- 例："若 Pair spread 反向扩大至 +1σ vs entry（当前 -2σ），论点暂时失效，减半仓"
- 例："若 short leg 公司被收购 / 重组，pair 论点立即失效，必须解 pair"

**Long with hedge**:
- 主仓 kill（同 Long-only）
- Hedge kill：hedge 工具到期前 / 被 called（option assigned）/ rebalance 触发

反例："如果基本面恶化"——空话，什么都没说。

### 7. Sizing 逻辑
基于以上的 asymmetry 和 kill criteria 的清晰程度，这个 position 应该多大？什么情况下加仓？什么情况下减仓？

通用原则：
- Kill criteria 非常明确、信号容易观察 → 可以更大仓位（风险可控）
- Thesis 依赖 5 个连续假设都对 → 仓位要小（path 太长）
- Catalyst 集中在某一时点 → 考虑用期权而不是正股，捕捉非对称性

按 trade structure 调整：

- **Short-only**: borrow availability + cost + crowded short 风险都进 sizing 考量。Single-name short 最大 sizing 应低于同 conviction 的 long（asymmetric loss）
- **Pair**:
  - Dollar-neutral 还是 beta-adjusted？给具体 ratio
  - 流动性差的腿决定整体 sizing 上限
  - Carry cost（borrow + funding）累积影响必须算进 12 个月持有总成本
- **Long with hedge**:
  - Hedge 比例（25% / 50% / 100% notional）依赖 conviction 和 catalyst 时点
  - Hedge cost 占预期回报多少？> 30% 说明 thesis 不够 asymmetric，要么不做要么不 hedge

### 8. 我假设了哪些可能错的事（列 3-5 条）
明确写出 thesis 依赖的关键假设。后续每个季度回来检查这些假设是否还成立。这是 thesis 的**维护手册**，也是 pre-mortem 的输入。

## 反模式自查

- ❌ 第 0 节没明确 trade structure → 整个 thesis 模糊，重写
- ❌ Pair 没 spec 配对标的 → 不是真 pair，是"再看一只票"
- ❌ Hedge 没 spec 工具（"用 ETF 对冲"不算） → 没法 sizing
- ❌ Variant view 只 vs long consensus，没 vs short consensus → LS 视角缺失
- ❌ Pair trade 但 long leg 论点和 short leg 论点不能各自独立 sound → 是单边赌相对，不是 pair
- ❌ Short-only 但 kill criteria 写法和 long 一样 → 没考虑 squeeze 风险
- ❌ 第 2 节是定性的、没有具体数字 → variant view 不存在，重写
- ❌ 第 3 节写不出来 → thesis 大概率有问题，先想清楚再继续
- ❌ Catalyst 都是"长期"——没有具体时间 → 实际上没有 catalyst，重列
- ❌ Bear case 回报是 -2% → bear 太弱，没认真想 bear 怎么发生
- ❌ Kill criteria 是"如果错了我就退" → 没有可观察的具体信号，等于没有
- ❌ 章节里大段复述业务模式 / 行业背景 → 那是 quickread 的活儿，这里只放和 thesis 直接相关的东西

**Source 专项**
- ❌ Variant view 引用 consensus 数字但无 source → 标记或补
- ❌ Catalyst 提到的事件（财报、监管会议、investor day）无具体日期 source → 补
- ❌ Kill criteria 引用了"当前 X 是 Y"但 Y 没有 source → 补
- ❌ Bull/Bear 假设引用了类比案例（"上次类似情况股票跌 30%"）但无 source → 补
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删
- ❌ Source 是"据报道""有传言""有人说" → 不是 source，找出处或删
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装

## 篇幅

完整产出 **800-1500 字**。这是要拿去 pitch 的东西，必须密度高、可执行。

## 状态文件契约（v1.2）

当用户要求保存 / 更新 thesis，或本 thesis 被确认为后续 tracker 的 canonical input 时，必须生成或更新：

- 单标的：`coverage/[ticker]/thesis.md`
- Pair trade：`pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`

文件顺序固定为：YAML frontmatter（第一段）→ human-readable 摘要 → 详细 thesis。YAML frontmatter 必须匹配 `FRAMEWORK.md §6.3` 的 `document_type: thesis` schema，至少覆盖：

```yaml
schema_version: 1
document_type: thesis
ticker: XOM
company_name: Exxon Mobil
coverage_area: oil_gas
industry: integrated_oil_gas
trade_structure: single_name
direction: long
created_at: 2026-05-07
updated_at: 2026-05-07
conviction: 4
health_status: active
time_horizon: 12-18M
next_catalyst: []
key_assumptions: []
kill_criteria: []
valuation_anchor: ""
expected_return_base_pct: null
downside_pct: null
sources: []
```

规则：
- ticker 使用 Bloomberg-style canonical ticker，例如 `XOM`, `700.HK`, `ASML.NA`。
- `coverage_area` 只用：`industrials`, `aerospace_defense`, `advanced_manufacturing`, `oil_gas`, `renewable`, `nuclear`, `emerging_tech`。
- 旧 thesis 已存在时，不重写历史判断；只更新 frontmatter 的 `updated_at`、health 字段和新增/变更的假设、catalyst、kill criteria，并在正文说明变更原因。

## 衔接关系

- 在 `stock-quickread` 之后用——quickread 帮你判断这家公司值不值得花时间，alpha-thesis 是真正建立观点
- 写完之后用 `bear-pre-mortem` 做空头压力测试
- 第 8 节的"假设清单"是 `earnings-setup` 中"thesis 假设核对"的输入
- 若生成 canonical thesis，后续 `decision-journal`、`thesis-tracker`、`earnings-setup`、`bear-pre-mortem` 都读取上述状态文件。
