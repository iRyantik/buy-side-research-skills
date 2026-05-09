---
name: earnings-setup
description: Use when preparing for an upcoming earnings print, reacting to newly reported results, or deciding whether earnings should trigger thesis, model, or decision updates.
---

# Earnings Setup

处理两个相关但不同的任务：
1. **财报前**：构建 setup——这单 print 的 risk/reward 是不是值得调整仓位
2. **财报后**：快速判断 thesis 是不是还成立——而不是一行一行复盘数字

## 心法

财报不是用来"了解公司近况"的。买方读财报的目的是：
- 我的 thesis 假设是不是还成立？
- 市场反应能不能给我一次机会（多 / 空）？

卖方 preview 的特征：consensus 数字 + 历年 beat/miss 概率 + "关注点"。**全部不要**，这些都是公开信息，没有 alpha。

## Source 政策

本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

Earnings setup 对 source 时效性要求极高。快速提醒：
- Consensus、隐含 move、IV skew、SI、borrow、股价数据必须标注 provider 和获取时点。
- KPI 基线、管理层 commentary、同业已报数据必须给具体 source；没有可靠 source 就标记 `[需查证]` / `[来源待补]`。
- 不确定 URL 是否存在时写 `[link 待补]`，不得编造；sub-agent URL 抽查匹配后才可使用。

---

## A. 财报前 Setup（如果用户问的是 preview）

### 1. 当前 Setup（市场怎么定价这次 print）

结构化展示，所有数字必须附 source 和**获取时点**：

| 维度 | 当前值 | 解读 | Source（含时点） |
|---|---|---|---|
| 隐含 move | ±7% | 期权市场对这次 print 的隐含波动 | [CBOE / OptionMetrics 2024-XX-XX HH:MM](url) |
| 财报前 1-3M 股价 vs 板块 | +12% vs XLE +3% | 跑赢 → buy-side 预期已偏高 | [Bloomberg / Yahoo](url) |
| Short Interest | 4.5% of float | 绝对水平 + 近 1M 趋势 | [Bloomberg SI 2024-XX-XX](url) |
| Borrow rate | 35bps | 是否便宜（无空头压力） | [borrow desk](url) |
| 卖方修订频率（近 30 天） | 7 上修 / 1 下修 | 上修势头 → 已 priced | [Visible Alpha 2024-XX-XX](url) |

### 2. Sell-Side 数字 vs Buy-Side Bar
- Sell-side consensus（收入、毛利、EBITDA、EPS、关键 KPI）
- 但 buy-side bar 通常和 sell-side 不一样——可以从这些里推断：
  - 财报前的 price action（强势跑赢 → buy-side bar 已经高于 consensus）
  - 同行业已报公司是否上修了行业预期
  - 卖方近 1-2 周是否有 above-consensus 报告流出
  - 期权市场 skew（put / call IV 差异）
- **明确给出"buy-side 实际期待的数字"区间**——这是 setup 最有 alpha 的一节

### 3. 真正要听 / 看的 3 件事（具体到 KPI 或 metric）
不是"看下游需求"——太空。要具体到具体数字阈值，且基线必须有 source：

| KPI | 上次基线 + Source | 这次的关键阈值 | 含义 |
|---|---|---|---|
| Permian rig count 2H 指引 | 12 台 [Q2 2024 call p.5](url) | ≥ 14 → 加速；< 12 → 收缩 | 决定 thesis 中 capex 假设 |
| Buyback pace | Q2 完成 $300M [Q2 2024 10-Q cash flow](url) | 全年 framework 是否上调 > $1.5B | 决定股东回报 willingness |
| OpEx per BOE | $9.5 [Q2 2024 supplementals p.3](url) | < $9 → 成本控制；> $10 → 通胀失控 | 利润率敏感度 |

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
| `model_update` | `no` / `actuals_only` / `driver_change` / `assumption_change` | 是否需要触发 `financial-model` |
| `journal_handoff` | `no` / `research-journal` / `boss-brief` | 是否已经形成值得沉淀或给老板看的判断增量 |
| `next_step_trigger` | `no` / `yes` | 是否暴露了高价值疑点，需要 `next-step` 继续拆 |
| `driver_map_trigger` | `no` / `yes` | 是否因为 segment、backlog、margin、price / volume / mix 变化需要触发 `driver-map` |

如果财报暴露披露口径、driver、margin、source 冲突等怪异信号，按 Senior Analyst Radar 直接点破。若数字改变的是 revenue / margin / backlog / price-volume-mix 口径，先触发 `driver-map`；若已经进入模型更新，再触发 `financial-model`。

---

## 反模式自查

- ❌ Setup 里只列了 consensus 数字、没有 buy-side bar 推断 → 没价值
- ❌ "关注点"是"看下游需求""关注资本支出指引"——没有具体阈值 → 无法 trade
- ❌ 没有 pre-print 决策树 → 等着 reaction 完了再想，已经晚了
- ❌ Post-print 是逐行数字复盘 → 这是卖方流水账，重写
- ❌ Post-print 没回到 thesis 的具体假设 → 没接上前面的工作
- ❌ Post-print 没有给出明确仓位决策 → 只是叙述了财报，没产生决策

**Source 专项**
- ❌ Consensus 数字无 provider（Visible Alpha / Bloomberg）和获取时点 → 数据可能已过期，必须补
- ❌ 隐含 move / IV / SI 数据无时点标注 → 这些是分钟级变化的数据，必须标注
- ❌ KPI 基线（"上次说 12 台"）无具体上次 call / filing 的位置 source → 补
- ❌ 用了"chat 群里说"的 whisper 但未标记"chat-sourced" → 必须标记，不能伪装成硬数据
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装

## 篇幅

- Pre-print setup：500-900 字
- Post-print read：400-700 字

超长就是抓不住重点。

## 衔接关系

- 输入来自 `alpha-thesis`（第 4 节 catalyst、第 8 节假设清单）
- 输出反过来更新 `alpha-thesis`（thesis 是否还成立，假设是否需要修订）
- 如果 post-print 显示 thesis 严重削弱，触发回到 `bear-pre-mortem` 重新压测
- 如果 post-print 暴露高价值疑点，触发 `next-step`；如果已经形成认知增量，触发 `research-journal`；如果数字改变 model driver，先触发 `driver-map`，再按需要触发 `financial-model`。
