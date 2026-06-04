# Process Industry — KPI Driver

> This is the English translation of [process-industry.md](./process-industry.md). The Chinese version is the source of truth.

Oil & Gas / Chemicals / Mining / Renewable Power Generation

## Raw Fields (→ `/financial-data --lite` elastic collection)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| Production Volume | `supplementary.production_volume` | 产量 | production volume | 生産量 |
| Unit Cost | `supplementary.unit_cost` | 单位成本 | unit cost | 単位コスト |
| Utilization | `supplementary.utilization` | 利用率 | utilization | 稼働率 |

## Derived Ratios (→ stock-quickread §4(c) Driver table)

EBITDA / Unit = EBITDA ÷ production_volume
Production YoY = (vol_t - vol_t-1) / vol_t-1

## Elastic Ratios (→ stock-quickread §4(b))

Production YoY | Utilization % | CapEx / Rev
