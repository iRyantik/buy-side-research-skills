---
name: research-viz
description: Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Research Viz

Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

## Positioning

`research-viz` is a **supporting visualization skill**, not a primary research-flow skill. It serves the visualization post-processing of research artifacts produced by `stock-quickread`, `mechanism-insight`, `peer-deep-dive`, `alpha-thesis`, `research-journal`, and others — making existing research easier for PM / IC to read quickly.

It can turn:

- A peer table in a research write-up into a scatter chart
- A mechanism / value-chain explanation into a structure diagram
- Valuation / sensitivity results into a band / heatmap / SOTP
- Price / event / consensus / revisions results into HTML charts more suitable for memos

It **does not replace** the primary research write-up, nor should it invent a complete thesis on its own without a baseline research artifact.

## Chart Types

Supports the following 18 chart categories; static HTML by default, interactive version when the user explicitly requests it:

| # | Chart | Reference file | Common trigger |
|---|---|---|---|
| 1 | Global operations / footprint map | `references/global-map.md` | "Draw factory/business distribution map" |
| 2 | Valuation band | `references/valuation-band.md` | "Build PE / EV-EBITDA band" |
| 3 | Waterfall / bridge | `references/waterfall-bridge.md` | "Build FCF / EBITDA / YoY bridge" |
| 4 | Sensitivity heatmap | `references/sensitivity-heatmap.md` | "Build DCF sensitivity" |
| 5 | SOTP stack | `references/sotp-stack.md` | "Build sum-of-the-parts chart" |
| 6 | Multi-panel cycle | `references/cycle-multipanel.md` | "Multiple or fundamentals" |
| 7 | Catalyst timeline | `references/catalyst-timeline.md` | "Build 12-month catalyst roadmap" |
| 8 | Price + events overlay | `references/price-events-overlay.md` | "Overlay stock price with events" |
| 9 | Peer scatter | `references/peer-scatter.md` | "Build growth vs margin / valuation scatter" |
| 10 | Business structure / value chain | `references/business-structure.md` | "Draw value chain / segment structure" |
| 11 | Sankey | `references/sankey.md` | "Build flow / revenue source diagram" |
| 12 | Correlation matrix | `references/correlation-matrix.md` | "Build correlation heatmap" |
| 13 | Beat/miss heatmap | `references/beat-miss-heatmap.md` | "Build earnings beat / miss heatmap" |
| 14 | Debt maturity + capital stack | `references/debt-maturity.md` | "Build debt ladder / capital stack" |
| 15 | Margin walk | `references/margin-walk.md` | "Build margin walk" |
| 16 | Consensus revisions | `references/consensus-revisions.md` | "Build estimate revision chart" |
| 17 | Concentration / Pareto | `references/concentration-pareto.md` | "Build concentration / pareto chart" |
| 18 | Cohort retention | `references/cohort-retention.md` | "Build cohort retention / NRR chart" |

Regardless of chart type, always load `references/design-tokens.md` first; for interactive versions, additionally load `references/interaction-patterns.md`.

## When to Use

When the user already has a research artifact or a clearly defined research question, and wants to:

- "Turn this research write-up into charts"
- "Add a system diagram / capability map to the mechanism-insight output"
- "Turn the peer comparison into a memo-ready chart"
- "Visualize DCF / SOTP / sensitivity results"
- "Plot price action, catalysts, valuation bands, or consensus changes"

Do not use for:

- Replacing the primary research write-up: the main research document comes first, charts come after
- Source-free, made-up "pretty charts"
- Pure brand / marketing / landing page visuals
- Real-time dashboards, streaming monitors, trading terminals

## Save Rules

This skill's topic-side save contract is fixed as follows:

- Must be bound to a **baseline markdown research artifact**
- Default: reuse the same stem, only changing the extension from `.md` to `.html`

For example:

```text
2026-05-25-mechanism-insight-korea-vs-global-system-dossier.md
2026-05-25-mechanism-insight-korea-vs-global-system-dossier.html
```

If the same baseline research needs multiple different charts, append a minimal qualifier after the stem, then keep `.html`:

```text
2026-05-25-mechanism-insight-korea-vs-global-system-dossier-peer-scatter.html
2026-05-25-mechanism-insight-korea-vs-global-system-dossier-global-map.html
2026-05-25-mechanism-insight-korea-vs-global-system-dossier-global-map-interactive.html
```

By default, do not invent parallel names such as `research-viz.html` or `YYYY-MM-DD-research-viz.html`.

If the user has not provided a clear baseline research artifact, first resolve or require a baseline markdown main document, then save the HTML.

## Output Contract

- Artifacts are **self-contained HTML**
- Default: start from `assets/template.html`; for interactive: use `assets/template-interactive.html`
- Charts must have:
  - Title
  - Subtitle (units / time period / ticker / accounting basis)
  - Source line
- Use tabular numerals throughout; clearly state units: `%`, `x`, `bps`, currency codes, etc.
- Missing data: mark as `n/a` or explain at the chart footer
- If the chart depends on factual judgments from a research write-up within the topic, the chart footer source line and the adjacent markdown description must trace back to the same set of sources

## Workflow

1. Identify chart type: map the user request to one of the 18 categories.
2. Identify the baseline research artifact: prioritize the `.md` file specified by the user; otherwise pick a clear baseline from the most recent relevant main document in the current topic.
3. Collect data: prioritize reusing the baseline research write-up, topic `_cache/`, and existing source-backed tables; supplement with sources only when necessary.
4. Load `references/design-tokens.md` and the target chart reference; for interactive, additionally load `references/interaction-patterns.md`.
5. Start from the corresponding template — do not build from scratch.
6. Write the title, subtitle, source line, and necessary callouts.
7. Save as an `.html` topic artifact bound to the baseline stem.
8. In the conversation, provide only a brief description: what this chart shows, which research it serves, where it was saved.

## Anti-Pattern Self-Check

- No baseline research write-up, yet fabricating a complete thesis on its own
- Chart numbers or conclusions without sources
- Sacrificing buy-side readability for "aesthetics"
- Treating marketing pages, hero sections, gradient cards as research charts
- Directly outputting `research-viz.html` without binding to a research stem
- Delivering an HTML file without title / subtitle / source line
- Chart reaching conclusions before the text does, or even contradicting the baseline research write-up

## Runtime Resources

```text
skills/research-viz/
  SKILL.md
  skill.yaml
  assets/template.html
  assets/template-interactive.html
  references/design-tokens.md
  references/interaction-patterns.md
  references/*.md
  examples/*.html
```
