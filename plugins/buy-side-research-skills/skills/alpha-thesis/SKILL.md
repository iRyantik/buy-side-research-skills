---
name: alpha-thesis
description: Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.
---

# Alpha Thesis

Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.

上游如果还没有把 bull/base/bear 的赔率、implied value 和最关键假设压清楚，优先先跑 `scenario-model`。`scenario-model` 负责 odds memo 和 sizing；本 skill 负责把这些输入装配成完整 thesis、variant view、catalyst 和 kill criteria。

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- `_shared/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## 心法

卖方报告和买方 thesis 最根本的区别：**买方的逻辑必须包含"为什么这个机会还存在"**。如果一个机会人人都能看到、人人都同意，那它已经被 priced in 了，不存在 alpha。所以 thesis 的核心是 **variant view**——你和 consensus 哪里不一样、为什么这个差异存在、什么会让市场逐步同意你。

没有 variant view 的"多头逻辑"不是 thesis，是叙事。叙事不赚钱。

举个例子——坏的 thesis："ASML 是 EUV 垄断龙头，长期看好。"好的 thesis："Consensus 2026 EUV 订单 $17bn，我认为是 $22bn——因为高 NA 单价 +20% 且 TSMC/Intel 先进制程 capex 没有放缓迹象。Q3 财报订单数就是第一个 catalyst。如果订单 <$15bn，我错，买这个 thesis 的人亏钱。"

## 必填章节（缺一不可，缺一项就重写）

### Primitive Preflight（先判断能不能直接写 thesis）

在写 Variant View、

## 情景回报计算

| # | 计算 | 公式 | 输入来源 |
|---|---|---|---|
| 1 | 情景回报率 | (目标价 - 当前价) ÷ 当前价 | DER, MKT |
| 2 | 目标价 (P/E法) | EPS × Target P/E | FS, CON |
| 3 | 目标价 (EV/EBITDA法) | (EBITDA × Target Multiple - Net Debt) ÷ Shares | FS, FS |
| 4 | 加权期望回报 | Σ (概率 × 情景回报) | DER |

Bull / Base / Bear、Kill Criteria 之前，先判断 thesis 依赖的关键 driver 是否已经拆清楚。不要因为用户要求"写 thesis"就跳过这个检查。

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
  - "Q3 财报（11 月 [I1](https://example.com/ir-earnings-calendar)）：管理层若给出 2026 capex 指引 < $2B [S1](./_cache/sources/q2-2024-capex-call.md)，将证伪 capital cycle bear thesis（概率 60%）"
  - "OPEC+ 12 月会议 [I2](https://example.com/opec-calendar)：减产延长将支撑油价 base case > $75（概率 70%）"

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
- 例："若 2024Q4 单井产量下降幅度 > 18%（vs. 当前 12% [S2](./_cache/sources/q3-2024-production-note.md)），decline 加速 thesis 失效"

**Short-only**：上行 catalyst 出现 / squeeze 风险
- 例："若 short interest 升至 30%+ 且 days-to-cover > 5（[I3](https://example.com/finra-short-interest) 当前 18% / 3.2 天），squeeze 风险升温必须减仓"
- 例："若公司宣布 strategic review / activist 介入（[I4](https://example.com/13d-precedent-study) 历史上常引发 30%+ rally），空头 thesis 失效"

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

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## Thesis Driver Mix

| Driver | Weight | Current | Target | Confidence |
|---|---|---|---|---|
| Growth (Rev CAGR) | X% | Y% | Z% | — |
| Margin (EBIT%) | X% | Y% | Z% | — |
| Multiple (PE re-rate) | X% | Yx | Zx | — |

Growth stalls + Margin holds → flat. Growth hits + Margin expands → bull re-rate.

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

## 篇幅基准

完整产出 **800-1500 字**。这是要拿去 pitch 的东西，必须密度高、可执行。

## Journal-First Handoff

本 skill 默认产出研究观点，不再写交易状态文件。若用户要求保存，把 thesis 作为当前日期化保存路径的研究材料保存为：

```text
industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-alpha-thesis.md
```

本 skill 的 `artifact_policy.naming_mode = plain`。默认继续使用 `YYYY-MM-DD-<artifact>.md`；只有文件名冲突时才交给 `agent` 追加 `-2 / -3` 兜底，不把 qualifier 当 thesis 默认命名。

如果当前日期化保存路径不明确，agent 按 policy baseline §11 自动创建目录和索引。

`research-journal` 只在 thesis 已被研究清楚、形成可复用认知增量后再吸收，不要把未验证 thesis 直接写成 memory。

如果 thesis 中出现披露口径、业务实质、model driver、source 冲突等高价值疑点，直接触发 `Research Runtime Capsule` 的 Senior Analyst Radar 提醒。若问题是 revenue / margin / backlog / price-volume-mix driver 没拆清楚，先用 `driver-map`；若问题是研究方向本身不清，再用 `next-step`。


