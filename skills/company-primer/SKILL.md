---
name: company-primer
description: Use when researching an unfamiliar company in depth, mapping what it sells, how the business evolved, how segments or KPIs changed, or why disclosure history may affect later driver, thesis, peer, or model work.
---

## Global Rules Capsule (v1)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查 URL 和 claim 是否匹配。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Company Primer

把一家公司的业务基础和披露演变讲清楚，让后续 `driver-map`、`stock-quickread`、`alpha-thesis`、`peer-deep-dive` 和 `financial-model` 不建立在错的公司理解上。核心价值不是写“公司介绍”，而是识别这家公司到底卖什么、谁付钱、业务边界如何变化、披露口径哪里断裂，以及哪些历史变化会污染后续 driver 或 thesis 判断。

如果输出变成成立年份、总部、管理层履历、按时间顺序罗列收购新闻、IR 话术复述或通用业务百科，本 skill 就失败了。历史只在它改变业务实质、segment 可比性、KPI 连续性、客户/产品边界或后续研究优先级时才写。

## 心法

`company-primer` 是公司研究的地基层。很多后续错误不是因为模型算错，而是因为研究员一开始就把公司理解错了：把旧业务当成当前业务、把 recast 后的 segment 当成连续历史、把 renamed KPI 当成同一口径、把并购带来的结构变化当成 organic trend。

本 skill 只回答“这家公司现在到底是什么、怎么变成今天这样、披露口径能不能直接拿来比较”。它不是 quickread 的投资判断，也不是 driver-map 的模型变量拆分。它把公司事实和披露历史整理到足够可靠，让下一层 skill 可以安全工作。

好的 primer 应该让读者少问泛泛背景问题，多问具体研究问题：这个 segment 是并购来的还是内生长出来的？这个 KPI 前后口径是否连续？这个业务现在还是利润核心，还是只是收入噪音？这些问题比“公司成立于哪一年”更接近 buy-side edge。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 company-primer-specific 要求。

特别强调：
- 公司业务、产品、客户、segment、KPI、并购、剥离、recast、rename、discontinued operations 和重大历史时间点必须有 source / as-of。
- 优先使用最新 10-K / annual report、10-Q、20-F、IR deck、earnings call、press release、transaction filing、公司官网业务页；二手资料只能补线索，不能替代公司披露。
- 历史事件只写影响当前业务理解的部分；每个历史事件必须说明它改变了什么业务边界或披露口径。
- Segment / KPI 前后口径不一致时必须标注，不得把不同定义的时间序列拼成一个 trend。
- 多个 source 对 segment、产品边界或交易影响说法冲突时，必须标注冲突并说明暂用哪个口径。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **公司历史流水账惯性** | AI 容易罗列成立年份、总部、管理层、并购清单 | 只写改变当前业务实质、披露口径或研究优先级的历史 |
| **业务边界幻觉** | AI 容易把相似产品、客户或供应链关系写成公司事实 | 每个产品 / 客户 / end-market claim 都回到公司 source |
| **披露连续性误读** | segment rename、recast、discontinued ops 被误当作连续趋势 | 强制做 disclosure timeline 和 comparability flag |
| **并购影响过度简化** | 把收购写成“增强能力”，不说明 revenue / margin / segment 影响 | 写清 acquired business 进入哪个 bucket、是否改变可比性 |
| **driver 越界** | 在 primer 里直接拆 revenue / margin driver 或写 model line item | 只标出 driver questions；正式拆分 handoff 到 `driver-map` |
| **机制越界** | 产品或设备原理没懂就硬解释 value capture | 触发 `mechanism-map`，不要在 primer 里发明 know-how |

## 触发场景

### Mode A: Foundation Primer

- “深度研究一下这家公司是做什么的”
- “这家公司业务到底是什么”
- “给我一个公司 primer”
- “我对这家公司不熟，但想认真开始看”
- “这家公司卖什么、客户是谁、收入从哪里来”
- “帮我把公司基础打牢”

### Mode B: Business Evolution Audit

- “这家公司过去几年怎么变成现在这样”
- “哪些并购 / 剥离改变了业务结构”
- “这家公司业务边界变过吗”
- “现在的业务和几年前是不是一回事”
- “这家公司哪块业务是核心，哪块是遗留 / 噪音”

### Mode C: Disclosure Evolution Audit

- “segment 口径是不是变过”
- “这个 KPI 前后可比吗”
- “为什么披露口径断了”
- “这家公司 rename / recast 后怎么对齐”
- “把 segment / KPI 历史口径梳理一下”
- “这个 disclosure map 会不会影响后续 driver”

### 不应触发

- 用户只想 30 分钟判断值不值得看 → `stock-quickread`。
- 用户要拆 revenue、margin、backlog、price-volume-mix 或 model driver → `driver-map`。
- 用户要解释工艺、工程原理、设备链条或专业术语 → `mechanism-map`。
- 用户要写 long / short thesis、variant view、catalyst、kill criteria → `alpha-thesis`。
- 用户要横向比较多家公司、peer 排序或 KPI 可比性排名 → `peer-deep-dive`。

## 输入澄清要求

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **对象** | ticker / 公司名 / 子公司 / segment / 产品线 | 默认按公司整体；若用户给 segment，则只做该 segment |
| **研究目的** | 建 coverage / 写 thesis / 做 peer / 搭 model / 看财报 | 默认服务后续 driver-map 和 thesis |
| **时间范围** | 最新业务结构 / 过去 3-5 年 / 上市以来 / 某次交易前后 | 默认最新披露 + 影响当前业务理解的历史变化 |
| **披露范围** | segment / KPI / geography / customer / product | 默认 segment + KPI + material M&A / divestiture |
| **source 状态** | 用户给 source / 需要自行找 source / source 冲突 | source 不足时标 `[来源待补]`，不编事实 |
| **保存需求** | 只在对话输出 / 写入 topic session | 默认对话；用户要求保存时写 `company-primer.md` |

如果用户只给 ticker，不要追问一堆背景；按 Foundation Primer 开始，但把 source gap 标出来。如果用户明确要披露口径对齐，则直接进入 Disclosure Evolution Audit，不要先写完整公司介绍。

## 模式设计

### Mode A: Foundation Primer

目标是建立最小但可靠的公司地基。

必须回答：
- 现在卖什么，谁付钱，收入来自一次性设备、项目、服务、订阅、耗材、usage 还是金融 / leasing。
- 当前业务 bucket 和真实业务边界是否一致。
- 哪些产品 / 客户 / end-market 是利润或战略核心，哪些只是收入噪音。
- 哪些基础事实仍然缺 source，不能进入下一步判断。

不要做：
- 不写完整公司历史。
- 不写 5 年财务回顾。
- 不写 management bio。
- 不用营销词替代业务实质。

### Mode B: Business Evolution Audit

目标是识别哪些历史变化会改变当前业务理解。

必须覆盖：
- material M&A、divestiture、spin-off、business exit、segment reshuffle。
- 每个变化进入或退出了哪个业务 bucket。
- 变化是改变了业务实质，还是只是披露呈现变化。
- 哪些历史数据不能直接同比。

历史事件的写法必须是：
```text
[事件 / 日期 / source] -> 改变了什么业务边界 -> 对当前研究有什么影响
```

### Mode C: Disclosure Evolution Audit

目标是把披露口径的断点和可比性讲清楚，不直接替代 `driver-map`。

必须输出：
- segment / KPI rename、recast、definition change、reporting unit change、discontinued ops。
- 每个口径变化的 source / as-of。
- 可比性判断：`comparable` / `partially comparable` / `not comparable` / `unknown`。
- 对后续工作的影响：是否阻塞 driver-map、peer compare、model 或 thesis。

可比性 hard standards：
| Rating | Hard standard |
|---|---|
| `comparable` | 公司明确说明口径未变，或提供可追溯 recast 数据 |
| `partially comparable` | 业务范围大体一致，但定义、segment allocation 或 time period 有局部变化 |
| `not comparable` | M&A、divestiture、discontinued ops、reporting unit change 或 KPI definition 改变核心口径 |
| `unknown` | source 不足，不能判断；必须标 `[来源待补]` 或 `[需查证]` |

如果 disclosure gap 已经影响 revenue / margin / backlog / price-volume-mix driver 判断，停止在 primer 内推断，输出 `driver-map` handoff block。

## 输出结构

### Foundation Primer

```markdown
## Company Primer

**结论先行**
[1-2 句话说明这家公司现在应如何理解，以及最大 source / disclosure gap]

## Business Snapshot

| 维度 | 当前理解 | Source / as-of | Gap |
|---|---|---|---|
| What it sells | [...] | [...] | [...] |
| Who pays | [...] | [...] | [...] |
| Revenue model | [...] | [...] | [...] |
| Core business bucket | [...] | [...] | [...] |

## Segment / Product Reality

| Reported segment / product | Business reality | Customer / end-market | Why it matters | Source / as-of |
|---|---|---|---|---|

## What Actually Changed

- [只写影响当前业务理解的历史变化]

## Disclosure / KPI Watchouts

- [口径断点、rename、recast、source conflict]

## Implications

- 对 `driver-map`： [...]
- 对 `alpha-thesis`： [...]
- 对 `peer-deep-dive`： [...]

## 可以问 AI

1. [...]
2. [...]
```

### Business Evolution Audit

```markdown
## Business Evolution Audit

**结论先行**
[业务演变中最影响当前判断的 1 个变化]

| Date / period | Event | What changed | Current research implication | Source |
|---|---|---|---|---|

## Non-comparable History

- [...]

## Next Handoff

- [...]
```

### Disclosure Evolution Audit

```markdown
## Disclosure Evolution Audit

**结论先行**
[哪些 segment / KPI 不能直接连起来看]

| Period | Reported segment / KPI | Definition / scope | Change vs prior | Comparability | Source |
|---|---|---|---|---|---|

## Source Reconciliation

- [冲突 source、暂用口径、原因]

## Impact on Downstream Work

- `driver-map`: [...]
- `peer-deep-dive`: [...]
- `financial-model`: [...]
```

### Primitive Handoff

```markdown
**先别继续写 primer 结论，我建议先触发 `[skill-name]`。**

阻塞点：
- [...]

为什么会污染后续判断：
- [...]

交给 `[skill-name]` 的问题：
1. [...]
2. [...]

需要补的 source / data：
- [...]
```

## 可选保存

默认只输出到对话。用户明确要求保存时，写入当前 topic session：
```text
topics/[topic-slug]/[YYYY-MM-DD]-[session-slug]/company-primer.md
```

如果当前没有 topic session，先 handoff 到 `new-session` 创建 / 解析路径；不要自行发明大量目录，也不要把 primer 写进 `research-journal.md`，除非已经通过 `research-journal` 的 Earned Insight Gate。

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| primer 发现公司基础事实不清、业务边界不明 | 继续留在 `company-primer` |
| 产品、工艺、设备链条、工程原理或 know-how 不清 | `mechanism-map` |
| revenue / margin / backlog / price-volume-mix driver 不清 | `driver-map` |
| segment / KPI 口径断裂影响 model driver | 先 `driver-map`，再回到 thesis / model |
| source 冲突或关键 claim 未验证 | `information-impact` |
| 需要快速判断是否值得继续研究 | `stock-quickread` |
| 基础已清楚，要形成 long / short 观点 | `alpha-thesis` |
| 多家公司业务边界或 KPI 要横向比较 | `peer-deep-dive` |
| primer 形成已研究清楚的认知增量 | `research-journal` |

## 反模式自查

### 流水账类
- ❌ 出现“成立于 / 总部位于 / 管理层经验丰富”，但没有解释它如何改变当前业务判断。
- ❌ 按时间顺序罗列所有并购、剥离、产品发布，而不是只写 material changes。
- ❌ 把 IR 里的“领先解决方案提供商”改写成中文，没有翻译成谁付钱、买什么、为什么买。
- ❌ 用 5 年收入 CAGR 代替业务演变解释。
- ❌ 写成 sell-side initiation 的公司介绍章节。

### Source 类
- ❌ 产品、客户、segment、KPI、并购、剥离或 recast 没有 source / as-of。
- ❌ 把公司官网当前业务页和历史 10-K 混用，却不标时间点。
- ❌ 多个 source 对 segment 或 KPI 口径冲突时只挑一个顺手的用。
- ❌ 把卖方或新闻对业务的描述当作公司披露事实。
- ❌ 编 URL、页码、交易金额、收购日期或 KPI 定义。

### Logic 类
- ❌ 把 segment rename 当成业务变化，或把业务变化当成单纯 rename。
- ❌ 把 discontinued ops、spin-off、divestiture 前后的数据连成连续趋势。
- ❌ 把 acquired revenue 当成 organic growth。
- ❌ 把 reported segment 名称直接当成 business reality。
- ❌ 把 disclosure gap 当成 driver conclusion，在 primer 里硬拆 model driver。

### Workflow 类
- ❌ 用户要 quick triage，却输出完整 primer。
- ❌ 用户要 driver-map，却先写长篇公司背景。
- ❌ 发现 engineering / know-how gap 但不触发 `mechanism-map`。
- ❌ 发现 source conflict 但不触发 `information-impact`。
- ❌ 把未研究清楚的 primer 草稿直接写进 `research-journal`。

## 篇幅基准

- Foundation Primer：900-1600 字 + 2-3 张表；低于 700 字通常 source / business boundary 不足，超过 1800 字通常开始流水账。
- Business Evolution Audit：600-1200 字 + 1 张事件表；超过 1400 字通常说明把 non-material history 写进来了。
- Disclosure Evolution Audit：700-1400 字 + 1 张口径表；超过 1600 字通常应拆给 `driver-map` 或 `peer-deep-dive`。
- Primitive Handoff：150-350 字；只写阻塞点、污染风险、交给哪个 skill、需要补什么 source / data。

## 与相邻 skill 的边界

- `stock-quickread` 判断一家公司值不值得继续看；本 skill 在决定继续看后，把业务基础和披露历史打牢。
- `driver-map` 把 reported bucket 翻译成 business reality 和 model driver；本 skill 只梳理公司事实、业务边界和披露口径演变，不正式拆 revenue / margin driver。
- `mechanism-map` 解释行业机制、工程原理、设备链条、工艺流程和术语；本 skill 不发明 know-how。
- `alpha-thesis` 写 variant view、catalyst 和 kill criteria；本 skill 只提供公司基础，不写完整 long / short thesis。
- `peer-deep-dive` 做横向比较和排序；本 skill 只说明目标公司自己的业务 / KPI 口径是否可比。
- `research-journal` 沉淀已研究清楚的 insight；本 skill 的普通 primer 不是 earned memory，只有研究结论足够清楚后才 handoff。
