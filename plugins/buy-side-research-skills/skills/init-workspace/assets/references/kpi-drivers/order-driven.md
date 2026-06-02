# Order-Driven — KPI Driver

Capital Equipment / Aerospace / 船舶 / EPC

## Raw Fields (→ `financial-data --lite` elastic collection)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Backlog | `supplementary.order_backlog` | 在手订单 | order backlog | 受注残高 |
| Backlog by Seg | `segments[].metric="order_backlog"` | 分业务在手 | backlog by seg | セグメント別 |
| Orders | `supplementary.orders` | 新签订单 | new orders | 受注高 |
| Orders by Seg | `segments[].metric="orders"` | 分业务新签 | orders by seg | セグメント別 |
| Installed Base | `supplementary.installed_base` | 装机量 | installed base | 設置台数 |

## Derived Ratios (→ stock-quickread §4(c) Driver 表)

Book-to-Bill = orders ÷ revenue
Backlog Coverage = backlog ÷ Q rev (months)
Orders YoY = (orders_t - orders_t-1) / orders_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Backlog / Q Rev | Orders YoY | R&D / Rev
