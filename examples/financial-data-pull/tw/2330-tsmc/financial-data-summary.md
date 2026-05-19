# 2330-tsmc Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `tw` / `2330`
- Provider: `finmind`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-smoke\topics\company\2330-tsmc\_cache\datasets\financial-data\tw\2330\20260518T074549Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `unavailable`
- Filing date: ``
- Accession / document id: ``
- Full filing retained internally: `False`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | provider-normalized-review | finmind | FY2023-FY2025 | provider-normalized-review |  |
| filing_index | provider-gap | finmind | FY2023-FY2025 | provider-gap |  |
| latest_full_filing | provider-gap | finmind | FY2023-FY2025 | provider-gap |  |
| income_statement | provider-normalized-review | finmind | FY2023-FY2025 | provider-normalized-review |  |
| balance_sheet | provider-normalized-review | finmind | FY2023-FY2025 | provider-normalized-review |  |
| cash_flow | provider-normalized-review | finmind | FY2023-FY2025 | provider-normalized-review |  |
| revenue_split | provider-gap | finmind | FY2023-FY2025 | provider-gap | no stable free structured TW revenue split route |

## Structured Actuals

- `income_statement`: 17 rows; periods: 2023-03-31, 2023-06-30, 2023-09-30, 2023-12-31, 2024-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2025-12-31
- `balance_sheet`: 103 rows; periods: 2023-03-31, 2023-06-30, 2023-09-30, 2023-12-31, 2024-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2025-12-31
- `cash_flow`: 30 rows; periods: 2023-03-31, 2023-06-30, 2023-09-30, 2023-12-31, 2024-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2025-12-31
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

- revenue_split: no stable free structured TW revenue split route
