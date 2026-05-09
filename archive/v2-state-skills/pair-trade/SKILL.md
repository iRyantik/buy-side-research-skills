---
name: pair-trade
description: Use when building or monitoring a long/short pair trade, evaluating whether two names can pair, finding a hedge candidate, checking spread health, or updating a spread log.
---

# Pair Trade

构建或监控 Long X / Short Y pair trade。LS 基金核心工具——但**绝大多数所谓的 "pair trade" 不是真 pair**，是两个独立的单边 trade 装在一起。本 skill 强制把两腿绑成一个 trade。

## 心法

Pair trade 真正的价值不是"两边都看一下"，是**用结构隔离掉共同 macro 风险，把 P/L 集中到 idiosyncratic alpha**。

所以判断一个 pair 是不是真 pair 的关键问题：
- **如果两腿一起跌 20% 你的 P/L 应该是 0**（被 hedge 掉）—— 这才是 pair
- 如果两腿一起跌 P/L 也跌 → 实际是单边赌注 + 装饰性 short

衍生出三条铁律：

1. **Long leg thesis 和 Short leg thesis 必须各自独立 sound**——不允许只有相对论点（"X 比 Y 好"）。如果只有相对论点，macro shock 时双杀。
2. **Spread 收敛/扩散必须有具体 mechanism**——不是"市场迟早会认识到"。要具体到事件 / 季度 / 数据点。
3. **P/L 主要来自 idiosyncratic factor 差异，不是共同 macro**——backtest 一下，如果历史 P/L 90% 来自共同 factor，你做的不是 pair。

如果以上三条都满足，再继续。否则要么换组合，要么干脆做单边 trade。

## Source 政策

本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

特别提醒：
- **价格 / spread / beta / correlation 必须有 as-of 时间戳**——金融数据 stale 几天就失真
- **Long leg 和 short leg 的数据必须同一时点**——不允许混用不同 cutoff
- **Spread 的历史 percentile / σ 必须给具体计算窗口**（5Y / 3Y / 1Y）
- **借券可得性 / borrow rate 必须给 source 和 as-of**——short side 流动性是真实约束，不是 backtest 假设

---

## Mode A: Builder（构建新 pair）

### A.1 触发

- "Long X / Short Y 怎么看"
- "这两个能不能 pair"
- "帮我搭一下 pair trade"
- "X 用什么对冲"
- "ASML 找一个 hedge candidate"
- "我看好 ASML 但担心 macro，怎么 pair"

### A.2 输出文件

写入两个文件：

1. `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`（pair thesis 全文）
2. `pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md`（初始 entry observation）

命名约定：`LONG-SHORT`，连字符分隔。例：`ASML-AMAT`、`XOM-CVX`、`9988HK-BABA`（同一公司多重上市 pair）。

### A.3 thesis.md 必填 frontmatter

```yaml
schema_version: 1
document_type: pair_thesis
pair_id: "[LONG]-[SHORT]"
long_ticker: "[X]"
short_ticker: "[Y]"
long_market: NYSE / HKEX / SSE etc.
short_market: NYSE / HKEX / SSE etc.
created_at: YYYY-MM-DD
direction: spread_converge   # 或 spread_diverge（极少见，做空 spread 大多用 spread_converge）
conviction: 1-5              # 1=低，5=极高
time_horizon: 6M / 12M / 18M
entry_spread: -2.0sigma vs 5Y mean   # 量化 entry 时点
target_spread: 0.0sigma              # 期望收敛到哪
kill_spread: +1.0sigma               # 反向到哪 thesis 失效
sizing_method: dollar_neutral / beta_neutral / vol_neutral
long_weight: 1.0   # 标准化权重
short_weight: -1.0  # beta_neutral 时可能是 -1.2 之类
benchmark: SPX / sector_etf   # 用于 P/L attribution
health_status: active   # active / watch / impaired / killed
updated_at: YYYY-MM-DD
next_catalyst: YYYY-MM-DD - [event description]
```

### A.4 thesis.md 必填章节

#### 1. Pair One-Liner（一句话 + table 概览）

一句话讲清楚：long X / short Y、收敛 thesis 核心、目标 spread / 时间窗口。

例："Long ASML / Short AMAT，spread 收敛 thesis：ASML EUV monopoly margin 持续扩张 vs AMAT 60% 收入暴露 memory 周期下行；目标 12 个月内 spread 从 -2σ 回归 0σ（约 +15% pair 回报）"

紧跟一张 setup 表：

| | Long | Short |
|---|---|---|
| Ticker | ASML.NA | AMAT |
| 业务定位 | EUV/DUV monopoly | Diversified WFE |
| 当前估值（NTM EV/EBITDA） | 22x | 18x |
| 5Y 估值 mean | 18x | 16x |
| Beta to 半导体设备 ETF | 1.05 | 1.10 |
| 流动性（日均成交量） | $2B | $1.5B |
| Borrow rate (annual) | n/a | 0.5% |

#### 2. 为什么这两家可比（Why are these two correlated）

**关键判断**：相关性必须 high enough（同一行业 / 重叠客户 / 类似 macro 暴露），否则 spread 不可比。但不能 100% 同质化（否则没差异），需要有结构性差异点。

按维度对比，每条要给具体 % 或事实，不允许 "两家都做半导体设备"这种空话：

| 维度 | Long X | Short Y | Source |
|---|---|---|---|
| 终端市场重叠 | 45% logic / 35% memory / 20% packaging | 30% logic / 60% memory / 10% packaging | [10-K segment data](url) |
| 客户重叠（top 10） | TSMC / 三星 / Intel / SK Hynix... | TSMC / 三星 / Intel / SK Hynix / Micron... | [investor day deck](url) |
| 产品 substitution | EUV 不可替代 | DUV 部分可替代 ASML 旧型号 | [行业研究](url) |
| 共同 macro 暴露 | 半导体 capex cycle、台美科技战、利率 | 同上 | [行业 capex tracker](url) |
| Idiosyncratic 差异 | EUV pricing power、单一 monopoly | Memory cycle 高暴露、Etch share gain | [10-K + 行业数据](url) |

**底线判断**：终端市场重叠 ≥ 60% + 客户重叠 ≥ 50% + 共同 macro 因子 ≥ 2 个 → 算相关。否则不是真 pair。

#### 3. 估值 Spread 历史

必须有具体 percentile / sigma，不允许 "spread 偏离历史"这种含糊判断。

| Metric | Long X 当前 | Short Y 当前 | Spread 当前 | 5Y mean | 5Y std | 当前 z-score | Source |
|---|---|---|---|---|---|---|---|
| EV/EBITDA NTM | 22x | 18x | +4x | +2x | 1.5x | +1.3σ | [Bloomberg as-of YYYY-MM-DD](url) |
| P/E NTM | 30x | 24x | +6x | +3x | 2x | +1.5σ | ... |
| EV/Sales | 9x | 5x | +4x | +2x | 1x | +2.0σ | ... |
| FCF yield | 3.5% | 5.0% | -1.5% | -0.5% | 0.8% | -1.25σ | ... |

**Spread converge 论点的强度判断**：
- z-score > +1.5σ 或 < -1.5σ：spread 显著偏离，mean-reversion 论点站得住
- z-score 在 ±0.5σ 内：spread 在 mean 附近，entry 不 attractive，等更好时点
- z-score > +3σ 或 < -3σ：极端偏离，要小心是不是真有 regime change（spread 不会回归）

#### 4. Beta / Correlation / 宏观敏感度

| Metric | 数值 | 解读 | Source |
|---|---|---|---|
| 180D return correlation (X vs Y) | 0.85 | 高 correlation 是 pair 必要条件；< 0.7 警惕，可能不是真 pair | [Bloomberg CORR](url) |
| 180D beta (X vs Y) | 1.05 | 用于 sizing：dollar-neutral 还是 beta-neutral | [Bloomberg BETA](url) |
| 共同 macro factor | 半导体设备 ETF beta、USD/JPY、10Y 利率 | 列出三个最显著的；这些 hedge 不掉 | ... |
| 独有 idiosyncratic factor | X: EUV bookings / 中国出口管制；Y: DRAM capex / etch share | 这才是 pair 的 alpha source | ... |
| 历史 max drawdown of pair | -8% (2022 行业 re-rating) | Pair 不是无风险 | [自算 historical pnl](url) |

**关键判断**：Pair 历史 P/L attribution 应主要来自 idiosyncratic 而非共同 macro。粗略测试：在历史 macro shock 日（如 2020/3/16、2022/6 等）pair P/L 是否被 isolation——如果 macro shock 日 pair P/L 也跌，说明结构没 hedge 住。

#### 5. Pair 论点（核心节，必须独立 sound）

**这是 pair-trade 的灵魂——必须**写成两个独立 thesis + 一个 spread converge mechanism**，不允许只写"X 比 Y 好"。

##### 5.1 Long leg thesis（why X should outperform）

按 alpha-thesis 简化逻辑：
- **Variant view vs long consensus**: 你比看多 X 的人还要看多在什么具体数字上
- **Why this gap exists**: 为什么这个 view 还没被 priced in
- **Catalyst**: 让市场认识到的具体事件 / 时间
- **关键假设**: thesis 依赖的 1-3 个核心假设（每个给 source）

例（Long ASML）：
> Variant view: 2026 EUV bookings $20B+（consensus $17B），来自高 NA EUV 单价 +20% upgrade 周期 [ASML investor day 2024](url) + 中国 lithography 国产替代失败留出 incremental 需求 [ASML China revenue trajectory](url)。Catalyst: Q3 2026 财报（10/22）EUV bookings 数据 + 2027 capacity expansion guidance。关键假设：(1) 高 NA 客户付费意愿 [TSMC capex commentary](url)；(2) Intel 晶圆代工进度不放缓采购 [Intel Q2 call](url)；(3) 中国 SMIC 等无法量产替代品 [行业研究](url)。

##### 5.2 Short leg thesis（why Y should underperform）

同样按 alpha-thesis 简化逻辑：
- **Variant view vs short consensus**: 你比看空 Y 的人还要看空在什么具体数字上
- **Why this gap exists**
- **Catalyst（下行）**
- **关键假设**

例（Short AMAT）：
> Variant view: 2026 收入 -8%（consensus -3%），核心是 memory 客户 capex cut 比 sell-side 模型多 [Samsung capex guidance](url) + Etch share 已到顶 [LAM cross-check](url)。Catalyst: Q4 2026 财报（11月）若 memory 收入 YoY < -20%；Samsung 半年度 capex 公告（春季）。关键假设：(1) Memory chip 价格回升不带动 capex（cycle 已变）；(2) Etch share gain 不能再 offset memory weakness；(3) 服务收入增速放缓 [10-Q service revenue trajectory](url)。

##### 5.3 Spread converge mechanism

**关键：什么具体事件 / 数据点会让 spread 收敛？**不能是"市场迟早会认识到"——要具体到事件 / 季度 / 数据点。

例：
> 2026 Q3 财报后：ASML EUV bookings 公布若 > $5B 同时 AMAT memory 收入 -25% YoY，spread 应收敛 8-12%（基于历史 spread vs sub-segment performance regression：每 1% memory revenue spread 对应约 1.5x EV/EBITDA spread）[历史回归数据](url)。

#### 6. 入场触发条件

具体的 entry trigger（不允许"现在就建仓"）：

- **Spread 当前位置**: z-score 或 percentile（来自 §3）
- **入场要求的 spread level**: 典型 z < -1σ 或 percentile < 20%
- **建仓节奏**: 一次入场 vs 分批 averaging in（建议 3 批：1/3 立即 + 1/3 一周后 + 1/3 财报前）
- **Timing 偏好**: 财报前（前 5 个交易日通常 spread 加剧）/ 财报后（基本面 confirmed）/ 财报中
- **流动性要求**: 单笔订单 < 日均成交量 5%；bid-ask spread < 5bps；total trade size < 单股 10D ADV
- **Borrow check**: short leg borrow availability + rate（< 100bps annualized 可接受）

#### 7. 退出触发条件

至少 4 类退出 trigger（必须全部具体化）：

| 退出类型 | 具体 trigger | Action |
|---|---|---|
| **Thesis played out** | Spread 收敛到 target_spread (frontmatter) | Close 全部，触发 decision-journal |
| **Thesis 失效（Long leg）** | Long leg 论点击穿 [具体数字]（如 ASML EUV bookings < $3B） | Close 全部 |
| **Thesis 失效（Short leg）** | Short leg 论点击穿（如 AMAT memory 收入 YoY 转正） | Close 全部 |
| **Stop-loss spread** | Spread 反向到 kill_spread (frontmatter) | Close 全部，记录失败 |
| **Single-name 事件** | 任一边被收购 / 重组 / CEO 离职 / 重大监管 | 立即 Close（fundamental 假设破坏） |
| **Time decay** | 持有 > time_horizon 仍无 converge 信号 | Review，决定继续 / 解 pair |
| **Borrow recall** | Short leg borrow 被 recall 或 rate > 5% annualized | 强制 close（成本侵蚀回报） |

#### 8. 风险 / Pair 失效模式（Pre-mortem）

明确列出 pair 经典失败 mode + 应对：

| 失败 mode | 历史案例 | 概率 | Mitigation |
|---|---|---|---|
| **Macro shock 双杀** | 2020/3 systemic risk-off，long/short 都 -20% | 10-15% in 12M | Position sizing 不超过 portfolio 5% |
| **行业 re-rating** | 2022 H2 半导体设备整体 -40%，spread 反而扩大 | 15-20% | Beta-neutral sizing；准备分批解 pair |
| **单边公司事件** | Long 被低估值收购→ spread 暴扩（"Long Williams / Short Spectra Energy"案，被 Energy Transfer 改报价时一周 +15%） | 5-10% per leg | 单股事件 trigger 立即 close |
| **Correlation 失效** | 2024 NVDA 从"半导体"重新定位"AI infrastructure"，半导体 pair 失效 | 10-20% over 12M | Quarterly correlation re-test |
| **Borrow availability shock** | Short leg borrow 紧张 / 被 recall（GME 事件加剧 small-cap short squeeze 风险） | 5% small caps / < 1% large caps | 只做 large-cap pair；borrow rate 监控 |
| **Carry cost 累积** | 12 个月 borrow + funding 累积 5-10%，侵蚀 spread converge 收益 | 累积 effect | 入场时计算 net 12M expected return after carry |

每条都要给概率估计 + 具体 mitigation。

### A.5 Sizing 详细考量

Pair sizing 不只是"两边数字相同"。三种 sizing method：

#### Dollar-neutral
- Long $X = Short $Y
- 优点：简单、流动性约束最直接
- 缺点：未 hedge beta 差异；如果 long beta 1.0 / short beta 1.5，市场跌 10% 时 pair 损失 5%

#### Beta-neutral（推荐 default）
- Long weight 1.0 / Short weight = beta(L) / beta(S)
- 优点：hedge 共同 macro 因子
- 缺点：需要定期 rebalance（beta 漂移）；short 权重 > 1.0 时流动性 / borrow 成本上升

#### Vol-neutral
- 按 volatility 反向加权（vol 大的腿少配）
- 适用于：vol 差异显著的 pair（如 small-cap vs large-cap）

**Pair 总 sizing 原则**：单 pair 不超过 portfolio 5%（gross），新建 pair 默认从 2-3% 开始 averaging in。

### A.6 Spread-log.md 初始 observation

Builder 完成后必须初始化 spread-log，记录 entry observation：

```yaml
schema_version: 1
document_type: spread_log
pair_id: "[LONG]-[SHORT]"
long_ticker: "[X]"
short_ticker: "[Y]"
spread_definition: "long total return - short total return"
base_currency: USD
created_at: YYYY-MM-DD
entry_schema: spread_observation_v1
```

第一条 observation（entry）：

````markdown
```spread_observation_v1
date: 2026-05-07
as_of: 2026-05-07 16:00 ET
note: "ENTRY"
long_price: 750.0
short_price: 165.0
long_weight: 1.0
short_weight: -1.05  # beta-adjusted
spread_value: 0.0     # entry baseline
spread_zscore: -2.0   # 来自 thesis frontmatter
beta_180d: 0.95
correlation_180d: 0.85
pnl_since_entry_pct: 0.0
borrow_rate_annual: 0.005
thesis_health: active
action: open
sources:
  - title: "Bloomberg pricing"
    url: "[link 待补]"
```
````

### A.7 Builder 输出篇幅

1200-2000 字 + 5 张表（setup、相关性、spread 历史、beta/correlation、风险矩阵）。

低于 1200 字大概率是论点不够具体；超过 2000 字开始水。

---

## Mode B: Monitor（监控现有 pair）

### B.1 触发

- "我的 X-Y pair 现在怎么样"
- "X-Y 还成立吗"
- "更新 spread-log"
- "pair 该解了吗"
- "review 一下所有 pair"（可批量处理多个 pair）

### B.2 工作流

1. 读取 `pairs/[X-Y]/thesis.md` frontmatter（特别是 entry_spread / target_spread / kill_spread / next_catalyst）
2. 读取 `pairs/[X-Y]/spread-log.md` 历史 observations
3. 拉取当前 spread 数据 + as-of 时间戳
4. 给出 4 部分输出（chat 显示 + 部分 append 到 spread-log）

### B.3 Monitor 输出格式

#### 1. Spread 状态

| | Entry | Target | Kill | 当前 | 距 Target | 距 Kill |
|---|---|---|---|---|---|---|
| Spread (z-score) | -2.0σ | 0σ | +1σ | -1.2σ | 1.2σ to go | 2.2σ buffer |
| Pair P/L since entry | - | - | - | +6.5% | - | - |

**趋势**：最近 5 / 20 个交易日 spread 移动方向 + 速率。

#### 2. P/L 来源拆解（核心，区分 alpha vs beta）

| 来源 | P/L 贡献 | 解读 |
|---|---|---|
| Long leg P/L (absolute) | +8% | Long thesis 是否 played out |
| Short leg P/L (absolute, 空头视角) | +3%（空头赚的，short 跌 -3%） | Short thesis 是否 played out |
| Spread converge | +5% | Spread 是否如预期收敛 |
| Carry cost (borrow + funding, annualized) | -1.5% | 持有成本累积 |
| Net Pair P/L | +6.5% | = 上述加总（dollar-neutral 简化） |

**关键判断**：
- **如果 P/L 主要来自单边而非 spread converge** → pair 实际是单边 trade，应重新评估 thesis（可能解 pair 转单边）
- 例："Long +8%，Short +3% (空头赚)，但 spread 实际只收敛 1%——P/L 大部分来自 long leg fundamental，不是 pair converge thesis"

#### 3. Thesis 健康度

按 §A.4.5 的 long thesis 和 short thesis 分别评估：

| | Status | 关键变化 | Source |
|---|---|---|---|
| Long thesis (§5.1 假设) | still valid / weakened / invalidated | 列出哪条 assumption 变化 | [新数据 / event](url) |
| Short thesis (§5.2 假设) | still valid / weakened / invalidated | 同上 | ... |
| Macro / correlation regime | stable / shifting | 共同因子是否变化 | ... |

#### 4. Action 建议

| 情景 | Action | 触发其他 skill |
|---|---|---|
| Spread 已到 target + 两边 thesis played out | **close** | decision-journal (close + outcome_v1) |
| Spread 接近 target 但有一边 thesis 仍 valid | **trim**（部分获利，留 50%） | decision-journal (trim) |
| Spread 反向但未触 kill + 两边 thesis 仍 valid | **monitor / add**（视 conviction） | 无（或 add → decision-journal） |
| Spread 反向到 kill / 一边 thesis invalidated | **close**（记录失败） | decision-journal (close + outcome_v1) |
| Spread 不动但 carry cost > 30% 预期收益 | **review** | thesis-tracker（重审 pair thesis） |
| 单边 single-name 事件触发 | **close immediately** | decision-journal + bear-pre-mortem |

### B.4 Monitor 写入

每次 monitor 必须 append 一条 observation 到 `pairs/[X-Y]/spread-log.md`：

````markdown
```spread_observation_v1
date: 2026-08-15
as_of: 2026-08-15 16:00 ET
note: "Q2 print review"
long_price: 820.0
short_price: 162.0
long_weight: 1.0
short_weight: -1.05
spread_value: 6.5
spread_zscore: -1.2
beta_180d: 0.92
correlation_180d: 0.83
pnl_since_entry_pct: 6.5
borrow_rate_annual: 0.005
thesis_health: active
action: monitor
notes_brief: "spread 收敛中，long thesis 主要 driver"
sources:
  - title: "ASML Q2 call transcript"
    url: "[link 待补]"
```
````

如果 action 是 `close` / `add` / `trim`，触发 `decision-journal` 并 update `thesis.md` frontmatter（`health_status` / `updated_at` / `next_catalyst`）。

### B.5 Monitor 输出篇幅

400-700 字。Monitor 是定期检查工具，不是 deep analysis。需要 deep analysis 时触发 thesis-tracker 重审或 bear-pre-mortem 重做。

---

## Workflow 联动

| 场景 | 触发的下游 skill |
|---|---|
| Builder 完成 → 入场决策 | `decision-journal`（写 open entry） |
| Monitor 发现 thesis 失效 | `bear-pre-mortem`（重审 pair） |
| Monitor 触发 close | `decision-journal`（写 close + outcome_v1，含 P/L attribution） |
| 来自其他 skill 的 pair 候选 | `peer-deep-dive` §5B 的 Long X / Short Y 建议直接接入 Builder |
| 跨市场 pair（如 A/H） | `cross-market-compare` 输出 pair candidate 后接入 Builder |
| Earnings 后调整 | `earnings-setup` post-print 的 `pair_readthrough` 字段触发 Monitor |

---

## 反模式自查

写完 Builder 必须自检：

**Long/Short thesis 独立性**
- ❌ Short leg thesis 写成"X 比 Y 好"——没有独立 short thesis，是装饰性 short
- ❌ Long leg thesis 全部论点 = "和 short 比相对好" → 没有 absolute thesis
- ❌ Pair 论点是"X 估值低，Y 估值高"——这不是论点，是 spread observation
- ❌ Spread converge mechanism 是"市场迟早会认识到" → hope 不是 catalyst

**业务相关性**
- ❌ "两家都做半导体设备" → 没量化客户重叠 / 终端市场重叠
- ❌ Correlation < 0.7 但仍叫 pair → 不是真 pair
- ❌ 业务完全相同（都做 EUV）→ 没有结构性差异点产生 spread

**Spread 量化**
- ❌ "估值有差距" → 没给 z-score / percentile
- ❌ Spread 在 mean 附近 (z < ±0.5σ) 仍建议建仓 → entry 不 attractive
- ❌ Spread 在 ±3σ 极端但没考虑 regime change → 可能 spread 不会回归

**Sizing**
- ❌ Dollar-neutral 但两腿 beta 差异 > 0.3 → 没 hedge macro
- ❌ 单 pair > 5% portfolio → sizing 过大
- ❌ 没考虑 borrow cost → 可能侵蚀全部预期回报

**风险 / 失败 mode**
- ❌ §8 风险只列两三条 → pair 失败 mode 历史上很多，没认真想
- ❌ 每条风险无 mitigation → 等于知道但不行动

**Source / 反幻觉**
- ❌ Spread 数字无 as-of 时间戳
- ❌ Beta / correlation 无具体计算窗口
- ❌ Long thesis 和 short thesis 用了不同 cutoff 数据
- ❌ Borrow rate 无 source（不是 backtest 假设）

Monitor 必须自检：
- ❌ P/L 没拆解到 long/short/spread/carry → 看不出 alpha 来源
- ❌ Thesis health 默认 "still valid" 没具体复查 → 装作 thesis 不变
- ❌ Action 是 "monitor" 但没说下次 review 触发条件 → 没具体下一步

---

## 篇幅基准

- **Builder 完整 thesis**: 1200-2000 字 + 5 张表
- **Monitor 输出**: 400-700 字
- 低于下限大概率内容不足；超过上限开始水或越权（应该触发其他 skill）
