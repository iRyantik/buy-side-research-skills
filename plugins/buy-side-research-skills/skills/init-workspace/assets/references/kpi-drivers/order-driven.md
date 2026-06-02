# Order-Driven — KPI Driver

Capital Equipment / Aerospace / 船舶 / EPC

## Elastic Fields

| KPI | actuals | Source | CN | EN | JP |
|---|---|---|---|---|---|
| Backlog | `supplementary.order_backlog` | IR segment note | 在手订单 | order backlog | 受注残高 |
| Backlog by Seg | `segments[].metric="order_backlog"` | IR segment | 分业务在手 | backlog by seg | セグメント別 |
| Orders | `supplementary.orders` | IR quarterly | 新签订单 | new orders | 受注高 |
| Orders by Seg | `segments[].metric="orders"` | IR segment | 分业务新签 | orders by seg | セグメント別 |
| Installed Base | `supplementary.installed_base` | annual report | 装机量 | installed base | 設置台数 |

## Derived
- Book-to-Bill = orders ÷ revenue
- Backlog Coverage = backlog ÷ Q rev (months)

## Ratios
- Backlog / Q Rev | Orders YoY | R&D / Rev
