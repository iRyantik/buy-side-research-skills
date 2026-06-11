# Data Landing Enforcement — actuals as Single Source of Truth

> 状态: planned | 日期: 2026-06-11 | 目标: v5.29.0

---

## 1. 问题

Agent 在研究过程中获取的数据（分部营收、季度利润、consensus、custom KPI）散落在 artifact 的 md 表格里——不落回 actuals。下次 session、下一个 skill 无法复用。CLAUDE.md 规则说"必须落地"但没有强制力——agent compact 后遗忘、跳过。

## 2. 设计

### 2.1 强制链

```
agent 发现数据
  ↓
skill pipeline: 先落地 actuals._supplement，再写 artifact（B 层——教正路）
  ↓
agent Edit actuals → 数据在 actuals 里了
  ↓
agent Read actuals → 从 actuals 取数 → Write artifact
  ↓
Hook CHECK 16: 扫 artifact 表格 → 查 actuals._supplement → 有 ✅ → 放行
                        → 无 ❌ → block + 给 agent 精确补数命令（C 层——挡错路）
```

### 2.2 CHECK 16 规则

**触发条件**：
- 文件路径在 `industry/*/companies/<ticker>/` 下
- artifact 含表格行（`| ... | ... | ... |` 最少 3 列）
- 列头匹配 `分部|segment|收入|营收|revenue|占比|产品线|地域|geography`

**检查**：
- `actuals._supplement.revenue_split` 非空 → 放行
- 空 → block + 输出精确补数命令

**Block 格式**：
```
⛔ pre_write_gate CHECK 16: artifact has segment data but actuals has no revenue_split.
   Land the data first:
   1. Read actuals-resolved.json
   2. Edit _supplement.revenue_split with segment data
   3. Re-run this Write
```

### 2.3 生效范围

**公司级 artifact**（`industry/*/companies/<ticker>/`）：stock-quickread / driver-map / earnings-setup / peer-deep-dive / moat-analysis / capital-allocation / 等——全锁。

**不拦**：行业级 artifact（teach-in / industry-landscape / mechanism-insight）、非 artifact 文件（RESEARCH.md、_cache/ 下的文件）。

### 2.4 Skill 层强化

stock-quickread pipeline 加：

```
数据流规则：
  任何公司级数据——不论来源——在写入 md 表格之前，必须先落地到 actuals._supplement。
  agent 不能"之后补"、不能跳过。
  actuals 是 fact source、artifact 是 display。
```

## 3. 文件改动

| 文件 | 改动 |
|---|---|
| `pre_write_gate.py` | CHECK 16 强化——表格行 + 列头匹配 + 精确 block 指令 |
| `stock-quickread/SKILL.md` | 数据流规则——落地 actuals 后再写 artifact |
| CLAUDE.md ZH/EN template | CHECK 16 描述更新 |

## 4. 不做

- 不改 `actuals-resolved.json` schema
- 不加 enrich.py（agent Edit 直接 merge）
- 不拦行业级 artifact
- 不要求所有表格数字都匹配（只检查 revenue_split 这个最容易遗漏的维度）
