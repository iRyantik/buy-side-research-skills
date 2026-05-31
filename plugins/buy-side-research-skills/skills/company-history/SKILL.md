---
name: company-history
description: Audit business evolution and disclosure comparability through M&A timelines, segment recasts, and KPI definition changes.
---

# Company History

Audit business evolution and disclosure comparability through M&A timelines, segment recasts, and KPI definition changes.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for business evolution tracing and disclosure comparability audits; unresolved facts stay as gap, hypothesis, or follow-up.

把一家公司的业务基础和披露演变讲清楚，让后续 `driver-map`、`stock-quickread`、`alpha-thesis`、`peer-deep-dive` 和 `3-statement-model / dcf-model / comps-analysis / model-update` 不建立在错的公司理解上。核心价值不是写“公司介绍”，而是识别这家公司到底卖什么、谁付钱、业务边界如何变化、披露口径哪里断裂，以及哪些历史变化会污染后续 driver 或 thesis 判断。

如果输出变成成立年份、总部、管理层履历、按时间顺序罗列收购新闻、IR 话术复述或通用业务百科，本 skill 就失败了。历史只在它改变业务实质、segment 可比性、KPI 连续性、客户/产品边界或后续研究优先级时才写。

## 心法

`company-history` 处理的是披露链条上最容易出错的一环：业务怎么变成今天这样，以及数字能不能直接比。

很多投研错误是因为把 recast 后的 segment 当成连续历史、把并购带来的结构变化当成 organic trend、把 renamed KPI 当成同一口径。本 skill 的任务是把这些断点讲清楚：什么时候变的、变了什么、对后续 driver-map / model / peer compare 有什么影响。

本 skill 不写公司介绍、不拆 model driver、不画产品价值链。它是 `driver-map` 和 `peer-deep-dive` 的口径上游——在 driver mapping 之前先确保数据能连着看。## 触发场景

### Mode A 触发（Business Evolution Audit）

- "这家公司过去几年怎么变成现在这样"
- "哪些并购 / 剥离改变了业务结构"
- "这家公司业务边界变过吗"
- "现在的业务和几年前是不是一回事"
- "这家公司哪块业务是核心，哪块是遗留 / 噪音"

### Mode B 触发（Disclosure Evolution Audit）

- "segment 口径是不是变过"
- "这个 KPI 前后可比吗"
- "为什么披露口径断了"
- "这家公司 rename / recast 后怎么对齐"
- "把 segment / KPI 历史口径梳理一下"

## 输入澄清要求

| 维度 | 含义 | 默认处理 |
|---|---|---|
| **对象** | ticker / 公司名 / 子公司 / segment / KPI | 默认按公司；用户可指定具体 segment 或 KPI |
| **研究目的** | 搞清业务演变 / 对齐披露口径 / 判断可比性 / feed driver-map | 默认服务后续 driver-map 和 peer compare |
| **时间范围** | 过去 3-5 年 / 上市以来 / 某次交易前后 / 某次 recast 前后 | 默认覆盖所有 material 变化 + 影响可比性的披露事件 |
| **披露范围** | segment / KPI / geography / customer / product | 默认 segment + KPI + material M&A / divestiture |
| **source 状态** | 用户给 source / 需要自行找 source / source 冲突 | 每个口径变化必须标 source + as-of；不足时标 `[来源待补]` |
| **保存需求** | 写入 topic 日期文件 | 默认保存到当前 topic |

如果用户只给 ticker，默认先做 Business Evolution Audit（过去 3-5 年 material 变化），再按需进入 Disclosure Evolution Audit。如果用户明确只要披露口径对齐，直接进 Mode B。

## Mode A: Business Evolution Audit

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

## Mode B: Disclosure Evolution Audit

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

### Business Evolution Audit

```markdown
## Business Evolution Audit

**结论先行**
[业务演变中最影响当前判断的 1 个变化]

| Date / period | Event | What changed | Current research implication | Ev |
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

| Period | Reported segment / KPI | Definition / scope | Change vs prior | Comparability | Ev |
|---|---|---|---|---|---|

## Source Reconciliation

- [冲突 source、暂用口径、原因]

## Impact on Downstream Work

- `driver-map`: [...]
- `peer-deep-dive`: [...]
- `3-statement-model / dcf-model / comps-analysis / model-update`: [...]
```

## Artifact / 保存策略

写入当前日期化保存路径：
```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-company-history.md
```

本 skill 的 `artifact_policy.naming_mode = required_qualifier`。

如果当前没有 dated result path，先 handoff 到 `new-session` 创建 / 解析路径。


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
- ❌ 把 sub-agent evidence card 直接粘成 company primer 结论，而没有主 agent 抽查 URL、统一时间口径和处理 source conflict。

### Logic 类
- ❌ 把 segment rename 当成业务变化，或把业务变化当成单纯 rename。
- ❌ 把 discontinued ops、spin-off、divestiture 前后的数据连成连续趋势。
- ❌ 把 acquired revenue 当成 organic growth。
- ❌ 把 reported segment 名称直接当成 business reality。

## 篇幅基准

- Mode A (Business Evolution)：600-1200 字 + 1 张事件表；超过 1400 字说明把 non-material history 写进来了。
- Mode B (Disclosure Evolution)：700-1400 字 + 1 张口径表；超过 1600 字通常应拆给 `driver-map`。
