---
name: earnings-setup
description: Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Earnings Setup

Prepare for or react to earnings and decide whether thesis drivers or model assumptions changed.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data pipeline**: call `/financial-data --lite <ticker>` to fetch three statements + market snapshot. Trust its results and pull data directly from `actuals-resolved.json`.
- **Data verification**: Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证]). See §3.2.
- **Actuals-only**: implied move, short squeeze score, and any ratio derived from financial statements use actuals-resolved.json.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

## The Mindset

Earnings are not for "catching up on the company." The buy-side reads earnings to answer two questions:
- Are my thesis assumptions still intact?
- Does the market reaction give me an opportunity (long / short)?

The sell-side preview template: consensus numbers + historical beat/miss probabilities + "things to watch." **None of it is useful** — it is all public information with zero alpha.

A good setup focuses on just 2-3 key observation points — for example, GE Vernova's H2 services orders growth and gas turbine backlog conversion. Those two numbers tell you whether the margin mix is improving, which is far more useful than EPS beat/miss. List your thesis assumptions before the print; 10 minutes after earnings you will know whether the thesis is still alive.

---

## A. Pre-Earnings Setup (if the user is asking for a preview)

### 0. Primitive Readiness (first confirm what this print is about)

Before earnings you cannot just list consensus. First confirm whether the key observation points for this print require unpacking mechanisms or drivers.

| Check Item | Pass Criteria | Action if Not Passed |
|---|---|---|
| KPI mechanism meaning | The industry mechanism, equipment chain, capacity units, or process flow behind the KPI to watch is clearly understood | Handoff to `mechanism-insight` first |
| KPI / segment definition | Definitions of KPIs, segments, backlog, orders, book-to-bill, and their revenue recognition relationships are clear | Handoff to `driver-map` first |
| Buy-side bar | The actual buy-side expectation can be mapped to revenue / margin / backlog / price-volume-mix drivers | Handoff to `driver-map` first |
| Thesis linkage | The 3 observation points for this print can be mapped to assumptions or catalysts in `alpha-thesis` | If the issue is unclear research direction, trigger `next-step` |

If not passed, output a minimal handoff block first:

```markdown
## Primitive Handoff Required

- Blocker: [which KPI / mechanism / driver has not been unpacked]
- Why it blocks earnings setup: [which section of the buy-side bar / key threshold / decision tree it affects]
- Handoff: `mechanism-insight` / `driver-map`
- Inputs needed: [filing / call / KPI definition / segment data that needs to be supplemented]
```

## Implied Volatility & Pressure

| # | Calculation | Formula | Input Source |
|---|---|---|---|
| 1 | Implied Move | ATM straddle price ÷ stock price | MKT — options market; use historical earnings move when A-share options are sparse |
| 2 | Historical Earnings Move | Average absolute return on earnings day ±1 day over the last N prints | MKT — must note lookback count |
| 3 | Short Interest | Short shares ÷ float market cap | MKT — available for HK/US equities; A-share opaque |
| 4 | Short Squeeze Score | Short Interest ÷ Avg Daily Volume | MKT — high = forced covering on a beat |

### 1. Current Setup (how the market is pricing this print)

Present in structured form; all numbers must include source and **as-of timestamp**:

| Dimension | Current Value | Interpretation | Ev |
|---|---|---|---|
| Implied move | ±7% | Options-implied volatility for this print | [S1](https://example.com/options-implied-move) |

Body claim example: `Options imply a 7.5% move into earnings, above the trailing eight-quarter realized median of 5.2%. [I1](https://example.com/options-implied-move)`
| Price vs sector 1-3M pre-earnings | +12% vs XLE +3% | Outperformance → buy-side expectations already elevated | [I1](https://example.com/price-vs-sector) |
| Short Interest | 4.5% of float | Absolute level + last 1M trend | [I2](https://example.com/short-interest) |
| Borrow rate | 35bps | Whether cheap (no short pressure) | [I3](https://example.com/borrow-rate) |
| Sell-side revision breadth (last 30 days) | 7 up / 1 down | Upward revision momentum → already priced | [I4](https://example.com/revision-breadth) |

### 2. Sell-Side Numbers vs Buy-Side Bar
- Sell-side consensus (revenue, gross margin, EBITDA, EPS, key KPIs)
- But the buy-side bar is usually different from sell-side — infer it from:
  - Pre-earnings price action (strong outperformance → buy-side bar already above consensus)
  - Whether peers that have already reported raised sector expectations
  - Whether sell-side above-consensus notes have circulated in the last 1–2 weeks
  - Options market skew (put / call IV spread)
- **Explicitly give the "buy-side actually-expected number" range** — this is the highest-alpha section of the setup

### 3. The 3 Things You Really Need to Listen For / Watch (specific to KPI or metric)
Not "watch downstream demand" — that is too vague. Must be specific numeric thresholds with sourced baselines:

| KPI | Last Baseline + Ev | Key Threshold This Print | Meaning |
|---|---|---|---|
| Permian rig count 2H guidance | 12 rigs [S1](./_cache/sources/permian-rig-guidance.md) | ≥ 14 → accelerating; < 12 → contracting | Determines capex assumption in thesis |

Body claim example: `Management kept FY26 revenue guidance unchanged but narrowed the margin range by 50 bps. [S1](./_cache/sources/company-annual-report.md)`
| Buyback pace | Q2 completed $300M [S1](./_cache/sources/q2-2024-cashflow.md) | Whether full-year framework raised above $1.5B | Determines shareholder return willingness |
| OpEx per BOE | $9.5 [S2](./_cache/sources/q2-2024-supplementals.md) | < $9 → cost control; > $10 → inflation runaway | Margin sensitivity |

Every single one must have a **concrete numeric threshold**, not "watch the trend." Baseline numbers must be sourced to the specific location in the last call / 10-Q.

### 4. Asymmetric Setup Judgment
Based on 1–3, the risk/reward of this print for the **current position**:
- Implied move 5%, but you think upside > 12%, downside ~ 5% → asymmetric long setup, can add / buy OTM calls
- Implied move 10%, expected in-line, setup already priced → hold / trim
- Clear outperformance vs sector + buy-side bar far above sell-side → asymmetric short / reduce
- **Must give an explicit pre-print action recommendation** — not "hold and observe"

### 5. Pre-Print Decision Tree (must be written down in advance)

| Scenario | Number Performance | Decision |
|---|---|---|
| Beat & raise | EBITDA > +5% & full-year guidance raised > 3% | Add X% |
| Beat & maintain | EBITDA > +5% & guidance maintained | Hold |
| Miss with cause | EBITDA -5% but attributable to [one-off] | Watch after-hours reaction, add on pullback to [price level] |
| Miss & cut | EBITDA -10% & guidance cut | Reduce 50%, reassess thesis |
| Thesis kill | KPI X hits [specific threshold] | Close position |

**Write this table before earnings; during earnings, just execute.** This is to fight the brain being flooded by noise on earnings day.

---

## B. Post-Earnings Quick Read (if the user is asking for a post-mortem)

### 0. Primitive Readiness (first determine what kind of surprise this is)

After earnings, first determine whether the surprise is an ordinary beat / miss, or whether it exposes a mechanism or driver definition issue. Do not give a thesis health assessment when definitions have not been unpacked.

- If the company dodged key KPIs, changed disclosure definitions, re-segmented, or backlog / orders decoupled from revenue, trigger `driver-map` first.
- If new information involves equipment chains, engineering constraints, capacity units, process flows, or know-how gaps, trigger `mechanism-insight` first.
- If it is just an ordinary deviation of actuals vs preset thresholds, proceed with the post-print quick read.

### 1. One-Line Characterization
Beat / miss / mixed? Price reaction confirming / surprising?

There are 4 combinations of number vs reaction, each with different meaning:
- **Beat + up** → standard
- **Beat + down** → buy-side bar was already above sell-side, warning signal (crowded positioning already priced)
- **Miss + down** → standard
- **Miss + up** → expectations were already more pessimistic, possible bottom (watch for contrarian add opportunity)

### 2. Key KPI Actuals vs Setup Checklist (direct comparison)
For each of the 3 observation points listed before earnings (see setup section 3 above), compare **actual number** vs **expected**. Items omitted or dodged should be flagged separately.

### 3. Thesis Assumption Check
Go back to `alpha-thesis` section 8 "What I assumed that could be wrong" — for each assumption: does this quarter's data **support / weaken / neutral**?

This section connects to thesis work — it is not about reading an earnings report in isolation, but checking the health of the existing thesis.

### 4. Catalyst Status Update
Catalysts listed in the original thesis (see `alpha-thesis` section 4):
- Those that have occurred → what was the outcome, impact on thesis
- Those not yet occurred → any change in timeline / probability

### 5. Decision (execute per pre-print decision tree)
Execute the preset decision. If the print produced information **completely unanticipated** (a genuine surprise), explain separately and give a new decision; also reflect on why this branch was not considered during the setup phase.

### 6. Research Update / Follow-up Triggers

Post-print must explicitly state whether the research judgment has changed, not just "continue to observe":

| Output Field | Allowed Values | Description |
|---|---|---|
| `research_update` | `none` / `refresh_required` / `thesis_weakened` / `thesis_strengthened` | Whether research views or related thesis need to be updated or rewritten |
| `model_update` | `no` / `actuals_only` / `driver_change` / `assumption_change` | Whether `3-statement-model / dcf-model / comps-analysis / model-update` needs to be triggered |
| `journal_handoff` | `no` / `research-journal` / `boss-brief` | Whether a judgment increment worth crystallizing or showing the boss has been formed |
| `next_step_trigger` | `no` / `yes` | Whether a high-value question has been exposed that needs `next-step` to unpack further |
| `mechanism_map_trigger` | `no` / `yes` | Whether `mechanism-insight` needs to be triggered due to equipment chains, engineering constraints, capacity units, process flows, or know-how gaps |
| `driver_map_trigger` | `no` / `yes` | Whether `driver-map` needs to be triggered due to changes in segments, KPI definitions, backlog, orders, margin, price / volume / mix |

If earnings expose strange signals in disclosure definitions, drivers, margins, or source conflicts, call them out directly per the Senior Analyst Radar. If the surprise is a mechanism / know-how issue, trigger `mechanism-insight` first; if the numbers change revenue / margin / backlog / price-volume-mix definitions, trigger `driver-map` first; if already in model-update territory, trigger `3-statement-model / dcf-model / comps-analysis / model-update`.

---

## Artifact / Save Strategy

Write to industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

If path is unclear → agent auto-creates per policy baseline §11.

## Source Contract

**Density table**:

| Section | Source Mandatory | Exemption |
|---|---|---|
| Consensus vs buy-side bar | Source for consensus numbers (provider+as-of), basis for buy-side bar | Researcher's bar inference itself |
| Pre-print decision tree | Source for threshold numbers in each scenario (guidance/history/peer) | — |
| Historical reaction patterns | Actual vs consensus specific numbers+source for each beat/miss | — |

**Completion Gate**: after writing, scan consensus numbers → every number has provider+as-of → buy-side bar has reasoning chain → `[待查]` ≤3 → Resources expanded.

## Anti-Pattern Self-Check

- ❌ Setup only lists consensus numbers, no buy-side bar inference → worthless
- ❌ "Things to watch" are "watch downstream demand" "watch capex guidance" — no specific thresholds → untradeable
- ❌ No pre-print decision tree → waiting until after the reaction to think is already too late
- ❌ Post-print is a line-by-line number recap → this is sell-side journaling, rewrite
- ❌ Post-print does not return to specific thesis assumptions → did not connect to prior work
- ❌ Post-print does not give an explicit position decision → just narrated the earnings, produced no decision
- ❌ Setting thresholds without understanding the KPI's underlying mechanism / equipment chain → trigger `mechanism-insight` first
- ❌ Updating thesis directly when segment, backlog, orders, price / volume / mix definitions have changed → trigger `driver-map` first

**Source-specific**
- ❌ Consensus numbers lack provider (Visible Alpha / Bloomberg) and as-of timestamp → data may be stale, must supplement
- ❌ Implied move / IV / SI data lack timestamp annotation → these are minute-level-changing data, must annotate
- ❌ KPI baseline ("last time they said 12 rigs") lacks specific source location in last call / filing → supplement

## Length Benchmark

- Pre-print setup: 500–900 words
- Post-print read: 400–700 words

If it is much longer, you are not capturing what matters.

## Appendix: Financial Data

python _scripts/financial-data/actuals-to-appendix.py <TICKER>

## Appendix: actuals-resolved.json

Complete field inventory -> `references/actuals-data-catalog.md`.

Structure: `meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`.

Consumption rules: read actuals first -> source_map to pull [S#]/[I#] labels (do not write [actuals]) -> ratios use only actuals real values (never forward estimates).
