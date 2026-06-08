---
name: stock-quickread
description: Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.
---

# Stock Quickread

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Material Collection & Source Verification

### Discipline

**Do not use WebSearch AI summary numbers to directly write claims.** Summaries may be right, they may be wrong. Every external fact claim must come from the source page.

### Source Priority (mandatory)

```
1. actuals-resolved.json    Local cache, machine-harvested, zero latency, highest confidence
   → Read corresponding [S#](url) labels from `source_map` field. Do not write bare [actuals] in artifacts.

2. [S#] Company disclosure   IR PDF, annual report, AGM presentation, earnings transcript
   → Fields not in actuals: order details, management quotes, product roadmap, capacity plans
   → WebFetch verify the original text → mark [S1-S9]

3. [I#] Third-party           Industry reports, news media (Bits&Chips, etc.), Yahoo Finance, sell-side reports
   → Where actuals and company disclosure both fall short: market share, TAM, competitive landscape, sell-side target, consensus
   → WebFetch/Playwright verify the original text → mark [I1-I20]

Cite only the single highest-priority source for the same claim.
Example: Revenue → already in actuals → do not mark [S1]. Q1 orders → not in actuals → [S1]. TSMC >60% share → company does not disclose → [I1].
```

### Two-Layer Data Pipeline

| Layer | Source | Use |
|---|---|---|
| 0-Actuals | `actuals-resolved.json` — local cache, verified | §3 financial tables, §4 ratios, Market Cap/PE. **No network call** |
| 1-External | Company IR, annual report PDF, industry reports, sell-side reports, news | §1 business breakdown, §5 capacity/pricing/industry change/narrative, §6 consensus, §7 long/short debate, §9 events |

### Page Fetch Fallback Chain

WebFetch frequently fails (403/503/JS-rendered empty return). **Must degrade by priority — never give up after one attempt:**

```
Tier 1  WebFetch(url)                        — static pages, fastest
   ↓ fail
Tier 2  Playwright MCP browser_navigate + browser_snapshot  — JS rendering, auth walls
   ↓ fail
Tier 3  bash: curl -sL url | python extract body    — raw HTML, last resort
   ↓ fail
Tier 4  Mark [UNVERIFIED] + record attempted URLs in Resources  — honest degradation
```

**Every external claim must be attempted at least through Tier 2.** Only mark [UNVERIFIED] after Tier 1+2 both fail.

### Platform Compatibility

| Tool | Claude Code | Codex |
|---|---|---|
| WebFetch | `WebFetch` tool | Not built-in — skip Tier 1 |
| Playwright MCP | `mcp__playwright__browser_*` | Requires MCP server install |
| curl fallback | `Bash` tool | `run_shell_command` |
| Final degradation | `[UNVERIFIED]` | `[UNVERIFIED]` |

> Codex path: WebSearch → Playwright MCP browser_navigate → curl → [UNVERIFIED]. Claude Code path: WebSearch → WebFetch → Playwright MCP → curl → [UNVERIFIED].

### Execution Flow (Gate-style — each step has intermediate output, next step checks previous)

```
┌─ Step 1: /financial-data <ticker>
│  → Pull 3-statement core items + segments + elastic supplementary + market_data
│  → Write to _cache/financial-data/internal/actuals-resolved.json
│  Gate: ls actuals-resolved.json → STOP if missing. Do not proceed.
│
├─ Step 2: python _scripts/evidence_ledger.py init <artifact> -t <TICKER>
│  → _cache/evidence/<TICKER>.evidence.json (must exist)
│
├─ Step 3: Discovery — WebSearch for candidate URLs
│  Gate: ≥2 candidate URLs per must-verify claim
│
├─ Step 4: Verification — verify claim-by-claim per Fallback chain
│  Tier 0: actuals-resolved.json → direct fetch, ledger method=actuals
│  Tier 1: WebFetch(url) → success? → ledger method=WebFetch, attempt logged
│  Tier 2: Playwright browser_navigate → success? → ledger method=Playwright, attempt logged
│  Tier 3: curl → success? → ledger method=curl, attempt logged
│  Tier 4: [UNVERIFIED] → only if ALL tiers failed, attempt logged as failed
│  Gate: Each [I#]'s attempts[] array has ≥1 Tier 1-2 entry
│
├─ Step 5: Image download (HARD GATE — each sub-step must execute, cannot skip)
│  5a. python _scripts/shared/download-image.py <url> --output <product>  (auto Tier 1→2, cache check)
│  5b. All tiers fail → mark [IMAGE MISSING] — only after ledger records download attempt
│  Gate: ls _cache/images/<product>.* has file → pass. No file AND no attempt record → STOP, cannot enter Step 6.
│
├─ Step 6: Write artifact
│  Every claim sentence suffix [S#](URL) / [I#](URL)
│  Verified sources carry no badge — only mark [UNVERIFIED] (unverified claims)
│  Tables strictly follow template (§3c=table, §4a=pool, §5=anchor table+scenario table+Ev column)
│  Pre-write checklist: _cache/images/<product>.* file exists ✅ | [IMAGE MISSING] has attempt record ✅ | [UNVERIFIED] ≤8 ✅
│
├─ Step 7: python _scripts/evidence_ledger.py auto <artifact> -t <TICKER>
│  → Auto-create ledger pending claims → agent fills text/quote/section → verify
│
├─ Step 8: python _scripts/evidence_ledger.py lint + status
│  → anchors aligned ✅ + 0 fabrication_risk + coverage >80%
│
└─ Step 9: python _scripts/financial-data/actuals-to-appendix.py <TICKER>
   → Generate appendix: financial data statement in artifact
```

### Source Numbering Rules

- `[S1]`–`[S9]`: company disclosure (IR PDF, annual report, AGM presentation)
- `[I1]`–`[I20]`: third-party sources (industry reports, news, sell-side, Yahoo Finance)
- URL only needs page-level granularity — no #anchor fragment required
- Same URL cited multiple times → reuse the same number

### Source Marking Convention

- Verified source: `[S#](url)` or `[I#](url)` — no badge appended. `[S#]/[I#]` = verified by default.
- Unverified claim: mark `[UNVERIFIED]` — only after all fallback tiers have failed.
- actuals Tier 0: read corresponding [S#] labels from `source_map`. Do not write bare `[actuals]`.
- Marking position: sentence suffix in body, or Ev column in tables. Verification status detail tracked in evidence ledger, not displayed in artifact.

### Anti-Patterns

- ❌ Construct URLs from memory (`tsmc.com/SoIC`) — must be WebFetch-verified
- ❌ One WebSearch summary mapped to 3 claims with different URLs — AI summary numbers cannot serve as sources
- ❌ URL returns 404 but remains in Resources — delete it, replace with one that opens
- ❌ Numbers that actuals-resolved.json already provides also fetched via WebSearch — read locally, zero latency

## Philosophy

The buy-side reads companies not to "understand the company," but to: (1) judge whether this is a name worth more time; (2) find the specific questions to ask at the next layer. So the quickread's output must drive straight to decision-useful information.

If your output reads like a sell-side initiation report, it has failed. Sell-side report markers: business segments expanded by chapter, management bios, 5-year historical financial table, chronological listing of all recent events. **Delete all of these.**

## Output Structure (follow strictly)



> **Appendix execution**: Run actuals-to-appendix.py BEFORE writing the artifact body. Embed output in ## Appendix above. Never leave a placeholder.

Every section has a length ceiling. It can be shorter. **Must never exceed.** Excessive length is itself a symptom of boilerplate.

**Pipeline Report** (mandatory at artifact opening — execution report, cannot be omitted):

```
> 2026-06-03 | <TICKER> | <PRICE> | MCap <VALUE>
> Pipeline: actuals ✅ | [UNVERIFIED] X | images ✅ | lint ✅ | coverage XX%
```

### 1. At a Glance

#### Business Overview

First, a table — a single scan shows the company's business segments and which ones are hot. **Focus at the lowest disclosure level** — if sub-segment product lines have completely different customers/value chains (e.g., Mycronic's GT division), break down to the product-line level and mark [DERIVED]; if the segment itself is pure (e.g., ASMPT's SEMI), stay at segment level.

| Business | Segment | What It Does (Plain English) | Revenue Share | Derivation Basis | Market Attitude |
|---|---|---|---|---|---|
| A | PG | <one sentence> | 51% | Company disclosure [S#](url) | Stable |
| B | GT | <one sentence> | ~8% | Order mix + IR verbal guidance [DERIVED] [S#](url) | 🔥 Focus |
| C | GT | <one sentence> | ~6% | Same as above [DERIVED] [S#](url) | 🔥 Focus |

> Prefer the lowest disclosed revenue level. Use company numbers for segments; estimated product-line figures must be marked [DERIVED] and **must state the derivation basis and source** (order mix, IR commentary, industry reports, etc.) — never just write "estimated." From this table: <one-sentence summary — which business is earning, which is growing, which is dragging>.

#### 🔥 What the Market Cares About Right Now

The following 2–3 product lines are core to the current investment thesis. No more than 3 — beyond that they're not "focal."

##### Focus 1: <Product Line> (Segment <Name>, Revenue <Share>)

**Why It Matters** (1–2 sentences — why this is the single largest investment narrative. Every factual claim suffixed with `[S#](url)` or `[I#](url)`; technology roadmap / customer name / market share / capacity / orders must have sources)

Example: `TSMC SoIC uses hybrid bonding for 3D stacking [S1](url). BESI D2W bonder is the only production-validated system globally [S2](url). 20 logic customers + all three major memory vendors in evaluation [S3](url).`

**What It Looks Like** (1–2 focus product images)

| ![Product](_cache/images/<slug>-<product>.png) |
|---|
| *Product Name — Function (≤15 words)* |

**Where It Sits** (focus segment value chain)

```mermaid
flowchart LR
    A[Upstream] --> B[**<Product Line>**<br/><what it does>] --> C[Downstream: <who pays>]
```

**How It Makes Money**
> One-time equipment / equipment + consumables / subscription / maintenance. Factual claims (pricing, capacity, customer count, etc.) must carry sources.

##### Focus 2: <Product Line>

(Same structure — why it matters / what it looks like / where it sits / how it makes money. Focus segments must include images — mark [IMAGE MISSING] if unavailable; do not skip.)

> Images only for focus segments. Other segments do not get images. ① Company website Media Kit → ② web search product image → ③ industry representative image if unavailable → ④ mark [IMAGE MISSING] as last resort. Download to `_cache/images/<slug>-<product>.png`.

#### Other Businesses

- **A**: <one sentence — what this business does and why it's not the current focus>
- **B**: <one sentence>

#### Plain English

> In short, it's <the simplest analogy>.

### 2. Terms to Know First

| Term | Plain English |
|---|---|
| <term> | <one sentence> |

> Max 5–8 terms. Not a glossary — how you'd explain it in conversation.

### 3. Where the Money Comes From (data table + takeaway)

> Numbers sourced from: `industry/<industry>/companies/<ticker>/_cache/financial-data/internal/actuals-resolved.json`

**Qualitative descriptions alone are partial understanding** — readers can't tell which segment matters, which is shrinking, where anomalies are. So this section has two parts:

**(a) Business Model Assessment**: agent judges business model → routes to `references/kpi-drivers/<template>.md` → determines elastic KPI checklist + 2–3 elastic ratios.

**(b) Key Financial Tables (standard + elastic)**

Break down by segment (for single-segment companies, substitute product line / geography / customer type). Minimum columns as shown. Each segment gets **latest full-year (or latest LTM)** plus **latest Q/H period** data — two rows (including YoY). Periods written as separate rows; period labels must read from actuals-resolved.json's real labels / basis — do not write HK H1 as Q2 or Q4.

| Segment | Period | Revenue | Rev Share | Rev YoY | Profit | Profit Method | Profit Share | Margin | Margin YoY | Ev |
|---|---|---|---|---|---|---|---|---|---|---|
| Segment A | FY2024 | 1,200 | 45% | +12% | 336 | EBIT | 65% | 28% | +2pp | [S1](./_cache/sources/...) |
| Segment B | FY2024 | 933 | 35% | +3% | 131 | EBIT | 25% | 14% | +1pp | [S10](./_cache/sources/...) |
| Segment C | FY2024 | 533 | 20% | -8% | [ND] — company does not disclose segment profit | — | — | — | — | [S10](./_cache/sources/...) |
| **Total** | **FY2024** | **2,667** | **100%** | **+5%** | 517 | EBIT | **100%** | **19%** | +2pp | [S11](./_cache/sources/...) |
| Segment A | H1 FY2025 | 620 | 43% | +8% | 161 | EBIT | 62% | 26% | -2pp | [S9](./_cache/sources/...) |
| Segment B | H1 FY2025 | 518 | 36% | +2% | 67 | EBIT | 24% | 13% | -1pp | [S9](./_cache/sources/...) |
| Segment C | H1 FY2025 | 302 | 21% | -6% | [ND] | — | — | — | — | [S9](./_cache/sources/...) |
| **Total** | **H1 FY2025** | **1,440** | **100%** | **+4%** | 259 | EBIT | **100%** | **18%** | -1pp | [S12](./_cache/sources/...) |

Body claim example: `FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./_cache/sources/...)`

**Disclosure Caveats**:

1. **Uniform method**: Use the same method for segment and consolidated (prefer segment EBIT > Gross Profit > Net Income). Mark [ND] if segment lacks a method. Report periods FY first, then Q/H. Two rows per segment.
2. **Derivation first**: Compute where possible (residual segment = Total - others; profit = revenue × margin). Mark [DERIVED] and show the logic. Don't rush to [ND].
3. **Honesty in gaps**: Only [ND] when computation is impossible. Don't fabricate numbers. Flag methodology changes, restatements, or non-disclosure — don't fake continuity.

**(c) Elastic KPI Detail** (only when expandable elastic KPIs exist — e.g., Backlog by segment / Orders trend. Skip if absent.)

**(d) Takeaway (2–3 sentences)**

Tables are not the endpoint — they must have interpretation. Cover:
- **Structural fact**: Is there a revenue structure vs. profit structure mismatch? Which segment is the real "profit engine"?
- **Directional fact**: Which segment is gaining importance, which is shrinking? Where are margin expansion / contraction concentrated?
- **Economic driver vs. GAAP segment mismatch**: e.g., "An auto company gets 70% of revenue from vehicles but 60% of profit from its finance subsidiary" — this insight must be in the takeaway; the table alone is insufficient.
- **Seasonality / inflection signals**: Do quarterly data and full-year trends diverge directionally? e.g., a segment with full-year margin expansion but recent-quarter contraction — this could be an early reversal signal; must be flagged in the takeaway.

> Counterexample (boilerplate): "The company has three segments: A, B, and C. A mainly does X, revenue share 45%, B mainly does Y..."
> Correct example: "On paper this is an A+B+C three-segment company, but A contributes 65% of profit with expanding margins while B/C suffer volume+price contraction. From a buy-side perspective, this is essentially a pure-play on A with B/C as noise."

### 4. Growth Drivers & KPIs

> Agent judges business model → routes to `references/kpi-drivers/<template>.md` → determines elastic ratios + Driver table columns.

**(a) Standard Ratios** (4 items, all companies required, data from actuals):

| # | Ratio | Formula | Purpose |
|---|---|---|---|
| 1 | FCF Yield | FCF ÷ Market Cap | True dividend capacity |
| 2 | Net Cash | Cash - Total Debt | Cushion — bankruptcy risk |
| 3 | Debt / Equity | Total Debt ÷ Equity | Leverage — will debt crush it? |
| 4 | Capex / Rev | CapEx ÷ Revenue | Investment intensity |

**(b) Elastic Ratios** (2–3 selected from kpi-drivers template):

| Business Model | Elastic Ratios |
|---|---|
| order-driven | Backlog / Q Rev, Orders YoY, R&D / Rev |
| process-industry | Production YoY, Utilization % |
| long-cycle | Backlog / Annual Rev |
| utility-infra | Utilization %, Capacity YoY |
| tech-manufacturing | R&D / Rev, Backlog YoY |
| saas-software | NRR, Magic Number |
| ai-emerging | Cash / Monthly Burn |

**(c) Elastic Driver Table** (same segment × period structure as §3):

From the kpi-drivers template, select **all KPIs that have data in actuals** as columns — the agent does not re-search; only reads actuals-resolved.json supplementary/segments fields. List everything with values; mark [NOT DISCLOSED] for missing. Example (order-driven):

| Segment | Period | Backlog | Backlog YoY | Orders | B2B | Coverage | Ev |
|---|---|---|---|---|---|---|---|
| PG | FY2025 | SEK 2,100m | +5% | 890m | 0.8x | 2.4mo | [S1](./_cache/sources/...) |
| PG | Q1 2026 | SEK 1,200m | -30% | 597m | 0.7x | 1.8mo | [S1](./_cache/sources/...) |

Unavailable fields: mark [ND] or [NOT DISCLOSED]. All numbers computed from actuals/IR.

> Generalized fallback is handled at the `/financial-data` elastic collection layer (`supplementary.custom_metrics`). §4 reads from actuals directly — no secondary search.

**Industry Cycle Position** (1 sentence): Capacity expansion / competition intensification / consolidation / decline? Is the company leading expansion, following, or contracting counter-cyclically?

### 5. What Drives the Stock

> Data anchor: actuals-resolved.json market_data + income_statement; price history: same file cache

A first-time reader should finish this section understanding **what this stock moves with** — not having memorized three variables named X, Y, Z.

#### How This Business Works (3–5 sentences)

Plain-language business logic — what determines whether it makes or loses money. Not repeating §1's analogy; this is about causation. No industry knowledge required to understand.

> Example: "ASMPT's business is fundamentally a cycle play — chipmakers buy its machines during capex expansion, stop during contraction. Each machine lasts 5–8 years. Revenue peak-to-trough swing: 40–50%. But because only 2–3 players globally can make high-end die bonders, gross margins hit 40%+ in good times and hold ~30% in bad."

#### What's Happening in the Industry Now (2–3 sentences)

The current position in the industry cycle — and **what this means for this company specifically**. Not generic industry primer.

> Example: "2025-2026 semiconductor back-end equipment is in an AI-driven structural expansion — not a traditional semiconductor cyclical recovery. Key difference: advanced packaging capex follows NVIDIA/AMD's AI chip iterations, not the smartphone cycle. AI chip generation-over-generation → packaging equipment demand refreshes → order cycle compressed from 3-4 years to 1.5-2 years."

#### What It Actually Moves With (2–3 variables)

One sub-section per variable. Not dropping keywords — derived from the business logic and industry change above.

##### Variable Name (one sentence — how this variable drives the stock)

**Data Anchor** (from financial-data)

| Metric | Current | Historical Range | Source |
|---|---|---|---|
| <related metric> | <value> | <min — max> | [S#](...) |

**What Story the Market Is Telling** (1–2 sentences — what longs think, what shorts think)

**How It Moved Last Time** (1 sentence — how the stock reacted when this variable changed) [S#](...)

**When It Might Not Work** (1 sentence — which quarter in history this variable and the stock diverged)

**How Sentiment Is Shifting** (1 sentence — recent subtle changes in analyst/market attitude)

**My Take** (1 sentence)

**If This Variable Moves**

| Scenario | This Variable | Stock | Probability | vs. History | Ev |
|---|---|---|---|---|---|
| Bull | <assumption> | +XX% | ~X% | > mean 1σ | [S#](...) |
| Base | — | — | ~X% | mean | — |
| Bear | <assumption> | -XX% | ~X% | < mean 1σ | [S#](...) |

#### Putting It Together (2–3 sentences)

If both variables move in the same direction → potential XX%. If they offset → market may enter a vacuum period — drifts with the index. The biggest crack in the whole story (1 sentence — point to the most fragile assumption).

### 6. What the Market Is Pricing In (consensus + reverse engineering)

> Valuation multiples: actuals-resolved.json market_data; Consensus: same file consensus field (best-effort)

Writing "PE 25x vs. historical 18x, looks expensive" is sell-side level. Buy-side needs to answer: **given the current valuation, what assumptions is the market embedding** — then judge "I agree / disagree with this assumption." That's the starting point of alpha.

**(a) Consensus Key Numbers**

NTM revenue, EBITDA, EPS, key KPI sell-side consensus estimates. Revision direction over the last 3–6 months (upgrades / downgrades / frequency).

**(b) Valuation Multiple Comparison**

| Multiple | Current | 5Y Median | Peer Current | Interpretation | Ev |
|---|---|---|---|---|---|
| EV/EBITDA | 8.5x | 6.2x | 7.1x | +37% vs. self, +20% vs. peers | [S1](url) |
| P/E | 18x | 14x | 16x | ... | [I1](url) |
| FCF yield | 5% | 7% | 6% | ... | [I2](url) |

Body claim example: `The stock trades at 8.5x EV/EBITDA versus its 5-year median of 6.2x and peers at 7.1x. [I1](url)`

Multiple selection must be consistent with §4's capital cycle stage assessment — don't say "harvesting phase" in §4 then use EV/Sales in §6.

**(c) Reverse Engineering: What Does the Current Valuation Imply (this is mandatory, most critical)**

Answer all four:
- **Implied growth rate**: Given the current PE, a reasonable ROE / payout, reverse-engineer the market-implied long-term growth rate. Has the company achieved this before?
- **Implied margin**: Given the current EV/Sales, reverse-engineer the market's long-term margin assumption. vs. historical average / vs. best-in-class peer?
- **Reverse DCF**: Given the current stock price, a reasonable WACC, reverse-engineer the required 5-year FCF CAGR.
- **Bear-implied**: What would it take for the stock to fall to X (historical low / peer low)? How likely is this scenario?

**Example output**:
> "Current EV/EBITDA 8.5x embeds ~12% 5-year EBITDA CAGR. The company's actual 5-year trailing CAGR is 7%; the best peer achieves 10%. To believe the current price, you need to believe [specific assumption X occurs]. This is the current long/short divide."

If §6 lacks reverse engineering, the researcher can only conclude "expensive / cheap" — they cannot locate **which assumption the mispricing sits on**. And alpha typically hides in a specific embedded assumption.

### 7. What Longs and Shorts Are Arguing About

**Not** a generic SWOT. It's "what longs and shorts are actually debating right now" — specific to a data point, an assumption, an event. If unknown, at minimum surface "questions that need to be checked."

### 8. What the Counterparty Needs to Believe

Quickly articulate the core assumption the other side must hold:
- If leaning long: what must shorts / sideliners believe to keep suppressing valuation?
- If leaning short: what must current longs believe to keep paying this price?
- Which assumption is most fragile — most likely to be falsified by the next data point or peer commentary?

This section is not a full thesis — just exposing the variant-view starting point for a later `alpha-thesis`.

### 9. What's Happening Recently

> Stock price: actuals-resolved.json market_data (yfinance cache); Events: web search

**Price**: From <date> <price> → current <price>, <change>. Same period benchmark/sector <change>. [I#](url)

**Events** (each with source):
- <date> <event> → stock <moved X%> [S#](...)
- <date> <event> → stock <moved X%> [S#](...)

> List 3–5 key recent events. Every event must have a source anchor — no "reportedly" or "according to sources."

### 10. 5 Questions for the Next Layer

Not vague questions like "Is management quality good?" Be specific — something a single data point, an event, or a document can answer.
- Counterexample: "How sustainable is the business?"
- Correct: "Has Permian legacy well decline rate accelerated from X% in 2023 to Y%? Which dataset can verify (company Q filing / Enverus / Rystad)?"

If the quickread uncovers complex revenue structure, strange segment buckets, or unclear model drivers, don't fully unpack them here. Explicitly recommend `driver-map` to separately break down `Reported Bucket → Business Reality → Model Driver`.

## Artifact / Save Policy

Write to industry topic:
```
industry/<industry>/companies/<ticker>/YYYY-MM-DD-stock-quickread-<company>.md
```

- Path unclear → agent auto-creates per policy baseline §11.
- Company qualifier extracted from company slug (e.g., `mycronic`, `robotchnik`).

## Word Count Baseline

- Standard quickread: 1,800–2,500 words. Below 1,800 indicates insufficient §5 driver expansion — the most informative section. Above 2,500 indicates doing `company-history` or `driver-map` work; split or deduplicate.


