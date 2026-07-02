# Revenue Modules — Contract & Reference

## yoy (modules/yoy.py)

独立模块。Rev FY0 = S1 ref, FY+1 = Prior×(1+YoY Active)。YoY Active 通过 IF(B1) 读隐藏 Bull/Base/Bear 行。

```json
{"name": "G1", "module": "yoy",
 "yoy": {"bull":[0.20,...], "base":[0.15,...], "bear":[0.10,...]},
 "gm": {"fy-2":0.28, "fy-1":0.30, "fy0":0.32, "proj":[0.34,...]},
 "sotp": {...}}
```

## vol_asp

Volume × Share% × ASP。Rev = Σ(Vol×Shr×ASP)/unit_scale。Tiers 分 BBE ASP 和 simple ASP。有 `capacity` 字段时渲染 Nameplate Capacity + Utilization 行。

- `unit_scale`: ASP×Vol → Rev 的除数。cn 默认 100（万→M）。日韩等市场自动 B mode 时设为 1000。
- `asp_unit`: ASP 行 C 列标签后缀。默认 `万/t`。
- History: `history.fy-2`/`history.fy-1` 存 `{volume, rev, <tier>_asp}`。所有 history 值用 I() 黄底。

```json
{"name": "R1", "module": "vol_asp",
 "unit_scale": 100, "asp_unit": "万/t",
 "volume": {"fy0":7000, "proj":[8000,...], "unit":"t"},
 "capacity": {"fy0":10000, "proj":[10000,...], "unit":"t",
              "ramp_notes": {"fy26": "P1 爬坡50%", ...}},
 "tiers": [
   {"name": "AI", "share_fy0":0.05, "share_proj":[...],
    "asp_bull":[26,...], "asp_base":[26,...], "asp_bear":[26,...],
    "asp_fy0": 26},
   {"name": "Consumer", "asp":[5.5, 6.5, 7.5, 8.5, 9], "asp_fy0":4.9}
 ],
 "gm": {"fy-2":0.35, "fy-1":0.37, "fy0":0.40, "proj":[0.45,0.50,...]},
 "sotp": {...},
 "history": {
   "fy-2": {"volume":6000, "rev":2500, "AI_asp":24},
   "fy-1": {"volume":6500, "rev":2800, "AI_asp":25}
 }}
```

**BBE 缓存**: 3 个隐藏行 `Bull/Base/Bear Rev @ SOTP`，Scenario Summary 读取。无 BBE tier 的 line 返回单值。

## backlog_burn

Beg Backlog × Burn Rate，跨列链式。Rev = Beg × Burn。End = Beg × (1 + OrderRate − Burn)。Beg_{t+1} = End_t（Excel 公式跨列链式引用）。

```json
{"name": "设备", "module": "backlog_burn",
 "beg_backlog": {"fy0":2500, "unit":"M"},
 "order_rate": {"fy0":0.45, "proj":[...]},
 "burn_rate": {"fy0":0.35, "proj":[...]},
 "gm": {...}, "sotp": {...}}
```

## ebitda (modules/ebitda.py)

EBITDA margin-based module. Used when `p&l_depth=ebitda` (US non-GAAP segments). Per-line renders:

- **EBITDA margin** (I): analyst assumption, blue font yellow fill
- **EBITDA** (F): = Revenue x EBITDA margin
- **EBITDA YoY** (F): = (EBITDA_t / EBITDA_{t-1}) - 1

No Cost, GM, Opex, or OI rows rendered in Section 1 / Section 2 for EBITDA depth lines. These are derived at the P&L level via gap formulas from the Hidden Bridge.

```json
{"name": "S1", "module": "ebitda",
 "ebitda_margin": {"fy-2": 0.32, "fy-1": 0.34, "fy0": 0.36, "proj": [0.38, 0.40, ...]},
 "sotp": {...}}
```

History values (`fy-2`/`fy-1`/`fy0`) use I() (assumption cells, not A() actuals). The Hidden Bridge stores FY0 actual EBITDA; Check rows compare formula EBITDA vs bridge actuals.

## Module Contract

```python
def render(ws, R, ll, anchor_info, ctx) -> dict:
    """
    ctx keys: C, I, A, CF, HL, nf, bf, itf, NUM, DEC, PCT, INT, DS, FY0, LC, SC, proj_n, bfyr
    
    Returns: {
        'next_R': int,
        'rev_r': int, 'gm_r': None, 'gp_r': None,  # gm_r/gp_r filled by caller
        'op_r': int,    # filled by caller if per-line profit chain renders
        'module': str,
        # Module-specific:
        'vol_r': int,     # vol_asp: Volume row
        'cap_r': int,     # vol_asp: Nameplate Capacity row (0 if none)
        'asp_rows': list, # vol_asp: ASP row numbers
        'asp_h_r': int,   # vol_asp: first ASP row (for Revenue history formula)
        'share_rows': list,
        'yb': int,        # BBE: Bull cache row
        'ybs': int, 'ybe': int,
        'ya': int,        # yoy: YoY Active row
        'beg_r': int,     # backlog_burn: Beg Backlog row
        'end_r': int, 'order_r': int, 'burn_r': int,
    }
    """
```

### Cell Helpers（通过 ctx 传入）

| Helper | 样式 | 用途 |
|---|---|---|
| `C()` | black Calibri 11, no fill | 通用值/公式 |
| `I()` | blue font, yellow fill | 假设（分析师可调） |
| `A()` | gray fill | Actuals（财报披露） |
| `CF()` | black font, no fill, guaranteed number_format | **公式专用**——强制 fmt |
| `HL()` | white bold font, deep red fill | 重点 driver 标签 |
| `BOLD()` | black bold font | 关键指标加粗 |

### 格式常量

| 常量 | 值 | 用途 |
|---|---|---|
| `NUM` | #,##0.0 | Rev/GP/OP/NI/Cost/Opex 等 |
| `DEC` | #,##0.00 | ASP/价格 |
| `INT` | #,##0 | Volume/Capacity/Shares |
| `PCT` | 0.0% | GM/YoY/Margins/Rates |

注册: `MODULES` dict + `_load_module()`。新 module 放 `modules/<name>.py`。
