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
| `p&l_depth` | str | `gp` / `op` / `ebitda`。控制 P&L 披露深度 + F/A 规则 + Check 行。segment 无对应数据时自动降级 |
| `net_debt` | int | EV 估值用，默认 0 |
| `nci_rate` | float | 少数股东占比，默认 0 |
| `basis` | str | 可选 `gaap`/`non-gaap`/`adjusted`。标记会计口径。不影响渲染 |
| `basis_note` | str | 可选。basis ≠ gaap 时说明调整内容 (excl. SBC $A, ...) |

### actuals

| 字段 | 说明 |
|---|---|
| `rev` | 必填（全 depth）。单位 M |
| `gp` | gp/op depth 必填；**ebitda depth 必填**（GAAP GP，用于 gap_gp 计算） |
| `op` | 必填（全 depth） |
| `ni` | 必填（全 depth） |
| `tax` | 必填（全 depth） |
| `da` | 必填（全 depth）。EBITDA depth 用于 Check D&A |
| `ebitda` | **ebitda depth 必填**（non-GAAP，公司 IR 披露） |

Cost、GM、Opex 永远公式推导，**不在 JSON 中存储**。

### segments

| 字段 | 说明 |
|---|---|
| `name` | 披露原文名 |
| `name_cn` | 可选。中文翻译，独占一行（B列 italic gray） |
| `fy-2`, `fy-1` | 可选。按 depth 填：gp depth→`{rev, gp}`; op depth→`{rev, gp, op}`; ebitda depth→`{rev, ebitda}` |
| `fy0` | 必填。按 depth 填对应字段。op/ni 选填——披露到什么填什么 |
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
| `gm` | `{fy-2?, fy-1?, fy0, proj: [proj_years値]}`。非 1:1 线必须填 history。**EBITDA depth 时语义为 EBITDA margin**，label 自动切换 |
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
| `tax_rate` | GP/OP depth: NM (=NI/Rev) 单一值；EBITDA depth: tax_rate (=Tax/OI) 单一值。**EBITDA depth 时 tax_rate 由 Excel 公式 `=Tax/OI` 从 FY0 actuals 自动计算** |

### 跨市场单位

| 市场 | unit_scale 默认 | B mode (10亿显示) | NUM 格式 |
|---|---|---|---|
| cn | 100（万→M） | 否 | #,##0.0 |
| jp/kr | 1 | 是 | #,##0.0 |
| us/hk/eu | — | M mode: #,##0.0 |

### P&L Depth 架构 (v1.5+)

`p&l_depth` 控制三个维度的行为：

**F/A 规则**：拆了 line 的 item → F/F（全公式）；没拆 line 的 → A/F（历史 actuals，预测公式）；EBITDA depth 特殊——gap 推导的 item 也 F/F。

| P&L Row | GP depth | OP depth | EBITDA depth |
|---|---|---|---|
| Rev | F/F | F/F | F/F |
| GP | F/F | F/F | F/F (gap公式) |
| OI | A/F | F/F | F/F (gap公式) |
| D&A | A/F | A/F | F/F |
| EBITDA | F/F | F/F | F/F |
| Tax | A/F | A/F | F/F |
| NI | A/F | A/F | F/F |

**Hidden Bridge (EBITDA depth)**：P&L 上方 collapsed 区，存 FY-2/FY-1/FY0 actuals + gap 公式。Gap = Excel 公式引用 FY0 actuals（不硬编码）。

**Check 行**：所有 F/F 行有对应 Check。Check 存 actuals（I()），公式 `=(P&L行 − actuals) / ABS(actuals)`。预测年空白。

| Check | GP | OP | EBITDA |
|---|---|---|---|
| Rev | ✓ | ✓ | ✓ |
| GP | ✓ | ✓ | ✓ |
| OI | — | ✓ | ✓ |
| D&A | — | — | ✓ |
| EBITDA | — | — | ✓ |
| Tax | — | — | ✓ |
| NI | — | — | ✓ |

## Quarterly Columns (v4.1+)

### meta Q fields

| 字段 | 类型 | 说明 |
|---|---|---|
| `q_actual_count` | int | 实际 Q 数。yfinance 数据量决定：≥4→4, 2-3→2, 1→1, 0→无Q列 |
| `q_proj_count` | int | 投影 Q 数，默认 4（一个前瞻财年） |
| `q_start_yr` | int | 最早 Q 列所属财年 |
| `q_start_q` | int | 最早 Q 列所属季度号 (1-4) |

### quarters (company-level)

```json
"quarters": {
  "q1": {"rev": 480, "gp": 160, "op": -3, "ni": 213, "opex": 163, "da": 61, "tax": -225}
}
```

### seg.quarters

与 company quarters 同结构。缺失时从 segment annual 按比例估算。

### ll.q_history

Per-line Q actuals。vol_asp: volume + asp。yoy: rev。

```json
"q_history": {
  "q1": {"volume": 0.55, "asp": 145},
  "q2": {"volume": 0.60, "asp": 150}
}
```

### Q 列生成

Q 标签从 `q_start_yr/q_start_q` 自动生成。4Q25A, 1Q26A, 2Q26E... Q 和 Y 之间空 2 列。

### Q→FY Check

完整 4Q FY 自动在 X 列写入 `=Annual − QSum`。跳过 margins/YoY/rates/split%。

### unit scale gate

`validate_json()` 验算 vol_asp: `Vol_FY0 × ASP_FY0 / unit_scale` vs `seg_rev × split%`。gap >10% 报警。
