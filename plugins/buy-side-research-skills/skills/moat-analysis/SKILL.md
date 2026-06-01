---
name: moat-analysis
description: Scorecard-based competitive moat analysis with testable evidence.
---

# Moat Analysis

Quantify a company's competitive moat with a scorecard backed by observable evidence. Not a generic "strong brand" narrative.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取三表 + 市场快照。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

moat analysis 最怕写成通用赞美诗。"技术领先"、"品牌强"、"客户粘性高"——每家公司都这么说。真正的壁垒必须有**可检验的证据**：代际精度门槛筛掉竞争对手、客户导入需要 2 年、毛利率持续高于同行 10pp。每个分数后面必须有数字或具体事实。

## 输出结构

```markdown
## Moat Scorecard

| 维度 | 评分(1-10) | 证据 | 持续性判断 |
|---|---|---|---|
| 技术壁垒 | 9 | 贴片精度 ±1m，只有 3 家能做 | 代际升级持续加深 |
| 客户锁入 | 7 | 固晶+耦合成套，替换需 6-12 月 | 中高 |
| 规模效应 | 5 | GT 订单规模比猎奇大 5x | 中 |
| 监管/认证 | 3 | 无特殊壁垒 | 低 |
| 品牌/渠道 | 4 | 瑞典小盘，品牌溢价有限 | 低 |

## 可检验假设

- [ ] 猎奇精度无法达到 ±3m → 观察下季度 1.6T 送样进度
- [ ] CPO 耦合只有 ficonTEC 和 MRSI 在验证 → 跟踪博通 Bailly 供应商公告
```

## 反模式

- ❌ 通用描述不作弊（"技术领先"、"品牌强"无数字支撑）
- ❌ 只打分不写证据
- ❌ 不作 peer 对标
- ❌ 把 moat = market share（份额 ≠ 护城河）

## 篇幅基准

600-1000 字 + 1 scorecard 表 + 3-5 可检验假设。

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| mechanism-insight | 技术壁垒证据 |
| driver-map | 规模/成本优势证据 |
| company-history | 历史竞争位演变 |
| peer-deep-dive | 同行对标 |

| 下游 | 场景 |
|---|---|
| alpha-thesis | moat 判断 → thesis 核心论点 |
