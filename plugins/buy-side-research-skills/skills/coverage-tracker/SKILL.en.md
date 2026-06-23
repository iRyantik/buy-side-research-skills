---
name: coverage-tracker
description: Auto-maintained coverage state tracking — tier, direction, conviction, stage, next trigger. Any company researched in the workspace is covered.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Coverage Tracker

Auto-maintained coverage state at workspace root. Not portfolio positions — research state machine. Any company that has an artifact in this workspace is automatically in the table. Companion to `research-journal`: tracker manages state, journal manages earned insight.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- This skill does not call financial-data; reads and writes `COVERAGE.md`.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## Mindset

You are not "deciding who to cover" — you are "marking state." Any company that has been researched in this workspace (i.e., has any artifact under `industry/<industry>/companies/<ticker>/`) automatically belongs to your coverage. COVERAGE.md does not need to be created proactively — it is auto-created (if absent) and the entry added on the first write of a company-level artifact.

Assigning Tier is your only active decision: **some companies are worth watching weekly, others are not.** Tier is a resource-allocation decision, not a research-quality rating. It is normal for a table to have more Tier 2 than Tier 1 names.

Direction and Conviction are auto-synced from upstream skills (candidate-screener → direction, alpha-thesis → conviction) — no duplicate data entry. Stage advances automatically with research progress; only downgrades (active → monitoring → dormant) require manual confirmation.

## Trigger Scenarios

- "update coverage"
- "what's MYCR status in coverage"
- "re-rank coverage priority"
- "bump BESI to Tier 1"
- "downgrade Lianxun to dormant — CPO is way out"
- Auto-prompt to update after any deep-dive

## Auto-Create Rules

When any skill writes to `industry/<industry>/companies/<ticker>/`:

1. Check whether `COVERAGE.md` exists at workspace root.
2. If not → create empty table + add the ticker, stage=building, tier=3.
3. If yes → look up the ticker in the table.
   - Not present → add a row, stage=building, tier=3.
   - Present → do not auto-modify.

## Output Structure

`COVERAGE.md`, at workspace root:

~~~markdown
## Coverage

| Ticker | Company | Tier | Direction | Conviction | Stage | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | 1 | Long | High | active | 2026-06-01 | Q2 GT orders | Alpha thesis done; catalyst in 3M |
| BESI NA | Besi | 2 | Long | Medium | testing | 2026-05-15 | TSMC COUPE 2027 | Early thesis; waiting on TSMC |
| 688808 | Lianxun Instruments | 2 | Short | High | monitoring | 2026-05-20 | PE <200x or CPO news | Bubble watch; thesis holds |
| 300757 | Robotec | 3 | — | — | building | 2026-05-10 | ficonTEC Q orders | Too early; data not yet pulled |
~~~

## Field Definitions

| Field | Who Fills It | Values |
|---|---|---|
| **Tier** | Researcher | `1` = spend time here this week / `2` = track regularly, wait for catalyst / `3` = radar, peripheral watch |
| **Direction** | Auto (manual override) | Long / Short / — (no direction formed). Auto source: candidate-screener L/S direction, alpha-thesis thesis direction |
| **Conviction** | Auto (manual override) | High / Medium / Low / —. Auto source: alpha-thesis conviction level |
| **Stage** | Auto + Manual | `building` → `testing` → `active` → `monitoring` → `dormant` |
| **Last Review** | Auto | Date of the most recent deep-research artifact |
| **Next Trigger** | Auto | Nearest catalyst from catalyst-map |

## Thesis Stages

| Stage | Definition | Transition Trigger |
|---|---|---|
| **building** | Just appeared in workspace, information gathering in progress | Auto — any skill writes to the company directory for the first time |
| **testing** | Direction formed, under verification | stock-quickread completed + at least 1 deep-work skill (auto) |
| **active** | Conviction thesis in place, close monitoring | alpha-thesis completed (auto) |
| **monitoring** | Thesis holds but no urgency | Catalyst >6M away, or researcher manually downgrades |
| **dormant** | Thesis broken or not worth the time | Kill criteria triggered, or researcher manually downgrades |

## Anti-Patterns

- ❌ No auto-create — no table means no coverage
- ❌ Stage stuck at building forever — alpha-thesis done but stage not updated
- ❌ Every ticker is Tier 1 — no differentiation equals no resource allocation
- ❌ Direction/Conviction not auto-synced — researcher manually fills in direction already given in candidate-screener
- ❌ Tracking positions/P&L — this is not a portfolio tracker
- ❌ Not linking to research-journal — stage changed but journal has no explanation why

## Output Size Baseline

Single table, continuously updated. No dated artifact generated.

## Workflow Links

| Upstream | What Is Auto-Pulled |
|---|---|
| Any skill writing to a company directory | Auto-create entry (ticker + stage=building) |
| `candidate-screener` | Direction (L/S) + Tier reference |
| `alpha-thesis` | Conviction |
| `catalyst-map` | Next Trigger |
| `research-journal` | Stage transition rationale |

| Downstream | Scenario |
|---|---|
| Researcher | Weekly review of Tier 1 + Next Trigger to decide time allocation for the week |

## Boundaries with Adjacent Skills

- Does not do investment thesis → `alpha-thesis`
- Does not do catalyst tracking → `catalyst-map`
- Does not do portfolio tracking → this is not a positions table
