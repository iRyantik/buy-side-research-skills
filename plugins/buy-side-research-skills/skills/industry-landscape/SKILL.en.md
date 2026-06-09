---
name: industry-landscape
description: Map industry value chain profit pools competitive dynamics and company roster with investment judgment.
---

# Industry Landscape

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Map an industry's value chain, profit pools, competitive dynamics, and company roster. Make an industry-level investment judgment. Hand off to candidate-screener for company prioritization.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- workspace `.references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Principles

Buy-side industry research is not about "understanding the industry landscape" — that is the sell-side initiation playbook. Buy-side industry research answers three questions: (1) Is this industry worth investing in right now? (2) Where is the money concentrated along the value chain? (3) Which companies are most worth looking at first?

The core output of `industry-landscape` is not an industry encyclopedia — it is a **value chain map + profit pool analysis + competitive dynamics + company roster + industry-level investment judgment**. It adds one layer of investment perspective beyond `teach-in`, and one layer of industry panorama beyond `candidate-screener`.

Failure criteria for this skill: output reads like industry科普 without investment judgment; a value chain is drawn but without profit allocation annotations; the company roster turns into a ranked recommendation list.

## AI Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Profit pool misjudgment | AI tends to assume "industry is growing = every segment is making money" | Must write a standalone value capture section, annotating which segment is eating the fat margins and which is in a race to the bottom |
| Value chain boundary blurring | AI tends to lump upstream raw materials, midstream equipment, and downstream applications all together | Draw the value chain diagram first, annotate representative companies for each segment |
| Competitive dynamics misreading | AI tends to treat "there is a domestic player" as "import substitution is happening" | Annotate localization rate, precision gap, and qualification lead time per segment |
| Concept-stock memory contamination | AI tends to anchor on hot names | Company roster must state exposure type and source status |

## Trigger Scenarios

- "Is this industry worth investing in"
- "Help me look at this industry's value chain"
- "Where are profits concentrated in this industry"
- "Who are the players in this industry"
- "What's the industry landscape like"
- "行业格局怎么样"
- "industry landscape"
- "行业全景"

Do not trigger:
- Zero foundation, need to build physical intuition first → `teach-in`
- Already have a company pool that needs ranking → `candidate-screener`
- Single-mechanism deep dive → `mechanism-insight`

## Input Clarification Requirements

| Dimension | Meaning | Default Assumption |
|---|---|---|
| Industry boundary | Product/service/value chain stage/downstream application | The narrowest investable boundary per the user's original wording |
| Geography | US/Greater China/Global | Global, prioritize anchors in markets the user commonly watches |
| Time window | 3M/12M/24M+ | 12M, with attention to 3M catalysts |
| Direction | Long/Short/Both | Both |

## Output Structure

> **Source contract**: Every factual claim in this document (numbers, company names, industry judgments, competitive landscape descriptions) must carry an inline [S#](url) or [I#](url) short-link anchor at the end of the sentence. Interpretive sentences ("I think", "my judgment") are not mandatory. Three or more consecutive factual claims without an intervening source → insufficient density.
>
> **Density table**:
>
> | Section | Mandatory source annotation | Exempt |
> |---|---|---|
> | §1 Verdict | Profit pool share numbers, directional judgment basis | The directional judgment itself |
> | §2 Value Chain Map | Value pool share % per segment, market share numbers, capacity numbers | ASCII diagram |
> | §3 Competitive Landscape | Each company's market share/positioning, industry concentration (CR3/CR5) | — |
> | §4 Profit Pools | Profit margin/share data for each pool | — |
> | §6 Company Roster | Each company's ticker+MCap+exposure type | — |
>
> **Completion Gate**: After writing, scan each section for density → `[待查]` ≤10 → the Resources section must expand every [S#]/[I#].

### 1. Verdict (~200 words)

Conclusion first: whether this industry is worth investing in now, why, where the profits are, and what the biggest risk is.

### 2. Value Chain Map (~800 words + ASCII diagram)

```
Upstream → Midstream → Downstream → End Customer
```

Annotate per segment:
- What this segment does (one sentence)
- Value pool share (% of total industry profit)
- Representative companies (3–5)
- Concentration trend (fragmenting → consolidating? being displaced?)
- Import substitution status (if applicable)

**A profit distribution summary must follow the value chain diagram**: which segment is eating the fattest margins, which segment is in a price war, where the profit pool is migrating.

### 3. Competitive Landscape (~600 words + table)

| Segment | Structure | Entry Barriers | Substitution Threat | Buyer Power | Supplier Power |
|---|---|---|---|---|---|
| — | Concentrated/Fragmented | — | — | — | — |

**Product photos**: actual product photos of key equipment/products (e.g., optical modules, die bonders, coupling equipment).

Takeaway: what direction competition in this industry is moving.

### 4. Industry Drivers (~400 words)

- Demand side: what is driving growth (specific KPIs — do not write "AI-driven" — write "per-GPU bandwidth demand moving from 400G→800G")
- Supply side: where the bottleneck is (capacity/capex/talent/upstream chips)
- Generational upgrade: what is changing the industry structure (e.g., 800G→1.6T→CPO precision step-change)
- Policy/geopolitics: whether there are export controls/domestic substitution mandates forcing change

### 5. Investment Judgment (~300 words)

- Current industry regime: expansion/contraction/consolidation/displacement
- Where the long/short disagreement lies
- When this judgment would be wrong (kill criteria)
- Industry-level variant view (where it differs from consensus)

### 6. Company Roster (~500 words + table)

| Company | Market | Value Chain Position | Exposure Type | Why It's on the List | Ev |
|---|---|---|---|---|---|
| — | — | — | direct/indirect/thematic | — | — |

**Do not rank.** Ranking is `candidate-screener`'s job. Here only list "which companies in this industry are worth knowing about."

### 7. Routing (~150 words)

| Next Step | Skill |
|---|---|
| Need to deep-dive a specific equipment segment/mechanism → | `/mechanism-insight <specific>` |
| Need company priority ranking → | `/candidate-screener` |
| Need horizontal comparison of 3–8 companies → | `/peer-deep-dive` |
| Quick look at a single company → | `/stock-quickread <ticker>` |
| Decompose a company's revenue/margin driver → | `/driver-map` |
| Need market expectation/priced-in analysis → | `/consensus-map` |

## Image Requirements

**Download method**: `python .scripts/shared/download-image.py <url> --output <slug>` — HTTP Tier 1 → Playwright Tier 2 `--base64` → `[缺图]` if all tiers fail.

| Image Type | Required | Source |
|---|---|---|
| Product photos | **Required** (key equipment/products) | Official product page → web search → `[缺图]` |

## Artifact / Save Strategy

Write to the industry topic root:
```
industry/<industry-slug>/YYYY-MM-DD-industry-landscape.md
```

`naming_mode = optional_qualifier`: use the default name for a full industry landscape; append a qualifier when covering only a specific value chain slice.

## Workflow Linkage

| Scenario | Next Step |
|---|---|
| Zero foundation, need to build physical intuition first | `teach-in` |
| Deep-dive a specific equipment segment/mechanism | `mechanism-insight` |
| Company priority ranking | `candidate-screener` |
| Horizontal company comparison | `peer-deep-dive` |
| Quick judgment on a single company | `stock-quickread` |
| Company driver decomposition | `driver-map` |
| Market expectation analysis | `consensus-map` |
| Form an investment thesis | `alpha-thesis` |

## Anti-Pattern Self-Check

- ❌ Value chain diagram has no profit distribution annotations — drawing it was pointless
- ❌ Competitive landscape only lists names without trends (consolidating? being displaced?)
- ❌ Company roster turns into a ranked recommendation list — that is `candidate-screener`'s job
- ❌ Investment judgment says "long-term bullish" without a specific regime
- ❌ No product photos
- ❌ Copies `teach-in` content verbatim (physical科普), skipping profit pools and investment judgment
- ❌ Copies `mechanism-insight` content verbatim (single-mechanism deep dive), skipping the industry panorama
- ❌ Company roster exceeds 30 names — too many, this is not a database
- ❌ Does not annotate exposure type (direct vs indirect vs thematic)

## Length Benchmark

- Standard industry-landscape: 2,000–3,000 words
- Below 1,800 words: value chain map or competitive landscape is insufficiently developed
- Above 3,500 words: doing `teach-in`'s or `mechanism-insight`'s job

## Boundaries with Adjacent Skills

| | teach-in | industry-landscape | mechanism-insight | candidate-screener |
|---|---|---|---|---|
| **Entry point** | Zero foundation | Knows basic concepts | Knows industry terminology | Has a company pool |
| **Question** | What is this thing | Is the industry worth investing in | How does the mechanism work | Which to look at first |
| **Investment judgment** | Zero | Industry-level | Mechanism-level | Company-level |
| **Coverage** | Full-chain科普 | Full-industry value chain + profit pools | 1–2 mechanisms | Company pool ranking |
| **Images** | Product photos | Product photos | Product photos | None |
| **Output length** | 6,000–8,000 words | 2,000–3,000 words | 1,000–1,800 words | 500–1,500 words |

> Product images: every unit involving physical equipment/products must include 1 product photo. Download priority: Company official Media Kit → Product page hero → web search → [缺图]. Download to the topic directory.
