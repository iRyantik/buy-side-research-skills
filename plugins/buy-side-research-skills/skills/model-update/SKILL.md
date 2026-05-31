---
name: model-update
description: Update a financial model for earnings guidance new data or revised assumptions.
---

# Model Update

Update a financial model for earnings guidance new data or revised assumptions.

## Modeling Runtime Capsule

- Hook-enforced workbook legality, change-map floors, valuation-basis checks, and sub-agent boundary rules live in workspace hooks and are not restated here.
- Before updating, verify actuals completeness, source-map coverage, review flags, and evidence-pack status.
- Missing or unmapped actuals stay blank or flagged; never coerce them to zero.
- Use bounded QA sub-agents only; the main agent owns the final workbook or update memo, valuation treatment, and delivery.

## Research Workspace Adapter

In this research workspace, prefer source-tracked company-topic inputs before external, web, or manual data:
- `_cache/financial-data/financial-data-summary.md` for human/LLM review
- `_cache/financial-data/internal/actuals-resolved.json` for machine historical actuals
- `_cache/financial-data/internal/evidence-pack.json` for completeness/source-map/cross-check
- `industry/<industry>/companies/<ticker>/_cache/driver-map/driver-map.md` for human/LLM driver treatment
- `industry/<industry>/companies/<ticker>/_cache/driver-map/internal/driver-map.json` for machine driver inputs

Separate reported actuals, revised assumptions, and formula changes. Do not plug missing or unmapped actuals as zero, and do not overwrite a workbook without a visible update map.

If `actuals-resolved.json` contains `income_statement_quarterly_derived` or `cash_flow_quarterly_derived`, use those rows for single-quarter reported flow updates; keep the original cumulative rows as audit evidence. Never derive or subtract balance sheet rows because they are point-in-time values.

## Model Sub-Agent Protocol

- Use sub-agents only for bounded QA work-packets; they return notes, not workbook edits or valuation conclusions.
- Close QA sub-agents once notes return; the main agent owns the update map, valuation treatment, and delivery.
- Useful QA buckets: reported-actuals reconciliation, assumption/formula delta review, and actuals completeness review.

# Model Update

description: Update financial models with new data — quarterly earnings, management guidance, macro changes, or revised assumptions. Adjusts estimates, recalculates valuation, and flags material changes. Use after earnings, guidance updates, or when assumptions need refreshing. Triggers on "update model", "plug earnings", "refresh estimates", "update numbers for [company]", "new guidance", or "revise estimates".

## Workflow

### Step 1: Identify What Changed

Determine the update trigger:
- **Earnings release**: New quarterly actuals to plug in
- **Guidance change**: Company updated forward outlook
- **Estimate revision**: Analyst changing assumptions based on new data
- **Macro update**: Interest rates, FX, commodity prices changed
- **Event-driven**: M&A, restructuring, new product, management change

### Step 2: Plug New Data

#### After Earnings
Update the model with reported actuals:

| Line Item | Prior Estimate | Actual | Delta | Notes |
|-----------|---------------|--------|-------|-------|
| Revenue | | | | |
| Gross Margin | | | | |
| Operating Expenses | | | | |
| EBITDA | | | | |
| EPS | | | | |
| [Key metric 1] | | | | |
| [Key metric 2] | | | | |

**Segment Detail** (if applicable):
- Update each segment's revenue and margin
- Note any segment mix shifts

**Balance Sheet / Cash Flow Updates**:
- Cash and debt balances
- Share count (buybacks, dilution)
- Capex actual vs. estimate
- Working capital changes

### Step 3: Revise Forward Estimates

Based on the new data, adjust forward estimates:

| | Old FY Est | New FY Est | Change | Old Next FY | New Next FY | Change |
|---|-----------|-----------|--------|------------|------------|--------|
| Revenue | | | | | | |
| EBITDA | | | | | | |
| EPS | | | | | | |

**Key Assumption Changes:**
- What assumptions are you changing and why?
- Revenue growth rate: old → new (reason)
- Margin assumption: old → new (reason)
- Any new items (restructuring charges, one-time gains, etc.)

### Step 4: Valuation Impact

Recalculate valuation with updated estimates:

| Valuation Method | Prior | Updated | Change |
|-----------------|-------|---------|--------|
| DCF fair value | | | |
| P/E (NTM EPS × target multiple) | | | |
| EV/EBITDA (NTM EBITDA × target multiple) | | | |
| **Price Target** | | | |

### Step 5: Summary & Action

**Estimate Change Summary:**
- One paragraph: what changed, why, and what it means for the stock
- Is this a thesis-changing event or noise?

**Rating / Price Target:**
- Maintain or change rating?
- New price target (if changed) with methodology
- Upside/downside to current price

### Step 6: Output

- Updated Excel model (if user provides the existing model)
- Estimate change summary (markdown or Word)
- Updated price target derivation

## Important Notes

- Always reconcile your estimates to the company's reported figures before projecting forward
- Note any non-recurring items and whether your estimates are GAAP or adjusted
- Track your estimate revision history — it shows your analytical progression
- If the quarter was noisy, separate signal from noise in your estimate changes
- Check consensus after updating — how do your revised estimates compare to the Street?
- Share count matters — dilution from stock comp, converts, or buybacks can materially affect EPS
