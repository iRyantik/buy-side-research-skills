---
name: capital-allocation
description: Score management capital allocation — buyback timing, dividend, M&A ROI, capex efficiency with 10Y record and anchored scoring.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Capital Allocation

Score management's capital allocation quality over a 10-year window. The biggest wealth creation or destruction doesn't happen in operations — it happens in the CFO's office.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data Pipeline**: Call `/financial-data --lite <ticker> --periods 10Y` to fetch 10Y CF data (buyback/dividend/capex/M&A).
- **Data Verification**: Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证]). See §3.2.
- **Actuals-only**: ROIC, FCF conversion, buyback yield, and all capital allocation ratios use actuals-resolved.json historical data only.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## Core Philosophy

The most important decision management makes is not strategy — it is how to spend money. In the same industry, on the same track, good vs. bad capital allocation can cause a 3-5x gap in long-term shareholder returns. Judging capital allocation is not about "how much was spent" — it is about "how much each dollar earns back." Buyback at low share prices is value-accretive; at high prices it is value destruction. An M&A deal that jumps 5% on announcement means nothing — the question is whether the acquired business becomes an independent growth engine or a write-off 3-5 years later.

There are only four core questions: How do they spend surplus cash? Did they pay the right price? What are the returns after spending? Is that behavior strengthening or depleting the moat?

## Trigger Scenarios

- "How well does xxx management spend money"
- "Analyze xxx's capital allocation"
- "Is xxx's buyback creating or destroying value"
- "xxx's M&A track record"

## Four-Dimensional Scoring

### 1. Buyback

| Score | Standard | How to assess |
|---|---|---|
| 9-10 | Consistently buys back at lows, not at highs; buyback yield > dividend yield | Overlay 10Y buyback volume and share price — buyback concentrated in trough periods = positive |
| 7-8 | Stable buyback but average timing | |
| 5-6 | Buyback uncorrelated with share price — like an auto-pilot program | |
| 3-4 | Heavy buyback at highs, no buyback at lows | |
| 1-2 | Buyback used to offset SBC dilution, not to return capital | If shares outstanding unchanged — buyback fully consumed by SBC = negative |

### 2. Dividend

| Score | Standard |
|---|---|
| 9-10 | Payout ratio 30-40% sustained for 10Y, never cut |
| 7-8 | Payout <30% but growing steadily |
| 5-6 | Payout volatile, swings with profit |
| 3-4 | Dividend > FCF — borrowing to pay dividends |
| 1-2 | Never paid dividends, and surplus cash wasted |

### 3. M&A ROI

This is the hardest dimension — do not look only at announcement return; look at real ROI 3-5 years after the deal.

| Score | Standard | How to assess |
|---|---|---|
| 9-10 | Has a transformative deal that contributed 30%+ of revenue 3-5Y later with independent moat | Mycronic buying MRSI: $125M → GT division now ~SEK 2B+ annual revenue |
| 7-8 | Multiple small tuck-ins, well-integrated, no significant write-offs | |
| 5-6 | Active M&A but returns unclear | |
| 3-4 | Has large write-offs or goodwill impairment | |
| 1-2 | Empire building — buying for scale, overpaying, culture clash | |

**Key data**: For every deal >5% of market cap, check the revenue/profit contribution of that business 3 years later. If disclosure is insufficient, mark [披露不足].

### 4. Capex Efficiency

| Score | Standard |
|---|---|
| 9-10 | ROIC >20% sustained for 5Y+, capex/revenue stable and generating organic growth |
| 7-8 | ROIC 15-20% |
| 5-6 | ROIC 10-15% |
| 3-4 | ROIC <10% |
| 1-2 | CapEx > operating CF — burning cash with no revenue acceleration |

## Relationship to Moat

This is the key bridge the agent must answer: **Is this management strengthening or weakening the moat?**

- Good moat + good capital allocation = compounder (MYCR style: precision barrier + smart M&A)
- Good moat + poor capital allocation = value trap (high ROIC but surplus cash wasted)
- Poor moat + good capital allocation = cannot save it (a good CFO cannot change the industry fundamentals)
- Poor moat + poor capital allocation = do not research

## Output Structure

> **Source contract**: Scorecard ratings, ROIC/FCF/conversion figures, buyback yield, etc. — every row must carry a source anchor.
>
> **Density table**:
>
> | Section | Mandatory source | Exemption |
> |---|---|---|
> | Scorecard table | Scoring-basis figures in the 10Y Evidence column on every row | The score itself |
> | Capital allocation history | Amount + date for every M&A/repo/dividend | Qualitative description |
> | ROIC/FCF trend | ROIC/FCF/conversion value for each year | Trend direction interpretation |
>
> **Completion Gate**: After writing, scan the scorecard → every row's Anchor column has [S#]/[I#] or `[待查]` → `[待查]` ≤3.

~~~markdown
## Capital Allocation Scorecard

| Dimension | Score | 10Y Evidence | Anchor |
|---|---|---|---|
| Buyback | 7 | Buyback at lows in 2020/2023, no buyback at highs in 2025; buyback yield avg 2% | Shares outstanding -8% in 10Y; SBC dilution ~1%/yr → net -7% |
| Dividend | 8 | 10Y consecutive growth, payout ratio 30-40% | Never cut; yield 1.5-2% |
| M&A ROI | 9 | MRSI $125M → GT division now 30%+ revenue | 3-5Y post-deal ROI estimate: 15x+ |
| Capex | 6 | ROIC 15-18%, capex/revenue 8-10% | Cycle-dependent; high capex years ROI dips to 12% |
| **Total** | **7.5** | — | — |

## Visual

**10Y Capital Flow** (ASCII bar or research-viz):
Buyback:   $800M
Dividend:  $600M
M&A:       $500M  (incl. MRSI $125M)
Capex:     $1.2B
─────────────────
Total deployed: $3.1B
~~~

Market cap created: $4.5B (10Y ago $1.5B → today $6B)
ROI on deployed capital: ~145%

## Moat Bridge

- MRSI acquisition → die-bonding + coupling suite → moat deepened (tech barrier 8→9, customer lock-in 6→7)
- Stable dividend → did not weaken moat (no R&D underinvestment due to cash shortage)

## Anti-Patterns

- ❌ Only looking at the last two years of buyback — timing needs a 10Y perspective
- ❌ Ignoring SBC dilution — buyback consumed by SBC is equivalent to no buyback at all
- ❌ Judging M&A by announcement return instead of 3-5Y ROI
- ❌ Not scoring, not anchoring
- ❌ Skipping the moat bridge — capital allocation disconnected from moat analysis
- ❌ Not comparing alternative uses of surplus cash (e.g. could R&D investment have been higher without buyback)
- ❌ Not flagging dividend > FCF in red (borrowing to pay dividends)
- ❌ Looking only at amounts not ROI — $5B capex is irrelevant, ROIC is what matters

## Length Baseline

500-800 words + 1 scorecard + 1 capital flow chart + 1 moat bridge.

## Workflow Linkage

| Upstream | What to fetch |
|---|---|
| `financial-data --periods 10Y` | 10Y CF: buyback/dividend/capex/M&A |
| `company-history` | M&A integration track record |
| `moat-analysis` | Moat scorecard → bridge |

| Downstream | Scenario |
|---|---|
| `alpha-thesis` | Management credibility → thesis conviction |

## Boundaries with Adjacent Skills

- Moat analysis → `moat-analysis`
- Thesis building → `alpha-thesis`
- Valuation → `dcf-model` / `comps-analysis`



## Appendix: actuals-resolved.json

Complete field listing -> `references/actuals-data-catalog.md`.

Structure: `meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`.

Consumption rules: Read actuals first → use source_map to pull [S#]/[I#] labels (do not write [actuals]) → ratios use actuals true values only (no forward estimates).
