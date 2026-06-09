---
name: stock-quickread
description: Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.
---

# Stock Quickread

Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 资料收集与 Source 验证

见 workspace `.references/runtime/research-runtime.md`——数据获取链（§1）、来源验证链（§2）、Source 优先级与纪律（§2.2）、图片获取链（§2.5）、资料收集（§2.1）。

以下仅保留 stock-quickread 特有的执行流程。每一步都是强制步骤——不可跳过、不可替换。

Windows 用户：如果 python 命令报 UnicodeEncodeError，前面加 PYTHONIOENCODING=utf-8。

```
Step 1: 方法 A — Skill("buy-side-research-skills:financial-data", "<TICKER> <market> --mode lite")
        方法 B（fallback）— python .scripts/financial-data/financial_data.py
          --market <market> --identifier <TICKER> --company-slug <slug> --mode lite
        ★ 产出: _cache/financial-data/actuals-resolved.json
        ★ 先试 A，A 失败再试 B
        ★ CLI 参数是 --identifier，不是 --ticker
        ★ market: us/cn/hk/jp/kr/tw/eu
        ★ Verify: Read 确认文件存在且 "statements" 非空
        ★ Fail → STOP. 没有 actuals 不得继续.
        ★ 如果 lite 模式缺 market_data，用 yfinance 补:
          python -c "import yfinance as yf; t=yf.Ticker('<TICKER>'); print(t.info)"

Step 2: python .scripts/evidence_ledger.py init <artifact-path> -t <TICKER>
        ★ 产出: _cache/evidence/<TICKER>.evidence.json
        ★ -t TICKER 是必填参数，不能省略
        ★ Verify: 文件存在
        ★ Fail → STOP. 不得手动创建 ledger.

Step 3: Discovery — WebSearch 找候选 source URL
        ★ 目标: ≥ 8 条候选 URL
        ★ Fail → 有多少用多少，但必须报告缺少多少.

Step 4: python .scripts/shared/verify-claim.py <url> --json（Tier 1→2→3）
        ★ 每条候选 URL 至少尝试 Tier 1 HTTP
        ★ Fail per URL → 标 [UNVERIFIED]. 全部 fail → STOP.

Step 5: python .scripts/shared/download-image.py --logo <TICKER>
        + python .scripts/shared/download-image.py <url> --output <slug>（产品图）
        ★ Logo MUST exist. Product image best-effort — [缺图] if all tiers fail.
        ★ Fail logo → STOP. 不得用 browser_take_screenshot 代替.

Step 6: Write artifact
        ★ pre_write_gate CHECK 15 自动校验（actuals/ledger/logo 文件必须存在）
        ★ 文件在 → 放行. 文件不在 → block + 给你补全命令

Step 7: python .scripts/evidence_ledger.py auto <artifact> -t <TICKER>
        + python .scripts/evidence_ledger.py lint <artifact> -t <TICKER>
        ★ auto 先跑，lint 再跑。两步 -t TICKER 都必填.
        ★ Verify: 所有 [S#] 在 ledger 中有 entry，lint 无报错
        ★ Fail → STOP. 不得手动编辑 ledger.

Step 8: python .scripts/financial-data/actuals-to-appendix.py --tickers <TICKER>
        ★ 使用 --tickers 参数（单个 ticker 也用它）
        ★ Best-effort. Fail → report and continue without appendix.
```

## ⛔ HARD GATE（不可跳过）

收到 stock-quickread 触发词后，**必须先完成 Step 1-2 才能写任何内容**：

1. Read workspace `.references/runtime/research-runtime.md` + workspace `CLAUDE.md` §5.5
2. Skill("buy-side-research-skills:financial-data", "<TICKER> <market> --mode lite") 或 fallback CLI → 等待 `actuals-resolved.json` 就绪
3. Run `python .scripts/evidence_ledger.py init <artifact-path> -t <TICKER>`

三项全部完成前，禁止 Write/Edit artifact。违反 → 研究无 source、数字无 provenance、结论无依据。

## 心法

买方读公司不是为了"懂公司"，而是为了：(1) 判断这是不是一个值得花更多时间的标的；(2) 找到下一层要问的具体问题。所以 quickread 的产出必须直奔决策有用的信息。

如果你写出来的东西像卖方初次覆盖报告，就是失败的。卖方覆盖报告的特征：业务分部按章节展开、管理层简历、5 年历史财务表、罗列所有近期事件。这些**全部不要**。

## 输出结构（严格按这个走）



> **Appendix 执行**：写 artifact 正文之前先跑 actuals-to-appendix.py，输出嵌入上方的 ## Appendix。禁止留占位符。

每一节都有篇幅上限。不到位可以更短，**绝不允许超长**。超长本身就是流水账的症状。

**Artifact 前置条件**：Write 前自动检查 actuals-resolved.json、evidence ledger、logo 文件存在。缺则 block。

### 1. 一眼看懂

#### 业务总览

先列一张表，扫一眼就知道公司几块业务、哪块是热点。**焦点选在披露的最底层**——如果部门内部产品线客户/价值链完全不同（比如 Mycronic 的 GT 部门），就拆到产品线级标 [推算]；如果部门本身是纯的（比如 ASMPT 的 SEMI），留在部门级即可。

| 业务 | 部门 | 干嘛的（大白话） | 收入占比 | 估算依据 | 市场态度 |
|---|---|---|---|---|---|
| A | PG | <一句话> | 51% | 公司披露 [S#](url) | 稳定 |
| B | GT | <一句话> | ~8% | 订单 mix + IR 口头指引 [推算] [S#](url) | 🔥 焦点 |
| C | GT | <一句话> | ~6% | 同上 [推算] [S#](url) | 🔥 焦点 |

> 收入优先取公司披露的最低层级。部门有数字用部门，产品线只有估算的标 [推算] 并**必须写估算依据和 source**（订单 mix、IR commentary、行业报告等），不能只写"估计"二字。从这张表就能看出：<一句话总结——哪个在赚钱、哪个在涨、哪个在拖>。

#### 🔥 市场现在最关心什么

以下 2-3 个产品线是当前 investment thesis 的核心。不超过 3 个——再多就不是"焦点"了。

##### 焦点 1：<产品线>（归属 <部门>，收入 <占比>）

**为什么重要**（1-2 句——为什么这是当前最大的投资叙事。每个事实 claim 句尾 `[S#](url)` 或 `[I#](url)`，技术路线/客户名/市占率/产能/订单等必须 source）

例：`TSMC SoIC 用 hybrid bonding 做 3D 堆叠 [S1](url)，BESI D2W bonder 全球唯一量产验证 [S2](url)。20 个逻辑客户 + 三大内存厂全在 eval [S3](url)。`

**长这样**（焦点产品图 1-2 张）

| ![产品](当前 topic 的 _cache/images/<slug>-<product>.png) |
|---|
| *产品名 — 功能（≤15字）* |

**在什么位置**（焦点业务的价值链）

```mermaid
flowchart LR
    A[上游] --> B[**<产品线>**<br/><做什么>] --> C[下游：<谁买单>]
```

**怎么收钱**
> 一次性设备 / 设备+耗材 / 订阅制 / 维护费。含定价/产能/客户数等事实 claim 的必须标 source。

例：> 一次性设备（hybrid bonder EUR 3-5M/台）+ 服务。产能从 ~180 台/年扩到 250 台/年 [S#](url)

##### 焦点 2：<产品线>

（同上结构——为什么重要 / 长这样 / 在什么位置 / 怎么收钱。焦点业务必须放图——找不到标 [缺图]，不能跳过。）

> 图片只放焦点业务的。其他业务不配图。下载到 `当前 topic 的 _cache/images/<slug>-<product>.<ext>`，`<ext>` 使用脚本返回的 `images[0].extension`。
>
> **下载方法**：`python .scripts/shared/download-image.py <url> --output <slug>`。Logo 模式：`--logo <TICKER>`（自动缓存，workspace 级跨 skill 共享）。图片来源优先级：① 公司 Media Kit → ② 产品页 hero → ③ web search → ④ 行业代表图 → ⑤ `[缺图]`。禁止 `browser_take_screenshot`。

#### 其他业务

- **A**：<一句话，这个业务是干嘛的、为什么不是当前焦点>
- **B**：<一句话>

#### 说人话

> 说白了就是 <最简单的类比>。

### 2. 不懂的词先看这

| 术语 | 大白话 |
|---|---|
| <术语> | <一句话> |

> 最多 5-8 个。不是词典，是聊天时怎么讲。

### 3. 钱从哪里来（数据表 + takeaway）
> 数字来源：`industry/<industry>/companies/<ticker>/_cache/financial-data/actuals-resolved.json`

**只有定性描述是片面认知**——读者无法判断哪个分部在 mattering、哪个在萎缩、哪里有异常。所以这一节由两部分组成：

**(a) 生意模式判断**：agent 先判断 business model → 路由到 workspace `.references/kpi-drivers/<template>.md` → 确定弹性指标 checklist + 2-3 个弹性比率。

**(b) 关键财务数据表（标准+弹性）**

按分部拆开（如果是单分部公司，按产品线 / 地区 / 客户类型替代），最少包含以下列。每个分部分别列出**最近一期完整年度（或最近 LTM）**和**最近一个 Q/H period**两行的数据（含同比变化）。期间拆行为独立行；period label 必须读取 `actuals-resolved.json` 的真实标签 / basis，不得把 HK H1 写成 Q2 或 Q4。

| 分部 | 期间 | 收入 | 收入占比 | 收入 YoY | 利润 | 利润口径 | 利润占比 | 利润率 | 利润率 YoY | Ev |
|---|---|---|---|---|---|---|---|---|---|---|
| 分部 A | FY2024 | 1,200 | 45% | +12% | 336 | EBIT | 65% | 28% | +2pp | [S1](./_cache/sources/company-annual-report.md) |
| 分部 B | FY2024 | 933 | 35% | +3% | 131 | EBIT | 25% | 14% | +1pp | [S10](./_cache/sources/fy2024-segment-note.md) |
| 分部 C | FY2024 | 533 | 20% | -8% | [ND]——公司未披露分部利润 | — | — | — | — | [S10](./_cache/sources/fy2024-segment-note.md) |
| **整体** | **FY2024** | **2,667** | **100%** | **+5%** | 517 | EBIT | **100%** | **19%** | +2pp | [S11](./_cache/sources/fy2024-income-statement.md) |
| 分部 A | H1 FY2025 | 620 | 43% | +8% | 161 | EBIT | 62% | 26% | -2pp | [S9](./_cache/sources/qh-segment-note.md) |
| 分部 B | H1 FY2025 | 518 | 36% | +2% | 67 | EBIT | 24% | 13% | -1pp | [S9](./_cache/sources/qh-segment-note.md) |
| 分部 C | H1 FY2025 | 302 | 21% | -6% | [ND] | — | — | — | — | [S9](./_cache/sources/qh-segment-note.md) |
| **整体** | **H1 FY2025** | **1,440** | **100%** | **+4%** | 259 | EBIT | **100%** | **18%** | -1pp | [S12](./_cache/sources/qh-income-statement.md) |

正文 claim 示例：`FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./_cache/sources/company-annual-report.md)`

**取舍说明**：

1. **口径统一（强制）**：
   - **年度 vs 季度**：FY 和 Q/H 必须用同一个利润科目（FY 用 EBIT → Q/H 也用 EBIT，不能 FY 用 EBIT、Q/H 用 Net Income）。
   - **分部 vs 整体**：分段和整体用同一个利润口径（分段列 EBIT → 整体也列 EBIT，不能分段列 Gross Profit、整体列 Net Income）。
   - **期间 label**：period label 从 `actuals-resolved.json` 真实 label/basis 读取，不得把 HK H1 写成 Q2 或 Q4。
2. **口径选择优先级**：segment EBIT > Gross Profit > Net Income。哪个口径在全部期间和分部/整体都有数据，用哪个。换了口径 → 必须标注原因。
3. **推导优先**：能算就推导（整体-分部扣减、收入×利润率），标 [推算] 且写逻辑。别急着标 [ND]。
4. **缺数诚实**：算不出来再 [ND]，别编数字。口径变了/重组了/没披露 → 标出来，不假装连续。

**(c) 弹性指标详情**（必须用表格，不可写 prose。仅当有 expandable KPI 时出现——没有就跳过整节）

| 指标 | Q/H period | FY period | Ev |
|---|---|---|---|
| <e.g. 季度订单> | <值> | <值> | [S#](url) |
| <e.g. B2B> | <值> | <值> | [S#](url) |

> 每行一个 KPI，每格必须有 source anchor。同一 source 在多行复用 → 每行各自写 `[S#](url)`，不空着。

**(d) Takeaway（2-3 句）**

表格不是终点，必须有解读。要讲清楚：
- **结构性事实**：收入结构 vs 利润结构是不是错配？哪个分部是真正的"利润引擎"？
- **方向性事实**：哪个分部在变重要、哪个在萎缩？利润率扩张 / 收缩集中在哪？
- **经济驱动 vs GAAP 分部不一样的地方**：比如"汽车公司 70% 收入来自整车，但 60% 利润来自金融子公司"——这种洞察必须在 takeaway 里给出，仅有表格不够。
- **季节性 / 拐点信号**：季度数据 vs 全年趋势是否有方向性背离？比如某分部全年利润率在扩张但最近季度已开始收窄——这可能是趋势反转的早期信号，必须在 takeaway 中指出。

> 反例（流水账）："公司分为 A、B、C 三个分部，A 主要做 X，收入占比 45%，B 主要做 Y..."——这是把表格用文字念了一遍
> 正例："公司表面是 A+B+C 三业务，但 A 贡献 65% 利润且利润率持续扩张，B/C 在量价双杀；从买方视角这其实是个 A 业务的纯标的，B/C 是干扰项"

### 4. Growth Drivers & KPIs

> agent 先判断 business model → 路由 workspace `.references/kpi-drivers/<template>.md` → 确定弹性比率 + Driver 表列。

**(a) 标准比率 pool**（从 actuals 取数，能算就算，算不出就跳过）：

> **Actuals only — 禁止用 estimate 算 ratio**：每个比率的所有 input 字段必须在 `actuals-resolved.json` 中有真实值。**任何 FY2026E / consensus / forward estimate 不能参与 ratio 计算。** 所有 input 齐全 → 输出该比率。任一 input 缺失 → **静默跳过该比率**，不标 [未披露]，不占行。最终输出的是"这个公司实际能算出来的比率"，而不是一排空表。

Agent 遍历以下 pool，逐个检查 input 字段可用性，输出能算的比率（通常 6-10 个）：

| # | 比率 | 公式 | 用途 | 所需 actuals 字段 |
|---|---|---|---|---|
| **Profitability** |
| 1 | Gross Margin | GP ÷ Rev | 定价力 | gross_profit, revenue |
| 2 | EBIT Margin | EBIT ÷ Rev | 运营利润 | ebit, revenue |
| 3 | Net Margin | NI ÷ Rev | 最终利润 | net_income, revenue |
| **Expense & Cash Quality** |
| 4 | R&D / Rev | R&D ÷ Rev | 研发重度 | r_and_d, revenue |
| 5 | Implied Opex / Rev | (GP − EBIT) ÷ Rev | SG&A+R&D 合计吃掉多少毛利 | gross_profit, ebit, revenue |
| 6 | FCF Conversion | OpCF ÷ EBIT | 利润变现 | operating_cf, ebit |
| **Asset Efficiency** |
| 7 | Asset Turnover | Rev ÷ Total Assets | 资本效率 | revenue, total_assets |
| 8 | Op ROA | EBIT ÷ Total Assets | 资产回报 | ebit, total_assets |
| 9 | Capex / Rev | CapEx ÷ Rev | 投资强度 | capex, revenue |
| 10 | D&A / CapEx | D&A ÷ CapEx | <1=扩产, >1=修旧 | depreciation, capex |
| **Shareholder** |
| 11 | FCF Yield | FCF ÷ Market Cap | 现金回报 | operating_cf, capex, market_data.market_cap |
| 12 | Net Cash | Cash − Total Debt | 安全垫 | cash, total_debt |

> 输出格式：`| # | 比率 | 值 | 判断 | 数据来源 |`，不输出无法计算的比率。

**(b) 弹性比率**（从 kpi-drivers 模板选 2-3 个，同受 actuals-only 约束，每个比率必须有 source）：

| Business Model | 弹性比率 |
|---|---|
| order-driven | Backlog / Q Rev、Orders YoY、R&D / Rev |
| process-industry | Production YoY、Utilization % |
| long-cycle | Backlog / Annual Rev |
| utility-infra | Utilization %、Capacity YoY |
| tech-manufacturing | R&D / Rev、Backlog YoY |
| saas-software | NRR、Magic Number |
| ai-emerging | Cash / Monthly Burn |

> 输出格式：`| 比率 | 值 | Ev |`，每个比率必须带 source anchor。

**(c) 弹性 Driver 表**（和 §3 同行同结构——每个分部 × FY + Q/H）：

从 kpi-drivers 模板选**actuals 里已有数据的所有 KPI** 作为列——agent 不重新搜，只读 `actuals-resolved.json` 的 supplementary/segments 字段。有值的全列，没值的标 [未披露]。例（order-driven）：

| 分部 | 期间 | Backlog | Backlog YoY | Orders | B2B | Coverage | Ev |
|---|---|---|---|---|---|---|---|
| PG | FY2025 | SEK 2,100m | +5% | 890m | 0.8x | 2.4mo | [S1](./_cache/sources/qh-segment-note.md) |
| PG | Q1 2026 | SEK 1,200m | -30% | 597m | 0.7x | 1.8mo | [S1](./_cache/sources/qh-segment-note.md) |

拿不到的标 [ND] 或 [未披露]。所有数字从 actuals/IR 算。

> 泛化兜底已在 `/financial-data` 弹性采集层完成（`supplementary.custom_metrics`）。§4 直接从 actuals 取数，不做二次搜索。

**行业周期阶段**（1 句）：产能扩张 / 竞争激化 / 整合 / 衰退？公司领先扩张 / 跟随 / 反向收缩？

### 5. 什么在驱动股价
> 数据锚点：actuals-resolved.json market_data + income_statement；股价历史：同文件缓存

第一次看的人，读完这节应该理解这家公司**到底跟什么动**，不是记住三个变量叫 X、Y、Z。

#### 这门生意怎么转（3-5 句）

用大白话讲商业逻辑——什么东西决定它赚钱还是亏钱。不是重复 §1 的类比，是讲因果。**每个事实 claim（客户名/市占率/定价/产能/竞争格局）句尾 `[S#](url)`。** 不需要行业知识就能理解。

> 例：`BESI 的生意本质是 AI capex 的杠杆 bet——TSMC/Intel/Samsung 建先进封装产线 → 买 BESI 的 hybrid bonder [S1](url)。一台设备 EUR 3-5M、交期 6-12 月 [S2](url)、用 5-8 年 [S3](url)。全球只有 BESI 能量产 D2W hybrid bonder [S4](url)，市占 ~70% [I1](url)，所以 GM 在好时候 60%+、差时候也能守 50%+ [actuals]。但 TSMC 可能占 60%+ 订单 [I2](url)，收入节奏极不均匀。`

#### 行业现在在发生什么（2-3 句）

当前行业周期的位置，以及**这对这家公司意味着什么**。不是通用行业科普。**趋势判断/产能数字/技术路线 claim 句尾 `[S#](url)` 或 `[I#](url)`。**

> 例：`2026 年是 hybrid bonding 量产化的关键年。TSMC CoWoS 从 2024 年 15K wpm → 2026 年 40K+ wpm [I1](url)，每万片需 ~10-15 台 hybrid bonder [I2](url)。HBM4 将在 2027 年开始用 hybrid bonding——BESI 是唯一通过三大内存厂 eval 的设备商 [S1](url)。但 TCB 市场有韩美半导体/Hanwha 追 [I3](url)，AMAT Kinex 是潜在 second source [I4](url)。`

#### 真正跟着什么动（2-3 个变量）

每个变量一个子节。不是扔关键词——是从上面的生意逻辑和行业变化推导出来的。

##### 变量名（一句话——这个变量怎么驱动股价）

**数据锚点**（来自 financial-data）

| 指标 | 当前 | 历史区间 | 来源 |
|---|---|---|---|
| <相关 metric> | <值> | <min — max> | [S#](...) |

**市场在讲什么故事**（1-2 句——多方/空方各自的观点和依据，每个 claim 标 source）

例：`多方说 hybrid bonding adoption 加速——20 个逻辑客户、三大内存厂 eval [S#](url)。空方说 TSMC 占 60%+ 订单 [I#](url)，且 Q1 有 pull-in 效应 [I#](url)。`

**最近一次怎么动的**（1 句——这个变量变化时股价怎么反应）[S#](...)

**什么时候可能不灵**（1 句——历史上哪个季度这个变量和股价背离了，标 source）[S#](...)

**情绪在怎么变**（1 句——最近分析师/市场的态度微妙变化）[S#](...)

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
> 估值倍数：actuals-resolved.json market_data；Consensus：同文件 consensus 字段（best-effort）

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

以下四项全部回答（**每个输入参数必须标注来源**——PE/EV/Sales 来自 market_data，FCF/CapEx 来自 actuals，ROE/WACC 引用计算依据，历史增长引用 actuals 或第三方 source）：

- **隐含增长率**：以当前 PE [I#](url)，按合理 ROE / payout [S#](url)，反推市场隐含的长期增长率是多少？这个增长率公司过去做到过吗 [S#](url)？
- **隐含 margin**：以当前 EV/Sales [I#](url)，反推市场对长期 margin 的假设是多少？vs 历史平均 / vs 行业最优秀玩家？
- **Reverse DCF**：以当前股价 [I#](url)、合理 WACC [推算——引用计算依据]，反推所需的 5 年 FCF CAGR 是多少？
- **Bear-implied**：股价跌到 X（历史低位 / 同业最低）需要发生什么？这个情景的概率？

**示例输出**：
> "当前 EV/EBITDA 8.5x 隐含 5 年 EBITDA CAGR ~ 12%。公司过去 5 年实际 CAGR 是 7%，行业最好的同行做到 10%。要相信当前估值，需要相信 [具体假设 X 发生]。这是当前的多空分歧点。"

如果第 6 节没有反向工程，研究员只能得出"贵了 / 便宜了"的判断，无法定位**贵在哪个假设上**——而 alpha 通常就藏在某个具体的隐含假设里。

### 7. 多空在争论什么
**不是**通用 SWOT。是"现在多空双方实际在 argue 什么"——具体到某个数据点、某个假设、某个事件。**每方的每个具体 claim 必须有 source anchor**（卖方报告、IR call、行业数据）。如果一时不知道，至少给出"需要查清楚的争论点"。

例：
- **多方**：BESI 是全球 hybrid bonding 绝对龙头，市占 ~70% [I1](url)，TSMC/Intel/Samsung 全在客户名单 [S1](url)。Q1 订单 +104.5% YoY [S2](url)。
- **空方**：EV/Rev 38x——买的是 2028 年收入不是 2025 年 [I2](url)。TSMC 可能占 60%+ 收入 [I3](url)。分析师 target EUR 189-239，当前 EUR 285 已跑赢所有卖方目标 [I4](url)。

### 8. 对手盘需要相信什么

快速写清楚反方需要相信的核心假设。**引用的具体数字/事件标 source：**
- 如果初步倾向多，空头 / 观望者必须相信什么才会继续压低估值？[I#](url)
- 如果初步倾向空，当前多头必须相信什么才愿意继续付这个价格？[I#](url)
- 哪个假设最脆、最容易被下一份数据或同业 commentary 证伪？[S#](url)

这一节不是完整 thesis，只是把后续 `alpha-thesis` 的 variant view 起点暴露出来。

### 9. 最近在发生什么
> 股价：actuals-resolved.json market_data（yfinance 缓存）；事件：web search

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

## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## 反模式自查

写完后自检，命中就重写：

**通用**
- ❌ 出现"成立于""总部位于""管理层经验丰富"——直接删
- ❌ 第 5、6、7 节看起来差不多——它们问的是不同问题
- ❌ 第 10 节的问题"再多查点资料"就能回答——太浅
- ❌ 任何 factual claim（数字、事件、引语）无 source anchor

**Source 密度（写完后逐段扫）**
- ❌ §1 焦点 "为什么重要"：0 个 source → 重写
- ❌ §5 "这门生意怎么转"：0 个 source → 重写
- ❌ §5 "行业现在在发生什么"：0 个 source → 重写
- ❌ §5 "市场在讲什么故事"：0 个 source → 重写
- ❌ §5 "什么时候可能不灵"：0 个 source → 重写
- ❌ §7 多空双方 claim 没有 source → 重写
- ❌ §8 对手盘假设引用的数字/事件没有 source → 重写
- ❌ 任何段落出现连续 3 句以上事实 claim 而中间没有 source anchor → 密度不够

**§3 分部表**
- ❌ 数据表但没有 takeaway
- ❌ Takeaway 用文字把表格念了一遍

**§4 比率**
- ❌ pool 遍历不全 / 能算的不算

**§5 驱动因素**

## 保存

写入公司 primary 行业目录：
```
industry/<industry-slug>/companies/<ticker>/YYYY-MM-DD-stock-quickread-<company-slug>.md
```

- 路径不明 → 先 handoff `agent` 解析行业和公司。
- 公司 qualifier 从 company slug 提取（如 `mycronic`、`robotchnik`）。

## 篇幅基准

- 标准 quickread：1800-2500 字。低于 1800 说明 §5 驱动因素展开不足——这是全文最有信息量的节。超过 2500 说明在替 `company-history` 或 `driver-map` 干活，应拆分或去重。


