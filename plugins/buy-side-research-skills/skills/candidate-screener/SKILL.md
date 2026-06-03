---
name: candidate-screener
description: Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.
---

# Candidate Screener

Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 获取三表 + 市场快照。信任其结果，直接从 `actuals-resolved.json` 取数。
- **数据验证**：Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证])。见  §3.2。
- **Actuals-only**: screening ratios (PE, PEG, EV/EBITDA, FCF Yield, ROIC, etc.) use actuals-resolved.json. Consensus data may appear as a separate column but never feeds into ratio computation.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.


- Use this skill for hypothesis engineering, candidate mining, priced-in triage, and idea funneling; unresolved facts stay as gap, hypothesis, or follow-up.

Step 1: Fork N subagents — 一 ticker 一 card（并行）

每个 subagent 独立完成两项任务：

  a. 拉取财务数据
     /financial-data --lite <TICKER>
     → 写入 _cache/financial-data/internal/actuals-resolved.json

  b. 生成证据卡
     读取 actuals + WebSearch 关键信息 → 按 `references/policy/evidence-card-schema.json` 输出 JSON
     证据卡含：financial_highlights, business_profile, competitive_position,
              growth_outlook, valuation_context, long_short_sentiment, scoring,
              key_claims_needing_verification, evidence_triplets

subagent N:
  /financial-data --lite <TICKER_N>
  + evidence card JSON per evidence-card-schema.json

全部 subagent 完成后主 agent 继续。单 ticker 失败不影响其他——主 agent 在最终 artifact 中标注
`subagent unavailable for <TICKER> — <reason>`，该 ticker 从合并对比中移除。

## 心法

研究员说”挖票”时，真正要的不是更多名字，而是一个可检验的买方漏斗：主题在哪里有真实经济暴露，哪一段价值链最可能被错价，哪些公司同时满足 **纯度高、增长快、估值不贵、市场还没完全发现**。

**没有 regime 不变的排序。** 同一家公司在 Pluggable 时代是 Top Idea，CPO 时代可能是 Reject。排序必须绑定场景，且必须同时给出 L/S 两个方向——不能只推多仓不管空仓。静态漏斗 = 单场景假设 = 漏掉最大的风险。

AI 的优势不是做完整 universe screen。Bloomberg / FactSet / Longbridge 等工具在全市场覆盖上更可靠。AI 的差异化价值是把 vague theme 翻译成可验证业务特征，再把候选按场景分成立体漏斗：**稳健多仓、场景赌注、方向翻转型、事件驱动、估值收敛对**。帮助研究员少追热门概念股，并在 regime 切换时有预案。

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
- "分场景排序 / L/S 排序 / 按场景推票"
- "[CPO/电动化/关税/...] 场景下应该多什么空什么"
- "动态 LS 视角 / regime-aware 挖票"

不要用于：

- 单条新闻、客户关系、供应链 claim 真假验证：用 `information-impact`。
- 陌生公司 first-pass：用 `stock-quickread`。
- 行业 first-pass、profit pool 和 KPI/source map：用 `industry-landscape`。
- 工程机制、设备链条、工艺流程不清：先用 `mechanism-insight`。
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

**Step 1: 定义场景 + 主题边界**

**1a. 场景定义**（新增）

把主题拆成 2-3 个宏观 regime，每个 regime 标概率 + 关键 catalyst trigger 阈值。regime 是排序的前提——同一家公司在不同 regime 下的 L/S 方向可能相反。

| Regime | 定义 | 概率 | Catalyst Trigger |
|---|---|---|---|
| R1: 当前主导 | 现有技术路线主导 | 60% | — |
| R2: 过渡期 | 新范式开始渗透 | 30% | [具体事件] 规模出货 |
| R3: 新范式主流 | 新范式 > 15% 渗透 | 10% | [具体事件] 量产 |

regime ≥ 3 时考虑为不同阶段推不同的票。不定义场景就直接排序 = 隐含”当前 regime 不变”的假设，必须显式化。

**1b. 主题边界和 value-chain pockets**

把用户输入拆成 3-6 个可投 pocket。例：`光模块设备` 不能直接等于”光模块概念股”，应拆成 coupling equipment、die bonding、burn-in / test、automation 等 pocket，并标出哪一段最可能 capture profit。

**Step 2: 主题 -> 可验证业务特征**

每个 pocket 翻译成 observable business traits：

- revenue purity：相关收入占比或 segment exposure。
- growth proof：订单、backlog、shipment、capacity、客户 capex、价格 / mix、margin inflection。
- value capture：稀缺工艺、客户认证、供应瓶颈、installed base、aftermarket、议价力。
- disclosure handle：公司用什么 segment / KPI 披露，哪里容易错读。

**Step 3: 叠加挖票条件**

默认用六维评分，不允许只按主题热度排序：

| 维度 | 权重 | 高分标准 |
|---|---:|---|
| Business purity | 22% | 主题相关业务对 revenue / profit / backlog 有可验证占比，最好 >50% |
| Growth evidence | 18% | 有 revenue / order / backlog / capacity / margin acceleration 的 source |
| Valuation appeal | 18% | 相对历史、同业或增长质量不贵；便宜但恶化要降为 value trap |
| Discovery edge | 18% | 低覆盖、分类错误、非主流上市地、估值未重估、股价未反映等 proxy |
| **Scenario sensitivity** | **12%** | 多场景 work 或 regime flip 时方向清晰；估值 flip 幅度可量化；不是每个 regime 都"中性偏正面" |
| Catalyst / liquidity / tradability | 12% | 3-12M 有验证节点，流动性可交易，borrow / squeeze 风险可控 |

**Step 4: 候选分层（五层）**

| Bucket | 定义 | 处理 |
|---|---|---|
| **Top Ideas** | 同时满足纯度、增长、估值、discovery edge 的 1-3 个 names（当前 regime 下） | 推荐进入 deep research |
| **Scenario Bets** | 只在某一个场景下成立，当前 regime 不 work。确认后再买已经翻倍 | 小仓位 2-5%，按归零承受力定仓位，不按估值便宜加仓 |
| **Watchlist** | 机制对，但估值、source、流动性或催化还不够 | 等待验证，不强推 |
| **Obvious / Already Priced** | 主题相关但 market 已经明显 price 或 crowding 高 | 用作 peer / hedge / avoid chasing |
| **Rejects / Value Traps** | 便宜但增长塌、纯度低、关联未证实、主题 beta 高但基本面弱 | 明确拒绝原因 |

**Step 5: Next verification**

Top Ideas 必须给下一步验证路线：

- 公司 first-pass：`stock-quickread`
- 业务 / segment / KPI 到 model driver：`driver-map`
- 复杂工程机制：`mechanism-insight`
- 单条客户 / 订单 / 供应链 claim：`information-impact`
- 3-8 个核心公司横向比较：`peer-deep-dive`

## 输出结构

> **Source contract**：以下所有表格中涉及估值倍数、概率百分比、Flip 幅度、spread 差、评分数字的列，**每行必须带 source anchor**（[S#](url) 或 [I#](url)）。估值来自 market_data 标 `[I#]`，业务数据来自 actuals 标 actuals，外部行业报告标 `[I#]`。

```markdown
## §1 结论先行

[当前 regime 判断 + 跨场景最稳健的 L/S 组合 + 最核心的场景估值洞察]

## §2 场景定义

| Regime | 定义 | 概率 | Catalyst Trigger | 估值环境 | Ev |
|---|---|---|---|---|---|
| R1: [当前主导] | ... | 60% | — | PE 15-30x | [S#](url) |
| R2: [过渡期] | ... | 30% | [事件+阈值] | 稀缺溢价 |
| R3: [新范式] | ... | 10% | [事件+阈值] | 杀旧业务估值 |

## §3 场景推票矩阵（主表）

行 = 公司，列 = 3 regime。格子格式：**方向 权重 | 当前估值 | 场景重估方向 | 一句话 | Key KPI（从 `references/kpi-drivers/` 取该行业最重要的 1 个数字）**

| 公司 | 代码 | R1: [当前] | R2: [过渡] | R3: [新范式] | 估值 Flip 幅度  Ev |
|---|---|---|---|---|---|---|
| AAA | TICKER | Long 高 | PE 18x | ↑ | 逻辑 | Long 高 | → ↑ | 逻辑 | Long 高 | → ↑↑ | 逻辑 | +60% |

估值 Flip = R1→R3 的重估幅度，必须量化。负值 = regime 切换时空仓收益。

## §4 跨场景合成

### §4.1 稳健多仓（全场景 work）

| 票 | 当前估值 | 全场景逻辑 | 上行 | 下行  Ev |
|---|---|---|---|---|---|

### §4.2 场景推票表（反向索引：场景→动作→票）

| 场景触发 | 动作 | 票 | 仓位 | 策略原型 | 当前估值 | 目标估值 | 逻辑  Ev |
|---|---|---|---|---|---|---|---|---|
| 当前 base | Long | AAA | 核心 | 代际升级 | PE 18x | PE 25x | ... |
| CPO>15% | Long | BBB | 小赌注 | 小赌注 | PS 8x | PS 20x | 0→1 |

**策略原型**（7 种）：全场景多仓 / 小赌注 / Flip 对冲 / 事件驱动 / 估值收敛 / 代际升级 / 叙事套利

### §4.3 方向翻转型（估值 flip 最大）

| 票 | R1→R3 估值路径 | Flip 幅度 | 核心逻辑  Ev |
|---|---|---|---|---|

### §4.4 估值收敛对（spread trade，可选）

| Long | Short | 当前 spread | 合理 spread | 收敛催化剂  Ev |
|---|---|---|---|---|---|

## §5 Base Case 漏斗（当前 regime 下）

### Top Ideas (1-3)

| # | 票 | 一句话 | Purity | Growth | 估值 | Discovery | Scenario | 总分  Ev |
|---|---|---|---|---|---|---|---|---|---|

### Scenario Bets（小赌注层）

| 票 | 赌的场景 | 当前估值 | 目标估值 | 为什么不等确认后再买  Ev |
|---|---|---|---|---|---|

### Watchlist

| 票 | 缺什么 |
|---|---|

### Rejects

| 票 | 当前估值 | 为什么拒  Ev |
|---|---|---|---|

## §6 Catalyst 日历 + 估值触发点

| 时间 | 事件 | 影响票 | 估值触发 | 场景切换  Ev |
|---|---|---|---|---|---|

## §7 Kill Criteria（平仓条件）

| 票 | 平仓信号 | 估值底线  Ev |
|---|---|---|---|

## AI Universe Caveat

[同上]
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

### 5. 分层数量必须收口

- Top Ideas：1-3 个（当前 regime 下）。
- Scenario Bets：1-3 个（只在特定场景成立的小赌注）。
- Watchlist：3-7 个。
- Rejects：至少 2 个，除非 universe 极窄。

如果候选太多，先按 purity 和 discovery edge 收紧；不要输出 20 个 ticker 让用户自己筛。

## Artifact / 保存策略

写入行业 topic：

```text
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md
```

路径不明 -> `agent` 解析行业。保存时 default artifact 仍为 `candidate-screener.md`，可用 qualifier 表示主题，例如 `candidate-screener-optical-module-equipment.md`。

## Workflow 联动

| 发现 | 下一步 |
|---|---|
| Top Idea 是陌生公司 | `stock-quickread` |
| Top Idea 的 revenue / margin / backlog driver 不清 | `driver-map` |
| value-chain pocket 依赖工程机制、设备链、工艺 | `mechanism-insight` |
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
- ❌ 工程机制不清仍强行列 names；应先 `mechanism-insight`。
- ❌ 公司 driver 不清仍写 growth thesis；应先 `driver-map`。
- ❌ 对 `[需查证]` 的客户 / 订单 / 供应链关系做强结论外推。

### 场景相关

- ❌ 不定义场景就排序——隐含"当前 regime 不变"是最大的假设漏洞。
- ❌ 把单场景推荐当全场景推荐——Top Idea 只在当前 regime 成立必须标清楚。
- ❌ Scenario Bets 不设仓位上限，按估值便宜加仓而不是按归零承受力定仓位。

## 篇幅基准

- 标准 Candidate Mining（含场景）：2000-3500 字 + 4-6 张表。
- 快速挖票：800-1500 字，Top Ideas 最多 2 个，场景定义可简化。
- 深度 universe pass（含完整 L/S 分场景）：3500-5000 字，按 regime 分组。

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


## Appendix: Financial Data

python _scripts/financial-data/actuals-to-appendix.py --tickers <TICKER_1>,<TICKER_2>,...

完整字段清单 -> `references/actuals-data-catalog.md`。

结构：`meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`。

消费规则：先读 actuals -> source_map 取 [S#]/[I#] 标签（不写 [actuals]）-> ratio 只用 actuals 真实值（不用 forward estimate）。

### Evidence Cards

主 agent 从每张 evidence card 取 1-3 个 evidence_triplets，按以下格式嵌入 artifact：

claim: <key factual claim from evidence card>
evidence: <supporting data>
source: [S#](url) or [I#](url)

至少 1 个 triplet（3 行）以满足 subagent_protocol hook 要求。
