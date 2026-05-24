---
name: reddit-sentiment
description: Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.
---

# Reddit Sentiment

Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.

## Research Runtime Capsule

本 skill 独立运行时也必须遵守以下 runtime 规则；详细维护基线在 `skills/_shared/research-policy-baseline.md`，但运行时不能假设会自动读取该文件，因此本 skill 自身必须携带可执行的规则摘要。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 非中文 / 英文公司披露项按最小必要原则保留源语言锚点：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 表格优先用 `Ev` / `证据` 短列承载 inline clickable short source anchor 和例外状态。默认 `[S1](link)`；例外状态追加 `:REV` / `:GAP` / `:ND` / `:EST` / `:CON`，干净值不写 `OK`；完整 source metadata 不在表后展开，每篇 artifact 文末统一写 `## Resources`，用 `- [S1](link) = source type | source title/provider | as-of/filed | page/location | fallback reason` 保持可追溯。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- Source locality rule: use source quality first (`workspace-local > primary public > reputable provider/news > internet market source`), then prefer `home-market / local-language source` within the same quality tier. News / event evidence should prefer local-language sources for the issuer, main listing venue, regulator, or operating country; market data should prefer the primary listing / trading-market source. Do not maintain market-specific provider whitelists in skill rules; if using a global, English, or non-home-market fallback, state the fallback reason in the final `## Resources` list.
- Sub-Agent Evidence Protocol：本 skill 默认单线执行。只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时，才开启 sub-agent / delegate worker 并行查 source；sub-agent 只能返回 evidence card，不得写最终结论、sentiment verdict、routing、thesis、valuation 或 model treatment；主 agent 必须完成 source conflict handling 和最终 synthesis。若用户明确要求并行而当前 host / runner 真的无法 spawn，必须在 artifact 中明示 `sub-agent unavailable`、原因和 coverage caveat。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 研究启动时先检查 `topics/<topic-slug>/_cache/` 是否存在已 ingest 的材料；如有，优先引用 cache 中的 source-tracked markdown。

# Reddit Sentiment

把 Reddit 从噪音池变成可用的买方研究线索：抓取相关帖子，标注 narrative clusters，识别社区分层、拥挤叙事、误导性 social claims、下一步验证任务，并给出 10-15 个最值得读的帖子。

如果输出把 Reddit 当成事实源、只写"散户很 bullish / bearish"、没有样本覆盖和 caveat、没有 Recommended Reading，或没有把 social claims 交给 filings / market data / primary source 验证，本 skill 就失败了。

## 心法

Reddit sentiment 不是为了证明公司基本面，而是为了回答：市场边缘人群在相信什么、哪些叙事正在传播、哪些误解可能影响价格、哪些帖子值得研究员亲自读。它是 `consensus-map` / `earnings-setup` / `alpha-thesis` 的输入，不是替代。

最有价值的输出不是情绪分数，而是三件事：第一，社区之间的分歧；第二，bull / bear 各自需要后续 source 验证的命题；第三，Recommended Reading，让研究员可以快速进入原始讨论语境。

## Source 政策

- Claim-Level Source Contract：正文里的每个 truth-like claim（样本数、core posts 数、usable comments、cluster 占比、某 subreddit 的情绪、某帖子代表什么叙事）都必须紧跟 inline clickable short anchor，如 `[C1](./_cache/.../coverage-summary.md)` / `[R014](https://www.reddit.com/...)`。
- Reddit 是 `reddit social source / clue only`。它可以证明"Reddit 上有人这么说"或"某社区里这个叙事出现"，不能证明公司事实、财务事实、S-1 内容、客户关系或管理层真实意图。
- 原文引用要短，只保留足以识别叙事的片段；长段评论不要整段搬运。若措辞本身不重要，用中文概述并挂 Reddit post anchor。
- `## Resources` 里必须展开每个高信号帖子：`- [R014](link) = reddit social source | r/subreddit | title | collected/as-of [date] | caveat: clue only`。
- 结构化数据和本地 evidence pack 用 `[C1](path)` / `[C2](path)`：coverage summary、evidence cards、cluster-counts、manifest 都要能点到。
- No Orphan Truth Claim：输出前检查样本规模、cluster 百分比、community segment、Recommended Reading 理由、social claims to verify 是否都有 anchor；没有就补 anchor、降级为 `[来源待补]`，或删除。

## 环境与工具

本 skill 包含 runtime 工具：

```text
skills/reddit-sentiment/
  scripts/reddit_label.py
  scripts/bootstrap-reddit-sentiment-deps.ps1
  scripts/bootstrap-reddit-sentiment-deps.sh
  assets/requirements-reddit-sentiment.txt
  assets/default-clusters.json
```

首次运行前先检查依赖：

```powershell
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1 -CheckOnly
```

如缺 `scrapi-reddit`，用户明确同意安装后再运行：

```powershell
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1 -Yes
```

macOS / Linux：

```bash
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh --check-only
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh --yes
```

不要静默安装依赖。缺依赖时先报告缺口和需要运行的 bootstrap 命令。

## 触发场景

使用本 skill 当用户问：

- "查 XXX 在 Reddit 上的情绪"
- "Reddit 怎么看这个 IPO / 财报 / 新闻"
- "reddit sentiment for [ticker / company / theme]"
- "帮我找 Reddit 上最值得读的帖子"
- "散户社区现在在争什么"
- "这个消息在 WSB / stocks / investing 上怎么传播"

不要用于：

- 核实一条业务事实或供应链 claim：用 `information-impact`。
- 系统拆 sell-side consensus / buy-side bar：用 `consensus-map`。
- 写投资 thesis：先用本 skill 取 sentiment clues，再交给 `alpha-thesis`。
- 生成假访谈或把 Reddit 评论当 primary research：这违反 source policy。

## 输入澄清要求

运行前必须尽量确认：

| 输入 | 必填 | 默认 |
|---|---|---|
| `subject` | 是 | 用户给出的公司 / ticker / 事件 / 主题 |
| `topic_path` | 是 | 若不明确，先用 `new-session` 解析 |
| `keywords` | 是 | subject + ticker + event words |
| `subreddits` | 建议 | `stocks,investing,wallstreetbets,SecurityAnalysis,ValueInvesting`，再加主题社区 |
| `from_date` / `to_date` | 是 | 最近 7 天 |
| `question` | 是 | 用户的研究问题 |
| `topic_terms` | 建议 | subject、ticker、产品名、事件词；用于过滤 false positive |

如果用户只给一句"查 Reddit 情绪"，不要硬跑。先给出建议 keywords / subreddits / 时间窗，并说明默认会用最近 7 天。

## 执行流程

### Phase 0: 路径和 run id

设定：

```text
run_id = YYYY-MM-DDTHH-MM-SSZ
scrapi_dir = topics/[namespace]/[topic]/_raw/datasets/reddit-sentiment/[run_id]/scrapi
raw_dir = topics/[namespace]/[topic]/_raw/datasets/reddit-sentiment/[run_id]
cache_dir = topics/[namespace]/[topic]/_cache/datasets/reddit-sentiment/[run_id]
report_path = topics/[namespace]/[topic]/[YYYY-MM-DD]-reddit-sentiment.md
```

### Phase 1: ScrapiReddit 采集

Search mode：

```powershell
scrapi-reddit --search "kw1" --search "kw2" --output-format json --output-dir "<scrapi_dir>"
```

Subreddit mode：

```powershell
scrapi-reddit stocks investing wallstreetbets --subreddit-sorts new --time-filter week --output-format json --output-dir "<scrapi_dir>"
```

可以分多次写同一个 `scrapi_dir`，但最终 `reddit_label.py` 只读取该目录下所有 `posts.json`。

### Phase 2: 标注和 cache 输出

```powershell
python skills/reddit-sentiment/scripts/reddit_label.py --scrapi-dir "<scrapi_dir>" --labels skills/reddit-sentiment/assets/default-clusters.json --topic "<topic_path>" --subject "<subject>" --topic-terms "term1,term2,ticker,event" --from YYYY-MM-DD --to YYYY-MM-DD --run-id "<run_id>"
```

输出：

```text
_raw/datasets/reddit-sentiment/[run_id]/
  post-universe.jsonl
  posts-core.jsonl
  comments-clean.jsonl
  cluster-counts.json
  manifest.json
  comments-cache/

_cache/datasets/reddit-sentiment/[run_id]/
  evidence-cards.md
  coverage-summary.md
  manifest.json
```

### Phase 3: LLM 总结

读取 `coverage-summary.md`、`evidence-cards.md`、`cluster-counts.json`、`manifest.json`。不要只读终端摘要。报告里的样本数、cluster 百分比、core post 数、subreddit 分布必须来自这些文件。

## 输出结构

```markdown
## Verdict

[2-4 句结论先行：Reddit 情绪是什么、最大分歧是什么、这对研究下一步意味着什么。样本数 / 时间窗 / 最大 cluster 必须挂 `[C1](link)`。]

## 1. Coverage & Caveats

| Item | Setting / Result | Ev |
|---|---|---|
| Time window | [from-to] | [C1](link) |
| Collection route | search + subreddit scan | [C4](link) |
| Core posts / usable comments | [n posts / n comments] | [C1](link) |
| Biggest limitation | [coverage caveat] | [C4](link) |

**Takeaway**: Reddit 是 clue-only social source；下文只说明叙事和情绪，不把评论当公司事实。

## 2. Community Segments

| Segment | Subreddits | Sample / signal | Bias caveat | Ev |
|---|---|---|---|---|
| Trader / meme | r/wallstreetbets 等 | [核心情绪] | 夸大短期价格和 options | [R001](link) [C2](link) |
| Fundamental / value | r/investing 等 | [核心情绪] | 样本少、偏谨慎 | [R002](link) [C2](link) |

## 3. Narrative Clusters

| Cluster | Share / count | Where it shows up | Research meaning | Ev |
|---|---:|---|---|---|
| valuation_skepticism | [x comments / y%] | [subreddits] | [对 buy-side bar 的含义] | [C3](link) [R014](link) |

## 4. Bull/Bear Burden Of Proof

| Side | What Reddit needs to believe | What would verify / falsify | Next source |
|---|---|---|---|
| Bull | [social claim] | [filing / KPI / market data] | `consensus-map` / `financial-data` |
| Bear | [social claim] | [filing / KPI / market data] | `information-impact` / `driver-map` |

## 5. Social Claims To Verify

| Claim from Reddit | Why it matters | Verification route | Status |
|---|---|---|---|
| [claim stated as Reddit claim, not fact] | [research relevance] | [filing / IR / market data] | `[来源待补]` until verified |

## 6. Excluded Material

[说明 false positives、tiny posts、deleted/removed comments、低质量板块，必须挂 `[C1](link)`。]

## 7. Phase 1 Routing

| Finding | Next step |
|---|---|
| Reddit narrative conflicts with market consensus | `consensus-map` |
| A repeated Reddit claim needs fact-checking | `information-impact` |
| A driver / KPI is repeatedly debated | `driver-map` |
| Sentiment changes print setup | `earnings-setup` |

## 8. Recommended Reading

如果只读 10-15 个帖子，优先读这些：

| # | Post | Subreddit | Why read | Ev |
|---:|---|---|---|---|
| 1 | [R014](link) | r/stocks | [一句话：最大讨论 / 最扎实分析 / 最尖锐 bear / 最典型 FOMO] | [R014](link) |

## Resources

- [C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) = local cache | coverage summary | run [run_id]
- [C2](./_cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) = local cache | evidence cards | run [run_id]
- [C3](./_raw/datasets/reddit-sentiment/[run_id]/cluster-counts.json) = local cache | cluster counts | run [run_id]
- [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) = local cache | manifest and source caveats | run [run_id]
- [R014](https://www.reddit.com/...) = reddit social source | r/[subreddit] | [title] | collected [date] | caveat: clue only
```

## Recommended Reading 规则

- 默认选 10-15 个 core posts；如果 core posts 少于 10 个，全部列出并说明 coverage thin。
- 排序优先级：讨论规模、代表性、cluster 覆盖、社区差异、是否能揭示 bull/bear burden of proof。
- 每个条目必须回答"为什么值得读"，不要只贴标题。
- 每个 ID 必须直接点击到 Reddit permalink。
- 不要把 Recommended Reading 变成 source dump；它是研究员阅读路线。

## Artifact / 保存策略

本 skill 属于 `default_topic_result`。因为运行会产生 dated raw/cache evidence pack，默认保存最终报告：

```text
topics/[topic-namespace]/[topic-slug]/[YYYY-MM-DD]-reddit-sentiment.md
```

本 skill 的 `artifact_policy.naming_mode = required_qualifier`。默认应由 `new-session` 解析成 `YYYY-MM-DD-<artifact>-<qualifier>.md`，用事件、话题或叙事锚点区分不同 sentiment 报告，而不是只靠同日后缀。

如果同日同 topic 已存在，保留历史并追加最低可用序号，例如 `2026-05-22-reddit-sentiment-2.md`。

## Workflow 联动

| 发现 | 下一步 |
|---|---|
| Reddit claim 可能是事实错误或供应链传闻 | `information-impact` |
| Reddit 叙事和 market expectations 可能错位 | `consensus-map` |
| 财报前 Reddit 关注点影响 print setup | `earnings-setup` |
| 反复争论某个 KPI / driver | `driver-map` |
| 情绪揭示 thesis 起点 | `alpha-thesis` |
| 需要压测 popular bull case | `bear-pre-mortem` |
| 形成可复用认知增量 | `research-journal` |

## 反模式自查

写完后必须自检：

- Reddit 评论被写成公司事实，而不是 "Reddit 上的叙事 / claim"。
- 没有样本数、时间窗、core posts、usable comments。
- 没有 `Coverage & Caveats`。
- 没有 `Recommended Reading`。
- Recommended Reading 没有 Reddit permalink。
- 表格无 `Ev` / `证据` 或正文 claim 无 clickable short anchor。
- 文末不是 `## Resources`，或在表后展开完整 source metadata。
- cluster 百分比没有来自 `cluster-counts.json` / `coverage-summary.md`。
- 把 low-quality / false-positive posts 当核心证据。
- 没有列出 excluded material。
- 没有把 social claims 交给后续 verification route。
- 使用了论坛/社媒作为 company-disclosed fact 的 source。

## 篇幅基准

- 标准报告：1200-1800 字，必须包含所有 8 个主体 section + `## Resources`。
- Tight mode：600-900 字，只能在用户明确要求快速判断时使用，但仍必须保留 coverage、top clusters、Recommended Reading 和 Resources。
- 超过 2200 字通常说明在复述帖子，应压缩为 cluster / community / verification route。

## 与相邻 skill 的边界

| Skill | 边界 |
|---|---|
| `information-impact` | 核实单条 claim 是否可信；本 skill 只发现 Reddit claim 和传播范围。 |
| `consensus-map` | 拆 market expectations / buy-side bar；本 skill 只提供 social sentiment clue。 |
| `earnings-setup` | 准备财报前后 setup；本 skill 可输入 Reddit 关注点。 |
| `stock-quickread` | 快速看公司基本面；本 skill 不写公司业务 overview。 |
| `research-journal` | 沉淀 earned insight；本 skill 的 social clues 只有验证后才进入 journal。 |
