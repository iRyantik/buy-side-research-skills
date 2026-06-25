# driver-model.json Schema (v4)

Agent 产出此 JSON 文件，与 driver-map.md 同目录同日期前缀。`build-logic-model.py` (v4) 从 JSON 生成公式联动 Excel。

## 完整 Schema

```json
{
  "meta": {
    "ticker": "300285.SZ", "company": "Sinocera", "market": "cn",
    "base_fy": 2025, "proj_years": 5, "sotp_offset": 2,
    "p&l_depth": "ni", "net_debt": 0, "nci_rate": 0,
    "mcap_m": null, "currency": "CNY"
  },
  "actuals": {
    "fy-2": {"rev": 3859, "gp": 1492, "opex": 737, "da": 120, "op": 755, "tax": 93, "ni": 605},
    "fy-1": {"rev": 4047, "gp": 1606, "opex": 831, "da": 130, "op": 775, "tax": 93, "ni": 610},
    "fy0":   {"rev": 4583, "gp": 1722, "opex": 951, "da": 150, "op": 771, "tax": 90, "ni": 610}
  },
  "segments": [{
    "name": "Electronic Materials",
    "fy0": {"rev": 693, "cost": 454, "gp": 239, "gm": 0.345},
    "logic_lines": [
      {"name": "R1 MLCC Powder", "split": 0.65},
      {"name": "G4 CCL Filler", "split": 0.04}
    ],
    "residual": {"gm": 0.25}
  }],
  "logic_lines": [{
    "name": "R1 MLCC Powder",
    "module": "vol_asp",
    "volume": {"fy0": 7000, "proj": [8000, 10500, ...], "unit": "t"},
    "capacity": {
      "fy0": 10000, "proj": [10000, 13000, ...], "unit": "t",
      "ramp_notes": {"fy26": "P1 2,000t 爬坡50%", ...}
    },
    "tiers": [
      {"name": "AI", "share_fy0": 0.05, "share_proj": [0.156, 0.333, ...],
       "asp_bull": [26, 33, ...], "asp_base": [26, 30, ...], "asp_bear": [26, 27, ...]},
      {"name": "Consumer", "asp": [4.9, 5.5, 6.5, 7.5, 8.5, 9]}
    ],
    "gm": {"fy0": 0.40, "proj": [0.45, 0.50, ...]},
    "sotp": {"method": "pe", "multiple": 30}
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
| `base_fy` | int | FY0（最新完整财年）|
| `proj_years` | int | 投影年数，默认 5 |
| `sotp_offset` | int | SOTP 年距 FY0 的 offset，默认 2 |
| `p&l_depth` | str | gp / ebitda / ebit / ni |
| `net_debt` | int | EV 估值用，默认 0 |
| `nci_rate` | float | 少数股东占比，默认 0 |
| `mcap_m` | int | yfinance 失败时的 fallback MCap (M)，可选 |
| `currency` | str | CNY/USD/JPY/KRW 等，C1 标签用 |

### actuals

| 字段 | fy-2/fy-1 | fy0 | 说明 |
|---|---|---|---|
| `rev, gp, op, tax, ni` | 必填 | 必填 | 单位 M |
| `opex` | 不填→gp−op推导 | 必填 | 单位 M |
| `da` | 默认 0 | ebitda深度时必填 | 单位 M |

### logic_lines

| 字段 | 说明 |
|---|---|
| `module` | yoy（默认）/ vol_asp / capacity_util / backlog_burn |
| `volume` | vol_asp: `{fy0, proj, unit}` |
| `capacity` | vol_asp 可选: `{fy0, proj, unit, ramp_notes}` |
| `unit_scale` | vol_asp: ASP×Vol 到 Rev 的除数。cn 默认 100（万→M），jp/kr 设为 1 |
| `asp_unit` | vol_asp: ASP 行标签后缀。cn 默认 `万/t`，jp 用 `千円/t` |
| `COLS` | 自动计算 = 3 + proj_years，无需手动填 |
| `tiers` | vol_asp: 数组，最后一项为 residual (无 share%) |
| `tiers[].new_cap_share` | 可选。增量产能分配比例（0-1），设置后 Share% 变为公式推导 |
| `tiers[].fy0_volume` | new_cap_share 模式下的 FY25 基年出货量（吨） |
| `tiers[].asp_mode` | 可选 `"multiplier"`。ASP 投影用乘数（上年×乘数）替代绝对值 |
| `beg_backlog` + `order_rate` + `burn_rate` | backlog_burn |
| `yoy` | yoy 默认: `{bull, base, bear}` 各 5 值 |
| `gm` | `{fy0, proj: [5值]}` |
| `sotp` | `{method, multiple}`。旧 `sotp_pe:40` 兼容 |

### ASP 数组规则

- **BBE tier** (`asp_bull/base/bear`): 各 6 值 [FY25, FY26, FY27, FY28, FY29, FY30]
  - `bull[0] = base[0] = bear[0]`（FY25 基年固定，不随情景变）
- **Simple ASP**: `asp` 数组 ≥ 1+proj_years。无 `asp_fy0` 时 `asp[0]=FY25`
- **禁止**: `asp_fy0` 和 `asp[0]` 相同——会导致 FY26 锁在 FY25 值

### global

| 字段 | 说明 |
|---|---|
| `opex_rate` | 数组，长度 = 3(实际年) + proj_years |
| `tax_rate` | 单一值或数组 |
