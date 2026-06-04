---
name: scenario-model
description: Quantify a scenario thesis into a verdict-first odds memo with bull/base/bear sizing and source-tracked assumptions.
---

# Scenario Model

Turn a scenario thesis into a verdict-first odds memo. Not a 3-statement-model replacement and not a full thesis writer — fast envelope math that forces every assumption onto the table where it can be challenged.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — 数据获取链、来源验证链、证据协议、产出合约、保存合约。
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## 心法

Scenario model 的真正价值不是那个 upside 数字，而是 **暴露哪个假设最值得花时间验证**。一个 $7.2B implied market cap 如果建立在 "TAM $1.2B, share 60%, PE 40x" 上，而 share 60% 的来源只是 "他是龙头"，这个数字就是垃圾。但如果 sensitivity 表告诉你 "share 从 60% 降到 40%，upside 从 148% 降到 100%"，你就知道 share assumption 还算稳健。这个 skill 的产出不是最终答案，而是一张“你最该验证什么”的地图。

最容易死在哪：agent 搜到一个 TAM 数字就复用，不追问这个 TAM 是从哪个源来的、可能偏大还是偏小、用在这个场景里合不合理。

## 触发场景

- "如果 CPO 渗透 15% AEHR 能涨多少"
- "算 MYCR bull/base/bear 理论市值"
- "这个场景下推的票，最坏情景能跌到哪"
- "倒推：要值 $5B，需要多少 CPO 订单"
- "这个逻辑赔率够不够，值不值得继续做 thesis"
- "最值得验证的假设是哪一个"

## 输入澄清

每个输入必须有 derivation path。agent 沿着 path 找，找不到就降级标注。

| 字段 | 去哪找（Derivation Path） | 找不到时 |
|---|---|---|
| **TAM** | 1. `market-sizing` artifact（优先）→ 2. 招股书/年报引用第三方报告 → 3. WebSearch 行业报告 → 4. 公司 IR presentation | 标 `[agent推算, Tier 2]`，写推算逻辑 |
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
  全是 Tier 2 + upside <20% → 告诉研究员“不值得做，因为即使最乐观假设也赚不到 20%”
  最极端的情景即使 hit 了也毁不掉 thesis → 不浪费研究员时间

Phase 2: 测算 → sensitivity（相关性标注）→ 给出 verdict 和最值得验证的假设
```

## 与相邻 skill 的边界

- `market-sizing` 仍是 TAM/SAM/SOM 主 skill。`scenario-model` 优先复用它；如果没有现成 TAM artifact，才允许做最小 TAM derivation，并显式标 Tier。
- `alpha-thesis` 仍是完整 thesis skill。`scenario-model` 只输出 odds memo，不接管完整 variant view、catalyst narrative、kill criteria。
- `dcf-model` 仍是完整 valuation workbook。`scenario-model` 不做 full forecast、WACC、terminal value 或完整 workbook。
- `3-statement-model` 仍负责三表联动。`scenario-model` 只做 envelope math。

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
如果某一步用的是 Tier 2（agent 推算），连线变成虚线。
```

### 标准路径

```
场景收入 = TAM × 目标份额
场景利润 = 场景收入 × 目标 Margin
场景市值 = 场景利润 × 目标 PE
Upside = (场景市值 - 当前市值) / 当前市值
```

### Reverse 路径（研究员问“值 $X 需要什么”）

```
所需利润 = 目标市值 / 目标 PE
所需收入 = 所需利润 / 目标 Margin
所需订单量 = 所需收入 / ASP
→ 对比当前：翻几倍？合理吗？
```

Agent 根据用户 query 自动判定方向。

### Sensitivity 规则

**变量之间不独立。** 如果把 TAM 和 share 当成独立变量做 sensitivity，等于假设市场变大但竞争不增加，这是错的。

正确做法：
- TAM 涨 → 通常意味着该市场更 attractive → 竞争加剧 → share 可能降。标注这个相关性
- Margin 涨 → 通常需要 scale → 可能已经隐含在 TAM 增长假设里
- PE 涨 → 通常意味着市场对增长的 confidence 提高 → 和 TAM/收入增速有相关性

在 sensitivity 表里用脚注标注相关性，例如：“TAM ↑ 50% 的情况下，share 大概率会从 60% 降到 45-50%”。

## 输出结构（固定为 odds memo）

> **Source contract**：所有 Implied Value、Upside/Downside %、Calculation 数字、Sensitivity 场景值必须带 source anchor。Assumptions 表已有 来源+Tier 列，其他数字表一律加 Ev。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | Assumptions 表 | 每行 assumption 的来源+Tier+Confidence | 假设本身 |
> | Odds memo 正文 | 每个 % 概率/涨跌幅背后的数据锚点 | 研究员概率判断 |
> | Sensitivity 表 | 每个场景的 PE/EV 倍数来源 | — |
>
> **完成 Gate**：写完扫 assumptions 表 → 每行有 source tier → 引用 actuals 的标 `[S1]`→Resources、引用外部的标 `[I#]`→Resources → `[待查]` assumption ≤3。

~~~markdown
## Scenario Verdict

- 一句话判断：值得继续 / 赔率一般 / 不值得继续
- 当前价格相对 Base / Bull / Bear 的位置

## Bull / Base / Bear Table

| Case | Key Assumptions | Implied Value | Upside / Downside | Why it matters | Ev |
|---|---|---|---|---|
| Bull | ... | ... | ... | ... |
| Base | ... | ... | ... | ... |
| Bear | ... | ... | ... | ... |

## Current Setup

- 当前市值 / 当前估值锚
- 当前市场大致隐含了什么

## Assumptions

| 假设 | 值 | 来源 | Tier | Confidence | 最容易在哪错 |
|---|---|---|---|---|---|
| TAM | $1.2B | Frost via 招股书 | 1 | Medium | Frost 在 IPO 招股书里通常偏大 20-30% |
| 份额 | 60% | AEHR 当前 100% wafer burn-in | 2 | Low | 如果 Teradyne/Keysight 进入会不会降？ |
| Margin | 25% | 当前 22% + scale effect | 2 | Medium | Scale margin improvement 可能在 3-5% 不是 3% |
| PE | 40x | Semi equipment peers 2028 forward PE | 1 | Medium | 如果 CPO 推迟，semi equipment 整体 de-rate |

## Calculation

| Step | Value | Ev |
|---|---|
| 场景收入 | $720M |
| 场景利润 | $180M |
| 场景市值 | $7.2B |
| 当前市值 | $2.9B |
| **Upside** | **+148%** |

## Sensitivity

| 变量 | Bear | Base | Bull | 相关性 | Ev |
|---|---|---|---|---|
| TAM | $0.8B | $1.2B | $1.5B | ↑TAM → ↓share 压力 |
| 份额 | 40% | 60% | 75% | ↑share → ↓margin 可能（价格竞争） |
| PE | 25x | 40x | 50x | ↑PE 需要 catalyst 确认 |

## What Matters Most

- 最关键的 1-3 个假设
- 每个假设的 source tier / confidence
- 哪个假设一旦错了会让赔率明显塌掉

## Research Priority

- `go alpha-thesis`
- `go market-sizing`
- `go dcf-model`
- `stop`

## Reverse Check

仅当用户问倒推时输出：
- 要值到目标市值，需要多少收入 / 份额 / margin / multiple
- 哪个条件最不现实
~~~

默认定位：
- 短、硬、判断导向
- 重点是赔率与假设优先级
- 不是长篇 thesis
- 不是半模型 workbook

## 反模式

- ❌ 假设没有 derivation path——“TAM $1.2B” 是哪来的？
- ❌ 把独立 sensitivity 当成真实情景——不标注变量间相关性
- ❌ Tier 2 假设不写推导过程
- ❌ “估值 flip 150%” 但所有假设都是 Tier 2——纯编
- ❌ 目标 PE 没有可比性说明——“40x” 和谁比？
- ❌ 最乐观情景 upside 都 <20% 还交差——应该直接说“不值的算”
- ❌ 不出 `What Matters Most` 或 `Research Priority`
- ❌ 精度假象——TAM $1,234M 但 share 是拍脑袋

## 判断标准

算完问自己：
- [ ] 如果明天 share assumption 被证明错了，upside 会怎样？
- [ ] 三个假设里哪个如果错了 upside 直接归零？
- [ ] 当前市场是不是已经在 price 这个场景了？（看当前 PE 和 scenario PE 的 gap）
- [ ] 这个 memo 的下一步是 `alpha-thesis`、`dcf-model`、`market-sizing` 还是直接停止？

## 篇幅基准

300-700 字 + 1 bull/base/bear 表 + 1 假设表 + 1 sensitivity 表。

## Workflow 联动

| 方向 | Skill | 取/给什么 |
|---|---|---|
| 上游 | `market-sizing` | TAM |
| 上游 | `financial-data` | baseline |
| 上游 | `mechanism-insight` | 份额依据 |
| 上游 | `comps-analysis` | PE 锚 |
| 下游 | `candidate-screener` | 量化场景推票 |
| 下游 | `alpha-thesis` | bull/base/bear sizing + odds framing |


## Appendix: Financial Data

Artifact 写入完成后，运行以下命令生成财务数据附录：

```
python _scripts/financial-data/actuals-to-appendix.py <TICKER>
```

将生成的 markdown 作为 `## Appendix: Financial Data` 插入 artifact（位于 `## Resources` 之前）。


## Appendix: actuals-resolved.json

完整字段清单 -> `references/actuals-data-catalog.md`。

结构：`meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`。

消费规则：先读 actuals -> source_map 取 [S#]/[I#] 标签（不写 [actuals]）-> ratio 只用 actuals 真实值（不用 forward estimate）。
