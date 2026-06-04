# SaaS / Software — KPI Driver

SaaS / 企业软件 / 平台

## Raw Fields (→ `/financial-data --lite` elastic collection)

| KPI | actuals | CN | EN | JP |
|---|---|---|---|---|
| ARR | `supplementary.arr` | 年度经常性收入 | ARR | 年間経常収益 |
| GRR | `supplementary.grr` | 毛留存率 | gross retention | グロスリテンション |
| NRR | `supplementary.nrr` | 净留存率 | net retention | ネットリテンション |
| Churn % | `supplementary.churn_pct` | 流失率 | churn rate | 解約率 |
| Customer Count | `supplementary.customer_count` | 客户数 | logo count | 顧客数 |

## Derived Ratios (→ stock-quickread §4(c) Driver 表)

Magic Number = ARR added ÷ S&M
Rule of 40 = Revenue Growth% + FCF%
ARR YoY = (arr_t - arr_t-1) / arr_t-1

## Elastic Ratios (→ stock-quickread §4(b))

NRR | Magic Number | ARR YoY
