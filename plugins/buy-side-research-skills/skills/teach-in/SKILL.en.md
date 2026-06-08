---
name: teach-in
description: Build zero-to-one physical intuition for an unfamiliar industry — why it exists, what's inside, how it's made, and who does what. Zero investment judgment.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Teach-In

Build physical intuition for an unfamiliar industry from absolute zero. No investment judgment. Pure engineering literacy.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- `references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Core Philosophy

The most common failure mode when a researcher faces a completely new industry — especially engineering-intensive tracks like semiconductors, advanced manufacturing, and energy equipment — is not "getting the judgment wrong," but **starting to write a thesis without understanding how the thing actually works**.

`teach-in` solves exactly this problem. It is not a research output — it is a **research prerequisite**. Before you run `industry-landscape` (is this industry worth investing in?) or `mechanism-insight` (how does a single mechanism work?), you first build the most basic physical intuition.

This skill's failure criterion: after reading the output, the researcher still cannot answer "what does this thing look like, what is it made of, how is it manufactured, and why is it designed this way." If the output turns into an investment analysis report, that is also a failure.

## AI Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| **Lacks spatial intuition** | AI tends to describe a data center as "many servers" without addressing physical spatial topology | Enforce layer-by-layer zoom (building → cabinet → port → chip), with ASCII diagrams |
| **Lacks scale intuition** | AI says "micron-level precision" without analogy | Enforce a scale-ladder diagram, annotating each level with everyday analogies (human hair, sesame seed, pizza) |
| **Skips physical constraints** | AI says "use light because it's fast" without explaining the physical limits of electrical signals | Enforce deriving design motivation from physical constraints |
| **Missing materials science** | AI says "lasers use InP" without explaining why silicon cannot be used | Semiconductor / advanced manufacturing tracks MUST explain the physical reasons behind material selection |
| **Turns popular science into an encyclopedia** | The output becomes a glossary without building a cognitive framework | Every layer must include the "why," not just the "what" |
| **Investment judgment leaks in** | Temptation to write "Company X is worth watching" in the landscape overview table | The landscape overview table lists only company name + positioning + precision tier; no value judgments |

## Trigger Scenarios

- "Explain this industry from scratch"
- "I know nothing about XX, give me a primer"
- "What is CPO / wafer / die bonding"
- "What are optical modules used for"
- "What even is this industry — give me a briefing first"
- "teach-in"
- "primer"
- "zero-base" / "from zero"

## Input Clarification Requirements

| Dimension | Meaning | Default Assumption |
|---|---|---|
| **Subject** | Industry / topic / product / technology | Start from the full industry, do not focus on a single company |
| **Depth** | Physical intuition vs. engineering detail | Default to the depth of "can understand what every step in the value chain does" |
| **Industry type** | Semiconductor / manufacturing vs. consumer / software | Semiconductor / advanced manufacturing MUST cover materials + physical constraints; consumer brands may skip the materials layer |
| **Save** | Whether to write to disk | Default to conversation output; write to a topic artifact when the user requests saving |

## Output Structure

### 7+1 Layer Cognitive Progression

Each layer answers one core question, progressing along WHY THIS CATEGORY → WHY → WHERE → WHAT → HOW → WHY NOW → WHO → TAKEAWAY.

```
Phase 0: WHY THIS CATEGORY — Why this class of thing is needed (the physical inevitability of the category's existence)
  Layer 0: Physical limits → Reason the category exists
          Example: Bandwidth × distance is a constant for electrical signals on copper → high speed cannot travel far → optical modules must exist
          Example: PCB manufacturing is a statistical-defect process → AOI can only inspect, not test → electrical testing must exist
          Must answer: "Why won't the most intuitive alternative work?"

Phase 1: WHY — Why this thing is needed
  Layer 1: Physical constraints and design motivation
          Why electricity is insufficient → Why light is the inevitable path → What physical problem this thing solves

Phase 2: WHERE — What it looks like, where it sits
  Layer 2: Spatial topology (from building to port, layer-by-layer zoom)
          Data center → Rack → Server → NIC → Port → This thing → What it connects to at the other end

Phase 3: WHAT — What's inside, what it's made of
  Layer 3: Internal structure + component teardown
          Open it up to see every internal component + what each component does

  Layer 3.5: Materials deep-dive (**mandatory** for semiconductor / advanced manufacturing / materials-intensive industries)
          Material × function matrix (which material → what it can do → what it cannot do → who supplies it)
          Physical principle behind each material (why this material and not another)
          How material selection drives downstream equipment requirements

Phase 4: HOW — How it's made
  Layer 4: End-to-end manufacturing chain (from raw material to shipment)
          Each step annotated: process name + equipment type + precision requirement + global / China players + yield bottleneck

Phase 5: WHY NOW — Why it's upgrading generationally
  Layer 5: Generational driving forces
          Physical limits driving upgrades + how precision / testing / packaging jumps each generation + next-generation paradigm + equipment super-cycle logic

Phase 6: WHO — Who's doing it (pure facts, no judgment)
  Layer 6: Full-chain company positioning table + competitive-moat dimension breakdown
          Each step annotated: global players / China players / precision ceiling
          Moat scoring table (precision hardness / testing lock-in / customer lock-in ⭐⭐⭐)

Closing trio (after Layer 6, required):
  Three-sentence summary — compressed physical intuition, not investment judgment
  Most common misconceptions — a cognitive calibration table for the reader
  Questions worth pursuing next + Routing Handoff
```

### Per-Layer Hard Requirements

| Layer | ASCII Architecture Diagram | Product Photo | Glossary | Scale Comparison | Yield Bottleneck | Value Share | Source |
|---|---|---|---|---|---|---|---|
| 0 | Required (physical limit comparison) | Not required | Not required | Required (constant orders of magnitude) | Not required | Not required | Physics textbooks / IEEE / standards bodies |
| 1 | Required (physical comparison) | Not required | Not required | Required (order-of-magnitude comparison) | Not required | Not required | IEEE / physics standards / textbooks |
| 2 | Required (spatial zoom) | **Required** (product photo + installation location) | Required (port / interface standards) | Required | Not required | Not required | Product pages / MSA specs / data center architecture |
| 3 | Required (exploded view) | **Required** (teardown photo) | Required (every component) | **Required** (scale ladder) | Not required | Not required | Product pages / teardowns / BOM analysis |
| 3.5 | Required (material × function matrix) | **Required** (material photo / wafer / cross-section SEM) | Required (material names + properties) | Required (wafer size / thickness comparison) | Not required | Not required | MatWeb / CRC / materials databases / fabs |
| 4 | Required (full-chain flow diagram) | **Required** (key equipment photo) | Required (every process step) | Not required | **Required** (⭐⭐⭐) | **Required** (if equipment industry) | Official equipment pages / prospectus / industry reports |
| 5 | Required (generational comparison diagram) | Not required | Required (new technology terms) | Not required | Not required | Not required | Standards bodies / generational roadmaps |
| 6 | Not required (pure table) | **Required** (representative company product / logo image) | Not required | Not required | Not required | **Required** (equipment segment percentage) | Prospectus / company website / industry reports |
| Closing | Not required | Not required | Not required | Not required | — | — | — |

### Image Requirements

**Product photo download priority**: Company website Media Kit → Product page hero image → web search product image → industry representative image → `[Image missing]`

Download to `_cache/images/`; embed in artifact as `![Description](relative path)`.

**Download method**: `python .scripts/shared/download-image.py <url> --output <slug>`. Logo mode: `--logo <TICKER>`. Source priority: 1) company media kit -> 2) product page hero -> 3) web search -> 4) `[missing image]`.

**ASCII architecture diagrams**: I will draw them. At least 1 per layer.

### Layer 3.5: Materials Deep-Dive (Mandatory for Semiconductor / Advanced Manufacturing / Materials-Intensive Industries)

When the industry type involves semiconductors, advanced manufacturing, precision equipment, or new materials, a materials deep-dive layer **MUST** be inserted after Layer 3. Consumer brands / software / internet may skip.

**Material × Function Matrix Table (required)**:

| Material | Chinese Name | What It Can Do | What It Cannot Do | Material Suppliers (Upstream) | Device / Equipment Makers (Downstream) |
|---|---|---|---|---|---|

**Plain-language physical principle for each material** (2–3 paragraphs per material):

- Why this material was chosen (physical mechanism — not "because performance is good")
- What the alternative materials are and why they did not win
- How this material choice constrains downstream equipment design

**Material → Equipment Requirement Mapping (required)**:

- How the material's physical properties dictate processing / testing precision requirements
- Example: InP wafers max out at 4 inches → fewer die per wafer → equipment throughput matters more

### Routing Handoff (Required at the End of Layer 6)

```markdown
## Next Steps

| What You Want to Do | Which Skill to Use |
|---|---|
| Assess whether this industry is worth investing in, value-chain profit pool allocation | `/industry-landscape` |
| Deep-dive a specific equipment segment / mechanism — how it works and where value is captured | `/mechanism-insight <specific mechanism>` |
| Screen and prioritize companies, rank research order | `/candidate-screener` |
| Quick first pass on a single company | `/stock-quickread <ticker>` |
| Break down a company's revenue / profit drivers | `/driver-map` |
```

### Closing Trio (After Layer 6, Required)

**Three-Sentence Summary** (required):

3 sentences of compressed physical intuition. No investment judgment (no "worth investing," "valuation," or "recommend"). One insight per sentence, corresponding to the core cognitive compression from Layers 1–5.

Format:
```markdown
### Three Sentences

1. **<insight 1>** — <physical constraint or reason the category exists>
2. **<insight 2>** — <core tension in the manufacturing / equipment chain>
3. **<insight 3>** — <generational upgrade or paradigm-shift driving force>
```

**Most Common Misconceptions** (required):

Cognitive calibration for the **reader** — not anti-patterns for the AI. Format: `| X Don't think of it this way | ✓ Think of it this way |` table, 5–7 rows. Cover: category boundaries, technology path, competitive landscape, upgrade logic, precision barriers.

**Questions Worth Pursuing Next** (required):

5–7 specific questions — specific enough that a single number, event, or document can answer them. Followed by the standard Routing Handoff table.

## Artifact / Save Strategy

Write to the industry topic root:
```
industry/<industry-slug>/YYYY-MM-DD-teach-in-<qualifier>.md
```

Path resolution is handled automatically by the agent per policy baseline §11. `qualifier` is required — e.g. `optical-module`, `die-bonding-equipment`.

## Workflow Handoff

| Scenario | Next Step |
|---|---|
| Physical intuition established, need to assess industry investment value | `industry-landscape` |
| Need to deep-dive a specific equipment segment / mechanism | `mechanism-insight` |
| Multiple candidate companies need ranking | `candidate-screener` |
| Go directly to a single company | `stock-quickread` |
| Break down a company's revenue / profit drivers | `driver-map` |
| Check market expectations / priced-in gap | `consensus-map` |

## Anti-Pattern Self-Check

### Structural
- ❌ Output has turned into an investment analysis report (contains "worth investing," "reasonable valuation," "recommended for attention")
- ❌ Skipped the materials layer (Layer 3.5) but this is a semiconductor / advanced manufacturing / precision equipment industry
- ❌ Missing Layer 0 (reason the category exists) — jumped straight to Layer 1 physical constraints
- ❌ Scale comparisons only list numbers without everyday analogies
- ❌ Not a single ASCII architecture diagram — pure-text popular science is guaranteed to fail
- ❌ Any one of the 7+1 layers is completely missing without explanation
- ❌ Closing section missing the three-sentence summary, most common misconceptions, or next-layer questions
- ❌ Fewer than 8 body images (< 10 for equipment / manufacturing industries)
- ❌ Layer 4 lacks yield bottleneck analysis (equipment / manufacturing industries)
- ❌ Layer 6 has only a company list without competitive-moat dimension breakdown (precision hardness / testing lock-in / customer lock-in)
- ❌ Layer 6 lacks equipment value-share percentage (if equipment industry)
- ❌ Layer 5 does not explain "why this is a super-cycle for equipment companies" (if equipment industry)

### Physical Intuition
- ❌ Only says "use light because it's fast" without explaining the bandwidth-distance product limit for electrical signals
- ❌ Only says "chips are small" without providing scale comparisons
- ❌ Only says "precision is high" without explaining why high precision is physically necessary

### Image
- ❌ Product photo uses a manufacturer logo instead of the actual equipment / product
- ❌ Cannot find an image → skips it — must mark `[Image missing]`
- ❌ Used a full-page webpage screenshot instead of a product hero image

### Source

**Source Density (minimum anchor density per layer)**

| Layer | Content Requiring Source Annotation | Exempt |
|---|---|---|
| 0 Category existence rationale | Every physical constant, every order-of-magnitude comparison, alternative-approach data | Common-sense analogies (e.g. "human hair ~80 μm") |
| 1 Physical constraints | Every physical constant, every order-of-magnitude analogy | Common-sense analogies (e.g. "human hair ~80 μm") |
| 2 Spatial topology | Equipment weight / volume / environmental requirements, product image source URL | ASCII architecture diagrams |
| 3 Internal structure | Material selection rationale for every component, probe / socket precision numbers | Exploded views (original diagrams) |
| 3.5 Materials deep-dive | Physical property data for every material (CTE, hardness, density, etc.), wafer size / capacity, supplier names | Physics common knowledge (e.g. "silicon does not emit light — indirect bandgap") |
| 4 End-to-end manufacturing | Precision numbers for every process step, equipment model / pricing, yield data | Process names (general knowledge) |
| 5 Generational | Every L/S number, layer-count range per generation, IPC / standards document references, TAM data | Directional trend judgments |
| 6 Company positioning | Every company name + positioning + precision ceiling, equipment value-share percentage | — |
| Closing trio | Not required (compressed summary, not new facts) | — |

**Source types**: `[S#](url)` equipment vendor product page / datasheet, `[I#](url)` third-party industry report / news, `[P#](url)` physical constant / materials database / textbook.

Physical constants → cite at least one verifiable source (MatWeb / CRC / textbook); no WebFetch verification needed.
Equipment specs / company names → WebFetch / Playwright must attempt at least Tier 2; mark `[To verify]` if all fail.

- ❌ Physical constants without source
- ❌ Terminology explanations without source
- ❌ Company list without source
- ❌ Layer 1 / 3 material selection rationale uses "because performance is good" without physical basis + source
- ❌ Zero inline anchors in body text — only a closing Resources list

**Completion Gate**: After writing, scan per-layer density → `[To verify]` count ≤ 8 → mark pipeline coverage → images ≥ 10 → closing trio complete → Resources section ≥ 15 cited sources.

### Routing
- ❌ Layer 6 ending lacks Routing Handoff
- ❌ Did work inside teach-in that belongs to industry-landscape or mechanism-insight

## Length Baseline

- Standard teach-in: 8,000–12,000 words (including ASCII diagrams and image links)
- Below 6,000 words: Layer 3 / 4 / 5 insufficiently expanded (manufacturing chain, generational driving forces, or materials deep-dive missing)
- Above 15,000 words: doing the job of `mechanism-insight` or `industry-landscape` — should be split
- **Image quantity baseline**: body images ≥ 10 (including product photos and material cross-section / SEM images). < 8 → image-deficit warning, < 5 → block
- **Source baseline**: ≥ 2 inline anchors per layer (except Layer 0 and closing). Closing Resources ≥ 15 entries

## Boundaries with Adjacent Skills

| | teach-in | industry-landscape | mechanism-insight |
|---|---|---|---|
| **Entry point** | Zero base | Knows basic concepts | Knows industry terminology |
| **Question** | What is this thing | Is the industry worth investing in | How does the mechanism work |
| **Investment judgment** | **Zero** | Industry-level | Mechanism-level |
| **Coverage** | Full-chain primer | Full industry value chain + profit pools | 1–2 mechanisms deep-dive |
| **Images** | Product photos ≥ 10 (required) | Company logos + product photos (required) | Product photos (required) |
| **Output length** | 8,000–12,000 words | 2,000–3,000 words | 1,000–1,800 words |

- `teach-in` is a **prerequisite** for `industry-landscape` and `mechanism-insight`, not a substitute.
- `teach-in` makes zero investment judgments; `industry-landscape` makes industry-level investment judgments; `mechanism-insight` makes mechanism-level value-capture judgments.
- Do not treat teach-in's Layer 4 (end-to-end manufacturing) as mechanism-insight — teach-in writes only 100–200 words per step; mechanism-insight can write 1,000+ words on a single segment.
