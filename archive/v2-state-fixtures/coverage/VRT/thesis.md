---
schema_version: 1
document_type: thesis
ticker: VRT
company_name: Vertiv Holdings Co
coverage_area: advanced_manufacturing
industry: electrical_equipment
trade_structure: single_name
direction: long
position_status: watchlist
created_at: 2026-05-08
updated_at: 2026-05-08
conviction: 3
health_status: watch
time_horizon: 12M
next_catalyst: "2026-Q2 earnings date [来源待补]"
valuation_anchor: "Market snapshot as of 2026-05-07 23:51 UTC: price $340.01, market cap $133.3B, P/E 85.4x; live quote link below"
expected_return_base_pct: null
downside_pct: null
key_assumptions:
  - id: vrt-ai-power-demand
    statement: "AI data-center power and thermal demand remains strong enough to support elevated FY2026 organic growth."
    current_status: watch
    source: "Vertiv Q1 2026 results"
  - id: vrt-margin-durability
    statement: "Operating leverage and adjusted operating profit growth persist without material price/cost reversal."
    current_status: watch
    source: "Vertiv Q1 2026 results"
  - id: vrt-valuation-discipline
    statement: "High multiple can still be supported by revisions and order durability."
    current_status: unproven
    source: "Yahoo Finance VRT quote"
kill_criteria:
  - id: vrt-growth-guide-break
    statement: "Organic sales guide is cut materially or order commentary no longer supports data-center demand durability."
    status: not_triggered
  - id: vrt-margin-break
    statement: "Adjusted operating profit growth decelerates sharply because margins normalize faster than revenue growth."
    status: not_triggered
  - id: vrt-valuation-no-revisions
    statement: "Stock keeps a high multiple but estimates stop moving up after the next print."
    status: watch
sources:
  - title: "Vertiv Q1 2026 results"
    url: "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx"
  - title: "Vertiv investor site"
    url: "https://investors.vertiv.com/"
  - title: "Yahoo Finance VRT quote"
    url: "https://finance.yahoo.com/quote/VRT"
---

# VRT Thesis State Sample

**结论先行**：VRT 只是 watchlist / review 状态，不是建仓建议。AI 电力 fixture 显示它是最纯的 data-center power / thermal direct exposure，但估值已经很高，下一步要验证的是订单持续性、margin durability 和 valuation support。

## 一页摘要

| 项目 | 当前判断 |
|---|---|
| Thesis one-liner | Long VRT 是 AI data-center power / thermal capex 的高纯度受益表达，但必须用持续上修证明高估值。 |
| Health | `watch`，因为基本面兑现强，但 valuation discipline 未完成。 |
| Position | `watchlist`，`position_gross_pct = 0`，没有真实入场。 |
| Next catalyst | Q2 2026 earnings date `[来源待补]`，重点看 orders、organic growth、adjusted operating margin 和 backlog commentary。 |
| Missing work | 需要补 10-Q、earnings call transcript、consensus revision、peer valuation table。 |

## 事实基础

Vertiv Q1 2026 net sales 为 $2.645B，同比增长 30.0%；organic net sales +23.3%；adjusted operating profit +57.0%；公司把 FY2026 organic net sales growth 指引上调到 +29% 到 +31%。来源：[Vertiv Q1 2026 results](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx)。

## Tracker 需要关注

1. Q2 是否继续支持 FY2026 organic growth guide。
2. Adjusted operating profit growth 是否仍然高于 revenue growth。
3. Data-center exposure 是否能从 backlog / orders / customer commentary 里继续被验证。
4. 如果 quote multiple 仍高而 estimates 不再上修，thesis health 应从 `watch` 转为 `impaired`。
