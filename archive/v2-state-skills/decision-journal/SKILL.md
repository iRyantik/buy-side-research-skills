---
name: decision-journal
description: Use when recording, reviewing, or closing an investment decision such as open, add, trim, close, or review for an equity position or pair trade.
---

# Decision Journal

把投资动作写成可复盘的 append-only 决策日志。目标不是写漂亮 memo，而是让三个月后能做 conviction calibration、P/L attribution 和错误归因。

## Source 政策

遵守 `CLAUDE.md §3`；若冲突，以 `CLAUDE.md` 为准。价格、估值、仓位、benchmark、pair leg、source links 必须可追溯；拿不到 source 就标记 `[需查证]` / `[来源待补]`。

## 触发场景

- "记录一下这个 decision"
- "我决定建仓 / 加仓 / 减仓 / 平仓"
- "把这次 trade 写进 journal"
- "帮我复盘这个动作"
- "这只是 review，不是 open"

## 状态文件

写入 `journal/decisions.md`。文件级 frontmatter 必须是第一段：

```yaml
schema_version: 1
document_type: decision_log
append_only: true
entry_schema: decision_v1
```

原则：

- 只 append 新 entry；禁止修改旧 entry 来美化判断。
- 如果旧 entry 有错误，用新的 `review` entry 纠正，不改旧记录。
- `close` 必须追加 `outcome_v1`。

## action 边界

| Action | 何时使用 | 必填重点 |
|---|---|---|
| `open` | 新建真实仓位或 paper trade 被用户明确当作 decision 记录 | position、price、valuation、conviction、upside/downside、linked_thesis |
| `add` | 增加已有仓位 | 新仓位、加仓触发点、原 thesis 是否变化 |
| `trim` | 降低已有仓位但未退出 | 降仓比例、P/L、剩余仓位、是否 thesis played out |
| `close` | 完全退出或 pair 结束 | `decision_v1` + `outcome_v1` |
| `review` | 进入研究队列、更新观点、watchlist、health review；没有真实交易 | 可以 `position_gross_pct: 0.0`，必须明确不是 open |

不要把"看一下"、"进入 watchlist"、"值得研究"写成 `open`。

## decision_v1 写入契约

每条决策追加一个 fenced YAML block：

```decision_v1
decision_id: 2026-05-08-VRT-review-001
date: 2026-05-08
ticker: VRT
trade_structure: single_name
action: review
direction: long
position_gross_pct: 0.0
position_net_pct: 0.0
price_at_decision: 340.01
valuation_at_decision: "P/E 85.4x; market cap $133.3B; as of 2026-05-07 23:51 UTC"
conviction: 3
expected_upside_pct: null
expected_downside_pct: null
time_horizon: 12M
entry_trigger: "AI 电力 fixture 将 VRT 识别为 top direct exposure，但 valuation / order durability work 还没完成。"
source_of_edge: "需要验证市场是否低估 data-center power / thermal demand 的持续性；当前只是 review，不是 open。"
linked_thesis: coverage/VRT/thesis.md
sources:
  - title: "Vertiv Q1 2026 results"
    url: "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx"
```

`decision_id` 格式：`YYYY-MM-DD-[TICKER-or-PAIR]-[action]-NNN`。

`trade_structure` 常用值：

- `single_name`
- `pair_trade`
- `basket`
- `hedge`

`action` 只能是 `open`, `add`, `trim`, `close`, `review`。

## close 必须追加 outcome_v1

当 `action: close` 时，必须在 `decision_v1` 后追加一个 `outcome_v1` block。没有 outcome 的 close entry 等于流水账。

```outcome_v1
decision_id: 2026-05-07-XOM-open-001
close_date: 2026-09-15
close_price: 145.0
holding_period_days: 131
realized_pnl_pct: 20.3
realized_pnl_vs_benchmark_pct: 12.5
benchmark: "SPX"
thesis_outcome: partially_right
thesis_outcome_reason: "variant view on capex discipline was right, but timing was slower than expected"
timing_outcome: too_early
exit_trigger: "thesis played out"
conviction_calibration:
  initial_conviction: 4
  ex_post_appropriate: high
  notes: "Conviction could have been higher once Q1 confirmed the variant view."
what_i_learned:
  - "Capital discipline thesis timing depended on buyback announcement, not only fundamentals."
  - "Position sizing was too small relative to confirmed variant view."
  - "Next time, separate fundamental confirmation from capital return catalyst."
sources:
  - title: "Q3 2026 earnings release"
    url: "[link 待补]"
```

约束：

- `thesis_outcome` 只能是 `right`, `wrong`, `partially_right`。
- `timing_outcome` 只能是 `right`, `on_time`, `too_early`, `too_late`。
- `what_i_learned` 至少 3 条，必须具体，不能写"以后多看数据"。
- `realized_pnl_vs_benchmark_pct` 必须有 benchmark，避免把 beta 当 alpha。

## Pair trade outcome 字段

Pair close 的 `outcome_v1` 还要加：

```yaml
pnl_attribution:
  long_leg_pct: 5.0
  short_leg_pct: 18.0
  spread_converge_pct: 13.0
  carry_cost_pct: -2.0
  notes: "P/L 主要来自 short leg，而不是 long thesis。"
```

如果 P/L 主要来自单边而不是 spread converge，必须写清楚；否则无法判断 pair 是否真的 hedge 了 common factor。

## 输出格式

1. **Decision Entry**：完整 `decision_v1` YAML block。
2. **一句话原因**：为什么现在记录这个动作。
3. **What would prove this wrong**：最短 kill / review trigger。
4. **Missing fields**：price、valuation、position、sources 缺什么就列出来，不要伪造。
5. **Next state handoff**：说明是否触发 `thesis-tracker`。

## VRT Fixture 示例

`2026-05-08-VRT-review-001` 的正确解读：

- `action: review`，不是 `open`。
- `position_gross_pct: 0.0`，所以不能进入真实 portfolio exposure。
- `linked_thesis: coverage/VRT/thesis.md`，因此会 feed into `thesis-tracker`。
- `expected_upside_pct` / `expected_downside_pct` 可以是 `null`，因为这不是建仓。

## 反模式

- 只写叙事，不写 price / valuation / position。
- 把 watchlist / research queue 写成 `open`。
- `review` entry 不链接 thesis，导致 tracker 读不到。
- `action: close` 但没追加 `outcome_v1`。
- 事后修改旧 entry 来美化判断。
- `thesis_outcome: right` 但 P/L 是负的，或 `wrong` 但 P/L 是正的，却没有解释归因。
- `conviction_calibration` 全部填 `appropriate`。
- `what_i_learned` 写空话。
