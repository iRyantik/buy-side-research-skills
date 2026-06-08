---
name: next-step
description: Choose the highest-value next research question when a thread feels stuck or incomplete.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Next Step

Choose the highest-value next research question when a thread feels stuck or incomplete.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in workspace `.references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

Compress the current research sticking point into a single highest-leverage question. **The core value is not task management** — it is judging which question is most likely right now to change business substance, model drivers, market expectations, peer framing, or research priorities, and then deciding whether to pursue it directly or hand off to an upstream primitive first.

If the output turns into a long task list, generic "look at financials / look at the industry / look at valuation," or forces a next step when the mechanism / driver gap has not been disentangled, this skill has failed.

## Core Philosophy

`next-step` is a research bottleneck router, not a research executor. It serves the `Better AI Question` in the v3 core loop: turning vague unease, stuckness, or the urge to dig deeper into a single question that can advance the judgment framework.

The best next step is typically small but high-leverage: it is not "gather more information," but rather can verify whether a key mechanism, driver, source, peer convention, or consensus framing has been misread. Default to giving only one question, because too many questions push the researcher back into information overwhelm.

## Trigger Scenarios

### Mode A: Direction Coach

- "How should I research this next?"
- "How do I dig deeper?"
- "next step"
- "I'm stuck."
- "What's most worth chasing here?"
- "How do I turn this into a better AI question?"

### Mode B: Research Audit

- "What feels off about this section?"
- "What's wrong with this research?"
- "Help me retrace this."
- "Help me audit this research."

## Input Clarification Requirements

| Dimension | Meaning | Default Handling |
|---|---|---|
| **Research Object** | Ticker / company / industry mechanism / event / a piece of research material | If the user didn't provide an object and context is insufficient to infer, ask one clarification question first. |
| **Current Artifact** | Quickread / thesis draft / peer compare / earnings note / raw idea | Default: treat it as an unfinished research fragment. |
| **User Objective** | Continue digging / audit / rewrite an AI question / select a skill route | Default: output a single highest-value question. |
| **Fact Quality** | Sourced / unsourced / mixed / stale | Unsourced facts are treated as hypotheses only, never written as facts. |
| **Anomaly Type** | Mechanism / driver / source / peer / market framing / catalyst | Classify first, then decide whether to hand off. |
| **Save Requirement** | Conversation output / handoff to `research-journal` | Default: do not save, do not create files. |

If missing information would not change the next-step judgment, do not ask follow-ups; go straight to the minimal next step and mark uncertainties explicitly.

## Primitive Preflight

Before producing formal output, do an internal classification. If the current bottleneck matches a hard trigger in the table below, do not force a generic next step.

| Bottleneck Type | Diagnostic Criteria | Next Step |
|---|---|---|
| **mechanism / know-how gap** | Industry mechanism, engineering principles, equipment chain, process flow, terminology, or value capture is unclear | Hand off to `mechanism-insight` first. |
| **driver / disclosure gap** | Revenue, margin, backlog, price-volume-mix, KPI definitions, reported buckets, or disclosure conventions are unclear | Hand off to `driver-map` first. |
| **company foundation / disclosure evolution gap** | What the company actually sells, how business boundaries evolved, segment / KPI rename or recast history is unclear | Hand off to `company-history` first. |
| **source / claim gap** | Key facts, customer relationships, news, sell-side views, or expert statements are unverified | Hand off to `information-impact` first. |
| **field evidence / channel validation gap** | Key assumptions require expert call, customer/supplier channel check, survey, or fieldwork validation | Hand off to `primary-research-plan` first. |
| **peer comparability gap** | Peer group, KPI conventions, business mechanisms, or value-capture models are not comparable | Hand off to `peer-deep-dive` first; precede with `mechanism-insight` / `driver-map` if necessary. |
| **thesis assembly gap** | Drivers are already disentangled, but variant view, catalysts, and kill criteria need to be consolidated into a document | Hand off to `alpha-thesis`. |
| **journal-ready insight** | Already researched, thought through, and capable of altering subsequent judgments | Hand off to `research-journal`. |

Weird disclosure bucket / KPI bucket rule: when encountering unnatural buckets like `Other / Solutions / Systems / Industrial / Services / CTS`, or breakdowns like `GTE / GTS / Industrial Products / Industrial Solutions`, do not treat this as a single-company diagnostic. First judge whether this is a mechanism gap, driver gap, or KPI-convention gap, then trigger the corresponding primitive.

## Mode A: Direction Coach

### Step 1: Locate the Research Bottleneck

First determine where the user is actually stuck:
- Don't understand how the business works → mechanism gap.
- Don't know which drivers go into the model → driver gap.
- Don't know whether information can be trusted → source gap.
- Don't know whether companies are comparable → peer comparability gap.
- Have material but don't know which angle has the most edge → next-step proper.

### Step 2: Select a Single Highest-Leverage Question

A candidate question must satisfy at least one of the following:
- Could change understanding of business substance.
- Could change revenue / margin / backlog / price-volume-mix drivers.
- Could change market expectations or consensus framing.
- Could change peer group / valuation framework.
- Could change next-step research priorities.

If a question only adds more background knowledge without changing any of the above, default to not selecting it.

### Step 3: Output a Short Answer

Output only one question and 1–2 ways to phrase it for an AI. Do not list all candidate questions unless the user explicitly asks to compare multiple directions.

## Mode B: Research Audit

Used when the user provides a piece of research, memo, thread, model logic, or post-print note and asks for a judgment on what feels off.

Workflow:
1. First identify the strongest conclusion already reached.
2. Then identify the largest unexplained anomaly.
3. Determine whether the anomaly belongs to mechanism, driver, source, peer, market framing, or thesis gap.
4. If it is a primitive gap, output a handoff block; otherwise output a next-step question.

Research Audit is not copy editing and not a full review; do not rewrite the user's material paragraph by paragraph.

## Mode C: Question Rewriter

Used to turn vague questions into ones better suited for an AI or downstream skill.

Rewriting criteria:
- The question must include the research object.
- The question must state the hypothesis or gap to be verified.
- The question must require source / as-of, unless it is a pure mechanism explanation.
- The question must not present unverified premises as facts.
- Default to only 1–2 questions, not a prompt pack.

## Output Structure

### Default: Direction Coach

```markdown
**I suggest chasing this question first: [one question]**

Why it could change the judgment:
- [Explain how it affects business substance / model driver / market expectations / peer framing / research priorities]

Try asking the AI this way:
1. [...]
2. [...]
```

### Research Audit

```markdown
**I suggest the next step is to fill: [one question or primitive handoff]**

Conclusions already earned:
- [...]

Largest unexplained anomaly:
- [...]

Why this question takes priority:
- [...]

Try asking the AI this way:
1. [...]
2. [...]
```

### Question Rewriter

```markdown
**Could be rephrased as:**
1. [...]
2. [...]

Why this is better:
- [...]
```

### Primitive Handoff

```markdown
**Don't continue writing [thesis/model/peer compare] yet — I suggest triggering `[skill-name]` first.**

Blocking point:
- [...]

Why it would contaminate downstream judgments:
- [...]

Questions to hand to `[skill-name]`:
1. [...]
2. [...]

Sources / data still needed:
- [...]
```

## Artifact / Save Policy

Conversation output. When the user requests saving, write to `industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md`.

## Anti-Pattern Checklist

### Output Category
- ❌ Output 5–10 generic tasks instead of 1 highest-leverage question.
- ❌ Use "look at financials / look at the industry / look at valuation / look at news" as the next step.
- ❌ Default to giving a prompt pack, research plan, or checklist exceeding what the user needs.
- ❌ The question has no research object, or the object is too broad to be executable.

### Logic / Routing Category
- ❌ See a mechanism / know-how gap but continue writing thesis, model, or peer compare.
- ❌ See a driver / KPI / disclosure gap but give a generic task list without triggering `driver-map`.
- ❌ See a source gap but continue reasoning from the claim as if it were fact.
- ❌ See a weird disclosure bucket / KPI bucket but fail to ask what economic substance it corresponds to.
- ❌ Treat an "interesting anomaly" as a "must-chase anomaly" without explaining what judgment it would change.
- ❌ Write un-researched inspiration into `research-journal`.

### Source Category
- ❌ Stuff unverified facts into the AI question, causing downstream answers to accept those premises by default.
- ❌ Fail to mark user-provided unsourced numbers, KPIs, or customer relationships with `[需查证]`.
- ❌ Fabricate URLs, page numbers, quotes, or source titles to make a question look complete.

### Workflow Category
- ❌ User asked for next-step but output a full research report.
- ❌ User asked to audit a research sticking point but polish the text paragraph by paragraph.

## Length Benchmarks

- Direction Coach: 150–300 words; below 100 words is usually too vague, above 400 usually starts becoming a mini-plan.
- Research Audit: 300–600 words; above 700 should cut secondary observations, keeping only the strongest conclusion, largest anomaly, and one question.
- Question Rewriter: 150–350 words; default 1–2 questions.
- Primitive Handoff: 150–350 words; only write the blocking point, contamination risk, which skill to hand off to, and what needs to be supplemented.
- If the user explicitly requests a full plan, it can be expanded, but first clarify that this is no longer the default next-step output.
