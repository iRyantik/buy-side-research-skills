---
name: reddit-sentiment
description: Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Reddit Sentiment

Collect label and summarize Reddit sentiment as clue-only social evidence for a research topic.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

Turn Reddit from a noise pool into usable buy-side research clues: scrape relevant posts, label narrative clusters, identify community segmentation, crowded narratives, misleading social claims, and next-step verification tasks, and produce a list of 10–15 posts most worth reading.

This skill fails if the output treats Reddit as a factual source, writes only "retail is bullish / bearish", lacks sample coverage and caveats, omits Recommended Reading, or fails to route social claims to filings / market data / primary sources for verification.

## Core Philosophy

Reddit sentiment is not meant to prove company fundamentals — it answers: what do market fringe participants believe, which narratives are circulating, which misconceptions may impact price, and which posts are worth the researcher reading firsthand. It is input to `consensus-map` / `earnings-setup` / `alpha-thesis`, not a substitute.

The most valuable output is not a sentiment score but three things: first, divergence between communities; second, the bull / bear propositions that each require subsequent source verification; third, the Recommended Reading that lets the researcher quickly enter the original discussion context.

## Environment & Tooling

`reddit-sentiment` retains its own bootstrap because it is an optional-dependency skill and is not merged with `financial-data` or the Source Intake runtime.

This skill includes runtime tools:

```text
skills/reddit-sentiment/
  scripts/reddit_label.py
  scripts/bootstrap-reddit-sentiment-deps.ps1
  scripts/bootstrap-reddit-sentiment-deps.sh
  assets/requirements-reddit-sentiment.txt
  assets/default-clusters.json
```

Check dependencies before first run:

```powershell
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1 -CheckOnly
```

If `scrapi-reddit` is missing, obtain explicit user consent before installing:

```powershell
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.ps1 -Yes
```

macOS / Linux:

```bash
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh --check-only
skills/reddit-sentiment/scripts/bootstrap-reddit-sentiment-deps.sh --yes
```

Do not install dependencies silently. When dependencies are missing, first report the gap and the bootstrap command that needs to be run.

## Trigger Scenarios

Use this skill when the user asks:

- "Check Reddit sentiment on XXX"
- "What does Reddit think of this IPO / earnings / news"
- "reddit sentiment for [ticker / company / theme]"
- "Help me find the posts most worth reading on Reddit"
- "What are retail communities arguing about right now"
- "How is this news spreading on WSB / stocks / investing"

Do not use for:

- Verifying a business fact or supply-chain claim: use `information-impact`.
- Systematically breaking down sell-side consensus / buy-side bar: use `consensus-map`.
- Writing an investment thesis: use this skill first for sentiment clues, then hand off to `alpha-thesis`.
- Fabricating mock interviews or treating Reddit comments as primary research: this violates source policy.

## Input Clarification Requirements

Must confirm as much as possible before running:

| Input | Required | Default |
|---|---|---|
| `subject` | Yes | Company / ticker / event / theme provided by user |
| `topic_path` | Yes | If unclear, agent auto-resolves per policy baseline §11 |
| `keywords` | Yes | subject + ticker + event words |
| `subreddits` | Recommended | `stocks,investing,wallstreetbets,SecurityAnalysis,ValueInvesting`, plus topic-specific communities |
| `from_date` / `to_date` | Yes | Last 7 days |
| `question` | Yes | The user's research question |
| `topic_terms` | Recommended | subject, ticker, product names, event words; used to filter false positives |

If the user only says "check Reddit sentiment" with no further detail, do not force a run. First suggest keywords / subreddits / time window, and explain that the default will use the last 7 days.

## Execution Flow

### Phase 0: Paths and Run ID

Set:

```text
run_id = YYYY-MM-DDTHH-MM-SSZ
scrapi_dir = industry/<industry>/companies/<ticker>/_raw/datasets/reddit-sentiment/[run_id]/scrapi
raw_dir = industry/<industry>/companies/<ticker>/_raw/datasets/reddit-sentiment/[run_id]
cache_dir = industry/<industry>/companies/<ticker>/_cache/datasets/reddit-sentiment/[run_id]
report_path = industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-reddit-sentiment.md
```

### Phase 1: ScrapiReddit Collection

Search mode:

```powershell
scrapi-reddit --search "kw1" --search "kw2" --output-format json --output-dir "<scrapi_dir>"
```

Subreddit mode:

```powershell
scrapi-reddit stocks investing wallstreetbets --subreddit-sorts new --time-filter week --output-format json --output-dir "<scrapi_dir>"
```

Multiple runs can write to the same `scrapi_dir`, but `reddit_label.py` ultimately reads all `posts.json` files under that directory.

### Phase 2: Labeling and Cache Output

```powershell
python skills/reddit-sentiment/scripts/reddit_label.py --scrapi-dir "<scrapi_dir>" --labels skills/reddit-sentiment/assets/default-clusters.json --topic "<topic_path>" --subject "<subject>" --topic-terms "term1,term2,ticker,event" --from YYYY-MM-DD --to YYYY-MM-DD --run-id "<run_id>"
```

Output:

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

### Phase 3: LLM Summary

Read `coverage-summary.md`, `evidence-cards.md`, `cluster-counts.json`, and `manifest.json`. Do not rely solely on the terminal summary. Sample counts, cluster percentages, core post counts, and subreddit distributions in the report must come from these files.

## Output Structure

```markdown
## Verdict

[2–4 sentences, conclusion-first: what the Reddit sentiment is, what the biggest divergence is, what this means for the next research step. Sample count / time window / largest cluster must link `[C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md)`.]

## 1. Coverage & Caveats

| Item | Setting / Result | Ev |
|---|---|---|
| Time window | [from-to] | [C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) |
| Collection route | search + subreddit scan | [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) |
| Core posts / usable comments | [n posts / n comments] | [C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) |
| Biggest limitation | [coverage caveat] | [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) |

**Takeaway**: Reddit is a clue-only social source; the following sections describe narratives and sentiment only, and do not treat comments as company facts.

## 2. Community Segments

| Segment | Subreddits | Sample / signal | Bias caveat | Ev |
|---|---|---|---|---|
| Trader / meme | r/wallstreetbets etc. | [core sentiment] | Amplifies short-term price moves and options | [R001](https://www.reddit.com/r/wallstreetbets/comments/example) [C2](./_cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) |
| Fundamental / value | r/investing etc. | [core sentiment] | Small sample, cautious bias | [R002](https://www.reddit.com/r/investing/comments/example) [C2](./_cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) |

## 3. Narrative Clusters

| Cluster | Share / count | Where it shows up | Research meaning | Ev |
|---|---:|---|---|---|
| valuation_skepticism | [x comments / y%] | [subreddits] | [implication for buy-side bar] | [C3](./_raw/datasets/reddit-sentiment/[run_id]/cluster-counts.json) [R014](https://www.reddit.com/r/stocks/comments/example) |

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

[Describe false positives, tiny posts, deleted/removed comments, low-quality subreddits; must link `[C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md)`.]

## 7. Phase 1 Routing

| Finding | Next step |
|---|---|
| Reddit narrative conflicts with market consensus | `consensus-map` |
| A repeated Reddit claim needs fact-checking | `information-impact` |
| A driver / KPI is repeatedly debated | `driver-map` |
| Sentiment changes print setup | `earnings-setup` |

## 8. Recommended Reading

If you only read 10–15 posts, prioritize these:

| # | Post | Subreddit | Why read | Ev |
|---:|---|---|---|---|
| 1 | [R014](https://www.reddit.com/r/stocks/comments/example) | r/stocks | [One-liner: largest discussion / most rigorous analysis / sharpest bear / most typical FOMO] | [R014](https://www.reddit.com/r/stocks/comments/example) |

## Resources

- [C1](./_cache/datasets/reddit-sentiment/[run_id]/coverage-summary.md) = local cache | coverage summary | run [run_id]
- [C2](./_cache/datasets/reddit-sentiment/[run_id]/evidence-cards.md) = local cache | evidence cards | run [run_id]
- [C3](./_raw/datasets/reddit-sentiment/[run_id]/cluster-counts.json) = local cache | cluster counts | run [run_id]
- [C4](./_raw/datasets/reddit-sentiment/[run_id]/manifest.json) = local cache | manifest and source caveats | run [run_id]
- [R014](https://www.reddit.com/...) = reddit social source | r/[subreddit] | [title] | collected [date] | caveat: clue only
```

## Recommended Reading Rules

- Default selection: 10–15 core posts; if fewer than 10 core posts exist, list all and note thin coverage.
- Sort priority: discussion scale, representativeness, cluster coverage, community divergence, whether it reveals bull/bear burden of proof.
- Every entry must answer "why it's worth reading"; do not just paste the title.
- Every ID must link directly to a Reddit permalink.
- Do not turn Recommended Reading into a source dump; it is a researcher's reading roadmap.

## Artifact / Save Policy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

Path unknown → agent auto-creates per policy baseline §11.

## Anti-Pattern Self-Check

After writing, must self-inspect:

- Reddit comments are presented as company facts rather than "narrative / claim on Reddit".
- Missing sample count, time window, core posts, usable comments.
- Missing `Coverage & Caveats`.
- Missing `Recommended Reading`.
- Recommended Reading has no Reddit permalink.
- Tables lack `Ev` column or prose claims lack clickable short anchors.
- Footer is not `## Resources`, or full source metadata is expanded after tables.
- Cluster percentages do not come from `cluster-counts.json` / `coverage-summary.md`.
- Low-quality / false-positive posts are used as core evidence.
- Excluded material is not listed.
- Social claims are not routed to subsequent verification routes.
- Forum / social media is used as the source for a company-disclosed fact.

## Length Benchmarks

- Standard report: 1,200–1,800 words, must include all 8 body sections + `## Resources`.
- Tight mode: 600–900 words, only when the user explicitly requests a quick judgment, but must still retain coverage, top clusters, Recommended Reading, and Resources.
- Exceeding 2,200 words usually means regurgitating posts; compress into cluster / community / verification route.
