# RESEARCH.md 研究轨迹自动追加 设计

> 状态: draft
> 日期: 2026-06-05
> 关联: research_memory_gate.py, RESEARCH.md §4

---

## 1. 问题

`research_memory_gate` hook 只在 RESEARCH.md 过期时 warn，不实际记录。agent 写完 artifact 后经常忘记更新研究轨迹，导致 RESEARCH.md §4 的 "已完成" 表滞后，新 session 不知道之前跑过什么 skill。

## 2. 目标

Stop hook 自动检测新写入的研究 artifact → 找到对应 RESEARCH.md → 追加一条记录到 §4 "已完成" 表 → 更新 `updated` 日期。

不变的部分（手工维护）：Source 地图、Thesis 状态、事实基线。这几个需要判断，auto 不了。

## 3. 触发条件

- Stop 事件
- target 文件匹配 `YYYY-MM-DD-<skill>-<qualifier>.md`
- 文件在 `industry/` 路径下
- 文件是**新写入**（之前不存在，或本次被 Write/Edit 修改）

## 4. 动作

### 4.1 找到对应的 RESEARCH.md

```
artifact: industry/<slug>/companies/<ticker>/2026-06-05-stock-quickread-mycronic.md
  → 先查 industry/<slug>/companies/<ticker>/RESEARCH.md（公司级）
  → 不存在则查 industry/<slug>/RESEARCH.md（行业级）
  → 两者都没有 → skip

artifact: industry/<slug>/2026-06-05-industry-landscape.md
  → 查 industry/<slug>/RESEARCH.md
```

### 4.2 提取产出摘要

从 artifact 文件的前几行提取一句话描述：

```python
def _extract_summary(artifact_path: str) -> str:
    with open(artifact_path, "r", encoding="utf-8") as f:
        head = f.read(2000)
    # 尝试取第一个 # 标题
    m = re.search(r'^#\s+(.+)', head, re.MULTILINE)
    if m:
        return m.group(1).strip()[:100]
    # fallback: 取第一段非空行
    for line in head.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("---"):
            return stripped[:100]
    return os.path.basename(artifact_path)
```

### 4.3 追加到 §4 已完成表

在 RESEARCH.md 的 `### 已完成` 子节下插入一行：

```markdown
### 已完成
| 日期 | Artifact | 一句话产出 |
|---|---|---|
| 2026-06-05 | [stock-quickread-mycronic.md](./stock-quickread-mycronic.md) | Mycronic — PG 垄断+GT AI-HBM 驱动的设备周期股 |
```

规则：
- 在 `### 已完成` 后第一个空行或 `|---|---|---|` 行后插入
- 按日期倒序（新记录插在表头行后第一行）
- 如果同一 artifact 文件已在表中 → 更新对应行（覆盖），不增加重复行
- 如果没有 `### 已完成` 子节 → 在 `## 4. 研究轨迹` 后创建

### 4.4 更新 frontmatter

```python
updated: 2026-06-05
```

只改这一行，不动其他 frontmatter 字段。

## 5. 不触发场景

| 场景 | 行为 |
|---|---|
| artifact 不在 `industry/` 下 | skip |
| 没有对应 RESEARCH.md | skip |
| 同一 artifact 已在表中且内容未变 | skip |
| Write/Edit 修改的是现有文件 | 更新对应行 |
| 文件不是 YYYY-MM-DD 格式 | skip |

## 6. 实现

改造现有 `research_memory_gate.py`：当前只 warn → 升级为 warn + append trail。

或者在 `hook_entry.py` STOP_RULES 中新增一个独立 hook `research_trail_append.py`，`research_memory_gate.py` 保留纯 warn。

**推荐**：升级 `research_memory_gate.py`——同一个 hook，职责从 "提醒" 升级为 "执行+提醒"。warn 仍然触发（提醒更新 Source/Thesis/事实），但研究轨迹自动 append 不再需要人工。

## 7. 非目标

- 不自动更新 Source 地图
- 不自动更新 Thesis 状态
- 不自动更新事实基线
- 不解析 artifact 内容做语义摘要（只取标题）
- 不删除旧记录
