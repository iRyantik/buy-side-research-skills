# Revenue Modules — Contract & Reference

## yoy (modules/yoy.py)

独立模块。Rev FY0 = S1 ref, FY+1 = Prior×(1+YoY Active)。YoY Active 通过 IF(B1) 读隐藏 Bull/Base/Bear 行。

```json
{"name": "G1", "module": "yoy",
 "yoy": {"base": {"FY2026E": {"annual": 0.15}, "FY2027E": {"annual": 0.12}},
         "bull": {"FY2026E": {"annual": 0.20}},
         "bear": {"FY2026E": {"annual": 0.10}}},
 "base_rate": {"FY2026E": {"annual": 0.34}, "FY2027E": {"annual": 0.35}},
 "sotp": {"method": "ev_ebitda", "multiple": 10}}
```

YoY rates are FY-keyed inside each scenario. Build reads via `ctx['_yoy_li'](scenario, FY)`.
base_rate is FY-keyed, read via `ctx['_br_li'](FY)`.

## vol_asp

Volume × Share% × ASP。Rev = Σ(Vol×Shr×ASP)/unit_scale。Tiers 分 BBE ASP 和 simple ASP。有 `capacity` 字段时渲染 Nameplate Capacity + Utilization 行。

- `unit_scale`: ASP×Vol → Rev 的除数。默认 100（M→M）。日韩等市场 B mode 时设为 1000。
- `asp_unit`: ASP 行 C 列标签后缀。默认 `M¥/unit`。
- History volume/ASP: 从各 FY 的 `volume` 和 `tiers[].asp` 直接读取（FY-inside），不再需要单独的 `history` 结构。
- Build reads via `ctx['_vol_li'](FY)`, `ctx['_asp_li'](FY, ti, sc)`, `ctx['_share_li'](FY, ti)`.

```json
{"name": "R1", "module": "vol_asp",
 "unit_scale": 100, "asp_unit": "M¥/unit",
 "volume": {"FY2025": {"annual": 7000}, "FY2026E": {"annual": 8000}, "unit": "t"},
 "capacity": {"FY2025": {"annual": 10000}, "FY2026E": {"annual": 10000}, "unit": "t",
              "ramp_notes": {"FY2026E": "P1 爬坡50%"}},
 "tiers": [
   {"name": "AI", "share": {"FY2025": {"annual": 0.05}, "FY2026E": {"annual": 0.06}},
    "asp_bull": {"FY2025": {"annual": 26}, "FY2026E": {"annual": 28}},
    "asp_base": {"FY2025": {"annual": 26}, "FY2026E": {"annual": 27}},
    "asp_bear": {"FY2025": {"annual": 26}, "FY2026E": {"annual": 25}}},
   {"name": "Consumer", "asp": {"FY2025": {"annual": 4.9}, "FY2026E": {"annual": 5.5}}}
 ],
 "base_rate": {"FY2025": {"annual": 0.40}, "FY2026E": {"annual": 0.45}},
 "sotp": {"method": "pe", "multiple": 20}}
```

## ebitda (modules/ebitda.py)

EBITDA margin assumption → EBITDA = Rev × margin。Rev 从 ctx 获取。

```json
{"name": "E1", "module": "ebitda",
 "base_rate": {"FY2025": {"annual": 0.30}, "FY2026E": {"annual": 0.32}},
 "sotp": {"method": "ev_ebitda", "multiple": 12}}
```

## backlog_burn (modules/backlog_burn.py)

Beginning Backlog × Burn Rate。Order Rate + Burn Rate 支持 BBE 三场景。

```json
{"name": "B1", "module": "backlog_burn",
 "beg_backlog": {"FY2025": {"annual": 5000}, "unit": "units"},
 "order_rate": {"FY2025": {"annual": 0.15}, "FY2026E": {"annual": 0.12}},
 "burn_rate": {"FY2025": {"annual": 0.20}, "FY2026E": {"annual": 0.18}},
 "sotp": {"method": "pe", "multiple": 15}}
```

BBE 场景下 `order_rate`/`burn_rate` 包含 `bull`/`base`/`bear` 子键，每个 FY-keyed。
Build reads via `ctx['_bb_li'](field, FY, scenario)`.

## capacity_util (modules/capacity_util.py)

Capacity × Utilization% × ASP。Volume = Capacity × Utilization（隐含，公式推导）。

```json
{"name": "C1", "module": "capacity_util",
 "capacity": {"FY2025": {"annual": 12000}, "FY2026E": {"annual": 15000}, "unit": "units"},
 "utilization": {"FY2025": {"annual": 0.85}, "FY2026E": {"annual": 0.90}},
 "unit_scale": 100,
 "tiers": [{"name": "Main", "asp": {"FY2025": {"annual": 50}, "FY2026E": {"annual": 55}}}],
 "sotp": {"method": "pe", "multiple": 18}}
```

Build reads via `ctx['_cap_li'](FY)`, `ctx['_util_li'](FY)`, `ctx['_asp_li'](FY, ti)`.
