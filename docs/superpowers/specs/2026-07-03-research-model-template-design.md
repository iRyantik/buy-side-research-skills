# actuals-resolved.json 统一模板设计

> **Deprecated.** 参见 `references/research-model-schema.md` (2026-07-04)。本文档保留仅作历史参考。

## 1. 设计目标

一个 JSON 文件同时承载：

- GAAP + non-GAAP 双口径
- 年度 + 季度
- 三表（利润表、资产负债表、现金流量表）
- 多维度段数据（运营段、地理、终端市场）
- 市场数据（股价、估值、分析师一致预期）
- 弹性 KPI
- GAAP → non-GAAP 调整桥接
- 投影年结构（与 actuals 同级）
- 字段级来源追踪
- 所有未拉到字段 = `null`

## 2. 顶层结构

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-03T00:00:00Z",
  "identity": { ... },
  "financial": { ... },
  "market": { ... },
  "kpi": { ... }
}
```

### 2.1 identity

```json
"identity": {
  "name": "Howmet Aerospace",
  "ticker": "HWM.US",
  "market": "us",
  "currency": "USD",
  "accounting_standard": "us_gaap",
  "cik": 4281,
  "sic": "3350",
  "fiscal_year_end": "1231",
  "sector": null,
  "industry": null,
  "employees": null,
  "filer_category": "Large accelerated filer"
}
```

| 字段 | type | 说明 |
|------|------|------|
| `accounting_standard` | str | `"us_gaap"` / `"ifrs"` / `"cn_gaap"` / `"jp_gaap"` |
| `market` | str | `"us"` / `"cn"` / `"hk"` / `"jp"` / `"kr"` / `"tw"` / `"eu"` |
| `fiscal_year_end` | str | `"1231"` / `"0331"` 等 |

### 2.2 financial

```json
"financial": {
  "FY2023": {
    "annual": {
      "gaap": { "is": {}, "bs": {}, "cf": {}, "segments": [] },
      "non_gaap": { "is": {}, "adj": {}, "segments": [], "reconciliation": {} }
    },
    "Q1": { "gaap": {}, "non_gaap": {} },
    "Q2": { "gaap": {}, "non_gaap": {} },
    "Q3": { "gaap": {}, "non_gaap": {} },
    "Q4": { "gaap": {}, "non_gaap": {} }
  },
  "FY2024": { ... },
  "FY2025": { ... },
  "FY2026E": { ... }
}
```

### 2.3 层级规则

```
Layer 1: FY2023 / FY2024 / FY2025 / FY2026E …（投影年与 actuals 同级）
Layer 2: annual / Q1 / Q2 / Q3 / Q4
Layer 3: gaap / non_gaap
Layer 4 (gaap):   is / bs / cf / segments
Layer 4 (non_gaap): is / adj / segments / reconciliation
```

- 投影年（FY2026E+）所有 gaap 字段 = `null`（无实际数据）
- 投影年 non_gaap 字段 = Agent 填充的假设值

## 3. gaap.is（利润表）

```json
"gaap": {
  "is": {
    "rev": 8252, "cogs": 5432, "gp": 2820,
    "sga": 370, "rnd": 37,
    "oi": 2046,
    "ebitda_gaap": 2329,
    "interest_income": 20,
    "interest_expense": 171,
    "other_income": 1,
    "pretax": 1840,
    "tax": 332,
    "ni": 1508,
    "ni_attr_parent": 1506,
    "minority": 2,
    "eps_basic": 3.73,
    "eps_diluted": 3.71,
    "shares_wa_basic": 404,
    "shares_wa_diluted": 406,
    "dividend_per_share": 0.44,
    "other_items": { "gain_on_sale": 15, "asset_write_down": -8 },
    "da": 283
  },
  "is._source": {
    "rev": "sec_10k",
    "oi": "sec_10k",
    ...
    "ebitda_gaap": "sec_10k"
  }
}
```

| 字段 | type | 说明 |
|------|------|------|
| `ebitda_gaap` | num | GAAP EBITDA = OI + D&A（非 non-GAAP）|
| `da` | num | IS 入账的 D&A（与 CF 表的 D&A 同值）|
| `other_items` | obj | **公司特有项目，模板未定义**。值已含在汇总行（oi/pretax/ni）中，不加不减，只做拆分展示。|
| `.*._source` | obj | 平行块，逐字段标来源 |

> **other_items 规则**：模板没有命名到的项目放这里。其值已经被包含在 `oi` / `pretax` / `ni` 等汇总行里，不需要额外加减。

**派生字段不存**（运行时计算）：`gross_margin`、`operating_margin`、`net_margin`。

## 4. gaap.bs（资产负债表）

```json
"gaap": {
  "bs": {
    "cash": 742,
    "short_term_investments": null,
    "accounts_receivable": 1150,
    "inventory": 1850,
    "prepaid_expenses": null,
    "current_assets": 3750,
    "ppe_net": 2650,
    "goodwill": 4022,
    "intangible_assets": 1250,
    "right_of_use_asset": null,
    "other_noncurrent_assets": null,
    "total_assets": 11179,
    "accounts_payable": 850,
    "short_term_debt": 354,
    "current_liabilities": 1850,
    "long_term_debt": 2859,
    "operating_lease_liability": null,
    "deferred_revenue": null,
    "other_noncurrent_liabilities": null,
    "total_liabilities": 5826,
    "total_debt": 3213,
    "preferred_stock": null,
    "common_stock": 1,
    "additional_paid_in_capital": null,
    "retained_earnings": null,
    "accumulated_oci": null,
    "treasury_stock": null,
    "total_equity": 5353,
    "liabilities_and_equity": 11179,
    "other_items": {}
  },
  "bs._source": {}
}
```

派生字段（不存）：`working_capital`、`book_value_per_share`。

## 5. gaap.cf（现金流量表）

```json
"gaap": {
  "cf": {
    "net_income": 1508,
    "da": 283,
    "sbc": 73,
    "deferred_tax": null,
    "change_in_receivables": null,
    "change_in_inventory": null,
    "change_in_payables": null,
    "change_in_other_wc": null,
    "op_cf": 1450,
    "capex": -280,
    "acquisitions": null,
    "investing_cf": null,
    "debt_issuance": null,
    "debt_repayment": null,
    "stock_repurchase": -150,
    "dividends_paid": -75,
    "financing_cf": null,
    "fcf": null,
    "other_items": {}
  },
  "cf._source": {}
}
```

派生字段（不存）：`fcf = op_cf − capex`。

## 6. gaap.segments / non_gaap.segments

```json
"gaap": {
  "segments": [
    { "type": "operating", "name": "Engine Products", "rev": 4320 },
    { "type": "operating", "name": "Fastening Systems", "rev": 1745 },
    { "type": "operating", "name": "Engineered Structures", "rev": 1148 },
    { "type": "operating", "name": "Forged Wheels", "rev": 1039 }
  ],
  "segments._source": {
    "Engine Products.rev": "sec_10k"
  }
},
"non_gaap": {
  "segments": [
    { "type": "operating", "name": "Engine Products", "ebitda": 1438, "margin": 0.333 },
    { "type": "operating", "name": "Fastening Systems", "ebitda": 530, "margin": 0.304 },
    { "type": "operating", "name": "Engineered Structures", "ebitda": 243, "margin": 0.212 },
    { "type": "operating", "name": "Forged Wheels", "ebitda": 296, "margin": 0.285 }
  ],
  "segments._source": {}
}
```

| 字段 | type | 说明 |
|------|------|------|
| `type` | str | `"operating"` / `"geography"` / `"end_market"` / `"product"` |
| `name` | str | 段名 |
| `rev` | num | 段营收（gaap 下必填）|
| `ebitda` | num | 段 EBITDA（non_gaap 下必填）|
| `margin` | num | 段利润率（派生）|

多维度可并存：

```json
[
  { "type": "operating", "name": "Engine Products", "rev": 4320 },
  { "type": "geography", "name": "United States", "rev": 5000 },
  { "type": "geography", "name": "Europe", "rev": 1500 },
  { "type": "end_market", "name": "Aero - Commercial", "rev": 3200 },
  { "type": "end_market", "name": "Defense", "rev": 800 }
]
```

## 7. non_gaap.is

```json
"non_gaap": {
  "is": {
    "ebitda": 2390,
    "ebitda_margin": 0.290,
    "op": 2046,
    "ni": 1508,
    "eps_adjusted": 3.71,
    "fcf": 1170
  },
  "is._source": {
    "ebitda": "ir_q4_fy25",
    "op": "sec_10k"
  }
}
```

## 8. non_gaap.adj（调整明细）

完全弹性 key-value。每家公司的 non-GAAP 调整项不同。

```json
"non_gaap": {
  "adj": {
    "sbc": 73,
    "restructuring": 15,
    "amort_intangible": 32,
    "acquisition_cost": null,
    "inventory_step_up": null,
    "impairment": null,
    "fx_loss": 3,
    "legal_settlement": null,
    "other": -7,
    "total": 116
  },
  "adj._source": {
    "sbc": "cf_sbc",
    "fx_loss": "sec_10k"
  }
}
```

| 字段 | type | 说明 |
|------|------|------|
| `total` | num | `Σ(adj)` 派生 |
| `other` | num | 未分类調整 |
| `other_items` | obj | **公司特有调整项，模板未定义**。值计入 `total`（影响 reconciliation 验证）。|
| `.*_source` | obj | 平行块 |

`missing_items` 说明：当 `gaap_value + Σadj + Σother_items ≠ non_gaap_value` 时，`covered: false`，agent 需追溯差额原因并填在 `missing_items[]` 里。不是数据，是验证结果。

## 9. non_gaap.reconciliation（自动验证）

```json
"non_gaap": {
  "reconciliation": {
    "ebitda": {
      "gaap_ebitda": 2329,
      "gaap_ebitda_source": "oi + da",
      "total_adjustments": 61,
      "expected_non_gaap": 2390,
      "actual_non_gaap": 2390,
      "diff": 0,
      "covered": true
    },
    "op": {
      "gaap_op": 2046,
      "gaap_op_source": "sec_10k",
      "total_adjustments": 0,
      "expected_non_gaap": 2046,
      "actual_non_gaap": 2046,
      "diff": 0,
      "covered": true
    }
  }
}
```

## 10. quarterly

Q 级结构与 annual 完全一致，平级放在年度下：

```json
"FY2025": {
  "annual": { "gaap": { ... }, "non_gaap": { ... } },
  "Q1": { "gaap": { "is": { "rev": 1942, "gp": 652, "oi": 490, "ni": 344, "tax": 102 }, "segments": [...] }, "non_gaap": { "is": { "ebitda": 572 }, "segments": [...] } },
  "Q2": { ... },
  "Q3": { ... },
  "Q4": { ... }
}
```

Q 级不存 `bs` 和 `cf`（一般为空或 4Q 合计）。

## 11. market

```json
"market": {
  "price": 270.41,
  "price_date": "2026-07-02",
  "mcap_m": 108193,
  "shares_m": 400.1,
  "enterprise_value_m": 110664,
  "pe_ttm": 62.9,
  "pe_fwd": 44.9,
  "pb": 19.6,
  "ps": 12.5,
  "ev_ebitda": 43.2,
  "ev_revenue": 12.8,
  "peg": null,
  "dividend_yield": 0.0018,
  "beta": 1.19,
  "hi52": 290.63,
  "lo52": 169.45,
  "target_price_mean": 305.98,
  "target_price_high": null,
  "target_price_low": null,
  "recommendation": null,
  "analyst_count": null,
  "custom_metrics": {},
  "_source": {
    "price": "yfinance"
  }
}
```

## 12. kpi

完全弹性 key-value：

```json
"kpi": {
  "order_backlog": null,
  "orders": null,
  "book_to_bill": null,
  "installed_base": null,
  "capacity": null,
  "utilization": null,
  "production_volume": null,
  "unit_cost": null,
  "arr": null,
  "nrr": null,
  "churn": null,
  "customer_count": null,
  "same_store_sales": null,
  "fleet_hours": 45000000,
  "engine_spares_rev": 520,
  "_source": {}
}
```

## 13. 投影年（FY2026E）

结构与 actual FY 完全一致。不同之处：

| 差异 | 说明 |
|------|------|
| `gaap.is` 全 `null` | 无实际 SEC 数据 |
| `non_gaap.is` = Agent 假设 | 来自 driver-map driver |
| `non_gaap.segments` = Agent 假设 | |
| `Q1`-`Q4` 也全 `null` | Q 列由 Q driver 自动生成 |
| `annual.non_gaap.is.ebitda` | Agent 填入指引值，如 3060 |

## 14. 来源追踪规则

`_source` 块与数据块同层：

```json
"is": { "rev": 8252, "oi": 2046 },
"is._source": { "rev": "sec_10k", "oi": "sec_10k" }
```

`_source` 允许值：

| 值 | 说明 |
|------|------|
| `"sec_10k"` | SEC 10-K |
| `"sec_10q"` | SEC 10-Q |
| `"ir_presentation"` | IR 业绩演示 |
| `"ir_transcript"` | IR 电话会记录 |
| `"press_release"` | 新闻稿 |
| `"yfinance"` | Yahoo Finance |
| `"bridge"` | Longbridge MCP |
| `"websearch"` | Web Search + Web Fetch |
| `"assumption"` | Agent 假设（非披露）|
| `"nd"` | 公司不披露 |
| `null` | 未拉取/未知 |

## 15. 字段值规则

| 情况 | 值 | 示例 |
|------|:---:|------|
| 已从 source 拉到 | 数值 | `8252` |
| 公司不披露此项目 | `"nd"` | `"nd"` |
| Provider 未覆盖但可能存在 | `null` | `null` |
| 聚合不适用（Q 级无 BS） | 不写该键 | — |

## 16. schema_version

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-03T07:00:00Z",
  ...
}
```

每次模板结构改动 → `schema_version` 递增。`driver-map` 的 `validate_json()` 检查此版本。

## Resources

- SEC EDGAR XBRL Taxonomy: `https://www.sec.gov/edgar/sec-financial-statement-data-sets`
- yfinance documentation: `https://pypi.org/project/yfinance/`
- Longbridge OpenAPI: `https://openapi.longbridge.com`
- IR data from company quarterly earnings presentations
