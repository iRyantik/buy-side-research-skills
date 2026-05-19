# 스피어 Financial Data Summary

**Conclusion**

- Status: `success`
- Market / identifier: `kr` / `347700`
- Provider: `dart-fss`
- Period filter: `latest4q`
- Latest run cache: `C:\Users\M\AppData\Local\Temp\bsrs-financial-data-kr-derived-smoke\topics\company\347700-sphere\_cache\datasets\financial-data\kr\347700\20260518T094147Z`
- Internal machine data: `internal/`

## Filing

- Filing status: `unavailable`
- Filing date: ``
- Accession / document id: ``
- Full filing retained internally: `False`

## Completeness Matrix

| Data item | Status | Provider | Period coverage | Model usable | Caveat |
|---|---|---|---|---|---|
| identity | evidence-ready | dart-fss | latest4q | evidence-ready |  |
| filing_index | provider-gap | dart-fss | latest4q | provider-gap |  |
| latest_full_filing | provider-gap | dart-fss | latest4q | provider-gap |  |
| income_statement | model-ready | dart-fss | latest4q | model-ready |  |
| balance_sheet | model-ready | dart-fss | latest4q | model-ready |  |
| cash_flow | model-ready | dart-fss | latest4q | model-ready |  |
| revenue_split | provider-gap | dart-fss | latest4q | provider-gap | no stable free structured DART revenue split route |

## Structured Actuals

- `income_statement`: 30 rows; periods: FY2025, FY2025H1, FY2025Q3, FY2026Q1
- `balance_sheet`: 53 rows; periods: FY2025, FY2025H1, FY2025Q3, FY2026Q1
- `cash_flow`: 32 rows; periods: FY2025, FY2025H1, FY2025Q3, FY2026Q1
- `revenue_split`: 0 rows; periods: none
- `income_statement_quarterly_derived`: 29 rows; periods: FY2025Q2, FY2025Q3, FY2025Q4, FY2026Q1
- `cash_flow_quarterly_derived`: 28 rows; periods: FY2025Q2, FY2025Q3, FY2025Q4, FY2026Q1

## Derived Quarter-Only KR Flow Statements

- OpenDART Q1/H1/Q3/FY flow statements can be cumulative; original cumulative rows are retained.
- Derived rows are calculated as `Q1 = Q1`, `Q2 = H1 - Q1`, `Q3 = Q3_YTD - H1`, `Q4 = FY - Q3_YTD`.
- Balance sheet is not derived because it is a point-in-time statement.
- `income_statement_quarterly_derived`: 29 rows; derived periods: FY2025Q2, FY2025Q3, FY2025Q4, FY2026Q1
- `cash_flow_quarterly_derived`: 28 rows; derived periods: FY2025Q2, FY2025Q3, FY2025Q4, FY2026Q1

## Model Input Policy

- Public surface is Markdown-only: this summary is the default file for humans and LLMs.
- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.
- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.
- Unmapped / unavailable items:
  - `filing_index`: `provider-gap`
  - `latest_full_filing`: `provider-gap`
  - `revenue_split`: `provider-gap`

## Errors / Caveats

- financial_statements_2026_H1: OpenDART returned no CFS/OFS rows
- financial_statements_2026_Q3: OpenDART returned no CFS/OFS rows
- financial_statements_2026_FY: OpenDART returned no CFS/OFS rows
- quarterly_statement_scope: OpenDART Q1/H1/Q3 values may be cumulative reporting-period amounts
- revenue_split: no stable free structured DART revenue split route
