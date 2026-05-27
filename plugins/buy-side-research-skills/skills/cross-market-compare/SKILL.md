---
name: cross-market-compare
description: Compare local listings ADRs or cross-market peers across valuation currency liquidity and access.
---

# Cross-Market Compare

Compare local listings ADRs or cross-market peers across valuation currency liquidity and access.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Compare`. It must preserve `Comparison Frame -> Difference Layer -> Priority Layer -> Research Layer`.
- It must be strict about basis, currency, ratio, and liquidity comparability.

## Layer Contract

- `Comparison Frame`: why these listings or markets are actually comparable
- `Difference Layer`: what differs in valuation, liquidity, accounting basis, or investor base
- `Priority Layer`: whether the spread matters
- `Research Layer`: what still needs normalization or verification
