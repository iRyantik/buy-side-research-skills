---
name: driver-map
description: Decompose revenue margin backlog price volume mix and segment drivers before modeling.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Driver Map

Decompose revenue margin backlog price volume mix and segment drivers before modeling.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for business reality translation and model driver mapping; unresolved facts stay as gap, hypothesis, or follow-up.
- **Actuals-only**: margin breakdowns, price/volume/mix ratios, and all quantitative driver ratios use actuals-resolved.json disclosed data. No forward estimate as ratio input.
- Sub-agent outputs must be evidence_cards_only; main agent synthesizes, cross-checks URLs, and resolves source conflicts.

Translate the company's disclosure taxonomy into real business and modelable drivers. **The core value is not writing a revenue breakdown table** — it is preventing the researcher and AI from mistaking accounting segments, management narrative, sell-side classifications, or concept-stock labels for economic substance.

If the output merely repeats company segment names, or fabricates undisclosed drivers as facts, this skill has failed.

## Mindset

Many investment research errors do not occur at the DCF, comps, or thesis conclusion stage — they occur earlier: you think you know what drives this company's growth, but in reality you have only accepted the bucket names the company gave you. The job of `driver-map` is to decompose disclosure taxonomy into business substance, then compress business substance into a small set of verifiable, trackable, modelable drivers.

Example: a company discloses a segment called "Industrial Solutions," which in reality bundles gas turbine equipment and long-term services together. Bad analysis writes "Industrial Solutions revenue $3.2bn" — that is just parroting the filing. Good analysis decomposes it: equipment sales $1.3bn at 22% gross margin, services $1.9bn at 45% gross margin, with service fleet utilization as the core driver. That is the value of `driver-map`.

**The single most important discipline**: undisclosed drivers must not be fabricated; they can only be written as `[来源待补]` (source pending), `[需查证]` (needs verification), or a researcher assumption. A driver map without sources is false precision.

## Financial-Data Integration

For elastic KPIs, first consult `references/kpi-drivers/` routed by business model. Pull data from `actuals-resolved.json` and process by revenue_split status:

1. revenue_split present → classify by source_type: `official-xbrl-dimension` = provider-structured, `filing-table-extracted` = provider-table-review → map to model bucket
2. revenue_split missing → read `full-filing.md`, LLM extracts disclosed split → label `llm-extracted-review`
3. No disclosure in source → label `not-disclosed`, do not fabricate

Rows with `review_required: true` require LLM interpretation of axis/member mapping and cannot be treated as final taxonomy directly. Does not override `financial-data` completeness.

## Trigger Scenarios

- "Help me decompose this company's revenue driver"
- "How do I break down this company's revenue"
- "What business is this segment / bucket actually"
- "Why is this business bucket broken down this way"
- "What business substance does this reported bucket correspond to"
- "What drives this company's growth"
- "Why did revenue grow but margin didn't"
- "How does backlog / orders flow into revenue"
- "Which is driving — price / volume / mix"
- "Does this business taxonomy seem odd"

## Input Clarification Requirements

| Dimension | Meaning | Default Assumption |
|---|---|---|
| **Subject** | Company / segment / product line / industry bucket | Company when user provides ticker; segment when user provides business name |
| **Research Purpose** | model / thesis / peer compare / earnings / journal | Default serves model and thesis |
| **Time Frame** | Latest annual, latest quarter, past 3-5 year trend | Latest verifiable disclosure + necessary historical comparison |
| **Driver Scope** | revenue / margin / backlog / price-volume-mix / installed base | revenue-first, expand to margin when necessary |
| **Source Cutoff** | Which filing / call / IR deck to use | Latest verifiable source; label `[来源待补]` when uncertain |
| **Save Requirement** | Write to company driver-map cache + topic artifact | Default save; human-readable `driver-map.md`, machine JSON to `internal/driver-map.json` |

If the user only says "decompose drivers," at minimum confirm company / business scope; if the user explicitly provides a business bucket, begin decomposing directly without expanding the scope into a full company study.

## Workflow

### Step 1: Reported Bucket → Business Reality

First translate the company's disclosed buckets into real business — do not accept the naming at face value.

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
| [segment] | [what is actually sold / done] | [customer or application] | [S1](url) | [gap] |

> For each core segment, attach a product/equipment image: download to the current topic's `_cache/images/<slug>-<product>.<ext>`, where `<ext>` uses the `extension` returned by the script.
>
> **Download method**: Read `_scripts/download-product-image.js` → replace `{{TARGET_URL}}` → invoke the current session's Playwright MCP `browser_run_code_unsafe` → decode with PowerShell on Windows, `python3` on macOS to write the file. Image source priority: ① Company Media Kit → ② Product page hero → ③ web search → ④ industry representative image → ⑤ `[缺图]` (image missing). See `stock-quickread` SKILL.md for details.

When encountering breakdowns like `GTE / GTS / Industrial Products / Industrial Solutions / CTS`, immediately trigger the Senior Analyst Radar: these may not be ordinary parallel segments, but rather a mixed breakdown across the gas turbine system value chain — product units, ancillary equipment, services, controls, or end-market dimensions.

### Step 2: Business Reality → Model Driver

Map each business bucket to observable drivers.

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| Equipment | units / MW / MTPA / orders | price / mix | orders, backlog, shipments | High / Medium / Low |
| Services | installed base | utilization / attach rate | service revenue, fleet hours | High / Medium / Low |

Common driver quick reference:

| Type | Metric | Applicable Context |
|---|---|---|
| Volume | unit shipment, capacity, MW, MTPA, rig count, installed base | Manufacturing / Energy / Equipment |
| Price | ASP, contract escalation, commodity pass-through | Pricing power analysis |
| Mix | equipment vs services, newbuild vs aftermarket, project vs recurring | Margin structure |
| Backlog/orders | order intake, book-to-bill, backlog conversion | Project-based / long-cycle |
| Utilization | fleet utilization, factory load, service hours, capacity factor | Services / O&M |
| Installed base | service attach rate, replacement cycle, parts intensity | Aftermarket |
| End-market proxy | LNG FID, data center power demand, aerospace build rate | Demand leading indicator |

### Step 3: Driver Quality

Every driver must be rated, and ratings cannot be based on intuition:

| Rating | Hard standard |
|---|---|
| **High** | Company directly discloses the KPI / bucket revenue / backlog / margin, with clear definition and trackability |
| **Medium** | Company partially discloses; requires peer / industry proxy supplementation, but direction is verifiable |
| **Low** | Primarily relies on inference, sell-side breakdown, or thematic association; must label `[来源待补]` / `[需查证]` |

### Step 4: Disclosure vs Inference / Proxy Strategy

Every key driver claim must clearly label its evidence status. Reasonable inferences can be written but cannot be presented as company facts; proxies can be used but must state proxy risk and model treatment.

Evidence status may only use:
- `company disclosed`: Company directly discloses this driver / KPI / bucket.
- `company implied`: Company language or disclosure structure implies this driver, but without a complete KPI.
- `peer proxy`: Approximated using peer or industry proxy.
- `researcher assumption`: Researcher assumption, must be verifiable subsequently.
- `unknown`: Not yet known, cannot enter base-case model.

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| [driver judgment] | company disclosed / company implied / peer proxy / researcher assumption / unknown | [proxy or none] | [ways proxy may mislead] | base case / sensitivity / scenario only / exclude |

Hard rule: `Low` confidence or `unknown` drivers cannot enter a single base case; they can only enter sensitivity, scenario, or be labeled `[来源待补]` until a stronger source is available.

## Output Structure

```markdown
## Driver Map

**Conclusion first**
[One sentence describing what driver framework this company / business should most fundamentally be understood through, and where the largest disclosure gap lies]

## 1. Reported Bucket → Business Reality

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
> For each core segment, attach a product/equipment image: download to the current topic's `_cache/images/<slug>-<product>.<ext>`, where `<ext>` uses the `extension` returned by the script.
>
> **Download method**: Read `_scripts/download-product-image.js` → replace `{{TARGET_URL}}` → invoke the current session's Playwright MCP `browser_run_code_unsafe` → decode with PowerShell on Windows, `python3` on macOS to write the file. Image source priority: ① Company Media Kit → ② Product page hero → ③ web search → ④ industry representative image → ⑤ `[缺图]` (image missing). See `stock-quickread` SKILL.md for details.

## 2. Business Reality → Model Driver

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|

## 3. Driver Quality

| Driver | Rating | Why | Ev | What would improve confidence |
|---|---|---|---|---|

## 4. Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|

## 5. Weird Buckets / Senior Analyst Radar

**Worth digging deeper**
- Oddity: [what is unnatural about the disclosure / bucket / KPI]
- May indicate: [1-2 explanations]

## 6. Implications

- [How this driver map changes model / thesis / peer compare]

```



## Artifact / Save Strategy

Write to industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

If the path is unclear → agent auto-creates per policy baseline §11.

## Growth Quality (200 characters)

Based on the driver decomposition above, answer three growth-quality questions:

| Dimension | Judgment | Evidence |
|---|---|---|
| Organic vs M&A | Past 3Y growth ~X% organic | M&A contributed ~Y% (estimated from acquisition disclosure) |
| Leading Indicator | [Backlog YoY / Orders YoY / Capacity ramp] | [specific figures] |
| Margin Trajectory | [Expanding / Stable / Compressing] | EBIT margin FY N-2 X% → FY N Y% |

## Anti-Pattern Self-Check

- ❌ Only repeats segment names without translating to business reality — sees Solutions / Systems / Industrial and doesn't probe further.
- ❌ Reported bucket, revenue, margin, backlog lack source / as-of; uses sell-side breakdowns in place of company disclosure without labeling as assumption.
- ❌ Treats peer proxy or researcher assumption as company disclosed fact.
- ❌ Low confidence driver enters base case directly without going into sensitivity / scenario.
- ❌ Only writes revenue drivers, doesn't ask whether margin drivers differ; substitutes historical CAGR for drivers.
- ❌ Treats theme association as a direct revenue driver.
- ❌ Sub-agent evidence cards used directly as final driver tree without main agent spot-checking URLs and taxonomy alignment.
- ❌ User only wants driver-map but outputs DCF / comps; needs to build a model but doesn't handoff to modeling skills.
- ❌ Driver confidence Low treated as core fact by subsequent thesis; clear awareness not logged into `research-journal`.

## Length Baseline

- Standard: 900-1600 characters + 3-4 tables. Below 700 characters often misses proxy strategy; above 1800 characters should narrow to core segments.


## Appendix: actuals-resolved.json

Complete field inventory -> `references/actuals-data-catalog.md`.

Structure: `meta` / `market_data` (15 fields) / `statements.income_statement` (13 fields) / `statements.balance_sheet` (10 fields) / `statements.cash_flow` (4 fields) / `segments` / `supplementary` / `source_map`.

Consumption rules: read actuals first → pull [S#]/[I#] labels from source_map (do not write [actuals]) → ratios only use actuals real values (no forward estimates).
