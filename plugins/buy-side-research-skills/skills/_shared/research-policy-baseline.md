# Research Policy Baseline

> This file is an authoring and review baseline for research skills. It is not a runtime authority.
> Runtime truth lives in invoked `SKILL.md`, installed workspace `CLAUDE.md`, and workspace hooks.

## 1. Core Goal

Research outputs should feel like a strong buy-side analyst explaining a business clearly, not like sell-side initiation filler.

Default reader assumption:
- understands stocks, valuation, orders, and cash flow
- does not already understand the target industry's products, mechanisms, or jargon

The first-pass goal is:
- explain the business or mechanism clearly
- explain why it matters now
- push the reader toward higher-value follow-up questions

## 2. Fixed Layers, Not Fixed Titles

Narrative research skills now follow `fixed layers`, not `fixed titles`.

Rules:
- each archetype has mandatory layers
- layers may be implemented with slightly different section titles
- sections may merge when natural
- layer responsibility may not disappear

All narrative skills must preserve order:
- explain first
- interpret second
- deepen third
- conclude last

## 3. Output Archetypes

### Primer

Used by:
- `stock-quickread`
- `industry-quickread`
- `mechanism-map`
- `company-primer`
- `driver-map`

Mandatory layers:
1. `Foundation Layer`
2. `Interpretation Layer`
3. `Research Layer`
4. `Decision Layer`

### Compare

Used by:
- `peer-deep-dive`
- `candidate-screener`
- `pair-trade`
- `cross-market-compare`

Mandatory layers:
1. `Comparison Frame`
2. `Difference Layer`
3. `Priority Layer`
4. `Research Layer`

### Market

Used by:
- `market-lens`
- `consensus-map`
- `information-impact`

Mandatory layers:
1. `Market State Layer`
2. `Expectation Layer`
3. `Proof Layer`
4. `Decision Layer`

### Thesis

Used by:
- `alpha-thesis`
- `bear-pre-mortem`
- `earnings-setup`
- `next-step`

Mandatory layers:
1. `Core View Layer`
2. `Support Layer`
3. `Failure Layer`
4. `Action Layer`

## 4. Beginner-First Writing Contract

Default behavior:
- assume the reader is new to the product or mechanism
- answer basic questions in the output itself
- do not force the reader to ask follow-up questions just to understand the business

The first visible screen should answer some combination of:
- what is this in real life
- who pays
- how it makes money
- why it matters now
- what people most often misread

For `Primer` outputs, the first screen should default to a `Reality -> Investment Bridge -> Research` reading path:
- `Reality`
  - one plain-language definition
  - card-style explanation of the key business, product, or mechanism buckets
  - one bridge table that connects understanding to stock relevance
- `Investment Bridge`
  - why the name matters now
  - what is most likely misread
  - the core framing
  - what actually drives the stock, theme, or mechanism
- `Research`
  - what the market or reader is already assuming
  - what to check next
  - a compact bottom line

For `Primer` cards:
- use one card per important bucket, usually `2-4`
- each card should answer:
  - what it sells or does
  - who pays or who is affected
  - how money is made or value is transmitted
  - why that bucket matters

For `Primer` bridge tables:
- they are mandatory
- they should connect reality to investing, not repeat the cards
- preferred column pattern:
  - bucket
  - who pays / who is affected
  - how money is made / how value transmits
  - what is easiest to notice
  - what matters more for the stock

Interpretive writing rules:
- jargon must be explained on first use
- tables need a takeaway, not restatement
- unclear facts must be labeled `[需查证]`, `[来源待补]`, `not disclosed`, or `working hypothesis`
- titles may be English; body text defaults to Chinese

Anti-patterns:
- textbook industry intros
- management biography filler
- section-by-section restatement of disclosed segments with no judgment
- generic SWOT
- decorative charts with no analytical job
- opening with market shorthand before the reader understands the real business
- using abstract buy-side shorthand such as `profit pool`, `option value`, `re-rating`, or `risk appetite` as first-screen explanations

## 5. Source And Truth Contract

Every truth-like claim needs a source anchor or explicit uncertainty label.

Truth-like claim includes:
- facts
- numbers
- dates
- quotes
- disclosed relationships
- customer or project claims
- industry facts
- market data snapshots

Rules:
- inline clickable short anchors in prose or tables
- one final `## Resources` section per artifact
- judgment may be unsourced, but its factual basis may not
- no fabricated URLs, quotes, or numbers

Source hierarchy:
- disclosure-fact track: `topic-local evidence cache > primary public > trusted third-party > web`
- market-snapshot track: `topic-local evidence cache / financial-data > trusted third-party > web`

Within the same quality tier:
- prefer home-market
- prefer local-language source

## 6. Visual Selection Policy

Images and charts are allowed whenever they materially reduce confusion.

Three visual families:
- `理解图`
  - product image
  - scene image
  - product map
  - mechanism diagram
  - value chain
  - footprint or capability map
- `比较图`
  - product exposure matrix
  - peer scatter
  - revenue or profit mix comparison
  - margin comparison
  - backlog or order comparison
  - valuation comparison
  - relative price performance
  - correlation matrix
- `投资图`
  - valuation band
  - reasonable vs FOMO track
  - price plus events overlay
  - catalyst timeline
  - consensus revisions
  - waterfall or bridge
  - margin walk
  - SOTP
  - sensitivity heatmap
  - concentration or Pareto
  - debt maturity or capital stack

Selection rule:
- choose visuals because they improve understanding
- do not add visuals for decoration

## 7. Visual Routing

Markdown is always the primary research artifact.

`research-viz` is the only formal HTML companion route.

Levels:
- `Level 0`: Markdown only
- `Level 1`: Markdown with light embedded visuals
- `Level 2`: Markdown plus `research-viz` companion HTML

Upgrade to `research-viz` when at least two are true:
- more than three core visual units need side-by-side reading
- more than one visual family is needed together
- Markdown would require repeated large tables or long visual stacks to stay understandable
- HTML would clearly reduce first-read friction

Companion HTML rules:
- never replaces the base Markdown artifact
- must stay within the thesis boundary of the base artifact
- must bind to the base artifact stem

## 8. Visual Source And Cache Policy

Source priority:
1. company website, IR, annual report, investor presentation
2. government, exchange, industry association, research institution public materials
3. reliable media, public databases, public reports
4. AI-generated analysis visuals only for mechanism, structure, overview, or analytical diagrams

Rules:
- real products, facilities, and deployment scenes should use real images where possible
- AI visuals must never masquerade as real-world photos
- every visual must answer a clear research question

Cache policy:
- `topic shared cache` for reusable source visuals
- `artifact local cache` for one-off analytical visuals
- reuse existing topic visuals before redownloading or regenerating

## 9. Governance Sync

Any shared research behavior change must be synced in the same change:
1. this file
2. affected active research `SKILL.md`
3. workspace `CLAUDE.md.template` when high-level workspace behavior changes
4. public docs and manifests when package-facing behavior changes

## 10. UTF-8 Discipline

Chinese and multilingual text files must remain UTF-8 without BOM.
