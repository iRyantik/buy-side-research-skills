# research-model.json 落地迁移计划

**状态：P0 split 进行中 | P1-P4 待执行**

---

## 0. 核心架构回顾

### 数据流向

```
历史 (FY2024-FY2026):    actuals → §1 Seg → §1 Line Split (seg × split) → §2 Line Rev (=引用§1)
投影 (FY2027E+):         assumptions → §2 BBE/yoy → §2 Line Rev(=公式) → §2→§1 Fill (Σ → Seg)
                                                                              ↓
                              assumptions → §2 base_rate → §2 EBITDA(=Rev×%)
                                                                              ↓
                              §3 P&L (= Σ line) → Hidden Bridge gap → GP/OI/NI
```

### 统一访问路径

```
{source}.{field}.{FY}.{period}

actuals.gaap.is.rev.FY2025.annual = 8252
assumptions.lines[0].base_rate.FY2026E.annual = 0.34
assumptions.global.tax_rate.FY2023.annual = 0.22
```

---

## 阶段总图

```
P0: JSON字段补全 (split + segment_residuals)
  ↓
P1: JSON字段补全 (tiers多层级 + opex_rate)
  ↓
P2: adapter补全 → 三公司JSON补全 → build验证
  ↓
P3: 新模块 (capacity + capacity_util + ebitda + backlog_burn)
  ↓
P4: 收尾 (P&L section替换 + adapter删除 + P2 schema reference + 旧doc deprecation)
```

---

## P0: JSON 核心字段补全（split + segment_residuals）

### P0.1 — `lines[].split`

| 属性 | 值 |
|---|---|
| 类型 | float, 0-1 |
| 1:1 line | 可选，默认 1.0 |
| non-1:1 line | 必填 |
| 用途 | 历史: line_rev = seg_rev × split |
| HWM 示例 | L1: 1.0, L2: 1.0, L3: 1.0, L4: 1.0, Non-core: 0 |
| Santec 示例 | tap-PD: 0.33, SLM: 0.67, 光通信测试: 0.72 |

### P0.2 — `segment_residuals`

| 属性 | 值 |
|---|---|
| 位置 | `assumptions` 顶层 |
| 类型 | `{ seg_name: { rev: int, base_rate: float } }` |
| 用途 | 段内 split 总和 < 1.0 时的未建模余额 → §2→§1 Fill: 段投影 = Σ线 + residual |
| HWM | 无（4条1:1线全覆盖） |
| Santec | `"その他": { "rev": 0, "base_rate": 0.36 }` |

### P0.3 — adapter 适配 + 三公司 JSON 补全

- adapter 读 `split` → `seg.logic_lines[].split`
- adapter 读 `segment_residuals` → `seg.residual`
- HWM: 加 `split: 1.0`（5条线全1:1）
- Santec: 加 `split` + `segment_residuals`
- Lumentum/Zhenhua: 迁移时一并填

---

## P1: JSON 字段补全（tiers + opex_rate）

### P1.1 — `lines[].tiers[]` 多层级

当前只有单 `asp_base`。恢复旧 schema 的多 tier 支持：

```json
"tiers": [
  {
    "name": "AI",
    "share": { "FY2026": { "annual": 0.05 }, "FY2027E": { "annual": 0.156 } },
    "asp": { "FY2026": { "annual": 26 }, "FY2027E": { "annual": 30 } }
  },
  {
    "name": "Consumer",
    "asp": { "FY2026": { "annual": 4.9 }, "FY2027E": { "annual": 5.5 } }
  }
]
```

最后一项无 `share` → residual tier（share = 1 − Σ前项）。

### P1.2 — `lines[].opex_rate`

线级 Opex/Rev 覆盖。FY-keyed，可选：

```json
"opex_rate": { "FY2026": { "annual": 0.22 }, "FY2027E": { "annual": 0.21 } }
```

缺 → fallback 到 `global.opex_rev`。

---

## P2: adapter 补全 + 三公司迁移

### P2.1 — adapter 补全

| 适配项 | 新格式 → old |
|---|---|
| `split` | → `seg.logic_lines[].split` |
| `segment_residuals` | → `seg.residual: {gm}` |
| `tiers[]` | → old `tiers[]` + `share_fy0` / `share_proj[]` + multi `asp_bull/base/bear` |
| `opex_rate` | → `ll.opex_rate[]` |
| `capacity` | → `ll.capacity: {fy0, proj[], unit, ramp_notes}` |

### P2.2 — 三公司 JSON 补全 + build

| 公司 | 补全项 | 验证 |
|---|---|---|
| HWM | split=1.0（已有，确认） | build checks 一致 |
| Santec | split + residuals + tiers + opex_rate | checks 对齐 old xlsx |
| Lumentum | 迁移 + 全字段 | build pass |
| Zhenhua | 迁移 + 全字段 | build pass |

---

## P3: 新模块

### P3.1 — `capacity` 字段

```json
"capacity": {
  "FY2026": { "annual": 10000 },
  "FY2027E": { "annual": 13000 }
}
```

可选。有则 vol_asp 渲染 Nameplate Capacity + Utilization 行。

### P3.2 — `capacity_util` module

```
Revenue = Capacity × Utilization × ASP / unit_scale
```

利用率为 I cell 假设。需要全新渲染逻辑。

### P3.3 — `ebitda` standalone module

将 `build()` 内联的 EBITDA profit chain（30行 if-is_ebitda_depth）封装为独立 module。零功能差异，纯重构。

### P3.4 — `backlog_burn` module

```
Beg Backlog × Burn Rate = Revenue
End Backlog = Beg × (1 + OrderRate − Burn)
Beg_{t+1} = End_t
```

长周期订单驱动（航空/国防）。

### P3.5 — `segment.name_cn`

段名中文翻译。B 列灰色斜体渲染。

---

## P4: 收尾

### P4.1 — 删除 adapter

条件：所有 old-format 引用已替换为 `_gaap()`/`_non()`/`_l()` 访问函数。

### P4.2 — P2: schema reference

文件：`references/research-model-schema.md`
内容：P0-P3 落地后的最终 schema + HWM/Santec 双示例 + 四维约束表

### P4.3 — 旧 doc deprecation

- `2026-07-03-research-model-template-design.md` → deprecation header
- `2026-07-03-research-model-full-schema.md` → deprecation header

### P4.4 — 旧格式文件清理

- 删 `test-hwm.json` / `test-q-santec.json` / `test-q-lumentum.json` / `test-q-zhenhua.json`

---

## 否决项

| # | 旧概念 | 理由 |
|---|---|---|
| 1 | `compute_gaps()` 3年均值 | Hidden Bridge FY0 anchor Excel公式替代 |
| 2 | Phase 1.2 公司Q→段Q拆分 | Agent 创建 JSON 时处理好 |
| 3 | `history` 独立 section | `volume.FY` / `asp.FY` 的 FY-keyed 结构已完成 |
| 4 | `volume.unit` | display sugar, `asp_unit` 已覆盖 |

---

## Resources

- Builder：`.scripts/driver-map/build-logic-model.py`
- Skill schema ref：`~/.claude/plugins/cache/buy-side-research-skills/.../driver-map/references/json-schema.md`
- HWM JSON：`industry/aerospace/companies/hwm/.cache/test_model/research-model.json`
- Santec JSON：`industry/optical-module-equipment/companies/santec/.cache/test_model/research-model.json`
- Migrate helper：`.scripts/driver-map/helpers/migrate_old_to_new.py`
