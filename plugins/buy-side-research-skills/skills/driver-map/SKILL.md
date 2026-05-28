---
name: driver-map
description: Decompose revenue margin backlog price volume mix and segment drivers before modeling.
---

# Driver Map

Decompose revenue margin backlog price volume mix and segment drivers before modeling.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

把公司披露口径翻译成真实业务和可建模 driver。**核心价值不是写一个收入拆分表**，而是防止研究员和 AI 把会计 segment、管理层 narrative、卖方分类或概念股标签误当成经济实质。

如果输出只是在复述公司 segment 名称，或者把未披露的 driver 编成事实，本 skill 就失败了。

## 心法

很多投研错误不是发生在 DCF、comps 或 thesis 结论，而是发生在更前面：你以为你知道这家公司靠什么增长，但其实只是接受了公司给的 bucket 名称。`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。

本 skill 复用 `3-statement-model / dcf-model / comps-analysis / model-update` 的 `Reported segment → Business reality → Model driver` 逻辑，也复用 `Research Runtime Capsule` 的 Senior Analyst Radar。它是研究原语：后续可以 feed `3-statement-model / dcf-model / comps-analysis / model-update`、`alpha-thesis`、`primary-research-plan`、`peer-deep-dive`、`pair-trade` 和 `research-journal`，但它自己不做估值、不写完整 thesis，也不设计访谈计划。

**最重要的纪律**：不披露的 driver 不能编；只能写成 `[来源待补]`、`[需查证]` 或 researcher assumption。没有 source 的 driver map 是假精确。

## Financial-Data 联动

`financial-data` 是本 skill 的 preferred upstream input，但不能替代 driver 判断。

读取顺序：

1. 先读 `topics/company/<company-slug>/_cache/financial-data/internal/actuals-resolved.json`。
2. 如果 `statements.revenue_split` 存在且非空，直接 review 其披露口径：`source_type = official-xbrl-dimension` 标为 `provider-structured`，`source_type = filing-table-extracted-review` 标为 `provider-table-review`，再转成 model bucket。
3. 如果 `revenue_split` 缺失或为空，读 `internal/evidence-pack.json` / `internal/completeness.json` 确认缺口，再读 `internal/full-filing.md`，用 LLM 从原文抽 disclosed revenue split，并标为 `llm-extracted-review`。
4. 如果原文也没有披露，标为 `not-disclosed`；不能编造 segment、product 或 geography split。

本 skill 可以改变收入 bucket 的建模处理方式，但不能覆盖 `financial-data` 的 completeness。`provider-structured`、`provider-table-review`、`provider-normalized-review`、`llm-extracted-review` 和 `not-disclosed` 必须在 `driver-map.md` 和 `internal/driver-map.json` 中分清。若 `revenue_split` row 标有 `review_required: true`，必须由 LLM 解释 axis/member 并映射 model bucket，不能直接当作最终建模口径。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **披露名称诱导** | AI 会把 `Solutions`、`Systems`、`Industrial` 这类名称当成真实业务 | 强制做 `Reported Bucket → Business Reality`，不让 bucket 名称直接进入模型 |
| **未披露 driver 编造** | AI 容易把行业常识写成公司披露事实 | 未披露一律标 proxy / assumption / `[来源待补]` |
| **KPI 口径错配** | orders、backlog、book-to-bill、installed base 在不同行业含义不同 | 每个 KPI 写 source、definition、as-of |
| **peer 类比过度** | 同业有 driver 不代表目标公司也披露或适用 | peer driver 只能作假设，不可替代公司 source |
| **概念暴露误读** | 主题相关不等于 revenue driver | 区分 direct revenue driver、indirect proxy、theme association |

## 触发场景

- "帮我拆一下这家公司 revenue driver"
- "这家公司收入怎么拆"
- "这个 segment / bucket 到底是什么业务"
- "某业务 bucket 为什么这么拆"
- "这个 reported bucket 对应什么业务实质"
- "这家公司靠什么增长"
- "为什么收入涨了但 margin 没涨"
- "backlog / orders 怎么进收入"
- "price / volume / mix 哪个在驱动"
- "这个业务口径是不是有点怪"

### 不应触发

- "帮我搭 model / 做 DCF / comps" → `3-statement-model / dcf-model / comps-analysis / model-update`，但它应消费或先产出 driver-map。
- "这家公司到底做什么 / 业务怎么演变 / segment 或 KPI 历史口径怎么变" → `company-primer`，先打牢公司基础和 disclosure evolution。
- "这个设备链条 / 工艺流程怎么连接" → `mechanism-map`，先搞清机制再拆 driver。
- "快速看一家公司值不值得研究" → `stock-quickread`，若 driver 不清再进入本 skill。
- "几家公司一起看、排序" → `peer-deep-dive`，若 KPI 口径不可比再引用本 skill。
- "写 long / short thesis" → `alpha-thesis`，若 thesis 依赖未拆清的 driver 再回到本 skill。

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **对象** | 公司 / segment / 产品线 / 行业 bucket | 用户给 ticker 时按公司；给业务名时按 segment |
| **研究目的** | model / thesis / peer compare / earnings / journal | 默认服务 model 和 thesis |
| **时间口径** | 最新年报、最新季度、过去 3-5 年趋势 | 最新可验证披露 + 必要历史对比 |
| **driver 范围** | revenue / margin / backlog / price-volume-mix / installed base | revenue-first，必要时扩到 margin |
| **source cutoff** | 使用哪份 filing / call / IR deck | 最新可验证 source；不确定标 `[来源待补]` |
| **保存需求** | 只在对话输出 / 写入 company driver-map cache | 默认对话；用户要求保存为建模输入时外显 `driver-map.md`，机器 JSON 写 `internal/driver-map.json` |

如果用户只说"拆 driver"，至少确认公司 / 业务范围；如果用户明确给出业务 bucket，则直接开始拆，不要把问题扩大成完整公司研究。

## 工作流

### Step 1: Reported Bucket → Business Reality

先把公司披露的 bucket 翻译成真实业务，不要直接接受命名。

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
| [segment / product] | [实际卖什么 / 做什么] | [客户或应用] | [S1](./_cache/sources/company-annual-report.md) | [缺口] |

遇到 `GTE / GTS / Industrial Products / Industrial Solutions / CTS` 这类拆分时，要直接触发 Senior Analyst Radar：这可能不是普通并列 segment，而是 gas turbine 系统价值链、产品本体、配套设备、service、controls 或 end-market 维度的混合拆分。

### Step 2: Business Reality → Model Driver

把每个业务 bucket 映射到可观察 driver。

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| Equipment | units / MW / MTPA / orders | price / mix | orders, backlog, shipments | High / Medium / Low |
| Services | installed base | utilization / attach rate | service revenue, fleet hours | High / Medium / Low |

常用 driver library：
- **Volume**：unit shipment、capacity、MTPA、MW、rig count、installed base、customer count。
- **Price**：ASP、contract escalation、commodity pass-through、pricing index。
- **Mix**：equipment vs services、newbuild vs aftermarket、large frame vs aero-derivative、project vs recurring。
- **Backlog / orders**：order intake、book-to-bill、backlog conversion、project timing。
- **Utilization**：fleet utilization、factory load、service hours、capacity factor。
- **Installed base / attach**：service attach rate、replacement cycle、parts intensity。
- **End-market proxy**：LNG FID、data center power demand、aerospace build rate、grid capex。

### Step 3: Driver Quality

每个 driver 必须评级，但评级不能凭感觉：

| Rating | Hard standard |
|---|---|
| **High** | 公司直接披露 KPI / bucket revenue / backlog / margin，且定义清楚、可跟踪 |
| **Medium** | 公司部分披露，需用 peer / industry proxy 补足，但方向可验证 |
| **Low** | 主要靠推断、卖方拆分或主题关联，必须标 `[来源待补]` / `[需查证]` |

### Step 4: Disclosure vs Inference / Proxy Strategy

每个关键 driver claim 都必须标清证据状态。合理推断可以写，但不能写成公司事实；proxy 可以用，但必须说明 proxy 风险和模型处理方式。

Evidence status 只能用：
- `company disclosed`：公司直接披露该 driver / KPI / bucket。
- `company implied`：公司语言或披露结构暗示该 driver，但没有完整 KPI。
- `peer proxy`：用同业或行业 proxy 近似。
- `researcher assumption`：研究员假设，必须可被后续验证。
- `unknown`：还不知道，不能进入 base-case model。

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| [driver 判断] | company disclosed / company implied / peer proxy / researcher assumption / unknown | [proxy or none] | [proxy 可能误导之处] | base case / sensitivity / scenario only / exclude |

Hard rule：`Low` confidence 或 `unknown` driver 不能进入单一 base case；只能进入 sensitivity、scenario 或标 `[来源待补]`，直到有更强 source。

### Step 5: Implications

说明这个 driver map 如何影响后续研究：
- 对 `3-statement-model / dcf-model / comps-analysis / model-update`：哪些 line item 应该按 driver 建模。
- 对 `alpha-thesis`：variant view 应该落在哪个 driver。
- 对 `primary-research-plan`：哪些 driver 假设需要 expert call、customer / supplier channel check、survey 或 fieldwork 验证。
- 对 `peer-deep-dive`：哪些 KPI 才可比，哪些不可比。
- 对 `pair-trade`：两腿是否受同一 driver 驱动，还是只是主题相似。
- 对 `research-journal`：哪些认知已经想清楚、值得沉淀。

## 输出结构

```markdown
## Driver Map

**结论先行**
[一句话说明这家公司 / 业务最应该按什么 driver 理解，最大披露缺口在哪里]

## Reported Bucket → Business Reality

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|

## Business Reality → Model Driver

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|

## Driver Quality

| Driver | Rating | Why | Ev | What would improve confidence |
|---|---|---|---|---|

## Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|

## Weird Buckets / Senior Analyst Radar

**这里值得深挖**
- 怪异点：[披露 / bucket / KPI 哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]

## Implications for model / thesis

- [这个 driver map 会如何改变 model / thesis / peer compare]

## 可以问 AI

- [1-2 个下一步问题]
```

## 可选保存

默认只输出到对话。用户明确要求保存为建模输入时，写入 company topic cache：

```text
topics/company/<company-slug>/_cache/driver-map/
  driver-map.md
  internal/
    driver-map.json
```

`driver-map.md` 是人和 LLM 的默认入口，必须明确推荐模型类型：DCF、comps、sum-of-the-parts、3-statement only、update existing model，或“不适合建模 / 先补数据”。`internal/driver-map.json` 至少包含 `segment_geography_treatment`、`revenue_drivers`、`margin_drivers`、`model_treatment`、`recommended_model_modules`、`valuation_methods`、`confidence_source_status`。

如果使用了 `financial-data`，`internal/driver-map.json` 还必须在 `confidence_source_status` 或相邻字段中记录收入拆分来源：`provider-structured`、`provider-table-review`、`llm-extracted-review` 或 `not-disclosed`。

如果当前没有 company topic，先 handoff 到 `new-session` 创建 / 解析路径，不要自行发明大量目录。theme / industry / pair topic 只链接或摘要 company cache，不保存第二套 canonical company driver-map。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 用户要继续搭 operating model / DCF / comps | `3-statement-model / dcf-model / comps-analysis / model-update` |
| driver work 发现公司业务边界、segment rename、KPI recast 或 material M&A 历史不清 | `company-primer` |
| driver map 暴露 variant view | `alpha-thesis` |
| driver 假设需要 expert call、customer / supplier channel check、survey 或 fieldwork 验证 | `primary-research-plan` |
| 多家公司 driver 需要横向比较 | `peer-deep-dive` |
| 两家公司是否受同一 driver 驱动 | `pair-trade` |
| driver 质量低或 bucket 怪，需要更好问题 | `next-step` |
| 已经研究清楚，想沉淀认知 | `research-journal` |
| 供应链 / 客户 claim 影响收入 driver | 先 `information-impact`，再回到本 skill |
| 业务 bucket 背后涉及工程机制 / 设备链条 / know-how gap | 先 `mechanism-map`，再回到本 skill |

## 反模式自查

### Source 类
- ❌ Reported bucket、segment revenue、orders、backlog、margin 没有 source / as-of。
- ❌ 用卖方拆分替代公司披露，却没标注为 assumption。
- ❌ 把合理推断、peer proxy 或 researcher assumption 写成 company disclosed fact。
- ❌ 多个 source 口径冲突但只挑一个顺手的用。
- ❌ 把 workbook 里的旧数字当 source。
- ❌ 把 sub-agent evidence card 直接写成 final driver tree / model treatment，而没有主 agent 抽查 URL、处理冲突和统一口径。

### Logic 类
- ❌ 只复述 segment 名称，没有翻译 business reality。
- ❌ 只写 revenue driver，不问 margin driver 是否不同。
- ❌ Low confidence driver 没有进入 sensitivity / scenario，却直接进入 base case。
- ❌ 把 theme association 写成 direct revenue driver。
- ❌ 用历史 CAGR 代替 driver。
- ❌ 看到 `Other / Solutions / Systems / Industrial` 这种 bucket 不追问。

### Workflow 类
- ❌ 用户只是要 driver-map，却输出完整 DCF / comps。
- ❌ 用户要搭 model，却停在 driver-map，不 handoff 到 `3-statement-model / dcf-model / comps-analysis / model-update`。
- ❌ driver confidence 是 Low，却被后续 thesis 当作核心事实。
- ❌ 形成清楚认知后没有建议 `research-journal` 沉淀。

## 篇幅基准

- Quick driver check：400-700 字 + 1-2 张表。
- Full company / segment driver-map：900-1600 字 + 3-4 张表。
- 超过 1800 字通常说明范围过大，应拆成 `peer-deep-dive`、`3-statement-model / dcf-model / comps-analysis / model-update` 或多个 segment。

## 与相邻 skill 的边界

- `3-statement-model / dcf-model / comps-analysis / model-update` 做 operating model、DCF、comps、workbook update；本 skill 只做 driver-map。
- `primary-research-plan` 设计合规 expert call、channel check、survey 和 fieldwork 计划；本 skill 只指出哪些 driver assumption 需要 field evidence。
- `company-primer` 处理公司业务基础、业务演变和 disclosure evolution；本 skill 在这些基础清楚后才把 bucket 映射成 model driver。
- `stock-quickread` 快速判断是否值得继续看；本 skill 深挖 revenue / margin driver。
- `peer-deep-dive` 做横向排序和 cross-cut insight；本 skill 提供可比较的 driver 口径。
- `mechanism-map` 处理行业 know-how、工程机制、设备链条、工艺流程和术语；本 skill 只处理公司业务到 model driver 的映射。
