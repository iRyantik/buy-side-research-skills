# Long-Cycle — KPI Driver

> This is the English translation of [long-cycle.md](./long-cycle.md). The Chinese version is the source of truth.

Aviation / Defense / Nuclear / Shipbuilding / Space / EPC

## Raw Fields (→ `financial-data --lite` elastic collection)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Backlog by Program | `segments[].metric="order_backlog"` | 分项目在手 | backlog by program | プログラム別 |
| Orders | `supplementary.orders` | 新签订单 | new orders | 受注高 |

## Derived Ratios (→ stock-quickread §4(c) Driver table)

Visibility (years) = backlog ÷ annual rev
Avg Project Size = backlog ÷ program count
Backlog YoY = (backlog_t - backlog_t-1) / backlog_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Backlog / Annual Rev | Orders YoY
