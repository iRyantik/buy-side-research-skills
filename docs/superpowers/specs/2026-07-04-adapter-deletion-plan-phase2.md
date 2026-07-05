# Adapter 彻底删除 + 全量新格式迁移计划（Phase 2）

## 0. 当前状态（Phase 1 成果）

Phase 1（5 batches, commits `0e8fdd6`→`36d13b3`）已完成：
- `build()` 内核心数据流切换到 direct accessors（`_gaap`, `_non`, `_br`, `_yoy`, `_vol`, `_asp`, `_gl`, `_opm`）
- `validate_json_new()` 直接读 FY-inside 格式
- PRICE_FMT + B-mode 从 currency 推断
- `display_unit` + `display_decimals` 显式声明在 JSON meta

**Adapter 仍承担的角色：**

```
raw (new format, read-only)
    ↑ direct accessors (_gaap, _br, ...)
    │
cfg = _adapt_new_to_old(raw)  ← 237 行，待删除
    │
    ├── cfg['meta']           ← pass-through（不变）
    ├── cfg['actuals']        ← gaap+non-gaap 合并为 flat dicts
    ├── cfg['segments']       ← FY-keyed segment data + logic_lines + quarters
    ├── cfg['quarters']       ← 公司级 Q data
    ├── cfg['logic_lines']    ← 业务线（gm/yoy/volume/tiers 转为旧数组格式）
    └── cfg['global']         ← tax_rate 标量 + opm 数组
```

## 1. 剩余旧格式依赖分布

### 1.1 模块渲染器（modules/*.py, ~744 lines）

| 模块 | 行数 | 旧格式依赖 | 使用公司 |
|---|---|---|---|
| **yoy.py** | 95 | `yoy['bull']`, `yoy['base']`, `yoy['bear']` 数组 | HWM, Santec, Lumentum, Zhenhua |
| **vol_asp.py** | 263 | `vol['fy0']`, `vol['proj']`, `tiers[].asp*` 数组, `history['fy-2']` | Santec, Lumentum, Zhenhua |
| **ebitda.py** | 74 | 待验证（目前未被深度使用） | — |
| **backlog_burn.py** | 192 | `ll['backlog']['burn']['proj']`, `ll['backlog']['order']` | 无（四家都没用） |
| **capacity_util.py** | 120 | `cap['fy0']`, `cap['proj']` | 无（四家都没用） |

### 1.2 build() 内剩余引用（~40 处）

| 区域 | 旧格式模式 | 数量 |
|---|---|---|
| **Phase 1.3 blend** | `ll_obj['gm']['proj'][proj_i]`, `ll_obj.get('opm')` | ~4 |
| **Section 1 渲染** | `seg.get('fy-2', {}).get('rev')`, `seg['fy0']`, `seg['logic_lines']`, `seg['quarters']` | ~15 |
| **Hidden Bridge** | `cfg['actuals'][fy_key]['rev']`, `['gp']`, `['oi']` 等 | ~6 |
| **P&L 渲染** | `cfg['actuals'][fy_key]` | ~5 |
| **Non-core gap Q** | `cfg['quarters']`, `seg['quarters']` | ~4 |
| **Section 2 渲染** | `ll['gm']`, `ll['yoy']`（部分已替换，剩余在模块调用链） | ~3 |
| **Compat vars** | `logic_lines = cfg['logic_lines']`, `gl = cfg['global']` | 2 |

### 1.3 待删除代码

| 代码块 | 行数 | 行号 |
|---|---|---|
| `validate_json()` (旧) | ~118 | L155-273 |
| `_adapt_new_to_old()` | ~237 | L351-588 |
| deep copy + compat vars | ~6 | L605-611 |

## 2. 执行计划

### Phase A: 模块渲染器 → 新格式（4-6 builds）

**策略**：给模块渲染器注入 `line_idx` + helper functions，通过 `ctx` 传递。不改函数签名。

#### A.1 — ctx 注入层（1 build）

在 `build()` 中，per-line 循环内设置：
```python
ctx['li'] = line_idx                    # line index
ctx['_br'] = lambda fy: _br(line_idx, fy)
ctx['_yoy'] = lambda sc, fy: _yoy(line_idx, sc, fy)
ctx['_vol'] = lambda fy: _vol(line_idx, fy)
ctx['_asp'] = lambda fy, tier=0: _asp(line_idx, fy, tier)
ctx['_unit_scale'] = _unit_scale(line_idx)
```

模块渲染器内部用法：
```python
# 旧：yoy['base'][idx]
# 新：ctx['_yoy']('base', f'FY{bfyr+1+i}E')

# 旧：vol['fy0'], vol['proj'][idx]
# 新：ctx['_vol'](FY0_KEY), ctx['_vol'](f'FY{bfyr+1+i}E')

# 旧：t.get('asp_base', [])[idx]
# 新：ctx['_asp'](f'FY{bfyr+1+i}E')
```

#### A.2 — yoy.py（1-2 builds）

改动量：~10 处数组访问 → `ctx['_yoy']()` 调用。
- `yoy['bull']`, `yoy['base']`, `yoy['bear']` → FY-keyed access
- 历史年 YoY 显示保持公式引用（不涉及 ll 访问）

**Verification**: HWM build（纯 yoy 公司），checks 不变。

#### A.3 — vol_asp.py（2-3 builds）

改动量最大：~25 处数组访问。
- `vol['fy0']` → `ctx['_vol'](FY0_KEY)`
- `vol['proj'][idx]` → `ctx['_vol'](f'FY{bfyr+1+i}E')`
- `t.get('asp_base', [])[idx]` → `ctx['_asp'](f'FY{bfyr+1+i}E')`
- `t.get('asp', [])[idx]` → `ctx['_asp'](f'FY{bfyr+1+i}E')`
- `t.get('asp_fy0')` → `ctx['_asp'](FY0_KEY)`
- `t.get('share_fy0')`, `t.get('share_proj', [])` → `raw` 直接访问
- `hist_all.get('fy-2', {})` → 用 FY2_KEY 从 raw 读 history volume/ASP
- `cap['fy0']`, `cap['proj']` → `raw` 直接访问
- `ll.get('unit_scale')` → `ctx['_unit_scale']`

**Verification**: Santec build（vol_asp + yoy），checks 不变。

#### A.4 — ebitda.py / backlog_burn.py / capacity_util.py（≤1 build）

这三个模块目前无公司使用，最小改动——确保不引用旧数组即可。backlog_burn 最复杂但无测试覆盖，标记为 "best-effort, verify on first use"。

### Phase B: Section 1 + build() 内部 → 新格式（4-6 builds）

#### B.1 — GM blend cache（1 build）

Phase 1.3 blend 中 `ll_obj['gm']['proj'][proj_i]` 建 mutable `_gm_cache`（类似 `_opm_cache`）：
```python
_gm_cache = {}
def _gm(line_idx, fy):
    if (line_idx, fy) not in _gm_cache:
        _gm_cache[(line_idx, fy)] = _br(line_idx, fy)
    return _gm_cache[(line_idx, fy)]
```

Blend 修改 `_gm_cache[(line_idx, proj_fy)] = round(gm_blend, 4)`。

#### B.2 — Section 1 渲染（2-3 builds）

- Revenue 行：`seg.get('fy-2', {}).get('rev')` → `_gaap_seg(seg['name'], 'rev', FY2_KEY)`
- GP 行：同上，field='gp'
- OP 行：`seg.get('fy-2', {}).get('op')` → `_gaap_seg(seg['name'], 'oi', FY2_KEY)`
- EBITDA 行：→ `_non_seg(seg['name'], 'ebitda', FY2_KEY)`
- Q 列数据：`seg.get('quarters', {}).get(qk, {}).get('rev')` → 从 raw actuals Q data 读取

Segment 列表可以从 `raw['actuals']['gaap']['segments']` 获取，不再依赖 `cfg['segments']`。

#### B.3 — Hidden Bridge + P&L（1-2 builds）

- `cfg['actuals'][fy_key]` → `_gaap()` / `_non()` 映射
- Hidden Bridge gap 公式已用 `_gaap()`/`_non()` 引用，验证完整性
- P&L Overall 行：`_gaap('rev', fy)` 等

#### B.4 — Non-core gap Q + 剩余（1 build）

- `cfg['quarters']` Q data → 从 raw actuals 读
- `seg.get('quarters', {})` → 同上
- 剩余的 `ll['name']`, `ll.get('module')` 等标量访问 → 保留（两者格式一致）

### Phase C: 删除 adapter（1-2 builds）

#### C.1 — 删 adapter 函数

```python
# 删除：
# - _adapt_new_to_old(cfg) 函数（L351-588, 237 lines）
# - validate_json(cfg) 函数（L155-273, 118 lines）
# - raw = json.loads(json.dumps(cfg)) deep copy（L605）
# - cfg = _adapt_new_to_old(cfg) 调用（L607）
# - 旧 compat vars（L610-612）

# 替换为：
validate_json_new(cfg)
raw = cfg  # no deep copy needed
```

#### C.2 — 适配 build() 直接读新格式

- `cfg['segments']` 不再存在 → 从 `raw['actuals']['gaap']['segments']` 构建 segment list
- `cfg['logic_lines']` 不再存在 → 直接用 `raw['assumptions']['lines']`
- `cfg['global']` 不再存在 → 直接用 `raw['assumptions']['global']` 或 `_gl()`
- `cfg['quarters']` 不再存在 → Q data 从 raw actuals 读

#### C.3 — 删 compat vars

```python
# 删除：
meta = cfg['meta']; actuals = cfg['actuals']; segments = cfg['segments']
logic_lines = cfg['logic_lines']; gl = cfg['global']

# 替换为直接访问：
meta = raw.get('meta', {})  # raw IS cfg now
```

### Phase D: 清理 + 验证（1-2 builds）

- 全局搜索 `['fy-2']`, `['fy-1']`, `['fy0']`, `['proj']`（数组索引）→ 确认全部消除
- 全局搜索 `cfg['segments']`, `cfg['logic_lines']`, `cfg['global']`, `cfg['quarters']` → 确认全部消除
- 删除 `_adapt_new_to_old` 相关的 import（如有）
- 更新 schema reference 文档

## 3. Verification Gates

| Phase | Gate | 标准 |
|---|---|---|
| A.2 | yoy.py 改完 | HWM build, checks 不变 |
| A.3 | vol_asp.py 改完 | Santec build, checks 不变 |
| A 完成 | 全部模块 | 四家公司 build, checks 不变 |
| B.1 | GM blend cache | HWM + Santec build, checks 不变 |
| B.2 | Section 1 改完 | 四家公司 build, checks 不变 |
| B 完成 | build() 内部 | 四家公司 build, checks 不变 |
| C 完成 | adapter 删除 | 四家公司 build, checks 不变, validate 拦截空 SOTP |
| D 完成 | 清理 | `grep -r "fy-2\|fy-1\|fy0\]"` 返回空（排除注释和 JSON） |

## 4. Estimated Effort

| Phase | Builds | 难度 | 风险 |
|---|---|---|---|
| A: 模块渲染器 | 4-6 | **高** | vol_asp.py 改动量大 (~25 处)；backlog_burn 无测试 |
| B: build() 内部 | 4-6 | 中 | Section 1 渲染路径多；blend cache 与 _br 互动 |
| C: 删 adapter | 1-2 | **高** | 一次性删 350+ 行；隐式依赖可能遗漏 |
| D: 清理 | 1-2 | 低 | grep 扫描 + 文档更新 |
| **Total** | **10-16** | | |

## 5. 累计进度

```
Phase 1 (已完成): Batches 1-5, 5 commits, ~80 old-format refs replaced
Phase 2 (本计划): Phases A-D, ~10-16 builds, 删除 adapter 237 行 + 老 validate 118 行
─────────────────────────────────────────────────────────
完成后: build-logic-model.py ~2900 lines (从 ~3265), 零旧格式依赖
```

## 6. Execution Order

```
Phase A (模块) → Phase B (build 内部) → Phase C (删 adapter) → Phase D (清理)
```

Phase A 和 B 可部分重叠（A 改模块接口，B 改 build 内部，两者通过 ctx 交互）。
每 phase 完成后 commit，可随时暂停。

---

## Resources

- Builder: `.scripts/driver-map/build-logic-model.py`（~3265 lines）
- Modules: `.scripts/driver-map/modules/{yoy,vol_asp,ebitda,backlog_burn,capacity_util}.py`
- Schema reference: `references/research-model-schema.md`
- Phase 1 plan: `docs/superpowers/specs/2026-07-04-adapter-generalization-plan.md`
- Test models:
  - HWM: `industry/aerospace/companies/hwm/.cache/test_model/research-model.json`
  - Santec: `industry/optical-module-equipment/companies/santec/.cache/test_model/research-model.json`
  - Lumentum: `industry/optical-module-equipment/companies/lumentum/.cache/test_model/research-model.json`
  - Zhenhua: `industry/aerospace/companies/zhenhua-chem/.cache/test_model/research-model.json`
