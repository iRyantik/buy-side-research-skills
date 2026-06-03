---
name: peer-deep-dive
description: Compare companies in one industry with sourced KPI matrices and research ranking.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Peer Deep Dive

Compare companies in one industry with sourced KPI matrices and research ranking.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data pipeline**: Call `/financial-data --lite <ticker>` to fetch three-statement financials + market snapshot. Trust its results; pull numbers directly from `actuals-resolved.json`.
- **Data verification**: Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证]). See §3.2.
- **Actuals-only ratio rule**: cross-company comparison ratios (PE, EV/EBITDA, PEG, ROIC, FCF Yield, margins, etc.) use actuals-resolved.json disclosed data only. No forward estimate as ratio input.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.


- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.


### Step 1: Fork N subagents — one evidence card per ticker (parallel)

Each subagent independently completes two tasks:

  a. Fetch financial data
     /financial-data --lite <TICKER>
     → writes _cache/financial-data/internal/actuals-resolved.json

  b. Generate evidence card
     Read actuals + WebSearch key information → output JSON per `references/policy/evidence-card-schema.json`
     Card contains: financial_highlights, business_profile, competitive_position,
                   growth_outlook, valuation_context, long_short_sentiment, scoring,
                   key_claims_needing_verification, evidence_triplets

subagent N:
  /financial-data --lite <TICKER_N>
  + evidence card JSON per evidence-card-schema.json

Main agent continues once all subagents complete. Single ticker failure does not block others —
main agent notes `subagent unavailable for <TICKER> — <reason>` in the final artifact,
removing that ticker from the merged comparison.


## Core Philosophy

The real value of cross-company research is what **vertical (single-company) research cannot do**:
- Extract a shared industry coordinate system across N companies, eliminating redundant work
- Discover where N companies' management commentary contradicts each other (contradiction = alpha starting point)
- See whether the valuation spread and fundamental spread match (mismatch = opportunity or trap)
- Rank: who to research first, how deep, and which pairs are suitable for paired study

If the output merely reads "here is a side-by-side comparison of these companies," you have done no cross-company research — you have only saved typing time.

**The litmus test**: strip out the "Industry Lens" and "Cross-Cut Insight" sections. Does the remainder look like N condensed quickreads? If yes, rewrite.

## Output Structure

> **Source contract**: Every factual claim in this document (numbers, company names, industry judgments, competitive landscape descriptions) must carry a [S#](url) or [I#](url) short-anchor at the end of the sentence. Interpretive sentences ("I think," "my judgment") are not mandatory. Three or more consecutive factual claim sentences without a source in between → insufficient density.

### §0 Task Definition & Preflight

The researcher first clarifies:
- **Company list**: 3–8 companies (if more than 8, pre-screen via free-form dialogue first, or group by sub-industry / business model)
- **Research purpose**: build core position / find hedge / find pair trade / thematic exposure / other
- **Time budget**: used for resource allocation in §7 ranking

Before cross-company comparison, confirm these companies genuinely fit into the same mechanism / driver / KPI coordinate system:

| Check item | Pass standard | Action if not passed |
|---|---|---|
| Mechanism / value-capture comparability | N companies sit on the same mechanism chain, or each company's value-capture point on the chain has been clearly identified | Handoff to `mechanism-insight` first to unify mechanism understanding |
| KPI definition comparability | Core KPI definitions are consistent, or differences can be footnoted / normalized | Handoff to `driver-map` first to decompose KPI / disclosure conventions |
| Driver comparability | Revenue, margin, backlog, price-volume-mix can be mapped to comparable drivers | Handoff to `driver-map` first |
| Peer group reasonableness | Differences in business model, commercialization stage, cyclicality, and policy exposure are not large enough to distort cross-cut analysis | Re-group first |

If any item does not pass, do not force a ranking / matrix. Output a minimal handoff block first.

### §1 Conclusion First (~200–400 words)

**This section is for the PM** — it must be sufficiently complete that the reader can make a directional judgment without needing to flip through later §2–§7.

Must include:
- **One-sentence overall judgment**: the overall directional assessment of this group as a cohort at the current stage
- **Priority ranking (micro-table)**: Company / Direction / One-line rationale
- **At-a-glance positioning**: Insert a Mermaid scatter chart — N companies' positions on the growth vs. valuation (PE TTM) axes
- **2–3 most critical cross-cut findings** (the most important insights pulled forward from §6)
- **First-priority action**

### §2 Industry Lens (~300–400 words)

The shared industry coordinate system across N companies — written once.

Must include:
- **Current regime**: What variable is the market trading in this industry this year?
- **Overall capital-cycle stage**: Is the industry in heavy-investment / sustain / harvest phase at the industry level?
- **Industry-level empirical drivers**: What external variables does the stock price primarily follow?
- **Industry base rate**: What is the historical evolution path from this valuation / cycle position?

Anti-patterns:
- Industry primer / regulatory 101 / historical development (this is an encyclopedia entry, not a lens)
- Listing how many players exist in the industry / top-5 market share (this is data, not insight)

### §3 Industry Structural Variables

When the industry faces a structural paradigm shift, rank each company from most-benefited to most-harmed.

When the industry faces a structural paradigm shift (electrification / CPO / gene therapy, etc.), rank each company from most-benefited to most-harmed.

| Company | Pre-paradigm core business | Post-paradigm position | Transition progress | Net impact |
|---|---|---|---|---|
| AEHR | Wafer burn-in niche market | CPO creates entirely new category | Volume production | Most positive |
| ficonTEC | Coupling turnkey lines | Coupling demand surge | CPO volume validation | Most positive |
| Lieqi | Mid-range die-bonding, high unit volume | Precision insufficient for CPO | No public progress | Negative |

**Net impact labels**: Most positive / Positive / Neutral / Negative

**General rules**:
- The paradigm shift is defined by the researcher or AI — it must be the industry's biggest current structural variable
- Every company must have its transition progress filled in (volume production / sampling / in development / no public progress)
- Net impact must give a direction; do not write "to be observed"

### §4 Cross-Sectional Matrix

#### §4.1 Universal Dimensions (listed for every industry)

| Company | Market | Currency | Mkt Cap (LC) | Mkt Cap (USD) | FX rate / as-of | Accounting standard | Revenue (LTM) | Revenue YoY | **Profit YoY** | **Margin Δ(bp)** | EBITDA margin | ROIC (ex-cash) | Net Debt/EBITDA | Capex/D&A | FCF yield | **PE TTM** | **PE NTM** | **PEG** | PB | EV/EBITDA | EV/Sales | Capital return / FCF | Ev |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MYCR | SE | SEK | 58.3B | 5.8B | 10.5 | IFRS | 7.9B | +12% | -4% | -120bp | 24% | 22% | 0.1x | 0.6x | 2.1% | 35x | 18x | 1.9x | 7.4x | 29x | 7.0x | 60% | [S1](./_cache/sources/mycr-peers-data.md) |
| ficonTEC/300757 | CN | CNY | ~1000B | ~138B | 7.25 | CAS | ~1.5B | +30% | N/A(loss) | N/A | ~15% | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 50x | ~100x | ~100x | N/A | [S2](./_cache/sources/ficontec-peers-data.md) |

**Cross-market rules**: When the same table includes ≥ 2 markets → the 5 columns Market / Currency / Mkt Cap (USD) / FX rate / Accounting standard are mandatory. Single-market tables may omit them.

**Flex-column rules**: If N companies share the same business model → add 2–3 core flex columns from the relevant `references/kpi-drivers/` template (e.g., all equipment companies → Backlog, Orders, Book-to-Bill). Mixed business models → do not add flex columns, to avoid non-comparable conventions.

Each row's Ev column notes the primary data source; fully expanded in `## Resources` at the end of the document.

#### §4.2 Industry-Specific KPIs

**Check industry templates first**: `references/kpi-drivers/`. Route by business model: order-driven / process-industry / long-cycle / utility-infra / tech-manufacturing / saas-software / ai-emerging.

**When no existing template is available, derive in 5 steps**:
1. Locate 4 dimensions: business model (commodity / capital equipment / project / SaaS / platform / pre-commercial) + cyclicality + policy dependency + commercialization stage
2. Answer 5 questions: revenue source / unit economics / capital cycle / risk structure / commercialization progress
3. Add industry-specific KPIs (ask the researcher when uncertain — AI should not pretend to be a domain expert)
4. Refine to 5–10 KPIs
5. Communicate the rationale + request calibration

**Convention consistency**: For every KPI, confirm that definitions are consistent across N companies. EBITDA adjustments, ROIC invested capital calculation, Capex including or excluding acquisitions — differences must be footnoted explicitly below the table. Do not pretend comparability exists.

#### §4.3 Competitive Decomposition

Each company's core business gets its own row, comparing key competitive-strength indicators.

| Company | Core business | Market share (units) | Market share (value) | Competitive indicator | Latest progress | Key customers | Moat | Biggest weakness |
|---|---|---|---|---|---|---|---|---|
| MRSI/Mycronic | High-end die-bonding | 21% | Top 3 | Precision ±1μm | 1.6T LEAP volume production | Undisclosed | Precision tier filters out competitors | CPO validation incomplete |
| ficonTEC | Active alignment | 10-15% | Likely #1 | Precision ±0.3μm | CPO Broadcom exclusive volume production | Broadcom, NVIDIA | Customer lock-in + algorithms | High customer concentration |

**General rules**:
- Competitive indicator: use precision tier for equipment (e.g. 1μm), range / autonomous-driving level for autos, price band / positioning for consumer goods, process node for semiconductors
- When unit share ≠ value share, annotate below the table (e.g., Lieqi 21% by units but only Top 5 by value)
- Key customers: list only publicly confirmable ones; mark undisclosed ones as `[未具名]`
- Moat and weakness must come from verifiable differentiation; do not write generic descriptions

**Comparability note**: For every indicator, confirm consistent conventions across N companies. Common pitfalls: mixing unit-based vs. value-based market share, inconsistent precision definitions (machine precision vs. placement precision), writing a confirmed relationship when the customer name is not publicly disclosed.

#### §4.4 Value Chain Positioning Matrix

When the comparison subjects sit on the same industry chain, compare where each company makes money by chain segment.

**Format**: rows = companies, columns = value chain segments. Cells = exposure label + rank/share + one-line positioning.

**Exposure labels** (plain text, no special symbols):

| Label | Meaning |
|---|---|
| **绝对主业** | The vast majority of the company's revenue and profit comes from this segment |
| **核心** | Important segment, but not the absolute core business |
| **主力** | Has business here with clear contribution, but not a profit engine |
| — | Does not touch this segment |

**Example (optical module equipment chain)**:

| Company | Die-bonding | Coupling | Burn-in | Final test | Wafer test | Turnkey |
|---|---|---|---|---|---|---|
| MRSI | 绝对主业 | 核心 | — | — | — | — |
| ficonTEC | 主力 | 绝对主业 | — | 主力 | — | 核心 |
| Keysight | — | — | 绝对主业 | 绝对主业 | 主力 | — |

**General rules**:
- Column headers = segment names of that industry chain (defined by the researcher or AI per the industry)
- Every cell must contain: exposure label + rank or share in that segment + one-line core competitive strength
- If data for a segment is missing, mark `[缺]`; do not leave blank
- Ranking must distinguish unit / value / capacity basis — cannot mix them

#### §4.5 Technology Roadmap & Generational Progress

When the industry has a clear generational iteration path, compare each company's position at each generation.

**Format**: rows = generational milestones, columns = companies, cells = progress label

| Generation | MRSI | ficonTEC | Besi | Lieqi |
|---|---|---|---|---|
| 800G | Volume production | Volume production | Volume production | Volume production |
| 1.6T | Volume production | Volume production | Volume production | Sampling |
| CPO | In development | Volume production | Volume production | — |

**Progress labels**: Volume production (delivering in volume) / Sampling (under customer validation) / In development (product exists, not yet sampled) / — (no presence in this generation)

**General rules**:
- Generational milestones are defined by the researcher or AI per the industry
- Progress must have a source — annual report / product launch / customer announcement / industry conference
- If a company skips a generation (e.g., from 800G directly to CPO), mark and explain

#### §4.6 Customer-Supplier Relationship Map

When customer concentration is a core investment variable for the comparison subjects, compare each company's depth of binding with key customers.

**Format**: rows = companies, columns = downstream key customers. Cells = degree of binding

| Company | Broadcom | NVIDIA | Zhongji Innolight | Google | Meta |
|---|---|---|---|---|---|
| ficonTEC | Exclusive | 核心 | — | — | — |
| MRSI | — | — | Sampling | — | — |
| Lieqi | — | — | 核心 | — | — |

**Binding-degree labels**:

| Label | Meaning |
|---|---|
| **独家** | This customer uses only this one supplier |
| **核心** | One of the main suppliers; stable relationship |
| **在供** | Supplies but not a primary supplier |
| **送样** | Product under validation at the customer |
| — | No supply relationship or cannot confirm |

**General rules**:
- Customer names must be publicly confirmable (annual report disclosure / product launch / industry conference / customer official website)
- Undisclosed customers: mark `[未具名]`; do not fabricate
- Investment implication: more concentrated customers = higher single-customer risk; deeper binding = higher switching costs = deeper moat

> When N ≤ 5, consider using a single large overview table in place of the separate tables in §4.3–§4.6. Keep Markdown to 12 columns or fewer; for the full 20-column version, output an HTML table using research-viz.

### §5 Per-Company Differential (~150 words per company)

**This is not a mini stock-quickread** — write only what differentiates the company from peers. Use only the following format per company:

#### [Company Name]

| ![logo](current topic `_cache/images/<ticker>-logo.png`) |
|---|

**One-line positioning** (where the company sits among peers, 10–15 words)

**Key differentials** (2–3 items, each must have a number + Source)
- e.g.: EBITDA margin 32% vs. peer average 24%, driven by cost advantage in Block X

**Directional judgment**: Long / Short / Neutral / Not interested + one-line rationale

> Competitive indicators, key customers, moat, etc. are already in the §4.3 table — do not repeat here. Include a logo per company (download to _cache/images/<ticker>-logo.png); mark `[缺 logo]` if not found.
>
> **Logo download**: Read `_scripts/download-product-image.js`, set `{{SELECTOR}}` to the logo selector (e.g., `.logo img`), call the current session's Playwright MCP `browser_run_code_unsafe`; the rest of the flow is the same as product-image download.

### §6 Cross-Cut Insight

**If this section is done poorly, the entire exercise has failed.** If cross-cut genuinely finds nothing, you must explicitly state "No X / Y / Z found" and explain why; do not pretend there is content.

#### §6.1 Management Signal Cross-Reference

**Contradictory signals**: Where do N companies' management commentaries contradict each other? This is the richest soil for alpha — because one side must be wrong.

Format:
> **[Contradiction point]**: Company X [specific quote] [S#]; Company Y said the opposite in the same period [opposing quote] [S#].
> **Context**: The two companies' end-market overlap is X% / both are upstream Permian / both serve a specific sub-application
> **Interpretation**: Possible explanations (one side sandbagging? regional differences? timing mismatch?) + which side's position is more credible + how to verify

If there are zero contradictory signals, explicitly state: "No obvious contradictions found — N companies maintain high consistency on [core narrative]."

**Consensus signals**: What are all N companies emphasizing? Use this to calibrate the industry lens understanding and identify which company has not yet acknowledged the consensus.

#### §6.2 Valuation Spread vs. Fundamental Spread

Revisit the §4 matrix: do valuation spread and fundamental spread match?

Format:
> **[Mismatch point]**: X PE 28x TTM, Y PE 18x TTM — X growth 25% / Y growth 22%
> **Growth-adjusted view**: PEG X=1.1x vs. Y=0.8x — on the surface X looks expensive, but growth-adjusted Y is more expensive
> **Expected spread**: growth differential ~14%, normal PE spread should be ~20–30%
> **Actual spread**: PE gap 55% (X is 55% more expensive than Y)
> **Interpretation**: The market may be assigning an excessive CPO premium to X, or Y has unpriced risk. EV/EBITDA (X 35x vs. Y 22x) points to the same gap

Provide at least 2–3 of the most conspicuous spread mismatches.

#### §6.3 The Story of Extremes

Who is the max / min on each dimension in the §4 matrix? Extremes are research starting points, not conclusions.

Format:
> **[Dimension] extreme**: max is X (specific number + Source), min is Y (specific number + Source)
> **Driver**: X is this high because of [fundamental reason + whether sustainable]
> **Judgment**: Is it an opportunity (market hasn't recognized) or a trap (fundamentals genuinely poor, valuation already reasonable)

Pick 3–5 of the most informative extremes; do not recite the max/min of every dimension.

### §7 Research Ranking & Next Steps

| Company | Priority | Recommended research depth | Time allocation | Ranking rationale |
|---|---|---|---|---|
| X | 1 | Full suite: stock-quickread → alpha-thesis | 2 days | Highest information density / earnings approaching |
| Y | 2 | Streamlined: stock-quickread | 1 day | Hedge candidate |
| ... | ... | ... | ... | ... |

Ranking dimensions: information density (more cross-cut hits = higher priority), time sensitivity, existing coverage depth, valuation setup

**Next steps**:
- Which company to look at first (specific name + why)?
- Pair / cluster suggestions — which companies are suitable to continue tracking together?
- When does the peer-deep-dive need to be redone (e.g., after concentrated earnings season, industry data milestones, policy events)?
- If industry mechanism / engineering principles / terminology are unclear, handoff to `mechanism-insight` first

> Mermaid scatter chart example — replace with real data when the agent outputs:

```mermaid
quadrantChart
    title Peer Positioning: Growth vs Value
    x-axis Slow Growth --> Fast Growth
    y-axis Expensive --> Cheap
    Company A: [0.72, 0.35]
    Company B: [0.55, 0.62]
```

## Length Benchmarks

- 3–5 companies: ~3,000 words / 6–8 companies: ~5,000 words / >8 companies: group by sub-industry / business model first
- Exceeding the upper bound typically means falling into the "N quickreads stitched together" trap — go back and delete content that restates what is already in the §5 differential

## Artifact / Save Strategy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

If the path is unclear → agent auto-creates per policy baseline §11.

## Anti-Pattern Checklist

**General**
- Stripping out the "Industry Lens" and "Cross-Cut" sections leaves N condensed quickreads → failure, rewrite
- Any section contains "founded in / headquartered in / experienced management team" → delete
- Conclusions buried in the second half of the document → §1 Conclusion First is missing or reads like a "table of contents preview"

**§2 (Industry Lens)**
- Describing how many players exist in the industry / market-share structure (not a lens, it's data)
- Generic filler like "benefiting from X"
- Doesn't state what variable the current regime is trading

**§4 (Matrix)**
- Tables missing the Ev column or no `## Resources` at the end of the document → add them

**§5 (Differential)**
- Restating business model / revenue composition (that's quickread's job)
- "Experienced management / stable team" (not a differential)
- Directional judgment says "to be observed" — must give a direction

**§6 (Cross-Cut)**
- Forced insights when none are found — must say "No X found" and explain why
- Valuation comparison only says "relatively expensive / cheap" without reverse-engineering


## Appendix: actuals-resolved.json

Full field inventory → `references/actuals-data-catalog.md`.

Structure: `meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`.

Consumption rules: read actuals first → source_map for [S#]/[I#] labels (do not write [actuals]) → ratios use actuals actual values only (no forward estimates).


## Appendix: Financial Data

Generate appendix from actuals-resolved.json:

```
python _scripts/financial-data/actuals-to-appendix.py --tickers <TICKER_1>,<TICKER_2>,<TICKER_3>,...
```

### Evidence Cards

Main agent selects 1-3 evidence_triplets from each evidence card and embeds them in the artifact:

claim: <key factual claim from evidence card>
evidence: <supporting data>
source: [S#](url) or [I#](url)

At least 1 triplet (3 lines) required to satisfy the subagent_protocol hook.
