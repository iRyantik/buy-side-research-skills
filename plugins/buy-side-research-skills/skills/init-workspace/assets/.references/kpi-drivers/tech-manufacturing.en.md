# Tech Manufacturing — KPI Driver

> This is the English translation of [tech-manufacturing.md](./tech-manufacturing.md). The Chinese version is the source of truth.

Semiconductor Equipment / Battery / Solar / 3D Printing

## Raw Fields (→ `/financial-data`)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Installed Base | `supplementary.installed_base` | 装机台数 | tool count | 設置台数 |
| Backlog | `supplementary.order_backlog` | 在手订单 | order backlog | 受注残高 |
| Orders | `supplementary.orders` | 新签订单 | new orders | 受注高 |

## Derived Ratios (→ stock-quickread §4(c) Driver table)

Book-to-Bill = orders ÷ revenue
Backlog YoY = (backlog_t - backlog_t-1) / backlog_t-1
Orders YoY = (orders_t - orders_t-1) / orders_t-1

## Elastic Ratios (→ stock-quickread §4(b))

R&D / Rev | Backlog YoY | Orders YoY
