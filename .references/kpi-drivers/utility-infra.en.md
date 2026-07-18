# Utility / Infra — KPI Driver

> This is the English translation of [utility-infra.md](./utility-infra.md). The Chinese version is the source of truth.

Power Generation (GT) / Grid / Water / Transport

## Raw Fields (→ `/financial-data`)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Regulated Asset Base | `supplementary.regulated_asset_base` | 有效资产基数 | rate base | レートベース |
| Capacity MW | `supplementary.capacity_mw` | 装机容量 | installed capacity | 設備容量 |
| Utilization | `supplementary.utilization` | 利用率 | load factor | 稼働率 |

## Derived Ratios (→ stock-quickread §4(c) Driver table)

RAB Growth YoY = (rab_t - rab_t-1) / rab_t-1
Capacity Growth YoY = (mw_t - mw_t-1) / mw_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Utilization % | Capacity YoY
