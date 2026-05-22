---
name: candidate-screener
description: Turn a theme event or screen into a sourced long or short candidate funnel.
---

## Global Rules Capsule (v2)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 表格优先用 `Ev` / `证据` 短列承载 source、时间点和例外状态。默认 `S1@FY25`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；表后用 `S1 = source title, as-of/filed, link` registry 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Sub-Agent Evidence Protocol：本 skill 默认必须启动 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、ranking、thesis、valuation 或 model treatment；主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis。若当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Candidate Screener

把 hypothesis 转化成具体的可投资 candidate basket。LS 默认 long + short 双向。**核心价值不是列 ticker**——Bloomberg screener 比 AI 更准。AI 的差异化价值在于：

1. 把 vague hypothesis 拆解成具体 mechanism（hypothesis 工程化）
2. 强制双向（long / short basket，sell-side 不会做）
3. 强制每个 candidate 给 hypothesis-relevant 的受益机制 + source
4. 强制评估 priced-in 程度（避免推荐已被 reprice 的概念股）
5. 强制识别 hypothesis 本身的弱点（自我 challenge）
6. 推荐 1-2 家进入 deep research（漏斗收口）

如果输出只是 ticker list 没有上述任何一项，本 skill 就失败了。

## 心法

研究员产生新 hypothesis 是有 alpha 的——但找具体 candidates 这一步常常退化成"列已知概念股 + 抄卖方报告"。这是浪费 hypothesis 的过程。

本 skill 的工作逻辑是 **brainstorm + 验证**：
- AI 推理：从 hypothesis 推导**应该 expose 到什么 mechanism** → 应该有什么**业务特征** → 哪些**公司类型** → 具体 **names**
- 研究员验证：每个 name 的业务关联必须有 source；估值 / 流动性 / priced-in 必须有 quantitative anchor
- 最终 funnel：从 brainstorm 出的 N 个 candidates 收敛到 1-2 个值得做 deep research 的

**最重要的纪律**：AI 不假装是 universe screener。本 skill 的输出是 **inferential brainstorm**，是研究员的 starting point，不是 final list。研究员必须 cross-check Bloomberg / 行业数据，并主动问"我可能漏了什么"。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（候选公司、业务关联、客户 / 供应链关系、筛选指标、市场数据）都必须紧跟短 anchor，如 `S1@FY25` / `P1@2026-05-21`。
- No Orphan Truth Claim：输出前检查每个 candidate 的业务关联、受益机制、screen metric 和排除理由是否都有 anchor；无 source 时只能留 gap，不得升级为 verified。

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v2)`。本节只补充 screener-specific 要求。

特别强调：
- **每个 candidate 的"业务 / 受益机制"必须有 source link**——不允许 AI 编造业务关联
- **找不到 source 的关联标 `[需查证]`**——不能因为"听说过"就当 verified
- **本 skill 不用自动 internet fallback 把业务关联、客户 / 供应链关系或受益机制升级成 verified fact**：缺本地 / 一手 source 时继续保留 `[需查证]` 线索状态。
- **卖方研报中的"概念股归类"不算 source**——卖方分类有 marketing 嫌疑，要找原始 disclosure（10-K、IR 资料、合同公告）
- **估值数据必须有 as-of 时间戳**——AI 数据可能 stale，明确标注获取时点
- **Sub-agent 返回的 ticker / 业务关联必须按 capsule 的反幻觉硬规则抽查**——这个 skill 高度依赖 web search，URL / 公司事实假冒是真实风险

## Parallel Evidence Pass

本 skill 默认必须按候选公司或主题链路启动 sub-agent / delegate worker 并行查证；sub-agent 只能返回 evidence card：

- 可拆任务：候选 ticker 的业务关联、合同 / 客户 / 供应链证据、估值 / liquidity as-of、priced-in 线索、short candidate 受损机制。
- sub-agent 不得写最终 tier、Top Candidates、Recommended for Deep Research 或 long / short basket 判断；这些必须由主 agent 去重、抽查、排序。
- 主 agent 必须抽查关键 URL / claim，尤其是供应链、客户关系、主题受益机制和最新业务变化。
- 找不到原始披露的候选只能保留为 `[需查证]` 线索，不能进入 Tier 1 verified list。
- 如果当前 host / runner 真的无法 spawn，主 agent 必须在 evidence notes 中写明 `sub-agent unavailable`、失败原因、实际单线程取证范围和 source coverage caveat；不能把未并行执行伪装成已完成并行取证。

## AI 的局限（必读，前置警告）

这个 skill 比其他 skills 更容易失败。研究员**必须**理解 AI 的局限再用结果：

| 局限 | 影响 | Mitigation |
|---|---|---|
| **Universe 偏差** | AI 主要覆盖 mid/large cap（前 1000-2000 主流名单）；small cap、最新上市、最新重组公司大量缺失 | 输出末尾必须建议研究员 Bloomberg / 行业 screen 补充；主动问"我可能漏了哪些 names" |
| **知识 cutoff** | AI 不知道最近 6-12 个月的业务变化、并购、重组、IPO | 涉及最新动态时主动 web_search 验证；标注数据 as-of |
| **编造业务关联风险** | AI 倾向于把"听过"的关联当作 verified（特别是供应链、客户关系） | 每条关联强制 source link；不确定标 `[需查证]` |
| **概念股堆砌惯性** | AI 容易给主流市场已知 candidates（NVDA / MSFT 类）→ 没差异化 alpha | 反模式自查：是否只列已被 priced 的 obvious names |
| **估值数据 stale** | AI 知道的估值倍数可能滞后数月 | 明确标注 as-of；推荐研究员二次验证 |
| **Tier-N 供应链 mapping 不可靠** | AI 对 Tier-2/3 供应链关系常出错 | Tier 2/3 必须有 source；多个 source corroboration |

**输出末尾必须包含一段"AI 候选 ≠ 全市场"的 caveat**，提示研究员补充。

## 触发场景

### Mode A 触发（Thematic / Event-driven）
- "推荐受益于 [事件] 的股票"
- "[主题] 怎么参与"
- "[现象] 哪些 names 受益 / 受损"
- "找类似 [X 公司] 在 [Y 市场] 的标的"
- "[政策事件] 的 long / short basket"
- "如果 [假设场景] 发生，谁最敏感"

### Mode B 触发（Quant / Conditional）
- "找 [财务条件] 的标的"
- "screening: [估值条件 + 业务条件]"
- "[行业] 中 ROIC > X% / capex 强度 < Y / FCF yield > Z 的"
- "类似 [X] 但估值 < [Y]"

### Mixed Mode 触发（最常见）
- "受益于某主题 demand 的股票，PE < 30"
- "某行业中 capex/CFO < 0.5 + 高质量资源年限 > 8 年"
- "某软件子行业中 ARR 增速 > 30% + Rule of 40 > 50 + 不依赖单一平台 API"

混合是常态——不要强行划分 mode。但内部推理要清楚哪些条件是 thematic 派生（mechanism 推导），哪些是 quant 过滤（pattern matching）。

## 输入澄清要求（必填 6 维度）

如果用户给的 hypothesis 缺以下任一关键维度，**主动澄清而不是硬猜**。澄清耗时但避免输出走偏：

| 维度 | 含义 | 默认假设（用户没说时） |
|---|---|---|
| **时间窗口** | 3M / 12M / 24M+，决定 catalyst 急迫性 | 12M（中期） |
| **受益机制范围** | Direct（pure-play）/ Indirect（供应链）/ Spillover（associated）/ All | All（但分 Tier 输出） |
| **方向** | Long / Short / Both | Both（LS 默认双向） |
| **市场偏好** | US / 大中华（A股+港股+ADR）/ 日韩 / 全球 / 不限 | 用户主要覆盖市场（默认偏大中华 + 全球工业 / 科技主题） |
| **流动性 / size 约束** | 最小日均成交量 / 最小市值 | 大中华 ≥ 100M USD ADV / 美股 ≥ 50M USD ADV |
| **风格偏好** | Value / Growth / 不限 | 不限 |

如果用户说"AI 受益股"——这远不够。至少澄清"时间窗口（capex 周期不同）"、"机制（GPU manufacturer / cloud / AI app / 电力 / 供应链）"、"方向（long only 还是含 short）"。

**关键判断**：如果 hypothesis 本身在你听来都模糊（如"科技股推荐"），主动 push back 而不是给"FAANG + 几个 hot names"。

## Mode A: Thematic / Event-driven

### A.1 推理路径（必须显式）

按 4 步推理，每步输出给用户看（让用户校准）：

**Step 1: 拆解 hypothesis → 受益 mechanism**

例（hypothesis: "AI 数据中心电力 demand 受益股"）：
> Mechanism 拆解：
> 1. 数据中心新建 → 设备 / EPC / 选址用地受益（建设期 1-3 年 capex 周期）
> 2. 数据中心运营 → 电力供应商 / 输配电设备受益（运营期 10-30 年）
> 3. 电力 supply 紧张 → 现存核电 / 燃气电厂 PPA 涨价（短期 1-3 年）
> 4. 长期电力转型 → SMR / 储能 / 可再生 capex（5-15 年）
> 反向 mechanism（受损）：
> 1. 利率敏感的 utility（成本上升）
> 2. 电力大用户工业股（电费上行）

**Step 2: Mechanism → 业务特征**

每个 mechanism 翻译成"什么样的公司能 expose"：
> Mechanism 1（建设期）→ 业务特征：数据中心 EPC、HVAC、配电设备、地产开发
> Mechanism 3（PPA 涨价）→ 业务特征：现存核电运营、被低估的火电 IPP、长期 PPA 锁价 < spot 的资产

**Step 3: 业务特征 → 具体 candidates**

按 Tier 分组（见 §A.2）。每个 candidate 给：ticker / 市场 / 业务关联 + source / priced-in 评估。

**Step 4: 候选漏斗 → 推荐 1-2 家深入**

基于（机制清晰度 + priced-in 程度 + 流动性 + 临近 catalyst）四维 score，推荐 1-2 家进入 stock-quickread / peer-deep-dive。

### A.2 输出结构

```
## Hypothesis (restated by AI)

[一句话重新表述用户给的 hypothesis，确认理解正确]
[列出澄清的 6 维度参数]

---

## Mechanism Analysis

[Step 1-2 的输出：拆解 mechanism + 翻译业务特征]

---

## Tier 1 — Direct Exposure (Pure-play / 主营 > 50% 受益)

| Ticker | Market | 业务 / 受益机制 | 受益强度 | Liquidity (ADV) | 估值锚 | Priced-in | Ev |
|---|---|---|---|---|---|---|---|
| AAA US | NYSE | 100% 数据中心运营核电；35% 容量已签 hyperscaler PPA $80/MWh | High | $150M | EV/EBITDA 12x (vs 5Y mean 8x) | 部分 | S1@FY25;S2@2026 |
| BBB | A 股 | 60% 收入来自数据中心 HVAC | High | $80M | PE 25x (vs 同业 18x) | Mostly | S3@FY25 |

Sources: `S1 = [filing/source title], as-of/filed [date], [link]`; `S2 = [contract/news source], as-of/filed [date], [link]`; `S3 = [segment source], as-of/filed [date], [link]`.

**Tier 1 判断**：受益机制 direct 且 quantifiable；普遍 priced-in 较多；alpha 来自基本面 vs 估值的 spread

## Tier 2 — Indirect / Supply Chain (Tier-N supplier / 30-50% 收入受益)

| Ticker | ... | ... | Medium | ... | ... | Less | ... |
| CCC | NYSE | Tier-1 配电设备给数据中心，但 60% 收入仍是工业 | Medium | $200M | EV/EBITDA 10x (vs 5Y 8x) | Partial | [10-K segment](url) |

**Tier 2 判断**：受益机制 indirect；priced-in 通常较少（市场没把它当 AI 概念股）；但需 verify 受益的实际 magnitude

## Tier 3 — Spillover / Theme Association (< 30% 收入受益 / 弱关联)

| Ticker | ... | ... | Low | ... | ... | Variable | ... |

**Tier 3 判断**：弱关联但市场可能 trade it as theme stock；high beta to theme but low fundamental link；short candidate 高发区

## Short Candidates

[同样的表格结构，方向反过来]

| Ticker | Market | 受损机制 | 受损强度 | Liquidity | 估值 | Already-shorting? | Ev |
|---|---|---|---|---|---|---|---|

Sources: `S1 = [source title/provider], as-of [date], [link/location]`.

**Short Candidate 关键判断**：
- Priced-in 评估更重要——明显的 short 多数已 priced（high SI、负面 sentiment）
- 受益于 thematic-priced-up 但基本面不变的 candidates 是优质 short
- 列 short borrow availability + rate（如可获取）

## Recommended for Deep Research (1-2 家)

按 (机制清晰度 × 50%) + (priced-in 反向 × 30%) + (流动性 × 10%) + (catalyst 临近 × 10%) 综合 score：

- **AAA US** (Tier 1, score 8/10): 机制最清晰 + 临近 Q3 PPA 公告 catalyst + 估值仅 partial priced-in → 触发 `stock-quickread`
- **CCC** (Tier 2, score 7/10): 受益 magnitude 待 verify 但 priced-in 几乎为 0 → 触发 `stock-quickread` 验证 segment exposure

## Hypothesis 漏洞自检

[必填，至少 3 条——这是 LS 研究员防止 over-confidence 的关键]
1. **Hypothesis 弱点**：AI 数据中心电力 demand 假设依赖 hyperscaler capex 持续——历史 base rate：tech capex 周期通常 2-3 年，2024-2026 已是 capex 高峰期，受益股 priced 充分
2. **Tier 风险**：Tier 1 已普遍 priced，alpha 主要来自 Tier 2-3 的 mispricing，但 Tier 2-3 的 mechanism 验证更难
3. **反向风险**：如果 inference cost 下降快于预期（→ datacenter capex 不需要 ramp 这么快），整个 hypothesis 大幅 weakening

## AI 候选 ≠ 全市场（caveat）

本输出基于 AI 已知的 mid/large cap 主流 universe（约 1000-2000 names）。可能漏：
- Small cap / micro cap（< $1B 市值）
- 最近 12 个月 IPO / spin-off / 重组的公司
- 主要在新兴市场上市的标的
- 你应该 cross-check：[1] Bloomberg theme screen [2] 行业研究机构（Wood Mac / Gartner / IDC） [3] 主动问"我漏了哪些 names"

[然后 chat 直接 prompt 用户：是否要补充某些 names？]
```

### Mode A 输出篇幅

1500-2500 字 + 4-5 张 candidate 表格。低于 1500 大概率推理不深；超过 2500 在水。

---

## Mode B: Quant / Conditional Screening

### B.1 推理路径

Mode B 的核心是 pattern matching，但 AI 仍需要做 inferential 工作（不是真 quant screen）：

**Step 1: 翻译条件 → 业务特征**

例（条件: "EV/EBITDA < 8x + FCF yield > 8% + capex/D&A < 0.7"）：
> 翻译：
> - EV/EBITDA < 8x → 价值股 / 周期股 / 困境股
> - FCF yield > 8% → mature 业务、capital return 重于 reinvestment
> - capex/D&A < 0.7 → 收割期资本周期，不再大投资
> 综合 profile：mature cyclical 收割期公司

**Step 2: Pattern matching**

在 AI universe 里识别匹配 profile 的 names。**关键**：必须区分以下三种来源：
- AI 通过具体数字 verified 匹配
- AI 推测匹配但需 verify
- AI 不确定（潜在 candidate 但 score 偏弱）

**Step 3: 数据验证**

对每个匹配 candidate 给具体数字（带 source）。AI 数据可能 stale，主动 web_search 最新季度数据。

### B.2 输出结构

```
## Screening Criteria (restated)

[列出用户的具体条件 + 澄清的维度]

---

## Conditions Translation

[Step 1 的输出：翻译条件成业务 profile]

---

## Matched Candidates

| Ticker | Market | EV/EBITDA | FCF yield | Capex/D&A | All criteria met? | Ev |
|---|---|---|---|---|---|---|
| AAA | US | 6.5x | 11% | 0.5 | ✅ | S1@2026Q1;S2@[date] |

Sources: `S1 = [filing/source title], as-of/filed [date], [link]`; `S2 = [market data provider], as-of [date]`.
| BBB | A 股 | 7.8x | 9% | 0.6 | ✅ | 2025 Q4 | [年报](url) |
| CCC | HK | 8.2x ❌ | 10% | 0.65 | ❌ (EV/EBITDA fail by 0.2x) | 2026 Q1 | [年报](url) |

**Note**: 包括 ❌ 但接近的 candidates（边缘合格）—— 给研究员判断空间。

## Top Candidates by Match Quality

按 (满足条件数 × 50%) + (额外 attractive 维度 × 30%) + (流动性 × 20%) 排序：

1. **AAA**: 全部条件满足 + ROIC 18% (extra)
2. **BBB**: 全部条件满足 + 股息 yield 6% (extra)

## Recommended for Deep Research (1-2)

[同 Mode A]

## Hypothesis 漏洞自检

[即使是 quant screening，也要质疑条件本身是否 capture 想要的 thesis]
- 你的条件可能筛出 value trap（FCF yield 高但因为基本面持续恶化）
- Capex/D&A < 0.7 在 emerging tech 行业可能意味着错过增长（不是 attractive）
- 建议加 ROIC vs WACC > 200bps 过滤 value trap

## AI 候选 ≠ 全市场 (caveat)

[同 Mode A]
```

### Mode B 输出篇幅

1200-2000 字 + 1-2 张 candidate 表。Mode B 比 Mode A 少推理多列表，但 caveat 和漏洞自检不能省。

---

## Mixed Mode（最常见）

混合查询的关键：内部推理要明确**哪些条件是 thematic（mechanism 推导）+ 哪些是 quant（pattern matching）**。

输出顺序：
1. Restate hypothesis + 6 维度
2. Mechanism analysis（thematic 部分）
3. Conditions translation（quant 部分）
4. **同时满足 mechanism + conditions 的 candidates**
5. Tier 分组（Direct / Indirect / Spillover）+ Quant pass/fail 双轴
6. Short candidates（如方向 = both）
7. Recommended for deep research
8. Hypothesis 漏洞 + AI universe caveat

输出篇幅：2000-3000 字（混合最复杂）

## 共同输出元素（无论 mode）

每次输出必须包含：

### 1. **Source for every business linkage**
每个 candidate 的"业务 / 受益机制"列必须有 source link。常见 source 类型：
- 10-K / 10-Q segment data
- IR presentation（注意 marketing spin）
- 8-K / 公告（M&A、合同）
- 卖方 deep dive 报告（**作为线索**，原始 source 还是 filing）
- 行业研究（IHS / Wood Mac / IDC）—— 用于 supply chain mapping

不确定的关联标 `[需查证]` —— **不能编造**。

### 2. **Priced-in 评估（quick estimate）**
不需要 AI 做 reverse DCF（太重）。简化为 3 级：
- **Fully priced**: 估值倍数 vs 5Y mean 已 +30% 以上 / 同业溢价 >20% / 已被卖方主推为 thematic name
- **Partial priced**: 估值倍数 vs 5Y mean +10-30% / 部分 thematic 溢价
- **Not priced (yet)**: 估值倍数 vs 5Y mean 持平或更低 / 市场还没 link 到 thematic

每个 candidate 必须给 priced-in 评估 + 简短理由。**Alpha 来自 not-priced 或 partial-priced 的 names**——fully priced 的 candidates 列出来主要是 short 候选或防漏。

### 3. **Hypothesis 漏洞自检**
LS 研究员最大风险是 self-reinforcing hypothesis。AI 必须 actively challenge：
- Hypothesis 本身的弱点（依赖什么 assumption）
- Base rate（历史上类似 hypothesis 的成功率）
- Tier 风险（Tier 1 priced / Tier 2 难 verify / Tier 3 weak link）
- 反向风险（什么发生会让 hypothesis 失效）

至少 3 条具体的 challenge，不允许"hypothesis 看起来 sound"这种空话。

### 4. **AI universe caveat**
固定模板提示用户 AI 不是 universe screener。

## Workflow 联动

## Artifact 输出契约

默认写入当前日期化保存路径：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-candidate-screener.md
```

如果当前日期化保存路径不明确，先 handoff 到 `new-session` 解析路径；不要临时发明目录或未解析路径就写入。

这个文件是 candidate funnel 的留痕，不是最终 thesis；后续 `stock-quickread`、`peer-deep-dive`、`research-journal`、`next-step` 可以读取其中的 recommended candidates、mechanism、source map 和 rejected names。

如果用户只是自由 brainstorm 且明确不需要留痕，可以只在对话中输出；否则默认保存筛选结果，避免下次重新从同一个 hypothesis 开始。

| 场景 | 触发的下游 skill |
|---|---|
| 推荐 1-2 家 deep research | `stock-quickread` |
| 推荐 3-8 家批量研究 | `peer-deep-dive` |
| Hypothesis 跨市场（如"中国 vs 美国 类似 names"） | `cross-market-compare` |
| 推荐 candidate 的受益机制依赖复杂工程原理 / 设备链条 / know-how | `mechanism-map` |
| 推荐 candidate 的受益机制依赖复杂 revenue / margin driver | `driver-map` |
| 推荐结果暴露 hypothesis 弱点 | 重新评估 hypothesis 或触发 `bear-pre-mortem` 反向思考 |
| 筛选暴露高价值怪异点 | `next-step` |
| 筛选完成后需要沉淀 | `research-journal` |

## 反模式自查

写完必须自检：

**编造 / 概念股堆砌**
- ❌ Candidate 的"业务 / 受益机制"列无 source link → 必须补
- ❌ 列了一堆 obvious names（NVDA / MSFT / GOOG）但没差异化分析 → 重新做
- ❌ Tier-2/3 关联只写"供应链相关"无具体 supplier link → 没 verify
- ❌ 把卖方研报的"概念股归类"当作业务关联依据 → 卖方分类有 marketing 嫌疑
- ❌ AI 依据"听过"或推测列 candidate 但没标 [需查证] → 编造嫌疑
- ❌ 把 sub-agent evidence card 直接当成最终 Tier / Top Candidates → 必须由主 agent 抽查、去重、分层和排序

**Hypothesis / Tiering**
- ❌ 没拆解 mechanism 直接列 candidates → AI 推理价值丢失
- ❌ Tier 1/2/3 划分没有具体标准（收入占比 % 等） → 无法 verify
- ❌ Hypothesis 漏洞自检写空话（"thesis 看起来 sound"）→ 必须给具体 challenge
- ❌ Hypothesis 太 vague 但 AI 没主动澄清就开始 list → 应该 push back
- ❌ Candidate 的受益机制依赖复杂工程原理 / 设备链条，却没有建议 `mechanism-map` 先讲清楚机制
- ❌ Candidate 的受益机制依赖复杂 revenue / margin driver，却没有建议 `driver-map` 验证量级

**LS 双向**
- ❌ 方向 = both 但 short candidates 缺失或硬凑 → 真没就明说"无明显 short"
- ❌ Short candidates 不评估 priced-in → 多数明显 short 已 priced
- ❌ Long / short basket 的 priced-in 评估不对称 → 双向都要做

**Priced-in / 估值数据**
- ❌ Priced-in 评估全部默认 "Partial" → 偷懒
- ❌ 估值数据无 as-of → AI 数据可能 stale
- ❌ 没说明数据 source（Bloomberg / 自算） → 无法 verify

**Universe / Caveat**
- ❌ 输出末尾没 "AI 候选 ≠ 全市场" caveat → 用户可能误以为这是 universe screen
- ❌ 没主动问"我漏了哪些 names" → 错失研究员补充机会

**漏斗收口**
- ❌ 推荐 deep research > 3 家 → 漏斗没收口，研究员还是 overwhelmed
- ❌ 推荐 0 家（"没有合适的"）但也没解释为什么 → 应该说明 hypothesis 本身的问题

## 篇幅基准

| Mode | 字数 | 表格数 |
|---|---|---|
| Mode A: Thematic | 1500-2500 | 4-5（含 short 表 + 推荐表） |
| Mode B: Quant | 1200-2000 | 1-2（matched candidates 表 + 推荐表） |
| Mixed Mode | 2000-3000 | 5-6 |

**篇幅触发的 trade-off**：
- 低于下限 → 推理不深 / candidates 太少 / 漏洞自检敷衍
- 超过上限 → 在堆 candidates 而非筛选；应该收紧 Tier / 减少 candidate 数

**Candidate 数量基准**：
- Tier 1: 3-5 家（pure-play 通常少）
- Tier 2: 3-5 家
- Tier 3: 1-3 家（如有）
- Short basket: 3-5 家（如方向 = both）
- 推荐 deep research: **必须 1-2 家**，不允许 0 或 ≥ 3

---

## 与 information-impact 的边界

两个 skill 都涉及 source 验证、claim 拆解，但**信息流方向相反**：

| | candidate-screener | information-impact |
|---|---|---|
| 输入 | Hypothesis / 主题 / 条件 | 已知 claim（一条信息） |
| 任务 | 找候选 names | 验证真伪 + research relevance |
| 方向 | Outbound（从 hypothesis 出发） | Inbound（信息已到） |
| 频率 | 每周 2-3 次（中频） | 每天几十次（高频） |

**不要混淆**：
- "某主题受益股有哪些" → candidate-screener
- "刚听说 X 公司是某 hyperscaler PPA 客户" → information-impact

如果用户问的是混合（"我听说有这个主题，能列 candidates 吗"），先用 information-impact 验证 claim，再用 candidate-screener 探索 candidates。
