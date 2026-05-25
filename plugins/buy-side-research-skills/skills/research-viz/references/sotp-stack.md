# SOTP stack

Sum-of-the-parts valuation: each business segment valued separately, then summed to a target equity value (with adjustments for net debt, minorities, etc).

## When to use

User asks: "sum of the parts", "value the segments", "break out the divisions", "SOTP for X", "how should we think about the conglomerate discount". Use this when a company has 2+ distinct businesses with different growth/margin/multiple profiles.

## Required inputs

```js
const segments = [
  { name: "Cloud",         metric: "EBITDA", value: 4200, multiple: 22.0, method: "EV/EBITDA" },
  { name: "Advertising",   metric: "EBITDA", value: 6800, multiple: 14.0, method: "EV/EBITDA" },
  { name: "Hardware",      metric: "Revenue",value: 3500, multiple:  2.0, method: "EV/Sales"  },
  { name: "Other / Bets",  metric: "Book",   value:  900, multiple:  1.0, method: "Book"      },
];
const adjustments = [
  { name: "Net cash",      value:  +2400 },     // positive adds to equity
  { name: "Minorities",    value:  -350  },
  { name: "Pension deficit", value: -180 },
];
const sharesOut = 1250;   // millions, for per-share

// computed:
//   ev_per_segment = value * multiple
//   ev_total       = Σ ev_per_segment
//   equity         = ev_total + Σ adjustments
//   per_share      = equity / sharesOut
```

## Visual structure

Two-column layout for the memo column format (800×1100):
- **Left** (60%): horizontal stacked bar showing each segment's contribution to EV, with the bar segmented by business. Bar runs top-to-bottom or as one long horizontal stack. Adjustments shown as separate floating bars after.
- **Right** (40%): tabular breakdown — segment, metric, value, multiple, EV — totals at the bottom in bold.

For the slide format (1200×675), do the bar on top (horizontal stack), table below.

## Core template — horizontal stacked bar + adjustments + final equity

```js
// Build the data sequence: segments stacking up to total EV, then adjustments, then equity.
const segEVs = segments.map(s => ({ ...s, ev: s.value * s.multiple }));
const totalEV = d3.sum(segEVs, d => d.ev);
const equity = totalEV + d3.sum(adjustments, d => d.value);

const margin = { top: 32, right: 80, bottom: 80, left: 24 };
const width = 1088, height = 280;
const innerW = width - margin.left - margin.right;
const innerH = 60;   // bar height

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const xMax = Math.max(totalEV, equity) * 1.05;
const x = d3.scaleLinear()
  .domain([0, xMax]).range([0, innerW]);

const segColors = ["var(--cat-1)","var(--cat-2)","var(--cat-3)","var(--cat-4)","var(--cat-5)"];

// row 1: stacked EV by segment
let cum = 0;
segEVs.forEach((s, i) => {
  g.append("rect")
    .attr("x", x(cum)).attr("y", 20)
    .attr("width", x(s.ev) - x(0))
    .attr("height", innerH)
    .attr("fill", segColors[i % segColors.length])
    .attr("stroke", "#FFF").attr("stroke-width", 1);
  // inline label
  g.append("text")
    .attr("class", "data-label")
    .attr("x", x(cum) + (x(s.ev) - x(0)) / 2)
    .attr("y", 20 + innerH / 2 + 4)
    .attr("text-anchor", "middle")
    .attr("fill", "#FFF")
    .text(s.name);
  // ev value above
  g.append("text")
    .attr("class", "data-label")
    .attr("x", x(cum) + (x(s.ev) - x(0)) / 2)
    .attr("y", 14)
    .attr("text-anchor", "middle")
    .text(d3.format(",")(Math.round(s.ev)));
  cum += s.ev;
});

// "Total EV" label
g.append("text")
  .attr("class", "data-label")
  .attr("x", x(totalEV) + 8)
  .attr("y", 20 + innerH / 2 + 4)
  .attr("font-weight", 600)
  .text(`EV ${d3.format(",")(Math.round(totalEV))}`);

// row 2: adjustments (smaller bars) → equity
const row2 = 130;
let cumAdj = totalEV;
adjustments.forEach((a, i) => {
  const w = Math.abs(a.value);
  const x0 = a.value >= 0 ? cumAdj : cumAdj + a.value;
  g.append("rect")
    .attr("x", x(x0)).attr("y", row2)
    .attr("width", x(w) - x(0))
    .attr("height", 36)
    .attr("fill", a.value >= 0 ? "var(--pos)" : "var(--neg)")
    .attr("opacity", 0.7);
  g.append("text")
    .attr("class", "data-label")
    .attr("x", x(x0) + (x(w) - x(0)) / 2)
    .attr("y", row2 + 22)
    .attr("text-anchor", "middle")
    .attr("fill", "#FFF")
    .text(`${a.name} ${d3.format("+,")(a.value)}`);
  cumAdj += a.value;
});

// final equity marker
g.append("line")
  .attr("x1", x(equity)).attr("x2", x(equity))
  .attr("y1", 10).attr("y2", row2 + 50)
  .attr("stroke", "var(--highlight)").attr("stroke-width", 2);
g.append("text")
  .attr("class", "data-label")
  .attr("x", x(equity) + 6).attr("y", row2 + 50)
  .attr("fill", "var(--highlight)")
  .attr("font-weight", 600)
  .text(`Equity ${d3.format(",")(Math.round(equity))}  ($${(equity/sharesOut).toFixed(0)}/sh)`);

// scale axis at bottom
g.append("g")
  .attr("class", "axis axis-num")
  .attr("transform", `translate(0,${row2 + 70})`)
  .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format(",")));
```

Pair with a table below the chart (use the `.tabular` class from template.html).

## Variants

- **Vertical stack** (column format) — same idea rotated 90°. Better for memos.
- **Range bars per segment** — show low/base/high valuation for each segment instead of a single point. Use error bars or split each bar into 3 tones.
- **Implied per-share table only** — sometimes the table is enough, no chart needed. Don't force a chart if the data is small.

## Gotchas

- **EV vs equity**: be explicit. EV = sum of segment values; equity = EV + net cash − minorities − preferred − pensions, etc. Get the bridge right.
- **Use consistent multiples**: don't mix forward-year and trailing-year multiples across segments without flagging. State the methodology in the subtitle.
- **Per-share consistency**: use a diluted share count; specify treasury method or fully-diluted in the source line.
- **Don't double-count**: if a segment is consolidated at 70% ownership, don't claim 100% of its EV. Subtract minority interest correctly.
- **Watch the conglomerate discount**: optionally include "current market cap" as a small reference line on the equity bar so the implied upside/discount is visible.

---

## Interactive variant — sliders for live recomputation

The slider variant turns SOTP from a static "here's the math" into a live "what do you think" — the PM moves a slider, the equity per-share recomputes immediately. This is the highest-value interactive variant in the skill.

### When to use the slider version
- Live IC discussion: PM challenges your multiples, you adjust on the fly
- Sharing with a colleague who has different views — let them try their own assumptions
- Sensitivity exploration paired with the static memo version

### Controls layout

One slider per segment for the multiple. Optional sliders for the underlying metric (revenue, EBITDA) for full scenario mode. Plus a "Reset to base" button.

```html
<div class="controls">
  <div class="controls-section" style="flex-direction:column;align-items:stretch;width:100%;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 24px;">
      <!-- sliders inserted by JS -->
    </div>
  </div>
  <button class="btn" onclick="resetSOTP()">Reset to base</button>
</div>

<div id="chart"></div>

<table class="tabular" id="sotp-table">
  <thead>
    <tr><th>Segment</th><th>Metric</th><th style="text-align:right;">Value</th>
        <th style="text-align:right;">Multiple</th><th style="text-align:right;">EV</th></tr>
  </thead>
  <tbody></tbody>
</table>
```

### Core template — live SOTP

```js
// segments: [{name, metric, value, multiple, method, multRange:[min,max]}]
// adjustments: [{name, value}]
// sharesOut, marketCap (optional, for upside indicator)

// Keep base values for reset
const base = segments.map(s => ({ ...s }));
const state = segments.map(s => ({ ...s }));

// ── Build sliders ──────────────────────────────────────────────
const slidersGrid = document.querySelector(".controls-section > div");
state.forEach((s, i) => {
  const min = s.multRange ? s.multRange[0] : s.multiple * 0.5;
  const max = s.multRange ? s.multRange[1] : s.multiple * 1.5;
  const row = document.createElement("div");
  row.className = "slider-row";
  row.innerHTML = `
    <label>${s.name}</label>
    <input type="range" min="${min}" max="${max}" step="0.1" value="${s.multiple}" data-i="${i}">
    <span class="slider-value" id="mult-out-${i}">${s.multiple.toFixed(1)}x</span>
  `;
  slidersGrid.appendChild(row);
  row.querySelector("input").addEventListener("input", (evt) => {
    const v = parseFloat(evt.target.value);
    state[i].multiple = v;
    document.getElementById(`mult-out-${i}`).textContent = v.toFixed(1) + "x";
    redraw();
  });
});

// ── SVG setup (same as static) ─────────────────────────────────
const segColors = ["var(--cat-1)","var(--cat-2)","var(--cat-3)","var(--cat-4)","var(--cat-5)"];
const margin = { top: 32, right: 80, bottom: 60, left: 24 };
const width = 1104, height = 280;
const innerW = width - margin.left - margin.right;
const barH = 60;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Layers that we re-populate on every redraw
const segG  = g.append("g").attr("class", "segments");
const adjG  = g.append("g").attr("class", "adjustments");
const eqG   = g.append("g").attr("class", "equity");
const axisG = g.append("g").attr("class", "axis axis-num");

const xScale = d3.scaleLinear().range([0, innerW]);

// ── Redraw function ───────────────────────────────────────────
function redraw() {
  const segEVs = state.map(s => ({ ...s, ev: s.value * s.multiple }));
  const totalEV = d3.sum(segEVs, d => d.ev);
  const equity  = totalEV + d3.sum(adjustments, d => d.value);
  const xMax = Math.max(totalEV, equity) * 1.05;
  xScale.domain([0, xMax]);

  // ── Segments (row 1) ─────────────────────────────────────────
  let cum = 0;
  const segs = segEVs.map((s, i) => ({ ...s, x0: cum, ev: s.ev, idx: i, _: (cum += s.ev) }));

  const segSel = segG.selectAll(".seg").data(segs, d => d.name);
  const segEnter = segSel.enter().append("g").attr("class", "seg");
  segEnter.append("rect");
  segEnter.append("text").attr("class","seg-name");
  segEnter.append("text").attr("class","seg-val");
  segSel.exit().remove();

  segG.selectAll(".seg rect")
    .data(segs, d => d.name)
    .attr("x", d => xScale(d.x0))
    .attr("y", 20)
    .attr("width", d => Math.max(0, xScale(d.ev) - xScale(0)))
    .attr("height", barH)
    .attr("fill", (d, i) => segColors[i % segColors.length])
    .attr("stroke", "#FFF").attr("stroke-width", 1)
    .style("cursor", "pointer")
    .on("mouseover", function(evt, d) {
      showTip(
        `<b>${d.name}</b><br>
         ${d.metric}: <span class="num">${d3.format(",")(d.value)}</span><br>
         Multiple: <span class="num">${d.multiple.toFixed(1)}x</span><br>
         EV: <span class="num">${d3.format(",")(Math.round(d.ev))}</span>`,
        evt
      );
    })
    .on("mouseout", hideTip);

  segG.selectAll(".seg-name")
    .data(segs, d => d.name)
    .attr("x", d => xScale(d.x0) + (xScale(d.ev) - xScale(0)) / 2)
    .attr("y", 20 + barH/2 + 4)
    .attr("text-anchor", "middle")
    .attr("fill", "#FFF")
    .attr("font-family", "var(--font-sans)")
    .attr("font-size", 12)
    .attr("font-weight", 500)
    .text(d => d.name);

  segG.selectAll(".seg-val")
    .data(segs, d => d.name)
    .attr("x", d => xScale(d.x0) + (xScale(d.ev) - xScale(0)) / 2)
    .attr("y", 14)
    .attr("text-anchor", "middle")
    .attr("class", "data-label seg-val")
    .text(d => d3.format(",")(Math.round(d.ev)));

  // ── Total EV label ───────────────────────────────────────────
  segG.selectAll(".ev-total").data([totalEV]).join("text")
    .attr("class", "data-label ev-total")
    .attr("x", xScale(totalEV) + 8)
    .attr("y", 20 + barH/2 + 4)
    .attr("font-weight", 600)
    .text(d => `EV ${d3.format(",")(Math.round(d))}`);

  // ── Adjustments (row 2) ──────────────────────────────────────
  const row2 = 130;
  let cumAdj = totalEV;
  const adjData = adjustments.map(a => {
    const x0 = a.value >= 0 ? cumAdj : cumAdj + a.value;
    const obj = { ...a, x0, w: Math.abs(a.value) };
    cumAdj += a.value;
    return obj;
  });

  const adjSel = adjG.selectAll(".adj").data(adjData, d => d.name);
  const adjEnter = adjSel.enter().append("g").attr("class", "adj");
  adjEnter.append("rect");
  adjEnter.append("text");
  adjSel.exit().remove();

  adjG.selectAll(".adj rect")
    .data(adjData, d => d.name)
    .attr("x", d => xScale(d.x0))
    .attr("y", row2)
    .attr("width", d => xScale(d.w) - xScale(0))
    .attr("height", 36)
    .attr("fill", d => d.value >= 0 ? "var(--pos)" : "var(--neg)")
    .attr("opacity", 0.7);

  adjG.selectAll(".adj text")
    .data(adjData, d => d.name)
    .attr("x", d => xScale(d.x0) + (xScale(d.w) - xScale(0))/2)
    .attr("y", row2 + 22)
    .attr("text-anchor", "middle")
    .attr("fill", "#FFF")
    .attr("class", "data-label")
    .attr("font-size", 11)
    .text(d => `${d.name} ${d3.format("+,")(d.value)}`);

  // ── Equity line + label ──────────────────────────────────────
  eqG.selectAll(".eq-line").data([equity]).join("line")
    .attr("class", "eq-line")
    .attr("x1", d => xScale(d)).attr("x2", d => xScale(d))
    .attr("y1", 10).attr("y2", row2 + 50)
    .attr("stroke", "var(--highlight)").attr("stroke-width", 2);

  eqG.selectAll(".eq-label").data([equity]).join("text")
    .attr("class", "data-label eq-label")
    .attr("x", d => xScale(d) + 6).attr("y", row2 + 50)
    .attr("fill", "var(--highlight)")
    .attr("font-weight", 600)
    .text(d => `Equity ${d3.format(",")(Math.round(d))}  ($${(d/sharesOut).toFixed(0)}/sh)`);

  // Optional: market cap reference (shows upside/downside live)
  if (typeof marketCap !== "undefined") {
    const upside = (equity / marketCap - 1);
    eqG.selectAll(".upside").data([upside]).join("text")
      .attr("class", "data-label upside")
      .attr("x", d => xScale(equity) + 6).attr("y", row2 + 66)
      .attr("fill", upside >= 0 ? "var(--pos)" : "var(--neg)")
      .text(d => `vs $${d3.format(",")(Math.round(marketCap))} mkt cap  ${d3.format("+.1%")(d)}`);
  }

  // ── X axis ───────────────────────────────────────────────────
  axisG.attr("transform", `translate(0,${row2 + 70})`)
    .call(d3.axisBottom(xScale).ticks(6).tickFormat(d3.format(",")));

  // ── Update the table below ───────────────────────────────────
  const tbody = d3.select("#sotp-table tbody");
  const rows = tbody.selectAll("tr.seg-row").data(segEVs, d => d.name);
  const rowsEnter = rows.enter().append("tr").attr("class", "seg-row");
  rowsEnter.append("td");
  rowsEnter.append("td");
  rowsEnter.append("td").attr("class","num");
  rowsEnter.append("td").attr("class","num");
  rowsEnter.append("td").attr("class","num");
  rows.exit().remove();

  tbody.selectAll("tr.seg-row td:nth-child(1)").data(segEVs, d=>d.name).text(d => d.name);
  tbody.selectAll("tr.seg-row td:nth-child(2)").data(segEVs, d=>d.name).text(d => d.metric);
  tbody.selectAll("tr.seg-row td:nth-child(3)").data(segEVs, d=>d.name).text(d => d3.format(",")(d.value));
  tbody.selectAll("tr.seg-row td:nth-child(4)").data(segEVs, d=>d.name).text(d => d.multiple.toFixed(1) + "x");
  tbody.selectAll("tr.seg-row td:nth-child(5)").data(segEVs, d=>d.name).text(d => d3.format(",")(Math.round(d.ev)));
}

// Reset to base values
function resetSOTP() {
  state.forEach((s, i) => {
    s.multiple = base[i].multiple;
    const slider = document.querySelector(`[data-i="${i}"]`);
    if (slider) slider.value = s.multiple;
    document.getElementById(`mult-out-${i}`).textContent = s.multiple.toFixed(1) + "x";
  });
  redraw();
}

// Initial draw
redraw();
```

### Optional: also slider the underlying metric

For full scenario mode, add a second slider per segment for the metric (revenue, EBITDA):

```js
// Add to each segment row:
//   <input type="range" min="${s.value * 0.7}" max="${s.value * 1.5}" step="..." value="${s.value}" data-metric-i="${i}">
// On input: state[i].value = parseFloat(v); redraw();
```

This makes the SOTP a true scenario tool: "what if Cloud grows EBITDA from $4.2bn to $5.0bn AND deserves 26x instead of 22x"?

### Interactive gotchas

- **D3 enter/update/exit pattern** is essential here — recreating elements on every slider tick causes flicker. Use `.data(d, keyFn).join()` or selections with data binding.
- **`step` on the slider** should match the precision you want to display. For multiples, 0.1 is fine; for $bn metrics, 0.1 might be too coarse — use 0.05 or finer.
- **Show the delta vs base case** somewhere on the chart — the eye should know whether the current state is "near base" or "very aggressive".
- **Don't auto-rescale the x-axis** on every slider move — readers lose their reference. Set `xMax` based on `base` + 30% buffer, keep it constant. Re-scale only on explicit reset.
- **Display the implied upside vs current market cap** as a live label — this is the number the PM cares about.
- **Save the slider state** in URL hash if you want shareable scenarios: `#mults=22.0,14.0,2.0,1.0` — parse on load.
