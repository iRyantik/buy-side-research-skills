---
name: scenario-model
description: Quick scenario sizing — TAM x share x margin x PE = implied market cap.
---

# Scenario Model

Turn a scenario thesis ("CPO >15% → Long AEHR") into quantified sizing: incremental revenue → profit → implied market cap → upside vs current.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取三表 + 市场快照。信任其结果，直接从 `actuals-resolved.json` 取数。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

Scenario model 不是完整三表模型，而是**快速信封背面测算**——用最少的假设算出方向性判断。如果假设错了，结论可能翻——所以 Phase 1 必须先暴露假设。Phase 2 只在假设经研究员确认后才执行。

## 两 Phase 流程

### Phase 1: 找数据 + 出假设表

Agent 搜索 TAM、份额、margin 依据 → 输出假设表。研究员审。

### Phase 2: 测算

```
场景 TAM × 公司份额 = 场景收入
场景收入 × 目标 margin = 场景利润
场景利润 × 目标 PE = 场景市值
vs 当前市值 = upside/downside %
```

**Gate 规则**：
- 所有假设 Tier 0 → auto pass
- 有 Tier 1 → warn + auto pass
- 有 Tier 2（研究员假设）→ block，等 confirm

## 输出结构

```markdown
## Phase 1: 假设表

| 假设 | 值 | 来源 | Tier | 替代情景 | Confidence |
|---|---|---|---|---|---|
| CPO burn-in TAM 2028 | $1.2B | market-sizing | 1 | $0.8B bear | Medium |
| AEHR share | 60% | mechanism-insight 竞争格局 | 2 | 40% | Low |
| Target margin | 25% | 当前 margin + peer | 1 | — | Medium |
| Target PE | 40x | comps-analysis 同组中位 | 1 | 25x bear | Medium |

## Phase 2: 测算

| Step | 计算 | 值 |
|---|---|---|
| 场景收入 | $1.2B × 60% | $720M |
| 场景利润 | $720M × 25% | $180M |
| 场景市值 | $180M × 40x | $7.2B |
| 当前市值 | — | $2.9B |
| **Upside** | $7.2B / $2.9B - 1 | **+148%** |
```

## 反模式

- ❌ Phase 1 假设表未审直接出 Phase 2 数字
- ❌ 精度假象：TAM 拍到 $1.234B 但份额纯猜
- ❌ 不回写 candidate-screener（算完要填回调用方）
- ❌ 每个假设不标 Tier + source

## 篇幅基准

Mode A (quick): 300-500 字 + 1 表
Mode B (multi-scenario): 500-1000 字 + 2-3 表

## Workflow 联动

| 上游 | 取什么 |
|---|---|
| market-sizing | TAM 数据 |
| financial-data | baseline 收入/利润/市值 |
| mechanism-insight | 竞争格局 → 份额依据 |
| comps-analysis | 目标 PE 锚 |

| 下游 | 场景 |
|---|---|
| candidate-screener | 量化 §4.2 场景推票表 |
| alpha-thesis | bull/bear case sizing |
| pair-trade | spread 回报测算 |
