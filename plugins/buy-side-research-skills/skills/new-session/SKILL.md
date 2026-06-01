---
name: new-session
description: Create or locate an industry topic and resolve a dated research result path for a company or industry artifact.
---

# New Session

`new-session` solves one narrow operations problem: where should this research live? It creates or locates an industry topic, ensures `index.md` and `_inbox/` exist, registers the company in `coverage.md` and industry `index.md`, and resolves a dated result path. It does not run research, ingest files, or build models.

## 心法

所有研究落在行业 topic 下。公司是行业的子目录——一个公司一个窝，跨行业只 reference，不搬文件。

```
industry/<industry-slug>/
  index.md                              # 行业 overview + 公司注册表
  companies/<ticker>/                   # 公司子目录
  _inbox/
coverage.md                             # 全局主表
```

`coverage.md` 是唯一映射层——行业 × 公司的全局索引。公司首次研究时注册，跨行业时追加 reference。

## 职责边界

负责：
- 创建或定位 `industry/<industry-slug>/`
- 确保 `index.md` + `_inbox/` 存在
- 在 `coverage.md` 和行业 `index.md` 注册公司
- 解析 dated result path
- 支持 `qualifier` 命名（required/optional/plain）

不负责：
- 创建 `_cache/`（financial-data, driver-map 等按需自建）
- 写研究结论
- 预建目录

## 触发与输入

Trigger: "new session", "create topic", "open topic", "resolve save path", "where should this artifact be saved"

| Input | 用途 | 默认 |
|---|---|---|
| `industry_slug` | 行业目录名 | agent 从 ticker 业务推断；推断不了问用户 |
| `ticker` | 公司标识 | 公司级 artifact 必填 |
| `date` | 日期 | 当前 YYYY-MM-DD |
| `artifact_name` | 保存的 artifact | 必填 |
| `qualifier` | 子主题/事件锚点 | 按 upstream skill 的 naming_mode |

## 场景矩阵

### 公司级 artifact

| # | 场景 | 行为 |
|---|---|---|
| 1 | 新行业 + 新公司 | 建 `industry/<industry>/` + `index.md` + `companies/<ticker>/` → 注册 `coverage.md` |
| 2 | 已有行业 + 新公司 | 建 `companies/<ticker>/` → 注册行业 `index.md` + `coverage.md` |
| 3 | 已有公司 + 同行业继续研究 | 直接落原 `companies/<ticker>/` |
| 4 | 已有公司 + 进新行业 | **文件不搬**——接着原目录写。新行业 `index.md` 注册 reference → `coverage.md` 更新 |
| 5 | agent 判断行业错了 | 文件 <3 个 → 搬家；≥3 → reference 不搬。用户确认 |
| 6 | 用户没指定行业 | agent 从 ticker 业务推断 → 不确定时问用户"放哪个行业？" |
| 7 | 公司改名/重组 | `coverage.md` + 行业 `index.md` 更新名称。目录不改——路径稳定性优先 |
| 8 | 退市/放弃覆盖 | `coverage.md` 标 `archived`，文件不删 |

### 行业级 artifact

| # | 场景 | 行为 |
|---|---|---|
| 9 | 行业 quickread / consensus-map 等 | 落 `industry/<industry>/YYYY-MM-DD-<artifact>.md` |
| 10 | 先行业 quickread，后筛公司 | 行业已存在 → 加 `companies/<ticker>/`，按 #2 |

### 跨公司 artifact

| # | 场景 | 行为 |
|---|---|---|
| 11 | peer-deep-dive 同行业 | 落该行业根 |
| 12 | peer-deep-dive / pair-trade 跨行业 | 落**主驱动行业**（thesis 核心 driver 在哪侧）。另一行业 `index.md` 注册 reference |

## 路径解析

### 公司级

```text
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>-<qualifier>.md
```

公司级 skill（stock-quickread, driver-map, company-history, alpha-thesis, earnings-setup, bear-pre-mortem, consensus-map Single-Name）默认 `required_qualifier`，qualifier = ticker。

### 行业级

```text
industry/<industry>/YYYY-MM-DD-<artifact>.md
```

行业级 skill（industry-landscape）默认 `optional_qualifier`。

### peer / pair

```text
industry/<industry>/YYYY-MM-DD-<artifact>-<qualifier>.md
```

默认 `optional_qualifier`。

### 碰撞处理

同名文件追加 `-2`, `-3`，不覆盖。

## Index Touch

轻量更新，不重写：

```markdown
# <Industry Name> — 研究 index

## Companies

| 公司 | Ticker | 主行业 | 文件位置 | 状态 |
|---|---|---|---|---|
| GE Vernova | GEV | ✅ | companies/ge-vernova/ | active |
| 西门子能源 | ENR.DE | — | → power-generation/companies/siemens-energy/ | monitor |
```

## coverage.md

```markdown
# Coverage Map

| 行业 | 公司 | 主行业 | 最新 artifact | 状态 |
|---|---|---|---|---|
| nuclear | GE Vernova | ✅ | 2026-05-31 stock-quickread | active |
| power-generation | GE Vernova | — | → nuclear | active |
| nuclear | 西门子能源 | ✅ | 2026-05-30 peer-deep-dive | active |
```

## 运行输出契约

```markdown
## New Session Result

**结论先行**
已创建 / 已定位行业 topic: industry/<industry-slug>/

## Topic
- industry: <slug>
- company: <ticker>
- mode: created / located
- industry index: <path>

## Result Path
- artifact: <artifact>
- path: industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md
```

## 失败处理

- 缺 industry_slug：propose candidate，不写
- 缺 ticker（公司级 artifact）：追问
- 已有 topic：report located，不重建
- 已有文件：suffix `-2`

## 安全自查

- ❌ 创建 `_cache/`
- ❌ 覆盖 `index.md`
- ❌ 覆盖已有文件
- ❌ 不注册就写文件
