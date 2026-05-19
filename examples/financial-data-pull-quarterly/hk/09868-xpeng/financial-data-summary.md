# 09868-xpeng Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `hk` / `09868`
- Provider: `akshare`
- Period filter: `latest4q`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-quarterly-smoke\topics\company\09868-xpeng\_cache\datasets\financial-data\hk\09868\20260518T085535Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `unavailable`
- Filing date: ``
- Accession / document id: ``
- Full filing retained internally: `False`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | provider-normalized-review | akshare | latest4q | provider-normalized-review |  |
| filing_index | provider-gap | akshare | latest4q | provider-gap |  |
| latest_full_filing | provider-gap | akshare | latest4q | provider-gap |  |
| income_statement | provider-normalized-review | akshare | latest4q | provider-normalized-review |  |
| balance_sheet | provider-normalized-review | akshare | latest4q | provider-normalized-review |  |
| cash_flow | provider-normalized-review | akshare | latest4q | provider-normalized-review |  |
| revenue_split | provider-gap | akshare | latest4q | provider-gap | no stable free structured HK revenue split route |

## Structured Actuals

- `income_statement`: 24 rows; periods: 2024-06-30, 2024-12-31, 2025-06-30, 2025-12-31
- `balance_sheet`: 49 rows; periods: 2024-06-30, 2024-12-31, 2025-06-30, 2025-12-31
- `cash_flow`: 40 rows; periods: 2024-06-30, 2024-12-31, 2025-06-30, 2025-12-31
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
