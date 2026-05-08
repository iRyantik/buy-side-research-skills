# Buy-Side Research Skills System — 最终框架

> **文档目的**：作为整个 buy-side research skills 系统的设计蓝图。
> **使用方式**：所有 skill 设计、状态文件 schema、workflow 串联都参考此文件。
> **修改原则**：本文件是 skill/system design blueprint，受 `CLAUDE.md` 约束。全局工作风格、source policy、反幻觉和反流水账规则以 `CLAUDE.md` 为唯一 constitution；skill 设计和状态文件 schema 参考本文件。
> **版本**：v2.2 (2026-05-08)

---

## 1. 研究员上下文与系统边界

### 1.1 我是谁

- **身份**：LS（Long-Short）对冲基金研究员
- **坐标**：亚洲（时区会影响美股 post-print 工作流）
- **覆盖市场**：大中华 + 全球（美日韩欧为主）
- **覆盖行业**：industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes

### 1.2 LS 工作的本质特征（决定系统设计）

| 特征 | 系统含义 |
|---|---|
| **双向都看** | 每个 thesis 自带"另一边怎么走"；空头 thesis 和多头 thesis 同等重要 |
| **Pair trade 是核心工具** | 不是 nice-to-have；必须有专门 skill 支持 |
| **跨市场惯性** | 同一公司多重上市、可比公司跨市场对比是常态；需专门 skill |
| **时区 disadvantage** | 美股财报后才工作；post-print 快速判断必须高效 |
| **持仓 vs 标的** | 不像 long-only，LS 持仓有 long + short 双面，需 separate tracking |

### 1.3 最痛的工作（系统优先解决的）

> **信息淹没**：信息太多、单个公司花的时间少、容易被淹没。

这是系统设计的**第一原则**——所有 skill 都要服务于"降低认知负担"，而不是"产出更多 / 更长的报告"。

### 1.4 系统**不**做的事（明确边界）

- 不做量化策略 / 系统化交易
- 不替代 PM 的最终决策
- 不替代我对"读"的工作（系统帮我处理输入，但读和判断仍是我的事）

---

## 2. 设计哲学（5 个核心原则）

### 2.1 服务"决策时刻"，不是"输出文档"

Skill 不应该按"输出形式"切（thesis、memo、report），应该按"研究员在哪个决策时刻调用"切。

- ❌ "写一份 X 公司的研究报告" → 模糊
- ✅ "决定要不要建仓 X" / "决定 X 财报后加减仓" / "决定建立 X-Y pair" → 具体

### 2.2 LS 视角默认（双向 thesis）

- 任何 thesis 类的 skill 都默认双向考虑
- alpha-thesis 第一步就问 "long / short / pair"，不是默认 long
- peer-deep-dive 的 pair trade section 默认 enabled（不是可选）
- 所有 catalyst / kill-criteria / sizing 都按方向调整

### 2.3 降低认知负担优先

针对"信息淹没"痛点：

- **每个 skill 输出第一行必须是"决策 / 判断"**，不是 context 铺垫
- **多数情况输出极短**——只有研究核心（quickread / thesis）才允许 1500+ 字，其他 skill 默认 < 500 字
- **状态文件顶部必须有一页摘要**：一句话 thesis + 健康度 + 下一个 catalyst
- **information-impact 是核心防淹没工具**——把信息流过滤成 actionable signals、monitor 项，或直接 Drop

### 2.4 状态文件是 skills 之间的 connector

- 所有 skills 通过本地 markdown 文件 share 状态
- 不是每次都重新生成——读取现有文件 + 增量更新
- 避免 "孤岛 skills"——每个 skill 都明确知道读什么 / 写什么

### 2.5 精简到核心，长尾用元方法论或自由对话

- 12 个 core skills 是当前上限——新增 skill 必须解决高频决策痛点，不能只是文档形态变化
- idea screening 已由 `candidate-screener` 覆盖；其他低频工作（portfolio review 等）暂不做 skill，用自由对话
- 行业 KPI 走元方法论（peer-deep-dive 已实现），不穷举

---

## 3. 系统总览：6 模块 + 12 个 skills

### 3.1 全景图

```
┌─────────────────────────────────────────────────────────────┐
│  模块 1：标的研究（Research）              5 个 skills        │
│   - candidate-screener (主题 / 条件 → 候选股票漏斗)           │
│   - stock-quickread (新公司 30 分钟入门)                     │
│   - peer-deep-dive  (N 家同业并行深入)                       │
│   - alpha-thesis    (构建 LS thesis)         ⚡ LS 改造      │
│   - bear-pre-mortem (空头压力测试)                           │
├─────────────────────────────────────────────────────────────┤
│  模块 2：建模（Modeling）                  1 个 skill         │
│   - financial-model (Revenue-first model / 财报后更新)       │
├─────────────────────────────────────────────────────────────┤
│  模块 3：跨市场（Cross-Market）            1 个 skill         │
│   - cross-market-compare (A/H、ADR、跨市场可比公司)          │
├─────────────────────────────────────────────────────────────┤
│  模块 4：持仓维护（Portfolio）             3 个 skills        │
│   - thesis-tracker   (Thesis 健康度 + Catalyst pipeline)    │
│   - pair-trade       (Pair 构建 + 监控)      ⚡ LS 核心      │
│   - decision-journal (建仓 / 调仓 / 平仓记录)               │
├─────────────────────────────────────────────────────────────┤
│  模块 5：事件 & 信号（Events）             2 个 skills        │
│   - earnings-setup     (财报前后)            ⚡ LS 改造      │
│   - information-impact (新闻 / 卖方 / 数据 → 影响判断)       │
│                                              ⭐ 防淹没核心   │
└─────────────────────────────────────────────────────────────┘

  [模块 6：复盘 & 学习]   暂不做 skill，用 decision-journal + 自由对话凑合
```

### 3.2 现状统计

| 状态 | 数量 | 名单 |
|---|---|---|
| ✅ v1.2 已对齐 | 5 | stock-quickread、peer-deep-dive、alpha-thesis、bear-pre-mortem、earnings-setup |
| ✅ v2.0 已 scaffold | 5 | cross-market-compare、thesis-tracker、pair-trade、decision-journal、information-impact |
| ✅ v2.1 skeleton | 1 | financial-model |
| ✅ v2.2 已新增 | 1 | candidate-screener |

---

## 4. 各 Skill 详细职责

### 4.1 模块 1：标的研究

#### `candidate-screener` ✅（v2.2）

- **触发**：
  - "找 AI 数据中心电力受益股"
  - "找 EV/EBITDA < 8x + FCF yield > 8% 的能源股"
  - "Trump 关税受损方有哪些"
  - "找类似 NVDA 在 A 股的标的"
- **定位**：outbound idea funnel，从 hypothesis / 主题 / 事件 / 条件筛选生成候选股票；不是验证单条传闻，也不是替代 Bloomberg / FactSet screener。
- **核心原则**：
  - LS 默认双向：long basket + short basket。
  - 每个 candidate 必须有 business linkage source，不允许概念股堆砌。
  - 必须评估 priced-in 程度和 hypothesis 漏洞。
  - 最后推荐 1-2 家进入 `stock-quickread` / `peer-deep-dive` / `pair-trade`。
- **边界**：`candidate-screener` 是 outbound（hypothesis → candidates）；`information-impact` 是 inbound（known claim → verdict + portfolio impact）。
- **状态文件**：→ 写入 `screens/[hypothesis-slug]-[YYYY-MM-DD].md`

#### `stock-quickread` ✅（轻度 LS 改造）

- **触发**：不熟的公司想 30 分钟过一下
- **现状**：已有完整版本（用户最近更新版）
- **LS 改造点**：
  - 第 5 节"市场在争论什么"加一行："**对手盘需要相信什么**"——即如果做空 / 做多，对手方在赌什么
- **输出篇幅**：1200-1800 字 + 3 张数据表（不变）
- **状态文件**：→ 写入 `quickreads/[ticker]-[YYYY-MM-DD].md`

#### `peer-deep-dive` ✅（中度 LS 改造）

- **触发**：N 家同业（3-8 家）已选定都要看，并行处理
- **现状**：已有完整版本 + 9 个行业模板 + 元方法论
- **LS 改造点**：
  - 原第 5B 节"Pair / Cluster 建议"是可选的 → **改为默认必填**
  - 必须明确给出 1-3 个 pair 候选 + 论点 + spread 历史触发条件，或明确说"无明显 pair 机会，因为 [具体理由]"
  - 各公司的 "Thesis 苗头" 不只是 long / short / 中性，新增 "pair 候选对手"字段
- **输出篇幅**：N 线性 scale（不变）
- **状态文件**：→ 写入 `peers/[industry]-[YYYY-MM-DD].md`

#### `alpha-thesis` ✅（重度 LS 改造）

- **触发**：建立 / 整理一个 thesis（可拿去 pitch 给 PM）
- **现状**：已有完整版本，默认 long-only 思维
- **LS 改造点**：
  - **新增第 0 节"Trade Structure"**：开头明确 thesis 类型
    - **Long-only**: 单边做多
    - **Short-only**: 单边做空
    - **Pair**: long X + short Y（必须 spec 配对标的）
    - **Long with hedge**: 主仓位 + 对冲（spec hedge 工具）
  - 后续所有节（catalyst、kill criteria、sizing、bull/base/bear）都按 trade structure 调整
  - 如果是 pair，bull/base/bear 表格变成 spread 收敛的情景
  - Variant view 必须从 LS 双向考虑：你的 view 和 long consensus 差多少 / 和 short consensus 差多少
- **输出篇幅**：800-1500 字（不变；如是 pair，可上调到 1000-1800）
- **状态文件**：→ 写入 `coverage/[ticker]/thesis.md`（或 pair 写入 `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`）

#### `bear-pre-mortem` ✅（不需改造）

- **触发**：对一个 thesis 做空头压力测试
- **现状**：已有完整版本
- **LS 改造**：**不需要**——本身就是 LS 思维（设想自己错了 + 对手是聪明的空头）
- **特殊用法**：对 short thesis 也能用——只是把"空头压测"换成"多头压测"，方向反过来
- **状态文件**：→ 写入 `coverage/[ticker]/bear-case.md`

---

### 4.2 模块 2：建模

#### `financial-model` ✅（v2.1 skeleton）

- **触发**：
  - "搭一个 model"
  - "帮我拆收入"
  - "根据新财报更新模型"
  - "更新已有 Excel model"
- **两种模式**：
  1. **Build New Model**：搭新的 buy-side Excel model，第一版重点是 revenue split / segment drivers。
  2. **Update Existing Model**：根据新财报更新各种样式的已有 Excel model。
- **核心原则**：
  - 新建模型采用轻骨架，不强制固定 5-sheet 模板。
  - 更新已有模型时保留原 workbook 的 sheet、布局、公式、格式。
  - 不把已有模型迁移成标准模板。
  - 无法可靠定位 actual / forecast 区时，只输出 update map，不直接改 workbook。
- **输出重点**：
  - Revenue architecture：reported segment → revenue stream → observable driver。
  - Source map：actuals、segment data、guidance、consensus、model assumptions 的 source / as-of。
  - Missing disclosure：公司不披露 driver 时明确标记，不编造。
  - Thesis read-through：模型更新是否改变 variant view、catalyst、kill criteria 或 action。
- **状态文件**：→ 默认写入 / 更新 `coverage/[ticker]/model.xlsx`

---

### 4.3 模块 3：跨市场

#### `cross-market-compare` ✅（v2.0 scaffold）

- **触发**：
  - "X 公司 A 股 vs ADR 比较"
  - "宁德 vs 松下 vs LG 比一下"
  - "台积电 vs 三星 vs Intel"
  - "腾讯港股 vs ADR 套利空间"
- **核心问题**：跨市场比较有传统单市场比较没有的 dimension
  - 汇率（看的是 USD-equivalent 还是 local？）
  - 估值锚（A 股给科技股的倍数 vs 美股 vs 港股 vs 日韩）
  - 流动性差异（小盘 ADR 流动性 issue）
  - Disclosure 标准（A 股披露 vs 10-K vs annual report 详尽度）
  - 多重上市套利空间（A/H premium、ADR vs 主板）
  - 监管 / 政策风险溢价（中概股、A 股 IPO 政策、日韩外资限制）
  - 投资者结构（A 股散户主导 vs 美股机构主导，影响估值习惯）
- **输出结构**（当前发布版）：
  1. 跨市场标的列表 + 上市信息
  2. 估值倍数表（必须 normalize 到同一货币 + 同一会计准则尽可能）
  3. 流动性 + 投资者结构对比
  4. 估值 spread 解读（合理 vs 不合理）
  5. Pair / 套利机会
  6. 监管 / 政策风险差异
  7. 跨市场 thesis 建议
- **输出篇幅**：1500-2500 字 + 2-3 张表
- **状态文件**：→ 写入 `cross-market/[group-name]-[YYYY-MM-DD].md`

---

### 4.4 模块 4：持仓维护（**最大缺口，P0 优先级**）

#### `thesis-tracker` ✅（v2.0 scaffold，合并 health-check + catalyst-tracker）

- **触发**：
  - 周度 / 月度："review 一下我所有持仓 thesis 健康度"
  - 单标的："X 的 thesis 还成立吗"
  - 事件后："Y 财报 / 新闻后，X 的 thesis 受什么影响"
- **核心功能（双合一）**：
  1. **Thesis Health Check**：把 alpha-thesis 中的"key assumptions" + "kill criteria" 拿出来对照实际数据，给健康度评分
  2. **Catalyst Pipeline**：按时间排序所有持仓的下一个 catalyst（财报、conference、政策事件、同行 read-across）
- **输出结构**：
  1. **持仓健康度表**（每个持仓一行）
     | Ticker | 方向 | 建仓日期 | 当前 P/L | Thesis 健康度（绿/黄/红） | 主要 assumption 状态 | 距 kill criteria 多远 |
  2. **Catalyst 时间线**（按日期排序，未来 8 周）
     | 日期 | Ticker | 事件类型 | 对 thesis 重要性 | Pre-print prep 是否做完 |
  3. **需要 attention 的标的**（健康度黄 / 红的，列出具体问题）
  4. **行动建议**（哪个标的需要 thesis 重审 / 触发 bear-pre-mortem 重做 / 考虑减仓）
- **输出篇幅**：跟持仓数 scale，单标的 ≤ 200 字，整体 review 不超 1500 字
- **状态文件**：
  - 读取：所有 `coverage/[ticker]/thesis.md` 和 `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`
  - 写入：`coverage/[ticker]/health-log.md`（追加式）和 `portfolio/catalyst-pipeline.md`

#### `pair-trade` ✅（v2.0 scaffold，合并 builder + monitor）

- **触发**：
  - 构建："X 和 Y 适合做 pair 吗" / "帮我找 X 的 hedge"
  - 监控："我的 X / Y pair 现在怎么样"
- **两模式**：

**Mode A: Pair Builder**
- 输入：候选标的 X（multi）和 Y（short）
- 工作流：
  1. 业务相关性分析（终端市场、上游、下游 overlap 程度）
  2. 估值 spread 历史（5Y、3Y、1Y）
  3. Beta / correlation（180D）
  4. 对宏观敏感度差异（利率、汇率、商品）
  5. **Pair 论点**：为什么 X 应该 outperform Y（必须有具体的 fundamental 差异，不是"X 看起来更好"）
  6. **入场触发条件**：spread 到什么位置入场
  7. **退出触发条件**：spread 收敛 / 论点失效 / 单边击穿
  8. **风险**：Pair 失效的最常见模式（macro shock、行业 re-rating、单边公司事件）
- 输出 800-1200 字 + spread 历史图（描述）

**Mode B: Pair Monitor**
- 输入：现有 pair（从 `pairs/[LONG_TICKER]-[SHORT_TICKER]/` 读取）
- 工作流：
  1. 当前 spread vs 入场 spread vs 历史 range
  2. 论点健康度（X 和 Y 的基本面 differential 是否在变化）
  3. P/L 来源拆解（是 X 多头赚的、Y 空头赚的、还是 spread 收敛赚的？）
  4. 是否有迹象 pair 应平掉（论点 played out / 论点失效 / 风险升温）
- 输出 ≤ 500 字
- **状态文件**：
  - 读取：`pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md`、`pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md`
  - 写入：追加 `pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md`（每次监控）

#### `decision-journal` ✅（v2.0 scaffold，**最重要的状态 skill**）

- **触发**：每次建仓 / 加仓 / 减仓 / 平仓
- **核心理念**：决策时刻必须**结构化**记录，事后才能复盘真正学到东西。如果决策只在脑子里，几个月后看 P/L 你只能讲故事，无法分辨"对的判断" vs "运气"。
- **输出结构**：必须使用 §6.3 的 `decision_v1` YAML entry 追加到 `journal/decisions.md`；正文解释可以跟在 YAML block 后面，但不得省略 schema 字段。
- **最小 entry 字段**：`decision_id`, `date`, `ticker`, `trade_structure`, `action`, `direction`, `position_gross_pct`, `position_net_pct`, `price_at_decision`, `valuation_at_decision`, `conviction`, `expected_upside_pct`, `expected_downside_pct`, `time_horizon`, `entry_trigger`, `source_of_edge`, `linked_thesis`, `sources`

- **关键约束**：
  - 建仓 / 加仓 / 减仓 / 平仓时必须完整填写 `decision_v1` 字段
  - 平仓可以追加 outcome 字段或新 close entry；不得改写原始 open/add/trim entry
  - 不允许事后修改原始判断字段（否则失去复盘价值）
- **输出篇幅**：单 entry 300-500 字
- **状态文件**：→ 追加到 `journal/decisions.md`

---

### 4.5 模块 5：事件 & 信号

#### `earnings-setup` ✅（中度 LS 改造）

- **现状**：已有，pre-print + post-print 两模式
- **LS 改造点**：
  - **Pre-print mode**：原"asymmetric setup 判断"改为"双向 asymmetric"——分别判断 beat scenario 和 miss scenario 的股价反应
  - **Post-print mode**：决策树新增分支——"对相关 pair / hedge 的影响"
    - 如果该标的是 pair 中的一边，pair partner 是否需要同时调整？
    - 如果该标的的财报有 read-across（例：台积电财报后 read-across 到设备厂、AI 厂），那 watchlist / 持仓中相关标的怎么办？
- **状态文件**：
  - Pre-print：写入 `coverage/[ticker]/earnings-setup-[date].md`
  - Post-print：触发 `decision-journal`（如有调仓）和 `thesis-tracker` 更新

#### `information-impact` ✅（v2.0 scaffold，**防信息淹没核心工具**）

- **触发**：
  - "看一下这条新闻对我的持仓有什么影响"
  - "这个消息靠谱吗"
  - "XX 公司是不是进了 SpaceX 供应链"
  - "这条供应链传闻有没有 source"
  - "帮我查这个 claim 能不能信"
  - "Goldman 这份卖方报告关键点 + 我同不同意"
  - "刚出的 EIA 数据 / PMI / 政策"
  - 任何 inbound 信息片段
- **核心理念**：研究员一天会看到大量信息（新闻、研报、数据点、Twitter、专家观点、供应链传闻）。**不是每条都需要深入分析**——先判断 claim 是否成立，再决定是否进入 portfolio impact。这个 skill 的核心价值是 **noise reduction + claim verification**，不是 deep analysis。
- **两模式**：
  - **Mode A: Claim Check**：先判断消息 / 传闻本身是否成立，尤其适合"XX 公司接入 SpaceX / Tesla / 军工 / 核电供应链"这类 claim。
  - **Mode B: Portfolio Impact**：只有 claim 至少达到 `Plausible but unconfirmed`，且命中 portfolio / watchlist 时，才判断对 thesis 的影响。

**Mode A: Claim Check 输出格式**（默认 1 页内）：

```markdown
## Claim Check

**Verdict**: Confirmed / Likely / Plausible but unconfirmed / Unsupported / Contradicted
**Bottom line**: [一句话判断，直接说能不能信]

| Claim piece | Evidence found | Source quality | Read-through |
|---|---|---|---|
| [claim拆分项] | [证据摘要] | A/B/C/D | direct / indirect / not proven |

**What would make it real**
- [还缺的关键证据]

**What not to infer**
- [不能从该消息外推出什么]

**Next action**
- Drop / Monitor / Log to inbox / Trigger thesis review / Ask IR / Search filings
```

- **Claim 拆解字段**：
  - `company`
  - `customer / program`（例：SpaceX / Starlink / Starship）
  - `product_or_role`
  - `relationship_type`（direct supplier / tier-2 supplier / partner / speculative exposure）
  - `timeframe`
- **Verdict 规则**：
  - `Confirmed`: 有一手 source 明确支持 claim。
  - `Likely`: 没有一手完整确认，但多个独立高质量 source 互相支持。
  - `Plausible but unconfirmed`: 产业链逻辑合理，但关键客户名、合同、认证、量产或收入贡献没有证实。
  - `Unsupported`: 只有社媒、论坛、聊天记录、券商转述或模糊媒体，没有可验证证据。
  - `Contradicted`: 找到明确反证，或 claim 和原文 source 不匹配。
- **Source 质量分级**：
  - A: filing、IR、earnings call、客户官方公告、监管 / 采购文件
  - B: Reuters / Bloomberg / FT / WSJ 等权威报道，且 claim 和 URL 内容匹配
  - C: 公司新闻稿、行业媒体、供应链数据库、专家访谈，需要交叉验证
  - D: 社媒、论坛、聊天记录、券商转述，只能作线索
- **强制区分**：
  - direct supplier
  - tier-2 / indirect supplier
  - product can be used
  - market concept / theme association
- **落盘规则**：
  - `Unsupported` / `Contradicted` 默认不写入 `inbox/information-log.md`，除非用户明确要求留痕。
  - `Confirmed` / `Likely` / `Plausible but unconfirmed` 只有命中 portfolio / watchlist 且达到 Medium / High impact 时，才进入 Mode B 并追加到 `inbox/information-log.md`。

**Mode B: Portfolio Impact 输出格式**（极短，30 秒可读完）：

```
## Information Impact

**Source**: [标题 + URL + 日期]
**Type**: 公司新闻 / 行业新闻 / 卖方观点 / 数据点 / 监管事件 / 宏观

**Relevance to portfolio** (核心判断):
| Ticker | 持仓方向 | 影响方向 | 强度 | 行动 |
|---|---|---|---|---|
| AAPL | Long | Confirming | Medium | 归档到 thesis-tracker |
| TSLA | Short | Contradicting | High | 触发 thesis 重审 |
| NVDA | Watchlist | Neutral | Low | 归档 |

**Key takeaway** (≤ 50 字): [一句话本质]

**Open questions** (最多 3 条):
1. [需要进一步追的具体问题]

**Action queue**:
- [ ] [具体下一步行动，如有]
```

- **特殊路径：无相关性时**

```
## No portfolio relevance — not logged by default

[标题] - [一句话总结] - 不落盘原因：[未命中 portfolio / watchlist 或仅为 unsupported claim]
```

- **输出篇幅上限**：500 字，绝不能超
- **强制约束**：
  - 必须 link 到具体 portfolio / watchlist 标的，不允许写"对行业有影响"这种空话
  - 强度评级（Low / Medium / High）必须给具体定义：
    - Low: 不改变 thesis，归档参考
    - Medium: 加入 thesis-tracker 监控队列，下次 health check 时复盘
    - High: 当下触发 thesis 重审或调仓决策
  - 如果信息有内部矛盾或不确定，明确标注，不要硬给方向
  - 搜索结果标题、论坛、社媒、聊天记录、券商转述不能当作已验证事实
- **状态文件**：→ 仅当命中 portfolio / watchlist 且达到 Medium / High impact，或用户要求留痕时，追加到 `inbox/information-log.md`，触发其他 skill 的 inputs

---

## 5. LS 改造统一说明

### 5.1 改造范围

| Skill | 改造程度 | 改造点 | 工作量 |
|---|---|---|---|
| stock-quickread | 轻度 | 第 5 节加"对手盘相信什么" | 加 1 行 + 1 段说明 |
| peer-deep-dive | 中度 | Pair section 默认 enabled + Thesis 苗头加 pair 字段 | 改 5B 节 + 改 differential profile 模板 |
| alpha-thesis | 重度 | 新增第 0 节"Trade Structure" + 后续节按 structure 调整 | 重写 thesis 结构 |
| bear-pre-mortem | 无 | 不改（本身已是 LS 思维） | 0 |
| earnings-setup | 中度 | 双向 asymmetric + post-print 加 pair 影响 | 改 pre-print 决策节 + 加 post-print pair 分支 |

### 5.2 LS 视角的核心 reframe

每个 thesis-related skill 都应明确回答：

1. **Direction**：Long / Short / Pair / Hedge（不是默认 long）
2. **What's on the other side**：对手盘是谁、相信什么、为什么和我相反
3. **What kills both sides**：thesis 失效的情景（不只 my side 失效，对手盘 thesis 失效也要想）
4. **Pair candidate**：即使是单边 thesis，理论上的 pair 对手是谁

---

## 6. 状态文件设计（本地 markdown）

### 6.1 目录结构

```
[project-root]/
├── CLAUDE.md                          # 项目宪法
├── FRAMEWORK.md                       # 本文件
│
├── coverage/                          # 单标的研究
│   └── [ticker]/                      # 每个标的一个目录
│       ├── thesis.md                  # 当前 thesis（alpha-thesis 写）
│       ├── model.xlsx                 # Revenue-first model（financial-model 写 / 更新）
│       ├── bear-case.md               # 空头压力测试（bear-pre-mortem 写）
│       ├── earnings-setup-[date].md   # 财报 setup（earnings-setup 写）
│       └── health-log.md              # Thesis 健康度历史（thesis-tracker 写）
│
├── pairs/                             # Pair trade 维护
│   └── [LONG_TICKER]-[SHORT_TICKER]/  # 每个 pair 一个目录（如 XOM-CVX）
│       ├── thesis.md                  # Pair 论点（pair-trade 写）
│       └── spread-log.md              # Spread 监控历史（pair-trade 写）
│
├── peers/                             # Peer deep dive 产出（一次性）
│   └── [industry]-[YYYY-MM-DD].md
│
├── quickreads/                        # Quickread 产出（一次性）
│   └── [ticker]-[YYYY-MM-DD].md
│
├── screens/                           # Candidate screener 产出（一次性）
│   └── [hypothesis-slug]-[YYYY-MM-DD].md
│
├── cross-market/                      # 跨市场比较产出
│   └── [group-name]-[YYYY-MM-DD].md
│
├── portfolio/                         # 组合层面
│   └── catalyst-pipeline.md           # 全持仓 catalyst 时间线（thesis-tracker 维护）
│
├── inbox/                             # 信息流处理
│   └── information-log.md             # information-impact 追加日志
│
└── journal/                           # 决策日志
    └── decisions.md                    # 所有建仓 / 调仓 / 平仓决策（decision-journal 追加）
```

### 6.2 文件 schema 摘要

| 文件 | 写入者 | 读取者 | 累积 vs 替换 |
|---|---|---|---|
| `coverage/[t]/thesis.md` | alpha-thesis | thesis-tracker、bear-pre-mortem、earnings-setup | 替换式（每次完整重写，但保留历史 commit） |
| `coverage/[t]/model.xlsx` | financial-model | alpha-thesis、earnings-setup、thesis-tracker | 原生 Excel；更新时保留原 workbook 结构 |
| `coverage/[t]/health-log.md` | thesis-tracker | 自身（看历史趋势） | 追加式 |
| `coverage/[t]/bear-case.md` | bear-pre-mortem | thesis-tracker、alpha-thesis | 替换式 |
| `screens/[hypothesis-slug]-[YYYY-MM-DD].md` | candidate-screener | stock-quickread、peer-deep-dive、pair-trade | 替换式（一次筛选一次文件） |
| `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md` | pair-trade (builder mode) | pair-trade (monitor mode) | 替换式 |
| `pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md` | pair-trade (monitor mode) | 自身 | 追加式 |
| `portfolio/catalyst-pipeline.md` | thesis-tracker | 多个 skills | 替换式 |
| `inbox/information-log.md` | information-impact | thesis-tracker、自身 | 追加式 |
| `journal/decisions.md` | decision-journal | trade-postmortem（未来）、自身 | 追加式（不可改前半部分） |

### 6.3 最小 YAML schema（状态文件可读契约）

只给后续 skill 会读取的状态文件加最小 schema；正文仍然用 markdown 写研究判断。ticker 使用 Bloomberg-style canonical ticker（如 `XOM`、`700.HK`、`ASML.NA`），pair 目录使用 `pairs/[LONG_TICKER]-[SHORT_TICKER]/`。

#### `coverage/[ticker]/thesis.md`

```yaml
---
schema_version: 1
document_type: thesis
ticker: XOM
company_name: Exxon Mobil
coverage_area: oil_gas
industry: integrated_oil_gas
trade_structure: long
direction: long
pair_id: null
created_at: 2026-05-07
updated_at: 2026-05-07
conviction: 7
health_status: green
time_horizon: 12m
valuation_anchor: EV/EBITDA
expected_return_base_pct: 20
downside_pct: -12
next_catalyst:
  date: 2026-07-31
  type: earnings
  description: Q2 2026 results
key_assumptions:
  - id: A1
    text: Upstream FCF breakeven remains below peer median
    metric: FCF breakeven oil price
    current_value: null
    kill_threshold: null
    source: "[source link or 来源待补]"
kill_criteria:
  - id: K1
    text: Capital discipline breaks relative to stated framework
    metric: capex_vs_guidance
    threshold: null
    action: review
sources:
  - claim: Baseline financials and operating metrics
    source_name: "[10-K / 10-Q / IR deck]"
    url: ""
    as_of: 2026-05-07
---
```

字段约束：
- `coverage_area`: `industrials`, `aerospace_defense`, `advanced_manufacturing`, `oil_gas`, `renewable`, `nuclear`, `emerging_tech`
- `trade_structure`: `long`, `short`, `pair`, `hedge`
- `direction`: `long`, `short`, `mixed`
- `health_status`: `green`, `yellow`, `red`
- `conviction`: 1-10 integer

#### `journal/decisions.md`

文件级 frontmatter：

```yaml
---
schema_version: 1
document_type: decision_log
append_only: true
entry_schema: decision_v1
---
```

每条 decision 追加一个独立 YAML block：

```yaml
decision_id: 2026-05-07-XOM-open
date: 2026-05-07
ticker: XOM
trade_structure: long
action: open
direction: long
position_gross_pct: 2.0
position_net_pct: 2.0
price_at_decision: null
valuation_at_decision: EV/EBITDA 6.5x
conviction: 7
expected_upside_pct: 20
expected_downside_pct: -12
time_horizon: 12m
entry_trigger: Thesis reached sufficient conviction after peer work
source_of_edge: analysis
linked_thesis: coverage/XOM/thesis.md
sources:
  - claim: Price, valuation, and consensus snapshot at decision time
    source_name: "[Bloomberg / CapIQ / filing]"
    url: ""
    as_of: 2026-05-07
```

字段约束：
- `action`: `open`, `add`, `trim`, `close`, `review`
- `source_of_edge`: `information`, `analysis`, `behavioral`, `other`
- entry append-only；建仓时写下的前半部分不得事后改写

#### `pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md`

文件级 frontmatter：

```yaml
---
schema_version: 1
document_type: spread_log
pair_id: XOM-CVX
long_ticker: XOM
short_ticker: CVX
spread_definition: valuation_spread
base_currency: USD
created_at: 2026-05-07
entry_schema: spread_observation_v1
---
```

每条 observation 追加一个独立 YAML block：

```yaml
date: 2026-05-07
as_of: 2026-05-07 15:30
long_price: null
short_price: null
long_weight: 1.0
short_weight: 1.0
spread_value: null
spread_zscore: null
beta_180d: null
correlation_180d: null
pnl_since_entry_pct: null
thesis_health: green
action: hold
sources:
  - claim: Price, spread, beta, and correlation snapshot
    source_name: "[Bloomberg / FactSet / broker]"
    url: ""
    as_of: 2026-05-07
```

字段约束：
- `spread_definition`: `valuation_spread`, `price_ratio`, `total_return_spread`, `custom`
- `thesis_health`: `green`, `yellow`, `red`
- `action`: `hold`, `add`, `trim`, `close`, `review`

### 6.4 文件顶部摘要约定（防淹没）

每个 `coverage/[t]/thesis.md` 的文件顺序必须是：YAML frontmatter（第一段）→ human-readable 摘要 → 详细 thesis。摘要紧跟 frontmatter：

```
# [Ticker] Thesis

> **Direction**: Long / Short / Pair / Hedge
> **One-line thesis**: [一句话]
> **Conviction**: High / Medium / Low
> **Time horizon**: 6m / 12m / 24m
> **Last updated**: [date]
> **Health status**: 🟢 / 🟡 / 🔴
> **Next catalyst**: [date - event]

---

[详细 thesis 内容]
```

每个 `pairs/[LONG_TICKER]-[SHORT_TICKER]/thesis.md` 顶部：

```
# [X] long / [Y] short

> **Pair logic** (一句话): X 应该 outperform Y 因为 [核心差异]
> **Entry spread**: [入场时的 spread]
> **Current spread**: [当前]
> **Conviction**: High / Medium / Low
> **Last updated**: [date]
```

---

## 7. Workflow 链路

### 7.1 标的 lifecycle（从发现到平仓）

```
发现阶段
├─ candidate-screener → screens/[hypothesis-slug]-[YYYY-MM-DD].md
│   └─ 推荐 1-2 家深入 → stock-quickread / peer-deep-dive / pair-trade
└─ stock-quickread → quickreads/[ticker].md
    │
    ├─ 不感兴趣 → 归档
    │
    └─ 想深入 → 是否多家同业？
        │
        ├─ Yes → peer-deep-dive → peers/[industry].md
        │         │
        │         └─ 选出 1-2 家深入 → 跨市场？
        │             │
        │             ├─ Yes → cross-market-compare
        │             │
        │             └─ No  → financial-model（如需要拆收入 / 更新模型）→ alpha-thesis
        │
        └─ No  → financial-model（可选）→ alpha-thesis → coverage/[ticker]/thesis.md
                  ↕ (双向迭代)
                  bear-pre-mortem → coverage/[ticker]/bear-case.md
                  │
                  └─ Conviction 充分 → 建仓决策
                                      │
                                      └─ decision-journal → journal/decisions.md

持仓阶段（持续）
─ thesis-tracker 周度运行 → coverage/[t]/health-log.md
─ pair-trade (monitor) 周度运行 → pairs/[LONG_TICKER]-[SHORT_TICKER]/spread-log.md
─ information-impact (随时触发) → Claim Check / Portfolio Impact
                                  │
                                  └─ 仅 Medium/High 且命中 portfolio/watchlist → inbox + thesis-tracker / 调仓

事件阶段
─ earnings-setup (财报前) → coverage/[t]/earnings-setup-[date].md
─ earnings-setup (财报后) → 触发 financial-model 更新（如涉及模型）+ decision-journal（如调仓）+ thesis-tracker 更新

退出阶段
─ Thesis played out / 失效 → decision-journal (平仓 entry)
                              │
                              └─ [未来] trade-postmortem
```

### 7.2 信息流入工作流（防淹没核心）

```
[每天信息流]
  新闻 / 研报 / 数据 / Twitter / 专家访谈 / 供应链传闻
       ↓
  information-impact: Claim Check
       ↓
  ┌──────────────────────────────┬───────────────────────┐
  Confirmed / Likely / Plausible  Unsupported / Contradicted
        ↓                                  ↓
  是否命中 portfolio / watchlist?        默认不落盘
        ↓
  ┌───────────────┬────────────────┐
  No              Yes
  ↓               ↓
 不落盘 / monitor  Portfolio Impact
                  ↓
        ┌────────┬───────────┬──────────────┐
        Low    Medium       High
        ↓       ↓            ↓
       Drop   加入 monitor  立即行动
              queue        ↓
                           ├─ thesis 重审
                           ├─ pair 调整
                           └─ 调仓决策
                              ↓
                              decision-journal
```

**关键设计**：传闻型信息先过 Claim Check；`Unsupported` / `Contradicted` 默认不写入 `inbox/information-log.md`，除非用户要求留痕。只有可验证性达到 `Plausible but unconfirmed` 以上且命中 portfolio / watchlist，才进入 Portfolio Impact。这是防信息淹没和防概念外推的核心机制。

---

## 8. Phase 推进路径

### Phase 1：核心研究 skills（v1.2 已完成）

- [x] stock-quickread
- [x] peer-deep-dive（含 9 个行业模板 + 元方法论）
- [x] alpha-thesis（已对齐 thesis schema contract）
- [x] bear-pre-mortem
- [x] earnings-setup（已补 post-print state handoff）
- [x] CLAUDE.md（项目宪法）

**v1.2 已完成**：
- 现有 5 个 skills 与 `CLAUDE.md` / 本框架的 LS 视角、状态 schema、source policy 引用方式对齐
- README / plugin metadata 同步到真实能力，不再把 `peer-scan` 描述为已发布 skill

### Phase 2：填补 LS 特色 + 持仓维护（v2.0 已 scaffold）

按重要性排序：

1. **decision-journal** — 已新增
2. **thesis-tracker** — 已新增
3. **pair-trade** — 已新增

**当前状态**：Phase 2 scaffold 已具备稳定接口；后续如果要提高质量，应做 sample run / fixture validation，而不是再改框架方向。

### Phase 3：信息处理 + 跨市场（v2.0 已 scaffold）

4. **information-impact** — 已新增，包含 claim-check + portfolio-impact
5. **cross-market-compare** — 已新增

### Phase 4：建模（v2.1 skeleton）

6. **financial-model** — 已新增 skeleton，覆盖 Build New Model + Update Existing Model；第一版不写脚本、不强制标准模板

### Phase 4.5：候选筛选（v2.2）

7. **candidate-screener** — 已新增，覆盖 thematic / event-driven / quant / mixed screening；输出 `screens/[hypothesis-slug]-[YYYY-MM-DD].md`

### Phase 5：未来扩展（P2，看实际需求再决定）

可能加的：
- `trade-postmortem`（平仓后 / 月度复盘）
- `theme-tracker`（AI 应用、人形机器人等主题 watchlist 维护）
- `morning-brief`（每天早上 thesis-tracker + catalyst + inbox 汇总）
- `ic-memo-writer`（投资委员会 memo）

但 Phase 5 不强求——**先用 v2.2 真实跑几轮，再决定是否扩展**。

---

## 9. CLAUDE.md 同步状态

当前 CLAUDE.md 已根据本框架完成以下同步；后续如修改覆盖范围、source policy 或 trigger 表，应先改 `CLAUDE.md`，再同步 README / skill metadata。

### 9.1 §1 研究员上下文（已同步）

```
- 身份：LS（Long-Short）对冲基金研究员
- 坐标：亚洲（时区影响美股 post-print 工作流）
- 覆盖市场：大中华 + 全球（美日韩欧为主）
- 覆盖行业：industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes
```

### 9.2 §2 全局工作风格（待进一步精炼）

新增条款：
- 任何 thesis-related 任务默认双向考虑（不假设是 long-only）
- 主动问 trade structure（long / short / pair / hedge）
- 给出 thesis 时同时考虑"对手盘相信什么"

### 9.3 §2.6（新增）信息淹没应对原则

- 默认输出极短（除非是 deep research skill）
- 第一行必须是"决策 / 判断"，不是 context 铺垫
- 不允许"对行业有影响"这类无 actionable 表述
- 信息和 portfolio 无关时直接说"归档无需行动"，不要硬讲

### 9.4 §5 Skill 触发指引（已同步）

表格已扩展到 12 个 skills。

### 9.5 §7 文件组织约定（已同步）

已按本文件 §6.1 的目录结构更新。

---

## 10. 反模式（系统设计层面的）

避免以下设计错误：

- ❌ **再造孤岛 skill**：不读 / 不写状态文件的新 skill 是孤岛，等于 0 价值
- ❌ **输出膨胀**：新 skill 默认 < 500 字，超过必须有理由
- ❌ **重复 LS 改造**：不是每个 skill 都需要 LS 改造，bear-pre-mortem 本身已经是 LS 思维
- ❌ **过度行业化**：不再为新行业写硬编码模板，用元方法论
- ❌ **trigger 冲突**：新 skill 的 trigger keywords 必须和现有 12 个不冲突，否则会误触发
- ❌ **状态文件无 schema**：每个状态文件必须明确"谁写、谁读、累积 vs 替换"
- ❌ **CLAUDE.md 升级了但 SKILL.md 没同步**：source policy 既然升格到 CLAUDE.md，所有 SKILL.md 应同步删除嵌入的 source policy 全文，只引用 `CLAUDE.md §3`

---

## 11. 决策日志（本框架的设计决策记录）

| 决策 | 选项 | 选择 | 理由 |
|---|---|---|---|
| Skill 数量 | 精简（8-12） vs 完整（15+） | 精简 12 | Candidate screening 是高频 outbound funnel，和 inbound information-impact 边界清晰，值得作为第 12 个 core skill |
| 状态持久化 | 本地 md / Project / Notion | 本地 md | 简单可控，先跑通 |
| 跨市场处理 | 融入 / 单独 skill | 单独 skill `cross-market-compare` | 跨市场有独特 KPI 和考量 |
| 建模处理 | 自由对话 / 单独 skill / 替换其他 skill | 单独 skill `financial-model` | revenue split 和财报后更新是高频工作，不应塞进 earnings-setup |
| 持仓维护 | 多个细分 / 合并 | 合并 thesis-tracker + 合并 pair-trade | 高频使用减少 trigger 决策成本 |
| 信息处理 | 不做 / 单独 skill | 单独 skill `information-impact` | 直接对应"信息淹没"痛点 |
| 候选筛选 | 自由对话 / 单独 skill / 并入 peer-deep-dive | 单独 skill `candidate-screener` | hypothesis → candidates 是高频入口，不应塞进 peer-deep-dive |
| LS 改造 | 全改 / 部分改 / 不改 | 部分改（4/5 skill） | bear-pre-mortem 不需要改 |
| Postmortem skill | Phase 1 / Phase 4 | Phase 4 | 频率低，先用自由对话 |
| 行业模板 | 穷举 / 元方法论 | 元方法论 + 9 个 anchor 模板 | 已实现，verified |

---

## 12. 已确认事项与待确认事项

### 12.1 已确认

1. **`coverage/[ticker]` 的 ticker 格式**：使用 Bloomberg-style canonical ticker，例如 `XOM`、`700.HK`、`ASML.NA`。
2. **Pair 目录命名**：使用 `pairs/[LONG_TICKER]-[SHORT_TICKER]/`，例如 `pairs/XOM-CVX/`。
3. **Decision-journal conviction**：entry 必须包含 `conviction` 数字（1-10 scale），方便复盘时做 conviction calibration。
4. **Financial model 路径**：默认使用 `coverage/[ticker]/model.xlsx`；更新已有模型时保留原 workbook 结构，不迁移到标准模板。
5. **Candidate screener 路径**：默认使用 `screens/[hypothesis-slug]-[YYYY-MM-DD].md`；它是候选漏斗留痕，不是最终 thesis。

### 12.2 待确认

1. **Health-log 频率**：周度自动 + 事件触发，还是只事件触发？
2. **Information-impact 输出 archive 项是否值得保留**：已确认默认不落盘；只有用户要求留痕，或 claim 至少 Plausible 且命中 portfolio/watchlist，才写 `inbox/information-log.md`。

---

**版本**：v2.2  
**状态**：v1.2 existing-skill alignment + v2.0 state workflow scaffolds + v2.1 financial-model skeleton + v2.2 candidate-screener 已完成；下一步应做 sample run / fixture validation，验证 12 个 skills 的输出能稳定读写公开状态接口。  
**最后更新**：2026-05-08
