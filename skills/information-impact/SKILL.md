---
name: information-impact
description: Use when checking whether a news item, rumor, supply-chain claim, sell-side note, industry data point, or expert-commentary snippet is credible and portfolio-relevant.
---

# Information Impact

把信息流过滤成 portfolio-actionable 信号。**绝大部分信息应该被归档而非分析**——这个 skill 的成功标准不是"写了多少分析"，是"过滤掉多少噪音 + 准确识别少数真正重要的"。

## 心法

研究员一天会看到几十条信息：公司公告、卖方观点、行业数据、市场传闻、推特片段、专家访谈摘要、政策事件、同行 read-through。**信息淹没的本质不是信息多，是不知道哪条 actionable**——所以本能反应是全都看，时间被切碎，单个公司花的时间反而少。

解决方案是结构化的快速过滤：

1. **先验证信息本身**（Mode A）——大部分传闻、推特片段、二手转述靠不住，verify 之前不要分析
2. **再判断 portfolio 影响**（Mode B）——必须 portfolio-specific，不允许"对行业有影响"这种空话
3. **绝大部分归档**——80%+ 信息应该是 Low / 无相关性 / 不可信，归档无需行动
4. **少数 actionable 触发其他 skill**——不在本 skill 内深入分析，而是 trigger thesis-tracker / bear-pre-mortem / decision-journal

**500 字硬上限**。如果觉得需要更多，应该触发其他 skill 而不是把 information-impact 写长。

## Source 政策

本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

特别强调：
- **Source quality 直接用 `CLAUDE.md §3.4` 的 4 级分级**（一手原始 / 二手权威 / 三手解读 / 谨慎使用）—— 不在本 skill 重新搞一套
- **传闻 / 推特 / 论坛 / 聊天记录 / 券商私下转述都属于第 4 级"谨慎使用"**——只能作为线索，不是 verified fact
- **Sub-agent 返回的 URL 必须按 `CLAUDE.md §3.7` 抽查验证**——信息处理高度依赖 web search，URL 假冒是常见失败 mode

## 触发场景

- "这条新闻怎么看"
- "这个传闻靠谱吗"
- "X 是不是进了 Y 的供应链"
- "Goldman / Morgan Stanley 这份报告关键点 + 我同不同意"
- "刚出的 EIA / PMI / CPI 怎么影响我"
- "Twitter 这条说 X 拿到 Y 大单怎么看"
- "今天早报过一遍"（批量模式）
- "review inbox 这周的信息"（批量模式）

## 信息类型 → 处理路径 Map

不同类型信息的典型路径不同。先识别类型，再走对应流程：

| 信息类型 | 典型 source 等级 | Mode A 是否必要 | 推荐路径 |
|---|---|---|---|
| 公司 filing / 交易所公告 | 1 级（一手） | 跳过（已 verified） | 直接 Mode B |
| 公司新闻稿 / IR 沟通 | 1-2 级 | 简化（marketing 语言可能 spin） | 简化 Mode A → Mode B |
| 监管 / 政府数据（EIA、PMI、CPI） | 1 级 | 跳过 | 直接 Mode B（但要量化 surprise） |
| 行业研究机构数据（Wood Mac 等） | 2 级 | 简化（只 verify methodology） | 简化 Mode A → Mode B |
| 卖方研究报告 | 3 级（**别人的判断**，不是 fact） | 完整（区分 fact vs opinion） | 完整 Mode A → Mode B |
| 主流媒体（Reuters / FT / WSJ） | 3 级 | 简化（看是否引用一手 source） | 简化 Mode A → Mode B |
| 行业垂直媒体 | 3 级 | 完整 | 完整 Mode A → Mode B |
| 推特 / Telegram / 聊天群片段 | 4 级 | **必做完整** | 完整 Mode A，verdict 至少 Plausible 才进 Mode B |
| 专家访谈摘要（Tegus / GLG 等） | 2 级（但有 selection bias） | 简化（注意专家是不是 self-promoting） | 简化 Mode A → Mode B |
| 同行公司财报 read-through | 1-2 级 | 跳过（财报是 fact） | 直接 Mode B（重点是推断 read-through 强度） |

**关键判断**：卖方研究报告是 **3 级 source**，不是 fact —— 不要把"高盛认为 X"当作"X 是真的"。卖方观点本身需要单独 verify 和挑战，不是 anchor。

## Mode A: Claim Check（验证消息真假）

**何时用**：所有 source 等级 ≥ 3 级的信息（即除了一手 filing / 数据外几乎都要做）。

### Verdict（5 级）

| Verdict | 含义 | 进 Mode B？ |
|---|---|---|
| **Confirmed** | 一手 source 证实 | Yes |
| **Likely** | 多个二手 source 一致，但缺一手；或单个一手但 marketing 嫌疑 | Yes |
| **Plausible but unconfirmed** | 单一二手 / 三手 source；或多个但 source 互相 cross-reference 同一原始（伪 corroboration） | Yes（但 strength 默认 ≤ Medium） |
| **Unsupported** | 仅推特 / 聊天群 / 论坛；找不到 corroborating 1-2 级 source | **Drop**（写极简归档行） |
| **Contradicted** | 已 sourced 一手数据反 claim | **Drop**（写极简归档行，但记录用于反向 inference） |

### Claim 拆解（必填字段）

把模糊 claim 拆成 atomic 可验证字段：

| 字段 | 含义 | 例 |
|---|---|---|
| company | 主语公司 | "拓普集团" |
| customer / counterparty | 涉及谁 | "Tesla" |
| product / role | 什么产品或角色 | "Optimus 关节执行器" |
| relationship_type | 直接 / 间接 / tier-N | "tier-1 supplier (claimed)" |
| timeframe | 时间窗口 | "2025 H2 量产" |
| magnitude | 量级 | "占公司 5% 收入 (claimed)" |

**关键约束**：必须区分以下 4 类（极易混淆）：
- ✅ **Direct supplier**（一手合同）
- ⚠️ **Tier-2 / indirect supplier**（through tier-1，关系弱很多）
- ⚠️ **Product can be used**（理论可用 ≠ 实际采购）
- ❌ **Market concept / theme association**（被市场归类到主题但无实际业务关系）

混淆 = claim 性质完全不同。例："X 进 SpaceX 供应链" 在这 4 类下含义 / 估值含义差几个量级。

### Mode A 输出

```
## Claim Check

**Verdict**: [5 级之一]
**Bottom line**: [一句话直接说能不能信]

| Claim piece | Evidence found | Source quality (1-4) | Read-through |
|---|---|---|---|
| [拆分项] | [证据摘要 + URL] | 1 / 2 / 3 / 4 | direct / indirect / not proven |

**What would make it real** (≤ 3 条):
- [还缺的关键证据，越具体越好]

**What not to infer** (≤ 3 条):
- [不能从该消息外推到什么——防止 weak claim 被外推到 strong thesis]

**Next step**: Drop / 进 Mode B / Ask IR / Search filings / Monitor for further evidence
```

如果 Verdict = Unsupported / Contradicted，**到此结束**——只在 `inbox/information-log.md` 写一行归档（见下方状态文件 schema）。

## Mode B: Portfolio Impact

**何时用**：Mode A verdict ≥ Plausible（即 Confirmed / Likely / Plausible），且至少命中一个 portfolio / watchlist 标的。

### B.1 读取 Portfolio

读取 `coverage/` 和 `pairs/` 目录的所有 thesis frontmatter，识别哪些标的可能被这条信息影响。Watchlist 也包括（即使未建仓但在跟踪）。

### B.2 Portfolio Relevance Table（核心输出）

每个相关标的列一行：

| Ticker / Pair | 持仓方向 | 影响方向 | 强度 | 立即行动 |
|---|---|---|---|---|
| XOM | Long (3% gross) | Confirming | Medium | 加入 thesis-tracker monitoring queue |
| TSLA | Short (2% gross) | Contradicting | High | 触发 thesis 重审 + decision-journal review |
| ASML-AMAT | Pair (Long ASML) | Confirming long leg | Low | 归档参考 |
| NVDA | Watchlist | Neutral | Low | 归档 |

### B.3 字段定义（Hard Standards）

#### 影响方向（4 类，必须明确）

| 方向 | 含义 |
|---|---|
| **Confirming** | 信息支持现有 thesis（Long 有利好 / Short 有利空 / Pair 论点 strengthen） |
| **Contradicting** | 信息反 thesis（Long 有利空 / Short 有利好 / Pair 论点 weaken） |
| **Neutral** | 相关但不显著影响 thesis 方向（如不改变 variant view 或 catalyst） |
| **Mixed** | 多空分歧（必须说明 mixed 在哪——不允许用 Mixed 偷懒） |

#### 强度（3 级，必须有 hard 标准，不允许凭感觉）

| 强度 | Hard Standard | Action |
|---|---|---|
| **Low** | 不影响 thesis 任何关键 assumption；不接近 kill criteria；信息 magnitude 小 | 归档参考，无需后续动作 |
| **Medium** | 影响 thesis 次要假设；或距 kill criteria 仍有 buffer（> 1σ）；或单点数据不足以触发 kill | 加入 thesis-tracker 监控队列，下次 health check 时复盘 |
| **High** | 影响 thesis 第 1 节 variant view 核心 assumption；或距 kill criteria < 1σ；或独立可触发调仓 | 当下触发 thesis 重审 / bear-pre-mortem / decision-journal review |

**强度评级必须给具体理由**，例如：
- ✅ "High because: thesis §5.1 long thesis 第 1 条假设是 'EUV bookings > $5B'，本次数据点 $3.2B 直接反向"
- ✅ "Medium because: 影响 capital discipline 假设但单季度数据，需后续 Q3 confirm"
- ❌ "High because: 这是大新闻"——凭感觉，重新评估
- ❌ "Medium because: 看起来影响中等"——同上

### B.4 Mode B 完整输出

```
## Portfolio Impact

**Source**: [标题 + URL + 日期 + as-of]
**Type**: [信息类型 from §信息类型 Map]
**Mode A Verdict**: [from Mode A]

### Relevance Table
[B.2 的表格]

### Key takeaway (≤ 50 字)
[一句话本质——对**我的 portfolio** 意味着什么。不是对行业、不是对宏观，必须 portfolio-specific]

### Open Questions (最多 3 条)
[每条要具体到"哪份文件 / 哪个数据点 / 哪个人能回答"，不允许"再多了解一下"]
1. [具体问题]
2. ...

### Action Queue
- **Immediate (今天内)**: [具体行动，如有]
- **This week**: [具体行动，如有]
- **Monitor**: [长期跟踪点]
```

### B.5 特殊路径：无 Portfolio Relevance

如果信息和所有 portfolio / watchlist 都无关，**不要硬讲影响**。极简归档：

```
## No portfolio relevance — archived

[标题] - [一句话总结] - 归档原因：[XX 行业 not in coverage / 时间窗口太短 / 已知信息 / 与现有持仓无关联]
```

依然写入 `inbox/information-log.md`（一行），防止后续发现 retroactively 重要。

## 批量处理模式（早报场景）

**触发**："今天早报过一遍"、"review 这周 inbox"、"批量看一下 [N 条信息]"。

**输出格式**：极简一表多行，不为每条做完整 Mode A/B。

```
## 批量信息处理 [YYYY-MM-DD]

| # | 信息标题 | Type | Verdict | Portfolio Hit | Strength | Action |
|---|---|---|---|---|---|---|
| 1 | EIA Crude inventory -3.5MB | 1级数据 | Confirmed | XOM (Long) | Medium | thesis-tracker queue |
| 2 | Twitter: NVDA 中国订单暴跌 | 4级传闻 | Unsupported | n/a | n/a | Drop |
| 3 | ASML Q2 transcript: EUV 加单 | 1级 | Confirmed | ASML-AMAT (long leg) | High | 触发 thesis 重审 |
| 4 | Goldman 上调 TSLA TP $400 | 3级（卖方观点） | Likely (是观点不是 fact) | TSLA (Short) | Low | 归档（卖方观点本身不是 catalyst） |
| ... | ... | ... | ... | ... | ... | ... |
```

**批量模式的关键约束**：
- 任何标记 **High** 的信息必须 **trigger 单独完整 Mode A/B 处理**——不能只在批量表里一行带过
- 任何 verdict **Confirmed/Likely 但 Portfolio Hit ≠ n/a 的 Medium 强度** 也建议触发完整处理（用户可选）
- Verdict Unsupported / Contradicted 的可以批量带过

**批量模式输出篇幅**：1000-1500 字（包含表格），但单条信息平均 < 50 字。

## 状态文件：`inbox/information-log.md`

### 文件级 Frontmatter

```yaml
schema_version: 1
document_type: information_log
append_only: true
entry_schema: information_v1
```

### 单条 entry schema（YAML）

每条信息追加一个 block，不改旧 entry：

````markdown
```information_v1
log_id: 2026-05-07-001
date: 2026-05-07
type: company_news / sellside / industry_data / rumor / regulatory / macro / earnings_readthrough
source_title: "..."
source_url: "[link 待补]"
source_quality: 1   # 1-4 from CLAUDE.md §3.4
mode_a_verdict: Confirmed / Likely / Plausible / Unsupported / Contradicted
mode_a_one_liner: "一句话 verdict 解释"
portfolio_hits:
  - ticker: XOM
    direction: Long
    influence: Confirming
    strength: Medium
    rationale: "..."
  - ticker: TSLA
    direction: Short
    influence: Contradicting
    strength: High
    rationale: "..."
key_takeaway: "≤ 50 字"
action_immediate: "..."
action_this_week: "..."
linked_skills_triggered:
  - thesis-tracker
  - bear-pre-mortem
follow_up_questions:
  - "..."
```
````

**No relevance 的极简 entry**（依然记录）：

````markdown
```information_v1
log_id: 2026-05-07-002
date: 2026-05-07
type: macro
source_title: "..."
source_url: "..."
source_quality: 1
mode_a_verdict: Confirmed
portfolio_hits: []
key_takeaway: "ARCHIVED — no portfolio relevance: [一句话理由]"
```
````

**追加规则**：
- 不允许修改旧 entry（append-only）
- `log_id` 用 `YYYY-MM-DD-NNN` 格式，便于检索
- High strength 的 entry 必须有完整 `linked_skills_triggered` 列表（说明触发了哪些下游 skill）

## Workflow 联动

| 场景 | 触发的下游 skill |
|---|---|
| Strength = High，影响 thesis | `thesis-tracker`（health check）+ `bear-pre-mortem`（重审） |
| Strength = High，触发调仓 | `decision-journal`（review / add / trim / close action） |
| Mode A verdict = Confirmed/Likely 但卖方观点反 thesis | `bear-pre-mortem`（把卖方观点作为对手 view） |
| 跨市场信息（如 ADR delisting risk）| `cross-market-compare`（评估 spread 影响） |
| Pair leg 单边 single-name 事件 | `pair-trade` Monitor mode（评估是否解 pair） |
| 同行 read-through 信号 | `peer-deep-dive` 重做 cross-cut（如果信号涉及多个标的） |
| 财报相关信息 | `earnings-setup`（Pre-print 或 Post-print） |
| Strength = Medium，加入监控 | 仅记录到 `inbox/information-log.md`，下次 thesis-tracker 自动 review |
| Strength = Low / No relevance | 仅归档，无下游 |

## 反模式自查

写完必须自检：

**Source 验证**
- ❌ 把卖方观点（"高盛认为 X"）当作 fact 直接进 Mode B → 卖方观点是 3 级 source，必须先验证内容
- ❌ Verdict = Confirmed 但只有推特 / 聊天群 → source 不够，至少 Plausible
- ❌ Mode A 找不到一手 source 但仍标 Confirmed → 不诚实
- ❌ 没区分 direct supplier / tier-2 / product can be used / market concept → 4 类含义差几个量级
- ❌ Sub-agent URL 没抽查就用 → 违反 CLAUDE.md §3.7

**Portfolio Relevance**
- ❌ 影响判断空话："对行业有影响"、"利好科技股" → 必须 portfolio-specific
- ❌ 强度 = High 但理由是"这是大新闻" → 必须 link 到具体 thesis assumption / kill distance
- ❌ 强度全部填 Medium → 没认真区分（绝大部分应该是 Low / No relevance）
- ❌ Open Questions 写"再多了解一下" → 必须具体到 source / 数据 / 人

**篇幅 / 流程**
- ❌ 完整 Mode A/B 输出 > 500 字 → 越权，应该触发其他 skill
- ❌ 批量模式 High strength 的项只在表里带过 → 必须 trigger 完整处理
- ❌ Mode A verdict = Unsupported 但仍写 Mode B → 错误流程
- ❌ No relevance 但写了一大段分析 → 应该极简归档
- ❌ 不写入 `inbox/information-log.md` → 状态丢失，下次 thesis-tracker 看不到
- ❌ Action Queue 没时间维度（Immediate/This week/Monitor）→ 没法排优先级

## 篇幅基准

| 场景 | 篇幅上限 |
|---|---|
| 单条 Mode A only（verdict ≤ Plausible） | 200-300 字 |
| 单条完整 Mode A + Mode B | 400-500 字（**500 硬上限**） |
| No portfolio relevance 归档 | < 50 字 |
| 批量处理（5-15 条） | 1000-1500 字 |
| 单条触发 High → trigger 其他 skill 时 | 本 skill 仍 ≤ 500 字，深度分析在被触发的 skill 内做 |

**500 字硬上限的意义**：信息处理的核心是 noise reduction，不是 deep analysis。如果觉得需要更多字数，意味着：
- 该信息真的重要 → 应该触发 thesis-tracker / bear-pre-mortem / decision-journal 的 deep work
- 或该信息其实不那么重要 → 你在过度分析，回头精简
