---
name: question-sharpener
description: Use when a research question is vague, mixes multiple dimensions, or the user says "I don't know how to ask this" — sharpens fuzzy questions into precise answerable questions by clarifying intent, surfacing hidden assumptions, and reframing the ask. Routing to downstream skills is a brief supplement, not the main output.
---

# Question Sharpener

Your job is not to route. Your job is to make the question better.

When someone asks a vague question, they usually know what they care about but can't articulate it. Help them find the real question.

## When to Use

- "这些都是啥" / "给我讲清楚"
- "帮我想想这个问题该怎么问"
- "我不太确定我在问什么"
- Multiple concepts mixed together (materials + companies + costs)
- Questions with hidden assumptions or missing context
- User's question feels "off" but you can't tell why

**Don't use for:** Already-precise questions, single-fact lookups, routing decisions you can make silently.

## Workflow

### Step 1: Figure Out What They Actually Want

Read the fuzzy question and ask yourself:

1. **What decision is behind this?** — Are they trying to invest? Understand an industry? Verify a claim? Size a market?
2. **What would a good answer look like?** — A number? A ranked list? A yes/no? A framework?
3. **What's the hidden context?** — What do they already know? What are they assuming?

This step is about intent, not decomposition. You're not splitting the question yet — you're understanding the person.

### Step 2: Surface the Blind Spots

What's missing that makes this question hard to answer?

- Missing scope (time horizon? geography? market segment?)
- Missing definitions (what counts as "good"? "big"? "important"?)
- Wrong framing (asking "who" when they should ask "how"; asking for a list when they need a mechanism)
- Premature precision (asking for a number when they don't understand the thing yet)

State these explicitly. "Your question assumes X, but X isn't settled. Let's check that first."

### Step 3: Rewrite the Question

Output 1-3 sharpened questions. Each must be:

- **Specific** — names the thing, the scope, the unit
- **Answerable** — you can imagine what a good answer looks like
- **Sequenced** — if there are multiple, earlier questions unblock later ones

Format:

```markdown
## Sharpened

> Your original: "[user's fuzzy question]"

What you're really trying to figure out is [intent]. But before we can answer that, we need to resolve [blind spot].

**Reframed:**

1. [Precise, specific question]
2. [Next question, if needed]
3. [Final question — the one that answers the original intent]
```

### Step 4: Suggested Path (Brief)

If the user wants to pursue the sharpened questions, suggest 1-2 downstream skills as a one-liner. This is not the main output — keep it short.

```
**Next**: Start with [skill] to [do what]. Then [skill] to [do what].
```

## Output Principles

- The sharpened questions ARE the output. Everything else supports them.
- Don't output a routing table as the main deliverable.
- Write like a senior analyst helping a junior think, not like a dispatcher.
- If the original question is already good, say so and suggest a direct path.
- If the question can't be sharpened without more context from the user, ask for it.

## Common Mistakes

- ❌ Treating sharpening as decomposition — you're not splitting, you're reframing
- ❌ Outputting a routing table as the main answer — routing is a footnote
- ❌ Skipping intent and going straight to "which skill" — understand first, route last
- ❌ Pretending a bad question is good — if it's missing context, say so
