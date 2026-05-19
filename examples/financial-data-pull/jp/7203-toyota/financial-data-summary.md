# TOYOTA MOTOR CORPORATION Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `jp` / `7203`
- Provider: `edinet-tools`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-fix-smoke\topics\company\7203-toyota\_cache\datasets\financial-data\jp\7203\20260518T083805Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `fetched`
- Filing date: `2025-06-18`
- Accession / document id: `S100VWVY`
- Full filing retained internally: `True`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | edinet-tools | FY2023-FY2025 | evidence-ready |  |
| filing_index | evidence-ready | edinet-tools | FY2023-FY2025 | evidence-ready |  |
| latest_full_filing | evidence-ready | edinet-tools | FY2023-FY2025 | evidence-ready |  |
| income_statement | model-ready | edinet-tools | FY2023-FY2025 | model-ready |  |
| balance_sheet | model-ready | edinet-tools | FY2023-FY2025 | model-ready |  |
| cash_flow | model-ready | edinet-tools | FY2023-FY2025 | model-ready |  |
| revenue_split | provider-gap | edinet-tools | FY2023-FY2025 | provider-gap | no stable structured EDINET revenue split parser in this route |

## Structured Actuals

- `income_statement`: 8 rows; periods: FY2024, FY2025
- `balance_sheet`: 12 rows; periods: FY2025
- `cash_flow`: 3 rows; periods: FY2025
- `revenue_split`: 0 rows; periods: none

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- revenue_split: no stable structured EDINET revenue split parser in this route
