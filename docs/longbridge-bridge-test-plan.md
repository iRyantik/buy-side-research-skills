# Longbridge Bridge Test Plan

This file is for maintainers of the plugin source repo. Normal plugin users do not need to read it.

## Summary

This test plan covers `trusted-market-bridge` and its 10 current consumer skills:

- `consensus-map`
- `earnings-setup`
- `peer-deep-dive`
- `pair-trade`
- `cross-market-compare`
- `stock-quickread`
- `candidate-screener`
- `alpha-thesis`
- `bear-pre-mortem`
- `industry-landscape`

The goal is not to validate every Longbridge API. The goal is to verify 6 repo-level behaviors:

1. A-share / Hong Kong / US market evidence can enter buy-side skills through the bridge.
2. `scope_restricted` degrades into web / internet market-source fallback in default `auto` mode.
3. Provider and fallback provenance survive into the final `## Resources` section.
4. Market/news/provider evidence does not get rewritten as business-fact truth.
5. Cross-market FX and premium framing can use the bridge without exposing Longbridge implementation details in the consumer.
6. High-risk cross-market fields do not get silently upgraded into Longbridge truth.

## Bridge Capability Checks

Validate the bridge itself first before checking consumer behavior.

### Supported markets

- `US`
- `HK`
- `SH`
- `SZ`

### Unsupported markets

- `JP`
- `KR`
- any market not explicitly listed above

### Theoretical v1 domains

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

### Current account empirical status

Working domains:

- `market_quote`
- `price_action`
- `valuation_snapshot`
- `kline_snapshot`
- `fx_snapshot`
- `adr_ah_premium`
- `consensus`
- `financial_snapshot`

Scope-restricted domains:

- `news`
- `filings`

Not yet live-checked as a bridge domain:

- `market_screen`

### Bridge acceptance criteria

- evidence bundle preserves `provider`, `symbol`, `market`, `as_of`, and `fallback_reason`
- `scope_restricted` exists as an internal bridge status
- default `auto` mode does not surface `scope_restricted` as a hard user-facing failure
- `longbridge_only` mode does not fall back on `scope_restricted` or `unsupported_market`

## Consumer Skill Checks

### `consensus-map`

- missing `consensus`, `market_quote`, or `valuation_snapshot` may use bridge first
- `news` or `filings` with `scope_restricted` fall back to web / internet source
- final `## Resources` includes:
  - Longbridge provider entry
  - web fallback entry
  - explicit `fallback reason`

### `earnings-setup`

- may use bridge for:
  - `market_quote`
  - `price_action`
  - `kline_snapshot`
  - `consensus`
  - `news`
  - `filings`
  - `financial_snapshot`
- `financial_snapshot` is used only as print context, not as filing truth or actuals base
- `scope_restricted` does not block the setup; it only changes the source mix in `## Resources`

### `peer-deep-dive`

- market / valuation / price fields in the peer matrix may use `[LBG1](https://longbridge.example.com/quote/0700.HK)` style anchors
- `news` with `scope_restricted` may fall back to `[I1](https://example.com/news)` style web source
- `filings`, if used, remain event-index or disclosure-entry evidence only
- peer business/disclosure comparison still follows the existing higher-grade source discipline

### `pair-trade`

- both legs may use bridge for price, valuation, consensus, and news context
- `scope_restricted` falls back to web / internet source without blocking pair verdict
- provider snapshots do not get rewritten as absolute business truth

### `cross-market-compare`

- may use bridge for:
  - `market_quote`
  - `valuation_snapshot`
  - `price_action`
  - `fx_snapshot`
  - `adr_ah_premium`
- `scope_restricted` still falls back to web / internet source without blocking the comparison
- `share class / ADR ratio / economic equivalence` still require authoritative sourcing
- `borrow / liquidity / conversion / accounting-basis` stay on the existing source hierarchy unless independently sourced

### `stock-quickread`

- may use bridge for:
  - `market_quote`
  - `valuation_snapshot`
  - `price_action`
  - `consensus`
  - `financial_snapshot`
- bridge evidence stays in market judgment and quick-context sections only
- `financial_snapshot` does not get rewritten as company-disclosed truth or `financial-data` replacement
- company description, segment economics, customer facts, and disclosure wording still follow the existing higher-grade source discipline

### `candidate-screener`

- may use bridge for:
  - `market_quote`
  - `valuation_snapshot`
  - `price_action`
  - `fx_snapshot`
  - `adr_ah_premium`
  - `market_screen`
- `market_screen` may carry scanner / anomaly style hits, candidate priority, and short trigger reasons
- `market_screen` does not count as thesis truth or business-fact authority
- `borrow / bid-ask / accounting basis / conversion / share-class truth` stay on the existing source hierarchy unless independently sourced

### `alpha-thesis`

- may use bridge for:
  - `market_quote`
  - `valuation_snapshot`
  - `price_action`
  - `consensus`
- bridge evidence stays inside `variant view vs consensus`, `priced-in`, `valuation anchor`, and market-context sections
- business facts, management quotes, customer / project facts, and disclosure wording still follow the existing higher-grade source discipline
- `scope_restricted` does not block the thesis; it only changes the source mix in `## Resources`

### `bear-pre-mortem`

- may use bridge for:
  - `market_quote`
  - `valuation_snapshot`
  - `price_action`
  - `consensus`
- bridge evidence stays inside downside valuation framing, market expectation mismatch, and price-setup / crowding-like context
- accounting, governance, Form 4, base-rate case support, and disclosure facts still follow the existing higher-grade source discipline
- `scope_restricted` does not block the pressure test; it only changes the source mix in `## Resources`

### `industry-landscape`

- may use bridge for:
  - `valuation_snapshot`
  - `price_action`
  - `fx_snapshot`
  - `adr_ah_premium`
- bridge evidence stays inside industry market clues such as board performance, valuation anchor, FX normalization, and premium framing
- this skill does not consume `market_screen`, `consensus`, `financial_snapshot`, `news`, or `filings`
- `scope_restricted` and `unsupported_market` fall back to the existing web / internet source path without turning the skill into a screener

## Provenance And Output Discipline

Check every consumer output for the following:

- bridge evidence uses `[LBG1](https://longbridge.example.com/quote/NVDA.US)` style anchors
- web fallback uses existing `[I1](https://example.com/quote)` style anchors
- `## Resources` makes it clear:
  - which fields came from Longbridge
  - which fields came from web fallback
  - why fallback happened
- body text does not need a long `scope_restricted` explanation
- provider-derived evidence is not rewritten as:
  - `company disclosed`
  - `management said`
  - `business fact`

## Boundary And Failure Checks

Validate these edge cases explicitly:

- `unsupported_market`
  - Japanese or Korean listings should not pretend to be covered
  - default behavior is fallback to existing web / internet market-source logic
- `ambiguous`
  - ambiguous symbol does not pretend to be resolved
- `scope_restricted`
  - `news` and `filings` default to web fallback in `auto` mode
- `longbridge_only`
  - no fallback allowed
- `financial_snapshot`
  - does not upgrade into `financial-data` source-of-record
- `market_screen`
  - does not upgrade into company-truth or verified business linkage
- `industry-landscape` boundary
  - does not upgrade into `candidate-screener`
  - does not consume `market_screen`, `consensus`, or `financial_snapshot`
- cross-market high-risk fields
  - `share class / ADR ratio / economic equivalence` cannot be hard-filled from bridge convenience
  - `borrow / liquidity / conversion mechanics / capital-control / accounting basis` do not downgrade into provider truth
- unsupported domains
  - business facts
  - segment truth
  - management intent
  - any non-market/provider truth domain

## Manual Acceptance Cases

Run at least these 15 manual checks:

1. `RKLB.US` with `consensus-map`
   - expected: `quote`, `consensus`, and `valuation` may come from Longbridge; `news` may fall back to web
2. `RKLB.US` with `earnings-setup`
   - expected: print context may consume bridge evidence; restricted domains fall back automatically
3. `RKLB.US`, `LUNR.US`, `SPIR.US` with `peer-deep-dive`
   - expected: matrix may mix `[LBGx]` and `[I1]`
4. `VRT.US` / `SMCI.US` with `pair-trade`
   - expected: both legs consume market evidence; restricted domains do not block verdict
5. `9988.HK` / `BABA.US` with `cross-market-compare`
   - expected: quote, FX, and premium framing may come from bridge; `## Resources` shows `[LBGx]` plus any fallback reason
6. `1398.HK` / `601398.SH` with `cross-market-compare`
   - expected: A/H premium framing can come from bridge; if premium support fails, the skill falls back to the existing web / internet source path
7. `0700.HK` with any consumer
   - expected: Hong Kong market path works
8. `600519.SH` with any consumer
   - expected: A-share path works
9. `RKLB.US` with `stock-quickread`
   - expected: `market_quote`, `valuation_snapshot`, `price_action`, `consensus`, and `financial_snapshot` may come from bridge without leaking into company-truth sections
10. `candidate-screener` with a US/HK/A market-screen use case
   - expected: `market_screen` can carry structured screen signals while quote / valuation / FX / premium still use the existing bridge domains
11. `alpha-thesis` with `RKLB.US`
   - expected: `valuation_snapshot`, `price_action`, and `consensus` may come from bridge in variant-view / priced-in sections without leaking into company-truth fields
12. `bear-pre-mortem` with a covered US/HK/A name
   - expected: downside valuation / market expectation / price setup may come from bridge while accounting / governance / base-rate still use the existing higher-grade source path
13. `industry-landscape` with an A/H/US-linked theme
   - expected: board performance, valuation anchor, FX, and premium framing may come from bridge without turning the skill into `candidate-screener`
14. `7203.JP` or a Korean listing with any consumer
   - expected: `unsupported_market`, then fallback to existing web / internet source logic
15. `SpaceX`
   - expected: does not pretend to be a normal listed-security market-evidence path; surfaces symbol or coverage gap

## Execution Notes

- This plan is manual acceptance plus output inspection. It does not require an automated test framework.
- Validate skill behavior and source discipline, not Longbridge platform correctness itself.
- Use the current Longbridge account assumption unless credentials change:
  - market-data and consensus surfaces work
  - `news` and `filings` may be `scope_restricted`
- Current bridge consumers are currently:
  - `consensus-map`
  - `earnings-setup`
  - `peer-deep-dive`
  - `pair-trade`
  - `cross-market-compare`
  - `stock-quickread`
  - `candidate-screener`
  - `alpha-thesis`
  - `bear-pre-mortem`
  - `industry-landscape`
