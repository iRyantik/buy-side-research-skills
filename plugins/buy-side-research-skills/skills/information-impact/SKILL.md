---
name: information-impact
description: Check whether a news claim rumor note or data point is credible and research-relevant.
---

# Information Impact

Check whether a news claim rumor note or data point is credible and research-relevant.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- This skill is a `Market`. It must preserve `Market State Layer -> Expectation Layer -> Proof Layer -> Decision Layer`.
- It is a fast event-check skill. Keep it concise and evidence-led.

## Layer Contract

### Market State Layer
- what happened
- who said it
- why it entered the market tape

### Expectation Layer
- what the market may now believe if the claim is true

### Proof Layer
- what still needs verification
- whether this is direct evidence, weak linkage, or noise

### Decision Layer
- whether the claim matters enough to chase further
- where to route next if it does

## Quality Bar

Good output should quickly distinguish:
- verified fact
- plausible but unverified signal
- weak thematic association
