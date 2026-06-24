# Revenue Modules — Contract & Reference

## yoy (default, built-in)

最简。Rev FY25A=S1 ref, FY26+=Prior×(1+YoY Active)。YoY Active 通过 IF(B1) 读隐藏 Bull/Base/Bear 行。

```json
{"name": "G1", "module": "yoy",
 "yoy": {"bull":[0.20,...], "base":[0.15,...], "bear":[0.10,...]},
 "gm": {...}, "sotp": {...}}
```

## vol_asp

Volume × Share% × ASP。Rev = Σ(Vol×Shr×ASP)/100。Tiers 分 BBE ASP 和 simple ASP。有 `capacity` 字段时渲染 Nameplate Capacity + Utilization 行。

```json
{"name": "R1", "module": "vol_asp",
 "volume": {"fy0":7000, "proj":[8000,...], "unit":"t"},
 "capacity": {"fy0":10000, "proj":[10000,...], "unit":"t",
              "ramp_notes": {"fy26": "P1 爬坡50%", ...}},
 "tiers": [
   {"name": "AI", "share_fy0":0.05, "share_proj":[...],
    "asp_bull":[26,...], "asp_base":[26,...], "asp_bear":[26,...]},
   {"name": "Consumer", "asp":[4.9, 5.5, 6.5, 7.5, 8.5, 9]}
 ],
 "gm": {...}, "sotp": {...}}
```

**BBE 缓存**: 3 个隐藏行 `Bull/Base/Bear Rev @ SOTP`，Scenario Summary 读取。无 BBE tier 的 line 返回单值。

## capacity_util

Capacity × Util% × ASP。Rev = Capa × Util% × ASP。Capacity 是输入，Util% 是模型假设。

```json
{"name": "钻针", "module": "capacity_util",
 "capacity": {"fy0":8, "proj":[...], "unit":"亿只/年"},
 "util_rate": {"fy0":0.75, "proj":[...]},
 "asp": {"fy0":5.0, "proj":[...], "unit":"元/支"},
 "gm": {...}, "sotp": {...}}
```

## backlog_burn

Beg Backlog × Burn Rate，跨列链式。Rev = Beg × Burn。End = Beg × (1 + OrderRate − Burn)。Beg_{t+1} = End_t（Excel 公式跨列链式引用）。

```json
{"name": "设备", "module": "backlog_burn",
 "beg_backlog": {"fy0":2500, "unit":"M"},
 "order_rate": {"fy0":0.45, "proj":[...]},
 "burn_rate": {"fy0":0.35, "proj":[...]},
 "gm": {...}, "sotp": {...}}
```

## Module Contract

```python
def render(ws, R, ll, anchor_info, ctx) -> dict:
    """
    ctx keys: C, I, nf, bf, itf, NUM, DEC, PCT, actfill, DS, FY0, LC, SC, proj_n, bfyr
    
    Returns: {
        'next_R': int,
        'rev_r': int, 'gm_r': None, 'gp_r': None,  # gm_r/gp_r filled by caller
        'module': str,
        # Module-specific:
        'vol_r': int,     # vol_asp: Volume row
        'cap_r': int,     # vol_asp: Nameplate Capacity row (0 if none)
        'yb': int,        # vol_asp BBE: Bull Rev @ SOTP cache row
        'ybs': int, 'ybe': int,
        'yb': int,        # yoy: Bull YoY hidden row
        'ybs': int, 'ybe': int, 'ya': int,
        'beg_r': int,     # backlog_burn: Beg Backlog row
        'end_r': int, 'order_r': int, 'burn_r': int,
    }
    """
```

注册: `MODULES` dict + `_load_module()`。新 module 放 `modules/<name>.py`。
