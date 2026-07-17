---
name: candidate-screener
description: Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.
---

# Candidate Screener

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Turn a theme, event, or screen into a sourced candidate-mining funnel for mispriced high-purity stock ideas.

## Research Runtime Capsule

**MUST read the following files before executing this skill:**
- workspace `.references/runtime/research-runtime.en.md` §1 (Data Pipeline) §2 (Source Verification) §2.1 (Material Collection) §2.2 (Source Discipline) §2.5 (Image Download) §4 (Output Contract) §5 (Save Contract)

**Auto Hook Defense:** `pre_write_gate` (source/tables/mermaid/image) `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

## Mental Model

When a researcher says "mine for stocks," what they really want is not more names but a testable buy-side funnel: where the theme has real economic exposure, which part of the value chain is most likely mispriced, and which companies simultaneously satisfy **high purity, fast growth, reasonable valuation, and not yet fully discovered by the market**.

**No ranking is regime-invariant.** The same company can be a Top Idea in the Pluggable era and a Reject in the CPO era. Rankings must be scenario-bound and must provide both L/S directions — you cannot push longs while ignoring shorts. A static funnel = single-scenario assumption = missing the biggest risk.

AI's advantage is not running a complete universe screen. Bloomberg / FactSet / Longbridge and similar tools are more reliable for full-market coverage. AI's differentiated value lies in translating vague themes into verifiable business characteristics, then sorting candidates by scenario into a multi-dimensional funnel: **Steady Longs, Scenario Bets, Direction-Flip types, Event-Driven plays, Valuation-Convergence pairs**. The goal is to help the researcher chase fewer hot-concept stocks and have a contingency plan when regimes shift.

**Most important discipline**: "not yet discovered by the market" is not a fact — it can only be assessed via proxies. Low sell-side coverage, un-re-rated valuation, price not reflecting the theme, missing theme classification, and narrative not yet diffused must all have sources or be tagged `[需查证]`.

## Trigger Scenarios

Use this skill when the user asks:

- "Use candidate-screener to mine [theme / industry chain / value-chain pocket]"
- "Mine for stocks / find stocks / find stocks the market hasn't discovered yet"
- "Find [theme] targets with high purity, fast growth, cheap valuation"
- "Are there any hidden winners / mispriced pure-plays in [theme]"
- "Find long / short candidates from [event / policy / capex cycle]"
- "Find companies with EV/EBITDA < 8x, FCF yield > 8%, growth not collapsing"
- "Stocks similar to [Company X] but cheaper / not yet discovered by the market"
- "Scenario-ranked sorting / L/S sorting / push stocks by scenario"
- "Under [CPO/electrification/tariff/...] scenario, what should be long and what should be short"
- "Dynamic L/S perspective / regime-aware stock mining"

Do not use for:

- Verifying the truth of a single news item, customer relationship, or supply-chain claim: use `information-impact`.
- First-pass on an unfamiliar company: use `stock-quickread`.
- Industry first-pass, profit pool, and KPI/source map: use `industry-landscape`.
- Unclear engineering mechanisms, equipment chains, or process flows: first use `mechanism-insight`.
- Unclear company revenue / margin / backlog / price-volume-mix drivers: use `driver-map`.

## Input Clarification Requirements

If the user's input is sufficiently unambiguous, declare default assumptions and begin directly — do not slow down stock mining with a long questionnaire. Only ask follow-up questions when the missing item would change the candidate direction.

| Dimension | Meaning | Default Assumption |
|---|---|---|
| **Theme / Signal** | Optical module equipment, AI power, nuclear fuel, a policy event, a financial condition | Defined by the narrowest investable boundary of the user's original wording |
| **Time Window** | 3M / 12M / 24M+ | 12M, with 3M catalyst considered |
| **Direction** | Long / Short / Both | Long-biased, but retain possible short / reject |
| **Market Preference** | US / Greater China A-H-ADR / Japan-Korea / Global / No restriction | User's coverage universe: Greater China + Global industrial / technology themes |
| **Purity Requirement** | Core business >50%, segment >30%, indirect / supply-chain | Prioritize direct / pure-play; indirect gets lower weight |
| **Growth Requirement** | revenue / backlog / order / capacity / margin inflection | Tag `[需查证]` when no source exists |
| **Valuation Requirement** | PE, EV/EBITDA, FCF yield, SOTP, relative to peers | Use available market snapshot; tag `[需查证]` if missing |
| **Discovery Edge** | Why the market may not have priced it in | Use proxies, do not state as fact |
| **Liquidity / Size** | Minimum ADV / market cap | Greater China >= 100M USD ADV; US >= 50M USD ADV; small-caps listed separately with risk noted |

## Candidate Mining / Stock Discovery

A unified approach for themes, events, screens, and hybrid conditions. Internally, decompose the input into three signal types — do not ask the user to choose a mode:

| Signal | Description | Example |
|---|---|---|
| **Theme signal** | Theme, event, policy, capex cycle, value-chain pocket | Optical module equipment, AI data-center power, export controls |
| **Fundamental / valuation filter** | Growth, margins, cash flow, valuation, ROIC, capex intensity | EV/EBITDA < 8x, FCF yield > 8%, backlog accelerating |
| **Discovery edge** | Why the market may not have fully priced it in | Low coverage, misclassification, non-mainstream listing venue, un-re-rated valuation, narrative not yet diffused |

### Reasoning Path (must be explicit)

**Step 1: Define Scenarios + Theme Boundary**

**1a. Scenario Definition** (newly added)

Decompose the theme into 2-3 macro regimes, each tagged with probability + key catalyst trigger threshold. Regime is the prerequisite for ranking — the same company's L/S direction can be opposite under different regimes.

| Regime | Definition | Probability | Catalyst Trigger |
|---|---|---|---|
| R1: Current Dominant | Existing technology path dominates | 60% | — |
| R2: Transition | New paradigm begins to penetrate | 30% | [Specific event] volume shipments |
| R3: New Paradigm Mainstream | New paradigm > 15% penetration | 10% | [Specific event] mass production |

When regimes >= 3, consider pushing different stocks for different stages. Ranking without defining scenarios = implicitly assuming "current regime unchanged" — this assumption must be made explicit.

**1b. Theme Boundary and Value-Chain Pockets**

Decompose the user input into 3-6 investable pockets. Example: `optical module equipment` cannot directly equal "optical module concept stocks" — it should be decomposed into pockets like coupling equipment, die bonding, burn-in / test, automation, and flag which segment is most likely to capture profit.

**Step 2: Theme -> Verifiable Business Characteristics**

Translate each pocket into observable business traits:

- revenue purity: share of relevant revenue or segment exposure.
- growth proof: orders, backlog, shipment, capacity, customer capex, price / mix, margin inflection.
- value capture: scarce processes, customer certification, supply bottlenecks, installed base, aftermarket, bargaining power.
- disclosure handle: what segment / KPI the company uses for disclosure, where misreading is likely.

**Step 3: Overlay Stock-Mining Criteria**

Default to six-dimension scoring. Do not rank by theme heat alone:

| Dimension | Weight | High-Score Standard |
|---|---|---:|
| Business purity | 22% | Theme-related business has verifiable share of revenue / profit / backlog, preferably >50% |
| Growth evidence | 18% | Sourced evidence of revenue / order / backlog / capacity / margin acceleration |
| Valuation appeal | 18% | Not expensive relative to history, peers, or growth quality; cheap but deteriorating must be downgraded to value trap |
| Discovery edge | 18% | Low coverage, misclassification, non-mainstream listing venue, un-re-rated valuation, price not reflecting — use proxies |
| **Scenario sensitivity** | **12%** | Works across multiple scenarios or has clear direction when regime flips; magnitude of valuation flip is quantifiable; not "neutral-to-slightly-positive" in every regime |
| Catalyst / liquidity / tradability | 12% | 3-12M verification node exists, liquidity is tradable, borrow / squeeze risk is manageable |

**Step 4: Candidate Tiering (Five Buckets)**

| Bucket | Definition | Handling |
|---|---|---|
| **Top Ideas** | 1-3 names simultaneously satisfying purity, growth, valuation, discovery edge (under current regime) | Recommended for deep research |
| **Scenario Bets** | Only valid under a specific scenario; does not work under current regime. Waiting until confirmed = already doubled | Small position 2-5%, size based on zero-tolerance, do not add based on valuation cheapness |
| **Watchlist** | Mechanism is right, but valuation, source, liquidity, or catalyst is not yet sufficient | Wait for verification, do not force |
| **Obvious / Already Priced** | Theme-relevant but market has clearly priced or crowding is high | Use as peer / hedge / avoid chasing |
| **Rejects / Value Traps** | Cheap but growth collapsing, low purity, unverified linkage, high theme beta but weak fundamentals | Clearly state rejection reason |

**Step 5: Next Verification**

Top Ideas must include  verification paths:

- Company first-pass: `stock-quickread`
- Business / segment / KPI to model driver: `driver-map`
- Complex engineering mechanism: `mechanism-insight`
- Single customer / order / supply-chain claim: `information-impact`
- Horizontal comparison of 3-8 core companies: `peer-deep-dive`

## Output Structure

> **Source contract**: For all tables below, columns involving valuation multiples, probability percentages, flip magnitude, spread differences, and scoring numbers **must carry a source anchor per row** ([S#](url) or [I#](url)). Valuation from market_data tags `[I#]`, business data from actuals tags actuals, external industry reports tag `[I#]`.

```markdown
## §1 Conclusion First

[Current regime judgment + most robust L/S combination across scenarios + most critical scenario-valuation insight]

## §2 Scenario Definition

| Regime | Definition | Probability | Catalyst Trigger | Valuation Environment | Ev |
|---|---|---|---|---|---|
| R1: [Current Dominant] | ... | 60% | — | PE 15-30x | [S#](url) |
| R2: [Transition] | ... | 30% | [Event + threshold] | Scarcity premium |
| R3: [New Paradigm] | ... | 10% | [Event + threshold] | Old-business valuation compression |

## §3 Scenario Stock-Push Matrix (Main Table)

Rows = companies, Columns = 3 regimes. Cell format: **Direction Weight · Current Valuation · Scenario Re-rating Direction · One-liner · Key KPI** (taken from workspace `.references/kpi-drivers/`, the single most important number for this industry). Note: use `·` inside cells, NEVER `|` (breaks table rendering)

| Company | Ticker | R1: [Current] | R2: [Transition] | R3: [New Paradigm] | Valuation Flip Magnitude | Ev |
|---|---|---|---|---|---|---|
| AAA | TICKER | Long High · PE 18x · ↑ · logic · KPI | Long High · → ↑ · logic · KPI | Long High · → ↑↑ · logic · KPI | +60% | [S#](url) |

Valuation Flip = re-rating magnitude from R1→R3, must be quantified. Negative value = short-side gain when regime switches.

## §4 Cross-Scenario Synthesis

### §4.1 Steady Longs (works across all scenarios)

| Stock | Current Valuation | Cross-Scenario Logic | Upside | Downside Ev |
|---|---|---|---|---|

### §4.2 Scenario Stock-Push Table (reverse index: scenario → action → stock)

| Scenario Trigger | Action | Stock | Position | Strategy Archetype | Current Valuation | Target Valuation | Logic Ev |
|---|---|---|---|---|---|---|---|
| Current base | Long | AAA | Core | Generational upgrade | PE 18x | PE 25x | ... |
| CPO>15% | Long | BBB | Small bet | Small bet | PS 8x | PS 20x | 0→1 |

**Strategy Archetypes** (7 types): Cross-Scenario Long / Small Bet / Flip Hedge / Event-Driven / Valuation Convergence / Generational Upgrade / Narrative Arbitrage

### §4.3 Direction-Flip Types (largest valuation flip)

| Stock | R1→R3 Valuation Path | Flip Magnitude | Core Logic Ev |
|---|---|---|---|

### §4.4 Valuation-Convergence Pairs (spread trade, optional)

| Long | Short | Current Spread | Fair Spread | Convergence Catalyst Ev |
|---|---|---|---|---|

## §5 Base Case Funnel (under current regime)

### Top Ideas (1-3)

| # | Stock | One-liner | Purity | Growth | Valuation | Discovery | Scenario | Total Score Ev |
|---|---|---|---|---|---|---|---|---|

### Scenario Bets (small-bet tier)

| Stock | Scenario Bet On | Current Valuation | Target Valuation | Why Not Wait Until Confirmed Ev |
|---|---|---|---|---|

### Watchlist

| Stock | What's Missing |
|---|---|

### Rejects

| Stock | Current Valuation | Reason for Rejection Ev |
|---|---|---|

## §6 Catalyst Calendar + Valuation Trigger Points

| Time | Event | Affected Stocks | Valuation Trigger | Scenario Switch Ev |
|---|---|---|---|---|

## §7 Kill Criteria (position exit conditions)

| Stock | Exit Signal | Valuation Floor Ev |
|---|---|---|

## AI Universe Caveat

[Same as above]
```

## Shared Hard Standards

### 1. Every business linkage must have a source or gap marker

Each candidate's exposure / purity / customer / product / value-chain role must have a source link or an explicit `[需查证]`. Sell-side theme classifications, social-media lists, and concept-stock articles can only serve as leads, not as business-linkage evidence.

### 2. Growth must have verifiable evidence

Growth evidence priority:

| Evidence Type | What It Can Support |
|---|---|
| Company-disclosed revenue / segment / backlog / order / shipment / capacity / margin | Can enter Top Ideas |
| Customer capex, industry shipment, price / utilization proxy | Can support pocket or watchlist |
| Sell-side forecasts, third-party industry reports | Can serve as leads; must tag source quality |
| Market rumors / social media / screenshots | Can only serve as follow-up; do not enter Top Ideas |

### 3. Valuation cheapness must be assessed together with growth quality

- **Cheap + growth intact**: Can enter Top Ideas.
- **Cheap + growth uncertain**: Watchlist.
- **Cheap + growth deteriorating**: Reject / Value Trap.
- **High growth + fully priced**: Obvious / Already Priced, unless there is a clear variant view.

### 4. Discovery edge can only be stated as proxy

Permitted proxies:

- Low sell-side coverage or mainstream models not covering the segment.
- Valuation multiples not re-rated relative to theme peers.
- Stock price not reacting in line with the theme basket.
- Company misclassified in a traditional industry, with theme exposure hidden in a segment / subsidiary.
- Non-mainstream listing venue, local-language disclosure, ADR/A/H structure causing coverage gap.

Prohibited formulations:

- "Market hasn't discovered it yet" without any proxy.
- "Undervalued" without valuation or price-reaction anchor.
- "High purity" without revenue / profit / backlog / segment evidence.

### 5. Bucket count must be constrained

- Top Ideas: 1-3 (under current regime).
- Scenario Bets: 1-3 (small bets that only work under a specific scenario).
- Watchlist: 3-7.
- Rejects: At least 2, unless the universe is extremely narrow.

If there are too many candidates, tighten by purity and discovery edge first; do not output 20 tickers and leave the user to screen them.

## Artifact / Save Policy

File naming follows workspace `CLAUDE.md` §3.2: `YYYYMMDD-[skill]-[Industry-Name][-variant].ext`.
Save to `industry/<industry>/panorama/<skill-slug>/`.
If the path is unclear, the agent resolves the industry per CLAUDE.md §3.4.

## Workflow Links

| Finding | Next Step |
|---|---|
| Top Idea is an unfamiliar company | `stock-quickread` |
| Top Idea's revenue / margin / backlog driver is unclear | `driver-map` |
| Value-chain pocket depends on engineering mechanism, equipment chain, process | `mechanism-insight` |
| A single customer, order, supply-chain, or supplier-relationship claim is unverified | `information-impact` |
| Horizontal comparison of 3-8 core candidates needed | `peer-deep-dive` |
| Theme's priced-in status, buy-side bar, or consensus debate is unclear | `consensus-map` |
| Top Ideas need to form long / short thesis | `alpha-thesis` / `bear-pre-mortem` |

## Anti-Pattern Self-Check

After writing, must self-check; rewrite if any of the following is triggered:

### Fabrication / Concept-Stock Piling

- ❌ Only listing hot tickers without explaining value-chain pocket and purity.
- ❌ Candidate's business exposure has no source link and is not tagged `[需查证]`.
- ❌ Treating sell-side theme classifications, social-media lists, concept-stock articles as business-linkage basis.
- ❌ Tier-N supply chain only marked "related" without specifying supplier link, product, timeframe.
- ❌ Treating sub-agent evidence cards directly as final Top Ideas; the main agent must spot-check, deduplicate, tier, and rank.

### Stock-Mining Quality

- ❌ Not explaining why the market may not have priced it in.
- ❌ Recommending solely because valuation is cheap, without checking whether growth is deteriorating.
- ❌ Recommending solely because growth is fast, without checking whether valuation is fully priced.
- ❌ Top Ideas exceeding 3, indicating failure to constrain.
- ❌ Not listing Obvious / Already Priced, leading the user to chase hot concept stocks.
- ❌ Not listing Rejects / Value Traps, causing the cheap screen to become a value trap list.

### Workflow Boundaries

- ❌ User asks whether a single claim is reliable but stock mining begins directly; should first use `information-impact`.
- ❌ Engineering mechanism is unclear but names are still forced; should first use `mechanism-insight`.
- ❌ Company driver is unclear but growth thesis is still written; should first use `driver-map`.
- ❌ Making strong-conclusion extrapolations from `[需查证]` customer / order / supply-chain relationships.

### Scenario-Related

- ❌ Ranking without defining scenarios — the implicit assumption of "current regime unchanged" is the biggest assumption gap.
- ❌ Treating single-scenario recommendations as cross-scenario recommendations — a Top Idea only valid under the current regime must be clearly marked.
- ❌ Scenario Bets without position caps, adding based on valuation cheapness instead of sizing by zero-tolerance.

## Length Benchmarks

- Standard Candidate Mining (with scenarios): 2,000-3,500 words + 4-6 tables.
- Quick stock mining: 800-1,500 words, Top Ideas at most 2, scenario definition may be simplified.
- Deep universe pass (with full L/S by scenario): 3,500-5,000 words, grouped by regime.

## Boundary with information-impact

Both skills involve source verification and claim decomposition, but the information flow direction is opposite:

| | candidate-screener | information-impact |
|---|---|---|
| Input | Theme, event, screen, stock-mining preference | Known claim, news, rumor, screenshot |
| Task | Starting from hypothesis, find researchable names | Verify truth + research relevance |
| Direction | Outbound: from theme outward to find | Inbound: information has already arrived |
| Output | Top Ideas / Watchlist / Rejects / Next verification | Verdict / What not to infer / Action |

Do not confuse:

- "Does the optical module equipment chain have high-purity, fast-growing, cheap, undiscovered stocks" -> `candidate-screener`
- "I heard X is an NVIDIA optical module supplier — is that reliable?" -> `information-impact`
- "This news is true, and I want to find beneficiary stocks following the news logic" -> first `information-impact`, then `candidate-screener`


