# Utility / Infra — KPI Driver

发电(GT) / 电网 / 水务 / 交通

## Raw Fields (→ `/financial-data --lite` elastic collection)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Regulated Asset Base | `supplementary.regulated_asset_base` | 有效资产基数 | rate base | レートベース |
| Capacity MW | `supplementary.capacity_mw` | 装机容量 | installed capacity | 設備容量 |
| Utilization | `supplementary.utilization` | 利用率 | load factor | 稼働率 |

## Derived Ratios (→ stock-quickread §4(c) Driver 表)

RAB Growth YoY = (rab_t - rab_t-1) / rab_t-1
Capacity Growth YoY = (mw_t - mw_t-1) / mw_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Utilization % | Capacity YoY
