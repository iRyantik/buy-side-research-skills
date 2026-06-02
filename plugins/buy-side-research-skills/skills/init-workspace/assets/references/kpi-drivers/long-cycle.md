# Long-Cycle — KPI Driver

航空/国防 / 核电 / 造船 / 航天 / EPC

## Elastic Fields

| KPI | actuals | Source | CN | EN | JP |
|---|---|---|---|---|---|
| Backlog by Program | `segments[].metric="order_backlog"` | IR segment note | 分项目在手 | backlog by program | プログラム別 |
| Orders | `supplementary.orders` | IR quarterly | 新签订单 | new orders | 受注高 |

## Derived
- Visibility = backlog ÷ annual rev (years)
- Avg Project = backlog ÷ count

## Ratios
- Backlog YoY | Orders YoY
