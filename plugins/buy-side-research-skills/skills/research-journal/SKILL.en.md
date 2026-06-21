---
name: research-journal
description: Summarize completed research into durable topic notes and boss brief outputs.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Research Journal

Summarize completed research into durable topic notes and boss brief outputs.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in workspace `.references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

Crystallize cognitive increments that have already been researched, clarified, and can change subsequent judgment into topic memory. **The core value is not recording the process** — it is preserving the judgments, mechanisms, drivers, source maps, open questions, and boss-ready conclusions the researcher has already earned, so future research can resume or the output can be transferred to the PM.

If the output turns into a transcript, a raw reminder, an unverified inspiration warehouse, or writes unsourced driver/mechanism guesses as settled fact, this skill has failed.

## Mindset

`research-journal` is the memory layer of the v3 journal-first system. It only accepts incremental insights after a round of research is complete. It does not help the user "think about the next step," nor does it store every anomaly as status.

Journal entries should read like notes a serious researcher writes to their future self: conclusion-first, sources clear, preserving disputes and unresolved questions, but never rehashing the conversation process. The Boss Brief is a high-density transfer for the PM/boss — not a shorter version of the journal, but a memo that compresses the most important judgments into something discussable.

## Trigger Scenarios

### Mode A: Private Research Journal

- "Summarize this round of research"
- "Summarize this round of industry research"
- "Summarize this round of topic research"
- "Write into journal"
- "research journal"
- "Organize this topic"
- "Crystallize this company / industry / theme research"

### Mode B: Boss Brief

- "Make a version for the boss"
- "Version for the PM"
- "boss brief"

## Input Clarification Requirements

| Dimension | Meaning | Default Handling |
|---|---|---|
| **topic path** | Dated Markdown file under topic root | When user does not provide a path, agent auto-creates directory per policy baseline §11 |
| **Research object** | Theme / company / event / peer set / thesis | Infer from context; ask 1 clarifying question if unclear |
| **Write purpose** | journal / Boss Brief / index update | Default to journal; use Boss Brief when user mentions PM / boss |
| **Source status** | sourced / mixed / unsourced | When mixed, write only sourced conclusions; unsourced stays as open question |
| **Research maturity** | noticed / researched / settled / disputed | Only researched or above can be crystallized |
| **Upstream artifacts** | mechanism-insight / driver-map /  / peer / thesis / model | First assess whether already digested; do not mechanically copy-paste |

If the path is missing but the user explicitly requests a file write, first suggest a path and indicate confirmation is needed; if the user only wants a conversation summary, do not write to disk.

## Earned Insight Gate

Only research that has already crossed the earned-insight and topic-index boundaries should land here. The detailed gate and index-only legality are enforced by workspace hooks; use this section only to decide whether a conclusion is mature enough to journal, brief, or leave as a follow-up.

## Mode A: Private Research Journal

### Step 1: Write Judgment

First produce a short confirmation table to avoid writing everything in:

| Research question / insight | Write depth | Value tags | Ev | Judgment rationale | Write location |
|---|---|---|---|---|---|

Depth levels:
- `skim`: one-sentence conclusion + why not digging deeper for now.
- `standard`: conclusion + key sources / data + research implications.
- `deep`: mechanism, drivers, source conflict, key data, residual questions all researched and clear.

Value tags:
- `data-anchor`
- `glossary`
- `mechanism`
- `market-structure`
- `model-driver`
- `alpha-view`
- `source-map`
- `open-question`
- `research-edge`
- `disclosure-anomaly`
- `source-conflict`
- `know-how-gap`
- `market-misread`

### Step 2: Write research-journal.md

Write path:

```text
industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-research-journal.md
```

`research-journal` has `artifact_policy.naming_mode = plain`. Earned memory continues to use `YYYY-MM-DD-<artifact>.md` by default; the Boss Brief also maintains the same dated-deliverable convention — qualifiers are not the default naming approach.

The Journal does not use a rigid template, but must include:
- This round's research map: which questions were researched, not what was discussed.
- Conclusion-first: every section opens with the conclusion.
- Source anchors: sources / as-of for key facts, numbers, KPIs, quotes.
- Research implications: what changed in business understanding, drivers, market framing, or subsequent priorities.
- Unresolved: parts not yet clarified that do not contaminate the current conclusions.

## Mode B: Boss Brief

The Boss Brief is a high-density transfer for the PM / boss, not a shorter version.

Write path:

```text
industry/<industry>/companies/<ticker>/[YYYY-MM-DD]-boss-brief.md
```

Before writing, confirm or extract from materials:
- Core conclusion.
- 3–5 final takeaways.
- Must-retain key data / sources / as-of.
- Biggest debate / variant view.
- Implications for model, thesis, peer framing, or  research priority.

The Boss Brief may use these headings, but do not mechanically cram them all in:
- `Conclusion`
- `Takeaways`
- `Key Data`
- `Debate`
- `Implications`
- `What Would Change Our Mind`

## Mode C: Topic Index Update

The topic `index.md` is an evolving map, not a status warehouse. Only maintain the current topic's research thread:
- Researched questions.
- Each session link.
- Current high-confidence conclusions.
- Unresolved open questions.
- Which sessions produced a Boss Brief or key driver / mechanism insight.

Write path:

```text
industry/<industry>/companies/<ticker>/index.md
```

Do not backfill history; do not forcibly reconstruct all old sessions. Only update the incremental contribution of this session to the topic map.

Recommended structure:

```markdown
# [Topic]

## Current Map

- [Current top 3–5 research judgments / open questions]

## Sessions

| Date | Session | What changed | Links |
|---|---|---|---|

## Open Questions

- [Questions still needing research]
```

## Primitive Consumption Rules

### Consuming `mechanism-insight`

Only write into the journal when the mechanism conclusion, key terminology, process / value-capture logic, source / as-of, and residual uncertainty are all clear.

If it is only "looks like it might be mechanism X," write as:
- `Working hypothesis`, tagged `[Needs verification]`; or
- handoff back to `mechanism-insight`.

### Consuming `driver-map`

Only write into the journal when the reported bucket, business reality, model driver, KPI / source / as-of, and confidence are all clear.

If the driver remains Low confidence, unknown, peer proxy, or researcher assumption, do not write as settled business reality; only write as open question, sensitivity, or handoff back to `driver-map`.

### Consuming `information-impact`

Only `Confirmed`, `Likely`, or clearly tagged `Plausible but unconfirmed` claims may enter the journal. `Unsupported` / `Contradicted` may be written into the source-map or as a false lead, but do not expand into research implications.

## Output Structures

### Private Research Journal

```markdown
# Research Journal — [topic / session]

## This Round's Research Map

- [Research question 1] → [Current conclusion]
- [Research question 2] → [Current conclusion / open]

## [Research question / insight]

**Conclusion First**
[1–2 sentences clearly stating the earned insight, e.g.: `Changes in order mix explain margin inflection better than total backlog; FY25 service-order share rose to 42%. [S1](./_cache/sources/company-annual-report.md)`]

**Source Anchors**
- `[S1](./_cache/sources/company-annual-report.md) = [source title] | as-of/filed [date]`

**Why It Matters**
- [What changed in business substance / driver / market framing / peer group / research priority]

**Unresolved**
- [Parts not yet clarified that do not contaminate the current conclusions]
```

### Boss Brief

```markdown
# Boss Brief — [topic / session]

## Conclusion

[One-sentence core judgment]

## Takeaways

1. [...]
2. [...]
3. [...]

## Key Data / Source Anchors

- [...]

## Debate / Variant View

- [...]

## Implications

- [...]
```

### Topic Index Update

```markdown
## Sessions

| Date | Session | What changed | Links |
|---|---|---|---|

## Open Questions

- [...]
```

## Artifact / Save Policy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

Path unclear → agent auto-creates per policy baseline §11.

## Anti-Pattern Self-Check

#
## Length Guidelines

- Write judgment table: 100–250 words + 1 table.
- Private Research Journal: 800–1,800 words; below 500 words usually means insufficient source / implication crystallization; above 2,200 words usually means it has become a transcript.
- Boss Brief: 500–1,200 words; below 400 words usually means it is just a summary; above 1,500 words usually means the PM-transfer density is lost.
- Topic Index Update: 100–500 words; above 700 words usually means journal content has been stuffed into the index.
- Handoff block: 150–350 words; only explain why it cannot be crystallized now and which skill it should hand off to.
