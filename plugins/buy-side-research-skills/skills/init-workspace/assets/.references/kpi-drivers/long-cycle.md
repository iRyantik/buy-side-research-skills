# Long-Cycle — KPI Driver

航空/国防 / 核电 / 造船 / 航天 / EPC

## Raw Fields (→ `/financial-data`)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Backlog by Program | `segments[].metric="order_backlog"` | 分项目在手 | backlog by program | プログラム別 |
| Orders | `supplementary.orders` | 新签订单 | new orders | 受注高 |

## Derived Ratios (→ stock-quickread §4(c) Driver 表)

Visibility (years) = backlog ÷ annual rev
Avg Project Size = backlog ÷ program count
Backlog YoY = (backlog_t - backlog_t-1) / backlog_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Backlog / Annual Rev | Orders YoY
