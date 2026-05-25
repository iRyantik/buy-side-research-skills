# Margin walk

Multi-line chart of gross margin, operating margin, and net margin over time — shows operating leverage and where the squeeze (or expansion) is happening in the P&L.

## When to use

User asks: "margin trend", "gross to net", "operating leverage", "where is margin expanding", "is opex growing faster than revenue", "margin walk". Standard answer is 3 lines (GM / OM / NM); add a 4th if the user cares about EBITDA margin or contribution margin specifically.

## Required inputs

```js
const data = [
  { period: "FY2019", gross: 0.451, operating: 0.232, net: 0.171 },
  { period: "FY2020", gross: 0.439, operating: 0.218, net: 0.155 },
  { period: "FY2021", gross: 0.482, operating: 0.265, net: 0.198 },
  { period: "FY2022", gross: 0.471, operating: 0.241, net: 0.182 },
  { period: "FY2023", gross: 0.495, operating: 0.272, net: 0.203 },
  { period: "FY2024", gross: 0.512, operating: 0.295, net: 0.221 },
  { period: "FY2025E", gross: 0.521, operating: 0.308, net: 0.232 },   // E = estimate
];
```

Periods can be annual, quarterly, or quarterly-trailing-twelve-month (TTM). State which in the subtitle.

## Visual structure

- 3 lines, each in `--accent` with progressively lighter shade — gross darkest, net lightest. (Or use accent for the focal margin and `--neutral` for the others.)
- All lines share one y-axis (percent)
- Each line labeled at the right end with its name and current value
- Estimate periods after the dashed vertical line render in a lighter shade

## Core template

```js
const margin = { top: 32, right: 100, bottom: 36, left: 48 };
const width = 1088, height = 440;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scalePoint()
  .domain(data.map(d => d.period))
  .range([0, innerW]).padding(0.5);

const allValues = data.flatMap(d => [d.gross, d.operating, d.net]);
const y = d3.scaleLinear()
  .domain([0, d3.max(allValues) * 1.1]).nice()
  .range([innerH, 0]);

// grid
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// estimate region (vertical dashed line + lighter shading)
const firstEstIdx = data.findIndex(d => d.period.endsWith("E"));
if (firstEstIdx > 0) {
  const xE = x(data[firstEstIdx].period) - (x(data[1].period) - x(data[0].period)) / 2;
  g.append("line")
    .attr("x1", xE).attr("x2", xE)
    .attr("y1", 0).attr("y2", innerH)
    .attr("stroke", "var(--ink-3)")
    .attr("stroke-dasharray", "3 4");
  g.append("text")
    .attr("x", xE + 6).attr("y", 12)
    .attr("class", "callout")
    .text("Consensus →");
}

const series = [
  { key: "gross",     label: "Gross",     color: "var(--accent)",       width: 2 },
  { key: "operating", label: "Operating", color: "var(--accent-soft)",  width: 1.8 },
  { key: "net",       label: "Net",       color: "var(--neutral)",      width: 1.5 },
];

series.forEach(s => {
  const line = d3.line()
    .x(d => x(d.period))
    .y(d => y(d[s.key]))
    .curve(d3.curveMonotoneX);
  g.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", s.color)
    .attr("stroke-width", s.width)
    .attr("d", line);

  // dots
  g.selectAll(`.dot-${s.key}`)
    .data(data).join("circle")
      .attr("cx", d => x(d.period))
      .attr("cy", d => y(d[s.key]))
      .attr("r", 3)
      .attr("fill", s.color);

  // end label
  const last = data[data.length - 1];
  g.append("text")
    .attr("x", innerW + 6).attr("y", y(last[s.key]) + 4)
    .attr("class", "data-label")
    .attr("fill", s.color)
    .attr("font-weight", 600)
    .text(`${s.label}  ${d3.format(".1%")(last[s.key])}`);
});

// axes
g.append("g").attr("class","axis")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x));
g.append("g").attr("class","axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d3.format(".0%")));
```

## Variants

- **Spread between GM and OM** as a separate small panel — useful when the question is "is opex bloating or shrinking as a % of revenue".
- **YoY margin change in bps** as a bar chart underneath the lines — same x-axis, shows direction of move year by year.
- **Peer overlay**: add peer-median GM/OM/NM as dotted lines in `--neutral` to show competitive position.
- **Contribution margin / unit-level margin** for SaaS — see `cohort-retention.md` for unit economics framing.

## Gotchas

- **GAAP vs non-GAAP**: pick one, state it. Don't mix.
- **Watch revenue restatements**: if the company changed revenue recognition (e.g. ASC 606), margins shift. Note breaks.
- **Don't fit smooth curves through quarterly data** that has obvious seasonality. Use `curveLinear` or quarterly markers, not `curveMonotoneX`.
- **Estimate region must be visually distinct** — readers should never confuse consensus from actual.
- **Anchor y-axis at zero** for margin lines. Truncating exaggerates moves.

---

## Interactive variant — crosshair + GAAP toggle + spread overlay

Hover for exact margins at a point. Toggle GAAP/non-GAAP. Optional: show G-O spread (gross minus operating, i.e. opex as % of revenue) as a fourth panel.

### Required input

Two data series (GAAP and non-GAAP) if the user wants the toggle:
```js
const data = {
  gaap: [
    { period: "FY2019", gross: 0.451, operating: 0.232, net: 0.171 },
    // ...
  ],
  nonGaap: [
    { period: "FY2019", gross: 0.485, operating: 0.262, net: 0.205 },
    // ...
  ],
};
```

If only one series, omit the toggle.

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Basis</span>
    <div class="pills" id="basis-pills">
      <span class="pill active" data-basis="gaap">GAAP</span>
      <span class="pill" data-basis="nonGaap">Non-GAAP</span>
    </div>
  </div>
  <div class="controls-section">
    <span class="controls-label">Show</span>
    <div class="pills" id="spread-pill">
      <span class="pill" data-spread="on">G–O spread</span>
    </div>
  </div>
</div>
<div id="chart"></div>
<p id="readout" style="font-family:var(--font-mono);font-size:11px;font-variant-numeric:tabular-nums;color:var(--ink-2);margin-top:6px;"></p>
```

### Core template

```js
let basis = "gaap";
let showSpread = false;

const series = [
  { key: "gross",     label: "Gross",     color: "var(--accent)",      width: 2   },
  { key: "operating", label: "Operating", color: "var(--accent-soft)", width: 1.8 },
  { key: "net",       label: "Net",       color: "var(--neutral)",     width: 1.5 },
];

const margin = { top: 32, right: 100, bottom: 36, left: 48 };
const width = 1088, height = 440;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scalePoint().range([0, innerW]).padding(0.5);
const y = d3.scaleLinear().range([innerH, 0]);

const gridG = g.append("g").attr("class","grid");
const linesG = g.append("g").attr("class","lines");
const xAxisG = g.append("g").attr("class","axis").attr("transform",`translate(0,${innerH})`);
const yAxisG = g.append("g").attr("class","axis axis-num");

const ch = g.append("g").style("display","none").style("pointer-events","none");
ch.append("line").attr("class","crosshair").attr("y1",0).attr("y2",innerH);

const readout = document.getElementById("readout");

function redraw() {
  const arr = data[basis];
  x.domain(arr.map(d => d.period));

  const allVals = arr.flatMap(d => [d.gross, d.operating, d.net,
                                    showSpread ? d.gross - d.operating : null].filter(v=>v!=null));
  y.domain([0, d3.max(allVals) * 1.1]).nice();

  gridG.call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));
  xAxisG.call(d3.axisBottom(x));
  yAxisG.call(d3.axisLeft(y).tickFormat(d3.format(".0%")));

  linesG.selectAll("*").remove();

  series.forEach(s => {
    const line = d3.line()
      .x(d => x(d.period)).y(d => y(d[s.key]))
      .curve(d3.curveMonotoneX);
    linesG.append("path").datum(arr)
      .attr("fill","none").attr("stroke", s.color).attr("stroke-width", s.width)
      .attr("d", line);
    linesG.selectAll(`.dot-${s.key}`).data(arr).join("circle")
      .attr("cx", d => x(d.period)).attr("cy", d => y(d[s.key]))
      .attr("r", 3).attr("fill", s.color)
      .style("cursor","pointer")
      .on("mouseover", (evt, d) => showTip(
        `<b>${s.label}</b> &middot; ${d.period}<br>
         <span class="num">${d3.format(".2%")(d[s.key])}</span>`, evt))
      .on("mouseout", hideTip);

    const last = arr[arr.length-1];
    linesG.append("text")
      .attr("x", innerW + 6).attr("y", y(last[s.key]) + 4)
      .attr("class","data-label")
      .attr("fill", s.color).attr("font-weight", 600)
      .text(`${s.label}  ${d3.format(".1%")(last[s.key])}`);
  });

  if (showSpread) {
    const spread = d3.line()
      .x(d => x(d.period)).y(d => y(d.gross - d.operating))
      .curve(d3.curveMonotoneX);
    linesG.append("path").datum(arr)
      .attr("fill","none").attr("stroke","var(--highlight)")
      .attr("stroke-width",1.2).attr("stroke-dasharray","3 3")
      .attr("d", spread);
    const last = arr[arr.length-1];
    linesG.append("text")
      .attr("x", innerW + 6).attr("y", y(last.gross - last.operating) + 4)
      .attr("class","data-label")
      .attr("fill","var(--highlight)")
      .text(`G–O ${d3.format(".1%")(last.gross - last.operating)}`);
  }
}
redraw();

// Crosshair overlay
const overlay = g.append("rect")
  .attr("width", innerW).attr("height", innerH).attr("fill","transparent")
  .style("cursor","crosshair");

const periodPositions = () => data[basis].map((d,i) => ({ d, sx: x(d.period) }));

overlay
  .on("mouseenter", () => ch.style("display", null))
  .on("mouseleave", () => { ch.style("display","none"); readout.textContent = ""; })
  .on("mousemove", function(evt) {
    const positions = periodPositions();
    const mx = d3.pointer(evt, this)[0];
    let best = positions[0], bestDiff = Infinity;
    positions.forEach(p => {
      const diff = Math.abs(p.sx - mx);
      if (diff < bestDiff) { bestDiff = diff; best = p; }
    });
    ch.select("line").attr("x1", best.sx).attr("x2", best.sx);
    readout.innerHTML = `${best.d.period} &nbsp;&middot;&nbsp; ` + series.map(s =>
      `<span style="color:${s.color};">${s.label} <b>${d3.format(".1%")(best.d[s.key])}</b></span>`
    ).join("&nbsp;&nbsp;");
  });

// Pill listeners
document.querySelectorAll("#basis-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#basis-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    basis = p.dataset.basis;
    redraw();
  });
});
document.querySelectorAll("#spread-pill .pill").forEach(p => {
  p.addEventListener("click", () => {
    p.classList.toggle("active");
    showSpread = p.classList.contains("active");
    redraw();
  });
});
```

### Interactive gotchas

- **Toggle basis must update ALL labels** — including the end-of-line labels and the readout strip. Easy to miss the readout text after switching.
- **G-O spread is dashed** to differentiate from the three main lines, and uses `--highlight` to indicate "this is the derived view, not raw data".
- **If user provides only GAAP**, hide the basis toggle (don't show a broken non-functional control).
- **Period axis is categorical** (ordinal), so brush-to-zoom doesn't apply here. Skip brush for this chart.
