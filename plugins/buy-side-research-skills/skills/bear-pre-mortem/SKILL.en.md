---
name: bear-pre-mortem
description: Stress test an investment thesis and build the strongest opposing case with sourced risks.
---

# Bear Pre-Mortem

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

Stress test an investment thesis and build the strongest opposing case with sourced risks.

## Research Runtime Capsule

Follow `_shared/research-runtime.md` — data pipeline, source verification chain, evidence protocol, artifact contract, save contract.
Hook-enforced: `pre_write_gate` (source/tables/mermaid), `source_contract`, `table_render_integrity`, `mermaid_syntax`, `skill_structure_contract`, `evidence_ledger_floor`.

## Mental Approach

The most common way a researcher dies is confirmation bias: once a thesis is built, every piece of information gets interpreted in the thesis's favor. A pre-mortem is the reverse operation — **assume this trade lost 30% a year from now, and work backward to figure out why**.

Don't ask "what are the risks" — that question only produces softened, pro-forma answers. Ask "if I'm wrong, what's the most likely way I'm wrong" — this question forces the brain to search for concrete scenarios, and only then do the answers become useful.

For example, you're long ASML: "A year later this trade is down 30%. Looking back — TSMC cut 2026 capex from $38bn to $28bn, EUV orders evaporated. High NA is too expensive, customers realized they can get by with multi-patterning on older EUV tools. This isn't a risk checklist — it's a concrete scenario."

## Inputs & Bidirectional Usage

- The default input is an `alpha-thesis` output, a thesis draft in the current conversation, or research conclusions already crystallized in a topic journal.
- If the input is a long thesis, this skill outputs the strongest short pre-mortem.
- If the input is a short thesis, this skill reverses direction and outputs "why this short would lose money": the strongest long case / short squeeze / crowded short / upside catalyst stress test.
- If the thesis file carries YAML frontmatter, prioritize reading `key_assumptions`, `kill_criteria`, `valuation_anchor`, `conviction`, `health_status`; do not parse only the natural-language body.

## Mechanism Assumption Audit

Before writing the strongest opposing case, first extract and stress-test the thesis's implicit mechanism assumptions. A pre-mortem cannot only attack valuation and macro; it must also ask "does this business actually operate the way the thesis says it does."

| Assumption Type | Question to Stress-Test | Action When Unclear |
|---|---|---|
| Engineering / equipment chain | Do the key equipment, process flows, and capacity units actually support the thesis's volume / cost assumptions | Handoff to `mechanism-insight` first |
| Unit economics | Does the per-unit economics — per machine, per barrel, per project, per customer — actually hold | If the mechanism is unclear, `mechanism-insight` first; if the financial driver is unclear, `driver-map` first |
| Value capture | Where is value actually captured — by the OEM, supplier, service provider, channel, or customer | Handoff to `mechanism-insight` first |
| Driver linkage | How do mechanism changes transmit to revenue, margin, backlog, price-volume-mix | Handoff to `driver-map` first |

If the mechanism assumption is unclear, do not pretend the stress test is complete. First output a minimal handoff block:

```markdown
## Primitive Handoff Required

- Blocker: [which mechanism assumption / driver assumption does not hold or is unclear]
- Why it blocks pre-mortem: [which section of the short pitch / unit economics / path of pain it affects]
- Handoff: `mechanism-insight` / `driver-map`
- Inputs needed: [technical documents / filings / call transcripts / KPIs / segment data needed to fill the gap]
```

## Output Structure

### 1. The Smartest Short Seller's Pitch (300–500 words)

Write the short logic with the sharpest pen. This section must contain **zero hedging, zero "on the other hand", zero "however"**. The short mindset is the short mindset — let it run at full force.

Elements:
- One sentence that captures the short thesis ("this is a melting ice cube" / "valuation detached from fundamentals" / "there exists a [specific] governance / financial problem" / "cycle peak, downside mean reversion hasn't started yet" / "the story cannot hold because of [specific constraint]")
- 2–3 key pieces of evidence
- Corresponding price target / downside magnitude

### 2. Unit Economics Interrogation

Don't let GAAP financials lead you around — interrogate the unit economics:
- For each incremental customer / barrel of oil / machine, how much profit is actually made? How has this number changed over the years?
- Does the incremental margin match the story management is telling?
- If you add back everything labeled "non-recurring," "adjusted," "one-time," what does the true earning power look like?
- For CAC / LTV type businesses: is CAC rising? Are the LTV assumptions credible?
- Depreciation policy: is the actual asset life really that long? Does the long-run capex / D&A ratio expose a problem?

### 3. Accounting / Financial Red Flag Checklist

## Accounting Red Flag Formulas

For multilingual account-line-item cross-reference, see `references/policy/statement-line-items.md`.

| # | Red Flag | Formula | Input Source | Statement Location | Warning Threshold |
|---|---|---|---|---|---|
| 1 | DSO deterioration | Receivables × 365 ÷ Revenue | FS, FS | BS + IS | YoY +30% / > 2x peer |
| 2 | Inventory buildup | COGS ÷ Average Inventory | FS, FS | IS + BS | Significant YoY decline |
| 3 | Profit without cash support | OCF ÷ NI | FS, FS | CF + IS | Sustained < 0.7 |
| 4 | Asset aging | CapEx ÷ D&A | FS, FS | CF | Sustained < 0.7 |
| 5 | M&A impairment risk | Goodwill ÷ Equity | FS, FS | BS | > 50% |
| 6 | Equity dilution | SBC ÷ Revenue | FS, FS | Notes + IS | > 10% |

Sweep every item; each must provide: current number / warning threshold / status / Ev. Items flagged as problematic must be individually expanded with supporting argument.

| Red Flag Item | Current | Warning Threshold | Status | Ev |
|---|---|---|---|---|
| DSO / Receivables growth vs Revenue growth | DSO 78 days | > 1.5x revenue growth | 🚩 | [S1](./_cache/sources/ar-aging-note.md) |

| Inventory growth vs Revenue growth | ... | ... | ... | [S1](./_cache/sources/inventory-vs-revenue.md) |
| Capex vs D&A long-run ratio | 1.8x | Sustained > 1.5x warns of overinvestment | ... | [S2](./_cache/sources/capex-da-history.md) |
| Operating cash flow vs Net income long-run alignment | OCF/NI 0.6 | Sustained < 0.7 is a warning | 🚩 | [S3](./_cache/sources/ocf-ni-bridge.md) |
| Goodwill / Intangible asset ratio, recent impairment history | ... | ... | ... | [S4](./_cache/sources/goodwill-impairment-note.md) |
| Related-party transactions / Off-balance-sheet items | ... | ... | ... | [S5](./_cache/sources/related-party-note.md) |
| Segment consolidation, disclosure-bucket changes | ... | Any change warrants scrutiny | ... | [S6](./_cache/sources/segment-disclosure-history.md) |
| True cost of stock-based compensation (still profitable after adding back?) | ... | SBC > 30% of NI warns | ... | [S7](./_cache/sources/sbc-note.md) |
| Recent management / insider selling | ... | Concentrated selling is a signal | ... | [I1](https://example.com/form4-disclosure) |
| Recent audit / accounting policy changes | ... | Any change warrants scrutiny | ... | [S8](./_cache/sources/audit-policy-note.md) |

Every item in 🚩 status must be individually expanded, citing specific data points and comparison benchmarks.

### 4. What the Long Thesis Is Downplaying (3–5 items)

Return to the original long thesis and identify every instance of "not material in the long run," "short-term noise," "one-time impact" — the short seller's job is to argue that these are not noise but trend.

### 5. Base Rate / Historical Analogues

For this type of "story" (high valuation + high growth expectations / cycle peak + capex wave / similar business model + similar stage), **what have the historical sample outcomes been**? Pull 3–5 comparable cases, each with specific company / time window / outcome / Ev.

| Comparable Context | Time Window | Company / Ticker | Outcome | Ev |
|---|---|---|---|---|
| Similar valuation + capex cycle peak | 2014 Q3 – 2016 Q1 | Whiting Petroleum | Share price fell from $X to $Y, −90% | [S1](./_cache/sources/whiting-10k-2014.md) [S2](https://example.com/whiting-price-history) |

| ... | ... | ... | ... | ... |

Base rate is the strongest weapon against narrative — management will always say "this time is different"; base rate tells you "usually it's not." **But the force of base rate lies entirely in source authenticity** — fabricated comparable cases weaken the stress test.

### 6. Behavioral Bias Self-Check

What biases might the researcher behind this thesis ("I") have that blind me to the short logic?
- Am I anchored to a purchase price / historical high?
- Did I recently read bullish news and find myself in an echo chamber?
- Do I hold personal affection / aversion toward management?
- Is there sunk cost — spent a lot of time researching and unwilling to admit being wrong?
- Am I framing the question so the thesis looks right ("how much will it go up" vs "what's the probability it drops 30%")?
- Am I under social proof — does an investor / friend I respect also hold this?

### 7. The Path of Pain

If the short logic is correct, what does the share-price decline path look like?
- First leg: what catalyst triggers it, how much does it drop?
- Second leg: what subsequent event accelerates it?
- Long-term equilibrium: where is support?

This section lets you know in advance what the **loss path** looks like, so you don't get reframed by narrative in the moment ("this is just a technical correction," "market sentiment is overreacting").

## Artifact / Save Strategy

Write into the industry topic:
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

Path unclear → agent auto-creates per policy baseline §11.

## Growth Break Scenario

If revenue growth falls from X% to Y%:
- Margin impact: EBIT margin Z% → Z'% (fixed cost leverage reverse)
- Multiple impact: PE Xx → Yx (growth de-rate)
- Implied downside: −A%

Most likely signal that triggers the growth break: [1–2 leading indicators]

## Source Contract

> Short-side stress testing demands the highest standard of source authenticity — "could go wrong" must be backed by a specific filing / page / number, not just "looks suspicious."

**Density table**:

| Section | Mandatory Source Annotation | Exemption |
|---|---|---|
| §1 Short narrative | Specific number / event backing each allegation | The narrative itself |
| §3 Red flag walk | Filing source + page for every row: DSO / inventory / OCF / Capex / SBC | The red-flag judgment |
| §4 Base rate | Ticker + year + drawdown + source for every historical comparable case | — |
| §5 Kill criteria | Source of threshold (filing / IR / history) for every trigger condition | — |

**Completion Gate**: After writing, sweep §3 → every row has a filing source → §4 every case has ticker + source → `[待查]` ≤ 5 → Resources expanded.

## Anti-Patterns Checklist

- ❌ §1 reads like "on the other hand, some people also think" — rewrite, be the short seller yourself
- ❌ §3 goes through the motions, every row says "no obvious issue" — you didn't actually look, go back and look
- ❌ §5 has no specific comparable cases, only "many companies are like this" → pull concrete examples
- ❌ The entire piece has no specific numbers, no specific timeframes, no specific events → too hollow, rewrite
- ❌ Every short point is immediately "rescued" by a matching long rebuttal → this is not a pre-mortem, it's a debate; rewrite
- ❌ The thesis depends on engineering mechanisms, equipment chains, capacity units, or value capture, but no Mechanism Assumption Audit was done first → trigger `mechanism-insight` first.
- ❌ The strongest opposing case attacks revenue / margin / backlog / price-volume-mix, but the original thesis never decomposed the drivers → trigger `driver-map` first.

**Source-specific (short-side stress testing demands the highest standard of source authenticity)**
- ❌ §3 red-flag items have numbers but no filing source / page → add them
- ❌ §5 base-rate cases have no specific company name / timeframe / link → fabricated comparables weaken the stress test, must be added
- ❌ Cites "heard about" / "rumored" / Twitter / forums as short evidence → high legal risk, must find primary source or delete
- ❌ Concrete numbers / quotes appear with no source link → mark `[需查证]` or delete
- ❌ Uses management selling / insider transactions as evidence with no Form 4 / disclosure source → add it
- ❌ URL uncertain whether it actually exists → write a description plus `[link 待补]`, do not pretend

## Length Benchmarks

- Quick pre-mortem: 600–900 words, suitable for rapidly checking whether a thesis has obvious blind spots.
- Full bear pre-mortem: 1,000–1,800 words, suitable for a complete stress test before IC; must include unit economics, accounting red flags, base rate, and path of pain.
- Over 2,000 words usually means you are writing a full short thesis and should pivot to the `alpha-thesis` short-only structure or break it into multiple risk modules.

## Usage Notes

This skill is used after `alpha-thesis` is written and before the IC memo is submitted. If the original thesis still holds up after the stress test, the conviction is real; if obvious blind spots are discovered, go back and fix the thesis, reduce sizing, or simply walk away from the trade.

## Appendix: Financial Data

python _scripts/financial-data/actuals-to-appendix.py --tickers <TICKER_1>,<TICKER_2>,...

Embed the output in the artifact's `## Appendix: Financial Data` section (before `## Resources`). **Must execute BEFORE writing the artifact body** — never leave a placeholder.
