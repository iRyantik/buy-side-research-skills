---
name: coverage-tracker
description: Maintain objective workspace coverage state with coverage status, monitor status, review dates, and next triggers.
---

# Coverage Tracker

`coverage-tracker` maintains objective coverage state at workspace root. It is not a portfolio tracker. Any company that has been researched in this workspace belongs in `COVERAGE.md`; this skill decides how closely it should be watched and what should trigger the next review.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

这不是“决定研究质量”的表，而是“决定监控强度”的表。真正要避免的是主观化：不能把 coverage 状态绑到“我很喜欢这家公司”或者“conviction 很高”这种感受上。状态必须基于可观察信息：ticker 是否完整、最近是否真的 review 过、有没有明确 trigger、是否已有公司级 artifact、是否需要每日公司新闻扫描。

`coverage-tracker` 管状态，`coverage-monitor` 管发送。前者决定每个名字的 `Coverage` 和 `Monitor`，后者把这张表转成日报和盘中提醒。`coverage-tracker` 不负责异动阈值、news 搜索、important mover explainer、Data Health 或 quote status 呈现。

## 触发场景

- “更新 coverage”
- “重排 coverage 优先级”
- “这家公司现在是 Core Coverage 还是 Building Coverage”
- “把这个名字降成 daily-only”
- “更新 last review / next trigger”
- 任何深度研究、财报准备、财报后复盘之后

## 输出结构

写入 workspace 根目录 `COVERAGE.md`：

```markdown
# Coverage Map

> 本文件是 workspace coverage source of truth。研究过的公司进入表；`coverage-monitor` 消费本表生成日报和盘中提醒。

| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | optical-module-equipment | Core Coverage | Core Watch | 2026-06-20 | 2026-07-15 Q2 results | core name |
| 6777 JP | Santec | optical-module-equipment | Building Coverage | Daily Watch | 2026-06-18 | customer order update | waiting for confirmation |
| IPO pending | Lieqi | optical-module-equipment | Radar | Daily Watch |  | IPO status watch | candidate |
```

字段要求：

| 字段 | 含义 |
|---|---|
| `Coverage` | `Core Coverage` / `Building Coverage` / `Radar` |
| `Monitor` | `Core Watch` / `Daily Watch` |
| `Last Review` | 最近一次真正研究或重大更新日期 |
| `Next Trigger` | 下一个需要回来看这家公司的一句话事件 |

> `Coverage` 和 `Monitor` 必须读取真实状态字段，不得用 subjective conviction 直接代替。

升级规则：

- `stock-quickread` 完成后，若公司进入 `COVERAGE.md`，默认是 `Building Coverage` + `Daily Watch`。
- `alpha-thesis`、`peer-deep-dive`、`earnings-setup`、`scenario-model`、`driver-map`、`catalyst-map` 等 deep-work artifact 完成后，触发 `Core Coverage` review。
- `Building Coverage` 升级到 `Core Coverage` 需要至少一个高强度 artifact，或两个以上 deep-work artifacts，并且 `RESEARCH.md` 有 source map、driver/thesis、next trigger。
- 用户明确说“加入核心覆盖 / Core Watch”时，可以直接升级，但仍要补齐 `Last Review` 和 `Next Trigger`。

## Artifact / 保存策略

写入 workspace 根目录：

```text
COVERAGE.md
```

这是持续维护的 workspace-level memory 表，不生成 dated artifact。

## 与相邻 skill 的边界

- 不写 thesis、不做 variant view → `alpha-thesis`
- 不做催化剂链本体 → `catalyst-map`
- 不发送日报或盘中提醒 → `coverage-monitor`
- 不记录仓位、成本、PnL → 不属于本系统

## 反模式自查

- ❌ 把 `Coverage` 建立在“High conviction”这种主观判断上。
- ❌ 所有名字都给 `Core Coverage`，没有资源分配意义。
- ❌ `Monitor` 和 `Coverage` 完全不区分，导致所有名字都盘中提醒。
- ❌ `Daily Watch` 默认发盘中提醒。
- ❌ 研究产物已经新增，但 `Last Review` 不更新。
- ❌ `Next Trigger` 留空，但又把名字放进 `Core Coverage`。
- ❌ ticker 缺失还放进 `Core Watch`。
- ❌ 只改表格，不在 `research-journal` 或相关研究产物中解释状态变化。
- ❌ 把这张表扩展成 portfolio tracker。

## 篇幅基准

- 这是单表维护 skill，不写长文。
- 用户可见更新说明通常 5-20 行即可。
- `COVERAGE.md` 应保持紧凑；如果 Notes 变成长段分析，说明你把研究 memo 塞错地方了。
