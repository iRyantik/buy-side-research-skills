---
name: alpha-thesis
description: Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Alpha Thesis

Build a sourced long or short investment thesis with variant view catalysts scenarios and kill criteria.

If upstream work has not yet clearly nailed down bull/base/bear odds, implied value, and the most critical assumptions, run `scenario-model` first. `scenario-model` handles the odds memo and sizing; this skill handles assembling those inputs into a complete thesis, variant view, catalyst, and kill criteria.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — data pipeline, source verification chain, evidence protocol, artifact contract, save contract.
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## Mental Model

The most fundamental difference between sell-side reports and a buy-side thesis: **the buy-side logic must explain "why this opportunity still exists."** If an opportunity is obvious to everyone and everyone agrees, it is already priced in — there is no alpha. Therefore the core of any thesis is the **variant view** — where you differ from consensus, why that gap exists, and what will make the market gradually agree with you.

A "long thesis" without a variant view is not a thesis; it is a narrative. Narratives don't make money.

Example — a bad thesis: "ASML is the EUV monopoly leader, long-term bullish." A good thesis: "Consensus 2026 EUV orders $17bn, I think $22bn — because High-NA ASP +20% and TSMC/Intel advanced-node capex shows no sign of slowing. The Q3 earnings order number is the first catalyst. If orders <$15bn, I am wrong, and anyone who buys this thesis loses money."

## Mandatory Sections (every one is required; if any is missing, rewrite)

### Primitive Preflight (determine whether a thesis can be written directly)

Before writing the Variant View,

## Scenario Return Calculation

| # | Calculation | Formula | Input Source |
|---|---|---|---|
| 1 | Scenario return rate | (Target Price - Current Price) ÷ Current Price | DER, MKT |
| 2 | Target Price (P/E method) | EPS × Target P/E | FS, CON |
| 3 | Target Price (EV/EBITDA method) | (EBITDA × Target Multiple - Net Debt) ÷ Shares | FS, FS |
| 4 | Weighted expected return | Σ (Probability × Scenario Return) | DER |

Bull / Base / Bear, and Kill Criteria, first determine whether the key drivers the thesis depends on have been clearly decomposed. Do not skip this check just because the user asked you to "write a thesis."

| Check Item | Pass Standard | Action if Not Passed |
|---|---|---|
| Revenue driver | Revenue growth can be decomposed into price / volume / mix, backlog conversion, segment mix, or observable KPIs | Handoff to `driver-map` first |
| Margin driver | Sources of gross / EBITDA margin changes can be decomposed into cost, mix, utilization, pricing, or operating leverage | Handoff to `driver-map` first |
| Backlog / orders | The relationship between backlog, orders, book-to-bill, and revenue recognition is clear | Handoff to `driver-map` first |
| Disclosure bucket | Reported segment / revenue buckets map to real business lines and model line items | Handoff to `driver-map` first |

If any item fails, do not force a full thesis. Output a minimal handoff block first:

```markdown
## Primitive Handoff Required

- Blocker: [which driver / disclosure bucket is unclear]
- Why it blocks thesis: [which section of variant view / scenario / kill criteria it affects]
- Handoff: `driver-map`
- Inputs needed: [filing / call / KPI / segment data needed to fill the gap]
```

### 0. Trade Structure (determines the perspective of all subsequent sections)

An L/S fund does not default to long-only. The first step must clarify what kind of single-name trade this is, because every subsequent section's writing depends on it.

| Structure | Description | Thesis Focus | Bull/Base/Bear Meaning | Kill Form |
|---|---|---|---|---|
| **Long-only** | Single-leg long | Long thesis, upside catalyst | Price + return % | Fundamental deterioration / valuation breach |
| **Short-only** | Single-leg short | Short thesis, downside catalyst | Price - return % (Bull = deeper decline, Bear = rally) | Upside catalyst / squeeze risk |

**Mandatory constraints**:
- **If the user gives Long X + Short Y, stop using this skill and switch to `pair-trade`.**
- **If the user asks "what to hedge X with" / "find a hedge candidate," stop using this skill and switch to `pair-trade`.**
- **Short-only kill criteria are written in the opposite direction from long-only** — longs worry about downside breach, shorts worry about upside squeeze.

**Bidirectional Variant View** (applies to all single-name theses):

Don't just ask "how far from long consensus"; ask in both directions:
- **vs long consensus** (bullish direction): Are your numbers / view more optimistic or more pessimistic than the bulls?
- **vs short consensus** (bearish direction): Are your numbers / view more optimistic or more pessimistic than the bears?

This prevents a long thesis from ignoring what smart shorts are asking, and prevents a short thesis from merely restating bad news the market already knows.

### 1. The Trade in One Sentence

State in one sentence: trade structure (from §0) + target + time window + approximate return range.

Examples by structure:
- **Long-only**: "Long XOM, next 12-18 months, target +35% (vs implied downside -15%)"
- **Short-only**: "Short ARKK, next 6-9 months, target -25% (vs implied upside +10%)"

Counterexamples:
- "Bullish on X's long-term prospects" — this is not a trade, it is an opinion.
- "Long X / Short Y" — this is a pair, not an alpha-thesis; use `pair-trade`.

### 2. Variant View (quantified, must have numbers)

State clearly: how much does your key forecast differ from consensus numbers?

- Example: "Consensus 2026 EBITDA $4.2B, my base case is $4.8B (+14%), the core difference is in [assumption X]"
- Counterexample: "I am more bullish than the market" — zero information.

If your core numbers align with consensus, **then you have no variant view, you are simply agreeing with consensus** — in that case no alpha exists. Either abandon this trade or rethink where you actually disagree.

### 3. Why the Gap Exists (this is the most important section)

Why is the opportunity still sitting there, unharvested? Think in categories:

- **Information edge**: Do you know something others don't? (Note: this is genuinely rare and must be compliance-clean.)
- **Time horizon arbitrage**: Is the market punishing near-term data while ignoring structural changes 2-3 years out?
- **Complexity / accounting**: Is the business complex, are financials misread, is it misclassified (treated as cyclical when it's actually a growth company; treated as a growth company when it's actually a melting ice cube)?
- **Behavioral / sentiment**: Is it hated, forgotten, just had a black swan, ESG-unloved, too small for anyone to cover?
- **Structural flow**: Passive fund / index deletion / major shareholder selling — technical pressure?

**If you cannot articulate why the gap exists, stop and re-examine the variant view** — it usually means your view is actually consistent with consensus, just using different wording.

### 4. Three Catalysts (each must be specific and time-bound)

What events will make the market start agreeing with you? When? What probability? The event itself needs a source; the probability is analyst judgment and does not need a source.

Adjust catalyst perspective by trade structure:
- **Long-only**: Upside catalysts (earnings beat, capacity ramp, capital return, regulatory tailwind).
- **Short-only**: Downside catalysts (earnings miss, guidance cut, adverse regulation, debt maturity).

Example (Long-only):
  - "Q3 earnings (November [I1](https://example.com/ir-earnings-calendar)): If management gives 2026 capex guidance < $2B [S1](./_cache/sources/q2-2024-capex-call.md), it will falsify the capital cycle bear thesis (probability 60%)"
  - "OPEC+ December meeting [I2](https://example.com/opec-calendar): Extension of production cuts would support oil price base case > $75 (probability 70%)"

Counterexample: "In the long run the market will recognize value" — this is not a catalyst, it is hope.

### 5. Bull / Base / Bear (each must have a concrete return number + probability)

Adjust meaning by trade structure:

**Long-only**:
| Scenario | Key Assumption | 12-18M Return | Probability | EV |
|---|---|---|---|---|
| Bull | ... | +60% | 25% | ... |

| Base | ... | +35% | 50% | ... |
| Bear | ... | -20% | 25% | ... |

**Short-only** (numbers are inverted: Bull = deeper decline, Bear = rally / squeeze):
| Scenario | Key Assumption | 12-18M Return | Probability | EV |
|---|---|---|---|---|
| Bull (short wins) | Earnings collapse / guidance cut | -45% | 30% | ... |

| Base | Slow bleed | -20% | 50% | ... |
| Bear (short loses) | Squeeze / earnings improve | +25% | 20% | ... |

**The scenarios themselves (numbers, probabilities) are analyst judgment** and do not need a source. But the **facts that the assumptions depend on** (current baseline numbers, historical analog cases, industry comparables) must have sources — otherwise the assumptions are groundless.

The probability-weighted return must be clearly > 0, and the gap between bull/base and base/bear must be realistic. If the bear case is more likely than the bull case but you assigned symmetric probabilities, that is self-deception.

### 6. Kill Criteria (specific to numbers / events; vague is not allowed)

Adjust kill form by trade structure:

**Long-only**: Fundamental deterioration triggers
- Example: "If Q4 2024 per-well production decline exceeds 18% (vs current 12% [S2](./_cache/sources/q3-2024-production-note.md)), the accelerating decline thesis is invalidated"

**Short-only**: Upside catalyst emerges / squeeze risk
- Example: "If short interest rises to 30%+ and days-to-cover > 5 ([I3](https://example.com/finra-short-interest) currently 18% / 3.2 days), squeeze risk escalates — must reduce position"
- Example: "If the company announces a strategic review / activist involvement ([I4](https://example.com/13d-precedent-study) historically triggers 30%+ rallies), the short thesis is invalidated"

Counterexample: "If fundamentals deteriorate" — empty words, says nothing.

### 7. Sizing Logic

Based on the asymmetry above and the clarity of kill criteria, how large should this position be? Under what conditions do you add? Under what conditions do you trim?

General principles:
- Kill criteria are very clear, signals are easy to observe → can take a larger position (risk is controllable).
- Thesis depends on 5 consecutive assumptions all being correct → position should be small (path is too long).
- Catalysts concentrated at a single point in time → consider using options rather than common stock to capture asymmetry.
- **Short-only**: borrow availability + cost + crowded short risk all enter sizing considerations. Single-name short max sizing should be lower than a long of the same conviction (asymmetric loss).

### 8. Key Assumptions Checklist

Explicitly list the key assumptions the thesis depends on. Revisit these assumptions each quarter to check whether they still hold. This is the **maintenance manual** for the thesis and the input for a pre-mortem.

Mandatory:
- 3-5 most critical assumptions.
- Current evidence / source for each assumption.
- Disconfirming signal for each assumption.
- Which assumptions should be rechecked at the next earnings release or industry data update.

## Artifact / Save Strategy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

If the path is unclear → agent auto-creates per policy baseline §11.

## Thesis Driver Mix

| Driver | Weight | Current | Target | Confidence |
|---|---|---|---|---|
| Growth (Rev CAGR) | X% | Y% | Z% | — |
| Margin (EBIT%) | X% | Y% | Z% | — |
| Multiple (PE re-rate) | X% | Yx | Zx | — |

Growth stalls + Margin holds → flat. Growth hits + Margin expands → bull re-rate.

## Anti-Pattern Self-Check

- ❌ Section 0 does not clarify trade structure → the entire thesis is vague, rewrite.
- ❌ User says Long X / Short Y but you continue writing alpha-thesis → wrong skill triggered, switch to `pair-trade`.
- ❌ User asks "what to hedge X with" but you continue writing alpha-thesis → wrong skill triggered, switch to `pair-trade`.
- ❌ Variant view, scenario, or kill criteria depend on revenue / margin / backlog / price-volume-mix drivers but no Primitive Preflight was done → trigger `driver-map` first.
- ❌ Variant view only vs long consensus, not vs short consensus → missing L/S perspective.
- ❌ Short-only but kill criteria written same as long → squeeze risk not considered.
- ❌ Section 2 is qualitative, no concrete numbers → variant view does not exist, rewrite.
- ❌ Section 3 cannot be written → thesis is likely problematic, think it through before continuing.
- ❌ Catalysts are all "long-term" — no specific timing → effectively no catalyst, relist.
- ❌ Bear case return is -2% → bear case too weak, didn't seriously think through how bear happens.
- ❌ Kill criteria are "if I'm wrong I'll exit" → no observable concrete signals, equivalent to nothing.
- ❌ Sections contain long recaps of business model / industry background → that's quickread's job; here only include what's directly relevant to the thesis.

**Source-specific**
- ❌ Variant view cites consensus numbers but no source → mark or supplement.
- ❌ Catalyst mentions events (earnings, regulatory meetings, investor day) without specific date sources → supplement.

## Length Baseline

Full output **800-1500 words**. This is meant to be pitched — must be high density and actionable.

## Journal-First Handoff

This skill defaults to producing research views and does not write trading-status files. If the user requests saving, save the thesis as a date-stamped research artifact at:

```text
industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-alpha-thesis.md
```

This skill's `artifact_policy.naming_mode = plain`. Default continues using `YYYY-MM-DD-<artifact>.md`; only when a filename collision occurs does the `agent` append `-2 / -3` as a fallback — do not make qualifiers the default thesis naming convention.

If the current date-stamped save path is unclear, the agent auto-creates the directory and index per policy baseline §11.

`research-journal` only absorbs a thesis after it has been researched clearly and forms a reusable cognitive increment; do not write unverified theses directly as memory.

If high-value questions arise during thesis writing — disclosure buckets, business substance, model drivers, source conflicts — directly trigger the Senior Analyst Radar alert from `Research Runtime Capsule`. If the issue is that revenue / margin / backlog / price-volume-mix drivers are not clearly decomposed, use `driver-map` first; if the issue is that the research direction itself is unclear, use `next-step`.

