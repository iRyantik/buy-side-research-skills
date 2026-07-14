---
name: earnings-setup
description: Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.
---

# Earnings Setup

Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

财报不是用来"了解公司近况"的。买方读财报的目的是：
- 我的 thesis 假设是不是还成立？
- 市场反应能不能给我一次机会（多 / 空）？

卖方 preview 的特征：consensus 数字 + 历年 beat/miss 概率 + "关注点"。**全部不要**，这些都是公开信息，没有 alpha。

好的 setup 只盯 2-3 个关键观察点——比如 GE Vernova 的 H2 services orders growth 和 gas turbine backlog conversion。这两个数告诉你 margin mix 是不是在改善，比 EPS beat/miss 有用得多。财报前把 thesis 假设列出来，财报后 10 分钟就能判断 thesis 还活不活。

---

## A. 财报前 Setup（如果用户问的是 preview）

### 0. Primitive Readiness（先确认这次 print 看什么）

财报前不能只列 consensus。先确认这次 print 的关键观察点是否需要先拆机制或 driver。

| 检查项 | 通过标准 | 不通过时动作 |
|---|---|---|
| KPI 机制含义 | 要看的 KPI 背后的行业机制、设备链条、产能单位或工艺流程已清楚 | 先 handoff 到 `mechanism-insight` |
| KPI / segment 口径 | KPI、segment、backlog、orders、book-to-bill 的定义和收入确认关系清楚 | 先 handoff 到 `driver-map` |
| Buy-side bar | buy-side 实际期待能映射到 revenue / margin / backlog / price-volume-mix driver | 先 handoff 到 `driver-map` |
| Thesis linkage | 这次 print 的 3 个观察点能对应 `alpha-thesis` 的假设或 catalyst | 若问题是研究方向不清，触发 `` |

若不通过，先输出最小 handoff block：

```markdown
## Primitive Handoff Required

- Blocker: [哪个 KPI / mechanism / driver 没拆清]
- Why it blocks earnings setup: [它会影响 buy-side bar / 关键阈值 / 决策树的哪一节]
- Handoff: `mechanism-insight` / `driver-map`
- Inputs needed: [需要补的 filing / call / KPI definition / segment data]
```

## 隐含波动与压力

| # | 计算 | 公式 | 输入来源 |
|---|---|---|---|
| 1 | Implied Move | ATM straddle 价格 ÷ 股价 | MKT — 期权市场；A 股标的少时用历史 earnings move |
| 2 | 历史 Earnings Move | 过去 N 次财报日 ±1 天平均涨跌幅 | MKT — 须标回看次数 |
| 3 | Short Interest | 融券余额 ÷ 流通市值 | MKT — 港股/美股可用，A 股不透明 |
| 4 | Short Squeeze Score | Short Interest ÷ Avg Daily Volume | MKT — 高 = 业绩 beat 时空头被迫平仓 |

### 1. 当前 Setup（市场怎么定价这次 print）[→ Bridge: valuation_snapshot, price_action, news]

结构化展示，所有数字必须附 source 和**获取时点**：

| 维度 | 当前值 | 解读 | Ev |
|---|---|---|---|
| 隐含 move | ±7% | 期权市场对这次 print 的隐含波动 | [S1](https://example.com/options-implied-move) |

正文 claim 示例：`Options imply a 7.5% move into earnings, above the trailing eight-quarter realized median of 5.2%. [I1](https://example.com/options-implied-move)`
| 财报前 1-3M 股价 vs 板块 | +12% vs XLE +3% | 跑赢 → buy-side 预期已偏高 | [I1](https://example.com/price-vs-sector) |
| Short Interest | 4.5% of float | 绝对水平 + 近 1M 趋势 | [I2](https://example.com/short-interest) |
| Borrow rate | 35bps | 是否便宜（无空头压力） | [I3](https://example.com/borrow-rate) |
| 卖方修订频率（近 30 天） | 7 上修 / 1 下修 | 上修势头 → 已 priced | [I4](https://example.com/revision-breadth) |

### 2. Sell-Side 数字 vs Buy-Side Bar [→ Bridge: consensus, forecast_eps, institution_rating]
- Sell-side consensus（收入、毛利、EBITDA、EPS、关键 KPI）
- 但 buy-side bar 通常和 sell-side 不一样——可以从这些里推断：
  - 财报前的 price action（强势跑赢 → buy-side bar 已经高于 consensus）
  - 同行业已报公司是否上修了行业预期
  - 卖方近 1-2 周是否有 above-consensus 报告流出
  - 期权市场 skew（put / call IV 差异）
- **明确给出"buy-side 实际期待的数字"区间**——这是 setup 最有 alpha 的一节

### 3. 真正要听 / 看的 3 件事（具体到 KPI 或 metric）
不是"看下游需求"——太空。要具体到具体数字阈值，且基线必须有 source：

| KPI | 上次基线 + Ev | 这次的关键阈值 | 含义 |
|---|---|---|---|
| Permian rig count 2H 指引 | 12 台 [S1](./.cache/sources/permian-rig-guidance.md) | ≥ 14 → 加速；< 12 → 收缩 | 决定 thesis 中 capex 假设 |

正文 claim 示例：`Management kept FY26 revenue guidance unchanged but narrowed the margin range by 50 bps. [S1](./.cache/sources/company-annual-report.md)`
| Buyback pace | Q2 完成 $300M [S1](./.cache/sources/q2-2024-cashflow.md) | 全年 framework 是否上调 > $1.5B | 决定股东回报 willingness |
| OpEx per BOE | $9.5 [S2](./.cache/sources/q2-2024-supplementals.md) | < $9 → 成本控制；> $10 → 通胀失控 | 利润率敏感度 |

每一个都要有**具体数字阈值**，不是"看趋势"。基线数字必须 source 到具体上次 call / 10-Q 的具体位置。

### 4. Asymmetric Setup 判断
基于 1-3，这次 print 对**当前持仓**的 risk/reward：
- 隐含 move 5%，但你认为上行 > 12%、下行 ~ 5% → asymmetric long setup，可加仓 / 买 OTM call
- 隐含 move 10%，预期 in-line，setup 已 priced → 持平 / trim
- 跑赢板块明显 + buy-side bar 远高于 sell-side → asymmetric short / 减仓
- **必须给出明确的 print 前动作建议**——不是"持有观察"

### 5. Pre-Print 决策树（必须提前写下来）

| 情景 | 数字表现 | 决策 |
|---|---|---|
| Beat & raise | EBITDA > +5% & 全年指引上调 > 3% | 加仓 X% |
| Beat & maintain | EBITDA > +5% & 指引维持 | 持平 |
| Miss with cause | EBITDA -5% 但归因于 [一次性] | 看盘后 reaction，回踩到 [价位] 加仓 |
| Miss & cut | EBITDA -10% & 指引下调 | 减仓 50%、重审 thesis |
| Thesis kill | KPI X 出现 [具体阈值] | 平仓 |

**财报前写好这张表，财报中只执行**。这是为了对抗财报当天大脑被 noise 淹没。

---

## B. 财报后 Quick Read（如果用户问的是后视）

### 0. Primitive Readiness（先判断 surprise 属于哪类）

财报后先判断 surprise 是普通 beat / miss，还是暴露了机制或 driver 口径问题。不要在口径没拆清时直接给 thesis health。

- 若公司绕开关键 KPI、改披露口径、重分 segment、backlog / orders 与收入脱钩，先触发 `driver-map`。
- 若新信息涉及设备链条、工程约束、产能单位、工艺流程或 know-how gap，先触发 `mechanism-insight`。
- 若只是实际数 vs 预设阈值的普通偏差，继续执行 post-print quick read。

### 1. 一句话定性
Beat / miss / mixed？股价反应是 confirming / surprising？

数字 vs 反应有 4 种组合，每种含义不同：
- **Beat + 涨** → 标准
- **Beat + 跌** → buy-side bar 已经高于 sell-side，警告信号（仓位拥挤已 priced）
- **Miss + 跌** → 标准
- **Miss + 涨** → 此前预期已经更悲观，可能是底（关注是否值得逆向加仓）

### 2. 关键 KPI 实际数 vs Setup 中要听的（直接对照）
财报前列的 3 个观察点（见上文 setup 第 3 节），每一个**实际数字** vs **预期**给出对照。漏报或被绕过的，单独标记。

### 3. Thesis 假设核对
回到 `alpha-thesis` 第 8 节"我假设了哪些可能错的事"，每一条假设：本季数据**支持 / 削弱 / 中性**？

这一节是和 thesis 工作的衔接——不是孤立看一份财报，而是检查既有 thesis 的健康度。

### 4. Catalyst 状态更新
原 thesis 列的 catalyst（见 `alpha-thesis` 第 4 节）：
- 已发生的 → 结果是什么、对 thesis 影响
- 未发生的 → 时间表 / 概率有变化吗

### 5. 决策（按 pre-print 决策树执行）
执行设定好的决策。如果 print 给出了**完全没预设到**的信息（真正的 surprise），单独说明并给新决策；同时反思 setup 阶段为什么没考虑到这个分支。

### 6. 研究更新 / 后续触发

Post-print 必须明确是否改变研究判断，而不是只写"继续观察"：

| 输出字段 | 允许值 | 说明 |
|---|---|---|
| `research_update` | `none` / `refresh_required` / `thesis_weakened` / `thesis_strengthened` | 是否需要更新研究观点或重写相关 thesis |
| `model_update` | `no` / `actuals_only` / `driver_change` / `assumption_change` | 是否需要触发 `3-statement-model / dcf-model / comps-analysis / model-update` |
| `journal_handoff` | `no` / `research-journal` / `boss-brief` | 是否已经形成值得沉淀或给老板看的判断增量 |
| `_trigger` | `no` / `yes` | 是否暴露了高价值疑点，需要 `` 继续拆 |
| `mechanism_map_trigger` | `no` / `yes` | 是否因为设备链条、工程约束、产能单位、工艺流程或 know-how gap 需要触发 `mechanism-insight` |
| `driver_map_trigger` | `no` / `yes` | 是否因为 segment、KPI 口径、backlog、orders、margin、price / volume / mix 变化需要触发 `driver-map` |

如果财报暴露披露口径、driver、margin、source 冲突等怪异信号，按 Senior Analyst Radar 直接点破。若 surprise 是机制 / know-how 问题，先触发 `mechanism-insight`；若数字改变的是 revenue / margin / backlog / price-volume-mix 口径，先触发 `driver-map`；若已经进入模型更新，再触发 `3-statement-model / dcf-model / comps-analysis / model-update`。

---

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## 反模式自查

- ❌ Setup 里只列了 consensus 数字、没有 buy-side bar 推断 → 没价值
- ❌ "关注点"是"看下游需求""关注资本支出指引"——没有具体阈值 → 无法 trade
- ❌ 没有 pre-print 决策树 → 等着 reaction 完了再想，已经晚了
- ❌ Post-print 是逐行数字复盘 → 这是卖方流水账，重写
- ❌ Post-print 没回到 thesis 的具体假设 → 没接上前面的工作
- ❌ Post-print 没有给出明确仓位决策 → 只是叙述了财报，没产生决策
- ❌ KPI 背后的机制 / 设备链条没搞清楚却硬设阈值 → 先触发 `mechanism-insight`
- ❌ segment、backlog、orders、price / volume / mix 口径变化却直接更新 thesis → 先触发 `driver-map`

**Source 专项**
- ❌ Consensus 数字无 provider（Visible Alpha / Bloomberg）和获取时点 → 数据可能已过期，必须补
- ❌ 隐含 move / IV / SI 数据无时点标注 → 这些是分钟级变化的数据，必须标注
- ❌ KPI 基线（"上次说 12 台"）无具体上次 call / filing 的位置 source → 补

## 篇幅基准

- Pre-print setup：30-60 行
- Post-print read：25-45 行

超长就是抓不住重点。


