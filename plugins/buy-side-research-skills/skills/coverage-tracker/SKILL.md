---
name: coverage-tracker
description: Auto-maintained coverage state tracking — tier, direction, conviction, stage, next trigger. Any company researched in the workspace is covered.
---

# Coverage Tracker

Auto-maintained coverage state at workspace root. Not portfolio positions — research state machine. Any company that has an artifact in this workspace is automatically in the table. Companion to `research-journal`: tracker manages state, journal manages earned insight.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — 数据获取链、来源验证链、证据协议、产出合约、保存合约。
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## 心法

你不是在"决定覆盖谁"——你是在"标记状态"。任何在这个 workspace 里被研究过的公司（有任何 artifact 写在 `industry/<industry>/companies/<ticker>/` 下），自动属于你的 coverage。COVERAGE.md 的存在不需要主动创建——首次写入公司-level artifact 时自动创建（若无）并加 entry。

分 Tier 是你唯一的主动决策：**有些公司值得每周盯，有些不值得。** Tier 是资源分配，不是研究质量评级。一张表里 Tier 2 比 Tier 1 多才是正常的。

Direction 和 Conviction 自动从上游 skill 同步（candidate-screener→direction，alpha-thesis→conviction），不重复录入。Stage 随研究进展自动推进，只有 downgrade（active→monitoring→dormant）需要手动确认。

## 触发场景

- "更新 coverage"
- "coverage 里 MYCR 状态是什么"
- "重排 coverage 优先级"
- "把 BESI 升到 Tier 1"
- "把联讯降 dormant——CPO 远远没到"
- 任何深看后自动提示更新

## 自动创建规则

任何 skill 写入 `industry/<industry>/companies/<ticker>/` 时：

1. 检查 workspace 根目录是否有 `COVERAGE.md`
2. 没有 → 创建空表 + 加该 ticker，stage=building, tier=3
3. 有 → 查表里有没有这个 ticker
   - 没有 → 加一行，stage=building, tier=3
   - 有 → 不自动修改

## 输出结构

`COVERAGE.md`，workspace 根目录：

~~~markdown
## Coverage

| Ticker | Company | Tier | Direction | Conviction | Stage | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | 1 | Long | High | active | 2026-06-01 | Q2 GT orders | Alpha thesis done; catalyst in 3M |
| BESI NA | Besi | 2 | Long | Medium | testing | 2026-05-15 | TSMC COUPE 2027 | Early thesis; waiting on TSMC |
| 688808 | 联讯仪器 | 2 | Short | High | monitoring | 2026-05-20 | PE <200x or CPO news | Bubble watch; thesis holds |
| 300757 | 罗博特科 | 3 | — | — | building | 2026-05-10 | ficonTEC Q orders | Too early; data not yet pulled |
~~~

## 字段说明

| 字段 | 谁填 | 值 |
|---|---|---|
| **Tier** | 研究员 | `1` = 本周花时间在这 / `2` = 定期跟踪，等 catalyst / `3` = radar 边缘观察 |
| **Direction** | 自动（可手动改）| Long / Short / —（未形成方向）。自动来源：candidate-screener 的 L/S 方向、alpha-thesis 的 thesis direction |
| **Conviction** | 自动（可手动改）| High / Medium / Low / —。自动来源：alpha-thesis 的 conviction level |
| **Stage** | 自动+手动 | `building` → `testing` → `active` → `monitoring` → `dormant` |
| **Last Review** | 自动 | 最近一次深度研究 artifact 的日期 |
| **Next Trigger** | 自动 | catalyst-map 的最近 catalyst |

## Thesis Stages

| Stage | 定义 | Transition 触发 |
|---|---|---|
| **building** | 刚出现在 workspace 里，正在收集信息 | 自动——任何 skill 首次写入公司目录 |
| **testing** | 方向形成、正在验证 | 完成 stock-quickread + 至少 1 个 deep-work skill（自动） |
| **active** | 有 conviction thesis，密切监控 | alpha-thesis 写完（自动） |
| **monitoring** | thesis 成立但 no urgency | catalyst >6M away，或研究员手动降级 |
| **dormant** | thesis 破了或不值得花时间 | kill criteria 触发，或研究员手动降级 |

## 反模式

- ❌ 不做 auto-create——没建表就没 coverage
- ❌ Stage 永远 building——做了 alpha-thesis 还不更新
- ❌ 所有 ticker 都是 Tier 1——不分级等于没做资源分配
- ❌ Direction/Conviction 不自动同步——需要研究员手动填已经在 candidate-screener 里给过的方向
- ❌ 记持仓/盈亏——这不是 portfolio tracker
- ❌ 不联 research-journal——stage 变了但 journal 里没说明为什么

## 篇幅基准

单表，持续更新。不生成 dated artifact。

## Workflow 联动

| 上游 | 自动取什么 |
|---|---|
| 任何 skill 写入公司目录 | 自动创建 entry（ticker + stage=building） |
| `candidate-screener` | Direction（L/S）+ Tier 参考 |
| `alpha-thesis` | Conviction |
| `catalyst-map` | Next Trigger |
| `research-journal` | Stage transition 触发原因 |

| 下游 | 场景 |
|---|---|
| 研究员 | 每周看 Tier 1 + Next Trigger，决定本周时间分配 |

## 与相邻 skill 的边界

- 不做 investment thesis → `alpha-thesis`
- 不做 catalyst tracking → `catalyst-map`
- 不做 portfolio tracking → 这不是持仓表
