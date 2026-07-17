---
name: trusted-market-bridge
description: Fetch A-share Hong Kong and US market evidence via Longbridge for market data price action FX ADR/AH premium filings news consensus financial snapshots and market-screen signals.
---

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

This bridge supports the following markets (Longbridge MCP coverage, verified 2026-06-09):

| Market | Code | Stock-level tools | Market-level tools | Notes |
|---|---|---|---|---|
| US | `US` | ✅ full | ✅ | quote/valuation/financials/consensus/filings/news/calendar |
| HK | `HK` | ✅ full | ✅ | + broker_holding (CCASS) / operating / AH premium |
| SH | `SH` | ✅ | ✅ | A-share (Shanghai) |
| SZ | `SZ` | ✅ | ✅ | A-share (Shenzhen) |
| SG | `SG` | limited | ✅ | market_temperature/calendar/status only |

If the requested symbol belongs to Japan, Korea, or any unsupported market:

- state that Longbridge is not covered for that market
- return `unsupported_market`
- fall back to the existing buy-side source and fallback logic unless the user explicitly asked for `longbridge_only`

## Supported Domains

This bridge may return evidence for:

- `market_quote` — latest OHLCV + turnover + trade status
- `price_action` — candlestick series + intraday minute data
- `kline_snapshot` — quick K-line range summary
- `valuation_snapshot` — PE/PB/PS/dividend_yield + industry percentile
- `valuation_peer` — valuation comparison with auto-selected peers
- `valuation_history` — multi-year PE/PB/PS time series
- `valuation_rank` — daily valuation percentile rank
- `industry_valuation` — peer valuation comparison
- `industry_valuation_dist` — PE/PB/PS distribution (min/p25/median/p75/max)
- `fx_snapshot` — all USD-cross exchange rates
- `adr_ah_premium` — A+H premium (dual-listed stocks only)
- `news` — latest news articles with titles + URLs
- `filings` — SEC/exchange filing index with file URLs
- `consensus` — analyst revenue/EBIT/EPS estimates with actual vs estimate comparison
- `forecast_eps` — EPS forecast trend over time
- `financial_statement` — structured IS/BS/CF with multi-year YoY
- `financial_snapshot` — latest key indicators (revenue/net_profit/ROE/EPS)
- `financial_snapshot_detail` — actual vs estimate + ratios + cash flow
- `business_segments` — geographic/segment revenue breakdown
- `company_profile` — name/employees/CEO/industry/profile
- `calendar` — earnings/dividend/split/IPO/macro/closed events
- `shareholder` — institutional + insider shareholders
- `shareholder_top` — top 20 shareholders
- `executive` — management team with bios
- `institution_rating` — analyst ratings + target prices
- `institutional_views` — monthly rating distribution
- `broker_holding` — HKEX CCASS broker flow (HK only)
- `dividend` — dividend history
- `operating` — operating metrics (HK only)
- `market_temperature` — market sentiment 0-100
- `market_status` — trading session status
- `top_movers` — price events with news context
- `screener` — stock screening
- `industry_peers` — sub-sector peer tree

## MCP Tool Mapping

Longbridge is accessed via MCP (145 tools, 15 categories). All tools verified 2026-06-09 against live data (AAPL.US + 700.HK).

### Core Market Data

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `market_quote` | `mcp__longbridge__quote` | `symbols=["AAPL.US","700.HK"]` (batch ok) | ✅ US+HK |
| `price_action` | `mcp__longbridge__candlesticks` | `symbol`, `period` (day/week/month/year), `count` (max 1000) | ✅ |
| `price_action` | `mcp__longbridge__intraday` | `symbol` — minute-by-minute OHLCV+turnover | ✅ |
| `price_action` | `mcp__longbridge__history_candlesticks_by_date` | `symbol`, `period`, `forward_adjust`, `start`, `end`, `trade_sessions` | ✅ schema |
| `kline_snapshot` | `mcp__longbridge__candlesticks` | 同上 — quick kline range summary | ✅ |
| `market_temperature` | `mcp__longbridge__market_temperature` | `market` (HK/US/CN/SG) → temperature/valuation/sentiment 0-100 | ✅ |
| `market_status` | `mcp__longbridge__market_status`, `mcp__longbridge__trading_session` | `market` | ✅ schema |
| `top_movers` | `mcp__longbridge__top_movers` | `markets`, `sort` (0=time/1=change/2=heat), `limit` | ✅ |

### Valuation

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `valuation_snapshot` | `mcp__longbridge__valuation` | `symbol` → PE/PB/PS/dividend_yield with industry percentile + 1yr history | ✅ |
| `valuation_peer` | `mcp__longbridge__valuation_comparison` | `symbol`, `currency` (USD/HKD/CNY) — auto-selects industry peers, returns PE/PB/PS with monthly history | ✅ |
| `valuation_history` | `mcp__longbridge__valuation_history` | `symbol` → long-term PE/PB/PS/dividend_yield time series | ✅ schema |
| `valuation_rank` | `mcp__longbridge__valuation_rank` | `symbol`, `start`, `end` (yyyymmdd) → daily PE/PB/PS percentile | ✅ schema |
| `industry_valuation` | `mcp__longbridge__industry_valuation` | `symbol` → peer valuation comparison | ✅ schema |
| `industry_valuation_dist` | `mcp__longbridge__industry_valuation_dist` | `symbol` → PE/PB/PS distribution (min/p25/median/p75/max + current percentile) | ✅ |

### Fundamentals & Financials

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `financial_statement` | `mcp__longbridge__financial_statement` | `symbol`, `kind` (IS/BS/CF/ALL), `report` (af/saf/qf/q1/q2/q3) → structured line items with YoY | ✅ multi-year |
| `financial_report` | `mcp__longbridge__financial_report` | `symbol`, `kind`, `report` — same as financial_statement | ✅ schema |
| `financial_snapshot` | `mcp__longbridge__financial_report_latest` ★ | `symbol` → revenue/net_profit/assets/debt/EPS/BPS/ROE/net_margin | ✅ primary |
| `financial_snapshot_detail` | `mcp__longbridge__financial_report_snapshot` | `symbol`, `report` (qf/saf/af), `fiscal_year`, `fiscal_period` → actual vs estimate + ratios + cash flow | ✅ |
| `business_segments` | `mcp__longbridge__business_segments` | `symbol` → geographic/segment revenue with percent + YoY | ✅ |
| `company_profile` | `mcp__longbridge__company` | `symbol` → name/founded/employees/CEO/website/profile | ✅ |

Note: `financial_report_latest` is the **best first stop** for a quick financial snapshot. Use `financial_report_snapshot` when you need estimate comparison + cash flow detail. Use `financial_statement` only when you need multi-year structured line-item tables.

### Consensus & Estimates

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `consensus` | `mcp__longbridge__consensus` | `symbol` → revenue/EBIT/EPS estimates per fiscal period with actual vs estimate + beat/miss | ✅ |
| `forecast_eps` | `mcp__longbridge__forecast_eps` | `symbol` → EPS forecast trend (median/mean/low/high) per window | ✅ |

### News, Filings & Events

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `news` | `mcp__longbridge__news` | `symbol` → title/description/url/published_at | ✅ |
| `filings` | `mcp__longbridge__filings` | `symbol` → SEC filings (US) / exchange filings (HK) with file_urls | ✅ US |
| `calendar` | `mcp__longbridge__finance_calendar` | `category` (report/dividend/split/ipo/macrodata/closed), `start`, `end`, `market` (optional: HK/US/CN/SG/JP/UK/DE/AU) | ✅ |

### Shareholders & Management

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `shareholder` | `mcp__longbridge__shareholder` | `symbol` → institutional + insider shareholders with percent + change | ✅ |
| `shareholder_top` | `mcp__longbridge__shareholder_top` | `symbol` → top 20 shareholders per reporting period (with object_id for drill-down) | ✅ HK |
| `executive` | `mcp__longbridge__executive` | `symbol` → management team with title + biography + wiki_url | ✅ US |
| `institution_rating` | `mcp__longbridge__institution_rating` | `symbol` → analyst buy/hold/sell counts + target price high/low/mean + industry rank | ✅ |
| `institutional_views` | `mcp__longbridge__institutional_views` | `symbol` → monthly rating distribution timeline | ✅ schema |

### Market-Specific

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `fx_snapshot` | `mcp__longbridge__exchange_rate` | No params needed — returns all USD-cross rates (use base_currency=USD, filter other_currency=HKD/CNY/etc.) | ✅ |
| `adr_ah_premium` | `mcp__longbridge__ah_premium` | `symbol` (A+H dual-listed only, e.g. `600036.SH` not `700.HK`) → premium K-line | ⚠️ dual-list only |
| `adr_ah_premium` | `mcp__longbridge__ah_premium_intraday` | `symbol` — intraday premium | ⚠️ dual-list only |
| `broker_holding` | `mcp__longbridge__broker_holding` | `symbol` (HK only) → HKEX CCASS top broker buy/sell with change | ✅ HK |
| `dividend` | `mcp__longbridge__dividend` | `symbol` → ex_date/pay_date/amount/currency | ✅ US |
| `operating` | `mcp__longbridge__operating` | `symbol` (HK only) → operating metrics (passenger/cargo/store counts etc.) | ✅ schema |
| `industry_peers` | `mcp__longbridge__industry_peers` | `BK counter_id` from `industry_rank` → hierarchical sub-sector tree | ✅ schema |

### Screen & Search

| Domain | MCP Tool | Key Parameters | Verified |
|---|---|---|---|
| `screener` | `mcp__longbridge__screener_search` | query params | ✅ schema |
| `market_screen` | `mcp__longbridge__top_movers` | `markets`, `sort`, `limit` — price events with news context | ✅ |

### Symbol Format

| Market | Format | Example |
|---|---|---|
| US | `TICKER.US` | `AAPL.US`, `NVDA.US` |
| HK | `CODE.HK` | `700.HK`, `9988.HK` |
| SH | `CODE.SH` | `600036.SH` |
| SZ | `CODE.SZ` | `000858.SZ` |

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

## Routing

Data routing is managed by the unified capability matrix, not by per-skill routing tables.

- **Runtime routing**: `python .scripts/shared/route.py <TICKER> <capability>` — resolves capability → full source chain
- **Capability registry**: `.references/routing/capability-matrix.json` — single source of truth for all source priorities
- **Section-level mapping**: `.references/routing/bridge-skill-map.md` — which skill section needs which capability

This bridge is one source (`longbridge_mcp`) in the matrix. Its capabilities, coverage markets, and tool mapping are defined in the matrix under `sources.longbridge_mcp` and `tool_map.longbridge_mcp`.

## Failure Discipline

Honest failures are mandatory:

- `unsupported_market`
- `not_allowed`
- `unavailable`
- `scope_restricted`
- `ambiguous`
- `stale`

Do not pretend Longbridge covers a market or field that it does not cover. In `auto` mode, `scope_restricted` should normally degrade into the existing web / internet market-source fallback and be disclosed at the end via `fallback reason: Longbridge scope_restricted for [domain]; used internet market source`.
