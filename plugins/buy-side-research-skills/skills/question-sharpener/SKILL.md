---
name: question-sharpener
description: Use when a research question is vague, mixes multiple dimensions, or the user says "I don't know how to ask this" — decomposes fuzzy questions into precise answerable sub-questions, maps known vs unknown against existing workspace artifacts, and routes each sub-question to the right downstream skill.
---

# Question Sharpener

Turn "I don't know how to ask this" into a precise research plan in <200 words.

## When to Use

- "这些都是啥" / "给我讲清楚"
- "帮我先把这个问题该怎么问想清楚"
- Multiple concepts mixed in one question (materials + companies + costs)
- User explicitly says they can't articulate the question

**Don't use for:** Single-fact lookup, already-precise questions, routing decisions you can make silently.

## Workflow

### Step 1: Dimension Split

Decompose one fuzzy question into 2-4 independent dimensions. Each dimension = sub-questions answerable under one cognitive frame.

### Step 2: Known vs Unknown

| Mark | Meaning |
|---|---|
| ✅ | Existing workspace artifact covers this |
| ⚠️ | Partial coverage, needs supplement |
| ❓ | Needs new research |

### Step 3: Route

| Question type | Downstream skill |
|---|---|
| "What is this thing" — physical intuition | `teach-in` |
| "Who makes it / industry structure" | `industry-landscape` |
| "Which company is worth looking at" | `candidate-screener` |
| "Verify a specific number or claim" | `deep-research` |
| "How does this company make money" | `driver-map` |
| "Compare these companies" | `peer-deep-dive` |
| "How big is this market" | `market-sizing` |
| "How does this mechanism work" | `mechanism-insight` |

### Step 4: Sequence

Always: **physical intuition first → landscape → company drivers → sort**. The sequence must follow cognitive dependency — you can't compare companies you don't understand, you can't analyze drivers without knowing the industry structure.

## Output Format

```markdown
## Question Decomposition

> Original: [user's fuzzy question]

| Dimension | Sub-questions | Status | Route |
|---|---|---|---|
| [Name] | [Precise question] | ✅/⚠️/❓ | [skill] |

**Suggested sequence**: ① [skill] → ② [skill] → ③ [skill]
```

## Common Mistakes

- ❌ Treating a mixed question as one monolithic task — always split dimensions first
- ❌ Routing to deep research before establishing physical intuition — teach-in first
- ❌ Skipping the "known" check — check existing artifacts before launching new research
- ❌ Outputting analysis instead of a routing table — this skill does navigation, not research