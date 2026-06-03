---
name: financial-data
description: Fetch or parse source-tracked company financial data by market and identifier.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Financial Data

`financial-data` turns machine-readable financial data from each market into a source-tracked evidence pack. It is an operations skill, not a research skill: it is only responsible for fetching, parsing, normalizing, annotating completeness, and writing to `_cache/datasets/financial-data/`. It does not interpret investment meaning, does not produce forecasts, and does not substitute for `driver-map` or `3-statement-model / dcf-model / comps-analysis / model-update`.

The core deliverable is not "three statements that look complete," but rather "which fields are actually available, where they come from, and whether they can be fed into a model." V1 fetches three statements by default; when the provider can structurally capture a revenue split, it writes it into `statements.revenue_split` in `actuals-resolved.json`; when it cannot, it marks `revenue_split = provider-gap` and preserves the original filing / annual report text for `driver-map` to extract via LLM. Inference-based gap-filling is not allowed.

## Core Philosophy

The most common pitfall in financial data fetching is not an API error; it is data that looks too clean: a provider-normalized label mistaken for original company disclosure, a segment bucket auto-merged, a ticker-only route resolving to the wrong entity, or the three statements being available while the revenue split the model actually needs is missing.

This skill's operating logic is **provenance first + completeness before model use**. Save the raw provider payload first, then save the normalized evidence pack. Day-to-day external consumption only sees `financial-data-summary.md`; machine inputs and audit files go into `internal/`. Tell the researcher what is missing first, then let `driver-map` and `3-statement-model / dcf-model / comps-analysis / model-update` decide whether modeling can proceed.

`financial-data` serves the topic-centric architecture: single-company data defaults to `industry/<industry>/companies/<ticker>/`; theme / industry topics only save snapshots or links, and do not become a second set of company master files.

## Responsibility Boundary

Responsible for:

- Fetching or parsing structured financial data by `market`, `identifier`, `identifier_type`, and `company_slug`.
- Writing by default to the canonical company topic: `industry/<industry>/companies/<ticker>/_cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/`.
- Saving the raw provider payload to `_raw/datasets/financial-data/`, and saving the normalized evidence pack to `_cache/datasets/financial-data/`.
- The raw evidence layer must at minimum include `provider_payload.json` and `identity-source.json`; when a real filing source exists, it must also write `filings/<filing-id>/source.*`, `source-metadata.json`, and `source.sha256`.
- Generating the public `financial-data-summary.md`; machine files go into `internal/`, including `evidence-pack.json`, `actuals-resolved.json`, `full-filing.md`, `manifest.json`, `financials.md`, `financials.normalized.json`, `completeness.json`, `source-map.json`, and `cross-check.json`.
- Outputting a field-level completeness matrix: three statements and `revenue_split` are labeled with separate statuses.
- Supporting current topic snapshots: `industry/<industry>/companies/<ticker>/_cache/datasets/financial-data-snapshot/<run-id>/`.
- Failing honestly for dependency gaps, credential gaps, and provider gaps.

Not responsible for:

- Company business interpretation, driver judgment, revenue split inference, or the true economic meaning of segments; those are handed to `company-history` / `driver-map`.
- Forecasts, DCF, comps, reverse DCF, or workbook updates; those are handed to `3-statement-model / dcf-model / comps-analysis / model-update`.
- Both Full and Lite automatically fetch market snapshot data (stock price, market cap, PE/PB/PS/EV/EBITDA, etc.) via the unified incremental fill engine: `yfinance(full set) → Bridge(covers US/HK/SH/SZ) → WebSearch(field-by-field) → Google Finance(last resort)`. See the market data section for details.
- Bridge only performs cross-checks in actuals (does not replace provider_api); in market data it serves as the US/HK/SH/SZ primary.
- Turning `_cache/` into earned memory; knowledge crystallization is handed to `research-journal`.
- Creating dated research Markdown artifacts.
- Promising that all markets support ticker-only auto discovery.

## Triggers and Inputs

Trigger phrases:

- "拉一下 GE 的结构化财报"
- "fetch financial data"
- "按 ticker 拉三表"
- "DART 拉韩国财报"
- "用 openesef 解析这份 ESEF"
- "把 ASML 的 ESEF package 转成 financial-data evidence pack"
- "给这个 theme 拉一篮子公司财务 snapshot"

Input fields:

| Input | Purpose | Default / Missing handling |
|---|---|---|
| `output_scope` | `canonical_company` / `current_topic_snapshot` | Default `canonical_company` |
| `company_slug` | Company canonical topic slug | Required for canonical output |
| `topic` | Current topic slug | Required for snapshot output |
| `market` | `us` / `cn` / `hk` / `jp` / `kr` / `tw` / `eu` | Required |
| `identifier` | ticker, CIK, EDINET code, DART corp code, LEI, filing URL, etc. | Required |
| `identifier_type` | `ticker` / `isin` / `lei` / `cik` / `edinet_code` / `dart_corp_code` / `filing_url` / `local_esef_package` | Default `ticker` |
| `periods` | `latest`, `FY2021-FY2025`, `quarterly`, etc. | Default `latest` |
| `items` | Three statements, `revenue_split`, filing / full text | Default fetch all |
| `source_mode` | `auto` / `filing_only` / `provider_normalized` | Default `auto` |
| `financial_data_pack_path` | Points a snapshot or `3-statement-model / dcf-model / comps-analysis / model-update` to an existing pack | Optional |

Europe special rules:

- `openesef` supports ESEF/iXBRL parsing.
- `identifier_type = filing_url` or `local_esef_package` is the trusted route.
- `identifier_type = ticker` is ticker-only discovery; V1 labels it `experimental`; when a filing cannot be located, output `provider-gap`.

## Execution Modes

### Dependency Bootstrap / Check

Run:

```powershell
python _scripts/financial-data/financial_data.py --check-deps
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly
```

Run only after explicit user confirmation:

```powershell
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes
```

### Canonical Company Fetch

Default write target:

```text
industry/<industry>/companies/<ticker>/
  _raw/datasets/financial-data/<market>/<canonical-id>/<run-id>/
    provider_payload.json
    identity-source.json
    filings/<filing-id>/
      source.*
      source-metadata.json
      source.sha256
  _cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/
    manifest.json
    identity.json
    filing-index.json
    financials.md
    financials.normalized.json
    full-filing.md
    full-filing.chunks.jsonl
    full-filing.index.json
    completeness.json
    source-map.json
    cross-check.json
  _cache/financial-data/
    financial-data-summary.md
    internal/
      evidence-pack.json
      actuals-resolved.json
      full-filing.md
      manifest.json
      identity.json
      financials.normalized.json
      completeness.json
      source-map.json
      cross-check.json
```

`_cache/financial-data/financial-data-summary.md` is the default entry point for humans and LLMs. `_cache/financial-data/internal/actuals-resolved.json` is the recommended machine entry point for `driver-map`, `3-statement-model`, `dcf-model`, `comps-analysis`, and `model-update` to read historical actuals; `statements` within it may contain `income_statement`, `balance_sheet`, `cash_flow`, and optional `revenue_split`. Missing / unmapped fields must not be written as 0. `internal/evidence-pack.json` aggregates completeness, source map, and cross-check; the run-id pack is only opened directly during audit or debugging.

If `industry/<industry>/companies/<ticker>/index.md` does not exist, the agent must auto-create the directory and index per policy baseline §11 before continuing.

### Lite Mode Fetch (fast pre-research fetch)

Trigger phrases: `/financial-data --lite <ticker>` or "pull quick financials for <ticker>"  
Trigger (3Y mode): `/financial-data --lite <ticker> --periods 3Y` or "pull 3-year financial data"

Lite mode does not parse the full filing and does not build an evidence pack. It fetches core three-statement line items + segment revenue/profit + market snapshot data, and writes them into `actuals-resolved.json`. The objective is the minimum necessary data before launching **stock-quickread / candidate-screener / peer-deep-dive / consensus-map / earnings-setup / alpha-thesis / bear-pre-mortem / pair-trade**.

**`--periods 3Y` (appendix display mode)**：Enable when a consuming skill needs to render a sell-side-style appendix. The agent fetches **3 full fiscal years + up to 4 sub-year periods** (quarterly reporter → Q1/Q2/Q3/Q4, half-year reporter → H1/H2), writing them into `actuals-resolved.json` under `fy_y2` / `fy_y1` / `fy_y0` / `sub_0` … `sub_3` keys. Field template defined in `_scripts/financial-data/actuals_schema.json`. Default `latest` mode writes only `latest_fy` + `latest_quarter`; in 3Y mode both coexist — `latest_*` keys are preserved.

**Consumer contract**: Consuming skills call `--lite [--periods 3Y]` and read data directly from `actuals-resolved.json`.

**Three-statement fetch logic**: Route to provider by market; if unavailable, degrade layer by layer: official_web → yfinance → trusted_web → broad_web. The rules follow the same provider_api + official_web priority principle as Full mode.

**Market data fetch logic** (unified incremental fill engine):

Trust ranking: `yfinance > Bridge > WebSearch > Google Finance`

Engine logic: Each layer fills as many as possible in one pass → immediately marks gaps → the next layer only fills remaining gaps.

```
Layer 1: yfinance(full set) → ticker.info returns ~50 fields in one call, zero marginal cost
  Fill: price, mcap, PE TTM, PE NTM, PB, PS, EV/EBITDA, EV/Sales, Dividend Yield, Beta
  → Checkpoint: N1/11 filled, gap list

Layer 2: Bridge(covers US/HK/SH/SZ) → high-trust coverage of yfinance-filled fields
  Supplement: consensus EPS, Target Price, FX
  → Checkpoint: N2/11 filled, gap list

Layer 3: RAG fallback chain(field-by-field gap fill) → only search remaining gaps; AI-summarized numbers must not be directly written
  3a. WebSearch for candidate URLs (2-5 candidates per field)
  3b. WebFetch open candidates → read original text → confirm the number exists on the page → write
  3c. WebFetch failure → Playwright MCP browser_navigate + snapshot → write
  3d. Playwright failure → curl raw HTML → write
  3e. All failed → field left null, not written (no false confidence)
  Core fields (Rev/EBIT/NI/TA/MCap): full four-layer path; important fields (GP/FCF/CapEx): two-layer path; supplementary fields (β/Div): one layer suffices
  Prioritize local language: CN→Chinese+English, JP→日本語+English, KR→한국어+English, Europe/US→English
  Verification success → label source_layer=official_web or provider_api, source_detail includes verified URL
  → Checkpoint: N3/11 filled, gap list

Layer 4: Google Finance(one fetch fills multiple gaps) → URL last resort
  Still missing → field left null
```

Per-layer checkpoint example:
```
yfinance:  8/11, missing EV/EBITDA, PEG, Target Price
Bridge:    9/11, remaining PEG, Target Price
RAG:       10/11, remaining PEG (all WebFetch attempts failed)
→ PEG = null (not written)
```

There is no official_web layer: exchange websites only publish trading data PDFs and do not compute PE/PB.

After fetching, write into `actuals-resolved.json` under `market_data` (audit anchor, not a substitute for the next fetch).

**Minimum fields written by Lite**:

| Category | Content | Status | Trust Layer |
|---|---|---|---|
| Three statements | 22 core line items (IS/BS/CF) | Required | provider_api > official_web > yfinance |
| Segments | Segment revenue + profit (if available) | Required | provider_api |
| Stock price | Latest closing price | Required | Bridge > yfinance > WebSearch > Google Finance |
| Market cap | Total market cap (local currency) | Required | Same as above |
| PE TTM | Trailing PE | Required | Bridge > yfinance > WebSearch > Google Finance |
| PE NTM | Forward PE (1Y Forward) | Required | Bridge(consensus) > WebSearch > yfinance |
| PB | Price-to-Book | Required | Bridge > yfinance > WebSearch > Google Finance |
| PS | Price-to-Sales | Required | Bridge > yfinance > Google Finance |
| EV/EBITDA | Enterprise Value / EBITDA | Required | Bridge > yfinance > WebSearch |
| EV/Sales | Enterprise Value / Revenue | Required | Bridge > yfinance |
| PEG | PE / Earnings growth rate | best-effort | WebSearch > yfinance |
| Dividend Yield | Dividend yield | Optional | yfinance > WebSearch |
| Target Price | Consensus target price | best-effort | Bridge(consensus) > WebSearch |
| Consensus EPS | EPS estimate (NTM) | best-effort | Bridge > WebSearch |
| Beta | Volatility | Optional | yfinance |
| Price history | 1-year daily line (driver analysis) | Required | yfinance |
| Supplement-standard | Shares outstanding, SBC | Fetch if available | provider_api > official_web |
| growth_rates | revenue_yoy_fy, revenue_yoy_q | Required — agent computes after fetching two-period data | derived |

> **Derived fields constraint**: All derived field inputs (including growth_rates, elasticity ratios, and any arithmetic ratio) must come from actual disclosed data in `actuals-resolved.json`. **Using FY2026E / consensus estimates / forward-looking numbers as inputs to compute ratios and write them into actuals is prohibited.** If a given input field has no actuals → that derived field is labeled `[未披露]`; do not compute, do not infer.

**Elasticity collection** (first determine business model → route to `references/kpi-drivers/<template>.md` → only fetch fields from that template):

| KPI | actuals field | Condition |
|---|---|---|
| Order Backlog | `supplementary.order_backlog` | order-driven / long-cycle / tech-manufacturing — IR segment |
| Orders / Bookings | `supplementary.orders` | Same as above — IR quarterly |
| Installed Base | `supplementary.installed_base` | order-driven / tech-manufacturing — annual report |
| Production Volume | `supplementary.production_volume` | process-industry — IR quarterly |
| Unit Cost | `supplementary.unit_cost` | process-industry — IR / annual |
| Utilization | `supplementary.utilization` | process-industry / utility-infra — IR / mgmt |
| Regulated Asset Base | `supplementary.regulated_asset_base` | utility-infra — regulatory filing |
| Capacity MW | `supplementary.capacity_mw` | utility-infra — IR / annual |
| ARR | `supplementary.arr` | saas-software — IR / earnings call |
| GRR | `supplementary.grr` | saas-software — IR / earnings call |
| NRR | `supplementary.nrr` | saas-software — IR / earnings call |
| Churn % | `supplementary.churn_pct` | saas-software — IR / earnings call |
| Customer Count | `supplementary.customer_count` | saas-software / ai-emerging — IR |
| Segment Backlog | `segments[].metric="order_backlog"` | order-driven / long-cycle — IR segment |
| Segment Orders | `segments[].metric="orders"` | order-driven / tech-manufacturing — IR segment |

If not found, label `[未披露]`; do not block the main flow.

**Generalized fallback**: After reading the IR/earnings call, if a KPI not covered by the template is discovered that is meaningful to the thesis → `supplementary.custom_metrics: [{kpi, value, source, relevance}]`. No limit on count, but each must pass the self-check: "If this metric were deleted, would it affect the conclusion?"

**Stop conditions** (stop when any one is met):
- All standard 33 fields filled + all elasticity fields for this business model filled → stop
- Two consecutive layers (e.g., yfinance→Bridge) with no new fields filled → stop
- All remaining gaps are `[未披露]` (company does not disclose) → stop

**Topic-facts.json write**: After fetching, write quantitative facts on valuation, TAM-related data, and elasticity KPIs into `_cache/topic-facts.json` (company-level fact cache under this topic, for downstream skills to reuse before searching, reducing duplicate searches).

**source_map generation (Provenance pass-through)**: Every field in actuals already has source_detail (including PDF page number + URL or yfinance source). After fetching, scan source_detail of all fields, deduplicate → generate `source_map` and write into actuals-resolved.json:

```json
"source_map": {
  "S_1": {"source_layer": "official_web", "url": "https://...Q1-2026.pdf", "detail": "Besi Q1-26 Results PDF p1", "label": "S5"},
  "I_1": {"source_layer": "yfinance", "url": null, "detail": "BESI.AS yfinance", "label": "I10"},
  "I_2": {"source_layer": "WebSearch", "url": "https://...", "detail": "...", "label": "I11"}
}
```

> **How consuming skills use this**: Read actuals-resolved.json → read source_map → label artifacts as [S5](url) or [I10] rather than [actuals]. Revenue uses [S5] pointing to the official PDF, not a vague "actuals."

**Data integrity rules**:

- ADR/dual-class/H+A: write `share_class` field
- Data freshness: each field labeled `[source_layer | as-of date]`, no global TTL
- Uncovered markets (SG/AU/IN/SEA): yfinance → WebSearch → Google Finance layer-by-layer degradation
- Unit normalization: AKShare 万元→元, EDINET 百万円→円, KR 억원→원
- Non-numeric placeholders (NaN/inf/—/N/A) → null, do not count as filled

**Output** (slimmed down):

- `actuals-resolved.json`: three statements + segments + `market_data` audit snapshot
- Does not output `financial-data-summary.md`

Lite does not write `evidence-pack.json`, `full-filing.md`, `completeness.json`, `source-map.json`.

### Fill-Gaps Mode (fill Layer 3 gaps)

Trigger phrases: `/financial-data --fill-gaps <ticker>` or "补全 xxx 的财务数据"

Process: Read actuals → iterate null fields → **fill on two tracks**:

**Three-statement gap fill**: Route to provider by market (US→EdgarTools, CN→AKShare, JP→EDINET, KR→OpenDART, TW→FinMind, EU→openesef) → fill values. When the provider is unavailable, search layer by layer using the web fallback strategy below. Fields that still cannot be filled are marked [ND].

**Market data gap fill**: Use the unified incremental fill engine (yfinance → Bridge → WebSearch → Google Finance), only filling fields missing from actuals. Existing fields are not overwritten. 5-15 seconds per company.

**Web Fallback strategy (general rules)**: First use `site:` to scope to the preferred domain → then drop the site: operator and use keywords → if still not found, mark `[ND]`. Each query is searched once in **local language + English**.

| Market | Three statements | Revenue split | Valuation | Consensus |
|---|---|---|---|---|
| **US** | `site:sec.gov <ticker> 10-K` → `site:stockanalysis.com <ticker> financials` → bare search | `site:sec.gov <ticker> segment revenue` → bare search | `site:yahoo.com <ticker> statistics` | `site:marketscreener.com <ticker> consensus` |
| **CN** | `site:eastmoney.com <ticker> 利润表` → `site:10jqka.com.cn <公司名>` → bare search | `site:cninfo.com.cn <ticker> 营业收入构成` → bare search | `site:eastmoney.com <ticker> PE PB 市值` | `site:eastmoney.com <ticker> 盈利预测` |
| **HK** | `site:aastocks.com <code> 利润表` → `site:xueqiu.com <code> 财务` → bare search | `site:hkexnews.hk <code> 分部收入` → bare search | `site:aastocks.com <code>` | `site:marketscreener.com <ticker>.HK consensus` |
| **JP** | `site:finance.yahoo.co.jp <code> 決算` → `site:kabutan.jp <code> 業績` → bare search | `<code> セグメント別売上高` → `<code> 決算説明会` | `site:finance.yahoo.co.jp <code>` → `site:kabutan.jp <code>` | `site:marketscreener.com <code>.T consensus` |
| **KR** | `site:comp.fnguide.com <gicode>` → `site:finance.naver.com <code> 재무제표` → bare search | `site:dart.fss.or.kr <code> 사업부문별` → bare search | `site:comp.fnguide.com <gicode>` → `site:markets.hankyung.com <code>` | `site:comp.fnguide.com <gicode>` → `site:marketscreener.com <ticker>.KS` |
| **TW** | `site:goodinfo.tw <code>` → `site:mops.twse.com.tw <code> 财务报告` → bare search | `<code> 營收 產品別 部門別` | `site:goodinfo.tw <code>` | `site:marketscreener.com <code>.TW consensus` |
| **EU** | `site:yahoo.com <ticker> financials` → bare search | `<ticker> revenue by segment` → bare search | `site:yahoo.com <ticker> statistics` | `site:marketscreener.com <ticker> consensus` |

Cross-market general: Consensus prefers MarketScreener, valuation prefers stockanalysis.com > yahoo.com. Uncovered markets (SG/IN/AU/SEA) follow bare English search → `[ND]`.

### Current Topic Snapshot

Used for theme / industry / peer workflows:

```text
industry/<industry>/companies/<ticker>/_cache/datasets/financial-data-snapshot/<run-id>/
  snapshot-index.md
  peer-completeness.json
```

Snapshots may link to the canonical company pack but must not duplicate single-company canonical data as a second set of master files.

## Tool Resources

This skill uses:

- If you just want to first check which shared environment variables the workspace needs, consult the unified environment entry provided by `init-workspace` and `_scripts/init-assets/env-setup.ps1.template`. This section still retains `financial-data`'s own complete provider / dependency / bootstrap detail and is not replaced by that shared entry.

- `skills/financial-data/scripts/financial_data.py`
- `skills/financial-data/scripts/bootstrap-financial-data-deps.ps1`
- `skills/financial-data/scripts/providers/sec_provider.py`
- `skills/financial-data/scripts/providers/akshare_provider.py`
- `skills/financial-data/scripts/providers/edinet_provider.py`
- `skills/financial-data/scripts/providers/dart_provider.py`
- `skills/financial-data/scripts/providers/openesef_provider.py`
- `skills/financial-data/assets/requirements-financial-data.txt`

Provider matrix:

| Market | Financial Provider | V1 status | Bridge / Longbridge role |
|---|---|---|---|
| US | EdgarTools / SEC | Three statements + filing markdown + SEC XBRL dimension `revenue_split` when available | **Market data primary**. Financials: `financial_snapshot` for cross-check, does not replace EdgarTools |
| CN A-share | AKShare / Eastmoney | Three statements + `stock_zygc_em` revenue split | **Market data primary**. Financials: cross-check only |
| HK | Eastmoney HKF10 direct | Three statements; prefer provider_api then official_web | **Market data primary** (including AH premium). Financials: cross-check only |
| JP | EDINET official / edinet-tools | EDINET-only route; no J-Quants/Yahoo fallback | Not supported |
| KR | OpenDART official + local corp_code metadata cache | requires `DART_API_KEY` | Not supported |
| TW | FinMind public API | Three statements best-effort | Not supported |
| EU | openesef | ESEF/iXBRL parser route; ticker-only discovery experimental | Not supported |

**Market Data Provider Matrix** (Lite mode four-layer degradation chain: `Bridge → yfinance → WebSearch → Google Finance`):

| Market | Layer 1: Bridge | Layer 2: yfinance | Layer 3: WebSearch | Layer 4: Google Finance |
|---|---|---|---|---|
| **US** | ✅ primary — all fields | fallback | last resort | last resort |
| **HK** | ✅ primary — all fields + AH premium | fallback | last resort | last resort |
| **SH/SZ** | ✅ primary — all fields | fallback | last resort | last resort |
| **JP** | ❌ skip | primary — acceptable | last resort (search `8035 PER 時価総額`) | last resort |
| **KR** | ❌ skip | primary — often missing fields | last resort (search `005930 PER 시가총액`) | last resort |
| **TW** | ❌ skip | primary — unstable | last resort (search `2330 本益比 市值`) | last resort |
| **SE/NL/DE** | ❌ skip | primary — small cap missing fields | last resort (search `MYCR PE ratio`) | last resort |
| **SG/IN/AU** | ❌ skip | primary | last resort | last resort |

Each field is independently labeled `[source_layer | as-of date]`; no global TTL. Lower layers must not overwrite higher layers.

KR / JP source policy:

- KR uses OpenDART official APIs only: a local 30-day metadata cache may store ticker -> corp_code identity mapping under `%LOCALAPPDATA%\buy-side-research-skills\financial-data-cache\dart-corp-code\`, but `fnlttSinglAcntAll.json` statements and `document.xml` full filing ZIP/Markdown are always fetched live. Set `BSRS_DART_CORP_CACHE_REFRESH=1` to force a corp_code metadata refresh. Do not cache KR statements, filing receipt numbers, ZIPs, Markdown, or research results.
- JP uses EDINET official APIs only. Daily document-list metadata may be cached locally to avoid repeated discovery scans, but the source filing remains the EDINET type=1 ZIP and full filing Markdown is only evidence-ready when that ZIP exists.
- Yahoo/yfinance is not a source-tracked `financial-data` provider for JP/KR three statements or filings.
- HK statements use Eastmoney HKF10 direct as the formal statement route. Do not use Longbridge as the HK statement source; Longbridge may supplement market data or consensus only.
- Layer 3 web fallback is priority-split into `official_web -> trusted_web -> broad_web`. `official_web` includes company IR/results pages plus official filing portals such as SEC, EDINET, DART, MOPS, and CNINFO when they are found via search/browser/PDF parsing rather than fetched through a stable provider route.
- Query-chain precedence must reflect that contract: for example `site:sec.gov`, `site:hkexnews.hk`, `site:disclosure.edinet-fsa.go.jp`, `site:dart.fss.or.kr`, `site:mops.twse.com.tw`, and `site:cninfo.com.cn` belong in `official_web`, not `trusted_web`.
- EU `openesef` currently requires a local ESEF package or explicit filing URL for deterministic parsing. If no local ESEF package is available, Lite should skip the `openesef` Layer 2 route and move directly to `official_web` fallback instead of treating the missing local package as a normal statement-provider failure.
- Source-trust ranking is formal: `provider_api + official_web > yfinance > trusted_web + broad_web`. Lower-trust sources must not overwrite higher-trust sources. Provider-fetched official filing caches remain `provider_api`; official company IR/results pages and official filing portals discovered via search remain `official_web`.
- Non-finite numeric placeholders such as `NaN` / `inf` are invalid in `actuals-resolved.json` and must be normalized back to missing before coverage, overwrite, or consumer use. They must not count as filled fields.
- `official_web` may also be materialized as a curated machine-readable cache at `industry/<industry>/companies/<ticker>/_cache/financial-data/internal/_raw/official_web_cache.json` when a company IR/results page or attached official PDF has already been source-read and normalized. Those cache entries stay `official_web`, not `provider_api`, and may carry scalar fields plus structured `segments.status` / `segments.segments`.
- `yfinance` may bootstrap statement fields when provider routes are absent, but only as a lower-trust fill layer. It should not displace existing `provider_api` or `official_web` values.
- Lite consumer-success coverage should optimize `provider_api + official_web` first. Do not rely on `trusted_web` / `broad_web` to make surface-level coverage look complete.
- `provider-gap` must be reasoned rather than generic. Use `provider_unavailable`, `official_source_available_not_extracted`, or `not_disclosed` instead of a single ambiguous gap label.
- Growth-first consumer profile: prioritize revenue, margin, segments, geography, `operating_cf`, and `capex`. Coarse usable debt fields such as `short_term_debt` and `long_term_debt` still matter when they change funding risk or runway; only finer debt detail should be treated as best-effort. Treat `supplementary.order_backlog` as sector-conditional, and treat `supplementary.sbc`, `cash_flow.*.dividends_paid`, `cash_flow.*.share_buybacks`, and fine debt detail as best-effort rather than universal Lite blockers.

Segment rule:

- Whenever a company discloses a structurally capturable split, preferentially write it back to `actuals-resolved.json` under `segments.status` + `segments.segments`; do not leave only a pending query.
- `segments.segments` is a generic container that allows simultaneously carrying different dimensions such as `business_line`, `geography`, and `end_market`, distinguished by `type`.
- `segments.segments` may optionally carry quantitative auxiliary fields such as `pct_of_total`, `yoy_pct`, `sequential_pct`, `margin_pct`, and `ratio`. If official disclosure provides ratios, year-over-year, sequential, or margin figures rather than absolute values, landing those fields first is allowed; when the period total, prior-year, prior-period, or denominator is known, the runtime should perform reversible back-calculation where possible and fill in the missing anchor points.
- `supplementary.revenue_by_geography` is the consumer convenience view for geography splits; if a geography split is disclosed, it should be written back or derived synchronously.
- When a split cannot be structurally captured, do not create a fake split; explicitly label `pending_official_extraction`, `provider_unavailable`, or `not_disclosed`. Do not collapse different gap causes into a single `provider-gap`.

## File Safety

- Do not overwrite an existing run-id directory; repeated runs at the same time must generate a new run-id or fail.
- Do not write an empty successful pack; when data is missing, write `provider-gap` / `partial`, or hard fail — do not pretend completeness.
- Do not create `research-journal.md`, `company-history.md`, `driver-map.md`, or workbooks.
- Do not treat a current topic snapshot as canonical company data.
- Do not move the user's existing `_raw/` files.
- When a dependency or credential is missing, do not write a fake cache.

## Runtime Output Contract

```markdown
## Financial Data Result

**Conclusion-first**
[available / partial / provider-gap / failed — one sentence on whether it can be used by 3-statement-model / dcf-model / comps-analysis / model-update]

| Data item | Status | Source/provider | Period coverage | Model usable? | Caveat |
|---|---|---|---|---|---|
| Income statement | available / partial / unavailable / provider-gap | [...] | [...] | yes / review / no | [...] |

## Output
- raw: [...]
- cache: [...]
- summary: `_cache/financial-data/financial-data-summary.md`
- internal_machine_inputs: `_cache/financial-data/internal/`
- financial_data_pack_path: [...]

## Provider / Credential
- market: [...]
- identifier_type: [...]
- provider: [...]
- credential_status: [...]

## Caveats
- [...]
```

`available / partial / unavailable / provider-gap` must be written clearly per field. In particular, the three statements and `revenue_split` must be labeled with separate statuses.

## Failure Handling

- The shared environment entry can first be checked via `init-workspace`, but this section remains the detailed source of truth for financial data environment configuration and honest-fail boundaries.
- Missing dependency: output what is missing and the bootstrap command; do not write a successful cache.
- Missing `EDGAR_IDENTITY`: US SEC route failed; do not claim SEC/XBRL is available.
- Missing `DART_API_KEY`: KR route failed; do not write fake DART data.
- EU ticker-only unable to discover: output `provider-gap`, suggest switching to `filing_url` or `local_esef_package`.
- Topic does not exist: agent auto-creates directory and index per policy baseline §11.
- Provider returns missing fields: write a partial pack and completeness matrix; do not infer undisclosed revenue split.

## Workflow Linkages

| Scenario | Handling |
|---|---|
| User only has local PDF / XLSX / CSV | Hand to `ingest` |
| User wants to pull structured financials by ticker / filing package | Use `financial-data` |
| User wants to explain revenue buckets or drivers | After `financial-data`, hand to `driver-map` |
| User wants to model, DCF, comps, update workbook | `financial-data` can serve as optional input to `3-statement-model / dcf-model / comps-analysis / model-update` |
| Theme / industry needs a basket of company data | Use `current_topic_snapshot`, and link to the canonical company pack |
| Data gaps affect model or research priority | `next-step` / `driver-map` / `company-history` |

Artifact policy:

- `save_policy`: `cache_artifact`
- `default_artifact`: `financials.md`
- `canonical_location`: `industry/<industry>/companies/<ticker>/_cache/datasets/financial-data/[market]/[canonical-id]/[run-id]/`

## Safety Self-Check

- ❌ Writing a provider-normalized field as a company disclosed fact.
- ❌ Not inferring undisclosed revenue split, but filling gaps with historical ratios when segments are missing.
- ❌ Treating three statements as model-ready just because they are available.
- ❌ Claiming openesef supports full European stock fetching when EU ticker-only cannot find a filing.
- ❌ Writing Korean financial statement cache when `DART_API_KEY` is missing.
- ❌ Claiming the SEC route is complete when `EDGAR_IDENTITY` is missing.
- ❌ Treating a theme snapshot as canonical company data.
- ❌ Writing research conclusions, forecasts, DCF, or price targets.
- ❌ Not outputting `completeness.json` or `source-map.json`.
- ❌ Not writing `identity-source.json`, `source-metadata.json`, or `source.sha256` when an official filing source exists.
- ❌ Overwriting an existing run-id directory.
