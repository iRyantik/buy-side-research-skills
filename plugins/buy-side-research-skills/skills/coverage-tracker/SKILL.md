---
name: coverage-tracker
description: Lightweight coverage state tracking — thesis stage, last review, next catalyst trigger, and priority.
---

# Coverage Tracker

Lightweight coverage state at workspace root. Tracks thesis stage, review dates, and priority — not portfolio positions. Companion to `research-journal`: tracker manages state, journal manages earned insight.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- 本 skill 不调用 financial-data；只读写 `coverage.md`。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

Coverage tracker 回答的不是"我们有什么仓"，而是"我们此时此刻该把研究时间花在哪"。好的 tracker 不是 CRM——不是"上次看是什么时候"，而是"上次看完判断变了什么"。每个 ticker 的 state transition 必须有原因。

和 research-journal 的分工：journal 是"我发现了一个新认知"，tracker 是"因为那个新认知，MYCR 从 active 变成 monitoring"。

## Thesis Stages

5 个 stage，有明确 transition 条件。不能让 agent 把一切标成 active。

| Stage | 定义 | Transition 条件 |
|---|---|---|
| **building** | 正在收集信息，没有方向性判断 | 完成了 stock-quickread + at least 1 deep-work skill |
| **testing** | 方向形成、正在验证 | driver-map/moat-analysis 有至少 3 个 Hard evidence |
| **active** | Conviction thesis，密切监控 | 有 written thesis (alpha-thesis) 且 catalyst 在 6 个月内 |
| **monitoring** | Thesis 成立但 no urgency | Catalyst >6 个月 away，或等待外部验证 |
| **dormant** | Thesis 破了或暂时不值得花时间 | Kill criteria 触发，或优先级被更重要的挤掉 |

**Transition 触发**：
- building → testing：至少完成 stock-quickread + 1 deep-work
- testing → active：形成 thesis + catalyst 在 6M 内
- active → monitoring：catalyst 推迟 >6M
- active → dormant：thesis broken 或 kill criteria hit
- dormant → building：新的外部变化（政策/tech/竞争）触发了重新审视
- monitoring → dormant：不确定超过 12M，不值得继续跟踪

## 输出结构

`coverage.md`，workspace 根目录，单表：

~~~markdown
## Coverage

| Ticker | Company | Stage | Last Review | Last Change | Next Trigger | Priority | Why Priority |
|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | active | 2026-06-01 | testing→active (alpha-thesis done) | Q2 GT orders | High | Catalyst in 3M; thesis fresh |
| BESI NA | Besi | testing | 2026-05-15 | building→testing (moat done) | TSMC COUPE 2027 | Medium | Catalyst 12M away |
| 688808 | 联讯仪器 | monitoring | 2026-05-20 | — | PE <200x or CPO news | High | Bubble watch; 500x PE |
| 300757 | 罗博特科 | building | 2026-05-10 | — | ficonTEC Q orders | Low | Data not yet pulled |

## Recent Changes

| Date | Ticker | Change | Reason |
|---|---|---|---|
~~~

| 2026-06-01 | MYCR SS | testing → active | Alpha thesis completed |
| 2026-05-15 | BESI NA | building → testing | Moat analysis done; early thesis forming |

## 反模式

- ❌ Stage 不更新——做完 alpha-thesis 还是 testing
- ❌ 所有 ticker 都是 active——必须分级
- ❌ 没有 transition reason——"变了"不够，"因为什么"必须写
- ❌ Priority 全是 high——至少给具体原因
- ❌ 记持仓/盈亏——这不是 portfolio tracker
- ❌ 不联 journal——tracker 和 journal 各自独立

## 篇幅基准

单表，持续更新。不生成 dated artifact。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| `candidate-screener` | 初始 candidate list |
| `research-journal` | Stage transition 触发 |
| `stock-quickread` / deep-work skills | 每次 review 后更新 |

| 下游 | 场景 |
|---|---|
| 研究员 | 每周决定把时间花在哪 |

