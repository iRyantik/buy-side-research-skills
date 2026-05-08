---
name: decision-journal
description: Use when recording, reviewing, or closing an investment decision such as open, add, trim, close, or review for an equity position or pair trade.
---

# Decision Journal

把买卖动作写成可复盘的 append-only 决策日志。目标不是写漂亮 memo，而是让三个月后能做 conviction calibration、P/L attribution 和错误归因。

## Source 政策

遵守 `CLAUDE.md §3`；若冲突，以 `CLAUDE.md` 为准。价格、估值、仓位、benchmark / pair leg、source links 必须可追溯；拿不到 source 就标记 `[需查证]` / `[来源待补]`。

## 触发场景

- "记录一下这个 decision"
- "我决定建仓 / 加仓 / 减仓 / 平仓"
- "把这次 trade 写进 journal"
- "帮我复盘这个动作"

## 状态文件

写入 `journal/decisions.md`。文件级 frontmatter 必须是第一段：

```yaml
schema_version: 1
document_type: decision_log
append_only: true
entry_schema: decision_v1
```

每条决策追加一个 YAML block，不改旧 entry：

````markdown
```decision_v1
decision_id: 2026-05-07-XOM-open-001
date: 2026-05-07
ticker: XOM
trade_structure: single_name
action: open
direction: long
position_gross_pct: 2.0
position_net_pct: 2.0
price_at_decision: 120.5
valuation_at_decision: "6.8x NTM EV/EBITDA"
conviction: 4
expected_upside_pct: 35
expected_downside_pct: -15
time_horizon: 12-18M
entry_trigger: "variant view confirmed by Q1 print"
source_of_edge: "market underwrites declining capital discipline; my view assumes buyback acceleration"
linked_thesis: coverage/XOM/thesis.md
sources:
  - title: "Q1 2026 earnings release"
    url: "[link 待补]"
```
````

`action` 只允许：`open`, `add`, `trim`, `close`, `review`。

## 平仓闭环 (outcome_v1)

`open` 时只填 `decision_v1`。**当 `action: close` 时，必须在 `decision_v1` block 之后追加一个 `outcome_v1` block**，关联回原 entry。这是 conviction calibration 和错误归因的核心数据——没有 outcome 闭环的 journal 等于流水账。

````markdown
```outcome_v1
decision_id: 2026-05-07-XOM-open-001  # 关联到原 open entry 的 decision_id
close_date: 2026-09-15
close_price: 145.0
holding_period_days: 131
realized_pnl_pct: 20.3
realized_pnl_vs_benchmark_pct: 12.5  # 相对 benchmark（SPX/沪深300/sector ETF），明确 benchmark
benchmark: "SPX"
thesis_outcome: right / wrong / partially_right
thesis_outcome_reason: "variant view on capex discipline correct, but timing slow; market only re-rated after Q3 print"
timing_outcome: right / on_time / too_early / too_late
exit_trigger: "thesis played out / kill triggered / catalyst missed / repositioning / stopped out"
conviction_calibration:
  initial_conviction: 4   # 原 decision_v1 里写的 conviction
  ex_post_appropriate: high / appropriate / low  # 事后看 conviction 给得对不对
  notes: "应该给 5——variant view 在 Q1 已经 confirm，可以更大仓位"
what_i_learned:
  - "Capital discipline thesis 的 timing 取决于 buyback 公告，不是 fundamental"
  - "Pair trade 中 long leg 弱于预期但 short leg 暴跌 30%——edge 来自 short side"
sources:
  - title: "Q3 2026 earnings release"
    url: "[link 待补]"
```
````

**outcome_v1 强制约束**：
- `thesis_outcome` 必须诚实——thesis 错了赚钱（运气）和 thesis 对了亏钱（执行 / timing 问题）都要明确标注，否则失去复盘价值
- `realized_pnl_vs_benchmark_pct` 必须有——绝对回报掩盖系统性 beta，相对回报才反映 alpha
- `what_i_learned` 必须 ≤ 3 条具体的，不允许"以后多看数据"这种空话
- `conviction_calibration.ex_post_appropriate` 不允许默认填 `appropriate`——大多数 trade 实际是 calibration 偏离的，自检要诚实

**Pair trade 的 outcome_v1 特殊字段**：
- `pnl_attribution`: 拆解 P/L 来源（long leg / short leg / spread / carry cost）
- 例：`"long +5%, short +18% (avoided drawdown), spread +13%, borrow cost -2%"`

## 输出格式

1. **Decision Entry**：完整 `decision_v1` YAML block。
2. **One-line reason**：一句话解释为什么现在做。
3. **What would prove this wrong**：最短 kill / review trigger。
4. **Missing fields**：如果 price、valuation、sources 等缺失，列出待补项，不要伪造。

## 反模式

- 不写 conviction 数字。
- 只写叙事，不写 price / valuation / position。
- 事后修改旧 entry 来美化判断。
- 把"看情况"写成 action。
- **`action: close` 但没追加 `outcome_v1`** —— journal 失去最重要的复盘价值。
- **`thesis_outcome: right` 但 P/L 是负的，或 `wrong` 但 P/L 是正的，且没标注归因** —— 没有诚实区分"thesis 对错"和"P/L 对错"，是骗自己。
- **`conviction_calibration` 全部填 `appropriate`** —— 不可能所有 trade 都 calibration 完美，这是不诚实自检。
- **`what_i_learned` 写空话**（"以后要更谨慎" / "需要多看数据"）—— 没具体行为改变就等于没学到。
