# Adapter 删除 + Generalization 计划

## 0. 背景

### 0.1 当前架构

```
research-model.json (新格式, FY-inside)
    ↓
_adapt_new_to_old()  ← 我们要删的 140 行
    ↓
build() 读取 old-format cfg → 写 Excel
    ↑
_gaap() / _br() / _gl() ← C1-C3 成果，部分直接读新格式
```

新格式统一路径：`{source}.{field}.{FY}.{period}`

```
actuals.gaap.is.rev.FY2025.annual = 8252
actuals.gaap.is.rev.FY2025.Q1 = 1942
assumptions.lines[0].base_rate.FY2026E.annual = 0.34
assumptions.global.tax_rate.FY2023.annual = 0.22
```

Adpater 做的事：
- `raw['actuals']['gaap']['is']['rev']['FY2025']['annual']` → `cfg['actuals']['fy0']['rev']`
- `raw['assumptions']['lines'][0]['base_rate']` → `cfg['logic_lines'][0]['gm']`
- `raw['assumptions']['global']` → `cfg['global']`

### 0.2 为什么删

1. **加新数据要改 adapter**——Q1 FY2026 actual 需要扩展 `range(4)`，下一季度还得改
2. **两套访问模式并存**——`cfg['actuals']['fy0']['rev']` 和 `_gaap('rev', FY0_KEY)` 同时存在，认知负担
3. **硬编码时间假设**——`fy-2/fy-1/fy0` 固定 3 年、`range(4)` 固定 4 季度、`fy_keys[2]` 隐式假定
4. **市场化推断**——`market in ('jp','kr','tw')` → B-mode，应该显式声明

### 0.3 当前覆盖状态

四家公司已在新格式下运行，checks 验证通过：

| 公司 | depth | module | 市场 | FY0 Check Revenue |
|---|---|---|---|---|
| HWM | ebitda | yoy | US | 0% |
| Santec | op | vol_asp+yoy | JP | 0.01% |
| Lumentum | op | vol_asp+yoy | US | 0.01% |
| Zhenhua | gp | vol_asp+yoy | CN | 0.87% |

HWM 已完成 Q1 FY2026 model update（actual 数据加入、q_actual_count 4→5、YOY 从 Q1 2026 earnings 校准）。

### 0.4 C1-C3 已完成内容

在 `build()` 函数顶部已添加直接访问层：

```python
_gaap(field, fy, period)   → raw['actuals']['gaap']['is'][field][fy][period]
_non(field, fy, period)    → raw['actuals']['non_gaap']['is'][field][fy][period]
_gaap_seg(name, field, fy) → raw['actuals']['gaap']['segments'][name][field][fy]
_non_seg(name, field, fy)  → raw['actuals']['non_gaap']['segments'][name][field][fy]
_br(line_idx, fy)          → raw['assumptions']['lines'][line_idx]['base_rate'][fy]['annual']
_yoy(line_idx, sc, fy)     → raw['assumptions']['lines'][line_idx]['yoy'][sc][fy]['annual']
_gl(field, fy)             → raw['assumptions']['global'][field][fy]['annual']
```

C1-C3 已完成：
- `seg['fy0']['rev']` → `_gaap_seg()`（15 处）
- `gl.get('opm')` / `gl.get('tax_rate')` → `_gl()`（4 处）
- Hidden Bridge + P&L 历史引用 → `_gaap()`/`_non()`（10 处）

---

## 1. Batch 1: C1-C2 — 剩余 `gl` + `actuals` + `segments` 替换

**约 25 处替换，2-3 builds。**

### 1.1 — `gl['opm']` 数组 → `_gl('opex_rev', fy)`（~8处）

文件：`build-logic-model.py`

影响位置：
- L672-699: Phase 1.3 Blend — 原地修改 `gl['opm'][idx]`。需要建 mutable dict `_opm_cache = {fy: _gl('opex_rev', fy) for fy in all_fys}`， blend 修改这个 cache 而不是 adapter 数组
- L1272: Section 1 OP rate — `gl.get('opm', [0.25]*8)[2]` → `_gl('opex_rev', FY0_KEY)`
- L1542: Section 2 line OPM — `gl.get('opm', [])` → 同上
- L1974: Section 2 Opex render — 同上
- L2596-2599: GP depth Opex/Rev — 同上

### 1.2 — `actuals` dict → `_gaap()`/`_non()`（~5处）

- Phase 1.1 reconcile: `a[['fy-2','fy-1','fy0'][fy_idx]]['rev']` → `_gaap('rev', fymap[fy_idx])`
- Provenance check: `a.get(fy_key, {}).get(field)` → skip（validate 在 Batch 3 重写）

### 1.3 — `segments` list → `_gaap_seg()`（~12处）

- Section 1: `seg.get('fy-2', {}).get('rev')` → `_gaap_seg(sn, 'rev', FY2_KEY)`
- §2→§1 Fill: `seg['fy0']['rev']` → 已部分替换，补完剩余
- SOTP: `seg['fy0']['rev']` → 同上

**Verification:** 每步后 build HWM + Santec，checks 不变。

### Pivot point
- 如果 Batch 1 反复出问题 → 先 commit working state，评估是否继续
- 如果 Batch 1-2 checks 出现差异 → stop，排查 adapter vs direct access 数据不一致

---

## 2. Batch 2: C3 — `logic_lines` 替换

**约 20 处替换，4-6 builds。整个计划最硬的部分。**

### 2.1 — Section 2 线渲染（~8处）

文件：`build-logic-model.py`，约 L1340-1950

核心改动模式：
```python
# 改前
for ll in logic_lines:
    gm = ll['gm']                     # old format dict
    proj_gm = gm.proj[i]           # array index
    yoy_base = ll.yoy.base[i]      # array index

# 改后
for idx, ll in enumerate(logic_lines):
    gm_fy0 = _br(idx, FY0_KEY)        # FY-key access
    proj_gm = _br(idx, proj_fys[i])
    yoy_base = _yoy(idx, 'base', proj_fys[i])
```

关键位置：
- L1440-1460: `gm = ll['gm']` → Section 2 per-line profit chain
- L1542: `om_rates` from `ll.get('opm')` or `gl.get('opm')`
- L1596: `nm_rates` from `ll.get('tax_rate')`
- L1955-1993: Section 2 inline Opex/OPM rendering

### 2.2 — Phase 1.1 + 1.3 + 1.4（~12处）

这些 phase 在 Section 2 之前运行，同样用 `ll['yoy']` 和 `ll['gm']`。

- Phase 1.1 reconcile: L569-640 — `ll['yoy']['base']`, `ll['gm']`
- Phase 1.3 blend: L658-685 — `gl['opm']` 原地修改（已在 Batch 1.1 处理）
- Phase 1.4 Q driver: L696-960 — `ll['yoy']['base']`, `ll['volume']['proj']`

**Verification:** 每步后 build 4 家公司，Q driver M 值不变，checks 不变。

---

## 3. Batch 3: C4 — 删 adapter + 重写 validate

**1-2 builds。**

### 3.1 — 删除

```python
# 删除以下代码块：
_adapt_new_to_old(cfg)          # ~140 lines, L266-506
raw = json.loads(json.dumps(cfg))  # deep copy
cfg = _adapt_new_to_old(cfg)       # adapter call
validate_json(cfg)                  # old-format validate
meta = cfg['meta']; actuals = ...   # compat vars
logic_lines = cfg['logic_lines']; gl = cfg['global']

# 替换为：
cfg = cfg  # 保持新格式
validate_json_new(cfg)  # 新 validate（见 3.2）
```

### 3.2 — validate 重写

旧 validate 检查 old-format 字段。新 validate 直接检查新格式：

```python
def validate_json_new(cfg):
    meta = cfg['meta']
    actuals = cfg['actuals']
    asm = cfg['assumptions']
    
    # depth check
    depth = meta.get('p&l_depth')
    
    # actuals: gaap.is.{rev, gp, oi, ni, tax, da} 必填 (by depth)
    # assumptions.lines[]: {name, module, segment, one_to_one, is_segment_core}
    #   + base_rate (non-1:1: all FYs, 1:1: projection FYs)
    #   + yoy (all lines with module=yoy)
    #   + sotp: {method, multiple} — 不能为空
    # assumptions.global: {tax_rate, opex_rev, nm} — all FYs
    # assumptions.segment_residuals: optional
```

**Verification:** 给 L1 的 sotp 写成 `{}` → build 报错。

---

## 4. Batch 4: D1-D4 — Generalization

**4-6 builds。**

### 4.1 — D1: `range(4)` → dynamic Q count

影响范围（adapter 已删后在 build 中搜索替换）：
- Phase 1.1 reconcile: `for j in range(4)` → `for j in range(fyc)` 或基于 q_actual_n
- Phase 1.4 Q driver: 同上
- Q 列生成: 基于 `q_actual_n + q_proj_n` 动态

### 4.2 — D2: FY keys 动态化

不再硬编码只有 3 个历史年。`base_fy` 定义 FY0，历史年数量 = `actuals.gaap.is.rev` 中不含 E 的 FY key 数。

### 4.3 — D3: PRICE_FMT 从 currency 推断

```python
PRICE_FMT = {'USD': '$#,##0.00', 'JPY': '¥#,##0', 'CNY': '¥#,##0.00', 'KRW': '₩#,##0'}
price_fmt = PRICE_FMT.get(meta['currency'], '#,##0.00')
```

删除 `market in ('jp','kr','tw')` 推断。

### 4.4 — D4: `display_unit` 形式化

**JSON 新增字段：**
```json
"meta": {
    "display_unit": "M",  // "M" | "B" | "K"
    "display_decimals": 1
}
```

**JSON 值规则：**
- 存原始值（美元存到个位: 8,252,000,000）
- `display_unit: "M"` → 显示 8,252.0
- `display_unit: "B"` → 显示 8.3

**Excel 影响：**
- `sc(v)` = `round(v / unit_divisor, display_decimals)` — M: 1000000, B: 1000000000
- NUM = `#,##0.0` 统一
- vol_asp Revenue 公式: `=(Vol × ASP) / unit_scale` 中的 `unit_scale` 仅用于 Vol×ASP→Rev 单位转换（不受 display_unit 影响）

**同步更新文件：**
- `references/research-model-schema.md` — 加 `display_unit` + `display_decimals`
- `skill.md` / `SKILL.md` — 更新 meta 字段说明

---

## 5. Batch 5: E — 四公司 JSON 原始值重写

**2-3 builds。**

用脚本批量转换所有 JSON actuals 为原始值。

```python
# 转换表
unit_multiplier = {'M': 1_000_000, 'B': 1_000_000_000}
for fy_data in actuals:
    for field in fy_data:
        fy_data[field] *= unit_multiplier[display_unit]
```

需触发：financial-data flipper (D1) 也会需要同步适配（provider 返回的原始值 vs 当前 unit 值）。

**Verification:** build 4 家公司，checks 不变，Excel 数值一致。

---

## 6. Verification Gates

| Batch | Gate | 标准 |
|---|---|---|
| 1-2 | 每 sub-step | HWM + Santec build，checks 不变 |
| 3 | 删 adapter | 4 家公司 build，validate 拦截空 SOTP |
| 4 | D1-D4 | 4 家公司 build，Q 列数动态正确，display_unit 生效 |
| 5 | JSON 重写 | 4 家公司 build，checks 不变 |

---

## 7. Estimated Effort

| Batch | Builds | 难度 | 风险 |
|---|---|---|---|
| 1: C1-C2 | 2-3 | 低 | gl mutable dict 可能出 bug |
| 2: C3 | 4-6 | 高 | line index 映射错误导致 checks 漂移 |
| 3: C4 | 1-2 | 低 | validate 漏检 |
| 4: D1-D4 | 4-6 | 中 | display_unit 改动影响 Excel 全表 |
| 5: E | 2-3 | 低 | 纯 JSON 批量操作 |
| **Total** | **13-20** | | |

---

## 8. Execution Order

```
Batch 1 → Batch 2 → Batch 3 → Batch 4 → Batch 5
```

每 batch 完成后 commit，可随时暂停。

---

## Resources

- Builder: `.scripts/driver-map/build-logic-model.py`（~3100 lines）
- Modules: `.scripts/driver-map/modules/{yoy,vol_asp,ebitda,backlog_burn,capacity_util}.py`
- Helpers: `.scripts/driver-map/helpers/{migrate_old_to_new,derive-base-rate,seasonality,split-annual-to-q,validate-q-fy}.py`
- Schema reference: `references/research-model-schema.md`
- Migration plan: `docs/superpowers/specs/2026-07-04-research-model-migration-plan.md`
- Skill reference: `~/.claude/plugins/cache/buy-side-research-skills/.../driver-map/SKILL.md`
- HWM: `industry/aerospace/companies/hwm/.cache/test_model/research-model.json`
- Santec: `industry/optical-module-equipment/companies/santec/.cache/test_model/research-model.json`
- Lumentum: `industry/optical-module-equipment/companies/lumentum/.cache/test_model/research-model.json`
- Zhenhua: `industry/aerospace/companies/zhenhua-chem/.cache/test_model/research-model.json`
