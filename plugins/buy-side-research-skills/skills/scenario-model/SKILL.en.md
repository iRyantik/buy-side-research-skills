---
name: scenario-model
description: Quantify a scenario thesis into a verdict-first odds memo with bull/base/bear sizing and source-tracked assumptions.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Scenario Model

Turn a scenario thesis into a verdict-first odds memo. Not a driver-map replacement and not a full thesis writer — fast envelope math that forces every assumption onto the table where it can be challenged.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- workspace `.references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Philosophy

The real value of a scenario model is not the upside number — it is **exposing which assumption is most worth spending time to verify**. A $7.2B implied market cap built on "TAM $1.2B, share 60%, PE 40x" where the 60% share is sourced only from "they're the leader" is garbage. But if the sensitivity table tells you "if share drops from 60% to 40%, upside falls from +148% to +100%," you know the share assumption is reasonably robust. The output of this skill is not a final answer — it is a map of "what you should verify first."

Easiest way to die here: the agent finds a TAM number and reuses it without asking which source it came from, whether it might be biased high or low, or whether it makes sense in this scenario.

## Trigger Scenarios

- "If CPO reaches 15% penetration, how much can AEHR rally?"
- "Calculate MYCR bull/base/bear theoretical market cap"
- "For the stock pushed in this scenario, how low can the worst case go?"
- "Reverse: what does it take to be worth $5B, how many CPO orders are needed?"
- "Are the odds on this thesis good enough to keep working on it?"
- "Which assumption is most worth verifying?"

## Input Clarification

Every input must have a derivation path. The agent follows the path to find it; if not found, downgrade and annotate.

| Field | Where to Find (Derivation Path) | Fallback |
|---|---|---|
| **TAM** | 1. `market-sizing` artifact (preferred) → 2. Prospectus / annual report citing third-party research → 3. WebSearch industry reports → 4. Company IR presentation | Mark `[agent推算, Tier 2]`, write out the derivation logic |
| **Target Share** | 1. `mechanism-insight` competitive landscape (current unit/value share) → 2. Customer filings' supplier concentration → 3. Industry conferences / product launches → 4. Benchmark leader share in analogous industry nascent markets | At minimum give high/low range, never a single-point guess |
| **Target Margin** | 1. `financial-data` actuals current margin → 2. Same-industry scale effect benchmark (how much margin typically improves when revenue doubles) → 3. Peer comparable product-line margin | Default = current margin |
| **Target PE** | 1. `driver-map` peer-group forward PE → 2. `peer-deep-dive` valuation table → 3. Company's own 3-year PE range → 4. Companies in same industry with equal growth rate PE | Must be filled |
| **Current Valuation** | `/financial-data` market_data | — |

> Tier 0 (machine-verified) = actuals / Bridge. Tier 1 (trusted third-party) = Frost/Gartner cited in official documents. Tier 2 (agent-derived) = has derivation but not verified by a third party. All Tier 2 assumptions must include the derivation process; they enter the model only after researcher confirmation.

## Execution Flow

```
Phase 1: Follow derivation paths to find data → Assumptions table (each row has source/tier/confidence)

Gate:
  All Tier 0/1 + upside >20% → auto-advance to Phase 2
  Has Tier 2 + upside >50% → worth doing, annotate [待确认] then advance to Phase 2
  All Tier 2 + upside <20% → tell researcher "not worth it — even the most optimistic assumptions can't deliver 20%"
  Even the most extreme scenario, if it hits, cannot destroy the thesis → don't waste researcher's time

Phase 2: Calculate → sensitivity (with correlation annotations) → deliver verdict and most-worth-verifying assumption
```

## Boundaries with Adjacent Skills

- `market-sizing` remains the primary skill for TAM/SAM/SOM. `scenario-model` reuses it whenever possible; only if no existing TAM artifact exists is a minimal TAM derivation permitted, with explicit Tier annotation.
- `alpha-thesis` remains the full thesis skill. `scenario-model` only outputs an odds memo — it does not take over the full variant view, catalyst narrative, or kill criteria.
- `driver-map` remains the full valuation workbook. `scenario-model` does not do full forecasts, WACC, terminal value, or a complete workbook.
- `driver-map` remains responsible for linked three-statement modeling. `scenario-model` only does envelope math.

## Calculation Method

### Computation Chain

```
                    ┌──────────────┐
                    │  Scenario    │  ← market-sizing / prospectus / WebSearch
                    │  TAM         │
                    │  e.g. $1.2B  │
                    └──────┬───────┘
                           │ × Target Share (60%)
                           ▼
                    ┌──────────────┐
                    │  Scenario    │  ← mechanism-insight competitive landscape
                    │  Revenue     │     supports share assumption
                    │  $720M       │
                    └──────┬───────┘
                           │ × Target Margin (25%)
                           ▼
                    ┌──────────────┐
                    │  Scenario    │  ← financial-data actuals → current margin
                    │  Profit      │     ± scenario delta
                    │  $180M       │
                    └──────┬───────┘
                           │ × Target PE (40x)
                           ▼
                    ┌──────────────┐
                    │  Scenario    │  ← driver-map peer-group
                    │  Market Cap  │     forward PE median
                    │  $7.2B       │
                    └──────┬───────┘
                           │ ÷ Current Market Cap ($2.9B)
                           ▼
                    ┌──────────────┐
                    │  Upside      │
                    │  +148%       │
                    └──────────────┘

Each step's right side annotates the standard derivation path for that input.
If a step uses Tier 2 (agent-derived), the connecting line becomes dotted.
```

### Standard Path

```
Scenario Revenue = TAM × Target Share
Scenario Profit  = Scenario Revenue × Target Margin
Scenario Market Cap = Scenario Profit × Target PE
Upside = (Scenario Market Cap - Current Market Cap) / Current Market Cap
```

### Reverse Path (when researcher asks "what does it take to be worth $X")

```
Required Profit  = Target Market Cap / Target PE
Required Revenue = Required Profit / Target Margin
Required Orders  = Required Revenue / ASP
→ Compare to current: how many multiples? Is it reasonable?
```

The agent determines direction automatically based on the user's query.

### Sensitivity Rules

**Variables are not independent.** Treating TAM and share as independent variables for sensitivity analysis is equivalent to assuming the market gets bigger but competition does not increase — this is wrong.

Correct approach:
- TAM ↑ → typically means the market is more attractive → competition intensifies → share may fall. Annotate this correlation.
- Margin ↑ → typically requires scale → may already be implicit in the TAM growth assumption.
- PE ↑ → typically means the market's confidence in growth has increased → correlated with TAM/revenue growth rate.

Use footnotes in the sensitivity table to annotate correlations, e.g.: "If TAM ↑ 50%, share is likely to fall from 60% to 45-50%."

## Output Structure (fixed as odds memo)

> **Source contract**: All Implied Value, Upside/Downside %, Calculation figures, and Sensitivity scenario values must carry a source anchor. The Assumptions table already has Source+Tier columns; all other numeric tables must add an Ev column.
>
> **Density table**:
>
> | Section | Mandatory source annotation | Exempt |
> |---|---|---|
> | Assumptions table | Source+Tier+Confidence for each assumption row | The assumption itself |
> | Odds memo body | Data anchor behind every % probability / upside-downside figure | Researcher probability judgment |
> | Sensitivity table | PE/EV multiple source for each scenario | — |
>
> **Completion Gate**: After writing, scan the assumptions table → each row has a source tier → references to actuals marked `[S1]`→Resources, references to external sources marked `[I#]`→Resources → `[待查]` assumptions ≤3.

```markdown
## Scenario Verdict

- One-line judgment: worth continuing / odds are so-so / not worth continuing
- Current price positioning relative to Base / Bull / Bear

## Bull / Base / Bear Table

| Case | Key Assumptions | Implied Value | Upside / Downside | Why it matters | Ev |
|---|---|---|---|---|---|
| Bull | ... | ... | ... | ... |
| Base | ... | ... | ... | ... |
| Bear | ... | ... | ... | ... |

## Current Setup

- Current market cap / current valuation anchor
- What the current market is roughly pricing in

## Assumptions

| Assumption | Value | Source | Tier | Confidence | Most Likely Wrong Because |
|---|---|---|---|---|---|---|
| TAM | $1.2B | Frost via prospectus | 1 | Medium | Frost figures in IPO prospectuses are typically 20-30% too high |
| Share | 60% | AEHR currently 100% wafer burn-in | 2 | Low | What if Teradyne/Keysight enters? |
| Margin | 25% | Current 22% + scale effect | 2 | Medium | Scale margin improvement may be 3-5% not 3% |
| PE | 40x | Semi equipment peers 2028 forward PE | 1 | Medium | If CPO is delayed, semi equipment broadly de-rates |

## Calculation

| Step | Value | Ev |
|---|---|---|
| Scenario Revenue | $720M |
| Scenario Profit | $180M |
| Scenario Market Cap | $7.2B |
| Current Market Cap | $2.9B |
| **Upside** | **+148%** |

## Sensitivity

| Variable | Bear | Base | Bull | Correlation | Ev |
|---|---|---|---|---|---|
| TAM | $0.8B | $1.2B | $1.5B | ↑TAM → ↓share pressure |
| Share | 40% | 60% | 75% | ↑share → ↓margin possible (price competition) |
| PE | 25x | 40x | 50x | ↑PE requires catalyst confirmation |

## What Matters Most

- The 1-3 most critical assumptions
- Source tier / confidence for each assumption
- Which assumption, if wrong, would visibly collapse the odds

## Research Priority

- `go alpha-thesis`
- `go market-sizing`
- `go driver-map`
- `stop`

## Reverse Check

Output only when the user asks for reverse calculation:
- To reach the target market cap, how much revenue / share / margin / multiple is needed
- Which condition is the least realistic
```

Default positioning:
- Short, hard, judgment-oriented
- Focus is on odds and assumption priority
- Not a long-form thesis
- Not a semi-model workbook

## Anti-Patterns

- ❌ Assumptions without derivation paths — where did "TAM $1.2B" come from?
- ❌ Treating independent sensitivity as real scenarios — not annotating correlations between variables
- ❌ Tier 2 assumptions without derivation process
- ❌ "Valuation flips 150%" but all assumptions are Tier 2 — pure fabrication
- ❌ Target PE without comparability justification — "40x" compared to whom?
- ❌ Most optimistic scenario upside <20% and still submitting — should just say "not worth calculating"
- ❌ Missing `What Matters Most` or `Research Priority`
- ❌ False precision — TAM $1,234M but share is a wild guess

## Judgment Criteria

After calculating, ask yourself:
- [ ] If the share assumption is proven wrong tomorrow, what happens to the upside?
- [ ] Of the three assumptions, which one, if wrong, zeros out the upside entirely?
- [ ] Is the current market already pricing in this scenario? (Look at the gap between current PE and scenario PE)
- [ ] Is this memo's next step `alpha-thesis`, `driver-map`, `market-sizing`, or stop?

## Length Benchmark

300-700 words + 1 bull/base/bear table + 1 assumptions table + 1 sensitivity table.

## Workflow Linkages

| Direction | Skill | What it gives/takes |
|---|---|---|
| Upstream | `market-sizing` | TAM |
| Upstream | `financial-data` | baseline |
| Upstream | `mechanism-insight` | share basis |
| Upstream | `driver-map` | PE anchor |
| Downstream | `candidate-screener` | quantified scenario stock screening |
| Downstream | `alpha-thesis` | bull/base/bear sizing + odds framing |


