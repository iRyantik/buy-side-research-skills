# Beat / miss heatmap

A grid of quarters × line items showing how much each metric beat or missed consensus. Tells you "this company beats revenue consistently but misses on margin", or "the surprise pattern flipped sign 4 quarters ago".

## When to use

User asks: "earnings beat/miss", "quarterly surprise", "consensus delta heatmap", "track of beats", "where do they always disappoint". Rows = metrics (revenue, EBITDA, EPS, GMs, capex...), columns = quarters.

## Required inputs

```js
const metrics = ["Revenue", "EBITDA", "EPS", "Gross margin", "FCF"];
const quarters = ["1Q24","2Q24","3Q24","4Q24","1Q25","2Q25","3Q25","4Q25"];
// matrix[metricIdx][qIdx] = surprise vs consensus (e.g. +0.024 = beat by 2.4%)
const matrix = [
  [+0.024, +0.018, +0.031, -0.005, +0.041, +0.052, +0.038, +0.026],   // Revenue
  [+0.018, +0.025, +0.012, -0.018, +0.022, +0.041, +0.028, +0.014],   // EBITDA
  [+0.082, +0.061, +0.045, -0.024, +0.073, +0.105, +0.088, +0.052],   // EPS
  [-0.012, -0.015, -0.018, -0.024, -0.008, +0.005, -0.011, -0.014],   // GM
  [+0.054, -0.038, +0.071, -0.092, +0.043, +0.118, -0.011, +0.067],   // FCF
];
```

Values are **deltas vs consensus**, signed and scaled. Typically as a percentage of consensus.

## Visual structure

- Heatmap grid, rows = metrics, cols = quarters
- Diverging color: `--neg` (large miss) → `--paper-edge` (in-line) → `--pos` (large beat)
- Cell labels in mono tabular-nums, signed (`+2.4%`, `-1.2%`)
- Row labels left, column (quarter) labels top
- A summary column on the right showing batting average (% of quarters with a beat) per metric

## Core template

```js
const cellW = 76, cellH = 36;
const margin = { top: 60, right: 100, bottom: 32, left: 100 };
const width = margin.left + cellW * quarters.length + margin.right;
const height = margin.top + cellH * metrics.length + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const flat = matrix.flat();
const maxAbs = d3.max(flat.map(Math.abs));
const color = d3.scaleLinear()
  .domain([-maxAbs, 0, maxAbs])
  .range(["#8B2635", "#F4F3EE", "#2D5F3F"])
  .interpolate(d3.interpolateRgb);

// cells
matrix.forEach((row, mi) => {
  row.forEach((v, qi) => {
    g.append("rect")
      .attr("x", qi * cellW).attr("y", mi * cellH)
      .attr("width", cellW).attr("height", cellH)
      .attr("fill", color(v))
      .attr("stroke", "#FFF").attr("stroke-width", 1);

    g.append("text")
      .attr("class", "data-label")
      .attr("x", qi * cellW + cellW/2)
      .attr("y", mi * cellH + cellH/2 + 4)
      .attr("text-anchor", "middle")
      .attr("fill", Math.abs(v) > maxAbs * 0.5 ? "#FFF" : "var(--ink)")
      .text(d3.format("+.1%")(v));
  });
});

// row labels (metrics)
metrics.forEach((m, mi) => {
  g.append("text")
    .attr("x", -10).attr("y", mi * cellH + cellH/2 + 4)
    .attr("text-anchor", "end")
    .attr("class", "axis-label")
    .attr("font-weight", 600)
    .text(m);
});

// column labels (quarters)
quarters.forEach((q, qi) => {
  g.append("text")
    .attr("x", qi * cellW + cellW/2).attr("y", -10)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .attr("font-family", "var(--font-mono)")
    .text(q);
});

// batting average column (right)
metrics.forEach((m, mi) => {
  const beats = matrix[mi].filter(v => v > 0).length;
  const total = matrix[mi].length;
  const avg = d3.mean(matrix[mi]);

  g.append("text")
    .attr("x", quarters.length * cellW + 14)
    .attr("y", mi * cellH + cellH/2 + 4)
    .attr("class", "data-label")
    .text(`${beats}/${total}  avg ${d3.format("+.1%")(avg)}`);
});
g.append("text")
  .attr("x", quarters.length * cellW + 14)
  .attr("y", -10)
  .attr("class", "axis-label")
  .attr("font-size", 10)
  .attr("font-weight", 600)
  .attr("letter-spacing", "0.06em")
  .attr("text-transform", "uppercase")
  .text("Batting avg");
```

## Variants

- **Absolute amounts instead of %**: useful when comparing across metrics with very different scales (revenue in $bn vs margin in %). But percent surprise is more comparable across periods.
- **Add a "guidance" column**: show whether guidance was raised/lowered alongside the surprise. Two-color stack within each quarter cell.
- **Stack vs prior trend**: include 4Q rolling average surprise in a separate column to show whether the company is trending toward beats or misses.

## Gotchas

- **Define "consensus"** in source line: street median? Bloomberg? FactSet? IBES? Different sources, different numbers.
- **Avoid "guidance beat" vs "consensus beat" confusion**. Be explicit.
- **Use percent surprises, not absolute**, when comparing across metrics — keeps the color scale meaningful.
- **Don't include too many metrics**. 4–6 is the sweet spot. Past that, the chart becomes a wall of numbers.
- **Watch unit consistency** — GAAP vs non-GAAP, organic vs reported, FX-neutral vs reported. State which you used.

---

## Interactive variant — hover detail + display mode toggle (% vs $)

Hover any cell for surprise %, absolute beat/miss in $, consensus value, and actual reported value. Toggle the cell label between surprise % and absolute dollar surprise.

### Required input (richer cells)

```js
const matrix = [
  [   // Revenue row
    { surprise: +0.024, consensus: 24500, actual: 25088 },
    { surprise: +0.018, consensus: 25100, actual: 25552 },
    // ...
  ],
  // ... one row per metric
];
```

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Cell labels</span>
    <div class="pills" id="display-pills">
      <span class="pill active" data-disp="pct">Surprise %</span>
      <span class="pill" data-disp="abs">Absolute $</span>
    </div>
  </div>
</div>
<div id="chart"></div>
```

### Core template

```js
let disp = "pct";

const cellW = 80, cellH = 36;
const margin = { top: 60, right: 130, bottom: 32, left: 100 };
const width = margin.left + cellW * quarters.length + margin.right;
const height = margin.top + cellH * metrics.length + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const flat = matrix.flat();
const surprises = flat.map(c => c.surprise);
const maxAbs = d3.max(surprises.map(Math.abs));
const color = d3.scaleLinear()
  .domain([-maxAbs, 0, maxAbs])
  .range(["#8B2635", "#F4F3EE", "#2D5F3F"])
  .interpolate(d3.interpolateRgb);

matrix.forEach((row, mi) => {
  row.forEach((cell, qi) => {
    const cellG = g.append("g").attr("transform", `translate(${qi*cellW},${mi*cellH})`);
    cellG.append("rect")
      .attr("class", "cell-rect")
      .attr("width", cellW).attr("height", cellH)
      .attr("fill", color(cell.surprise))
      .attr("stroke","#FFF").attr("stroke-width", 1)
      .style("cursor","pointer")
      .on("mouseover", function(evt) {
        const delta = cell.actual - cell.consensus;
        showTip(
          `<b>${metrics[mi]}</b> &middot; ${quarters[qi]}<br>
           Consensus: <span class="num">${d3.format(",")(cell.consensus)}</span><br>
           Actual: <span class="num">${d3.format(",")(cell.actual)}</span><br>
           Surprise: <span class="num" style="color:${cell.surprise >= 0 ? 'var(--pos-soft)' : 'var(--neg-soft)'};">${d3.format("+,")(delta)}</span>
           &nbsp;<span style="color:var(--neutral);">(${d3.format("+.1%")(cell.surprise)})</span>`,
          evt);
      })
      .on("mouseout", hideTip);

    cellG.append("text")
      .attr("class","cell-label data-label")
      .attr("x", cellW/2).attr("y", cellH/2 + 4)
      .attr("text-anchor","middle")
      .attr("fill", Math.abs(cell.surprise) > maxAbs * 0.5 ? "#FFF" : "var(--ink)");
  });
});

// Row labels
metrics.forEach((m, mi) => {
  g.append("text").attr("class","axis-label")
    .attr("x", -10).attr("y", mi*cellH + cellH/2 + 4)
    .attr("text-anchor","end").attr("font-weight", 600)
    .text(m);
});

// Column labels
quarters.forEach((q, qi) => {
  g.append("text").attr("class","axis-label")
    .attr("x", qi*cellW + cellW/2).attr("y", -10)
    .attr("text-anchor","middle")
    .attr("font-family","var(--font-mono)")
    .text(q);
});

// Batting average column
metrics.forEach((m, mi) => {
  const beats = matrix[mi].filter(c => c.surprise > 0).length;
  const total = matrix[mi].length;
  const avg = d3.mean(matrix[mi], c => c.surprise);
  g.append("text").attr("class","data-label")
    .attr("x", quarters.length * cellW + 14)
    .attr("y", mi*cellH + cellH/2 + 4)
    .text(`${beats}/${total}  avg ${d3.format("+.1%")(avg)}`);
});
g.append("text")
  .attr("x", quarters.length * cellW + 14).attr("y", -10)
  .attr("class","axis-label").attr("font-size",10)
  .attr("font-weight",600).attr("letter-spacing","0.06em")
  .attr("text-transform","uppercase").text("Batting avg");

function updateLabels() {
  g.selectAll(".cell-label").each(function(d, idx) {
    // Recompute cell from position
    const node = this;
    const parent = node.parentNode;
    const trans = parent.getAttribute("transform").match(/translate\(([^,]+),([^)]+)\)/);
    const qi = Math.round(+trans[1] / cellW);
    const mi = Math.round(+trans[2] / cellH);
    const cell = matrix[mi][qi];
    const text = disp === "pct"
      ? d3.format("+.1%")(cell.surprise)
      : d3.format("+,")(cell.actual - cell.consensus);
    d3.select(this).text(text);
  });
}
updateLabels();

document.querySelectorAll("#display-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#display-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    disp = p.dataset.disp;
    updateLabels();
  });
});
```

### Interactive gotchas

- **Tooltip shows all three numbers** (consensus, actual, surprise) so the user can verify the math at a glance.
- **Color stays driven by surprise %** in both display modes — the color encodes signal, label encodes magnitude. Don't switch color by absolute $.
- **Absolute $ display works best for revenue, EBITDA, FCF** (large numbers). For EPS, "+0.07" is fine. For margins, % is the right basis — don't show "0.5pp" mixed with "+45m".
