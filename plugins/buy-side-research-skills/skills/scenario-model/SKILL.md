---
name: scenario-model
description: Quantify scenario thesis — TAM x share x margin x PE = implied market cap with source-tracked assumptions.
---

# Scenario Model

Turn a scenario thesis into quantified sizing. Not a 3-statement-model replacement — fast envelope math that forces every assumption onto the table where it can be challenged.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `skills/_shared/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取 baseline 三表 + 市场快照。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes and calculates.

## 心法

Scenario model 的真正价值不是那个 upside 数字——是**暴露哪个假设最值得花时间验证**。一个 $7.2B implied market cap 如果建立在 "TAM $1.2B, share 60%, PE 40x" 上，而 share 60% 的来源只是 "他是龙头"——这个数字就是垃圾。但如果 sensitivity 表告诉你"share 从 60% 降到 40%，upside 从 148% 降到 100%"，你就知道 share assumption 是稳健的。**这才是 scenario model 的产出：不是答案，是一张"你最该验证什么"的地图。**

最容易死在哪：agent 搜到一个 TAM 数字就复用，不追问"这个 TAM 是从哪个源来的、可能偏大还是偏小、用在这个场景里合不合理"。

## 触发场景

- "如果 CPO 渗透 15% AEHR 能涨多少"
- "算 MYCR bull/base/bear 理论市值"
- "这个场景下推的票，最坏情景能跌到哪"
- "倒推：要值 $5B，需要多少 CPO 订单"

## 输入澄清

每个输入必须有 derivation path。agent 沿着 path 找，找不到就降级标注。

| 字段 | 去哪找（Derivation Path） | 找不到时 |
|---|---|---|
| **TAM** | 1. `market-sizing` artifact → 2. 招股书/年报引用第三方报告 → 3. WebSearch 行业报告 → 4. 公司 IR presentation | 标 [agent推算, Tier 2]，写推算逻辑 |
| **目标份额** | 1. `mechanism-insight` 竞争格局（当前台数/金额份额）→ 2. 客户财报里的 supplier concentration → 3. 行业峰会/产品发布 → 4. 对标相似行业新生市场的 leader 份额 | 至少给 high/low range，不拍单点 |
| **目标 Margin** | 1. `financial-data` actuals 当前 margin → 2. 同行业 scale effect benchmark（revenue doubling 时 margin 通常 improve 多少）→ 3. peer 可比产品线 margin | 默认 = 当前 margin |
| **目标 PE** | 1. `comps-analysis` 同组 forward PE → 2. `peer-deep-dive` valuation table → 3. 公司自身 3 年 PE range → 4. 同行业同等 growth rate 公司的 PE | 必填 |
| **当前估值** | `financial-data --lite` market_data | — |

> Tier 0（机器验证）= actuals / Bridge。Tier 1（trusted 第三方）= Frost/Gartner cited in 官方文件。Tier 2（agent 推算）= 有 derivation 但未经第三方验证。所有 Tier 2 假设必须写推导过程，由研究员确认后进测算。

## 执行流程

```
Phase 1: 沿着 derivation path 找数据 → 假设表（每行有 source/tier/confidence）

Gate:
  所有 Tier 0/1 + upside >20% → 自动进 Phase 2
  有 Tier 2 + upside >50% → 值得做，标注 [待确认] 后进 Phase 2
  全是 Tier 2 + upside <20% → 告诉研究员"不值得做，因为即使最乐观假设也赚不到 20%"
  最极端的情景即使 hit 了也毁不掉 thesis → 不浪费研究员时间

Phase 2: 测算 → sensitivity（相关性标注）→ 判断"最值得验证的假设是哪个"
```

## 测算方法

### 计算链

```
                    ┌──────────────┐
                    │  场景 TAM     │  ← market-sizing / 招股书 / WebSearch
                    │  e.g. $1.2B  │
                    └──────┬───────┘
                           │ × 目标份额 (60%)
                           ▼
                    ┌──────────────┐
                    │  场景收入     │  ← mechanism-insight 竞争格局支撑份额
                    │  $720M       │
                    └──────┬───────┘
                           │ × 目标 Margin (25%)
                           ▼
                    ┌──────────────┐
                    │  场景利润     │  ← financial-data actuals → 当前 margin ± 场景变化
                    │  $180M       │
                    └──────┬───────┘
                           │ × 目标 PE (40x)
                           ▼
                    ┌──────────────┐
                    │  场景市值     │  ← comps-analysis 同组 forward PE 中位
                    │  $7.2B       │
                    └──────┬───────┘
                           │ ÷ 当前市值 ($2.9B)
                           ▼
                    ┌──────────────┐
                    │  Upside      │
                    │  +148%       │
                    └──────────────┘

每步右侧标注了该输入的标准 derivation path。
如果某一步用的是 Tier 2（agent推算），连线变成虚线。
```

### 标准路径

```
场景收入 = TAM × 目标份额
场景利润 = 场景收入 × 目标 Margin
场景市值 = 场景利润 × 目标 PE
Upside = (场景市值 - 当前市值) / 当前市值
```

### Reverse 路径（研究员问"值 $X 需要什么"）

```
所需利润 = 目标市值 / 目标 PE
所需收入 = 所需利润 / 目标 Margin
所需订单量 = 所需收入 / ASP
→ 对比当前：翻几倍？合理吗？
```

Agent 根据用户 query 自动判定方向。

### Sensitivity 规则

**变量之间不独立。这是最容易犯的错。** 如果把 TAM 和 share 当成独立变量做 sensitivity——"TAM 涨 50%，share 不变"——等于假设市场变大但竞争不增加。这是错的。

正确做法：
- TAM 涨 → 通常意味着该市场更 attractive → 竞争加剧 → share 可能降。标注这个相关性
- Margin 涨 → 通常需要 scale → 可能已经隐含在 TAM 增长假设里
- PE 涨 → 通常意味着市场对增长的 confidence 提高 → 和 TAM/收入增速有相关性

在 sensitivity 表里用脚注标注相关性："TAM ↑ 50% 的情况下，share 大概率会从 60% 降到 45-50%"

## 输出结构

```markdown
## Assumptions

| 假设 | 值 | 来源 | Tier | Confidence | 最容易在哪错 |
|---|---|---|---|---|---|
| TAM | $1.2B | Frost via 招股书 | 1 | Medium | Frost 在 IPO 招股书里通常偏大 20-30% |
| 份额 | 60% | AEHR 当前 100% wafer burn-in | 2 | Low | 如果 Teradyne/Keysight 进入会不会降？ |
| Margin | 25% | 当前 22% + scale effect | 2 | Medium | Scale margin improvement 可能在 3-5% 不是 3% |
| PE | 40x | Semi equipment peers 2028 forward PE | 1 | Medium | 如果 CPO 推迟，semi equipment 整体 de-rate |

## Calculation

| Step | Value |
|---|---|
| 场景收入 | $720M |
| 场景利润 | $180M |
| 场景市值 | $7.2B |
| 当前市值 | $2.9B |
| **Upside** | **+148%** |

## Sensitivity

| 变量 | Bear | Base | Bull | 相关性 |
|---|---|---|---|---|
| TAM | $0.8B | $1.2B | $1.5B | ↑TAM → ↓share 压力 |
| 份额 | 40% | 60% | 75% | ↑share → ↓margin 可能（价格竞争） |
| PE | 25x | 40x | 50x | ↑PE 需要 catalyst 确认 |

Bull case composite: +200% (if all hit)
Bear case composite: +60% (if only TAM/PE moderate)

## Visual

**Sensitivity Bridge** (ASCII or research-viz):
```
Base Upside: +148%
  │
  ├─ TAM +25%      → +30pp   (independent)
  ├─ Share +15pp   → +25pp   (partially correlated with TAM)
  ├─ PE +10x       → +35pp   (requires catalyst confirmation)
  └─ Margin +3pp   → +10pp   (scale effect, correlated with TAM)
  ─────────────────────────
  Bull Composite:  +248%  (if all hit, less correlation overlap)
  Bear Composite:   +60%  (TAM+PE moderate, share at low end)
```
标注每个变量的独立贡献和相关性，帮助研究员判断"哪个假设值得花时间验证"。
```

> 如果用户请求 bull/base/bear，输出三个独立的以上结构。如果请求 reverse，倒推输出。

## 反模式

- ❌ 假设没有 derivation path——"TAM $1.2B" 是哪来的？
- ❌ 把独立 sensitivity 当成真实情景——不标注变量间相关性
- ❌ Tier 2 假设不写推导过程
- ❌ "估值 flip 150%" 但所有假设都是 Tier 2——纯编
- ❌ 算完不回写调用方
- ❌ 目标 PE 没有可比性说明——"40x" 和谁比？
- ❌ 最乐观情景 upside 都 <20% 还交差——应该直接说"不值的算"
- ❌ 不出"最值得验证的假设"——sensitivity 白做了
- ❌ 精度假象——TAM $1,234M 但 share 是拍脑袋

## 判断标准

算完问自己：
- [ ] 如果明天 share assumption 被证明错了，upside 会怎样？
- [ ] 三个假设里哪个如果错了 upside 直接归零？
- [ ] 当前市场是不是已经在 price 这个场景了？（看当前 PE 和 scenario PE 的 gap）

## 篇幅基准

300-600 字 + 1 假设表 + 1 测算表 + 1 sensitivity 表。

## Workflow 联动

| 方向 | Skill | 取/给什么 |
|---|---|---|
| 上游 | `market-sizing` | TAM |
| 上游 | `financial-data` | baseline |
| 上游 | `mechanism-insight` | 份额依据 |
| 上游 | `comps-analysis` | PE 锚 |
| 下游 | `candidate-screener` | 量化场景推票 |
| 下游 | `alpha-thesis` | bull/bear sizing |

## 与相邻 skill 的边界

- 不做 TAM 拆解 → `market-sizing`
- 不做三表 → `3-statement-model`
- 不做 DCF → `dcf-model`
