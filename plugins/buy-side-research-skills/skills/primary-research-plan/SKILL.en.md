---
name: primary-research-plan
description: Design an expert call, channel check, survey, or fieldwork plan to verify a key investment hypothesis.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Primary Research Plan

Design an expert call, channel check, survey, or fieldwork plan to verify a key investment hypothesis.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `_shared/research-runtime.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Philosophy

The value of primary research is not "ask more people" — it is taking the most fragile, most decision-altering assumptions from desk research and testing them against the real world.

Three core questions matter more than twenty interview questions:
1. **Which hypothesis is most worth verifying?** — Not every gap needs primary research. Pick the one that would change the direction of your thesis.
2. **Who has the answer?** — Customers know demand, suppliers know capacity, ex-employees know internal operations, distributors know pricing.
3. **What result tells you to stop?** — Confirm / Mixed / Weaken / Kill — four gates, written in advance, to prevent post-hoc cherry-picking.

Compliance red lines must be flagged — do not ask about non-public orders, customer lists, undisclosed pricing, contract terms, or forward guidance. But compliance is a guardrail, not the centerpiece. The core of a good plan is research design, not a compliance checklist.

## Trigger Scenarios

- "Which people should I talk to for verifying this hypothesis"
- "Help me design an expert interview plan / channel check"
- "How do I ask customers / suppliers compliantly"
- "Which parts of this thesis need primary research"
- "Design a survey / fieldwork verification plan"

**Should NOT trigger**: verifying the credibility of a single claim → `information-impact`; decomposing drivers → `driver-map`; writing a thesis → `alpha-thesis`.

## Input Clarification Requirements

| Dimension | Meaning | Default Assumption |
|---|---|---|
| Research Subject | ticker / company / industry / segment | As stated by user |
| Hypothesis to Verify | consensus gap / driver gap / thesis assumption | Extracted from context |
| Respondent Profile | customer / supplier / competitor / ex-employee / expert | Default: multi-persona |
| Time Window | next print / 3M / 12M | Default: 12M |
| Compliance Constraints | internal restricted list / expert network rules | Default: unknown, note "follow firm compliance" |

## Mode A: Standard Plan

Used to turn multiple key hypotheses into a complete fieldwork plan.

### Output Structure

```markdown
## Verdict

[2–3 sentences: the most worth-verifying hypothesis, which persona to target, what result would change the decision]

## 1. What to Verify

| Hypothesis | Existing Evidence | What's Missing | What Decision It Changes | Priority |
|---|---|---|---|---|
| [hypothesis] | [existing source] | [what information fills the gap] | [thesis / model / sizing / ranking] | High / Med / Low |

> Pick 1–2 High-priority items to develop in §2–§4. Medium and low priority items are marked "follow-up."

## 2. Who to Ask

| Persona | What They Know | How Many | Why Them |
|---|---|---|---|
| [customer / supplier / ex-employee / expert / distributor] | [process / historical / directional / aggregated] | [n≥3] | [which §1 hypothesis this verifies] |

## 3. How to Judge

| Result | What Evidence | What to Do |
|---|---|---|
| ✅ Confirm | [specific threshold] | advance thesis / model |
| ⚠️ Mixed | [not clear enough] | add one more round / cross-check |
| ❌ Weaken | [contrary evidence] | lower conviction / revise |
| 💀 Kill | [hypothesis directly invalidated] | drop thesis |

**Triangulation**: [cross-verify the same claim from 2–3 different personas or public sources]

## 4. How to Ask

### [Persona A]

Must-ask (2–3 items):
1. [open-ended, non-leading question]
2. [...]

Red lines: do not ask about [non-public orders / customer names / pricing / contract terms / guidance / confidential pipeline]. Reword as [public / historical / directional proxy].

### [Persona B]

[same structure]
```

### Mode A Length: 1000–1600 words

---

## Mode B: Expert Call Guide

Used for a single expert call. Output compressed to 600–1000 words — §1 one-line hypothesis + §2 one persona + §3 decision gate + §4 three to five must-ask questions + red lines. No triangulation section.

## Mode C: Channel Check / Survey

Used for bulk verification via customers / suppliers / distributors. Builds on Mode A with an added sample plan (target n≥10, persona split, geographic split) and bias controls (don't only look at happy customers / recent buyers). Length 800–1400 words.

## Artifact / Save Strategy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

If path is unclear → agent auto-creates per policy baseline §11.

## Source Contract

- Every row in the hypothesis register's "existing evidence" column must be tagged `[S#](url)` or `[I#](url)` or `[待查]` (to be checked).
- Every source idea in the triangulation plan must note the source type (persona / public / filing / expert).
- Numbers referenced in expert interview questions → cite the source (which report / filing contains this number).

**Completion Gate**: after writing, scan the hypothesis register → every row's Source column must be non-empty → if `[待查]` exceeds 50% of rows, flag coverage <50%.

## Anti-Pattern Checklist

- ❌ A long question list but no hypothesis register — unclear what each question is verifying.
- ❌ No decision gate — every outcome is treated as "interesting."
- ❌ Only one type of respondent, no triangulation.
- ❌ Questions are leading, nudging the expert to confirm the thesis.
- ❌ Hinting at soliciting MNPI (orders, pricing, customer lists, contracts, guidance).
- ❌ Writing a planned call as if it were actual expert feedback.
- ❌ Using small-N anecdotes to directly overturn or confirm a thesis.
- ❌ Wrong persona chosen — interviewed 10 experts but none could answer the core hypothesis.

## Length Baseline

| Mode | Word Count |
|---|---|
| Standard | 1000–1600 |
| Expert Call | 600–1000 |
| Channel Check | 800–1400 |

Below the lower bound typically means a missing hypothesis or decision gate; above the upper bound means you are writing an execution handbook.
