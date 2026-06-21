---
name: coverage-tracker
description: Maintain objective workspace coverage state with coverage status, monitor status, review dates, and next triggers.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Coverage Tracker

`coverage-tracker` maintains objective coverage state at the workspace root. It is not a portfolio tracker. Any company already researched in this workspace belongs in `COVERAGE.md`; this skill decides how closely it should be watched and what should trigger the next review.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- workspace `.references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.en.md` BEFORE any action. All runtime rules in that file + hooks — this capsule only states what is unique to this skill.

## Mindset

This is not a research-quality table. It is a monitoring-intensity table. The main failure mode is subjectivity: coverage status cannot be driven by "I like this company" or "conviction is high." Status must be driven by observable facts: whether the ticker is complete, whether the name was actually reviewed recently, whether a concrete trigger exists, and whether company-level artifacts exist.

`coverage-tracker` owns state. `coverage-monitor` owns delivery. The tracker decides each name's `Coverage` and `Monitor`; the monitor turns that table into daily briefs and intraday alerts.

## Trigger Scenarios

- "update coverage"
- "re-rank coverage priority"
- "is this company Core Coverage or Building Coverage now"
- "downgrade this name to daily-only"
- "update last review / next trigger"
- After any deep-dive, earnings setup, or post-earnings review

## Output Structure

Write to workspace-root `COVERAGE.md`:

```markdown
# Coverage Map

> This file is the workspace coverage source of truth. Researched companies belong here; `coverage-monitor` consumes it for daily briefs and intraday alerts.

| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | optical-module-equipment | Core Coverage | Core Watch | 2026-06-20 | 2026-07-15 Q2 results | core name |
| 6777 JP | Santec | optical-module-equipment | Building Coverage | Daily Watch | 2026-06-18 | customer order update | waiting for confirmation |
| IPO pending | Lieqi | optical-module-equipment | Radar | Daily Watch |  | IPO status watch | candidate |
```

Field rules:

| Field | Meaning |
|---|---|
| `Coverage` | `Core Coverage` / `Building Coverage` / `Radar` |
| `Monitor` | `Core Watch` / `Daily Watch` |
| `Last Review` | Date of the latest real research or material update |
| `Next Trigger` | The next one-line event that should bring the name back on screen |

> `Coverage` and `Monitor` must reflect real state fields. They must not be replaced by subjective conviction.

Upgrade rule: `stock-quickread` defaults to `Building Coverage` + `Daily Watch`; deep-work artifacts trigger `Core Coverage` review.

## Artifact / Save Policy

Write to workspace root:

```text
COVERAGE.md
```

This is a continuously maintained workspace-level memory table. No dated artifact is created.

## Boundaries With Adjacent Skills

- Does not write the thesis or variant view → `alpha-thesis`
- Does not own the catalyst chain itself → `catalyst-map`
- Does not send daily or intraday alerts → `coverage-monitor`
- Does not track positions, cost basis, or P&L → outside this system

## Anti-Pattern Self-Check

- ❌ Building `Coverage` directly from "High conviction."
- ❌ Making every name `Core Coverage`, which destroys prioritization.
- ❌ Treating `Monitor` as identical to `Coverage`, so everything gets intraday alerts.
- ❌ Marking `Daily Watch` names for intraday watch by default.
- ❌ Adding research artifacts without updating `Last Review`.
- ❌ Leaving `Next Trigger` empty while still calling the name `Core Coverage`.
- ❌ Keeping a missing-ticker row in `Core Watch`.
- ❌ Changing the table without explaining the state change in `research-journal` or adjacent research output.
- ❌ Expanding this table into a portfolio tracker.

## Output Size Baseline

- This is a single-table maintenance skill, not a long-form writing skill.
- User-facing update notes should usually stay within 5-20 lines.
- `COVERAGE.md` should remain compact; if Notes become paragraph-length analysis, the research memo is in the wrong place.
