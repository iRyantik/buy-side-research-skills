---
name: earnings-setup
description: Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.
---

# Earnings Setup

Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.

## Research Runtime Capsule

本 skill 独立运行时也必须遵守以下 runtime 规则；详细维护基线在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设会自动读取该文件，因此本 skill 自身必须携带可执行的规则摘要。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 inline clickable short source anchor 和例外状态。默认 `[S1](link)`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；完整 source metadata 不在表后展开，每篇 artifact 文末统一写 `## Resources`，用 `- [S1](link) = source type | source title/provider | as-of/filed | page/location | fallback reason` 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Source locality rule: use source quality first (`workspace-local > primary public > reputable provider/news > internet market source`), then prefer `home-market / local-language source` within the same quality tier. News / event evidence should prefer local-language sources for the issuer, main listing venue, regulator, or operating country; market data should prefer the primary listing / trading-market source. Do not maintain market-specific provider whitelists in skill rules; if using a global, English, or non-home-market fallback, state the fallback reason in the final `## Resources` list.
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、ranking、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。若是单公司研究，同时检查相关 `topics/company/<company-slug>/_cache/financial-data/financial-data-summary.md`；需要审计或机器输入时再进入 `internal/evidence-pack.json`、`internal/actuals-resolved.json`、`internal/source-map.json`。

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

- Claim-Level Source Contract：正文里的每个 truth-like claim（KPI baseline、consensus、implied move、revision、peer reaction、price action）都必须紧跟 inline clickable short anchor，如 `[S1](link)` / `[I1](link)`，不只表格 `Ev` 要挂证据。
- No Orphan Truth Claim：输出前检查财报数据、市场预期、管理层表述、`company disclosed` / `market expects` claim 是否都有 anchor；没有就补 source、降级为 gap，或删除。

全局 source / anti-hallucination 规则已内嵌在 `Research Runtime Capsule`。本节只补充 earnings-specific 要求。

Earnings setup 对 source 时效性要求极高。快速提醒：
- Consensus、隐含 move、IV skew、SI、borrow、股价数据必须标注 provider 和获取时点。
- KPI 基线、管理层 commentary、同业已报数据必须给具体 source；没有可靠 source 就标记 `[需查证]` / `[来源待补]`。
- 当本地 cache 缺失时，可对 implied move、IV、SI、borrow、近 1-3M revision、peer print reaction、板块 price action 补公开网页 market data，但必须显式标 `internet source`、provider、as-of、URL / source location，并在 `Ev` 使用 `[I1](link)`。
- KPI baseline、management commentary、company-disclosed threshold 仍优先 local / filing；这些不是自动 internet fallback 的范围。
- 若首次使用 internet fallback，正文加一句：`以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。`
- 不确定 URL 是否存在时写 `[link 待补]`，不得编造；sub-agent URL 抽查匹配后才可使用。

- Locality-aware news / event evidence: at the same source-quality tier, prefer home-market / local-language sources for event claims; if using global or English fallback, state the fallback reason in the final `## Resources` list.
## Parallel Evidence Pass

本 skill 默认必须按财报 setup 组件启动 sub-agent / delegate worker 并行查证；sub-agent 只能返回 evidence card：

- 可拆任务：consensus / buy-side bar 线索、last print baseline、guidance / KPI thresholds、peer read-through、options / implied move / borrow / SI timestamp。
- sub-agent 不得写最终 asymmetric setup、pre-print decision tree、post-print thesis update 或 position decision；这些必须由主 agent 综合。
- 主 agent 必须抽查关键 URL / claim，并统一所有时效性数据的 timestamp。
- 财报后模式中，sub-agent 可摘 press release / transcript / KPI actuals，但主 agent 必须亲自对照 pre-print setup 后写决策。
- 如果用户明确要求并行而当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

---

## A. 财报前 Setup（如果用户问的是 preview）

### 0. Primitive Readiness（先确认这次 print 看什么）

财报前不能只列 consensus。先确认这次 print 的关键观察点是否需要先拆机制或 driver。

| 检查项 | 通过标准 | 不通过时动作 |
|---|---|---|
| KPI 机制含义 | 要看的 KPI 背后的行业机制、设备链条、产能单位或工艺流程已清楚 | 先 handoff 到 `mechanism-map` |
| KPI / segment 口径 | KPI、segment、backlog、orders、book-to-bill 的定义和收入确认关系清楚 | 先 handoff 到 `driver-map` |
| Buy-side bar | buy-side 实际期待能映射到 revenue / margin / backlog / price-volume-mix driver | 先 handoff 到 `driver-map` |
| Thesis linkage | 这次 print 的 3 个观察点能对应 `alpha-thesis` 的假设或 catalyst | 若问题是研究方向不清，触发 `next-step` |

若不通过，先输出最小 handoff block：

```markdown
## Primitive Handoff Required

- Blocker: [哪个 KPI / mechanism / driver 没拆清]
- Why it blocks earnings setup: [它会影响 buy-side bar / 关键阈值 / 决策树的哪一节]
- Handoff: `mechanism-map` / `driver-map`
- Inputs needed: [需要补的 filing / call / KPI definition / segment data]
```

### 1. 当前 Setup（市场怎么定价这次 print）

结构化展示，所有数字必须附 source 和**获取时点**：

| 维度 | 当前值 | 解读 | Ev |
|---|---|---|---|
| 隐含 move | ±7% | 期权市场对这次 print 的隐含波动 | [S1](link) |


正文 claim 示例：`Options imply a 7.5% move into earnings, above the trailing eight-quarter realized median of 5.2%. [I1](link)`
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

| KPI | 上次基线 + Ev | 这次的关键阈值 | 含义 |
|---|---|---|---|
| Permian rig count 2H 指引 | 12 台 [S1](link) | ≥ 14 → 加速；< 12 → 收缩 | 决定 thesis 中 capex 假设 |


正文 claim 示例：`Management kept FY26 revenue guidance unchanged but narrowed the margin range by 50 bps. [S1](link)`
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

### 0. Primitive Readiness（先判断 surprise 属于哪类）

财报后先判断 surprise 是普通 beat / miss，还是暴露了机制或 driver 口径问题。不要在口径没拆清时直接给 thesis health。

- 若公司绕开关键 KPI、改披露口径、重分 segment、backlog / orders 与收入脱钩，先触发 `driver-map`。
- 若新信息涉及设备链条、工程约束、产能单位、工艺流程或 know-how gap，先触发 `mechanism-map`。
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
| `next_step_trigger` | `no` / `yes` | 是否暴露了高价值疑点，需要 `next-step` 继续拆 |
| `mechanism_map_trigger` | `no` / `yes` | 是否因为设备链条、工程约束、产能单位、工艺流程或 know-how gap 需要触发 `mechanism-map` |
| `driver_map_trigger` | `no` / `yes` | 是否因为 segment、KPI 口径、backlog、orders、margin、price / volume / mix 变化需要触发 `driver-map` |

如果财报暴露披露口径、driver、margin、source 冲突等怪异信号，按 Senior Analyst Radar 直接点破。若 surprise 是机制 / know-how 问题，先触发 `mechanism-map`；若数字改变的是 revenue / margin / backlog / price-volume-mix 口径，先触发 `driver-map`；若已经进入模型更新，再触发 `3-statement-model / dcf-model / comps-analysis / model-update`。

---

## 反模式自查

- ❌ Setup 里只列了 consensus 数字、没有 buy-side bar 推断 → 没价值
- ❌ "关注点"是"看下游需求""关注资本支出指引"——没有具体阈值 → 无法 trade
- ❌ 没有 pre-print 决策树 → 等着 reaction 完了再想，已经晚了
- ❌ Post-print 是逐行数字复盘 → 这是卖方流水账，重写
- ❌ Post-print 没回到 thesis 的具体假设 → 没接上前面的工作
- ❌ Post-print 没有给出明确仓位决策 → 只是叙述了财报，没产生决策
- ❌ KPI 背后的机制 / 设备链条没搞清楚却硬设阈值 → 先触发 `mechanism-map`
- ❌ segment、backlog、orders、price / volume / mix 口径变化却直接更新 thesis → 先触发 `driver-map`

**Source 专项**
- ❌ Consensus 数字无 provider（Visible Alpha / Bloomberg）和获取时点 → 数据可能已过期，必须补
- ❌ 隐含 move / IV / SI 数据无时点标注 → 这些是分钟级变化的数据，必须标注
- ❌ KPI 基线（"上次说 12 台"）无具体上次 call / filing 的位置 source → 补
- ❌ 用了"chat 群里说"的 whisper 但未标记"chat-sourced" → 必须标记，不能伪装成硬数据
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删
- ❌ URL 不确定真实存在 → 写描述加 `[link 待补]`，不要假装
- ❌ 把 sub-agent evidence card 直接写成 pre-print decision tree / post-print position decision，而没有主 agent 抽查时点、统一口径和综合判断

## 篇幅基准

- Pre-print setup：500-900 字
- Post-print read：400-700 字

超长就是抓不住重点。

## 可选保存

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-earnings-setup.md
```

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

## Workflow 联动

- 输入来自 `alpha-thesis`（第 4 节 catalyst、第 8 节假设清单）
- 输出反过来更新 `alpha-thesis`（thesis 是否还成立，假设是否需要修订）
- 如果 post-print 显示 thesis 严重削弱，触发回到 `bear-pre-mortem` 重新压测
- 如果 post-print 暴露高价值疑点，触发 `next-step`；如果已经形成认知增量，触发 `research-journal`；如果暴露机制 / know-how gap，先触发 `mechanism-map`；如果数字改变 model driver，先触发 `driver-map`，再按需要触发 `3-statement-model / dcf-model / comps-analysis / model-update`。
