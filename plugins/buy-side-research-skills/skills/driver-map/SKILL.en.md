---
name: driver-map
description: Decompose revenue margin backlog price volume mix and segment drivers before modeling.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Driver Map

Decompose revenue margin backlog price volume mix and segment drivers before modeling.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — data pipeline, source verification chain, evidence protocol, artifact contract, save contract.
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

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
> **Download method**: `python _scripts/shared/download-image.py <url> --output <slug>`. Logo mode: `--logo <TICKER>`. Source priority: 1) company media kit -> 2) product page hero -> 3) web search -> 4) `[missing image]`.

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
> **Download method**: `python _scripts/shared/download-image.py <url> --output <slug>`. Logo mode: `--logo <TICKER>`. Source priority: 1) company media kit -> 2) product page hero -> 3) web search -> 4) `[missing image]`.

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

> **Appendix 执行指令**：写 artifact 正文之前先跑 `python _scripts/financial-data/actuals-to-appendix.py --tickers <TICKER_1>,<TICKER_2>,...`，输出直接嵌入上方的 `## Appendix: Financial Data`。禁止在 artifact 中留 `*(Run python...)*` 占位符。

