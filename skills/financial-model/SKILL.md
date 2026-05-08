---
name: financial-model
description: Use when building or updating buy-side Excel financial models, especially revenue-first models with segment and driver decomposition, earnings actuals refreshes, or model assumption updates.
---

# Financial Model

Build or update a buy-side Excel model. The core job is not to force a standard template; it is to preserve the model's useful structure while making revenue drivers explicit enough to support thesis work.

## Source Policy

Follow `CLAUDE.md §3`. Financial statement actuals, segment data, guidance, consensus, model assumptions, and as-of market data must have sources or be marked `[需查证]` / `[来源待补]`. Do not invent missing disclosure.

## Modes

### Mode A: Build New Model

Use when the user asks to:
- "搭一个 model"
- "build a model"
- "帮我拆收入"
- "给 X 公司做 revenue model"

Output target: `coverage/[ticker]/model.xlsx`.

Principles:
- Use a light model skeleton, not a rigid 5-sheet template.
- Start with reported revenue segments, then break each segment into observable drivers where possible.
- Useful drivers include price, volume, mix, backlog, utilization, installed base, customer count, bookings, capacity, production, and take rate.
- If the company only discloses total revenue or high-level segments, keep placeholders and mark the missing driver data. Do not fabricate segment drivers.
- First version is revenue-first. Add gross margin / EBITDA margin only as a light bridge when needed; do not build a full three-statement model unless the user explicitly asks.

Minimum output in chat:
1. Revenue architecture: segments, streams, and drivers.
2. Model layout proposal: sheets / sections tailored to this company.
3. Source map: where each actual, driver, and assumption comes from.
4. Missing disclosure: what the company does not disclose and how to handle it.

### Mode B: Update Existing Model

Use when the user asks to:
- "根据新财报更新 model"
- "更新已有 Excel model"
- "把新 quarter actuals 放进模型"
- "refresh the model from earnings"

Core rule: preserve the existing workbook. Do not rename sheets, move model blocks, overwrite formulas, or migrate the workbook into a standard template.

Workflow:
1. Inspect the workbook structure first: sheet names, period columns, actual / forecast boundary, formulas, hardcodes, source notes, and output summary.
2. Identify what the new earnings release changes: actual revenue by segment, drivers, guidance, margins, backlog, orders, cash flow items if relevant.
3. Produce an update map before editing: sheet / section / row or cell area, old value, new value, source, and whether the change is actual, guidance, or assumption.
4. If the actual / forecast area cannot be located reliably, stop at the update map and ask for confirmation instead of editing the workbook.
5. If editing is allowed, update only the necessary actuals and forward assumptions; preserve old historical actuals and formulas.

Minimum output in chat:
- **Update summary**: what changed and why it matters.
- **Update map**: where the model should change.
- **Model integrity risks**: formulas, links, or hardcodes that need caution.
- **Thesis read-through**: whether the model update changes variant view, catalyst, or decision triggers.

## Handoff

- Feeds `alpha-thesis` by turning revenue drivers into variant-view assumptions.
- Feeds `earnings-setup` by defining the model lines that matter before a print.
- Feeds `thesis-tracker` when new actuals change `key_assumptions`, `next_catalyst`, or `health_status`.
- Can trigger `decision-journal` if the model update changes action.

## Anti-Patterns

- Forcing every company into the same workbook template.
- Rebuilding an existing model from scratch when the user asked for an update.
- Replacing formulas with hardcodes without flagging it.
- Inventing segment drivers when the company does not disclose them.
- Treating a model as finished without a source map and missing-disclosure list.
