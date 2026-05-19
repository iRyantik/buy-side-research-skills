# 300750-catl-a Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `cn` / `300750`
- Provider: `akshare`
- Period filter: `FY2023-FY2025`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-smoke\topics\company\300750-catl-a\_cache\datasets\financial-data\cn\300750\20260518T074031Z`
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
| revenue_split | provider-normalized-review | akshare | FY2023-FY2025 | provider-normalized-review |  |

## Structured Actuals

- `income_statement`: 97 rows; periods: 2023一季报, 2023三季报, 2023中报, 2023年报, 2024一季报, 2024三季报, 2024中报, 2024年报, 2025一季报, 2025三季报, 2025中报, 2025年报
- `balance_sheet`: 142 rows; periods: 2023一季报, 2023三季报, 2023中报, 2023年报, 2024一季报, 2024三季报, 2024中报, 2024年报, 2025一季报, 2025三季报, 2025中报, 2025年报
- `cash_flow`: 143 rows; periods: 2023一季报, 2023三季报, 2023中报, 2023年报, 2024一季报, 2024三季报, 2024中报, 2024年报, 2025一季报, 2025三季报, 2025中报, 2025年报
- `revenue_split`: 12 rows; periods: 2023-06-30, 2023-12-31, 2024-06-30, 2024-12-31, 2025-06-30, 2025-12-31

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `filing_index`: `provider-gap`
  - `latest_full_filing`: `provider-gap`
