---
name: company-primer
description: Map an unfamiliar company's business segments customers history and disclosure evolution.
---

# Company Primer

Map an unfamiliar company's business segments customers history and disclosure evolution.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Primer`. It must preserve `Foundation Layer -> Interpretation Layer -> Research Layer -> Decision Layer`.
- It is lighter than `stock-quickread` on market and valuation, and heavier on business continuity and disclosure evolution.

## Layer Contract

### Foundation Layer
- what the company actually does
- what products or segments matter
- who pays
- use bucket cards before narrative summary
- each card should answer:
  - what it sells
  - who buys
  - how money is made
  - why that bucket matters
- include a mandatory `Business Map` bridge table with:
  - business bucket
  - who buys
  - how money is made
  - what is easiest to notice
  - what matters more for the stock

### Interpretation Layer
- how the business changed
- what disclosure or segment continuity can mislead the reader
- what the most likely business misread is
- use this as the `Investment Bridge Page`

### Research Layer
- what business or disclosure question still blocks judgment
- where to route next: `driver-map`, `mechanism-map`, or `information-impact`
- this is the lighter `Research Page`
- it should end with `What To Check Next` and `Bottom Line`

### Decision Layer
- whether the business foundation is now clear enough for deeper work

## Quality Bar

Good output should stop the reader from asking:
- what this company actually does
- whether current segments line up with prior history

It should push the next question toward:
- which driver needs decomposition
- which mechanism still needs explanation
