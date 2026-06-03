# actuals-resolved.json Data Catalog

> 本文件是 `_cache/financial-data/internal/actuals-resolved.json` 的字段清单。
> 消费 actuals 的 skill 在附录中引用本文件，agent 可据此判断哪些数据可用，无需打开 JSON。
> 由 `financial-data --lite` 生成。字段存在与否取决于 provider 覆盖和公司披露。

## 顶层结构

```
actuals-resolved.json
├── meta                    # 元数据
├── market_data             # 市场快照（Bridge/yfinance/WebSearch 降级链）
├── statements              # 三表 + 可选 revenue_split
│   ├── income_statement
│   ├── balance_sheet
│   └── cash_flow
├── segments                # 分部数据（如有）
├── supplementary           # 弹性 KPI（按 business model 采集）
└── source_map              # provenance 透传（消费 skill 用此标签，不写 [actuals]）
```

---

## 1. meta

| 字段 | 类型 | 说明 |
|---|---|---|
| `ticker` | string | 如 `688097.SH` |
| `company_name` | string | 公司全名 |
| `company_slug` | string | workspace slug |
| `market` | string | `us` / `cn` / `hk` / `jp` / `kr` / `tw` / `eu` |
| `currency` | string | `CNY` / `USD` / `JPY` / `KRW` / `TWD` / `EUR` 等 |
| `data_as_of` | date | 数据拉取日期 |
| `source_layers` | object | `{financials: "longbridge_provider_api", market_data: "longbridge_bridge", ...}` |

---

## 2. market_data

> 统一增量 fill 引擎：Bridge → yfinance → WebSearch → Google Finance。
> 缺失字段 = `null`，不填 0。

| 字段 | 类型 | 说明 | 典型 source |
|---|---|---|---|
| `price` | float | 最新收盘价 | Bridge / yfinance |
| `market_cap` | float | 总市值（本地货币） | Bridge / yfinance |
| `pe_ttm` | float | 追踪市盈率 | Bridge / yfinance |
| `pe_ntm` | float | 远期市盈率 | Bridge (consensus) / WebSearch |
| `pb` | float | 市净率 | Bridge / yfinance |
| `ps_ttm` | float | 市销率 | Bridge / yfinance |
| `ev_ebitda` | float | 企业价值/EBITDA | Bridge / yfinance |
| `ev_sales` | float | 企业价值/营收 | Bridge / yfinance |
| `dividend_yield_pct` | float | 股息率 | yfinance / WebSearch |
| `beta` | float | 波动率 | yfinance |
| `eps_ttm` | float | 追踪每股收益 | 计算或 provider |
| `bps` | float | 每股净资产 | provider |
| `total_shares` | int | 总股本 | provider |
| `circulating_shares` | int | 流通股本 | provider |
| `exchange` | string | 交易所代码 | provider |
| `industry` | string | 行业分类 | provider |

---

## 3. statements

### 3.1 income_statement

> 期间标签从 provider 真实 label 读取（如 FY2024、Q1 2025、H1 FY2025），不得自行改写。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `periods` | string[] | ✅ | 可用期间列表 |
| `FY20XX.revenue` | float | ✅ | 营业收入 |
| `FY20XX.revenue_yoy_pct` | float | ✅ | 收入同比（derived） |
| `FY20XX.gross_profit` | float | best-effort | 毛利 |
| `FY20XX.gross_margin_pct` | float | best-effort | 毛利率 |
| `FY20XX.operating_income` | float | best-effort | 营业利润 |
| `FY20XX.ebit` | float | best-effort | EBIT（中国准则=营业利润） |
| `FY20XX.net_income` | float | ✅ | 归母净利润 |
| `FY20XX.net_income_yoy_pct` | float | ✅ | 净利同比（derived） |
| `FY20XX.net_margin_pct` | float | best-effort | 净利率 |
| `FY20XX.eps` | float | best-effort | 每股收益 |
| `FY20XX.r_and_d` | float | best-effort | 研发费用 |
| `FY20XX.d_and_a` | float | best-effort | 折旧摊销 |
| `FY20XX.source` | string | ✅ | 数据来源标注 |

### 3.2 balance_sheet

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `periods` | string[] | ✅ | 可用期间列表 |
| `FY20XX.total_assets` | float | ✅ | 总资产 |
| `FY20XX.total_liabilities` | float | ✅ | 总负债 |
| `FY20XX.total_equity` | float | ✅ | 所有者权益 |
| `FY20XX.cash_and_st_invest` | float | best-effort | 现金及短期投资 |
| `FY20XX.net_debt` | float | best-effort | 净负债 |
| `FY20XX.inventory` | float | best-effort | 存货 |
| `FY20XX.receivables` | float | best-effort | 应收账款 |
| `FY20XX.ppe_net` | float | best-effort | 固定资产净值 |
| `FY20XX.goodwill` | float | best-effort | 商誉 |
| `FY20XX.bps` | float | best-effort | 每股净资产 |

### 3.3 cash_flow

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `periods` | string[] | ✅ | 可用期间列表 |
| `FY20XX.operating_cf` | float | ✅ | 经营活动现金流 |
| `FY20XX.capex` | float | best-effort | 资本支出（取绝对值） |
| `FY20XX.free_cash_flow` | float | best-effort | OpCF − CapEx |

---

## 4. segments（如有）

> `status` 字段说明可用性：`from_provider` / `from_annual_report_web` / `pending_official_extraction` / `not_disclosed`。
> `segments` 是通用容器，支持 `business_line` / `geography` / `end_market` 等维度，由 `type` 区分。

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | 分部数据可用性状态 |
| `segments[].type` | string | `business_line` / `geography` / `end_market` |
| `segments[].name` | string | 分部名 |
| `segments[].revenue` | float | 分部收入（绝对值） |
| `segments[].pct_of_total` | float | 占总收入 % |
| `segments[].yoy_pct` | float | 同比增速 |
| `segments[].margin_pct` | float | 分部利润率（如有） |
| `segments[].description` | string | 业务描述 |
| `segments[].source` | string | 数据来源 |

---

## 5. supplementary（弹性 KPI）

> 按 business model 采集。搜不到标 `[未披露]`，不阻塞主流程。

| 字段 | 适用 business model | 说明 |
|---|---|---|
| `order_backlog` | order-driven / long-cycle / tech-manufacturing | 在手订单（含 period + yoy + breakdown） |
| `orders` | order-driven / tech-manufacturing | 新签订单 |
| `overseas_revenue` | 通用 | 海外收入（含占比 + yoy） |
| `installed_base` | order-driven / tech-manufacturing | 装机量 |
| `production_volume` | process-industry | 产量 |
| `utilization` | process-industry / utility-infra | 产能利用率 |
| `capacity_mw` | utility-infra | 装机容量 MW |
| `arr` | saas-software | 年度经常性收入 |
| `nrr` | saas-software | 净留存率 |
| `grr` | saas-software | 毛留存率 |
| `churn_pct` | saas-software | 流失率 |
| `customer_count` | saas-software / ai-emerging | 客户数 |
| `regulated_asset_base` | utility-infra | 监管资产基数 |
| `custom_metrics` | 通用 | 泛化兜底 `[{kpi, value, source, relevance}]` |

---

## 6. source_map

> 消费 skill 读此字段将数据字段映射到具体 [S#](url) / [I#] 标签，而非写 [actuals]。
> 每个 entry 含 `source_layer`、`url`、`detail`、`label`。

```json
"source_map": {
  "S_1": {"source_layer": "official_web", "url": "https://...Q1-results.pdf", "detail": "Q1 Results PDF p3", "label": "S1"},
  "I_1": {"source_layer": "yfinance", "url": null, "detail": "yfinance quote", "label": "I1"}
}
```

---

## 7. 消费 skill 使用规则

1. **先读 actuals-resolved.json，再读 source_map**——用 source_map 的 label（[S1]/[I1]）而非 [actuals]。
2. **actuals-only ratio rule**：所有 ratio 的 input 必须在 actuals 中有真实值。禁止用 FY20XXE / consensus / forward estimate 参与计算。
3. **缺字段静默跳过**：某个 input 缺失 → 该 ratio 不输出，不标 [未披露]，不占行。
4. **期间 label**：必须读 actuals 的真实 period label，不得把 HK H1 写成 Q2。
5. **分部口径**：分段和整体用同一利润口径；换了口径必须标注原因。
