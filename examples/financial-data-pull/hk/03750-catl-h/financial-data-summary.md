# 03750-catl-h Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `hk` / `03750`
- Provider: `akshare`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-smoke\topics\company\03750-catl-h\_cache\datasets\financial-data\hk\03750\20260518T074041Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `unavailable`
- Filing date: ``
- Accession / document id: ``
- Full filing retained internally: `False`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | provider-normalized-review | akshare | FY2023-FY2025 | provider-normalized-review |  |
| filing_index | provider-gap | akshare | FY2023-FY2025 | provider-gap |  |
| latest_full_filing | provider-gap | akshare | FY2023-FY2025 | provider-gap |  |
| income_statement | provider-normalized-review | akshare | FY2023-FY2025 | provider-normalized-review |  |
| balance_sheet | provider-normalized-review | akshare | FY2023-FY2025 | provider-normalized-review |  |
| cash_flow | provider-normalized-review | akshare | FY2023-FY2025 | provider-normalized-review |  |
| revenue_split | provider-gap | akshare | FY2023-FY2025 | provider-gap | no stable free structured HK revenue split route |

## Structured Actuals

- `income_statement`: 32 rows; periods: 2023-12-31, 2024-12-31, 2025-12-31
- `balance_sheet`: 65 rows; periods: 2023-12-31, 2024-12-31, 2025-12-31
- `cash_flow`: 26 rows; periods: 2023-12-31, 2024-12-31, 2025-12-31
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

- revenue_split: no stable free structured HK revenue split route
