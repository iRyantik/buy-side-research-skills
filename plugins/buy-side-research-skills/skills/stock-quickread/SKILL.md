---
name: stock-quickread
description: Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.
---

# Stock Quickread

Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

本 skill 独立运行时也必须携带最小必要的 runtime 摘要。详细 authoring baseline 仍在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设该文件会被自动读取。
- 默认用中文输出，结论先行，数据优先。只有在可追溯性更强时，才保留 ticker、source title、URL 以及必要的财务 / 行业术语英文。
- Source stance 分两条 track：disclosure-fact fields 优先 `topic-local evidence cache > primary public > trusted third-party > web`；market-snapshot fields 优先 `topic-local evidence cache / financial-data > trusted third-party > web`。同一质量层内优先 `home-market / local-language source`；`internet source` 只补 market / consensus / valuation / liquidity / price-action 缺口，不冒充 company-disclosed fact。
- 最终 synthesis、source conflict handling、quickread verdict 和 routing 由主 agent 统一负责。只有用户明确要求 `sub-agent`、`delegate` 或并行时，才允许 sub-agent 做 bounded evidence gathering / QA。
- 主动执行 Senior Analyst Radar：凡是可能改变业务现实、model driver、consensus framing、peer set、valuation framework 或 research priority 的疑点，都要直接点破。
- 机制 / 工程原理 / 设备链条类 gap 交给 `mechanism-map`；revenue / margin / backlog / price-volume-mix 或 disclosure bucket 异常交给 `driver-map`；expectations / priced-in gap 交给 `consensus-map`；下一个最值得追的问题交给 `next-step`。
- 研究启动先检查 topic `_cache/` 和 `financial-data` 输出，优先复用已有的 source-tracked material，而不是重建原始数据上下文。

让一个买方研究员在 30 分钟内对一家陌生公司从零起步，达到"能问出像样的下一层问题"的状态。**不是**全面了解公司——全面了解是浪费时间，因为 90% 的细节最终不会进入决策。

## 心法

买方读公司不是为了"懂公司"，而是为了：(1) 判断这是不是一个值得花更多时间的标的；(2) 找到下一层要问的具体问题。所以 quickread 的产出必须直奔决策有用的信息。

如果你写出来的东西像卖方初次覆盖报告，就是失败的。卖方覆盖报告的特征：业务分部按章节展开、管理层简历、5 年历史财务表、罗列所有近期事件。这些**全部不要**。

## 输出结构（严格按这个走）

每一节都有篇幅上限。不到位可以更短，**绝不允许超长**。超长本身就是流水账的症状。

### 1. 一句话生意（≤ 2 句）
他们到底在卖什么、谁在付钱、付的是什么钱（一次性 / 订阅 / 运营 / 产品）。撕掉营销语言。
- 反例（PR 腔）："是一家领先的、致力于通过创新技术为客户提供价值的能源解决方案提供商"
- 正例："开采美国二叠纪盆地的页岩油，按现货油价卖给中游管道公司；上游 E&P，纯粹的油价 beta"

### 2. 钱从哪里来、利润从哪里来（必须包含数据表 + takeaway）

**只有定性描述是片面认知**——读者无法判断哪个分部在 mattering、哪个在萎缩、哪里有异常。所以这一节由两部分组成：

**(a) 关键财务数据表（必填）**

按分部拆开（如果是单分部公司，按产品线 / 地区 / 客户类型替代），最少包含以下列。每个分部分别列出**最近一期完整年度（或最近 LTM）**和**最近一个单季度**两行的数据（含同比变化）。期间拆行为独立行。

| 分部 | 期间 | 收入占比 | 收入 YoY | 利润占比 | 利润 YoY | 利润率 | 利润率 YoY 变化 | Ev |
|---|---|---|---|---|---|---|---|---|
| 分部 A | FY2024 | 45% | +12% | 65% | +25% | 28% | +250 bps | [S1](./_cache/sources/company-annual-report.md) |

正文 claim 示例：`FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./_cache/sources/company-annual-report.md)`
| 分部 A | Q1 2025 | 43% | +8% | 62% | +15% | 26% | +100 bps | [S9](./_cache/sources/q1-2025-segment-note.md) |
| 分部 B | FY2024 | 35% | +3% | 25% | -5% | 14% | -120 bps | [S10](./_cache/sources/fy2024-segment-note.md) |
| 分部 B | Q1 2025 | 36% | +2% | 24% | -6% | 13% | -150 bps | [S9](./_cache/sources/q1-2025-segment-note.md) |
| 分部 C | FY2024 | 20% | -8% | 10% | -30% | 10% | -300 bps | [S10](./_cache/sources/fy2024-segment-note.md) |
| 分部 C | Q1 2025 | 21% | -6% | 14% | -22% | 12% | -200 bps | [S9](./_cache/sources/q1-2025-segment-note.md) |
| **整体** | **FY2024** | **100%** | **+5%** | **100%** | **+8%** | **19%** | **+50 bps** | [S11](./_cache/sources/fy2024-income-statement.md) |
| **整体** | **Q1 2025** | **100%** | **+4%** | **100%** | **+6%** | **18%** | **-20 bps** | [S12](./_cache/sources/q1-2025-income-statement.md) |

**取舍说明**：
- "利润"用什么口径要明确——优先 segment EBIT / EBITDA（公司一般会披露），其次是 segment operating income。**不要混用口径**。
- 列**只放最近一期 + 同比**——不放 5 年历史，那是流水账。如果想看趋势是否加速 / 反转，写在 (b) 的 takeaway 里。
- 如果分部数据公司不披露，要明确写"公司未披露分部利润"——这本身就是信息（披露质量差 = 估值压力 / 治理疑虑）。
- 数据有缺漏（某分部利润口径变了 / 重组中）要标注，不要假装连续。

**(b) Takeaway（2-3 句）**

表格不是终点，必须有解读。要讲清楚：
- **结构性事实**：收入结构 vs 利润结构是不是错配？哪个分部是真正的"利润引擎"？
- **方向性事实**：哪个分部在变重要、哪个在萎缩？利润率扩张 / 收缩集中在哪？
- **经济驱动 vs GAAP 分部不一样的地方**：比如"汽车公司 70% 收入来自整车，但 60% 利润来自金融子公司"——这种洞察必须在 takeaway 里给出，仅有表格不够。
- **季节性 / 拐点信号**：季度数据 vs 全年趋势是否有方向性背离？比如某分部全年利润率在扩张但最近季度已开始收窄——这可能是趋势反转的早期信号，必须在 takeaway 中指出。

> 反例（流水账）："公司分为 A、B、C 三个分部，A 主要做 X，收入占比 45%，B 主要做 Y..."——这是把表格用文字念了一遍
> 正例："公司表面是 A+B+C 三业务，但 A 贡献 65% 利润且利润率持续扩张，B/C 在量价双杀；从买方视角这其实是个 A 业务的纯标的，B/C 是干扰项"

### 3. 当前所处的资本周期阶段（必须用关键比率支撑判断）

只写"在收割期"是定性印象。判断必须用关键比率支撑，否则研究员的判断和读者的判断没有区别。

**(a) 关键比率（最少给出以下 4 项）**

| 比率 | 当前值 | 判断 | Ev |
|---|---|---|---|
| Capex / D&A | 1.8x | >1.5 重投资 / ~1.0 维持 / <0.7 收割 | [S1](./_cache/sources/cashflow-statement.md) |

| FCF / 净利润 | 0.6 | 现金转化质量；持续 < 0.7 是警告 | [S1](./_cache/sources/cashflow-statement.md) |
| 净负债 / EBITDA | 2.5x | 绝对水平 + 近 2 年变化方向 | [S2](./_cache/sources/net-debt-ebitda-bridge.md) |
| 资本返还 / FCF | 30% | 派息 + 回购占 FCF 比；判断股东回报 willingness | [S3](./_cache/sources/capital-return-bridge.md) |
| ROIC vs WACC | 14% vs 9% | 是否 value-creating（500bps 以上才算 meaningful） | [S4](https://example.com/wacc-method) [S5](./_cache/sources/roic-bridge.md) |

ROIC vs WACC 如果差距小于 200bps，要警惕"伪成长"——投得多但不创造价值。

**(b) 行业周期阶段**

行业整体在哪一阶段（产能扩张 / 竞争激化 / 整合 / 衰退）？这家公司在行业内的相对位置（领先扩张 / 跟随 / 反向收缩）？

**(c) 估值框架含义**

不同阶段决定看什么估值锚点——这一节是在为第 5 节的 valuation 工作做铺垫：
- 重投资期 → 看 capex 效率、ROIC 趋势；估值锚 EV/Sales 或 EV/EBITDA + 增长
- 维持 / 成熟期 → 看 FCF yield、资本返还 yield；估值锚 P/FCF
- 收割期 → 看资本返还节奏、剩余资产价值；估值锚 NAV / liquidation
- 困境期 → 看流动性、refinancing 能力、resilience；估值锚 EV/restructured EBITDA

如果你的"判断"和后面第 5 节用的估值框架对不上，说明这一节没真做。

### 4. 实证驱动因素：这只股票在当前 regime 下真正在跟着什么动

**这一节最容易退化成"驱动因素：油价、产量、成本"——这是教科书答案，零信息含量。**

教科书答案讲的是"什么决定基本面"。但买方要找的是**当前 regime 下市场实际交易什么**——同一只票在不同市场环境下，"真正 move 股价的变量"是不一样的。比如同一只 E&P 股票，在 2020 年 OPEC 打价格战时跟全球库存动，在 2022 年俄乌时跟地缘动，在 2024 年大选时跟美国能源政策动。

**输出格式**：列 2-3 个变量，每个给具体证据。

| 关键变量 | 证据 | 为什么是当前 regime 的关键 | Ev |
|---|---|---|---|
| EIA 周度原油库存 | 近 8 季度财报后 ±1 周内股价反应 vs 库存 surprise 的相关系数 0.7 | 市场当前焦虑短期供需平衡，不是长期需求 | [S1](https://example.com/eia-inventory) [S2](https://example.com/price-reaction-study) |

| 单井 EUR 公布数 | Q1/Q2 2024 财报后股价跌 8%/6%，EUR 数据均低于预期 | 市场在 reprice Permian 储量耗尽担忧 | [S6](https://example.com/q1-q2-earnings-release) [S7](https://example.com/eur-data) |
| 单位 OpEx | 上调 OpEx 指引那次股价 -12% | 投资人当前对成本通胀极度敏感 | [S8](https://example.com/q3-2024-call-transcript) |

**研究方法提示**：
- 看近 8 个季度财报后 ±5 个交易日的股价反应，对应是哪个 KPI 的 surprise
- 同行业公司财报错峰发布时，本股票股价是否被同行的某个 KPI 带动
- 高频数据（行业月度数据、宏观数据）公布日，股价反应模式

如果你最后输出的变量是"油价、产量、成本"，回去重做。这是教科书答案，**任何看 5 分钟年报的人都能写出来**。要找的是当前 regime 特有的、不普通的那个变量。

### 5. 当前 consensus 在哪里、什么被 priced in（必须包含反向工程）

写"PE 25x vs 历史 18x，偏贵"是卖方水平。买方要回答的是**以当前估值，市场在隐含什么假设**——然后判断"我同意 / 不同意这个假设"。这是 alpha 的起点。

**(a) Consensus 关键数字**

NTM 收入、EBITDA、EPS、关键 KPI 的卖方一致预期。最近 3-6 个月的修订方向（上修 / 下修 / 频率）。

**(b) 估值倍数对比**

| 倍数 | 当前 | 自身 5 年中位 | 同业当前 | 解读 | Ev |
|---|---|---|---|---|---|
| EV/EBITDA | 8.5x | 6.2x | 7.1x | 相对自身 +37%，相对同业 +20% | [S1](https://example.com/valuation-comps) |

正文 claim 示例：`The stock trades at 8.5x EV/EBITDA versus its 5-year median of 6.2x and peers at 7.1x. [I1](https://example.com/valuation-comps)`
| P/E | 18x | 14x | 16x | ... | [I1](https://example.com/pe-comps) |
| FCF yield | 5% | 7% | 6% | ... | [I2](https://example.com/fcf-yield-comps) |

倍数选择和**第 3 节的资本周期阶段判断要一致**——不要在第 3 节说"收割期"，第 5 节用 EV/Sales。

**(c) 反向工程：当前估值在隐含什么（这是必填、最关键）**

至少回答以下其中两个：
- **隐含增长率**：以当前 PE，按合理 ROE / payout，反推市场隐含的长期增长率是多少？这个增长率公司过去做到过吗？
- **隐含 margin**：以当前 EV/Sales，反推市场对长期 margin 的假设是多少？vs 历史平均 / vs 行业最优秀玩家？
- **Reverse DCF**：以当前股价、合理 WACC，反推所需的 5 年 FCF CAGR 是多少？
- **Bear-implied**：股价跌到 X（历史低位 / 同业最低）需要发生什么？这个情景的概率？

**示例输出**：
> "当前 EV/EBITDA 8.5x 隐含 5 年 EBITDA CAGR ~ 12%。公司过去 5 年实际 CAGR 是 7%，行业最好的同行做到 10%。要相信当前估值，需要相信 [具体假设 X 发生]。这是当前的多空分歧点。"

如果第 5 节没有反向工程，研究员只能得出"贵了 / 便宜了"的判断，无法定位**贵在哪个假设上**——而 alpha 通常就藏在某个具体的隐含假设里。

### 6. 当下市场在争论什么（3-5 句）
**不是**通用 SWOT。是"现在多空双方实际在 argue 什么"——具体到某个数据点、某个假设、某个事件。如果一时不知道，至少给出"需要查清楚的争论点"。

### 7. 对手盘需要相信什么（3-5 句）

快速写清楚反方需要相信的核心假设：
- 如果初步倾向多，空头 / 观望者必须相信什么才会继续压低估值？
- 如果初步倾向空，当前多头必须相信什么才愿意继续付这个价格？
- 哪个假设最脆、最容易被下一份数据或同业 commentary 证伪？

这一节不是完整 thesis，只是把后续 `alpha-thesis` 的 variant view 起点暴露出来。

### 8. 最近 1-3 个月叙事变化（2-4 句）
为什么现在这只股在 radar 上？发生了什么？股价反应是什么？

### 9. 下一层要问的 5 个具体问题
不是"管理层质量如何"这种空泛问题。要具体——具体到一个数字、一个事件、一份文件能回答。
- 反例："业务可持续性如何？"
- 正例："Permian 老井 decline rate 从 2023 年的 X% 是否已加速到 Y%？哪份数据可以验证（公司 Q 表 / Enverus / Rystad）？"

如果 quickread 发现收入结构复杂、segment bucket 怪、model driver 不清楚，下一步不要在 quickread 内完整展开。明确推荐 `driver-map`，让它单独拆 `Reported Bucket → Business Reality → Model Driver`。

## 反模式自查

写完后必须自检以下症状，命中就重写：

**通用**
- ❌ 出现"成立于 XXXX 年""总部位于 XXXX""管理层经验丰富"——直接删
- ❌ 引用了 5 年前的财务数据但没有给出当前结论——删
- ❌ 第 4、5、6 节看起来差不多——这三节问的是不同问题，重写
- ❌ 第 9 节的问题"再多查点资料"就能回答——太浅，重写

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

**第 3 节专项**
- ❌ 关键比率不全 / 没给数字判断（"capex 较高"而不是"capex/D&A = 1.8x，重投资期"）
- ❌ 第 3 节判断的资本周期阶段，和第 5 节用的估值锚点对不上——说明判断没真做

**第 4 节专项**
- ❌ 输出的变量是"油价 / 产量 / 成本"等教科书答案——回去找当前 regime 特有的变量
- ❌ 没有具体证据（没引用具体季度的股价反应、没给相关性数据）
- ❌ 发现 driver / bucket 怪但在 quickread 里硬写完整模型拆分 → 触发错层级，应该交给 `driver-map`

**第 5 节专项**
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

## 可选保存

默认输出到对话。用户明确要求保存时，写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-stock-quickread.md
```

本 skill 的 `artifact_policy.naming_mode = plain`。默认继续使用 `YYYY-MM-DD-<artifact>.md`；不要为了 quickread 的普通保存随意追加 qualifier。

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

## 篇幅基准

- 标准 quickread：1200-1800 字，必须保留数据表、takeaway、反向工程和下一层问题。
- 快速 triage：600-900 字，只能用于判断是否值得继续研究；若低于 600 字，通常 source / valuation / driver 不足。
- 超过 2200 字通常说明已经越界到 `company-primer`、`consensus-map`、`alpha-thesis`、`driver-map` 或 `3-statement-model / dcf-model / comps-analysis / model-update`，应拆分。
