---
name: mechanism-insight
description: Deep-dive a single industry mechanism engineering principle or equipment chain — explain how it works and where value is captured.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Mechanism Insight

Deep-dive a single industry mechanism, engineering principle, or equipment chain. The core value is not writing an encyclopedia entry — it's producing an insight that can change an investment judgment.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## The Philosophy

In much of industrials, energy, nuclear, aerospace, and advanced manufacturing research, genuine edge lies not in "knowing a term" but in knowing how the system behind that term works, where the bottlenecks are, who captures value, and which links transmit to revenue / margin / backlog drivers.

`mechanism-insight`'s job is to turn know-how gaps into structures that can be researched, questioned, and consolidated. The core value is not writing popular science — it is **producing insights that can change an investment judgment**.

This skill is the upstream complement to `driver-map`: `mechanism-insight` explains "how the mechanism works and where value is captured"; `driver-map` then explains "how those mechanisms flow into revenue, margin, backlog, and price/volume/mix drivers." Do not substitute mechanism explanation for driver-map, and do not directly produce DCF, comps, workbook, or full thesis within this skill.

If the output is merely an encyclopedia explanation, or if after reading it one cannot say how it changes a research judgment, this skill has failed.

## AI's Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Confusing similar terminology | AI easily conflates concepts like train, turbine, compressor, generator | Mandate a `Terms that matter` section, explaining plain meaning and boundaries for each term |
| Over-simplifying processes | Complex systems get flattened into "equipment drives growth," losing bottlenecks and value capture points | Must draw a lightweight flowchart / chain diagram |
| Writing capability as adoption | "Product can be used for LNG / data center / nuclear" is miswritten as already supplying | Customer / project / supply chain claims must be tagged with source or `[需查证]` |
| Outdated technical facts | Process routes, equipment configurations, regulatory requirements may change | Tag as-of dates when referencing latest projects, standards, installed capacity, or costs |
| Turning into an encyclopedia | Output becomes generic popular science and does not serve investment judgment | Every mechanism explanation must land on value capture / thesis read-through |

## Trigger Scenarios

### Mode A: Mechanism Explainer
- "What does this industry term actually mean"
- "How is this equipment chain connected"
- "Why is this equipment chain designed this way"
- "How does this process flow work"
- "Why is this system designed this way"
- "Where is the bottleneck / control point"
- "What does this process step do in the system"
- "Why does this mechanism matter"

### Mode B: Mechanism-to-Research Map
- "Which companies does this mechanism create value for"
- "How does this engineering constraint affect the revenue driver"
- "Why does this equipment chain affect margin / service mix"
- "Does this know-how gap affect the thesis"
- "Can this mechanism explain peer valuation divergence"

### Mixed Mode
- "What is the mechanism behind this business bucket, and why is it segmented this way"
- "First explain the mechanism, then tell me which company types could benefit"
- "How does this equipment chain work, and which links are most likely to capture value"

### Should Not Trigger
- Completely zero base, no physical intuition built → `teach-in`
- Full-industry value chain and profit pools → `industry-landscape`
- "What is this company's revenue driver" → `driver-map`
- "Help me build a model / DCF / comps" → `3-statement-model / dcf-model / comps-analysis / model-update`

## Input Clarification Requirements

| Dimension | Meaning | Default Assumption |
|---|---|---|
| Object | Term / equipment / process / system / value chain | User provides a specific noun → single mechanism; user provides a theme → narrow to the most critical mechanism first |
| Research purpose | Understand mechanism / feed driver-map / feed model / feed thesis / peer compare | Default: serve downstream driver-map and thesis |
| Technical depth | Intuitive explanation / engineering chain / business constraints | Default: depth sufficient for a researcher to model and ask questions; not a textbook |
| Industry scope | User-specified industry / equipment chain / process chain | Scope to user's coverage industry; do not expand to unrelated industries |
| Save requirement | Whether to persist to disk | Default: conversation output; write to topic root when user requests save |

## Mode A: Mechanism Explainer

### Step 1: Insight in one sentence

State the single most important investment-research implication of this mechanism in one sentence.

### Step 2: Terms that matter

| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |
|---|---|---|---|---|

### Step 3: How it works

Default to a lightweight flowchart / chain diagram:

```
input / fuel / feedstock -> core equipment/process -> output -> bottleneck / control point
```

Then explain in 3-6 steps. Do not exceed the depth the mechanism itself requires.

### Step 4: Bottleneck and control point

Explicitly identify where in the system the following are most likely to be determined: capacity / throughput, uptime / reliability, efficiency, capex intensity, service intensity, regulatory / safety constraint.

## Mode B: Mechanism-to-Research Map

### Step 1: Where value is captured

| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |
|---|---|---|---|---|

### Step 2: Insight → Driver-map bridge

| Mechanism implication | Driver-map link | Model / thesis implication | Confidence |
|---|---|---|---|

Rating hard standards:

| Rating | Hard standard |
|---|---|
| **High** | Has primary or authoritative source, and can be directly mapped to a driver |
| **Medium** | Mechanism and business relationship are reasonable, but company-level disclosure is incomplete |
| **Low** | Primarily researcher inference or thematic association; must tag `[来源待补]` / `[需查证]` |

### Step 3: What not to infer

- `product can be used` vs `customer adopted`
- `equipment exposure` vs `recurring service exposure`
- `industry bottleneck` vs `company-specific revenue driver`
- `technical importance` vs `pricing power`

## Output Structure

> **Source contract**: Every factual claim in this document (numbers, company names, industry judgments, competitive landscape descriptions) must carry a [S#](url) or [I#](url) short-link anchor at the end of the sentence. Interpretive sentences ("I think," "my judgment") are not mandatory. Three or more consecutive factual claims without an intervening source → insufficient density.
>
> **Density table**:
>
> | Section | Mandatory source tagging | Exemptions |
> |---|---|---|
> | Physical principles / mechanism description | Every physical constant, key technical parameter, material property | Universally accepted physical laws |
> | Equipment / process details | Equipment model, precision figures, capacity data, pricing | — |
> | Industry chain positioning | Every company name + product name + positioning | — |
> | Value capture analysis | Market share / margin / pricing power figures | Qualitative judgment |
>
> **Completion Gate**: Scan section by section after writing → physical constants have [P#], equipment figures have [S#]/[I#] → `[待查]` ≤8 → Resources expands all sources.

```markdown
## Conclusion first
[A one-sentence statement of the most important investment-research implication of this mechanism]

## Insight in one sentence
[What this mechanism is + what it does in the system + which investment variable it affects]

## Terms that matter
| Term / part | Plain meaning | Boundary / not this | Why it matters | Ev |

## How it works
[Lightweight flowchart + 3-6 step explanation]

## Where value is captured
| Value capture point | Who captures value | Revenue / margin channel | Evidence quality | Research read-through |

## Research read-through
| Mechanism implication | Driver-map link | Model / thesis / peer implication | Confidence |

## What not to infer
- [Conclusions that should not be extrapolated]

## Routing
- Decompose company drivers → `/driver-map`
- Form thesis → `/alpha-thesis`
```

## Image Requirements

**Product/equipment photographs are mandatory**. Source priority: company product page hero image → web search → `[缺图]`.

**Download method**: `python _scripts/shared/download-image.py <url> --output <slug>`. Logo mode: `--logo <TICKER>`. Source priority: 1) company media kit -> 2) product page hero -> 3) web search -> 4) `[missing image]`.

## Artifact / Save Strategy

Write to the industry topic root:
```
industry/<industry-slug>/YYYY-MM-DD-mechanism-insight-<qualifier>.md
```

`naming_mode = required_qualifier`, where qualifier is named by the specific mechanism / equipment / process.

## Workflow Linkage

| Scenario | Next Step |
|---|---|
| Mechanism is explained; need to decompose revenue / margin / backlog drivers | `driver-map` |
| Mechanism affects model | `3-statement-model / dcf-model / comps-analysis / model-update` |
| Mechanism exposes high-value unknowns but unclear how to ask | `next-step` |
| Mechanism explains peer divergence or KPI incomparability | `peer-deep-dive` |
| Mechanism forms a long / short variant view | `alpha-thesis` |
| Zero base; need to build physical intuition first | `teach-in` |
| Need full-industry landscape and investment judgment | `industry-landscape` |

## Anti-Pattern Self-Check

### Source Category
- ❌ Capacity, cost, efficiency, orders, pricing, customers, installed volume lack source / as-of
- ❌ Treating industry common knowledge as company-disclosed fact
- ❌ Multiple sources conflict but conflict is not flagged

### Logic Category
- ❌ Only encyclopedia explanation, no value capture or research read-through
- ❌ Writing `product can be used` as `customer adopted`
- ❌ Directly extrapolating technical importance into pricing power
- ❌ No flowchart / chain diagram drawn
- ❌ Explained equipment function but did not identify bottleneck, control point, or service intensity

### Workflow Category
- ❌ User only asked about a mechanism, but output includes DCF / comps / price target
- ❌ No product/equipment photograph included
- ❌ Mechanism is still Low confidence, but treated as core fact
- ❌ Performed industry-landscape-level full value chain overview within mechanism-insight

## Length Benchmark

- Quick check: 500-900 words + 1 flowchart/table
- Full insight: 1000-1800 words + 2-4 tables
- Over 2000 words: scope is too broad; should split into multiple mechanisms or transition to `peer-deep-dive`

## Boundaries with Adjacent Skills

| | teach-in | industry-landscape | mechanism-insight | driver-map |
|---|---|---|---|---|
| **Entry point** | Zero base | Know basic concepts | Know industry terms | Know mechanism |
| **Question** | What is this thing | Is the industry worth investing in | How does the mechanism work | How to decompose revenue / margin |
| **Coverage** | Full chain education | Full industry | 1-2 mechanisms | Single company / segment |
| **Images** | Physical photos | Company logo + product photos | Product physical photos | None |
| **Artifact length** | 6000-8000 | 2000-3000 | 1000-1800 | 800-1500 |

> Product photos: Every unit involving physical equipment/products must include 1 physical photo. Download priority: Company website Media Kit → product page hero → web search → [缺图]. Download to topic.
