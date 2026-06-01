---
name: capital-allocation
description: Scorecard-based capital allocation analysis with 10Y track record.
---

# Capital Allocation

Score management's capital allocation quality — buyback timing, dividend sustainability, M&A ROI, and capex effectiveness over a 10-year window.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker> --periods 10Y` 获取 10 年三表 + 市场快照。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

管理层最重要的决策不是战略——是钱花在哪。同一个行业、同一条赛道，资本配置好和差的管理层可以差 3-5x 市值。本 skill 的衡量标准是"每一块钱赚回多少"。

## 输出结构

```markdown
## Capital Allocation Scorecard

| 维度 | 评分(1-10) | 10Y 证据 |
|---|---|---|
| Buyback Timing | 7 | 2020/2023 低位回购，2025 高位未回购 |
| Dividend Policy | 8 | 连续 10 年增长，payout ratio 30-40% |
| M&A ROI | 9 | MRSI 并购 ($125M → 现在占收入 30%+) |
| Capex Efficiency | 6 | ROIC 15-18%，周期波动大 |

## 管理层画像

- 风格：disciplined acquirer，不烧钱扩张
- 最大风险：并购依赖（下次并购能不能复制 MRSI 的成功？）
```

## 反模式

- ❌ 不看 10 年只看最近两年
- ❌ buyback 不查时机（高位回购 = 毁灭价值）
- ❌ M&A 不追问"这笔交易的 ROI 到底多少"
- ❌ 打分无数字支撑

## 篇幅基准

500-800 字 + 1 scorecard。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| financial-data --periods 10Y | CF: buyback/dividend/capex/M&A |
| company-history | 并购整合记录 |

| 下游 | 场景 |
|---|---|
| alpha-thesis | 管理层可信度 → thesis conviction |
| stock-quickread | 快速扫描后跳转深入 |
