---
name: reddit-sentiment
description: Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.
---

# Reddit Sentiment

Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in workspace `.references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

把 Reddit 从噪音池变成可用的买方研究线索：抓取相关帖子，标注 narrative clusters，识别社区分层、拥挤叙事、误导性 social claims、下一步验证任务，并给出 10-15 个最值得读的帖子。

如果输出把 Reddit 当成事实源、只写"散户很 bullish / bearish"、没有样本覆盖和 caveat、没有 Recommended Reading，或没有把 social claims 交给 filings / market data / primary source 验证，本 skill 就失败了。

## 心法

Reddit sentiment 不是为了证明公司基本面，而是为了回答：市场边缘人群在相信什么、哪些叙事正在传播、哪些误解可能影响价格、哪些帖子值得研究员亲自读。它是 `consensus-map` / `earnings-setup` / `alpha-thesis` 的输入，不是替代。

最有价值的输出不是情绪分数，而是三件事：第一，社区之间的分歧；第二，bull / bear 各自需要后续 source 验证的命题；第三，Recommended Reading，让研究员可以快速进入原始讨论语境。

## 环境与工具

如果你只是在找 workspace 级共享环境入口，先看 `init-workspace` 提供的 `.scripts/init-assets/env-setup.ps1.template`。`reddit-sentiment` 继续保留自己的 bootstrap，因为它是额外可选依赖型 skill，不与 `financial-data` / `ingest` 合并。

本 skill 包含 runtime 工具：

```text
skills/reddit-sentiment/
  scripts/reddit_label.py
  scripts/bootstrap.py
  assets/requirements-reddit-sentiment.txt
  assets/default-clusters.json
```

首次运行前先检查依赖：

```powershell
skills/reddit-sentiment/scripts/bootstrap.py -CheckOnly
```

如缺 `scrapi-reddit`，用户明确同意安装后再运行：

```powershell
skills/reddit-sentiment/scripts/bootstrap.py -Yes
```

macOS / Linux：

```bash
skills/reddit-sentiment/scripts/bootstrap.py --check-only
skills/reddit-sentiment/scripts/bootstrap.py --yes
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
| `topic_path` | 是 | 若不明确，agent 按 policy baseline §11 自动解析 |
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
scrapi_dir = industry/<industry>/companies/<ticker>/_raw/datasets/reddit-sentiment/[run_id]/scrapi
raw_dir = industry/<industry>/companies/<ticker>/_raw/datasets/reddit-sentiment/[run_id]
cache_dir = industry/<industry>/companies/<ticker>/.cache/datasets/reddit-sentiment/[run_id]
report_path = industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-reddit-sentiment.md
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

.cache/datasets/reddit-sentiment/[run_id]/
  evidence-cards.md
  coverage-summary.md
  manifest.json
```

### Phase 3: LLM 总结

读取 `coverage-summary.md`、`evidence-cards.md`、`cluster-counts.json`、`manifest.json`。不要只读终端摘要。报告里的样本数、cluster 百分比、core post 数、subreddit 分布必须来自这些文件。

## 输出结构

```markdown
## Verdict

[2-4 句结论先行：Reddit 情绪是什么、最大分歧是什么、这对研究下一步意味着什么。样本数 / 时间窗 / 最大 cluster 必须挂 `[C1](./.cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md)`。]

## 1. Coverage & Caveats

| Item | Setting / Result | Ev |
|---|---|---|
| Time window | [from-to] | [C1](./.cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) |
| Collection route | search + subreddit scan | [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) |
| Core posts / usable comments | [n posts / n comments] | [C1](./.cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) |
| Biggest limitation | [coverage caveat] | [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) |

**Takeaway**: Reddit 是 clue-only social source；下文只说明叙事和情绪，不把评论当公司事实。

## 2. Community Segments

| Segment | Subreddits | Sample / signal | Bias caveat | Ev |
|---|---|---|---|---|
| Trader / meme | r/wallstreetbets 等 | [核心情绪] | 夸大短期价格和 options | [R001](https://www.reddit.com/r/wallstreetbets/comments/example) [C2](./.cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) |
| Fundamental / value | r/investing 等 | [核心情绪] | 样本少、偏谨慎 | [R002](https://www.reddit.com/r/investing/comments/example) [C2](./.cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) |

## 3. Narrative Clusters

| Cluster | Share / count | Where it shows up | Research meaning | Ev |
|---|---:|---|---|---|
| valuation_skepticism | [x comments / y%] | [subreddits] | [对 buy-side bar 的含义] | [C3](./_raw/datasets/reddit-sentiment/[run_id]/cluster-counts.json) [R014](https://www.reddit.com/r/stocks/comments/example) |

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

[说明 false positives、tiny posts、deleted/removed comments、低质量板块，必须挂 `[C1](./.cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md)`。]

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
| 1 | [R014](https://www.reddit.com/r/stocks/comments/example) | r/stocks | [一句话：最大讨论 / 最扎实分析 / 最尖锐 bear / 最典型 FOMO] | [R014](https://www.reddit.com/r/stocks/comments/example) |

## Resources

- [C1](./.cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) = local cache | coverage summary | run [run_id]
- [C2](./.cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) = local cache | evidence cards | run [run_id]
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

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

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
