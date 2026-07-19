# actuals-resolved.json Data Catalog

> 本文件是 `.cache/financial-data/actuals-resolved.json` 的字段清单。
> 由 `/financial-data` 生成。字段存在与否取决于 provider 覆盖和公司披露。
> Field schema 唯一来源：`.references/policy/statement-line-items.md`（117 concepts）。

## 顶层结构

```
actuals-resolved.json
├── ticker, market, source
├── identity              # 公司身份信息
├── statements            # 三表 + 分部 (concept-row 格式)
│   ├── income_statement  # [{concept, label, values: {period: value}, unit, source}]
│   ├── balance_sheet     # 同上
│   ├── cash_flow         # 同上
│   └── revenue_split     # [{segment, type, revenue: {period: value}, operating_profit: {period: value}}]
├── commentary            # 管理层讨论 (string)
├── outlook               # 业绩展望 (object)
├── market_data           # 市场快照 (yfinance/Bridge)
└── source_map            # provenance (S1: {url, detail})
```

## 1. identity

| 字段 | 类型 | 说明 |
|---|---|---|
| `ticker` | string | 如 `4183.T` |
| `name_en` | string | 公司英文名 |
| `name_native` | string | 公司本地名 |
| `fiscal_year_end` | string | 财年截止日 `03-31` / `12-31` |

## 2. statements

**格式**: concept-row 数组，每条一个财务科目。

```json
{
  "concept": "revenue",
  "label": "売上収益",
  "values": {"FY2024": 1749743, "FY2025": 1809164},
  "unit": "JPY_M",
  "source": "S1"
}
```

**规则**：
- `concept` 必填——从 statement-line-items.md registry 取标准名，registry 没有的用原生 label 的 snake_case
- `label` 选填——native language label
- `values` 的 key 从 provider/filing 真实读取（`FY2025`、`Q1 2026`、`H1 FY2025`），不硬编码
- 缺字段不存，不标 `[ND]` 也不留空行
- 全字段清单见 `statement-line-items.md`（IS 30 + BS 48 + CF 16 + SG 11 + MK 12 = 117）

## 3. market_data

| 字段 | 类型 | 说明 |
|---|---|---|
| `price` | float | 最新收盘价 |
| `market_cap` | float | 总市值（本地货币） |
| `pe_ttm` | float | 追踪市盈率 |
| `pe_ntm` | float | 远期市盈率 |
| `pb` | float | 市净率 |
| `ps_ttm` | float | 市销率 |
| `ev_ebitda` | float | EV/EBITDA |
| `dividend_yield_pct` | float | 股息率 |
| `beta` | float | 波动率 |
| `currency` | string | 货币代码 |
| `source_layer` | string | `yfinance` / `bridge` |
| `as_of` | date | 数据日期 |

## 4. source_map

```json
"source_map": {
  "S1": {
    "source_layer": "ir_tdnet",
    "url": "http://ke.kabupro.jp/...",
    "detail": "三井化学 FY2025 決算短信 PDF"
  }
}
```

## 5. 消费规则

1. 按 `concept` 名查询——不依赖字段顺序或位置
2. 从 `values` 读取期间数据——不假设 `FY2024` 一定存在
3. 缺字段 = 不渲染、不报错、不占行
4. 单位从 `unit` 字段读取——不假设所有数字同单位
