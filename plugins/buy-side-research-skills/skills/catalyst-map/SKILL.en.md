---
name: catalyst-map
description: Full timeline catalyst chain with probability estimation, asymmetric payoff, and time density analysis.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Catalyst Map

Map every catalyst on a timeline with probability, magnitude, direction, and payoff ratio. Not a calendar — a probability-weighted payoff matrix that tells you which events are worth researching and which are noise.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Mental Model

A good catalyst map does not answer "what's coming up next" — it answers "which events, if they happen, would change the thesis, and which would be irrelevant even if they occur." Most catalysts are asymmetric — miss drops 5%, hit gains 20%. Catalysts with payoff ratio >3x are where you allocate research resources. Catalysts with ratio <1x are not worth your time tracking.

The second pitfall: mistaking a time point for a catalyst. "Q2 earnings" is not a catalyst; "Q2 earnings reveal GT orders >SEK 350M" is. The agent must refine every event into a specific, verifiable number.

The third pitfall: probabilities are not precise — but they are not pulled out of thin air either. There are three anchors: historical base rate, current progress proxy, and external verification signals. A good catalyst map tells you "which anchor was used to derive this probability."

## Trigger Scenarios

- "Draw the catalyst timeline for xxx"
- "What catalysts does xxx have"
- "What events will affect the thesis over the next 12 months"
- "Which catalysts are most worth tracking"

## Methodology

### Probability Estimation (Three Anchors — At Least One Must Be Labeled)

| Anchor | Approach | Applicable To |
|---|---|---|
| **Historical Base Rate** | Hit rate of similar past events for the company / peer group | Recurring events (quarterly beats, product delivery milestones) |
| **Progress Proxy** | Wording changes in announcements, timeline adjustments, supplier/customer signals | One-off events (CPO mass-production verification) |
| **External Verification** | Industry conference demos, customer capex guidance, supply chain leaks | Technology milestones, orders, customer onboarding |

### Upside/Downside Asymmetry

| Concept | Explanation |
|---|---|
| **Payoff Ratio** | = magnitude on hit / magnitude on miss (absolute values). Ratio >3x → highest tracking priority |
| **Noise** | Hit gains 5%, miss drops 5% → ratio 1x → not worth tracking |

### Time Density

Catalysts are unevenly distributed. High density during earnings season, sparse otherwise. Reallocate resources during high-density periods.

## Output Structure

> **Source contract**: Every column involving valuation, probability, scoring, payoff, or market-size figures in the tables below must carry a source anchor per row ([S#](url) or [I#](url)).
>
> **Density table**:
>
> | Section | Mandatory source labeling | Exempt |
> |---|---|---|
> | Catalyst Timeline table | Probability / magnitude / Payoff / Base rate per row | Catalyst name itself |
> | Price anchors | price target, current price, 52w range | — |
> | Event odds memo | date/source/expected value per event | Directional judgment |
>
> **Completion Gate**: After writing, scan every row → every row has [S#]/[I#] or `[待查]` → `[待查]` ≤5 → Resources section must expand all sources.

```markdown
## Catalyst Timeline

| Time | Catalyst | Probability | Direction | Magnitude | Payoff Ratio | Anchor | Thesis Impact | Ev |
|---|---|---|---|---|---|---|---|---|
| 2026 Q3 | Q2 GT orders >SEK 350M | 40% | ↑ | +15% | 3.0x | Base rate: beat in 2 of last 4Q | Validates 1.6T upgrade driver |
| 2026 Q4 | Nvidia Rubin includes CPO | 25% | ↑ | +25% | 5.0x | Proxy: architecture leak signals | CPO roadmap validation |
| 2027 H1 | Leiki patent loss | 30% | ↑ | +20% | 2.0x | Base rate: plaintiffs ~60% | MRSI competitive clearance |
| 2026 H2 | FPGA shortage easing | 50% | ↑ | +5% | 1.0x | Proxy: lead time shortening | Bottleneck removed, already priced in |
| 2026 Q4 | Semi cycle downturn | 20% | ↓ | -15% | — | Base rate: cycle avg | Industry-wide de-rate |

## Payoff Matrix

| Rank | Catalyst | Payoff Ratio | Weighted Impact | Ev |
|---|---|---|---|---|
| 1 | Rubin includes CPO | 5.0x | +6.3% (25% × 25%) |
| 2 | GT >350M | 3.0x | +6.0% (40% × 15%) |
| 3 | Leiki loss | 2.0x | +6.0% (30% × 20%) |

## Visual

**Timeline** (ASCII):

    2026 Q3 ─── Q4 ─── 2027 H1 ─── 2027 H2
   │         │         │           │
   │ GT ▲    │ Rubin ▲│ Leiki ▲   │ COUPE?
   │ 40%     │ 25%     │ 30%       │
   │ +15%     │ +25%    │ +20%      │
   │         │         │           │
            │ FPGA ▼  │
            │ 50%     │ ← noise
            │ +5%      │

    Density: Q3-Q4 = HIGH (3 catalysts in 6M) — allocate research time.
```

## Anti-Patterns

- ❌ "Q2 earnings" treated as a catalyst — refine to a specific number
- ❌ No probability — "might go up" is not a catalyst
- ❌ Upside/downside asymmetry not labeled
- ❌ Only upside, no downside
- ❌ Probability anchor not labeled — where did 40% come from
- ❌ Not linked to thesis
- ❌ All "if...then..." — at least half should have a progress proxy
- ❌ Payoff ratio not differentiated — all equally weighted
- ❌ Downside catalysts also labeled with "payoff ratio" — for downside, talk about severity

## Length Baseline

500-800 words + 1 timeline table + 1 payoff matrix + ASCII timeline.

## Workflow Linkages

| Upstream | What to pull |
|---|---|
| `consensus-map` | What is already priced in |
| `financial-data` | Historical beat rate, earnings dates |
| `earnings-setup` | Single pre-print bar |

| Downstream | Scenario |
|---|---|
| `alpha-thesis` | catalyst → conviction |
| `candidate-screener` | §6 catalyst calendar |
| `post-earnings-quick` | Verify whether catalyst triggered |

## Boundaries with Adjacent Skills

- Do not do earnings setup → `earnings-setup`
- Do not do thesis → `alpha-thesis`
- Do not do market expectations → `consensus-map`

