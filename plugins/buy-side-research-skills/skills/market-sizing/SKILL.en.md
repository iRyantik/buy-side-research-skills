---
name: market-sizing
description: Bottom-up TAM SAM SOM estimation — structured breakdown with source tier, confidence, and alternative scenarios per segment.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Market Sizing

Turn "how big is this market" into a structured estimate where every row has a source, a tier, a confidence level, and an alternative scenario. The output is not one number — it's a breakdown table plus a visual pyramid. Feeds directly into `scenario-model`, which now acts as the downstream odds memo skill.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `_shared/research-runtime.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Philosophy

The real difficulty of TAM estimation is not "can't find the data" — it's "do I trust the data I found." Prospectuses cite Frost & Sullivan figures; Frost is a paid-report firm whose clients are the IPO companies — inherently upward-biased. Sell-side industry chapters may have been copied from Frost by an intern. Company IR's "addressable market $10B" is a PR number.

The most common agent mistake: search up a number and cite it. What you should do instead: find at least two independent sources → cross-validate → if divergence >2x, flag `[分歧大]` and use the midpoint. If one source is 5x larger than another, flag `[可能虚高, 源: xxx]`.

Another fatal pitfall: not distinguishing TAM / SAM / SOM. TAM is "the whole world that could possibly buy this," SAM is "the portion we can reach," SOM is "the portion we can realistically capture." Confusing them causes `scenario-model` to use TAM directly as SAM — overstating upside.

## Trigger Scenarios

- "How big is the CPO equipment market"
- "Break down the optical module burn-in test TAM"
- "What is the SAM for this niche segment"
- "TAM breakdown for xxx industry"

## Methodology

### Two Paths — Choosing the Right One Is Key

| Path | Approach | When to Use | Pitfalls |
|---|---|---|---|
| **Bottom-up** | Reachable customers × ASP × penetration rate | When granular data exists (specific equipment category, known customer base) | Inaccurate ASP amplifies error. Customer count is easily overstated (counting "might buy" as "will buy") |
| **Top-down** | Industry report total × target segment share × adjustment factor | Only macro data available; segment too new for dedicated reports | The industry report's segmentation cut rarely matches what you need. Share percentages are finger-in-the-air |

**Selection Rule**: If a market can be sized bottom-up (customer count <100 and known), prefer bottom-up. If the customer count is "all datacenters" — uncountable — use top-down and flag `[top-down, source]`.

### Data Source Credibility

| Source Type | Typical Bias | Why | Usage |
|---|---|---|---|
| Third-party reports in prospectuses | 20-30% overstated | The third-party report's paying client is the IPO company; conflict of interest | Use as upper bound, discount by 20% |
| Neutral firms: Gartner / IDC | Conservative | Serve the buy side; fear being challenged | Use as baseline |
| Sell-side reports | Varies by broker | Nobody audits their TAM numbers | Cross-validation only, not primary source |
| Company IR | Overstated | PR bias | Flag as "their own estimate," mark `[公司自估]` |
| Academic / government | Most reliable but possibly stale | Independent, public | Primary source |

### Tier Classification

| Tier | Definition | Example | Allowed into scenario-model? |
|---|---|---|---|
| **Tier 0** | Machine-verified data | Segment revenue from actuals | Auto pass |
| **Tier 1** | Trusted third-party report, citable | Gartner 2025 semiconductor equipment report | Auto pass |
| **Tier 2** | Agent-derived, with clear derivation | "50 HPC DC × $20M × 60% penetration" | Requires researcher confirmation |
| **Tier 3** | No source / irreproducible | — | Forbidden |

## Output Structure

> **Source contract**: Every row in the tables below that contains valuation, probability, score, return, or market-size figures must carry a source anchor ([S#](url) or [I#](url)).
>
> **Density table**:
>
> | Section | Source mandatory | Exempt |
> |---|---|---|
> | TAM Breakdown table | Every row's Method / Source / Tier columns — Source column must be clickable | Segment name |
> | Bottom-up derivation | Digital source for every input parameter | Researcher-chosen method |
> | Cross-validation | Provenance for every alternative estimate | — |
>
> **Completion Gate**: After writing, scan the TAM table → every row's Source column has a link → Tier 1–2 rows have been verified via WebFetch → Resources section expands all sources.

```markdown
## TAM Breakdown

| Segment | Method | 2026 | 2028E | Growth | Source | Tier | Confidence |
|---|---|---|---|---|---|---|---|
| CPO burn-in test | Bottom-up | $0.2B | $1.2B | 145% | Frost via 猎奇 prospectus | 1 | Medium |
| CPO coupling | Top-down | $0.5B | $2.8B | 136% | Yole report, cross-checked w/ sell-side | 1 | Medium |
| CPO die bonding | Agent-derived | $0.3B | $1.5B | 124% | 5 OSAT × $300M capex × 20% CPO alloc | 2 | Low |

## Breakdown Dimensions

Break down by [segment / region / customer-type / technology] dimension. (Pick 1–2 most relevant dimensions.)

## SAM (addressable by Company)

| Company | Addressable Segment | SAM | Share Rationale | Ev |
|---|---|---|---|---|
| AEHR | CPO burn-in test | $720M | Currently the only wafer-level burn-in supplier |

## Key Assumptions

| Assumption | Value | Alternative Scenario | Why | Ev |
|---|---|---|---|---|
| HPC DC count 2028 | 50 | 30–70 | AMD / NVDA roadmaps suggest 50–60; if ASIC-only, could be 30 |
| CPO penetration | 15% by 2028 | 5–25% | Broadcom Bailly 2027; if delayed, 5% |
| ASP per DC | $20M | $10M–$30M | varies by DC scale; large hyperscaler = $30M |

## Visual

- TAM Pyramid (ASCII): three layers TAM → SAM → SOM
```

- Segment Pie: if TAM is broken down by multiple segments, optional pie chart (description only, actual chart via research-viz)

### TAM Pyramid (Output Example)

```
        ┌──────────────────┐
        │       TAM        │  $1.2B  Global CPO burn-in test equipment demand
        │                  │
        ┌──────────────────┐
        │       SAM        │  $720M  Market AEHR can reach (wafer-level, not module-level)
        │                  │
        ┌──────────────────┐
        │       SOM        │  $360M  AEHR's realistic capture (assuming 50% of SAM, Teradyne may enter)
        └──────────────────┘
```

## Anti-patterns

- ❌ A single number with no breakdown table
- ❌ A single source with no cross-validation
- ❌ No distinction between Bottom-up vs Top-down
- ❌ No distinction between TAM / SAM / SOM
- ❌ Taking prospectus figures at face value without adjusting for bias
- ❌ Using smooth CAGR to mask a non-linear adoption curve
- ❌ No tier label — downstream scenario-model cannot determine usability
- ❌ Key assumptions with no alternative scenarios
- ❌ TAM sliced on only one dimension (at minimum: segment + one other dimension)
- ❌ No as-of date

## Length Benchmark

500–1,200 words + 1 TAM breakdown table + 1 SAM table + 1 TAM pyramid (ASCII).

## Workflow Linkages

| Downstream | Scenario |
|---|---|
| `scenario-model` | Feed TAM as priority input for deep-work odds memo / scenario sizing |
| `candidate-screener` | Provide market-size context for industry ranking |
| `industry-landscape` | TAM can be written into the industry index |

## Boundaries with Adjacent Skills

- No scenario sizing or odds judgment → `scenario-model`
- No industry landscape → `industry-landscape`
- No company revenue forecast → `driver-map`

