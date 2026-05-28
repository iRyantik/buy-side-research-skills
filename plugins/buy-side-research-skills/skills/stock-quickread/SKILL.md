---
name: stock-quickread
description: Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.
---

# Stock Quickread

Run a fast sourced first pass on an unfamiliar company and decide whether to dig deeper.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Primer`. It must preserve `Foundation Layer -> Interpretation Layer -> Research Layer -> Decision Layer`.
- Use this skill for first-pass judgment and routing. Unresolved facts stay as gap, hypothesis, or follow-up.

## Intent

This skill is for the first serious look at an unfamiliar company.

It should answer:
- what the company actually sells
- who pays
- how the company makes money
- why the stock matters now
- what the market is likely already pricing
- what should be checked next

It should not become:
- a sell-side initiation clone
- a management biography
- a five-year history dump
- a full thesis or model

## Layer Contract

### Foundation Layer

Must make the business legible in plain language.

Reality Page responsibilities:
- `Understand The Business First`
- `Business Cards`
- `Business Map`

Questions to answer:
- what is this company in real life
- what does it sell
- who buys it
- how does money get made

First-screen contract:
- start with a plain-language business definition, not a market summary
- use one card per important business bucket, usually `2-4`
- each card should answer:
  - what it sells
  - who buys
  - how money is made
  - why that bucket matters
- `Business Map` is mandatory and should bridge business understanding to stock understanding
- preferred `Business Map` columns:
  - business bucket
  - who buys
  - how money is made
  - what is easiest to notice
  - what matters more for the stock
- do not open with market shorthand or valuation framing

### Interpretation Layer

Must explain why the stock matters now and what people most often misunderstand.

Investment Bridge Page responsibilities:
- `Why This Matters Now`
- `Most Likely Misread`
- `Business Type + Market Phase`
- `What Actually Drives The Stock`

Hard requirement:
- `Business Type + Market Phase` is mandatory
- `What Actually Drives The Stock` is mandatory
- `What Actually Drives The Stock` should default to a compact table:
  - driver
  - why it matters
  - current state
- valuation framing must distinguish `Reasonable Track` and `FOMO Track` when the stock is actively investable

### Research Layer

Must narrow the next research question.

Research Page responsibilities:
- `Financial Snapshot`
- `Capital Cycle`
- `Market Lens`
- `What The Market Is Pricing`
- `Valuation Framing`
- `Key Catalysts`
- `Risks`
- `What To Check Next`

Typical handoffs:
- `company-primer` for business history, disclosure evolution, or segment continuity
- `driver-map` for revenue, margin, backlog, or price-volume-mix decomposition
- `consensus-map` for priced-in analysis, buy-side bar, and explicit expectations work
- `alpha-thesis` once the variant view is explicit

### Decision Layer

Must end with a compact judgment.

Expected section responsibilities:
- `Bottom Line`
- `Resources`

## Visual Guidance

Visuals should be chosen only when they materially improve understanding.

Default visual behavior:
- `Level 0`: Markdown only
- `Level 1`: Markdown with one to three light visuals
- `Level 2`: Markdown plus `research-viz` companion HTML

Good visuals for this skill:
- product or asset image
- business-bucket cards when multiple products or revenue buckets define the company
- business map table
- stock-driver table
- valuation band
- reasonable vs FOMO track visual
- compact bridge or margin trend when it clarifies the stock

Upgrade to `research-viz` when Markdown would become visually crowded, especially when:
- multiple products matter at once
- financial and market visuals need side-by-side reading
- the output needs card-style browsing

## Quality Bar

Good output leaves the reader no longer asking:
- what is this company
- who pays it
- why is it public-market relevant now

Good output should instead push the next question toward:
- what is the key unproven driver
- what is the market already assuming
- what would make this worth deeper work
