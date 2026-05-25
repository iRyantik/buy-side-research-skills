# Valuation band

PE / EV-EBITDA / EV-Sales / P/B multiple over time, with min/max/avg envelope and the current point highlighted. The single most common buy-side chart.

## When to use

User asks for: "PE band", "trading range", "where does it trade vs history", "multiple over time", "rerated", "EV/EBITDA history". Use the band variant (median + ±1σ envelope) when the question is "is it cheap vs history". Use a plain line when the question is "how has the multiple moved".

## Required inputs

A series of (date, multiple) pairs, weekly or monthly:
```js
[
  { date: "2019-01-31", multiple: 14.2 },
  { date: "2019-02-28", multiple: 13.8 },
  ...
  { date: "2026-03-31", multiple: 22.1 },  // most recent — will be focal
]
```

Plus optional reference lines: 5-year average, 10-year average, all-time high/low, prior cycle peak/trough.

If user has Bloomberg/Koyfin output, they can paste it in. If they want you to estimate, ask them to provide — don't fabricate multiples.

## Visual structure

- X axis: time (~5–10 years)
- Y axis: multiple (x)
- Filled band: ±1σ around mean, in `--accent-ghost`
- Line: actual multiple over time, in `--accent`
- Horizontal dotted line: long-run mean
- Focal dot: current point, in `--highlight`, labeled with current multiple and percentile

## Core template

```js
// data: [{date: Date, multiple: number}, ...]
const margin = { top: 24, right: 80, bottom: 32, left: 44 };
const width = 1088, height = 420;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime()
  .domain(d3.extent(data, d => d.date))
  .range([0, innerW]);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.multiple) * 1.1]).nice()
  .range([innerH, 0]);

// stats
const mean = d3.mean(data, d => d.multiple);
const std  = d3.deviation(data, d => d.multiple);
const last = data[data.length - 1];
const pct  = data.filter(d => d.multiple < last.multiple).length / data.length;

// band: ±1σ
g.append("rect")
  .attr("x", 0).attr("y", y(mean + std))
  .attr("width", innerW)
  .attr("height", y(mean - std) - y(mean + std))
  .attr("fill", "var(--accent-ghost)")
  .attr("opacity", 0.5);

// dotted grid (horizontal only)
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// mean line
g.append("line")
  .attr("x1", 0).attr("x2", innerW)
  .attr("y1", y(mean)).attr("y2", y(mean))
  .attr("stroke", "var(--ink-2)")
  .attr("stroke-width", 1)
  .attr("stroke-dasharray", "2 3");

// the multiple line
const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.multiple))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", "var(--accent)")
  .attr("stroke-width", 1.5)
  .attr("d", line);

// focal dot — current value
g.append("circle")
  .attr("class", "focal")
  .attr("cx", x(last.date))
  .attr("cy", y(last.multiple))
  .attr("r", 5);

// focal label
g.append("text")
  .attr("class", "data-label")
  .attr("x", x(last.date) + 8)
  .attr("y", y(last.multiple) + 4)
  .attr("fill", "var(--highlight)")
  .text(`${last.multiple.toFixed(1)}x  (${(pct*100).toFixed(0)}th pct)`);

// mean label, right of chart
g.append("text")
  .attr("class", "data-label")
  .attr("x", innerW + 6)
  .attr("y", y(mean) + 4)
  .attr("fill", "var(--ink-2)")
  .text(`${mean.toFixed(1)}x  avg`);

// axes
g.append("g")
  .attr("class", "axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
g.append("g")
  .attr("class", "axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d => d + "x"));
```

## Variants

- **Multiple bands stacked**: Show PE band on top of EV/EBITDA band in a 2-row panel — see `cycle-multipanel.md` for the layout.
- **Forward vs trailing**: Plot both as two lines (trailing dashed, forward solid). Use `--accent` and `--accent-soft`.
- **Cycle-adjusted**: Add a second horizontal band for "prior cycle peak/trough" labeled explicitly.
- **Percentile shading**: Instead of ±1σ, use 25th–75th percentile band. Choose based on whether the data is roughly normal (use σ) or skewed (use percentiles).

## Gotchas

- **Always state the multiple type in the subtitle**: "Trailing 12M EV/EBITDA, weekly" — never just "EV/EBITDA".
- **Don't include negative-earnings periods** in PE bands — they distort the average. Filter them out and note "ex. FY20 (loss)" in the source line.
- **Anchor the y-axis at zero** for PE, EV/EBITDA, EV/Sales. Don't auto-truncate — readers calibrate against zero.
- **The focal dot's percentile is the message**. Always label it ("82nd percentile") so the reader can react immediately.

---

## Interactive variant — crosshair + brush-to-zoom + live percentile

Hover anywhere on the chart to see the multiple, date, and percentile at that point. Drag horizontally to zoom into a date range (band statistics recompute). Double-click to reset.

### Controls (minimal)

```html
<div class="controls">
  <span class="controls-label">Drag to zoom · Double-click to reset</span>
  <button class="btn" onclick="resetZoom()">Reset</button>
</div>
<div id="chart"></div>
<p id="readout" class="callout" style="margin-top:8px;font-style:italic;color:var(--ink-2);"></p>
```

### Core template

```js
// data: [{date: Date, multiple: number}, ...]
let view = { x0: d3.min(data, d=>d.date), x1: d3.max(data, d=>d.date) };

const margin = { top: 24, right: 80, bottom: 32, left: 44 };
const width = 1088, height = 420;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime().range([0, innerW]);
const y = d3.scaleLinear().range([innerH, 0]);

const bandG = g.append("rect")
  .attr("fill", "var(--accent-ghost)").attr("opacity", 0.5);
const meanLine = g.append("line")
  .attr("stroke", "var(--ink-2)").attr("stroke-width", 1)
  .attr("stroke-dasharray", "2 3");
const gridG = g.append("g").attr("class", "grid");
const linePath = g.append("path")
  .attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 1.5);
const focalDot = g.append("circle").attr("class", "focal").attr("r", 5);
const focalLabel = g.append("text").attr("class", "data-label").attr("fill", "var(--highlight)");
const meanLabel = g.append("text").attr("class", "data-label").attr("fill", "var(--ink-2)");
const xAxisG = g.append("g").attr("class", "axis axis-num").attr("transform", `translate(0,${innerH})`);
const yAxisG = g.append("g").attr("class", "axis axis-num");

// Crosshair group
const ch = g.append("g").style("display", "none").style("pointer-events","none");
ch.append("line").attr("class","crosshair").attr("y1",0).attr("y2",innerH);
const chDot = ch.append("circle").attr("r",4)
  .attr("fill","var(--paper)").attr("stroke","var(--highlight)").attr("stroke-width",1.5);

const readout = document.getElementById("readout");

function redraw() {
  const visible = data.filter(d => d.date >= view.x0 && d.date <= view.x1);
  const mean = d3.mean(visible, d=>d.multiple);
  const std  = d3.deviation(visible, d=>d.multiple);
  const last = visible[visible.length-1];
  const pct  = visible.filter(d=>d.multiple < last.multiple).length / visible.length;

  x.domain([view.x0, view.x1]);
  y.domain([0, d3.max(visible, d=>d.multiple) * 1.1]).nice();

  bandG.attr("x", 0).attr("y", y(mean+std))
       .attr("width", innerW).attr("height", y(mean-std) - y(mean+std));
  meanLine.attr("x1", 0).attr("x2", innerW).attr("y1", y(mean)).attr("y2", y(mean));

  gridG.call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

  const line = d3.line()
    .x(d => x(d.date)).y(d => y(d.multiple))
    .curve(d3.curveMonotoneX);
  linePath.datum(visible).attr("d", line);

  focalDot.attr("cx", x(last.date)).attr("cy", y(last.multiple));
  focalLabel.attr("x", x(last.date) + 8).attr("y", y(last.multiple) + 4)
    .text(`${last.multiple.toFixed(1)}x  (${(pct*100).toFixed(0)}th pct)`);
  meanLabel.attr("x", innerW + 6).attr("y", y(mean) + 4)
    .text(`${mean.toFixed(1)}x  avg`);

  xAxisG.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
  yAxisG.call(d3.axisLeft(y).tickFormat(d => d + "x"));
}
redraw();

// Brush + crosshair overlay (transparent rect on top)
const bisect = d3.bisector(d=>d.date).left;
const brush = d3.brushX()
  .extent([[0,0],[innerW,innerH]])
  .on("end", ({selection}) => {
    if (selection) {
      view = { x0: x.invert(selection[0]), x1: x.invert(selection[1]) };
      brushG.call(brush.move, null);
      redraw();
    }
  });

const brushG = g.append("g").attr("class","brush").call(brush);

brushG.selectAll(".overlay")
  .on("mouseenter", () => ch.style("display", null))
  .on("mouseleave", () => { ch.style("display", "none"); hideTip(); readout.textContent = ""; })
  .on("mousemove.crosshair", function(evt) {
    const visible = data.filter(d => d.date >= view.x0 && d.date <= view.x1);
    const mx = d3.pointer(evt, this)[0];
    const date = x.invert(mx);
    const i = Math.min(visible.length-1, Math.max(0, bisect(visible, date)));
    const d = visible[i];
    const sx = x(d.date), sy = y(d.multiple);
    ch.select("line").attr("x1", sx).attr("x2", sx);
    chDot.attr("cx", sx).attr("cy", sy);
    const mean = d3.mean(visible, e=>e.multiple);
    const pct = visible.filter(e=>e.multiple < d.multiple).length / visible.length;
    readout.innerHTML = `${d3.timeFormat("%b %Y")(d.date)} &middot; <span style="font-family:var(--font-mono);">${d.multiple.toFixed(2)}x</span> &middot; ${(pct*100).toFixed(0)}th percentile of visible range &middot; <span style="color:var(--ink-3);">${(d.multiple/mean*100-100).toFixed(0)}% vs avg</span>`;
  })
  .on("dblclick.reset", () => resetZoom());

function resetZoom() {
  view = { x0: d3.min(data, d=>d.date), x1: d3.max(data, d=>d.date) };
  redraw();
}
```

### Interactive gotchas

- **Band statistics recompute on zoom** — this is the point: zooming into 2021–2023 shows the band for that period, not the whole-series band. The subtitle should say "± 1σ of visible range".
- **Crosshair vs brush selection**: brush rectangle visually overrides the crosshair while dragging. That's correct — the user is selecting, not reading.
- **Don't zoom y on brush** — only the x range changes. Y still anchors at 0 for valuation bands; the user's mental model is "show this period in context", not "zoom to fit".
- **Save view in URL hash** `#from=2021-01&to=2023-12` for shareable date ranges.
