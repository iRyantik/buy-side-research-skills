---
name: peer-deep-dive
description: Compare companies in one industry with sourced KPI matrices and research ranking.
---

# Peer Deep Dive

Compare companies in one industry with sourced KPI matrices and research ranking.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Compare`. It must preserve `Comparison Frame -> Difference Layer -> Priority Layer -> Research Layer`.
- It must not degrade into multiple quickreads pasted together.

## Intent

This skill exists to create a shared comparison frame across several names.

It should answer:
- why these names belong together
- what is truly different between them
- which name deserves time first
- what still has to be validated

## Layer Contract

### Comparison Frame

Expected section responsibilities:
- `Why These Names Belong Together`
- `Comparison Frame`

This must define:
- why the peer set is coherent
- what basis of comparison is valid

### Difference Layer

Expected section responsibilities:
- `Quick Comparison`
- `Most Important Differences`
- `Product Exposure Matrix`
- financial and market comparison

Hard requirement:
- product, business, financial, market, and valuation differences must be surfaced directly
- the output may not look like N isolated company notes

### Priority Layer

Expected section responsibilities:
- `Market Overlay`
- `Ranking / Preferred Setup`
- `Reasonable vs FOMO` comparison where relevant

### Research Layer

Expected section responsibilities:
- `What To Check Next`
- `Bottom Line`
- `Resources`

This layer may be shorter, but it may not disappear.

## Visual Guidance

This skill is one of the most likely to escalate to `research-viz`.

Preferred visuals:
- product exposure matrix
- peer scatter
- revenue or profit mix comparison
- margin or return comparison
- backlog or order comparison
- valuation comparison
- relative price performance

Markdown is still the base artifact.

Escalate to `research-viz` when:
- multiple comparison visuals need side-by-side reading
- the peer set cannot be scanned comfortably in linear Markdown

## Quality Bar

Good output should stop the reader from asking:
- why these names are in the same set
- what actually separates them
- who should be researched first

It should push the next question toward:
- which mismatch is real
- which valuation spread is unjustified
- which name deserves a full single-name workup
