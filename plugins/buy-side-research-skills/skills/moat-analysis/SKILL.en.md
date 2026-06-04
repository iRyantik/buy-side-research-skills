---
name: moat-analysis
description: Scorecard-based competitive moat analysis with anchored scoring, evidence grading, peer comparison, and moat trajectory.
---

# Moat Analysis

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Quantify competitive moat — not with adjectives, but with anchored scores, graded evidence, peer comparison, and a trajectory judgment. Every score must answer: why not one point higher or lower? Every moat must answer: is it getting wider or narrower?

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — data pipeline, source verification chain, evidence protocol, artifact contract, save contract.
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## Core Philosophy

The most common failure mode of moat analysis is reading like a hymn — "leading technology," "strong brand," "high customer stickiness." The bar for distinguishing good moat analysis from bad is simple: after reading it, do you know **which variable, if it changes, would break the moat**? If not, the analysis is not done.

The second fatal flaw: moat is relative. MYCR scores a 9 on technology barriers because Huntkey is a 5 and Besi is an 8. If Huntkey breaks through 1μm precision tomorrow, MYCR's barrier does not automatically change — but your 9 must change. A moat scorecard must include peer benchmarking.

The third fatal flaw: moat is dynamic. In the CPO era, wire bonding as a process may simply disappear — K&S's moat is not narrowing, it is gone. Every moat analysis must answer: under the next-generation technology / product / paradigm, is this barrier strengthening, staying flat, weakening, or vanishing?

## Analysis Mode Selection

Determine which template to use based on the user's question:

| Mode | When to Use | Template |
|---|---|---|
| **A: Single Entity** | Analyze the moat depth, width, and trajectory of one company / business | See §Single-Entity Moat Analysis |
| **B: Paradigm Shift** | A technology / regulatory / competitive paradigm change → how moat is reallocated across industry segments | See §Paradigm-Shift Moat Analysis |

Rule of thumb: if the user's question involves "after XX technology/paradigm/policy change, how will the industry moat be reallocated," "which segments' barriers will deepen or disappear" — use Mode B.

## Trigger Scenarios

- "Analyze xxx's moat"
- "Who has deeper barriers, xxx or yyy"
- "Can xxx defend its current market share"
- "Is xxx's competitive position improving or deteriorating"
- "How will the CPO / new technology paradigm change the moat of the xxx industry"
- "Impact of xxx change on the competitive landscape — who benefits, who gets hurt"

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

## Causal Chain & Falsification Conditions

> Expand the causal chain for each dimension — derive the score from capability/fact, and provide the falsification condition (which single variable, if reversed, would change the score). This is not repeating the Evidence column; it's answering *why this score* and *what breaks it*.

### Technology Barriers [Score]
[Core capability / technical fact] → [Why competitors can't catch up: $ / time / IP / process secret] → [How far ahead] → Score [X]
**Breaks if**: [Specific variable], because [physical / structural reason — must be an observable single event]

### Customer Lock-in [Score]
[Lock-in mechanism: bundled suite / certification cycle / redesign cost] → [Quantified switching cost: $ / time / risk] → [Any case of a major customer actually switching?] → Score [X]
**Breaks if**: [Specific variable]

### Scale Effects [Score]
[How scale drives cost down: procurement leverage / fixed-cost absorption / learning curve] → [Gross margin trend evidence: rev vs GM relationship over past 3-5 years] → Score [X]
**Breaks if**: [Specific variable]

### Regulatory / Certification [Score]
[Certification type and cycle] → [Is this a gatekeeping condition or a bonus?] → Score [X]
**Breaks if**: [Specific variable]

### Brand [Score]
[Premium evidence or lack thereof: ASP vs peer / used-equipment residual value / customer specification rate] → Score [X]
**Breaks if**: [Specific variable]

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

### Paradigm-Shift Moat Analysis (Industry-Level)

> Use when: a technology / regulatory / competitive paradigm change → how moat is reallocated across industry segments. The core task is **causal chain transmission**: starting from the physical / engineering facts of the paradigm change, derive the barrier direction change for each segment, and provide a falsification condition for each derivation.

~~~markdown
## Verdict First

One sentence: [Paradigm change] → moat is [not simply weakened / but reallocated — which segments deepen / which disappear / which emerge from nothing] → core tension: [one sentence capturing the key contradiction]

## One Diagram

```
[Old Paradigm]          →        [New Paradigm]

Segment A      ████████████ High     ████████████████████ Very High ↑↑
Segment B      ██████████ High       ██████████████ High ↑
Segment C           Does not exist       ████████████████ 🆕 Brand New
Segment D      ████████ Mid-High       ██ → ╳ Gone ⬇⬇
Segment E      ██████ Mid             ██████ Mid →
```

> Label each segment's direction: ↑↑ Surging / ↑ Deepening / → Stable / ↓ Weakening / ↓↓ Vanishing / 🆕 From Zero to One

## Segment Deep-Dive

### [Segment Name] — [Direction]

**Where the moat came from under [Old Paradigm]**
1-2 paragraphs explaining the barrier nature of this segment under the old paradigm — not just "good technology," but why entry and switching are hard. If it was a commodity with no moat under the old paradigm, say so directly.

**What [New Paradigm] changes**
Physical / engineering-level changes, not business-level. Must be quantified ("fiber count from 1-2 to 16-64" not "more demand"). Explain the physical mechanism — what the substrate changes from and to, what the process changes from and to, what precision moves from and to.

**Why the moat deepens / weakens (root cause)**
Derive barrier changes from physical changes, in one sentence all the way through. Cannot stop at "more difficult" or "competition intensifies" — must state: physical variable X changes → barrier dimension Y changes → score moves from A to B.

**What would break this logic**
Counterfactual condition — which single variable, if reversed, would invalidate this segment's analysis. Must be an observable single event ("Huntkey breaks through ±1μm precision"), not a vague trend ("competition intensifies").

**Scoring**

| Dimension | Old Paradigm | New Paradigm | Change | Rationale | Break |
|---|---|---|---|---|---|
| Technology Barriers | X | Y | ↑/↓/→ | One sentence | What condition breaks it |
| Customer Lock-in | | | | | |
| Scale Effects | | | | | |
| Regulatory / Certification | | | | | |
| Brand | | | | | |

## Cross-Cutting Factor Scan

Factors that cut across segments — e.g., "Will general semiconductor giants cross over into this?" or "Is the customer shift from Type A to Type B good or bad?" Each factor gets 1-2 paragraphs + ASCII comparison diagram where warranted.

## Summary Table

| Segment | Old→New Change | One-Liner Root Cause | Winners | Losers |
|---|---|---|---|---|
| Segment A | ↑↑ | [Physical root cause] | [Company name] | [Company name] |
| Segment B | ↑ | ... | | |
| Segment C | 🆕 | ... | | |
| Segment D | ↓↓ | ... | | |
| Segment E | → | ... | | |

## Routing

| Next Step | Skill |
|---|---|
| [Action] | `/skill-name` |

## Resources

- [S1](url) — description
- [I1](url) — description
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

**Causal chain specific anti-patterns**:

- ❌ Causal chain stops at "demand increases / competition intensifies" — must dig down to the physical / engineering / structural root cause
- ❌ "Breaks if" describes a vague trend rather than an observable single event — "competitive landscape deteriorates" is not falsifiable; "Huntkey breaks through ±1μm" is
- ❌ Paradigm shift analysis lumps all segments together — the same paradigm change can push different segments in completely opposite directions

## Length Benchmark

**Mode A (Single Entity)**: 800-1200 words + scorecard + causal chain + trajectory table + radar chart + killer question.
**Mode B (Paradigm Shift)**: 1500-2500 words + one diagram + segment deep-dives (each with scoring table) + cross-cutting factor scan + summary table. The more segments, the longer — but each segment's causal chain must be fully developed.

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
