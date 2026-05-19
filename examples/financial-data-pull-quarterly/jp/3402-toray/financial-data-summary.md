# TORAY INDUSTRIES,INC. Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `jp` / `3402`
- Provider: `edinet-tools`
- Period filter: `latest4q`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-quarterly-smoke\topics\company\3402-toray\_cache\datasets\financial-data\jp\3402\20260518T090229Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `fetched`
- Filing date: `2025-11-14`
- Accession / document id: `S100X38C`
- Full filing retained internally: `True`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | edinet-tools | latest4q | evidence-ready |  |
| filing_index | evidence-ready | edinet-tools | latest4q | evidence-ready |  |
| latest_full_filing | evidence-ready | edinet-tools | latest4q | evidence-ready |  |
| income_statement | model-ready | edinet-tools | latest4q | model-ready |  |
| balance_sheet | model-ready | edinet-tools | latest4q | model-ready |  |
| cash_flow | model-ready | edinet-tools | latest4q | model-ready |  |
| revenue_split | provider-gap | edinet-tools | latest4q | provider-gap | no stable structured EDINET revenue split parser in this route |

## Structured Actuals

- `income_statement`: 8 rows; periods: 2025-03-31, 2026-03-31, FY2024, FY2025
- `balance_sheet`: 12 rows; periods: 2025-03-31, 2026-03-31, FY2024, FY2025
- `cash_flow`: 3 rows; periods: FY2024, FY2025
- `revenue_split`: 0 rows; periods: none

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- revenue_split: no stable structured EDINET revenue split parser in this route
