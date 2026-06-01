---
name: post-earnings-quick
description: Post-earnings 5-min verdict — beat/miss vs pre-print bar, thesis impact.
---

# Post Earnings Quick

5-minute post-print assessment. Not a full earnings review — a rapid verdict: did the numbers beat or miss the pre-print bar? Does the thesis still hold?

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取最新 actuals + 市场快照。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

财报后 5 分钟需要回答的不是"这份财报好不好"——而是"跟我们的 pre-print bar 比，差了多少？thesis 要改吗？" earnings-setup 管事前拆 bar，post-earnings-quick 管事后快速比。

## 输入

- Ticker
- 最近 quarterly actuals（from financial-data）
- 最近的 earnings-setup artifact（找 pre-print bar）
- 如果没有 pre-print bar → 用 consensus data 做 proxy

## 输出结构

```markdown
## Verdict

Beat / Miss / In-Line vs pre-print bar

| Metric | Actual | Pre-print Bar | Consensus | Beat/Miss |
|---|---|---|---|---|
| Revenue | $X | $Y | $Z | +2% |

## Guidance vs Consensus

| Guidance | Consensus | Delta | Implication |
|---|---|---|---|

## Thesis Impact

- Thesis status: unchanged / needs review / broken
- 如果 needs review → handoff stock-quickread
- 如果 broken → handoff bear-pre-mortem 或直接 mark dormant in coverage-tracker
```

## 反模式

- ❌ 没有 pre-print bar 就空口说 beat/miss——必须找到基准
- ❌ 写成 full earnings review
- ❌ thesis 状态不给判断（"有待观察"不算）
- ❌ 不联动 coverage-tracker 更新

## 篇幅基准

300-500 字。硬上限 500 字。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| earnings-setup | pre-print bar（beat/miss 阈值） |
| financial-data | 刚出的 actuals |
| consensus-map | 如果无 pre-print bar 做 proxy |

| 下游 | 场景 |
|---|---|
| stock-quickread | thesis needs review |
| coverage-tracker | 更新 thesis stage |
| driver-map | 如果 guidance 改变 driver 假设 |
