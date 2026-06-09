# GATE 强化 + Source Contract 修复 + 编码修复

> 状态: spec → 实现
> 日期: 2026-06-09
> 目标: v5.14.5

---

## 原则

只有一种东西能真的拦住 Agent：**hook 检查文件是否存在**。Pipeline 报告、GATE 标签、★ 标记——这些是辅助，不是防线。

防线必须是二进制：文件存在 → 放行。文件不存在 → block。

---

## Part A: CHECK 15 改写（pre_write_gate.py）

### 现状
CHECK 15 解析 Pipeline report header (`> Pipeline: actuals ✅ | ...`)——检查格式但不验证内容真假。

### 改为
CHECK 15 直接检查文件存在性。不读 Pipeline 报告——读文件系统。

```python
# CHECK 15: Artifact pipeline preconditions — files must exist before write
# For research artifacts under industry/*/companies/<slug>/:
#   - actuals-resolved.json must exist
#   - evidence ledger must exist  
#   - logo must exist
```

**检查逻辑**：
1. 从 artifact 路径提取 company slug（`companies/<slug>/`）
2. 检查 `<slug>/_cache/financial-data/actuals-resolved.json` 存在且非空
3. 检查 `<slug>/_cache/evidence/` 下存在 `*.evidence.json`
4. 检查 `_cache/images/<TICKER>-logo.*` 存在（workspace 级）
5. 任缺 → block + 告诉 Agent 哪条命令可以补

**soft-gate**：block 但给出明确的修复指令，Agent 补完重新 Write 即可。

### 不检查
- verify-claim 结果（无文件产出）
- discovery URL 数量（无文件产出）
- appendix 存在（best-effort）
- 数据新鲜度（Agent 责任）

---

## Part B: 删 image_exists hook

### 现状
`image_exists.py` 在 Stop 时检查 artifact 引用图片存在性。

### 改为
CHECK 15 已经在 Write 时检查 logo 文件。product image 的检查移入 CHECK 15（artifact 引用 `_cache/images/<slug>.png` 时检查）。`image_exists.py` 删除。

---

## Part C: Pipeline Report 从 stock-quickread 删除

### 现状
stock-quickread SKILL.md 要求 artifact 包含 Pipeline report header：

```
> Pipeline: actuals ✅ | verify-claim X/N ✅ | images ✅ | ledger ✅
```

### 改为
删除整个 Pipeline report 模板。Agent 不再需要写声明——hook 直接查文件。

---

## Part D: [actuals] 作为标准 code

### 现状
`source_contract.py` STANDARD_CODE_RE 不认 `actuals` 和 `actuals-source`。`[actuals](path)` 在 Resources 中会被报 non-standard label。

### 改为
STANDARD_CODE_RE 增加 `actuals` 和 `actuals-source`。artifact 中可以写 `[actuals](./_cache/financial-data/actuals-resolved.json)` 作为 valid inline source。

（已修改，未提交）

---

## Part E: update_agent_runtime.py date 编码修复

### 现状
`subprocess.run(["date", "-u", ...], shell=True)` 在 Windows 上产生 GBK 编码错误。

### 改为
`from datetime import datetime, timezone; datetime.now(timezone.utc).strftime(...)`。

（已修改，未提交）

---

## 文件变更清单

| 文件 | 动作 |
|---|---|
| `pre_write_gate.py` | CHECK 15 改写（文件存在检查）+ 删 image_exists 逻辑 |
| `image_exists.py` | 删除 |
| `source_contract.py` | STANDARD_CODE_RE 加 actuals（已改） |
| `update_agent_runtime.py` | date → datetime（已改） |
| `stock-quickread/SKILL.md` | 删 Pipeline report 模板 |
| `stock-quickread/SKILL.en.md` | 同上 |
| `pre_write_gate.py` CHECK 1-14 | 保持不变 |

---

## 影响面

| 组件 | 风险 |
|---|---|
| CHECK 15 | 低——从解析 text 改为检查文件，更简单更可靠 |
| 删 image_exists | 低——CHECK 15 已覆盖 |
| stock-quickread | 低——只删一个模板代码块 |
| source_contract | 低——只加两个 alias |
| update_agent_runtime | 低——等价替换 |
