---
name: consensus-map
description: Map consensus buy-side bar priced-in assumptions revisions and variant-view gaps.
---

# Consensus Map

Map consensus buy-side bar priced-in assumptions revisions and variant-view gaps.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Market`. It must preserve `Market State Layer -> Expectation Layer -> Proof Layer -> Decision Layer`.
- It exists to explain what the market already believes and what still has to be proven.

## Layer Contract

### Market State Layer
- what current price or setup implies

### Expectation Layer
- `Consensus In Plain English`
- `What The Market Already Believes`
- `current price` vs `priced in`

### Proof Layer
- `The Real Bar`
- `Reasonable Track Or FOMO Track`
- what evidence must still arrive

### Decision Layer
- variant questions
- bottom line
- resources

## Quality Bar

Good output should stop the reader from asking:
- what is already priced in
- whether the market bar is easy or hard

It should push the next question toward:
- what KPI or event would break the current setup
- whether there is a true variant-view gap worth a thesis
