---
name: pair-trade
description: Evaluate a long short pair trade hedge candidate spread logic and key risks.
---

# Pair Trade

Evaluate a long short pair trade hedge candidate spread logic and key risks.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Compare`. It must preserve `Comparison Frame -> Difference Layer -> Priority Layer -> Research Layer`.
- It must stay direction-aware. A pair is not a neutral compare note.

## Layer Contract

- `Comparison Frame`: why these two belong together
- `Difference Layer`: what actually separates long and short legs
- `Priority Layer`: why one leg should win
- `Research Layer`: what breaks the spread and what to verify next
