---
name: alpha-thesis
description: Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.
---

# Alpha Thesis

Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.

上游如果还没有把 bull/base/bear 的赔率、implied value 和最关键假设压清楚，优先先跑 `scenario-model`。`scenario-model` 负责 odds memo 和 sizing；本 skill 负责把这些输入装配成完整 thesis、variant view、catalyst 和 kill criteria。

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

卖方报告和买方 thesis 最根本的区别：**买方的逻辑必须包含"为什么这个机会还存在"**。如果一个机会人人都能看到、人人都同意，那它已经被 priced in 了，不存在 alpha。所以 thesis 的核心是 **variant view**——你和 consensus 哪里不一样、为什么这个差异存在、什么会让市场逐步同意你。

没有 variant view 的"多头逻辑"不是 thesis，是叙事。叙事不赚钱。

举个例子——坏的 thesis："ASML 是 EUV 垄断龙头，长期看好。"好的 thesis："Consensus 2026 EUV 订单 $17bn，我认为是 $22bn——因为高 NA 单价 +20% 且 TSMC/Intel 先进制程 capex 没有放缓迹象。Q3 财报订单数就是第一个 catalyst。如果订单 <$15bn，我错，买这个 thesis 的人亏钱。"

## Trade Structure 路由（不在产出中独立成节）

LS 基金不预设 long-only。写 thesis 前先判断 trade structure——后续每节的写法都依赖于此。

| Structure | 说明 | Thesis 重心 | Bull/Base/Bear 含义 | Kill 形式 |
|---|---|---|---|---|
| **Long-only** | 单边做多 | 多头 thesis、上行 catalyst | 股价 + 回报 % | 基本面恶化 / valuation 击穿 |
| **Short-only** | 单边做空 | 空头 thesis、下行 catalyst | 股价 - 回报 %（Bull = 跌深、Bear = 涨） | 上行 catalyst / squeeze 风险 |

**强制约束**：
- **如果用户给出 Long X + Short Y，停止使用本 skill，改用 `pair-trade`**。
- **如果用户问 "X 用什么对冲" / "找 hedge candidate"，停止使用本 skill，改用 `pair-trade`**。

**Long-only**：Trade Structure 不在产出中独立成节——在 §1 里一笔带过即可。Kill Criteria（§7）、Sizing（§8）、Key Assumptions（§9）为可选。

**Short-only**：Trade Structure 必须独立成节（§0）。Kill Criteria（§7）、Sizing（§8）、Key Assumptions（§9）为必填。Short-only 的 kill criteria 写法和 Long-only 反过来——多头担心下跌击穿，空头担心上涨 squeeze。

**Variant View 双向化**（适用所有单股 thesis）：

不只问 "vs long consensus 差多少"，要双向问：
- **vs long consensus**（多头方向）：你的数字 / view 比看多者更乐观还是更悲观？
- **vs short consensus**（空头方向）：你的数字 / view 比看空者更乐观还是更悲观？

这能防止多头 thesis 忽略聪明空头的问题，也能防止空头 thesis 只是在复述市场已经知道的坏消息。

## 产出结构

章节顺序固定，不可重排。

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

### §0. Trade Structure（仅 Short-only 时独立成节）

Short-only 时必须先声明 trade structure。Long-only 跳过此节，在 §1 一笔带过即可。

### §1. Thesis

紧凑段落，不超过 5 句。必须包含：核心数字分歧（指引/consensus vs 你的数）、估值锚点、peer reference（如有）。

反例：
- "看好 X 的长期前景"——这不是 trade，是观点。
- 超过 5 句——把 §2/§3 的内容塞进来了，收窄。

### §2. Exposure Map（条件必填）

**触发条件**：公司有 ≥2 个分部，且至少一个分部内部业务对终端市场的暴露不同。单分部/纯业务公司跳过。

三个子块：

1. **官方分部表**：收入 / 占比 / YoY / 近期季度增速 / OPM。必须从 actuals 取数。
2. **分部内拆终端市场**：每个分部内按终端市场/产品线拆收入（推算），必须标 `[推算]` + 估算依据。
3. **主题敞口汇总**：ASCII 百分比 rollup，落到一个百分比数字。
4. **一句话利润来源**：哪个分部/产品线是真正的利润引擎。

### §3. Variant View（量化，必须有数字）[→ Bridge: consensus, valuation_snapshot, institution_rating]

三个组件，按数据可得性装配：

**组件 A：增速差异表（必填）**

明确说出：你的关键预测和指引/consensus 差多少？每个业务线一行，加"差异根因"列。

例：
| 变量 | 指引隐含 | Base | 差异根因 |
|---|---|---|---|
| 业务线 A 增速 | ~15% | +73% | peer 增速远高于指引隐含 |
| 业务线 B 增速 | ~15% | +60% | 新工厂全年投产未体现 |

反例："我比市场更乐观"——零信息。

如果你的核心数字和 consensus 一致，**那你没有 variant view，你只是同意 consensus**——这种情况下不存在 alpha，要么放弃这单 trade，要么重新想哪里其实不一致。

**组件 B：Peer 交叉验证段（条件必填——有可比标的时必填）**

选一个同终端市场、不同产品/赛道的可比标的，用它的增速/capex/order 反证指引或 consensus 的合理性。找不到则不写，不编。

**组件 C：Guidance beat 历史表（条件必填——公司有出指引历史时必填）**

年度指引 vs 实际，beat rate，均值。至少 3 年数据才构成 pattern。

### §4. Why the Gap Exists（这是最重要的一节）

机会为什么还在那里没被收割？分类思考：

- **Information edge**：你知道一些别人不知道的事？（注意：这通常很难真正存在，且要合规）
- **Time horizon arbitrage**：市场在 punish 短期数据、忽略 2-3 年后的结构性变化？
- **Complexity / accounting**：业务复杂、报表有误读、分类错误（被当成周期股，实际是成长股；被当成成长股，实际是 melting ice cube）？
- **Behavioral / sentiment**：被讨厌、被遗忘、刚出过黑天鹅、ESG 不待见、太小没人看？
- **Structural flow**：被动资金 / 指数除名 / 大股东减持等技术性压力？

**如果你说不出 why the gap exists，停下来重新审视 variant view**——通常意味着你的 view 实际上和 consensus 一致，只是用了不同 wording。

### §5. Catalysts（3-5 个，每个都要具体、可定时）

什么事件会让市场开始同意你？时间？概率？事件本身要给 source；概率是研究员判断不需要 source。

按 trade structure 调整 catalyst 视角：
- **Long-only**：上行 catalyst（财报 beat、产能爬坡、capital return、监管利好）。
- **Short-only**：下行 catalyst（财报 miss、guidance cut、负面监管、debt 到期）。

例（Long-only）：
  - "Q3 财报（11 月 [I1](https://example.com/ir-earnings-calendar)）：管理层若给出 2026 capex 指引 < $2B [S1](./_cache/sources/q2-2024-capex-call.md)，将证伪 capital cycle bear thesis（概率 60%）"
  - "OPEC+ 12 月会议 [I2](https://example.com/opec-calendar)：减产延长将支撑油价 base case > $75（概率 70%）"

反例："长期来看市场会认识到价值"——这不是 catalyst，是 hope。

### §6. Bull / Base / Bear

**所有 thesis 均为增速型 thesis**。使用以下固定格式：

**表格格式**：双年并排（FY27 Bear / Base / Bull | FY28 Bear / Base / Bull 或等同的 NTM/NTM+1）。行结构固定：

```
| | FY27 Bear | FY27 Base | FY27 Bull | FY28 Bear | FY28 Base | FY28 Bull |
|---|---|---|---|---|---|---|
| **假设变量1增速** | ... | ... | ... | ... | ... | ... |
| **假设变量2增速** | ... | ... | ... | ... | ... | ... |
| （每个关键 driver 一行）|
| **Revenue** | ... | ... | ... | ... | ... | ... |
| **Growth** | ... | ... | ... | ... | ... | ... |
| **OPM** | ... | ... | ... | ... | ... | ... |
| **OP** | ... | ... | ... | ... | ... | ... |
| **EPS** | ... | ... | ... | ... | ... | ... |
| | | | | | | |
| **Forward PE (on actual)** | ... | ... | ... | ... | ... | ... |
| **Target Price (@XXx PE)** | ... | ... | ... | ... | ... | ... |
| **Upside/Downside (vs ¥XXX)** | ... | ... | ... | ... | ... | ... |
```

Target Price 必须标注 PE 倍数依据。Upside/Downside 行放在最底，用当前股价算。

**Short-only**：方向反转。Bull = 空头胜（跌深），Bear = 空头败（涨被 squeeze）。Forward PE / Target Price 行同样反向。

**Scenario 本身（数字）是研究员判断**，不需要 source。但**假设依赖的事实**（当前基线数字、历史类比案例、行业可比）必须有 source——否则假设是凭空的。

**Upside 情景叙事**：表格后跟一段，说明 Bull→Super Bull 的路径和条件。

### §7. Kill Criteria（具体到数字 / 事件，不允许空泛）

**Long-only**：可选。
**Short-only**：必填。

按 trade structure 调整 kill 形式：

**Long-only**：基本面恶化触发
- 例："若 2024Q4 单井产量下降幅度 > 18%（vs. 当前 12% [S2](./_cache/sources/q3-2024-production-note.md)），decline 加速 thesis 失效"

**Short-only**：上行 catalyst 出现 / squeeze 风险
- 例："若 short interest 升至 30%+ 且 days-to-cover > 5（[I3](https://example.com/finra-short-interest) 当前 18% / 3.2 天），squeeze 风险升温必须减仓"
- 例："若公司宣布 strategic review / activist 介入（[I4](https://example.com/13d-precedent-study) 历史上常引发 30%+ rally），空头 thesis 失效"

反例："如果基本面恶化"——空话，什么都没说。

### §8. Sizing 逻辑

**Long-only**：可选。
**Short-only**：必填。

基于以上的 asymmetry 和 kill criteria 的清晰程度，这个 position 应该多大？什么情况下加仓？什么情况下减仓？

通用原则：
- Kill criteria 非常明确、信号容易观察 → 可以更大仓位（风险可控）。
- Thesis 依赖 5 个连续假设都对 → 仓位要小（path 太长）。
- Catalyst 集中在某一时点 → 考虑用期权而不是正股，捕捉非对称性。
- **Short-only**：borrow availability + cost + crowded short 风险都进 sizing 考量。Single-name short 最大 sizing 应低于同 conviction 的 long（asymmetric loss）。

### §9. Key Assumptions Checklist

**所有 trade structure**：可选。

明确写出 thesis 依赖的关键假设。后续每个季度回来检查这些假设是否还成立。这是 thesis 的**维护手册**，也是 pre-mortem 的输入。

必填：
- 3-5 条最关键假设。
- 每条假设的当前证据 / source。
- 每条假设的反证信号。
- 哪些假设应在下一次财报或行业数据更新时复查。

### 产品详解（必填，§6 之后 §Resources 之前）

核心产品（占 thesis driver >10%）和边缘产品区分处理：

**核心产品**：每个产品一个子节。

| 字段 | 说明 |
|---|---|
| 一句话功能 | 大白话，这个产品干嘛的 |
| 竞争格局表 | 公司 / 技术路线 / 定位。必须标 source |
| 护城河 & 技术壁垒 | 分维度（物理壁垒/制造壁垒/时间壁垒等），不做空泛类比 |
| 利润率 & 定价权 | ASP 区间 + OPM 推算或 GM 推算 |
| 量价驱动 | 量/价/新增三个因子，各自一句话 |
| 产品实物图 | 必须。下载方法见 Research Runtime Capsule §2.5 |

**边缘产品**：一句话功能 + 产品实物图 + 主题关系判断。不写竞争格局/护城河/ASP。

---

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## 反模式自查

**通用**
- ❌ Long X / Short Y 还继续写 alpha-thesis → 触发错 skill，改用 `pair-trade`。
- ❌ Variant view、scenario 或 kill criteria 依赖 revenue / margin / backlog / price-volume-mix driver，但没有先做 Primitive Preflight → 先触发 `driver-map`。
- ❌ Variant view 只 vs long consensus，没 vs short consensus → LS 视角缺失。
- ❌ 章节里大段复述业务模式 / 行业背景 → 那是 quickread 的活儿，这里只放和 thesis 直接相关的东西。

**§1 Thesis**
- ❌ 超过 5 句 → 把 §2/§3 的内容塞进来了，收窄。
- ❌ "看好 X 的长期前景"——这不是 trade，是观点。

**§2 Exposure Map**
- ❌ 分部内拆终端市场只有"估计"但没有估算依据和 source → 重写。
- ❌ 满足触发条件（≥2 分部 + 内部异质）但跳过不写 → 补。

**§3 Variant View**
- ❌ 差异表没有数字（"我比市场更乐观"）→ variant view 不存在，重写。
- ❌ 差异表引用 consensus/指引数字但无 source → 标记或补。
- ❌ 有 peer 交叉验证数据但没写 → 补。
- ❌ 有 ≥3 年 guidance beat 历史但没列 → 补。

**§4 Why the Gap**
- ❌ 写不出来 → thesis 大概率有问题，先想清楚再继续。

**§5 Catalysts**
- ❌ 都是"长期"——没有具体时间 → 实际上没有 catalyst，重列。
- ❌ 提到的事件（财报、监管会议、investor day）无具体日期 source → 补。

**§6 Bull / Base / Bear**
- ❌ Bear case 增长几乎不打折 → bear 太弱，没认真想 bear 怎么发生。
- ❌ 只有单年没有 out-year → 增速型 thesis 必须有 out-year。
- ❌ Target Price 没标 PE 倍数依据。
- ❌ Upside/Downside 不在最底行。
- ❌ Short-only 方向没反转。

**§7 Kill Criteria（如有）**
- ❌ Short-only 但 kill criteria 写法和 long 一样 → 没考虑 squeeze 风险。
- ❌ "如果错了我就退" → 没有可观察的具体信号，等于没有。

**产品详解**
- ❌ 核心产品没有竞争格局表 → 补。
- ❌ 护城河写成空泛类比（"数据积累不可复制"类空话）→ 必须落到物理/制造/时间等具体维度。
- ❌ 核心产品缺少实物图 → 补。

**Source 专项**
- ❌ Variant view 引用 consensus 数字但无 source → 标记或补。
- ❌ Catalyst 提到的事件（财报、监管会议、investor day）无具体日期 source → 补。
- ❌ Exposure Map 推算收入无估算依据 → 标 `[推算]` + source。

## 篇幅基准

完整产出 **120-300 行**（含产品详解）。这是要拿去 pitch 的东西，必须密度高、可执行。

## Journal-First Handoff

本 skill 默认产出研究观点，不再写交易状态文件。若用户要求保存，把 thesis 作为当前日期化保存路径的研究材料保存为：

```text
industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-alpha-thesis.md
```

本 skill 的 `artifact_policy.naming_mode = plain`。默认继续使用 `YYYY-MM-DD-<artifact>.md`；只有文件名冲突时才交给 `agent` 追加 `-2 / -3` 兜底，不把 qualifier 当 thesis 默认命名。

如果当前日期化保存路径不明确，agent 按 policy baseline §11 自动创建目录和索引。

`research-journal` 只在 thesis 已被研究清楚、形成可复用认知增量后再吸收，不要把未验证 thesis 直接写成 memory。

如果 thesis 中出现披露口径、业务实质、model driver、source 冲突等高价值疑点，直接触发 `Research Runtime Capsule` 的 Senior Analyst Radar 提醒。若问题是 revenue / margin / backlog / price-volume-mix driver 没拆清楚，先用 `driver-map`；若问题是研究方向本身不清，再用 `next-step`。
