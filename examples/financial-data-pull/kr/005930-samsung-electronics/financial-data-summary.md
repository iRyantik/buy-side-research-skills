# 삼성전자 Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `kr` / `005930`
- Provider: `dart-fss`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-fix-smoke\topics\company\005930-samsung-electronics\_cache\datasets\financial-data\kr\005930\20260518T083741Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `unavailable`
- Filing date: ``
- Accession / document id: ``
- Full filing retained internally: `False`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | dart-fss | FY2023-FY2025 | evidence-ready |  |
| filing_index | provider-gap | dart-fss | FY2023-FY2025 | provider-gap |  |
| latest_full_filing | provider-gap | dart-fss | FY2023-FY2025 | provider-gap |  |
| income_statement | model-ready | dart-fss | FY2023-FY2025 | model-ready |  |
| balance_sheet | model-ready | dart-fss | FY2023-FY2025 | model-ready |  |
| cash_flow | model-ready | dart-fss | FY2023-FY2025 | model-ready |  |
| revenue_split | provider-gap | dart-fss | FY2023-FY2025 | provider-gap | no stable free structured DART revenue split route |

## Structured Actuals

- `income_statement`: 30 rows; periods: FY2023, FY2024, FY2025
- `balance_sheet`: 58 rows; periods: FY2023, FY2024, FY2025
- `cash_flow`: 41 rows; periods: FY2023, FY2024, FY2025
- `revenue_split`: 0 rows; periods: none

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `filing_index`: `provider-gap`
  - `latest_full_filing`: `provider-gap`
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- revenue_split: no stable free structured DART revenue split route
