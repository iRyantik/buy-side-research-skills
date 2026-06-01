---
name: catalyst-map
description: Full timeline catalyst chain with probability-weighted impact per event.
---

# Catalyst Map

Map every catalyst on a timeline—not just "what might happen" but "when, how likely, which direction, how big, and what does it mean for the thesis."

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取三表 + 市场快照。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

好的 catalyst map 不是时间表—而是概率加权的 payoff 矩阵。"Q2 财报"不是 catalyst，"Q2 财报里 GT 订单超 SEK 350M 概率 40% → +15% 股价"才是。

## 输出结构

```markdown
## Catalyst Timeline

| 时间 | 事件 | 概率 | 方向 | 幅度 | 影响票 | 对 thesis 的影响 |
|---|---|---|---|---|---|---|
| 2026 Q3 | Q2 GT 订单 >SEK 350M | 40% | ↑ | +15% | MYCR | 验证 1.6T 升级驱动 |
| 2027 H1 | 猎奇专利败诉 | 30% | ↑ | +20% | MYCR | 竞争出清 |

## 概率加权 12M Impact

- 上行加权: +20% (各 catalyst 概率×幅度加总)
- 下行加权: -10%
- Net: +10%
```

## 反模式

- ❌ "Q2 财报" 当作 catalyst——太泛
- ❌ 没有概率估计
- ❌ 只有上行、没下行 catalyst
- ❌ 不和 thesis 联动（每个 catalyst 要说明对 thesis 的影响）

## 篇幅基准

400-800 字 + 1 核心表 + timeline 描述。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| consensus-map | 市场预期 vs 可能事件 |
| financial-data | baseline 数据 |
| earnings-setup | 财报节点 |

| 下游 | 场景 |
|---|---|
| alpha-thesis | catalyst → thesis 时间线和置信度 |
| candidate-screener | §6 catalyst 日历增强 |
