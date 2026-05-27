---
name: market-lens
description: Map current market style risk appetite theme crowding and FOMO expansion conditions.
---

# Market Lens

Map current market style risk appetite theme crowding and FOMO expansion conditions.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Market`. It must preserve `Market State Layer -> Expectation Layer -> Proof Layer -> Decision Layer`.
- It is an environment overlay skill. It does not replace company research or thesis work.

## Intent

This skill exists to answer:
- what kind of stocks the market is rewarding now
- how much crowding is already present
- whether FOMO expansion still has room
- what signals would invalidate the current setup

## Layer Contract

### Market State Layer

Expected section responsibilities:
- `What The Market Is Rewarding Right Now`
- `Global Risk Appetite`
- `Local Market Style`
- `Theme Crowding`

### Expectation Layer

Expected section responsibilities:
- `Current Setup In Plain English`
- `1-3M Tape / Style`
- `6-12M Fundamental Setup`

### Proof Layer

Expected section responsibilities:
- `FOMO Expansion Test`
- `Key Market Signals`
- `Failure Signals`

### Decision Layer

Expected section responsibilities:
- `Bottom Line`
- `Resources`

## Output Boundary

This skill should:
- provide market overlay
- influence research priority and style preference

This skill should not:
- give a full single-name thesis
- replace `consensus-map`
- replace `stock-quickread`

## Visual Guidance

Good visuals:
- style weight chart
- valuation band
- price plus events overlay
- crowding or breadth visual

Escalate to `research-viz` when:
- several market visuals are needed together
- the note would otherwise become a dense stack of market tables
