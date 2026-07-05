# research-model.json Schema Reference

## 1. 顶层结构

```
research-model.json
├── schema_version: "1.0"
├── generated_at: "2026-07-04T00:00:00Z"
├── identity        — 公司识别
├── meta            — 模型配置
├── actuals         — 历史披露（纯事实）
│   ├── gaap.is     — 利润表
│   ├── gaap.segments — 段营收
│   ├── non_gaap.is — non-GAAP 利润
│   ├── non_gaap.adj — 调整明细
│   └── non_gaap.segments — 段 non-GAAP
├── assumptions     — 全部假设+投影驱动
│   ├── lines[]     — 业务线
│   ├── global      — 全局参数
│   └── segment_residuals — 段未建模余额
├── market          — 市场数据
└── kpi             — 弹性指标
```

### 统一访问路径

```
{source}.{field}.{FY}.{period}

actuals.gaap.is.rev.FY2025.annual = 8252
actuals.gaap.is.rev.FY2025.Q1 = 1942
assumptions.lines[0].base_rate.FY2026E.annual = 0.34
assumptions.global.tax_rate.FY2023.annual = 0.22
```

---

## 2. identity

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 公司全名 |
| `ticker` | str | 股票代码，如 "HWM.US" |
| `market` | str | us/cn/hk/jp/kr/tw/eu |
| `currency` | str | USD/CNY/JPY/KRW 等 |
| `accounting_standard` | str | us_gaap/jp_gaap/cn_gaap/ifrs |

---

## 3. meta

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `ticker` | str | ✅ | |
| `company` | str | ✅ | |
| `market` | str | ✅ | |
| `base_fy` | int | ✅ | FY0 年份 |
| `proj_years` | int | ✅ | 投影年数，默认 5 |
| `p&l_depth` | str | ✅ | gp/op/ebitda |
| `basis` | str | | gaap/non-gaap |
| `currency` | str | ✅ | |
| `display_unit` | str | | 显示单位：M (百万)/B (十亿)，默认 M |
| `display_decimals` | int | | 显示小数位，默认 1 |
| `price` | float | | 股价 |
| `shares_m` | float | | 股本（百万）|
| `mcap_m` | float | | 市值（百万）|
| `net_debt` | int | | 净债务 |
| `sotp_offset` | int | | SOTP 年份 offset |
| `q_actual_count` | int | | 实际 Q 数 |
| `q_proj_count` | int | | 投影 Q 数 |
| `q_start_yr` | int | | Q 起始年份 |
| `q_start_q` | int | | Q 起始季度号 (1-4) |

---

## 4. actuals

### 4.1 gaap.is

```
gaap.is.{field}.{FY}.{period} = value

字段: rev, gp, oi, ni, tax, da, cogs, sga, rnd, pretax
FY: FY2023, FY2024, FY2025（仅历史，不存投影）
period: annual, Q1, Q2, Q3, Q4
```

示例:
```json
"gaap": {
  "is": {
    "rev": { "FY2025": { "annual": 8252, "Q1": 1942 } },
    "gp": { "FY2025": { "annual": 2820 } },
    "oi": { "FY2025": { "annual": 2046 } }
  }
}
```

### 4.2 gaap.segments

数组。每项: `name` + `rev.{FY}.{period}`。OP/GP depth 加 `gp`/`oi`。

```json
"segments": [
  {
    "name": "Engine Products Segment",
    "name_cn": "（发动机产品）",
    "rev": { "FY2025": { "annual": 4320, "Q1": 1017 } },
    "gp": { "FY2025": { "annual": 3420 } }
  }
]
```

### 4.3 non_gaap.is

```
字段: ebitda, oi, ni
```

### 4.4 non_gaap.adj

```
字段: sbc, restructuring, amort_intangible, fx, other
全部 FY-keyed
```

### 4.5 non_gaap.segments

数组。每项: `name` + `ebitda.{FY}.{period}`。

---

## 5. assumptions

### 5.1 lines[] — 通用字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | str | ✅ | 唯一标识 |
| `module` | str | ✅ | yoy/vol_asp/backlog_burn/capacity_util |
| `segment` | str | ✅ | **GAAP 精确段名**，Non-core 填 "" |
| `one_to_one` | bool | ✅ | line = segment 且 split=1.0 |
| `is_segment_core` | bool | ✅ | Non-core 填 false |
| `split` | float | 1:1→可选 | 历史 line_rev = seg_rev × split |
| `base_rate` | obj | 见下方 | { FY{xxx}: { annual: rate } } |
| `sotp` | obj | ✅ | { method, multiple } |
| `opex_rate` | obj | 可选 | 线级 Opex/Rev（FY-keyed） |

### 5.2 module: yoy

```json
{
  "name": "L1 Engine Products",
  "module": "yoy",
  "one_to_one": true,
  "split": 1.0,
  "base_rate": { "FY2026E": { "annual": 0.34 } },
  "yoy": {
    "bull": { "FY2026E": { "annual": 0.12 } },
    "base": { "FY2026E": { "annual": 0.10 } },
    "bear": { "FY2026E": { "annual": 0.05 } }
  }
}
```

| 字段 | 历史 | 投影 | 说明 |
|---|---|---|---|
| `base_rate` | 1:1→不存, non-1:1→必填 | 必填 | depth 决定含义 |
| `yoy` | ❌ | 必填 | bull/base/bear 三场景 |

### 5.3 module: vol_asp

```json
{
  "name": "tap-PD",
  "module": "vol_asp",
  "one_to_one": false,
  "split": 0.33,
  "unit_scale": 1000,
  "base_rate": { "FY2026": { "annual": 0.52 }, "FY2027E": { "annual": 0.53 } },
  "volume": { "FY2026": { "annual": 70, "Q4": 20 }, "FY2027E": { "annual": 78 } },
  "tiers": [
    {
      "name": "tap-PD",
      "asp": { "FY2026": { "annual": 30, "Q4": 30 }, "FY2027E": { "annual": 32 } }
    }
  ]
}
```

| 字段 | 历史 | 投影 | 说明 |
|---|---|---|---|
| `volume` | 必填 | 必填 | 全部 FY |
| `tiers[].asp` | 必填 | 必填 | 全部 FY |
| `tiers[].share` | 必填（非末 tier）| 必填 | 份额 % |
| `unit_scale` | 单值 | | Vol×ASP→Rev 除数 |
| `base_rate` | 必填（通常 non-1:1）| 必填 | |

### 5.4 module: backlog_burn

```json
{
  "module": "backlog_burn",
  "beg_backlog": { "FY2026": { "annual": 2500 } },
  "order_rate": { "FY2026": { "annual": 0.45 }, "FY2027E": { "annual": 0.40 } },
  "burn_rate": { "FY2026": { "annual": 0.35 }, "FY2027E": { "annual": 0.35 } }
}
```

### 5.5 module: capacity_util

```json
{
  "module": "capacity_util",
  "capacity": { "FY2026": { "annual": 10000 }, "FY2027E": { "annual": 13000 } },
  "utilization": { "FY2026": { "annual": 0.85 }, "FY2027E": { "annual": 0.90 } },
  "tiers": [{
    "name": "Product",
    "asp": { "FY2026": { "annual": 100 } }
  }]
}
```

### 5.6 global

```json
"global": {
  "tax_rate": { "FY2023": { "annual": 0.22 }, ..., "FY2030E": { "annual": 0.22 } },
  "opex_rev": { "FY2023": { "annual": 0.181 }, ... },
  "nm": { "FY2023": { "annual": 0.115 }, ... }
}
```

全部 FY 必填。EBITDA depth 时 tax_rate/opex_rev 被 bridge 覆盖但必须存在。

### 5.7 segment_residuals

```json
"segment_residuals": {
  "その他": { "rev": 0, "base_rate": 0.36 }
}
```

段内 split 总和 < 1.0 时的未建模余额。§2→§1 Fill: 段投影 = Σ 线 + residual。

---

## 6. market

```json
"market": {
  "price": 270.41, "mcap_m": 108193, "shares_m": 400.1,
  "pe_ttm": 62.9, "pe_fwd": 44.9, "pb": 19.6,
  "ps": 12.5, "ev_revenue": 13.4, "ev_ebitda": 43.2,
  "beta": 1.19, "hi52": 290.63, "lo52": 169.45,
  "target_price_mean": 305.98
}
```

---

## 7. kpi

弹性 key-value。公司自定义指标。

---

## 8. 四维约束表

`assumptions 字段需求 = f(1:1/non-1:1, module, 历史/投影, depth)`

### 8.1 1:1 vs non-1:1

| 字段 | 1:1 历史 | 1:1 投影 | non-1:1 历史 | non-1:1 投影 |
|---|---|---|---|---|
| `base_rate` | ❌ | ✅ | ✅ | ✅ |
| `yoy` | ❌ | ✅ | ❌ | ✅ |
| `volume` | ❌ | ❌ | ✅ | ✅ |
| `split` | 1.0 | — | 必填 | — |

### 8.2 depth → base_rate 含义

| depth | base_rate = | build 公式 |
|---|---|---|
| gp | Gross Margin | Rev × base_rate = GP |
| op | Gross Margin | Rev × base_rate = GP |
| ebitda | EBITDA Margin | Rev × base_rate = Segment EBITDA |

### 8.3 global 生效矩阵

| global | gp | op | ebitda |
|---|---|---|---|
| `tax_rate` | ✅ | ✅ | ❌(bridge) |
| `opex_rev` | ✅ | 可选 | ❌(bridge) |
| `nm` | 可选 | 可选 | ❌(bridge) |

---

## 9. 设计规则附录

### 9.1 数据流向

```
历史: actuals → §1 Seg → §1 Line Split(×split) → §2 Line Rev(=引用)
投影: assumptions → §2 yoy/vol_asp → §2 Line Rev → §2→§1 Fill → §1 Seg(=Σ线)
```

### 9.2 Hidden Bridge (EBITDA depth)

gap_gp = (EBITDA_fy0 − GP_fy0) / Rev_fy0  
gap_oi = (EBITDA_fy0 − OI_fy0) / Rev_fy0  
gap_ni = (OI_fy0 − NI_fy0) / Rev_fy0

均为 Excel 公式引用 FY0 actuals 单元格，FY0 单年 anchor。

### 9.3 (OI-NI)/Rev

EBITDA depth: 引用 Hidden Bridge gap_ni 公式。  
其他 depth: 锚定 FY0 列值。

### 9.4 build 零推理原则

JSON 必须完整。缺项 = build 报错，不设默认值。

### 9.5 Non-core Corporate

`is_segment_core: false`, Rev=0, EBITDA = company − Σ segment（gap 自动吸收）。

### 9.6 模型更新

季度财报出 → Agent patch `actuals.gaap.is.{field}.{FY}.{period}` → 
`validate-q-fy.py` → `derive-base-rate.py` → build → checks。
