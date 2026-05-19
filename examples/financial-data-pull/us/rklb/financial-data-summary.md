# Rocket Lab Corp Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `us` / `RKLB`
- Provider: `edgartools`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-smoke\topics\company\rklb\_cache\datasets\financial-data\us\rklb\20260518T074010Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `fetched`
- Filing date: `2026-02-26`
- Accession / document id: `0001819994-26-000013`
- Full filing retained internally: `True`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | edgartools | FY2023-FY2025 | evidence-ready |  |
| filing_index | evidence-ready | edgartools | FY2023-FY2025 | evidence-ready |  |
| latest_full_filing | evidence-ready | edgartools | FY2023-FY2025 | evidence-ready |  |
| income_statement | model-ready | edgartools | FY2023-FY2025 | model-ready |  |
| balance_sheet | model-ready | edgartools | FY2023-FY2025 | model-ready |  |
| cash_flow | model-ready | edgartools | FY2023-FY2025 | model-ready |  |
| revenue_split | provider-gap | edgartools | FY2023-FY2025 | provider-gap | SEC segment/geography extraction requires a dedicated XBRL dimensions or filing-table parser |

## Structured Actuals

- `income_statement`: 25 rows; periods: FY 2023, FY 2024, FY 2025
- `balance_sheet`: 30 rows; periods: FY 2023, FY 2024, FY 2025
- `cash_flow`: 37 rows; periods: FY 2023, FY 2024, FY 2025
- `revenue_split`: 0 rows; periods: none

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- revenue_split: SEC segment/geography extraction requires a dedicated XBRL dimensions or filing-table parser
