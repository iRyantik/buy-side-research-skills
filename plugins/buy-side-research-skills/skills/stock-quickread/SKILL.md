---
name: stock-quickread
description: Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.
---

# Stock Quickread

Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.

## Research Runtime Capsule


**三表数据前置（由 subagent 执行）：** 将 financial-data 获取委托给 subagent——1. subagent 检查 topics/company/<slug>/_cache/financial-data/internal/actuals-resolved.json 2. 不存在 → subagent 执行 /financial-data --lite <ticker>，写入后返回 3. 存在 → 主 agent 从 actuals 取所需科目。artifact 必须包含 financial-data 来源证据（source_layer 标记或 /financial-data 执行痕迹）
- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

本 skill 独立运行时也必须携带最小必要的 runtime 摘要。详细 authoring baseline 仍在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设该文件会被自动读取。
- 默认用中文输出，结论先行，数据优先。只有在可追溯性更强时，才保留 ticker、source title、URL 以及必要的财务 / 行业术语英文。
- Source stance 分两条 track：disclosure-fact fields 优先 `topic-local evidence cache > primary public > trusted third-party > web`；market-snapshot fields 优先 `topic-local evidence cache / financial-data > trusted third-party > web`。同一质量层内优先 `home-market / local-language source`；`internet source` 只补 market / consensus / valuation / liquidity / price-action 缺口，不冒充 company-disclosed fact。
- 最终 synthesis、source conflict handling、quickread verdict 和 routing 由主 agent 统一负责。financial-data 获取**默认委托 subagent 执行**（不限用户显式要求）；其他 evidence gathering / QA 类 sub-agent 仅在用户明确要求 `sub-agent`、`delegate` 或并行时才启用。
- 主动执行 Senior Analyst Radar：凡是可能改变业务现实、model driver、consensus framing、peer set、valuation framework 或 research priority 的疑点，都要直接点破。
- 机制 / 工程原理 / 设备链条类 gap 交给 `mechanism-map`；revenue / margin / backlog / price-volume-mix 或 disclosure bucket 异常交给 `driver-map`；expectations / priced-in gap 交给 `consensus-map`；下一个最值得追的问题交给 `next-step`。
- 研究启动先检查 topic `_cache/` 和 `financial-data` 输出，优先复用已有的 source-tracked material，而不是重建原始数据上下文。

让一个买方研究员在 30 分钟内对一家陌生公司从零起步，达到"能问出像样的下一层问题"的状态。**不是**全面了解公司——全面了解是浪费时间，因为 90% 的细节最终不会进入决策。

## 心法

买方读公司不是为了"懂公司"，而是为了：(1) 判断这是不是一个值得花更多时间的标的；(2) 找到下一层要问的具体问题。所以 quickread 的产出必须直奔决策有用的信息。

如果你写出来的东西像卖方初次覆盖报告，就是失败的。卖方覆盖报告的特征：业务分部按章节展开、管理层简历、5 年历史财务表、罗列所有近期事件。这些**全部不要**。

## 输出结构（严格按这个走）

每一节都有篇幅上限。不到位可以更短，**绝不允许超长**。超长本身就是流水账的症状。

### 1. 一眼看懂

#### 打个比方（≤2 句）

用日常物品做类比。不需要行业知识就能懂。

- 反例（PR 腔）："是一家领先的、致力于通过创新技术为客户提供价值的能源解决方案提供商"
- 正例："好比一个超精密的激光打印机，但它是给芯片厂在光掩膜上'刻电路图'用的。一台 $4-30M。"

#### 产品长这样

每个主要产品线 1 张图。① 公司官网 Media Kit → ② web search `<产品名> 产品图片` 找新闻稿配图 → ③ 搜不到就不放图。存到 `_cache/images/<slug>-<product>.png`。

| ![产品A](_cache/images/<slug>-a.png) | ![产品B](_cache/images/<slug>-b.png) |
|---|---|
| *产品名 — 功能（≤15字）* | *产品名 — 功能（≤15字）* |

#### 在产业链哪一环

```mermaid
flowchart LR
    A[上游：<卖什么的>] --> B[**<公司>**<br/><做什么>] --> C[下游：<谁买单>]
```

#### 怎么收钱（≤1 句）

> 一次性设备 / 设备+耗材 / 订阅制 / 维护服务费

#### 说人话

> 说白了就是 <最简单的类比>。

### 2. 不懂的词先看这

| 术语 | 大白话 |
|---|---|
| <术语> | <一句话> |

> 最多 5-8 个。不是词典，是聊天时怎么讲。

### 3. 钱从哪里来（数据表 + takeaway）

**只有定性描述是片面认知**——读者无法判断哪个分部在 mattering、哪个在萎缩、哪里有异常。所以这一节由两部分组成：

**(a) 关键财务数据表（必填）**

按分部拆开（如果是单分部公司，按产品线 / 地区 / 客户类型替代），最少包含以下列。每个分部分别列出**最近一期完整年度（或最近 LTM）**和**最近一个单季度**两行的数据（含同比变化）。期间拆行为独立行。

| 分部 | 期间 | 收入占比 | 收入 YoY | 利润 | 利润口径 | 利润占比 | 利润率 | Ev |
|---|---|---|---|---|---|---|---|---|
| 分部 A | FY2024 | 45% | +12% | EBIT | 65% | 28% | [S1](./_cache/sources/company-annual-report.md) |
| 分部 B | FY2024 | 35% | +3% | EBIT | 25% | 14% | [S10](./_cache/sources/fy2024-segment-note.md) |
| 分部 C | FY2024 | 20% | -8% | [ND]——公司未披露分部利润 | — | — | [S10](./_cache/sources/fy2024-segment-note.md) |
| **整体** | **FY2024** | **100%** | **+5%** | EBIT | **100%** | **19%** | [S11](./_cache/sources/fy2024-income-statement.md) |
| 分部 A | Q1 2025 | 43% | +8% | EBIT | 62% | 26% | [S9](./_cache/sources/q1-2025-segment-note.md) |
| 分部 B | Q1 2025 | 36% | +2% | EBIT | 24% | 13% | [S9](./_cache/sources/q1-2025-segment-note.md) |
| 分部 C | Q1 2025 | 21% | -6% | [ND] | — | — | [S9](./_cache/sources/q1-2025-segment-note.md) |
| **整体** | **Q1 2025** | **100%** | **+4%** | EBIT | **100%** | **18%** | [S12](./_cache/sources/q1-2025-income-statement.md) |

正文 claim 示例：`FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./_cache/sources/company-annual-report.md)`

**取舍说明**：

1. **口径统一**：分段和整体用同一个口径（优先 segment EBIT > Gross Profit > Net Income）。分段没口径就标 [ND]，整体随分段。期间先 FY 后 Q，每分部两行。
2. **推导优先**：能算就推导（整体-分部扣减、收入×利润率），标 [推算] 且写逻辑。别急着标 [ND]。
3. **缺数诚实**：算不出来再 [ND]，别编数字。口径变了/重组了/没披露 → 标出来，不假装连续。

**(b) Takeaway（2-3 句）**

表格不是终点，必须有解读。要讲清楚：
- **结构性事实**：收入结构 vs 利润结构是不是错配？哪个分部是真正的"利润引擎"？
- **方向性事实**：哪个分部在变重要、哪个在萎缩？利润率扩张 / 收缩集中在哪？
- **经济驱动 vs GAAP 分部不一样的地方**：比如"汽车公司 70% 收入来自整车，但 60% 利润来自金融子公司"——这种洞察必须在 takeaway 里给出，仅有表格不够。
- **季节性 / 拐点信号**：季度数据 vs 全年趋势是否有方向性背离？比如某分部全年利润率在扩张但最近季度已开始收窄——这可能是趋势反转的早期信号，必须在 takeaway 中指出。

> 反例（流水账）："公司分为 A、B、C 三个分部，A 主要做 X，收入占比 45%，B 主要做 Y..."——这是把表格用文字念了一遍
> 正例："公司表面是 A+B+C 三业务，但 A 贡献 65% 利润且利润率持续扩张，B/C 在量价双杀；从买方视角这其实是个 A 业务的纯标的，B/C 是干扰项"

### 4. 关键比率

以下 6 个比率全部计算并输出，拿不到的标 [ND]。所有数字从三张表算，不得随手拍。科目对照见 。

| # | 比率 | 公式 | 用途 |
|---|---|---|---|
| 1 | Gross Margin | (Rev - COGS) ÷ Rev | 定价权——最底层的竞争力指标 |
| 2 | OpEx / 收入 | (SG&A + R&D) ÷ Rev | 经营杠杆——费用结构决定利润弹性 |
| 3 | Capex / D&A | CapEx ÷ (折旧+摊销) | 投资强度——>1.5 扩张 / ~1.0 维持 / <0.7 收割 |
| 4 | FCF | OCF - CapEx（绝对值） | 真金白银——利润可以造假，现金不能 |
| 5 | 有息负债 / 净资产 | (短期+长期借款) ÷ Equity | 杠杆——会不会被债压死 |
| 6 | 商誉 / 净资产 | Goodwill ÷ Equity | M&A 风险——商誉暴雷是最快的归零方式 |

**行业周期阶段**（1 句）：产能扩张 / 竞争激化 / 整合 / 衰退？公司在行业内领先扩张 / 跟随 / 反向收缩？

| 比率 | 当前值 | 判断 | Ev |
|---|---|---|---|
| Gross Margin | 28% | 定价权——越高越有议价力，趋势比绝对值重要 | [S1](./_cache/sources/income-statement.md) |
| OpEx / 收入 | 18% | 经营杠杆——费用结构决定利润弹性 | [S1](./_cache/sources/income-statement.md) |
| Capex / D&A | 1.8x | >1.5 重投资 / ~1.0 维持 / <0.7 收割 | [S2](./_cache/sources/cashflow-statement.md) |
| FCF | ¥2,500M | 真金白银，利润可以造假现金不能 | [S2](./_cache/sources/cashflow-statement.md) |
| 有息负债 / 净资产 | 35% | >50% 是警戒线 | [S3](./_cache/sources/balance-sheet.md) |
| 商誉 / 净资产 | 12% | >50% 单独看减值风险 | [S3](./_cache/sources/balance-sheet.md) |

### 5. 什么在驱动股价

第一次看的人，读完这节应该理解这家公司**到底跟什么动**，不是记住三个变量叫 X、Y、Z。

#### 这门生意怎么转（3-5 句）

用大白话讲商业逻辑——什么东西决定它赚钱还是亏钱。不是重复 §1 的类比，是讲因果。不需要行业知识就能理解。

> 例："ASMPT 的生意本质上是个周期游戏——芯片厂 capex 扩张时买他的机器，收缩时停买。一台机器用 5-8 年，收入波峰波谷差 40-50%。但因为全球只有 2-3 家能做高端 die bonder，所以毛利率在好时候能到 40%+，差时候也能守住 30%。"

#### 行业现在在发生什么（2-3 句）

当前行业周期的位置，以及**这对这家公司意味着什么**。不是通用行业科普。

> 例："2025-2026 半导体后端设备处于 AI 驱动的结构性扩张期——不是传统半导体的周期性复苏。关键差异：先进封装的 capex 跟着英伟达/AMD 的 AI 芯片迭代走，不是手机周期。AI 芯片一代一代更新 → 封装设备需求跟着换代 → 订单周期从 3-4 年缩到 1.5-2 年。"

#### 真正跟着什么动（2-3 个变量）

每个变量一个子节。不是扔关键词——是从上面的生意逻辑和行业变化推导出来的。

##### 变量名（一句话——这个变量怎么驱动股价）

**数据锚点**（来自 financial-data）

| 指标 | 当前 | 历史区间 | 来源 |
|---|---|---|---|
| <相关 metric> | <值> | <min — max> | [S#](...) |

**市场在讲什么故事**（1-2 句——多方怎么想，空方怎么想）

**最近一次怎么动的**（1 句——这个变量变化时股价怎么反应）[S#](...)

**什么时候可能不灵**（1 句——历史上哪个季度这个变量和股价背离了）

**情绪在怎么变**（1 句——最近分析师/市场的态度微妙变化）

**我的看法**（1 句）

**如果变量走**

| 场景 | 该变量 | 股价 | 概率 | 和历史比 | Ev |
|---|---|---|---|---|---|
| 乐观 | <假设> | +XX% | ~X% | > 均值 1σ | [S#](...) |
| 基准 | — | — | ~X% | 均值 | — |
| 悲观 | <假设> | -XX% | ~X% | < 均值 1σ | [S#](...) |

#### 放在一起看（2-3 句）

如果两个变量同时朝一个方向 → 可能 XX%。如果互相抵消 → 市场可能进入真空期——跟大盘漂。整个故事最大的裂缝在哪（1 句点出最脆的假设）。

### 6. 市场在交易什么（consensus + 反向工程）

写"PE 25x vs 历史 18x，偏贵"是卖方水平。买方要回答的是**以当前估值，市场在隐含什么假设**——然后判断"我同意 / 不同意这个假设"。这是 alpha 的起点。

**(a) Consensus 关键数字**

NTM 收入、EBITDA、EPS、关键 KPI 的卖方一致预期。最近 3-6 个月的修订方向（上修 / 下修 / 频率）。

**(b) 估值倍数对比**

| 倍数 | 当前 | 自身 5 年中位 | 同业当前 | 解读 | Ev |
|---|---|---|---|---|---|
| EV/EBITDA | 8.5x | 6.2x | 7.1x | 相对自身 +37%，相对同业 +20% | [S1](https://example.com/valuation-comps) |
| P/E | 18x | 14x | 16x | ... | [I1](https://example.com/pe-comps) |
| FCF yield | 5% | 7% | 6% | ... | [I2](https://example.com/fcf-yield-comps) |

正文 claim 示例：`The stock trades at 8.5x EV/EBITDA versus its 5-year median of 6.2x and peers at 7.1x. [I1](https://example.com/valuation-comps)`

倍数选择和**第 4 节的资本周期阶段判断要一致**——不要在第 4 节说"收割期"，第 6 节用 EV/Sales。

**(c) 反向工程：当前估值在隐含什么（这是必填、最关键）**

以下四项全部回答：
- **隐含增长率**：以当前 PE，按合理 ROE / payout，反推市场隐含的长期增长率是多少？这个增长率公司过去做到过吗？
- **隐含 margin**：以当前 EV/Sales，反推市场对长期 margin 的假设是多少？vs 历史平均 / vs 行业最优秀玩家？
- **Reverse DCF**：以当前股价、合理 WACC，反推所需的 5 年 FCF CAGR 是多少？
- **Bear-implied**：股价跌到 X（历史低位 / 同业最低）需要发生什么？这个情景的概率？

**示例输出**：
> "当前 EV/EBITDA 8.5x 隐含 5 年 EBITDA CAGR ~ 12%。公司过去 5 年实际 CAGR 是 7%，行业最好的同行做到 10%。要相信当前估值，需要相信 [具体假设 X 发生]。这是当前的多空分歧点。"

如果第 6 节没有反向工程，研究员只能得出"贵了 / 便宜了"的判断，无法定位**贵在哪个假设上**——而 alpha 通常就藏在某个具体的隐含假设里。

### 7. 多空在争论什么
**不是**通用 SWOT。是"现在多空双方实际在 argue 什么"——具体到某个数据点、某个假设、某个事件。如果一时不知道，至少给出"需要查清楚的争论点"。

### 8. 对手盘需要相信什么

快速写清楚反方需要相信的核心假设：
- 如果初步倾向多，空头 / 观望者必须相信什么才会继续压低估值？
- 如果初步倾向空，当前多头必须相信什么才愿意继续付这个价格？
- 哪个假设最脆、最容易被下一份数据或同业 commentary 证伪？

这一节不是完整 thesis，只是把后续 `alpha-thesis` 的 variant view 起点暴露出来。

### 9. 最近在发生什么

**股价**：从 <日期> <价格> → 现在 <价格>，<涨跌幅>。同期大盘/板块 <涨跌幅>。[I#](https://finance.yahoo.com/...)

**事件**（每条带 source）：
- <日期> <事件> → 股价 <涨跌 X%> [S#](...)
- <日期> <事件> → 股价 <涨跌 X%> [S#](...)

> 列 3-5 个近期关键事件。每个事件必须有 source anchor——不要"据报道""有消息称"。

### 10. 下一层要问的 5 个问题
不是"管理层质量如何"这种空泛问题。要具体——具体到一个数字、一个事件、一份文件能回答。
- 反例："业务可持续性如何？"
- 正例："Permian 老井 decline rate 从 2023 年的 X% 是否已加速到 Y%？哪份数据可以验证（公司 Q 表 / Enverus / Rystad）？"

如果 quickread 发现收入结构复杂、segment bucket 怪、model driver 不清楚，下一步不要在 quickread 内完整展开。明确推荐 `driver-map`，让它单独拆 `Reported Bucket → Business Reality → Model Driver`。

## 反模式自查

写完后必须自检以下症状，命中就重写：

**通用**
- ❌ 出现"成立于 XXXX 年""总部位于 XXXX""管理层经验丰富"——直接删
- ❌ 引用了 5 年前的财务数据但没有给出当前结论——删
- ❌ 第 5、6、7 节看起来差不多——这三节问的是不同问题，重写
- ❌ 第 10 节的问题"再多查点资料"就能回答——太浅，重写

**Source 专项**
- ❌ 出现具体数字 / 引语但无 source link → 标记 `[需查证]` 或删
- ❌ 表格无 `Ev` / `证据` 短链接列或文末 `## Resources` 缺失 → 加上
- ❌ Source 是"据报道""有传言""有人说" → 不是 source，找出处或删
- ❌ 用 Wikipedia / 推特 / 论坛作为关键事实依据 → 找一手 source 替换
- ❌ 多 source 冲突时只挑了一个 → 必须标注冲突
- ❌ URL 是猜的 / 不确定真实存在 → 写描述加 `[link 待补]`，不要假装

**第 2 节专项**
- ❌ 数据表但没有 takeaway——表格不是终点
- ❌ Takeaway 用文字把表格内容念了一遍——重复劳动

**第 4 节专项**
- ❌ 关键比率不全 / 没给数字判断（"capex 较高"而不是"capex/D&A = 1.8x，重投资期"）
- ❌ 第 4 节判断的资本周期阶段，和第 6 节用的估值锚点对不上——说明判断没真做

**第 4 节专项**
- ❌ 输出的变量是"油价 / 产量 / 成本"等教科书答案——回去找当前 regime 特有的变量
- ❌ 没有具体证据（没引用具体季度的股价反应、没给相关性数据）
- ❌ 发现 driver / bucket 怪但在 quickread 里硬写完整模型拆分 → 触发错层级，应该交给 `driver-map`

**第 6 节专项**
- ❌ 只写了"贵 / 便宜"，没做反向工程——无法定位市场到底在 pricing 哪个假设，必须重写。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| quickread 判断这家公司值得继续研究，且需要形成 long / short 观点 | `alpha-thesis` |
| 需要系统拆 sell-side consensus、buy-side bar、priced-in assumptions 或 variant-view gap | `consensus-map` |
| 公司基础、业务演变、segment / KPI 历史口径或 material M&A / divestiture 影响当前理解 | `company-primer` |
| 收入结构复杂、segment bucket 怪、model driver 不清楚 | `driver-map` |
| 业务机制、设备链条、工艺流程或术语不清 | `mechanism-map` |
| 需要和一组 peer 横向比较 | `peer-deep-dive` |
| 需要把估值隐含假设量化成 model / reverse DCF | `3-statement-model / dcf-model / comps-analysis / model-update` |
| 只是不知道下一层问题怎么问 | `next-step` |
| 已经形成可复用认知增量 | `research-journal` |

## 保存

默认保存到当前工作的 topic 下，命名格式：`YYYY-MM-DD-stock-quickread-<company>.md`。

- 路径：`topics/<current-topic>/YYYY-MM-DD-stock-quickread-<company>.md`
- 当前 topic 不明确 → 先 handoff `new-session` 解析路径
- 公司 qualifier 从 company slug 提取（如 `mycronic`、`robotchnik`）

## 篇幅基准

- 标准 quickread：1800-2500 字。低于 1800 说明 §5 驱动因素展开不足——这是全文最有信息量的节。超过 2500 说明在替 `company-primer` 或 `driver-map` 干活，应拆分或去重。
