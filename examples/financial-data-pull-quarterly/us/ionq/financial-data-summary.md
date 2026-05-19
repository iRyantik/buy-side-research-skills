# IonQ, Inc. Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `us` / `IONQ`
- Provider: `edgartools`
- Period filter: `latest4q`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-quarterly-smoke\topics\company\ionq\_cache\datasets\financial-data\us\ionq\20260518T085323Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `fetched`
- Filing date: `2026-05-07`
- Accession / document id: `0001193125-26-211876`
- Full filing retained internally: `True`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | edgartools | latest4q | evidence-ready |  |
| filing_index | evidence-ready | edgartools | latest4q | evidence-ready |  |
| latest_full_filing | evidence-ready | edgartools | latest4q | evidence-ready |  |
| income_statement | model-ready | edgartools | latest4q | model-ready |  |
| balance_sheet | model-ready | edgartools | latest4q | model-ready |  |
| cash_flow | model-ready | edgartools | latest4q | model-ready |  |
| revenue_split | provider-gap | edgartools | latest4q | provider-gap | SEC segment/geography extraction requires a dedicated XBRL dimensions or filing-table parser |

## Structured Actuals

- `income_statement`: 23 rows; periods: Q1 2026, Q2 2025, Q3 2025, Q4 2025
- `balance_sheet`: 29 rows; periods: Q1 2025, Q1 2026, Q2 2025, Q3 2025
- `cash_flow`: 33 rows; periods: Q1 2026, Q2 2025, Q3 2025, Q4 2025
- `revenue_split`: 0 rows; periods: none

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- revenue_split: SEC segment/geography extraction requires a dedicated XBRL dimensions or filing-table parser
