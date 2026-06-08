---
name: post-earnings-quick
description: Post-earnings 5-min verdict — three-dimension beat/miss judgment with thesis impact decision.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Post Earnings Quick

Five-minute post-print verdict. Not a full review — a rapid three-dimension check: did they beat or miss versus the pre-print bar? Did guidance move? Does the thesis still hold?

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Philosophy

The first thing after earnings is not reading the release — it is finding the benchmark. A beat/miss judgment without a benchmark is noise. Benchmark priority: earnings-setup pre-print bar → consensus range → prior year same-quarter trend. If no benchmark is found, say outright "no benchmark, no judgment."

Second trap: beat by 2% but guidance came down — good or bad? Mechanically judging beat=good misses the most important signal. **Three-dimension judgment**: actuals vs bar, guidance vs prior guidance, quality of beat (one-time gain or recurring improvement).

Hard cap of 500 words. This is not deep analysis — it is a rapid thesis directional check. You should produce a verdict within 5 minutes.

## Trigger Scenarios

- "xxx reported earnings, quick look"
- "MYCR just reported Q2, how is it?"
- "What does this quarter's earnings mean for the thesis?"

## Benchmark Priority

```
1. Most recent earnings-setup artifact for the same ticker (pre-print bar is most accurate)
2. Consensus range (from /financial-data market_data or WebSearch)
3. Prior year same-quarter growth trend (weakest proxy — unreliable if prior year had COVID or M&A)
4. None available → "No benchmark; no directional judgment; list numbers and guidance changes only"
```

## Three-Dimension Judgment

| Dimension | Question | How to Assess |
|---|---|---|
| **Actuals vs Bar** | Revenue/EPS beat or miss? | 2%+ = beat, -2% = miss, between = in-line |
| **Guidance** | Guidance vs prior guidance / consensus | Guidance raise > actuals beat. Guidance cut > actuals beat — guidance about the future matters more than past numbers |
| **Quality** | Is the beat one-time or recurring? | Tax benefit, asset sale, FX gain = one-time. Organic growth beat, margin expansion from scale = quality |

Synthesis: If revenue beat but guidance cut → thesis needs re-examination. If missed but guidance raised (cost cutting taking effect, order pipeline accelerating) → thesis may strengthen.

## Output Structure

```markdown
## Verdict

**Beat — thesis unchanged** (or other combination)

| Metric | Actual | Pre-Print Bar | Consensus | Beat/Miss |
|---|---|---|---|---|
| Revenue | $1.2B | $1.15B | $1.18B | Beat +4% |
| EPS | $0.45 | $0.42 | $0.43 | Beat +7% |

## Guidance

| Guidance | Prior | Consensus | Direction |
|---|---|---|---|
| FY revenue | $5.0-5.2B | $4.8-5.0B | $5.1B | Raised |

## Quality Check

- Revenue beat: +4%, driven by GT orders +8% QoQ — organic, recurring
- EPS beat: +7%, FX tailwind ~2% — partially non-recurring
- No one-time items of concern

## Thesis Impact

**Thesis: unchanged.** 1.6T upgrade driver intact. GT orders beat supports thesis. Guidance raise consistent with our base case.

**Next**: update coverage-tracker. No need to re-do stock-quickread. Monitor next catalyst: Q3 GT orders (Oct 2026).

> Hard cap: 500 words. Do not write a full earnings review. If you need more space, handoff to `stock-quickread` or `driver-map`.
```

## Anti-Patterns

- ❌ Asserting beat/miss without a benchmark — must locate the bar
- ❌ Judging beat/miss on actuals alone without looking at guidance — guidance matters more
- ❌ Not distinguishing one-time vs recurring
- ❌ Exceeding 500 words — turning into a full review
- ❌ Not stating thesis status — "needs further observation" is not a judgment
- ❌ Not updating coverage-tracker

## Length Benchmark

Hard cap of 300–500 words. If it exceeds that, you are doing it wrong.

## Workflow Linkage

| Upstream | What to Pull |
|---|---|
| `earnings-setup` | pre-print bar |
| `financial-data` | actuals + consensus |
| `consensus-map` | if no earnings-setup available |

| Downstream | Scenario |
|---|---|
| `stock-quickread` | thesis needs full review |
| `coverage-tracker` | update stage/priority |
| `driver-map` | guidance changes driver assumptions |

## Boundaries with Adjacent Skills

- Do not do pre-earnings prep → `earnings-setup`
- Do not do deep earnings analysis → `stock-quickread`
- Do not rewrite the thesis → `alpha-thesis`
