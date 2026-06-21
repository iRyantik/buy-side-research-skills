---
name: information-impact
description: Check whether a news claim rumor note or data point is credible and research-relevant.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Information Impact

Check whether a news claim rumor note or data point is credible and research-relevant.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- workspace `.references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Principles

Verify authenticity first, then assess research relevance. Rumors, clickbait headlines, sell-side re-reporting, social media screenshots, and expert soundbites may all carry lead value, but cannot be treated as facts until a reliable source is found.

This skill's operating logic is **claim decomposition + evidence grading + research relevance**:
- First, break vague information into verifiable claims.
- Then assign source quality and verdict.
- Only when the verdict reaches at least `Plausible but unconfirmed` does the skill proceed to assess whether it is worth continued research.

**The most critical discipline**: `product can be used`, `theme association`, `tier-2 supplier` must never be written as `direct supplier`.

## Trigger Scenarios

### Mode A Triggers (Claim Check)
- "Is this news reliable?"
- "Can this claim be trusted?"
- "Is there a source?"
- "Has company X entered a certain customer's supply chain?"
- "Is there a source for this supply chain rumor?"
- "Is this customer relationship real?"
- "Can this screenshot be trusted?"

### Mode B Triggers (Research Relevance)
- "Is this news worth following up?"
- "What incremental research value does this add?"
- "What should be asked next about this data point?"

## Input Clarification Requirements (6 Mandatory Dimensions)

If the user provides a vague rumor, first fill in missing dimensions or mark as unknown:

| Dimension | Meaning | Default Handling |
|---|---|---|
| **Claim original text** | The complete statement the user heard | Quote verbatim, do not strengthen |
| **Company** | The subject company | Ask if unknown, do not guess |
| **Counterparty / program** | Customer, project, supply chain, policy, data source | Mark `[needs verification]` if unknown |
| **Product / role** | Product, service, component, relationship role | Decompose into claim pieces |
| **Timeframe** | When it happened / effective date / source timestamp | Write `timeframe unknown` if absent |
| **User intent** | Verify truth only / assess research value / batch filter | Default to verify truth first |

If the claim itself would be distorted by a missing field, clarify first. For example, "entered a certain customer's supply chain" must distinguish whether it is direct supplier, tier-2, product usable in a certain application, or market theme association.

## Mode A: Claim Check

### A.1 Reasoning Path (Must Be Explicit)

**Step 1: Decompose the Claim**

| Claim piece | Question to verify |
|---|---|
| company | Who is the subject |
| customer / program | Who is the counterparty / which project |
| product_or_role | What is supplied / what service is provided |
| relationship_type | direct / tier-2 / product can be used / theme association |
| timeframe | When it happened |
| magnitude | Revenue, order, capacity, profit, or shipment volume |

**Step 2: Find Evidence**

Graded by source quality:

| Level | Type | Can Support |
|---|---|---|
| 1 | Filing, exchange announcement, company IR, earnings call, regulatory / government data, customer official announcement, procurement / contract documents | Can support `Confirmed` |
| 2 | Transcript databases, Bloomberg / FactSet / CapIQ / Visible Alpha, industry research firms, expert interview platforms | Can support `Likely` |
| 3 | Reuters / Bloomberg News / FT / WSJ, industry media, company press releases, sell-side reports | Must separate fact vs opinion |
| 4 | Social media, forums, chat logs, rumor screenshots, personal blogs, broker re-reporting | Leads only |

**Step 3: Issue Verdict**

| Verdict | Meaning | Next Step |
|---|---|---|
| `Confirmed` | Primary source or customer / company / regulatory filing directly substantiates | Can proceed to Research Relevance |
| `Likely` | Multiple fairly reliable sources are consistent, but direct primary evidence is lacking | Can proceed to Research Relevance |
| `Plausible but unconfirmed` | Leads or a single source exist, but evidence is insufficient | Weak relevance judgment only |
| `Unsupported` | Only low-quality sources, no reliable corroboration found | `Drop` |
| `Contradicted` | Reliable sources already provide counter-evidence | `Drop` |

### A.2 Supply Chain Claim Hard Classification

These four categories must be clearly distinguished:

- **direct supplier**: Has a primary contract, customer announcement, or company confirmation.
- **tier-2 / indirect supplier**: Indirect exposure through upstream or downstream, relationship strength is much lower.
- **product can be used**: The product could theoretically be used in a certain scenario — this does not mean it has been procured.
- **theme association**: The market groups the company into a theme, but there is no evidence of a business relationship.

If "X entered a certain customer's supply chain" is only `product can be used` or `theme association`, it must not be written as direct supplier.

### A.3 Output Structure

```markdown
## Claim Check

**Verdict**: Confirmed / Likely / Plausible but unconfirmed / Unsupported / Contradicted
**Bottom line**: [One-sentence judgment — directly state whether it can be trusted]

| Claim piece | Evidence found | Source quality | Read-through |
|---|---|---|---|
| [claim decomposition item] | [evidence summary + source / as-of] | 1 / 2 / 3 / 4 | direct / indirect / not proven |

**What not to infer**
- [What cannot be extrapolated from this information]

**Research relevance**
- Worth continued research: Yes / No
- Why: [one sentence]
- Questions to ask AI: [1-2 questions]
```

If the verdict is `Unsupported` or `Contradicted`, default to short output:

```markdown
**Verdict**: Unsupported / Contradicted
**Bottom line**: [Why it cannot be trusted, or what source refutes it]
**Action**: Drop
```

## Mode B: Research Relevance

Only when the Mode A verdict reaches at least `Plausible but unconfirmed` does the skill proceed to assess whether continued research is warranted.

The criterion is not "is this newsworthy" but whether it could potentially change:

- Understanding of business substance
- Revenue / margin / backlog / price-volume-mix driver
- Market expectations or consensus framing
- Peer group / valuation framework
- Research prioritization
- An anomaly flagged by `Senior Analyst Radar`

If there are high-value questions, output 1-2 questions most worth asking AI, and suggest triggering ``. If it merely confirms a fact without research increment, end there — do not force an expansion.

## Batch Mode

Used for morning briefs or rapid multi-item filtering. Output retains only filtering value — no status file is written:

```markdown
## Information Filter

| Title | Source quality | Verdict | Research relevance | Action |
|---|---|---|---|---|
| [title] | 1 / 2 / 3 / 4 | [verdict] | [Yes / No + one sentence] | Drop / Ask 1-2 AI questions / Trigger  / Save later via research-journal |
```

Action must be one of:

- `Drop`
- `Ask 1-2 AI questions`
- `Trigger `
- `Save later via research-journal`

`Unsupported` / `Contradicted` default to `Drop`. Do not save unless the user explicitly requests an audit trail.

## Artifact / Save Policy

Conversation output. When the user requests a save, write to industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md.

## Anti-Pattern Self-Check

### Source Category
- ❌ Treating news headlines as sources.
- ❌ Treating sell-side opinions as facts.
- ❌ Treating social media screenshots / chat logs as confirmed evidence.
- ❌ Multiple outlets re-reporting the same low-quality source, treated as multi-source corroboration.

### Claim Category
- ❌ Conflating direct supplier, tier-2, product can be used, theme association.
- ❌ Drawing strong conclusions from `Plausible but unconfirmed`.
- ❌ Omitting timeframe, making an old relationship appear new.
- ❌ Issuing a broad conclusion without decomposing claim pieces.

### Workflow Category
- ❌ Writing a lengthy thesis because a piece of information "looks important."
- ❌ Continuing to expand research value for `Unsupported` / `Contradicted`.
- ❌ Turning every morning brief item into a follow-up, creating information noise.

## Length Benchmarks

- Unsupported / Contradicted: 100-250 words.
- Single Claim Check: 300-700 words + 1 evidence table.
- Batch Mode: 1 row per item, expand only top 1-3 items at most.
- Exceeding 900 words typically indicates this is no longer filtering — hand off to another research skill.

