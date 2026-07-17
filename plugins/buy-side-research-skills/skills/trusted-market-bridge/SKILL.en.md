---
name: trusted-market-bridge
description: Fetch A-share Hong Kong and US market evidence via Longbridge for market data price action FX ADR/AH premium filings news consensus financial snapshots and market-screen signals.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Trusted Market Bridge

Fetch A-share, Hong Kong, and US market evidence via Longbridge for market data, price action, valuation, FX, ADR/AH premium, filings, news, consensus, financial snapshots, and market-screen signals.

This is an operations bridge, not a research conclusion skill. It can be invoked directly by the user or used implicitly by research skills that need a clean provider boundary.

In the global source policy, this bridge is the default trusted third-party layer for market-snapshot fields after `topic-local evidence cache / financial-data` and before generic web fallback. It does not replace `primary public` for disclosure-fact truth.

## What This Skill Is For

Use this skill when the task is to retrieve or normalize provider-derived market evidence for:

- latest market quote / price data
- price action / recent range / simple kline summary
- valuation snapshot
- FX snapshot for currency normalization
- ADR / A-share / H-share premium framing
- recent news
- filing index / recent disclosures
- analyst consensus / revisions / target-price context
- financial snapshot for quick reference
- market-screen signals for candidate generation and anomaly-driven prioritization

This skill is intentionally narrow. It does not write a thesis, rank ideas, build a model, or infer company truth from provider pages.

## Supported Markets

This bridge only supports the following markets in v1:

- `US`
- `HK`
- `SH`
- `SZ`

If the requested symbol belongs to Japan, Korea, Singapore, crypto, or any unsupported market:

- state that Longbridge is not covered for that market
- return `unsupported_market`
- fall back to the existing buy-side source and fallback logic unless the user explicitly asked for `longbridge_only`

## Supported Domains

This bridge may return evidence for:

- `market_quote`
- `price_action`
- `valuation_snapshot`
- `kline_snapshot`
- `fx_snapshot`
- `adr_ah_premium`
- `news`
- `filings`
- `consensus`
- `financial_snapshot`
- `market_screen`

## MCP Tool Mapping

Longbridge is accessed via MCP (145 tools). Map bridge domains to MCP tools:

| Domain | MCP Tool | Key Parameters |
|---|---|---|
| `market_quote` | `mcp__longbridge__quote` | `symbols=["TICKER.US"]` |
| `price_action` | `mcp__longbridge__candlesticks`, `mcp__longbridge__intraday` | `symbol`, date range |
| `valuation_snapshot` | `mcp__longbridge__valuation` | `symbol` |
| `consensus` | `mcp__longbridge__consensus`, `mcp__longbridge__forecast_eps` | `symbol` |
| `financial_snapshot` | `mcp__longbridge__financial_statement`, `mcp__longbridge__financial_report` | `symbol` |
| `news` | `mcp__longbridge__news` | `symbol` |
| `company_profile` | `mcp__longbridge__company` | `symbol` |
| `calendar` | `mcp__longbridge__finance_calendar` | `category`, `start`, `end` |
| `fx_snapshot` | `mcp__longbridge__exchange_rate` | `symbols` |
| `adr_ah_premium` | `mcp__longbridge__ah_premium`, `mcp__longbridge__ah_premium_intraday` | `symbol` |
| `filings` | `mcp__longbridge__filings` | `symbol` |
| `shareholder` | `mcp__longbridge__shareholder`, `mcp__longbridge__shareholder_top` | `symbol` |
| `institution` | `mcp__longbridge__institution_rating`, `mcp__longbridge__institutional_views` | `symbol` |
| `screener` | `mcp__longbridge__screener_search` | query params |
| `industry` | `mcp__longbridge__industry_peers`, `mcp__longbridge__industry_valuation` | `symbol` |
| `market_status` | `mcp__longbridge__market_status`, `mcp__longbridge__trading_session` | `market` |
| `dividend` | `mcp__longbridge__dividend`, `mcp__longbridge__dividend_detail` | `symbol` |
| `operating` | `mcp__longbridge__operating` | `symbol` |

All tools use US ticker format `TICKER.US` and HK format `CODE.HK`.

## Installation

```bash
# Claude Code (global)
claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp
# Then /mcp → longbridge → Authenticate

# Codex
codex mcp add longbridge --url https://openapi.longbridge.com/mcp
codex mcp login longbridge
```

It must reject unsupported requests such as:

- business facts
- segment truth
- undisclosed drivers
- management intent
- full actuals source-of-record extraction

## Evidence Contract

Bridge-derived evidence must preserve:

- provider: `Longbridge Securities`
- symbol
- market
- as-of timestamp
- domain
- fallback reason when fallback is used

Use clickable short anchors in the form `[LBG1](https://longbridge.example.com/quote/NVDA.US)` in body tables or bullets. The body anchor target must exactly match the `## Resources` target. Expand full metadata only once in the final `## Resources` section.

Example:

```markdown
| Field | Value | Ev |
|---|---|---|
| Price | 125.40 | [LBG1](https://...) |

## Resources
- [LBG1](https://...) = Longbridge Securities | market_quote | NVDA.US | as-of 2026-05-25 09:30 ET
```

Do not rewrite bridge-derived evidence as `company disclosed`, `management said`, or other primary-public wording unless the underlying source is actually a primary filing or disclosure and that distinction is preserved.

## Input Shape

When using this skill, normalize the request to:

| Field | Meaning |
|---|---|
| `symbol` | security code |
| `market` | one of `US/HK/SH/SZ` |
| `need_type` | one of the supported domains |
| `mode` | `auto`, `longbridge_only`, or `off` |

Interpretation:

- `auto`: use Longbridge if the market and domain are supported; otherwise return an honest fallback signal
- `longbridge_only`: do not fall back silently; fail explicitly if unsupported or unavailable
- `off`: do not use Longbridge

## Output Shape

Return an evidence bundle, not a research artifact:

```markdown
## Bridge Status
- status: ok / unavailable / scope_restricted / ambiguous / unsupported_market / stale / not_allowed
- provider: Longbridge Securities
- symbol: [symbol]
- market: [market]
- as-of: [timestamp]

## Evidence
- [domain-specific facts with [LBG1](https://longbridge.example.com/quote/NVDA.US) anchors]

## Resources
- [LBG1](https://longbridge.example.com/quote/NVDA.US) = Longbridge Securities | market_quote | NVDA.US | as-of 2026-05-25 09:30 ET | fallback reason: topic-local market snapshot cache unavailable
```

When unsupported or unavailable, say so plainly and include the reason. When the bridge is `scope_restricted`, the default user-facing behavior is web fallback plus a short fallback note in `## Resources`, not a hard stop.

## FX And Premium Boundary

`fx_snapshot` and `adr_ah_premium` are allowed only as:

- currency normalization context
- ADR-vs-local or A/H premium framing
- cross-market valuation context
- quick premium / discount snapshots with explicit as-of timestamps

They are not:

- authoritative proof of share-class equivalence
- a substitute for verified ADR ratio or conversion mechanics
- a substitute for borrow, bid-ask, settlement, capital-control, or accounting-basis sourcing

If a downstream task needs verified share-class mapping, conversion truth, borrow detail, or access constraints, keep using the existing buy-side source hierarchy and preserve `[来源待补]` when no reliable source is available.

## Financial Snapshot Boundary

`financial_snapshot` is allowed only as:

- quick reference
- latest summary check
- filing-adjacent fast context
- fallback assist for research skills

It is not:

- a substitute for `financial-data`
- a source-of-record actuals pack
- a basis for full three-statement modeling

If a downstream task needs source-tracked actuals or model-grade field mapping, route to `financial-data`, `driver-map`, `driver-map`, or `model-update`.

## Market Screen Boundary

`market_screen` is allowed only as:

- candidate generation
- anomaly-aware prioritization
- market-screen convenience output for downstream ranking or triage

It is not:

- a thesis
- business-fact truth
- proof of company exposure without separate sourcing

Downstream consumers may use `market_screen` to narrow the funnel or explain why a candidate entered the screen, but they must still source business linkage, disclosure facts, and company-specific truth separately.

## Default Routing

| Situation | Route |
|---|---|
| Need market expectations and revisions | `consensus-map` + this bridge |
| Need pre/post earnings setup | `earnings-setup` + this bridge |
| Need peer market context | `peer-deep-dive` + this bridge |
| Need pair spread monitoring | `pair-trade` + this bridge |

| Need quick market and consensus context on a new name | `stock-quickread` + this bridge |
| Need candidate generation or anomaly-aware prioritization | `candidate-screener` + this bridge |
| Need thesis market-pricing inputs | `alpha-thesis` + this bridge |
| Need downside valuation and crowding context | `bear-pre-mortem` + this bridge |
| Need industry market clues without full screening | `industry-landscape` + this bridge |
| Need source-tracked actuals | `financial-data` |
| Need business/segment truth | `company-history` / `driver-map` / `mechanism-insight` |

## Failure Discipline

Honest failures are mandatory:

- `unsupported_market`
- `not_allowed`
- `unavailable`
- `scope_restricted`
- `ambiguous`
- `stale`

Do not pretend Longbridge covers a market or field that it does not cover. In `auto` mode, `scope_restricted` should normally degrade into the existing web / internet market-source fallback and be disclosed at the end via `fallback reason: Longbridge scope_restricted for [domain]; used internet market source`.
