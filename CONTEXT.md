# CONTEXT.md — Buy-Side Research Skills

> Domain glossary and design decisions for the buy-side-research-skills plugin.
> This file is about language and architecture, not implementation details.

## Glossary

### Workspace structure

- **industry** — Top-level research organization. Each industry is a directory: `industry/<industry-slug>/`.
- **company** — A ticker-scoped subdirectory under an industry: `industry/<industry>/companies/<ticker>/`. A company has exactly one **primary industry**.
- **primary industry** — The first industry where a company had a research artifact written. Determined by `index.md` registration date, not by revenue/profit thesis. Other industries only cross-reference.
- **topic** — Legacy term (deprecated). Previously `topics/` was the workspace root. Now replaced by `industry/`. The `topics/` directory no longer exists on disk.
- **artifact** — A dated research file: `YYYY-MM-DD-<skill>-<qualifier>.md`. Only saved in the company's primary industry directory.

### Source system

- **[S#](url)** — Company disclosure source (IR PDF, annual report, product page). Primary evidence.
- **[I#](url)** — Third-party source (industry report, news, market data). Secondary evidence.
- **[P#](url)** — Physical constant or materials database reference (MatWeb, CRC, engineering handbook).
- **[需查证]** — Unverified claim. Only allowed after all fallback tiers have failed (WebFetch → Playwright → curl).
- **[缺图]** — Missing product image. Only allowed after image download was attempted and logged in evidence ledger.
- **[actuals]** — Deprecated. Do not use in artifacts. Use `source_map` to map actuals fields to [S#] tags.
- **bare anchor** — An `[S#]` or `[I#]` without a URL. Always blocked by hooks.
- **verification badge** — Previous convention: `[S1](url) (Playwright ✅)`. Removed in v5.7.0. Verified sources carry no badge; only unverified claims are marked.

### Evidence system

- **evidence ledger** — Ticker-scoped JSON file: `_cache/evidence/<TICKER>.evidence.json`. Tracks every claim with method, tier, attempts, and verification status.
- **Claim Fill Pipeline** — Four-tier fallback for verifying external claims: Tier 0 (actuals) → Tier 1 (WebFetch) → Tier 2 (Playwright) → Tier 3 (curl) → Tier 4 ([需查证]).

### Gate system

- **Pre-write gate** — Hook that intercepts Write/Edit tool calls BEFORE the file lands on disk. Checks source format, image existence, [需查证] count, actuals freshness, pipeline header accuracy, and evidence coverage.
- **Post-write gate** — Hook that runs after file write. Checks source contract, claim proximity, ledger floor.
- **Gate is prose, not DSL** — Block messages are plain English. Agent reads the message and determines the fix. No structured `| gate: XXX | action: YYY` DSL.

### Path conventions

- **Company artifact**: `industry/<industry>/companies/<ticker>/YYYY-MM-DD-<skill>-<qualifier>.md`
- **Industry artifact**: `industry/<industry>/YYYY-MM-DD-<skill>-<qualifier>.md`
- **Cache**: `industry/<industry>/companies/<ticker>/_cache/`
- **Images**: `_cache/images/<slug>-<product>.<ext>` (no subdirectory per skill)
- **Legacy**: `topics/` is deprecated. `stock-quickread` explicitly warns against saving there.

## Architecture Decisions

### Why pre-write gate instead of post-write only
Post-write hooks catch errors after the file is written — by then source_contract has already passed and the agent may not go back to fix image/source issues. Pre-write blocks before the file lands, forcing the agent to fix problems first.

### Why no verification badges
Verified sources are the default state of a `[S#]`/`[I#]` anchor. Only exceptions need marking. The evidence ledger already tracks verification method per claim — duplicating this in artifact prose adds clutter without adding information.

### Why single industry primary residence
A company may serve multiple industries (e.g., Mycronic's MRSI serves optical modules, ATG serves PCB testing). But duplicating research artifacts creates consistency problems: which quickread is authoritative? Where are the actuals? The rule is: first industry to research the company owns the artifacts. Other industries cross-reference via index.md.

### Why business segments before geography in financial-data
Business segments (PG, GT, AS-HV) explain the economics. Geography segments (Asia, EMEA) explain the customer mix. For stock analysis, the business segment view is the primary lens. Both are preserved in actuals-resolved.json with a `type` field.

### Why topics/ was dropped
The `topics/<namespace>/<slug>/` structure added an unnecessary container layer. The namespace (`industry/`, `company/`) is already encoded in the path. `industry/pcb-equipment/companies/mycronic/` is self-documenting; `topics/industry/pcb-equipment/` adds no information.

## Known Cross-Industry Companies

| Company | Primary Industry | Cross Industry | Cross Segment |
|---|---|---|---|
| Mycronic (MYCR SS) | optical-module-equipment | pcb-equipment | ATG bare board testing, GT PCB test |
| Keysight (KEYS US) | optical-module-equipment | pcb-equipment | ICT bed-of-nails, TDR modules |
