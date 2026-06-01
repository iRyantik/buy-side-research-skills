---
name: market-sizing
description: Bottom-up TAM SAM SOM estimation with source-quality annotations.
---

# Market Sizing

Turn a vague "how big is this market" question into a structured bottom-up TAM/SAM/SOM estimate with source quality annotations for every assumption.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取三表 + 市场快照。信任其结果，直接从 `actuals-resolved.json` 取数。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

TAM 估算最容易犯的错误不是算错数字，而是把拍脑袋的数字写成确定事实。本 skill 的核心产出不是"一个数"——而是**可追溯的拆解表**：每一行有来源、有置信度、有替代假设。

## 触发场景

- "CPO 设备市场有多大"
- "光模块 burn-in test TAM 多少"
- "帮我拆一下 this market 的空间"
- market-sizing keyword: TAM, market size, 市场空间, 市场规模

## 输出结构

```markdown
## TAM 拆解

| Segment | 2026 TAM | 2028E TAM | Growth CAGR | Source | Tier | Confidence |
|---|---|---|---|---|---|---|
| CPO burn-in test | $0.2B | $1.2B | 145% | Frost via 猎奇招股书 | 1 | Medium |
| ... | ... | ... | ... | ... | ... | ... |

## SAM (addressable by [Company])

| Company | Segment | Share rationale | SAM $ | Basis |
|---|---|---|---|---|

## 关键假设

| 假设 | 值 | 替代情景 | 影响 |
|---|---|---|---|

## Sources
```

## 反模式

- ❌ 只输出一个数字（"TAM $1.2B"）没有拆解表
- ❌ 每行没有 source + Tier 标注
- ❌ TAM/SAM/SOM 混用不区分
- ❌ 把第三方报告的数字当确定事实，不标 confidence

## 篇幅基准

500-1200 字 + 1-2 张拆解表。

## Workflow 联动

| 下游 | 场景 |
|---|---|
| scenario-model | 喂 TAM 给场景测算 |
| candidate-screener | 给行业排序提供市场规模语境 |
| industry-landscape | TAM 可以写入行业 index |
