---
name: coverage-tracker
description: Lightweight coverage state tracking — thesis stage, last deep dive, next catalyst, priority.
---

# Coverage Tracker

Lightweight coverage state tracker at workspace root. Tracks thesis stage, review dates, and priority — not portfolio positions. Works alongside research-journal: tracker manages state, journal manages earned insight.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- 本 skill 不调用 financial-data；只读写 `coverage.md`。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

coverage-tracker 不是 portfolio tracker——不记持仓、不记仓位、不记盈亏。它只回答一个简单问题："我们现在在看哪些公司？状态如何？下次什么时候重看？" 和 research-journal 的分工：tracker 管状态，journal 管认知。

## 输出结构

```markdown
## Coverage

| Ticker | Company | Thesis Stage | Last Deep Dive | Next Catalyst | Priority | Notes |
|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | active | 2026-06-01 | 2026 Q3 GT orders | High | waiting for Q2 report |
| BESI NA | Besi | testing | 2026-05-15 | 2027 TSMC COUPE | Medium | early thesis forming |
| 688808 CH | 联讯仪器 | monitoring | 2026-05-20 | 2026 Q3 report | High | PE 505x bubble watch |

## Thesis Stages

- building: gathering data, no thesis yet
- testing: thesis forming, evidence collecting
- active: conviction thesis, monitoring
- monitoring: thesis active but no urgency
- dormant: paused, not actively researching
```

## 反模式

- ❌ 记持仓/盈亏——这不是 portfolio tracker
- ❌ thesis stage 不更新（做完 alpha-thesis 还是 building）
- ❌ priority 全是 high——必须分级
- ❌ 不和 research-journal 联动

## 篇幅基准

一页表，持续更新。不生成 dated artifact。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| candidate-screener | 初始 candidate population |
| research-journal | thesis 状态变更提示 |

| 下游 | 场景 |
|---|---|
| 研究员 | 每周看 coverage 决定这周花时间在哪 |
