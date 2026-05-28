---
name: research-viz
description: Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.
---

# Research Viz

Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is the only formal `Visual Companion` route.
- It generates companion HTML. It does not replace the base Markdown research artifact.

## Intent

Use this skill when a research artifact is already valid in Markdown, but reading would clearly improve with a visual companion.

It should:
- make complex visual relationships easier to scan
- stay inside the thesis boundary of the base Markdown
- reuse saved source-backed material and cached visuals where possible

It should not:
- become a standalone research flow
- invent unsupported claims
- ship HTML without a bound Markdown base artifact

## Routing Contract

The base artifact remains primary.

Valid escalation examples:
- many product buckets need side-by-side treatment
- several comparison charts must be scanned together
- mechanism, product, and market visuals would overload Markdown

Typical chart families:
- understanding visuals
- comparison visuals
- investment visuals

Template routing should follow:
1. archetype template
2. skill delta
3. artifact-specific override only when clearly needed

For `Primer` companions, default to a three-screen reading path:
1. `Reality`
2. `Investment Bridge`
3. `Research`

For `Primer` first screens:
- start with a plain-language reality definition, not a market summary
- use card-style explanation for the key business, product, or mechanism buckets
- include one bridge table that connects understanding to stock relevance
- avoid opening with abstract shorthand such as `profit pool`, `option value`, or `re-rating`

For `Primer` bridge tables, prefer:
- bucket
- who buys / who is affected
- how money is made / how value transmits
- what is easiest to notice
- what matters more for the stock

For `stock-quickread` companions specifically, default blocks are:
- `Business Cards`
- `Business Map`
- `Why This Matters Now`
- `Most Likely Misread`
- `Business Type + Market Phase`
- `What Actually Drives The Stock`
- `Reasonable Track vs FOMO Track`
- `research-viz` is mandatory when `stock-quickread` escalates to `Level 2`
- the companion should not be hand-built outside this route

## Save Contract

HTML must:
- bind to a base Markdown research artifact
- reuse the base stem
- stay self-contained
- include title, subtitle, and source line

Companion HTML may use a minimal qualifier after the base stem when needed for multiple visuals.

## Quality Bar

Good output should make the underlying Markdown easier to read, not replace it.
