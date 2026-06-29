# driver-model.json Schema (v4.1)

Agent 产出此 JSON 文件，与 driver-map.md 同目录同日期前缀。`build-logic-model.py` (v4.1) 从 JSON 生成公式联动 Excel。

## 完整 Schema

```json
{
  "meta": {
    "ticker": "300285.SZ", "company": "Sinocera", "market": "cn",
    "base_fy": 2025, "proj_years": 5, "sotp_offset": 2,
    "p&l_depth": "ni", "net_debt": 0, "nci_rate": 0,
    "mcap_m": null, "currency": "CNY",
    "basis": "gaap", "basis_note": "excl. SBC $A, restructuring $B"
  },
  "actuals": {
    "fy-2": {"rev": 3859, "gp": 1492, "opex": 737, "da": 120, "op": 755, "tax": 93, "ni": 605},
    "fy-1": {"rev": 4047, "gp": 1606, "opex": 831, "da": 130, "op": 775, "tax": 93, "ni": 610},
    "fy0":   {"rev": 4583, "gp": 1722, "opex": 951, "da": 150, "op": 771, "tax": 90, "ni": 610}
  },
  "segments": [{
    "name": "Electronic Materials",
    "name_cn": "（电子材料）",
    "fy-2": {"rev": 3200, "cost": 2100, "gp": 1100, "gm": 0.344, "op": 500},
    "fy-1": {"rev": 3500, "cost": 2250, "gp": 1250, "gm": 0.357, "op": 580},
    "fy0":  {"rev": 693, "cost": 454, "gp": 239, "gm": 0.345, "op": 105},
    "logic_lines": [
      {"name": "R1 MLCC Powder", "split": 0.65},
      {"name": "G4 CCL Filler", "split": 0.04}
    ],
    "residual": {"gm": 0.25}
  }],
  "logic_lines": [{
    "name": "R1 MLCC Powder",
    "module": "vol_asp",
    "unit_scale": 100, "asp_unit": "万/t",
    "volume": {"fy0": 7000, "proj": [8000, 10500, ...], "unit": "t"},
    "capacity": {
      "fy0": 10000, "proj": [10000, 13000, ...], "unit": "t",
      "ramp_notes": {"fy26": "P1 2,000t 爬坡50%", ...}
    },
    "tiers": [
      {"name": "AI", "share_fy0": 0.05, "share_proj": [0.156, 0.333, ...],
       "asp_bull": [33, ...], "asp_base": [30, ...], "asp_bear": [27, ...],
       "asp_fy0": 26},
      {"name": "Consumer", "asp": [5.5, 6.5, 7.5, 8.5, 9], "asp_fy0": 4.9}
    ],
    "gm": {"fy-2": 0.35, "fy-1": 0.37, "fy0": 0.40, "proj": [0.45, 0.50, ...]},
    "sotp": {"method": "pe", "multiple": 30},
    "history": {
      "fy-2": {"volume": 6000, "rev": 2500, "AI_asp": 24},
      "fy-1": {"volume": 6500, "rev": 2800, "AI_asp": 25}
    },
    "opex_rate": [0.22, 0.21, 0.20, 0.20, 0.19, 0.19, 0.18, 0.18]
  }],
  "global": {"opex_rate": [0.22, ...], "tax_rate": 0.15}
}
```

## 字段说明

### meta

| 字段 | 类型 | 说明 |
|---|---|---|
| `ticker` | str | yfinance 格式。A股: `300285.SZ`/`600183.SS` |
| `yf_ticker` | str | 可选。yfinance 实际 ticker（与 `ticker` 不同时用） |
| `market` | str | cn/us/jp/kr/tw — 决定 Price 格式和单位 |
| `unit` | str | 可选 `M`/`B`。不填则按 market 自动推断 |
| `currency` | str | CNY/USD/JPY/KRW 等，C1 标签用 |
| `mcap_m` | int | 可选。yfinance 失败时的 fallback MCap (M) |
| `base_fy` | int | FY0（最新完整财年） |
| `proj_years` | int | 投影年数，默认 5 |
| `sotp_offset` | int | SOTP 年距 FY0 的 offset，默认 2 |
| `p&l_depth` | str | gp / ebitda / ebit / ni。用于 validate_json，**运行时由 max_seg_depth 接管** |
| `net_debt` | int | EV 估值用，默认 0 |
| `nci_rate` | float | 少数股东占比，默认 0 |
| `basis` | str | 可选 `gaap`/`non-gaap`/`adjusted`。标记会计口径。不影响渲染 |
| `basis_note` | str | 可选。basis ≠ gaap 时说明调整内容 (excl. SBC $A, ...) |

### actuals

| 字段 | fy-2/fy-1 | fy0 | 说明 |
|---|---|---|---|
| `rev, gp, op, tax, ni` | 必填 | 必填 | 单位 M |
| `opex` | 不填→gp−op推导 | 必填 | 单位 M |
| `da` | 默认 0 | ebitda深度时必填 | 单位 M |

### segments

| 字段 | 说明 |
|---|---|
| `name` | 披露原文名 |
| `name_cn` | 可选。中文翻译，独占一行（B列 italic gray） |
| `fy-2`, `fy-1` | 可选。segment 历史数据: `{rev, cost, gp, gm, op?, ni?}` |
| `fy0` | 必填: `{rev, cost, gp, gm}`。`op`/`ni` 选填——披露到什么填什么 |
| `logic_lines` | 数组。每个 `{name, split}` |
| `residual` | 选填: `{gm}`。split 之和未满 1.0 时的尾部 |
| `max_seg_depth` | 自动检测：扫描所有 seg.fy0，有 op→`op`，有 ni→`ni` |

### logic_lines

| 字段 | 说明 |
|---|---|
| `module` | yoy / vol_asp / capacity_util / backlog_burn |
| `volume` | vol_asp: `{fy0, proj, unit}` |
| `capacity` | vol_asp 可选: `{fy0, proj, unit, ramp_notes}` |
| `unit_scale` | vol_asp: ASP×Vol 到 Rev 的除数。cn 默认 100（万→M）。B mode（jp/kr）需要匹配显示单位 |
| `asp_unit` | vol_asp: ASP 行标签后缀 |
| `tiers` | vol_asp: 数组，最后一项为 residual (无 share%) |
| `yoy` | yoy: `{bull, base, bear}` 各 proj_years 值 |
| `gm` | `{fy-2?, fy-1?, fy0, proj: [proj_years値]}`。非 1:1 线必须填 history GM，否则 GP=0→OP 为负 |
| `sotp` | `{method, multiple}`。旧 `sotp_pe:40` 兼容 |
| `history` | 可选。`{fy-2/fy-1: {volume?, rev?, <tier>_asp?...}}` |
| `opex_rate` | 可选数组。per-line opex 覆盖，不填 fallback 到 global。长度 = 3 + proj_years |
| `tax_rate` | 可选。per-line tax 覆盖（数组则长度 = 3 + proj_years） |

### ASP 数组规则

- **BBE tier** (`asp_bull/base/bear`): 各 `1 + proj_years` 值（含 FY0）
  - `bull[0] = base[0] = bear[0] = asp_fy0`（FY0 基年固定）
- **Simple ASP**: `asp` 数组 ≥ proj_years。有 `asp_fy0` 时 `asp[0..]` = 投影年；无 `asp_fy0` 时 `asp[0]` = FY0
- **禁止**: `asp_fy0` 和 `asp[0]` 相同——会导致 FY+1 锁在 FY0

### global

| 字段 | 说明 |
|---|---|
| `opex_rate` | 数组，长度 = 3(实际年) + proj_years |
| `tax_rate` | 单一值或数组 |

### 跨市场单位

| 市场 | unit_scale 默认 | B mode (10亿显示) | NUM 格式 |
|---|---|---|---|
| cn | 100（万→M） | 否 | #,##0.0 |
| jp/kr | 1 | 是 | #,##0.0 |
| us/hk/eu | — | M mode: #,##0.0 |

### 利润深度——自动检测

不再依赖 `p&l_depth` 字段控制 Section 2 per-line 深度。脚本扫描所有 segment 的 `fy0` 字段：
- 有 `op` → per-line 渲染 Opex→OP→Check OP
- 有 `ni` → per-line 渲染 Tax→NI→Check NI

Section 3 始终渲染全 P&L 链（GP→OP→EBITDA→EBIT→NI）。

### Check 行规则

| Check | 触发条件 | 公式 |
|---|---|---|
| Check Rev | 模块为 vol_asp/backlog_burn/capacity_util | `=S1 anchor Rev` |
| Check GP | line 非 1:1（GM 为 I()） | `=seg_gp × split%` |
| Check OP | seg 有 op | `=seg_op × split%` |
| Check NI | seg 有 ni | `=seg_ni × split%` |
