---
name: candidate-screener
description: Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.
---

# Candidate Screener

Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for hypothesis engineering, candidate mining, priced-in triage, and idea funneling; unresolved facts stay as gap, hypothesis, or follow-up.
- Market-snapshot fields default to `topic-local evidence cache / financial-data` then trusted third-party then web fallback. A-share / HK / US screening that needs market_quote, valuation_snapshot, or market_screen may call `trusted-market-bridge` first; bridge misses fall back to web. Borrow, bid-ask, accounting basis, and share-class truth stay at `[需查证]` without high-quality source.
- Sub-agent outputs must be evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

**三表数据前置（按需调用）：** priced-in 评估和估值锚需要 market_data——主 agent 先从 actuals-resolved.json 取市场数据；如需为未覆盖 ticker 拉数据，委托 subagent 执行 /financial-data --lite <ticker>。
**市场数据统一入口：** 市场数据（股价、市值、PE TTM/NTM、PB、PS、EV/EBITDA、EV/Sales、PEG、Dividend Yield、Target Price）统一由 `financial-data --lite` 的 trust-based fill 链获取（Bridge → yfinance → WebSearch → Google Finance），不再各自调 `trusted-market-bridge`。每个字段标 `[source_layer | as-of]`。

把主题、事件、value-chain pocket 或财务 / 估值条件转化成可研究股票漏斗。默认偏 long-biased idea mining，但保留 LS 纪律：obvious / fully priced / 低纯度高 beta 的 names 要进 watchlist、reject 或 possible short，不要硬塞进 Top Ideas。

如果输出只是受益股列表、概念股堆砌、卖方报告 tickers 汇总，或者没有解释为什么市场可能还没 price，本 skill 就失败了。

## 心法

研究员说“挖票”时，真正要的不是更多名字，而是一个可检验的买方漏斗：主题在哪里有真实经济暴露，哪一段价值链最可能被错价，哪些公司同时满足 **纯度高、增长快、估值不贵、市场还没完全发现**。

AI 的优势不是做完整 universe screen。Bloomberg / FactSet / Longbridge 等工具在全市场覆盖上更可靠。AI 的差异化价值是把 vague theme 翻译成可验证业务特征，再把候选分成 Top Ideas、Watchlist、Already Priced 和 Rejects，帮助研究员少追热门概念股。

**最重要的纪律**：`还没被市场发现` 不是事实，只能用 proxy 判断。低 sell-side coverage、估值未重估、股价未反映、主题归类缺失、叙事尚未扩散都必须有 source 或标 `[需查证]`。

## 触发场景

使用本 skill 当用户问：

- "用 candidate-screener 挖 [主题 / 产业链 / value-chain pocket]"
- "挖票 / 找票 / 找还没被市场发现的股票"
- "找纯度高、增长快、估值便宜的 [主题] 标的"
- "[主题] 里有没有 hidden winners / mispriced pure-play"
- "从 [事件 / 政策 / capex 周期] 找 long / short candidates"
- "找 EV/EBITDA < 8x、FCF yield > 8%、增长没塌的公司"
- "类似 [X 公司] 但估值更便宜 / 市场还没发现的标的"

不要用于：

- 单条新闻、客户关系、供应链 claim 真假验证：用 `information-impact`。
- 陌生公司 first-pass：用 `stock-quickread`。
- 行业 first-pass、profit pool 和 KPI/source map：用 `industry-quickread`。
- 工程机制、设备链条、工艺流程不清：先用 `mechanism-map`。
- 公司 revenue / margin / backlog / price-volume-mix driver 不清：用 `driver-map`。

## 输入澄清要求

如果用户输入足够明确，直接声明默认假设并开始，不要用长问卷拖慢挖票。只有缺失项会改变候选方向时才追问。

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **主题 / 信号** | 光模块设备、AI 电力、核燃料、某政策事件、某财务条件 | 按用户原词最窄可投边界定义 |
| **时间窗口** | 3M / 12M / 24M+ | 12M，兼顾 3M catalyst |
| **方向** | Long / Short / Both | Long-biased，但保留 possible short / reject |
| **市场偏好** | US / 大中华 A-H-ADR / 日韩 / 全球 / 不限 | 用户覆盖市场：大中华 + 全球工业 / 科技主题 |
| **纯度要求** | 主营 >50%、segment >30%、indirect / supply-chain | 优先 direct / pure-play，indirect 降权 |
| **增长要求** | revenue / backlog / order / capacity / margin inflection | 没有 source 时标 `[需查证]` |
| **估值要求** | PE、EV/EBITDA、FCF yield、SOTP、相对同业 | 用可得市场快照；缺失则标 `[需查证]` |
| **Discovery edge** | 为什么可能没被 market price | 用 proxy，不写成事实 |
| **流动性 / size** | 最小 ADV / market cap | 大中华 >= 100M USD ADV；美股 >= 50M USD ADV；小票另列风险 |

## Candidate Mining / 挖票

统一处理主题、事件、screen 和混合条件。内部把输入拆成三种信号，而不是让用户选择 mode：

| Signal | 说明 | 例子 |
|---|---|---|
| **Theme signal** | 主题、事件、政策、capex 周期、value-chain pocket | 光模块设备、AI data-center power、出口管制 |
| **Fundamental / valuation filter** | 增长、利润率、现金流、估值、ROIC、capex 强度 | EV/EBITDA < 8x、FCF yield > 8%、backlog 加速 |
| **Discovery edge** | 为什么市场可能没完全 price | 低覆盖、分类错误、非主流上市地、估值未重估、叙事未扩散 |

### 推理路径（必须显式）

**Step 1: 定义主题边界和 value-chain pockets**

把用户输入拆成 3-6 个可投 pocket。例：`光模块设备` 不能直接等于“光模块概念股”，应拆成 optical transceiver、laser / EML、DSP / switch ASIC、testing equipment、packaging / connector、capex equipment / automation 等 pocket，并标出哪一段最可能 capture profit。

**Step 2: 主题 -> 可验证业务特征**

每个 pocket 翻译成 observable business traits：

- revenue purity：相关收入占比或 segment exposure。
- growth proof：订单、backlog、shipment、capacity、客户 capex、价格 / mix、margin inflection。
- value capture：稀缺工艺、客户认证、供应瓶颈、installed base、aftermarket、议价力。
- disclosure handle：公司用什么 segment / KPI 披露，哪里容易错读。

**Step 3: 叠加挖票条件**

默认用五维评分，不允许只按主题热度排序：

| 维度 | 权重 | 高分标准 |
|---|---:|---|
| Business purity | 25% | 主题相关业务对 revenue / profit / backlog 有可验证占比，最好 >50% |
| Growth evidence | 20% | 有 revenue / order / backlog / capacity / margin acceleration 的 source |
| Valuation appeal | 20% | 相对历史、同业或增长质量不贵；便宜但恶化要降为 value trap |
| Discovery edge | 20% | 低覆盖、分类错误、非主流上市地、估值未重估、股价未反映等 proxy |
| Catalyst / liquidity / tradability | 15% | 3-12M 有验证节点，流动性可交易，borrow / squeeze 风险可控 |

**Step 4: 候选分层**

| Bucket | 定义 | 处理 |
|---|---|---|
| **Top Ideas** | 同时满足纯度、增长、估值、discovery edge 的 1-3 个 names | 推荐进入 deep research |
| **Watchlist** | 机制对，但估值、source、流动性或催化还不够 | 等待验证，不强推 |
| **Obvious / Already Priced** | 主题相关但 market 已经明显 price 或 crowding 高 | 用作 peer / hedge / avoid chasing |
| **Rejects / Value Traps** | 便宜但增长塌、纯度低、关联未证实、主题 beta 高但基本面弱 | 明确拒绝原因 |

**Step 5: Next verification**

Top Ideas 必须给下一步验证路线：

- 公司 first-pass：`stock-quickread`
- 业务 / segment / KPI 到 model driver：`driver-map`
- 复杂工程机制：`mechanism-map`
- 单条客户 / 订单 / 供应链 claim：`information-impact`
- 3-8 个核心公司横向比较：`peer-deep-dive`

## 输出结构

```markdown
## Candidate Mining Verdict

[2-4 句结论先行：这个主题最可能错价的 pocket、Top Ideas 数量、最重要 caveat]

## 1. Signal Translation

| Input signal | Translation | Default / caveat |
|---|---|---|
| Theme signal | [主题边界 + value-chain pocket] | [...] |
| Fundamental / valuation filter | [增长 / 估值 / 现金流条件] | [...] |
| Discovery edge | [未发现 proxy] | [需查证 / source-backed] |

## 2. Value-Chain Pockets

| Pocket | Why it can capture value | What to verify | Likely public names | Source status |
|---|---|---|---|---|
| [pocket] | [利润池 / 瓶颈 / 认证 / capex] | [KPI / source] | [names or GAP] | sourced / [需查证] |

**Pocket takeaway**: [最可能产生 mispriced name 的 1-2 个 pocket]

## 3. Candidate Funnel

| Name | Market | Pocket / exposure | Purity | Growth proof | Valuation | Discovery edge | Score | Bucket | Ev |
|---|---|---|---|---|---|---|---:|---|---|
| AAA | US | [业务暴露] | High | [具体证据] | [倍数 / 相对] | [proxy] | 8.1 | Top Idea | [S1](...) |

## 4. Top Ideas (1-3)

### 1. [Ticker / Company] - [一句话 idea]

- **Why it fits**: [纯度 + 增长 + 估值 + discovery edge]
- **What market may be missing**: [只能写 proxy，不写成确定事实]
- **Key source / gap**: [source 或 `[需查证]`]
- **Why not obvious**: [不是热门概念股 / 非主流分类 / 估值未重估 / 覆盖低]
- **Next verification**: `stock-quickread` / `driver-map` / `information-impact`

## 5. Watchlist

| Name | Why close | Missing proof | Next trigger |
|---|---|---|---|

## 6. Obvious / Already Priced

| Name | Why relevant | Why not Top Idea |
|---|---|---|

## 7. Rejects / Value Traps

| Name | Looks attractive because | Reject reason |
|---|---|---|

## 8. Hypothesis Fragility

- [主题本身最可能错在哪里]
- [哪些 Top Ideas 的 source / driver 最脆弱]
- [什么情况会让该主题变成 crowded / fully priced]

## 9. AI Universe Caveat

AI 不是 universe screener。本列表可能漏掉 small cap、最近 IPO / spin-off、非英语市场、低覆盖本地上市公司。你应该 cross-check Bloomberg / FactSet / Longbridge / 本地交易所 screen，并主动问“我可能漏了哪些 names”。
```

## 共同硬标准

### 1. 每个业务关联必须有 source 或 gap 标记

每个 candidate 的 exposure / purity / customer / product / value-chain role 必须有 source link 或明确 `[需查证]`。卖方主题分类、社媒列表、概念股文章只能当线索，不能当业务关联证据。

### 2. 增长必须有可验证证据

增长证据优先级：

| 证据类型 | 可支持什么 |
|---|---|
| 公司披露 revenue / segment / backlog / order / shipment / capacity / margin | 可进入 Top Ideas |
| 客户 capex、行业 shipment、价格 / utilization proxy | 可支持 pocket 或 watchlist |
| 卖方预测、第三方行业报告 | 可作线索，需标 source quality |
| 市场传闻 / 社媒 / 截图 | 只能作 follow-up，不进 Top Ideas |

### 3. 估值便宜必须和增长质量一起判断

- **Cheap + growth intact**：可进 Top Ideas。
- **Cheap + growth uncertain**：Watchlist。
- **Cheap + growth deteriorating**：Reject / Value Trap。
- **High growth + fully priced**：Obvious / Already Priced，除非有明确 variant view。

### 4. Discovery edge 只能写 proxy

允许的 proxy：

- sell-side coverage 少或主流模型未覆盖该 segment。
- 估值倍数未相对主题 peers 重估。
- 股价没有跟随主题 basket 反应。
- 公司被错误归类在传统行业，主题 exposure 藏在 segment / subsidiary。
- 非主流上市地、本地语言披露、ADR/A/H 结构导致 coverage gap。

禁止写成：

- "市场还没发现"但没有任何 proxy。
- "低估"但没有估值或价格反应 anchor。
- "纯度高"但没有收入 / 利润 / backlog / segment 证据。

### 5. Top Ideas 数量必须收口

- Top Ideas：1-3 个。
- Watchlist：3-7 个。
- Obvious / Already Priced：最多 5 个。
- Rejects / Value Traps：至少 2 个，除非 universe 极窄。

如果候选太多，先按 purity 和 discovery edge 收紧；不要输出 20 个 ticker 让用户自己筛。

## Artifact / 保存策略

写入行业 topic：

```text
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md
```

路径不明 -> `new-session` 解析行业。保存时 default artifact 仍为 `candidate-screener.md`，可用 qualifier 表示主题，例如 `candidate-screener-optical-module-equipment.md`。

## Workflow 联动

| 发现 | 下一步 |
|---|---|
| Top Idea 是陌生公司 | `stock-quickread` |
| Top Idea 的 revenue / margin / backlog driver 不清 | `driver-map` |
| value-chain pocket 依赖工程机制、设备链、工艺 | `mechanism-map` |
| 单条客户、订单、供应链、供应商关系 claim 未验证 | `information-impact` |
| 需要横向比较 3-8 个核心 candidates | `peer-deep-dive` |
| 主题的 priced-in、buy-side bar 或 consensus debate 不清 | `consensus-map` |
| Top Ideas 需要形成 long / short thesis | `alpha-thesis` / `bear-pre-mortem` |

## 反模式自查

写完必须自检，命中就重写：

### 编造 / 概念股堆砌

- ❌ 只列热门 ticker，没有解释 value-chain pocket 和 purity。
- ❌ Candidate 的业务暴露无 source link，也没标 `[需查证]`。
- ❌ 把卖方主题归类、社媒列表、概念股文章当作业务关联依据。
- ❌ Tier-N 供应链只写"相关"，没有说明 supplier link、product、timeframe。
- ❌ 把 sub-agent evidence card 直接当最终 Top Idea；主 agent 必须抽查、去重、分层和排序。

### 挖票质量

- ❌ 没有说明为什么 market 可能没 price。
- ❌ 只因估值便宜就推荐，没检查增长是否恶化。
- ❌ 只因增长快就推荐，没检查估值是否 fully priced。
- ❌ Top Ideas 超过 3 个，说明没有收口。
- ❌ 没有列 Obvious / Already Priced，导致用户追热门概念股。
- ❌ 没有列 Rejects / Value Traps，导致 cheap screen 变成 value trap list。

### Workflow 边界

- ❌ 用户问单条 claim 靠不靠谱，却直接挖票；应先 `information-impact`。
- ❌ 工程机制不清仍强行列 names；应先 `mechanism-map`。
- ❌ 公司 driver 不清仍写 growth thesis；应先 `driver-map`。
- ❌ 对 `[需查证]` 的客户 / 订单 / 供应链关系做强结论外推。

## 篇幅基准

- 标准 Candidate Mining：1200-2500 字 + 3-5 张表。
- 快速挖票：800-1200 字，Top Ideas 最多 2 个。
- 深度 universe pass：2500-4000 字，但必须按 pocket 分组，不能变成 ticker dump。

低于 800 字通常没有完成 source / purity / valuation / discovery 四件事；超过 4000 字通常说明没有收口，应缩减候选或 handoff `peer-deep-dive`。

## 与 information-impact 的边界

两个 skill 都涉及 source 验证、claim 拆解，但信息流方向相反：

| | candidate-screener | information-impact |
|---|---|---|
| 输入 | 主题、事件、screen、挖票口味 | 已知 claim、新闻、传闻、截图 |
| 任务 | 从 hypothesis 出发找可研究 names | 验证真假 + research relevance |
| 方向 | Outbound：从主题往外找 | Inbound：信息已经到了 |
| 输出 | Top Ideas / Watchlist / Rejects / Next verification | Verdict / What not to infer / Action |

不要混淆：

- "光模块设备链有没有纯度高、增长快、估值便宜、没被发现的票" -> `candidate-screener`
- "听说 X 是 NVIDIA 光模块供应商，靠谱吗" -> `information-impact`
- "这个新闻是真的，而且想按新闻逻辑找受益股" -> 先 `information-impact`，再 `candidate-screener`
