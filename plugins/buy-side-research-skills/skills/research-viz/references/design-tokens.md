# Design Tokens — buy-side editorial

The visual spine. Every chart honors these. Read this file before drawing anything.

## Color palette

The palette is intentionally narrow. One accent per chart, plus neutrals.

```css
:root {
  /* Surfaces */
  --paper:           #FAFAF7;   /* page background — warm white, prints like paper */
  --paper-edge:      #F4F3EE;   /* card/figure background, slightly inset */
  --ink:             #1A1A1A;   /* primary text */
  --ink-2:           #4A4A4A;   /* secondary text */
  --ink-3:           #6B6B6B;   /* tertiary / captions */
  --hairline:        #D4D4CE;   /* 1px borders, table rules */
  --grid:            #E8E7E1;   /* dotted grid lines on charts */

  /* Primary data — the "buy-side blue" */
  --accent:          #1F3A5F;   /* deep navy, the workhorse */
  --accent-soft:     #4A6B8A;   /* lighter navy, secondary series */
  --accent-ghost:    #C8D2DE;   /* navy at low opacity, for bands/fills */

  /* Contrast accent — use sparingly, for ONE highlighted element */
  --highlight:       #8B2635;   /* deep burgundy, never bright red */
  --highlight-soft:  #C77E3A;   /* umber, alternative highlight */

  /* Diverging — for positive/negative, beat/miss, etc. */
  --pos:             #2D5F3F;   /* deep green, never bright */
  --pos-soft:        #A8C4B0;
  --neg:             #8B2635;   /* deep burgundy */
  --neg-soft:        #D4A5A5;
  --neutral:         #B5B5AE;   /* warm gray, the "no signal" color */

  /* Categorical (max 5, used for SOTP / value chain / peer groups) */
  --cat-1:           #1F3A5F;   /* navy */
  --cat-2:           #8B2635;   /* burgundy */
  --cat-3:           #C77E3A;   /* umber */
  --cat-4:           #6B7F5C;   /* sage */
  --cat-5:           #4A5D6C;   /* slate */
}
```

**Rule**: Use `--accent` for the main data series. Use `--highlight` only for ONE thing per chart (the focal point — the current value, the called-out year, the company being valued). Use `--neutral` for everything else (peers, comparisons, context).

For diverging data (beat/miss, YoY growth signs, sensitivity heatmaps), use `--pos` / `--neg` with `--neutral` at zero. Never bright red/green — they read as "alarm" to the eye and break the print aesthetic.

## Typography

```css
:root {
  --font-serif:  'Source Serif Pro', 'Source Serif 4', 'Tinos', 'Georgia', serif;
  --font-sans:   'Inter', 'Helvetica Neue', 'Arial', sans-serif;
  --font-mono:   'JetBrains Mono', 'Source Code Pro', 'Menlo', monospace;
}

body {
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.5;
  font-feature-settings: "tnum" 1, "lnum" 1;  /* tabular + lining numerals globally */
}

.chart-title {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--ink);
  margin: 0 0 4px 0;
}

.chart-subtitle {
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 400;
  color: var(--ink-2);
  margin: 0 0 18px 0;
}

.chart-source {
  font-family: var(--font-sans);
  font-size: 10.5px;
  color: var(--ink-3);
  font-style: italic;
  margin-top: 14px;
  border-top: 1px solid var(--hairline);
  padding-top: 8px;
}

.axis-label, .axis text {
  font-family: var(--font-sans);
  font-size: 11px;
  fill: var(--ink-2);
}

.data-label {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  fill: var(--ink);
}

.callout {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 12px;
  fill: var(--ink-2);
}
```

**Rule**: Serif for the title and editorial callouts. Sans for everything UI (axes, legends, subtitles). Mono with tabular-nums for any number that needs to align (data labels, tables, axis ticks where alignment matters).

## Layout

Two canonical sizes:

| Format | Dimensions (px) | Use for |
|---|---|---|
| Slide / 16:9 | 1200 × 675 | Maps, time series, scatters, sankey, multi-panel |
| Memo column | 800 × 1100 | Vertical stacks (SOTP, debt ladder, Pareto), tall heatmaps, business structure trees |

Inner figure padding: `48px 56px 40px 56px` (top, right, bottom, left). The extra left/right gives room for axis labels and source-line breathing.

Chart drawable area starts at `margin: { top: 60, right: 24, bottom: 48, left: 56 }` inside the inner figure — top space holds title+subtitle.

## Hairlines, grids, ticks

```css
.hairline { stroke: var(--hairline); stroke-width: 1; fill: none; }
.grid line {
  stroke: var(--grid);
  stroke-width: 1;
  stroke-dasharray: 1 3;   /* dotted */
  shape-rendering: crispEdges;
}
.grid path { stroke: none; }   /* hide D3's default grid path */
.axis path, .axis line { stroke: var(--hairline); }
```

**Rule**: Solid hairlines on the baseline (x-axis) and at the chart frame. Dotted (1px dash, 3px gap) on internal grid lines. Never use a heavy grid — readers should read data, not the grid.

## Source attribution

Every chart ends with a source line, always in this format:

```
Source: [primary source]; [secondary if needed]. As of [date]. [Optional: analyst initials].
```

Examples:
- `Source: Company 10-K filings (FY2019–FY2024). As of 31 Mar 2026.`
- `Source: Bloomberg consensus; FactSet. As of 15 Feb 2026. JL.`
- `Source: Author's analysis using Company IR data. As of 1Q26.`

If you do not know the source, ask. Do not omit the line; do not fake the source.

## Number formatting

| Magnitude | Format | Example |
|---|---|---|
| Currency, large | `$X.Xbn`, `$Xbn` | `$2.4bn`, `$28bn` |
| Currency, small | `$Xm`, `$X.Xm` | `$45m`, `$1.2m` |
| Percent | `X.X%` (1 dp default) | `14.2%`, `-3.1%` |
| Basis points | `+XXbps` / `-XXbps` | `+45bps` |
| Multiples | `X.Xx` | `12.4x`, `0.8x` |
| Counts | thousand separators | `42,150` |
| Years | YYYY, optionally `FY` prefix | `FY2024`, `2024E` |
| Quarters | `1Q24`, `4Q23E` | (E = estimate) |
| Dates on charts | `Mar '24` or `1Q24` | (axis labels) |

D3 helpers:
```js
const fmtPct = (d) => d3.format("+.1%")(d);              // +14.2%
const fmtBn  = (d) => "$" + d3.format(".2~s")(d * 1e9);  // $2.4B → render as $2.4bn manually
const fmtX   = (d) => d3.format(".1f")(d) + "x";         // 12.4x
const fmtInt = (d) => d3.format(",")(d);                 // 42,150
```

## Callouts

When you want to draw the eye to ONE thing on a chart (the focal year, the current value, a turning point), use:

- A **filled circle** in `--highlight` at the focal point
- A **thin annotation line** (1px, `--ink-2`) leading off to a short label
- A **serif italic label** (`.callout` class), 12px, in `--ink-2`

Use this at most twice per chart. If you'd need three callouts, the chart is too crowded.

## What NOT to do

- No drop shadows, no glows, no gradients
- No bright red/green (use `--pos` / `--neg`)
- No rounded corners > 4px (most things are 0px or 2px)
- No 3D, no perspective, no pie charts past 4 slices
- No legends at the top — put labels at the end of lines, or inline
- No more than 5 categorical colors
- No emojis, no icons unless functional (e.g. arrow direction)
- No background fills on bars/lines beyond functional bands

When in doubt: **less.** The buy-side reader respects restraint.
