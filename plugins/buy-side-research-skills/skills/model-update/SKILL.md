---
name: model-update
description: Update a financial model for earnings guidance new data or revised assumptions.
---

# Model Update

Update a financial model for earnings guidance new data or revised assumptions.

## Modeling Runtime Capsule

- Hook-enforced modeling rules (missing_actuals_not_zero, balance_integrity, structure_floor, etc.) live in workspace hooks.

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.
- Shared modeling protocol: workspace `.references/policy/research-policy-baseline.md` §6.
- **数据源**：从 `actuals-resolved.json` 取 historical actuals，从 `.cache/driver-map/` 取 driver assumptions。缺失 actuals 不填零。
- Sub-agent QA bounded; main agent owns the final workbook.

- Missing or unmapped actuals stay blank or flagged; never coerce them to zero.
- **Actuals-only ratio rule**: any ratio or derived metric in the updated model must trace back to actuals-resolved.json disclosed data. No estimate input for computed ratios.

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

**Forward 回写（estimates 层，L1）：** 模型更新后，把新 FY1 关键数字回写到 estimates-resolved.json，让日报估值列显示更新后的假设（`L1 fwd`）：

```bash
python3 .scripts/financial-data/estimates_store.py set-forward <TICKER> \
  --basis model --source model-update --currency <币种> \
  --eps <FY1 EPS> --revenue <FY1 Rev> --ebitda <FY1 EBITDA> --net-income <FY1 NI> ...
```

必写 `--eps` 或 `--revenue` 至少一个；拿不到的字段不传（null 不硬凑）。新值覆盖旧值，旧值自动进 `history`（append-only）。跑完留一行：`Forward 已回写 estimates-resolved.json（FY1 eps=… basis=model）`。

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

