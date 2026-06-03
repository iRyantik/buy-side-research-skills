---
name: moat-analysis
description: Scorecard-based competitive moat analysis with anchored scoring, evidence grading, peer comparison, and moat trajectory.
---

# Moat Analysis

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Quantify competitive moat — not with adjectives, but with anchored scores, graded evidence, peer comparison, and a trajectory judgment. Every score must answer: why not one point higher or lower? Every moat must answer: is it getting wider or narrower?

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data pipeline**: Call `/financial-data --lite <ticker>` for baseline.
- **Data validation**: Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证]). See §3.2.
- **Actuals-only**: ROIC, margins, and all moat scorecard financial metrics use actuals-resolved.json disclosed data only.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## Core Philosophy

The most common failure mode of moat analysis is reading like a hymn — "leading technology," "strong brand," "high customer stickiness." The bar for distinguishing good moat analysis from bad is simple: after reading it, do you know **which variable, if it changes, would break the moat**? If not, the analysis is not done.

The second fatal flaw: moat is relative. MYCR scores a 9 on technology barriers because Huntkey is a 5 and Besi is an 8. If Huntkey breaks through 1μm precision tomorrow, MYCR's barrier does not automatically change — but your 9 must change. A moat scorecard must include peer benchmarking.

The third fatal flaw: moat is dynamic. In the CPO era, wire bonding as a process may simply disappear — K&S's moat is not narrowing, it is gone. Every moat analysis must answer: under the next-generation technology / product / paradigm, is this barrier strengthening, staying flat, weakening, or vanishing?

## Trigger Scenarios

- "Analyze xxx's moat"
- "Who has deeper barriers, xxx or yyy"
- "Can xxx defend its current market share"
- "Is xxx's competitive position improving or deteriorating"

## Five-Dimension Scoring

Each dimension scored 1-10, must include peer benchmarking, must be backed by observable evidence.

### 1. Technology Barriers

Not "good technology" — it is how long and how much money a new entrant needs to catch up to your current level. And how much further you have run while they are chasing.

| Score | Criterion | Example |
|---|---|---|
| 9-10 | Only you + 1 other globally can do it. Entry requires 3+ years and $100M+ | ASML EUV: only one. Optoelectronic die-bonding at 1μm: only MRSI/Besi/ASMPT |
| 7-8 | 3-5 players can do it, but you have a generational lead (one generation ahead of #2) | ficonTEC CPO coupling: 2-3 players chasing, but 18-month lead |
| 5-6 | >5 players can do it, you are top 3 but the gap is not significant | Mid-range die-bonding: Huntkey/Bozhong etc. all capable, precision gap not significant |
| 3-4 | Technology learnable within 12 months, no IP protection | Turnkey automation lines: all 3C automation firms can do it |
| 1-2 | Technology threatened by substitutes, your tech roadmap may be leapfrogged | Wire bonding may simply disappear in the CPO era |

**Key question**: How much R&D spend does it take to pull one generation ahead? $10M? $100M? Divide this number by the company's annual R&D expense = how many years of R&D budget a chaser needs. The larger the ratio, the deeper the barrier.

### 2. Customer Lock-in

Not "good customer relationships" — it is how much money, time, and risk a customer would incur if they switched suppliers.

| Score | Criterion | Example |
|---|---|---|
| 9-10 | Switching requires 1+ year requalification, may affect customer deliveries | Aircraft engines: requires re-certification; customers will not take that risk to save 5% |
| 7-8 | Switching requires 3-12 months, real cost but not impossible | Die-bonding + coupling as a bundle: swapping the bonder means re-running coupling parameters, but customers will trial a second source |
| 5-6 | Switching <3 months, mainly relationship/habit rather than genuine lock-in | Most industrial goods |
| 3-4 | Almost zero switching cost | Standard parts, commodity |
| 1-2 | Customers are actively seeking alternatives, your product is a pain point | |

**Key question**: When was the last time a major customer switched suppliers? How long did it take? If it has never happened, it may not be lock-in — it may just be that no one has tried.

### 3. Scale Effects

Not "large revenue" — it is the rate at which unit cost declines with scale.

| Score | Criterion |
|---|---|
| 9-10 | Unit cost declines >15% per doubling, with evidence (gross margin trend rising consistently) |
| 7-8 | Declines 10-15% |
| 5-6 | Declines 5-10% |
| 3-4 | Declines <5% |
| 1-2 | No scale effect, or diseconomies (harder to manage as scale increases) |

**Key data**: How many times revenue has doubled over the past 5 years, and how gross margin has changed.

### 4. Regulatory / Certification

| Score | Criterion |
|---|---|
| 9-10 | Statutory barrier to entry, 5+ year certification cycle, only you and 1-2 others hold it |
| 7-8 | Industry-mandated certification 1-3 years, not anyone can just enter |
| 5-6 | Certification exists but is not a gatekeeping condition |
| 3-4 | Voluntary standards |
| 1-2 | No regulation of any kind |

### 5. Brand / Switching Cost / Network Effects

Brand is not "being famous" — it is whether you can charge a premium. Switching cost is not "inconvenient" — it is "switching means losing data / business disruption."

| Score | Criterion |
|---|---|
| 9-10 | Brand premium >20% vs #2, and quantifiable |
| 7-8 | Premium 5-20% |
| 5-6 | Same price, brand is the tiebreaker |
| 1-2 | Must discount to compete |

## Evidence Strength

Every piece of evidence must be tagged with strength. Hard evidence = publicly available numbers. A good moat analysis has at least one Hard.

| Strength | Definition | How to find |
|---|---|---|
| **Hard** | Quantifiable, publicly verifiable | Gross margin vs peer over 10 years, customer concentration, switching case study, ROIC history |
| **Medium** | Observable but not quantified | Industry interviews mentioning onboarding cycle, customer RFQ frequency, supplier list changes |
| **Soft** | Qualitative only | "Industry consensus," "reportedly," agent inference |

## Output Structure

> **Source contract**: Every row in all tables below that involves valuation, probability, scoring, returns, or market-size figures must carry a source anchor ([S#](url) or [I#](url)).
>
> **Density table**:
>
> | Section | Source required | Exemption |
> |---|---|---|
> | Moat Scorecard | Specific numbers/events + source in Evidence column, every row | The score itself |
> | Competitive landscape comparison | Market share / margin / pricing data for each peer | — |
> | Switching cost / Barrier | Quantified evidence for each barrier (contract term / switching cost / certification cycle) | — |
>
> **Completion Gate**: After writing, scan the scorecard → every row in Evidence has [S#]/[I#] → rows with `[待查]` ≤3 → Resources section is expanded.

~~~markdown
## Moat Scorecard

| Dimension | Score | Evidence | Strength | Peer A | Peer B |
|---|---|---|---|---|---|
| Technology Barriers | 9 | Die-bonding precision 1μm, only Besi/ASMPT can match; R&D/$rev = 15% vs peer 8% | Hard | 8 | 5 |
| Customer Lock-in | 7 | Die-bonding + coupling bundled suite, switching requires 6-12 months; but no case of a major customer actually switching yet | Medium | 6 | 4 |
| Scale Effects | 5 | Rev doubled in 3Y, gross margin +300bp | Hard | 6 | 4 |
| Regulatory / Certification | 3 | — | Soft | 3 | 3 |
| Brand | 4 | Swedish brand, no premium in China market | Soft | 6 | 3 |
| **Total** | **5.6** | — | — | **5.8** | **3.8** | Ev |

## Moat Trajectory

| Dimension | Current | 3 Years Out | Driver |
|---|---|---|---|
| Technology Barriers | 9 | → 9 (stable) | 1.6T precision requirements continue to filter out contenders |
| Customer Lock-in | 7 | → 8 (widening) | CPO coupling suite further deepens bundling |
| Scale Effects | 5 | → 6 (widening) | GT order scale growth |
| Regulatory | 3 | → 3 (stable) | — |
| Brand | 4 | → 5 (widening) | CPO volume production validation raises industry recognition |

## Visual

**Moat Radar** (description; actual chart via research-viz):
         Technology Barriers (9)
            ▲
           /|\
          / | \
Brand  |  |  Customer Lock-in
(4) --+-- (7)
          |
          |
        Scale (5) ---- Regulatory (3)

## Killer Question

If a PE fund gave you $2B to replicate this business within 3 years:
- What is the hardest link in the chain? (= deepest barrier)
- How many people and how much time would it take? (= quantified scale effects + technology barriers)
- Where would you poach people from in Year 1? (= talent barrier)
- Why wouldn't customers switch? Even if you were 20% cheaper? (= real strength of customer lock-in)
~~~

## Anti-Patterns

- ❌ No scoring anchor — cannot explain the difference between an 8 and a 7
- ❌ No peer benchmarking — moat cannot be assessed in isolation
- ❌ Evidence not tagged with strength, all Soft
- ❌ Score of 9 or above with no Hard evidence
- ❌ No moat trajectory — only a snapshot
- ❌ No killer question
- ❌ Not looking at gross margin trend vs peer — absolute gross margin is useless; look at dispersion
- ❌ Treating market share as moat (high share may have been won through price wars)
- ❌ Treating a single-generation product advantage as a structural barrier
- ❌ Not re-evaluating under the next-generation paradigm

## Length Benchmark

600-1000 words + 1 scorecard + 1 trajectory table + radar chart + killer question.

## Workflow Linkage

| Upstream | What to pull |
|---|---|
| `mechanism-insight` | Engineering basis for technology barriers |
| `driver-map` | Scale / cost evidence |
| `company-history` | Historical competitive position evolution |
| `peer-deep-dive` | Peer benchmarking data |

| Downstream | Scenario |
|---|---|
| `alpha-thesis` | moat → thesis conviction |
| `peer-deep-dive` | Moat score embedded in §4.3 |

## Boundaries with Adjacent Skills

- Technology fundamentals → `mechanism-insight`
- Management assessment → `capital-allocation`
- Full thesis → `alpha-thesis`

## Appendix: Financial Data

python _scripts/financial-data/actuals-to-appendix.py <TICKER>

## Appendix: actuals-resolved.json

Full field listing -> `references/actuals-data-catalog.md`.

Structure: `meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`.

Consumption rules: read actuals first → pull [S#]/[I#] tags from source_map (do not write [actuals]) → ratios use only actuals-resolved true values (not forward estimates).
