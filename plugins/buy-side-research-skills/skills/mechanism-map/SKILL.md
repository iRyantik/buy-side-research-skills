---
name: mechanism-map
description: Explain industry mechanisms engineering principles equipment chains and process flows.
---

# Mechanism Map

Explain industry mechanisms engineering principles equipment chains and process flows.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Primer`. It must preserve `Foundation Layer -> Interpretation Layer -> Research Layer -> Decision Layer`.
- Use this skill when the reader does not yet understand how the machine, chain, or process actually works.

## Intent

This skill exists to prevent fake understanding.

It should explain:
- the key terms
- the flow of the system
- the bottleneck or control point
- where value is captured
- what this mechanism changes for research

It should not become:
- a generic industry intro
- a stock thesis
- a DCF or comps note

## Layer Contract

### Foundation Layer

Must make the mechanism legible in plain language.

Expected section responsibilities:
- `Understand The Mechanism First`
- `Mechanism In Plain English`
- `Terms That Matter`
- `How It Works`

### Interpretation Layer

Must explain why the mechanism matters economically.

Expected section responsibilities:
- `Why This Mechanism Matters`
- `Most Likely Misread`
- `Bottleneck / Control Point`
- `Where Value Is Captured`

### Research Layer

Must connect the mechanism to downstream research.

Expected section responsibilities:
- `Research Read-Through`
- `What To Check Next`

Typical handoffs:
- `driver-map` for revenue, margin, backlog, or model-driver implications
- `peer-deep-dive` when the mechanism clarifies cross-company differences
- `alpha-thesis` once the investment expression is ready

### Decision Layer

Must leave a compact conclusion.

Expected section responsibilities:
- `Bottom Line`
- `Resources`

## Visual Guidance

Mechanism visuals are preferred over product photos when the chain itself is the confusing part.

Good visuals:
- mechanism diagram
- process flow
- value chain
- capability map
- bottleneck map

Escalate to `research-viz` when:
- the chain needs multiple coordinated diagrams
- the explanation requires side-by-side mechanism, economics, and company exposure views

## Quality Bar

Good output should stop the reader from asking:
- how this process works
- which step is the real bottleneck
- why one part of the chain earns more than another

It should push the next question toward:
- which company captures that value
- which driver this mechanism affects
- what assumption in the thesis depends on this chain
