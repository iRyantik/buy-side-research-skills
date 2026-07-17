# Research Policy Baseline

> This is the English translation of [research-policy-baseline.md](./research-policy-baseline.md). The Chinese version is the source of truth.
>
> This file is the maintenance baseline for research skill authoring / review / batch sync. It is not the runtime authority.
> Skills at runtime cannot assume this file is automatically read; the real runtime truth lives in the invoked `SKILL.md`.
> This file now also serves as the shared runtime/source baseline: research skills no longer carry local copies of the long-form source policy, No Orphan Truth Claim, or Sub-Agent Evidence Protocol.

## 0. Role and Sync Order

- **Responsible for**: the complete research policy baseline, authoring reference master, and capsule batch-sync baseline.
- **Not responsible for**: unilaterally determining runtime behavior.
- When public research rules change, the fixed order is:
  1. Edit this file
  2. Sync all affected active research `SKILL.md` files
  3. If workspace high-level principles are affected, then edit `CLAUDE.md.template`

## 0.1 UTF-8 Text Discipline

All Chinese or multilingual text assets must use **UTF-8 without BOM**.

- `.md` / `.yaml` / `.json` defaults to UTF-8 without BOM.
- When modifying Chinese files, explicitly write back as UTF-8.
- Batch scripts rewriting text must specify UTF-8 to avoid mojibake.
- If Chinese text looks corrupted, first determine whether it's a console display issue or whether the file content was actually corrupted, then proceed.

## 1. Research Context

- **Role context**: Buy-side equity researcher, hedge fund / long-short orientation.
- **Primary coverage**: industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable energy, nuclear, emerging tech themes.
- **v3 core objective**: Not to maintain trade status, but to discover high-value research questions like a senior analyst, and to preserve genuinely thought-through cognitive increments as topic journal / Boss Brief.

## 2. Global Output Rules

- Default natural language output in English; tickers, company names, product names, source titles, URLs, YAML / JSON keys, financial and industry terms may be retained in their original language.
- For non-English company disclosure items, use the minimum-necessary principle of "source-language anchor + English explanation": on first occurrence, write official segments, products, KPIs, projects, programs, disclosure buckets, order/backlog classifications, regulatory/contract terms, customer/end-market names, source titles, and any terms that may require later source lookup as `Source Language (English translation)`; subsequent references default to the English short name unless the same table contains multiple easily-confused original-language buckets.
- Plain English is sufficient for: ordinary analysis sentences, takeaways, generic accounting/business concepts, previously-defined repeated items, non-critical source wording. Management quotes: preserve a short original quote only when the exact wording itself affects judgment; otherwise summarize in English and attach the source.
- All analysis must be conclusion-first. Do not write filler such as "Great question", "you're right", "it depends".
- When uncertain, say so directly and mark `[UNVERIFIED]` or `[SOURCE PENDING]`.
- Do not write sell-side boilerplate: company history, management bios, industry primers, generic SWOT, data-free qualitative statements, table recaps.
- Data tables must have a takeaway, and the takeaway must deliver structural insight — do not re-read the table.

## 2.5 Hooks-First Runtime Law

- Binary / machine-checkable runtime law goes into workspace hooks first, not scattered and duplicated across individual research skills.
- Skill-level `Research Runtime Capsule` retains only a very short reminder and non-binary delta.
- Once a source / boundary / structure rule enters a hook, the corresponding prose in the `SKILL.md` must be deleted.

## 3. Source Policy

Every factual statement, number, and quote must have a source link or clear source description. Researcher judgment itself does not need a source, but the facts on which the judgment is based must have sources.

Must have a source:
- Financial numbers, valuations, market data, prices, as-of data.
- KPI / operating data: production volumes, customer counts, ARR, inventory, orders, backlog, etc.
- Industry data: market share, pricing, capacity, demand, TAM.
- Management quotes, expert interview statements, regulatory statements, third-party judgments.
- Historical events and dates.

### 3.0 Claim-Level Source Contract (shared baseline, not skill-local boilerplate)

- `truth-like claim` = any verifiable or refutable fact, number, quote, business relationship, market data, industry fact, historical event, disclosure classification change.
- Every `truth-like claim` must be immediately followed by an inline clickable short source anchor; visible text stays short-code, but the short code itself must carry a real link, e.g. `[S1](./source.md)`, `[L1](./.cache/source.md)`, `[P1](https://...)` or `[I1](https://...)`. Do not embed dates or long URLs in the visible text.
- Body text example: `FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./source.md)`
- Every research artifact must end with one and only one `## Resources`, reusing the same clickable short anchors, and expanding source type, title/provider, as-of / filed date, page / table / URL location, fallback reason (if applicable). Short codes in the body and tables must be directly clickable; do not default to expanding full source metadata below tables.
- Multiple sources are written as `[S1](./source.md) [I1](https://...)`, not as `[S1][I1]`; only when the same source code has conflicting versions within the same artifact should you escalate to `[S1a](...)` / `[S1b](...)`.
- `judgment` / `synthesis` / `probability assessments` are not required to carry per-sentence sources, but the factual claims they rest on must already be source-backed.
- Claims without sources must only be written as `[UNVERIFIED]` / `[SOURCE PENDING]` / `not disclosed` / `working hypothesis`, and must not masquerade as facts.

### 3.1 Source Hierarchy and Controlled Fallback

- Use two source tracks rather than one flat hierarchy.
- Disclosure-fact track: `topic-local evidence cache > primary public > trusted third-party > web`. Use this for company facts, segment / KPI disclosure, customer / project / supply-chain relationship facts, management quotes, and regulatory / filing facts.
- Market-snapshot track: `topic-local evidence cache / financial-data > trusted third-party > web`. Use this for `market_quote`, `valuation_snapshot`, `price_action`, `kline_snapshot`, `consensus`, `financial_snapshot`, `fx_snapshot`, `adr_ah_premium`, and clearly market-data-like liquidity / market-context fields.
- `financial-data` is the highest-value reusable structured cache inside `topic-local evidence cache`. It takes priority over trusted third-party providers for market / snapshot fields, but it does not replace `primary public` when wording, segment definition, or disclosure truth must be checked.
- Optional provider bridge rule: when a skill explicitly invokes `trusted-market-bridge`, A-share / Hong Kong / US market-snapshot fields may use Longbridge as the default trusted third-party layer before generic internet fallback. Supported bridge domains now include market data, price action, valuation, FX, ADR/AH premium, consensus, financial snapshots, and high-level `market_screen` signals. This does not upgrade Longbridge into `primary public source` or company-truth authority.
- `topic-local evidence cache` means this research workspace's topic `.cache/`, company `financial-data`, source-tracked ingest markdown, and saved internal data packs; it is different from home-market / local-language source priority.
- Within the same quality tier, prefer `home-market / local-language source`: local-language news / event sources for the issuer, main listing venue, regulator, or operating country; primary listing / trading-market data for price, valuation, liquidity, borrow, FX, and cross-market fields.
- Do not maintain market-specific provider whitelists in global or skill rules. If a global, English, or non-home-market fallback is used because the local-language / home-market source is unavailable or weaker, the final `## Resources` list must state the fallback reason.

- The shorthand order is not a single-line total order, but dual-track: disclosure-fact track `topic-local evidence cache > primary public > trusted third-party > web`; market-snapshot track `topic-local evidence cache / financial-data > trusted third-party > web`.
- `topic-local evidence cache`: current topic `.cache/`, company `financial-data`, source-tracked markdown after ingest, saved internal data packs; does not include research artifacts, which can only serve as navigation, routing, and pending-review clues.
- `primary public source`: filings, IR, exchange, regulatory, government, industry association, company website, and other publicly verifiable original sources.
- `trusted third-party`: provider aggregation layers such as Longbridge; the current unified entry preference is `trusted-market-bridge`, but it only serves market / snapshot fields and does not elevate to company truth.
- `internet source`: market/provider data on public web pages, financial sites, trading pages, public news pages, public database pages.
- `internet source` may only auto-fallback when **locally absent** and the **field inherently belongs to the market-snapshot track**.
- If `trusted-market-bridge` is used, preserve provider-specific anchors such as `[LBG1](https://longbridge.example.com/quote/NVDA.US)` and expand provider, symbol, market, as-of, and fallback reason in the final `## Resources` list.
- `internet source` must not impersonate company-disclosed fact. Business facts, segment profits, company-disclosed KPIs, customer / project / supply-chain relationships, management quotes, undisclosed driver gaps — when source is absent — continue to write `[UNVERIFIED]` / `[SOURCE PENDING]` / `not disclosed`.
- After a successful fallback, data may enter the main table / body, but must be explicitly marked with `internet source`, provider, as-of, URL / source location.
- If `internet source` conflicts with local / primary public source, the conflict must be preserved and noted; never silently overwrite.
- Even when fallback is permitted, if a reliable source cannot be obtained from the public web either, continue honest degradation: `[UNVERIFIED]` / `[SOURCE PENDING]` / `not disclosed`.

Source quality:
- Primary original: SEC filings, exchange announcements, company IR, earnings calls, regulatory / government data.
- Secondary authoritative: transcripts, Bloomberg / FactSet / CapIQ / Visible Alpha, industry research firms, expert interview platforms.
- Tertiary interpretive: Reuters, Bloomberg News, FT, WSJ, Nikkei, sell-side reports, industry media.
- Clues only: social media, forums, chat logs, rumor screenshots, personal blogs, broker-dealer relay.

Use primary over secondary whenever possible. When multiple sources conflict, mark the conflict — do not pick the convenient one.

### 3.2 Source Priority (shared by all Research Skills)

```
1. actuals-resolved.json    Local cache, machine-harvested, highest confidence
   → 22 core line items + Market Cap/PE/EV/EBITDA/Beta/52w
   → marked in skills as [actuals], not [S#]/[I#]

2. [S#] Company disclosure   IR PDF, annual report, AGM, earnings transcript
   → fields not in actuals → WebFetch/Playwright verify → [S1-S9]

3. [I#] Third-party          Industry reports, news media, Yahoo Finance, sell-side reports
   → actuals and company disclosure both unavailable → WebFetch/Playwright verify → [I1-I20]

For the same claim, only cite the highest priority. Revenue is already in actuals → don't mark [S1]. Q1 orders not in actuals → [S1]. Market share → [I1].
```

### 3.3 RAG Source Verification Pipeline (shared by all Research Skills)

**Discipline**: Do not use WebSearch AI summary numbers to directly write claims. Every external claim must come from the source page.

**Two-layer data architecture**: 0-Actuals (local, 0s) → 1-External (WebFetch/Playwright/curl, requires verification)

**Page fetch fallback chain**:

```
Tier 1  WebFetch(url)                           — static pages
   ↓ fail
Tier 2  Playwright MCP browser_navigate + 
        browser_snapshot                         — dynamic / JS-rendered pages
   ↓ fail
Tier 3  curl -sL url                             — raw HTTP fallback
   ↓ fail
Tier 4  [UNVERIFIED]                             — honest degradation
```

- Source verification starts at Tier 1; only escalates on failure.
- WebSearch may be used to **discover candidate URLs**, but must never be used to directly cite AI summary numbers.
- Every verified claim records method, tier, and timestamp.

## 4. Sub-Agent Evidence Protocol

Sub-agents return evidence cards only. The main agent synthesizes.
Evidence cards must carry source, status (verified / plausible / unverified / disputed / fabrication_risk), method, tier, and as-of.

### 4.1 Sub-Agent Prohibition List

Sub-agents must not:
- Write final research artifacts
- Make investment judgments
- Decide routing or  recommendations
- Run unstructured searches beyond their assigned evidence-gathering scope
- Return claims without source or status markup

## 5. No Orphan Truth Claim

Any truth-like claim appearing in a research artifact body more than once across paragraphs must be tracked back to a single source. If a claim is repeated without a source, it is an orphan claim. Orphan claims must be either:
- Killed (removed), or
- Re-anchored to a source, or
- Marked `[SOURCE PENDING]` with an explicit verification plan.

## 6. Anti-Sell-Side Rules

Research artifacts must not exhibit sell-side patterns:
- ❌ Company history by chapter
- ❌ Management bios
- ❌ Generic industry primer
- ❌ SWOT without specific data points
- ❌ 5-year historical financial table without structural takeaway
- ❌ Recent event chronology without investment implication
- ❌ Table re-read disguised as takeaway
- ❌ "Founded in..." / "Headquartered in..." / "Management is experienced..."

## 7. Evidence Ledger

Evidence tracking is ticker-scoped, not artifact-scoped. Cross-artifact reuse is the default.

- Ledger path: `.cache/evidence/<TICKER>.evidence.json`
- Init: `evidence_ledger.py init <DIR> -t <TICKER>` (ticker mode only — artifact-scoped mode is deprecated)
- Each claim carries: id, source code, text, status, method, tier, quote, section, checked_at, provenances, attempts
- Statuses: verified, plausible, unverified, disputed, fabrication_risk
- Method tiers: actuals=0, WebFetch=1, Playwright=2, curl=3, WebSearch=4, unknown=4
- Coverage threshold: <80% verified+plausible → block (enforced by pre-write gate)

## 8. Actuals Data Contract

`financial-data` writes structured actuals to `.cache/financial-data/internal/actuals-resolved.json`. Research skills consume it — do not bypass it to fetch raw financials directly.

- 22 core line items: Revenue, COGS, Gross Profit, SG&A, R&D, EBIT, Interest Expense, Pre-Tax Income, Net Income, SBC, Cash, AR, Inventory, Goodwill, Short-Term Debt, Long-Term Debt, Bonds Payable, Total Equity, Operating CF, CapEx, D&A, Dividends
- Market data: Market Cap, PE, EV, EBITDA, Beta, 52w High/Low, Share Price, Shares Outstanding
- Each value carries source provenance via `source_map`
- Actuals freshness gate: latest_quarter_period >180 days → block (pre-write gate CHECK 10)

## 9. Single-Industry Primary Residence

Each company's research lives in exactly one industry directory, determined by the earliest research artifact date for that company.

- Company artifacts live at: `industry/<industry-slug>/companies/<ticker>/`
- A company mentioned in research for a second industry gets a cross-reference in that industry's `index.md`, but files do not move.
- When in doubt, check artifact timestamps — earliest wins.
- For cross-industry companies (e.g., Mycronic), the industry with the first research artifact is primary.

## 10. Segment Data Priority

When both business-segment and geographic-segment data are available, business segments take priority for:
- Revenue driver decomposition
- Margin analysis
- Peer comparison
- Model driver construction

Geographic segments are secondary and should only be used when business segments are not disclosed or when geographic mix is itself a key thesis driver (e.g., tariff exposure, supply-chain relocation).

## 11. Skill Routing Table

| Scenario | Skill |
|---|---|
| Zero-baseline physical intuition for an industry | `teach-in` |
| Unfamiliar company first pass | `stock-quickread` |
| Full industry picture + investment judgment | `industry-landscape` |
| Business / segment / disclosure history | `company-history` |
| Industry mechanism / engineering principles / equipment chains | `mechanism-insight` |
| Market sizing / TAM estimation | `market-sizing` |
| Revenue / margin / backlog / price-volume-mix drivers | `driver-map` |
| Market expectations / priced-in / variant-view gap | `consensus-map` |
| Scenario-based L/S ranking | `candidate-screener` |
| Cross-market peer comparison | `peer-deep-dive` |
| Competitive barrier quantification | `moat-analysis` |
| Catalyst timeline | `catalyst-map` |
| Management capital allocation | `capital-allocation` |
| Bull/base/bear odds memo / assumption tracing | `scenario-model` |
| Pre-earnings setup | `earnings-setup` |
| Post-earnings quick verdict | `post-earnings-quick` |
| L/S pair | `pair-trade` |
| Financial statements / structured actuals | `financial-data` |
| Model / DCF / comps | `driver-map` / `driver-map` / `driver-map` |
| Track coverage state | `coverage-tracker` |
| Generate daily coverage briefs / intraday alerts | `coverage-monitor` |
| Capture earned insights | `research-journal` |
| Structure voice-transcribed meeting notes | `meeting-minutes` |
| Upgrade plugin / sync workspace | `update-agent-runtime` |
| Initialize a new workspace | `init-workspace` |
| Ingest raw materials | `ingest` |
| New session routing + path resolution | `agent (auto-scaffold per policy baseline §11)` |
