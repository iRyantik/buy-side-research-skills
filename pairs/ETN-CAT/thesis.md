---
schema_version: 1
document_type: pair_thesis
pair_id: ETN-CAT
long_ticker: ETN
short_ticker: CAT
long_market: NYSE
short_market: NYSE
created_at: 2026-05-08
updated_at: 2026-05-08
direction: spread_converge
paper_candidate: true
trade_ready: false
conviction: 2
time_horizon: 12M
entry_spread: "[来源待补]"
target_spread: "[来源待补]"
kill_spread: "[来源待补]"
sizing_method: dollar_neutral_placeholder
long_weight: 1.0
short_weight: -1.0
benchmark: SPX
health_status: watch
next_catalyst: "Q2 2026 earnings dates [来源待补]"
sources:
  - title: "Eaton Q1 2026 results"
    url: "https://www.eaton.com/content/dam/eaton/company/investor-relations/quarterly-earnings/2026/q1/EatonReportsFirstQuarterEarningsPerShareof$2.45,RecordAdjustedEarningsPerShareof$2.72,Up13PercentOvertheFirstQuarterof2025.pdf"
  - title: "Caterpillar Q1 2026 results"
    url: "https://www.caterpillar.com/en/news/corporate-press-releases/h/1q-2026-financial-results.html"
  - title: "Yahoo Finance ETN quote"
    url: "https://finance.yahoo.com/quote/ETN"
  - title: "Yahoo Finance CAT quote"
    url: "https://finance.yahoo.com/quote/CAT"
---

# ETN-CAT Paper Pair Thesis Sample

**结论先行**：Long ETN / Short CAT 只是 paper pair candidate，不是 trade-ready pair。它适合验证 `pair-trade` 的 state schema：ETN 的 data-center electrical order evidence 更直接，CAT 有 power generation angle 但集团周期暴露更重；不过当前缺 spread history、beta、correlation、borrow 和 valuation normalization，不能开仓。

## 1. Pair One-Liner

Long ETN / Short CAT 的假设是：ETN 的 data-center electrical order momentum 更能直接转化成 electrical equipment earnings，而 CAT 的 broader machinery exposure 会稀释 AI power generation tailwind。这个假设目前只够进入 review，不够形成 pair trade。

| | Long | Short |
|---|---|---|
| Ticker | ETN | CAT |
| 业务定位 | Diversified electrical equipment，Electrical Americas data-center orders 明确 | Broader machinery + Power & Energy exposure |
| 当前价格快照 | $399.15 as of 2026-05-07 23:51 UTC | $895.69 as of 2026-05-07 23:51 UTC |
| 估值快照 | P/E 37.8x | P/E 46.2x |
| Pair readiness | Not ready | Not ready |

## 2. 为什么还不是可交易 pair

| 缺口 | 当前状态 | 需要补什么 |
|---|---|---|
| Spread history | `[来源待补]` | 3Y / 5Y relative return 和 valuation spread z-score |
| Beta / correlation | `[来源待补]` | 180D beta、180D correlation、common factor exposure |
| Borrow / liquidity | `[来源待补]` | CAT borrow availability、borrow rate、as-of |
| Segment normalization | 部分完成 | ETN Electrical Americas vs CAT Power & Energy 的 margin / order bridge |

## 3. 下一步

先只写 `pairs/ETN-CAT/spread-log.md` 的 paper observation。只有当 spread history、beta/correlation、borrow 和 valuation normalization 补齐后，才允许把 `trade_ready` 改成 true。
