---
name: industry-quickread
description: Run a first pass on an industry theme value chain demand pocket or profit pool.
---

# Industry Quickread

Run a first pass on an industry theme value chain demand pocket or profit pool.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Primer`. It must preserve `Foundation Layer -> Interpretation Layer -> Research Layer -> Decision Layer`.
- Use this skill to decide whether an industry or theme deserves deeper work and where to cut in next.

## Intent

This is not an encyclopedia dump.

It should answer:
- what this industry sells in real life
- who pays
- where the profit pool sits
- what current regime or bottleneck matters
- what should be researched next

## Layer Contract

### Foundation Layer

Must make the industry understandable before jargon.

Reality Page responsibilities:
- `Understand The Industry First`
- `Product / Value Chain Cards`
- `Industry Map`

Hard requirement:
- card-style product or value-chain explanation must appear before deep regime analysis when product form is not already intuitive
- `Industry Map` is mandatory and should bridge product understanding to stock relevance
- preferred `Industry Map` columns:
  - product bucket or value-chain step
  - who pays
  - how money is made
  - what is easiest to notice
  - what matters more for the stock

### Interpretation Layer

Must explain why the industry matters now.

Investment Bridge Page responsibilities:
- `Why This Matters Now`
- `Most Likely Misread`
- `Current Regime / Bottleneck`
- `Value Pool / Value Capture`
- `What Actually Drives This Theme`

### Research Layer

Must narrow the next research step.

Research Page responsibilities:
- `KPI / Source Map`
- `Anchor Names`
- `What To Check Next`
- `Bottom Line`

This skill should route to:
- `mechanism-map` when the chain itself is not understood
- `candidate-screener` when the next job is finding names
- `peer-deep-dive` when the next job is comparing a chosen set
- `stock-quickread` when one name deserves first-pass company work

### Decision Layer

Must end with a compact industry verdict.

Expected section responsibilities:
- `Resources`

## Visual Guidance

This skill is one of the most likely to benefit from visual support.

Good visuals:
- product map
- value chain
- capability map
- footprint map
- compact peer or value-pool chart

Escalate to `research-viz` when:
- several product buckets matter at once
- product, comparison, and market visuals need side-by-side reading
- Markdown would otherwise become a long stack of tables and images

## Quality Bar

Good output should stop the reader from asking:
- what does this industry actually sell
- who pays in this chain
- where does profit really sit

It should push the next question toward:
- which KPI is the real truth signal
- which company bucket deserves work
- whether the regime is durable or already crowded
