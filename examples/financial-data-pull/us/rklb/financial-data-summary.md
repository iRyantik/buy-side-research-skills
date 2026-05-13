# RKLB Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `us` / `RKLB`
- Provider: `edgartools / SEC`
- Period coverage: `FY2023-FY2025`
- Source filing: FY2025 Form 10-K, filed 2026-02-26, accession `0001819994-26-000013`
- SEC URL: https://www.sec.gov/Archives/edgar/data/1819994/000181999426000013/rklb-20251231.htm
- Internal machine data: `internal/financial-data/`

## Completeness Matrix

| Data item | Status | Source/provider | Period coverage | Model usable? | Caveat |
|---|---|---|---|---|---|
| Identity | evidence-ready | SEC / EdgarTools | FY2023-FY2025 | yes | Company identity resolved from SEC data. |
| Filing index | evidence-ready | SEC / EdgarTools | FY2023-FY2025 | yes | Latest 10-K identified and indexed. |
| Latest full filing | evidence-ready | SEC / EdgarTools | FY2025 10-K | yes, for evidence review | Full filing is retained internally, not exposed as a top-level artifact. |
| Income statement | model-ready | SEC XBRL | FY2023-FY2025 | yes | Use `internal/financial-data/actuals-resolved.json` for machine input. |
| Balance sheet | model-ready | SEC XBRL | FY2023-FY2025 | yes | Use `internal/financial-data/actuals-resolved.json` for machine input. |
| Cash flow | model-ready | SEC XBRL | FY2023-FY2025 | yes | Use `internal/financial-data/actuals-resolved.json` for machine input. |

## Structured Actuals

- `income_statement`: FY2023, FY2024, FY2025 rows extracted.
- `balance_sheet`: FY2023, FY2024, FY2025 rows extracted.
- `cash_flow`: FY2023, FY2024, FY2025 rows extracted.
- Missing/unmapped policy: leave blank and flag review; never fill missing values with zero.

## Internal Files

Machine-readable data and audit evidence are intentionally internal:

- `internal/financial-data/actuals-resolved.json`
- `internal/financial-data/evidence-pack.json`
- `internal/financial-data/financials.normalized.json`
- `internal/financial-data/full-filing.md`
- `internal/financial-data/completeness.json`
- `internal/financial-data/source-map.json`
- `internal/financial-data/cross-check.json`
- `internal/financial-data/_raw/`
