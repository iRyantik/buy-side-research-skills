# Peer 2D scatter

A scatter where each dot is a company, positioned on two metrics (e.g. growth vs margin, valuation vs ROIC, FCF yield vs leverage). Used to position the target name visually against its peer set.

## When to use

User asks: "where do peers sit", "growth vs margin", "valuation vs ROIC", "2x2 peer map", "show the comp set". The two axes encode the trade-off you want the reader to see. The target name is highlighted; everyone else is neutral.

## Required inputs

```js
const peers = [
  { ticker: "AAPL", name: "Apple",     x: 0.061, y: 0.31, size: 3200, focal: false },
  { ticker: "MSFT", name: "Microsoft", x: 0.13,  y: 0.42, size: 3050, focal: false },
  { ticker: "GOOGL", name: "Alphabet", x: 0.115, y: 0.33, size: 2100, focal: true  },
  { ticker: "META", name: "Meta",      x: 0.16,  y: 0.39, size: 1450, focal: false },
  { ticker: "ORCL", name: "Oracle",    x: 0.07,  y: 0.28, size: 480,  focal: false },
];

const xMeta = { label: "Revenue growth, 3y CAGR", fmt: d3.format(".0%") };
const yMeta = { label: "EBIT margin",             fmt: d3.format(".0%") };
const sMeta = { label: "Market cap ($bn)" };
```

Optionally provide quadrant lines (`xMid`, `yMid`) — usually the sample median for each axis.

## Visual structure

- Scatter plot, axes labeled with metric + units
- Each dot: filled circle. Target name in `--highlight`, all others in `--neutral`. Size optionally encodes a third metric (market cap, revenue).
- Ticker labels at each dot (8–9pt, mono); avoid overlap
- Median lines (dotted, hairline) dividing the plot into quadrants — optional
- Subtitle states what "good" looks like: "Upper-right = high growth + high margin"

## Core template

```js
const margin = { top: 32, right: 32, bottom: 56, left: 64 };
const width = 1088, height = 540;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear()
  .domain(d3.extent(peers, d => d.x)).nice()
  .range([0, innerW]);
const y = d3.scaleLinear()
  .domain(d3.extent(peers, d => d.y)).nice()
  .range([innerH, 0]);
const r = d3.scaleSqrt()
  .domain([0, d3.max(peers, d => d.size)])
  .range([0, 24]);

// grid
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));
g.append("g").attr("class","grid")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickSize(-innerH).tickFormat(""));

// optional quadrant lines (sample median)
const xMid = d3.median(peers, d => d.x);
const yMid = d3.median(peers, d => d.y);
g.append("line")
  .attr("x1", x(xMid)).attr("x2", x(xMid))
  .attr("y1", 0).attr("y2", innerH)
  .attr("stroke", "var(--ink-3)").attr("stroke-dasharray", "3 4");
g.append("line")
  .attr("x1", 0).attr("x2", innerW)
  .attr("y1", y(yMid)).attr("y2", y(yMid))
  .attr("stroke", "var(--ink-3)").attr("stroke-dasharray", "3 4");

// dots
g.selectAll(".peer")
  .data(peers).join("circle")
    .attr("class", "peer")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r",  d => r(d.size))
    .attr("fill", d => d.focal ? "var(--highlight)" : "var(--neutral)")
    .attr("fill-opacity", 0.55)
    .attr("stroke", d => d.focal ? "var(--highlight)" : "var(--ink-3)")
    .attr("stroke-width", 1);

// ticker labels
g.selectAll(".peer-label")
  .data(peers).join("text")
    .attr("class", "data-label")
    .attr("x", d => x(d.x) + r(d.size) + 4)
    .attr("y", d => y(d.y) + 4)
    .attr("fill", d => d.focal ? "var(--highlight)" : "var(--ink-2)")
    .attr("font-weight", d => d.focal ? 600 : 400)
    .text(d => d.ticker);

// axes with labels
g.append("g")
  .attr("class", "axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickFormat(xMeta.fmt));
g.append("text")
  .attr("class", "axis-label")
  .attr("x", innerW / 2).attr("y", innerH + 40)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(xMeta.label);

g.append("g")
  .attr("class", "axis axis-num")
  .call(d3.axisLeft(y).tickFormat(yMeta.fmt));
g.append("text")
  .attr("class", "axis-label")
  .attr("transform", `translate(${-margin.left + 18}, ${innerH/2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(yMeta.label);
```

## Variants

- **Connected scatter** (a.k.a. ant trail): plot the same company over multiple years as a path. Useful for "how has this company moved on the growth-margin map over the past 5 years".
- **Industry-grouped colors**: replace `--neutral` with per-industry palette from `--cat-*` tokens when comparing across industries.
- **With trendline**: fit OLS regression across peers, draw thin dashed `--hairline` line. The target's position relative to the line tells you "premium" or "discount" vs implied.

## Gotchas

- **Pick axes that frame a trade-off the reader cares about**: not just two random metrics. Growth vs margin, valuation vs ROIC, FCF yield vs leverage — these are the durable ones.
- **Don't include too many peers** — 8–15 is the sweet spot. Past 20, ticker labels overlap and the chart loses signal.
- **Beware logarithmic instincts**: if market cap spans 100x, you might need log scale or grouping. Mention if you've log-transformed.
- **Always label all dots**. An unlabeled dot is wasted data and looks lazy.
- **State data normalization** in the source line: trailing-12M, last-reported, consensus-NTM. Don't mix.

---

## Interactive variant — axis switchers + sticky click

For peer analysis exploration: let the user swap the x/y/size metrics from a dropdown, hover for full company card, click a dot to sticky-highlight it. Lets you ask "where do peers sit on growth vs margin"... then immediately "vs valuation vs ROIC" without rebuilding.

### Required input (richer data shape)

```js
const peers = [
  {
    ticker: "AAPL", name: "Apple",
    metrics: {
      growth_3y: 0.061, ebit_margin: 0.31, roic: 0.42, fwd_pe: 28.5,
      mkt_cap: 3200, fcf_yield: 0.034, net_debt_ebitda: -0.5,
    },
    focal: false,
    industry: "Hardware",
  },
  // ...
];

const metricsCatalog = [
  { key: "growth_3y",       label: "Revenue growth, 3y CAGR", fmt: d3.format(".0%") },
  { key: "ebit_margin",     label: "EBIT margin",             fmt: d3.format(".0%") },
  { key: "roic",            label: "ROIC",                    fmt: d3.format(".0%") },
  { key: "fwd_pe",          label: "Fwd PE",                  fmt: d => d.toFixed(1)+"x" },
  { key: "mkt_cap",         label: "Market cap ($bn)",        fmt: d3.format(",") },
  { key: "fcf_yield",       label: "FCF yield",               fmt: d3.format(".1%") },
  { key: "net_debt_ebitda", label: "Net debt / EBITDA",       fmt: d => d.toFixed(1)+"x" },
];
```

Add as many metrics as the data supports — the dropdown reads from `metricsCatalog`.

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">X axis</span>
    <select id="x-metric"></select>
  </div>
  <div class="controls-section">
    <span class="controls-label">Y axis</span>
    <select id="y-metric"></select>
  </div>
  <div class="controls-section">
    <span class="controls-label">Size</span>
    <select id="s-metric"></select>
  </div>
  <button class="btn" onclick="clearSelection()">Clear selection</button>
</div>

<div id="chart"></div>
```

```css
.controls select {
  font-family: var(--font-sans);
  font-size: 11px;
  padding: 3px 8px;
  border: 1px solid var(--hairline);
  background: var(--paper);
  color: var(--ink);
  border-radius: 2px;
  cursor: pointer;
}
.controls select:hover { border-color: var(--ink-2); }
```

### Core template

```js
let xKey = "growth_3y", yKey = "ebit_margin", sKey = "mkt_cap";
let selected = null;

// Populate dropdowns
const xSel = document.getElementById("x-metric");
const ySel = document.getElementById("y-metric");
const sSel = document.getElementById("s-metric");
metricsCatalog.forEach(m => {
  [xSel, ySel, sSel].forEach(sel => {
    const opt = document.createElement("option");
    opt.value = m.key; opt.textContent = m.label;
    sel.appendChild(opt);
  });
});
xSel.value = xKey; ySel.value = yKey; sSel.value = sKey;

const margin = { top: 32, right: 32, bottom: 56, left: 64 };
const width = 1088, height = 540;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().range([0, innerW]);
const y = d3.scaleLinear().range([innerH, 0]);
const r = d3.scaleSqrt().range([4, 28]);

// Static layers
const gridG = g.append("g").attr("class", "grid-layer");
const quadG = g.append("g").attr("class", "quad-layer");
const dotG  = g.append("g").attr("class", "dot-layer");
const labelG = g.append("g").attr("class", "label-layer");
const xAxisG = g.append("g").attr("class", "axis axis-num x-axis")
  .attr("transform", `translate(0,${innerH})`);
const yAxisG = g.append("g").attr("class", "axis axis-num y-axis");
const xLabelText = g.append("text").attr("class","axis-label x-axis-label")
  .attr("x", innerW/2).attr("y", innerH + 40).attr("text-anchor","middle").attr("font-weight",600);
const yLabelText = g.append("text").attr("class","axis-label y-axis-label")
  .attr("transform", `translate(${-margin.left+18},${innerH/2}) rotate(-90)`)
  .attr("text-anchor","middle").attr("font-weight",600);

function redraw() {
  const xMeta = metricsCatalog.find(m => m.key === xKey);
  const yMeta = metricsCatalog.find(m => m.key === yKey);
  const sMeta = metricsCatalog.find(m => m.key === sKey);

  // Scales
  x.domain(d3.extent(peers, d => d.metrics[xKey])).nice();
  y.domain(d3.extent(peers, d => d.metrics[yKey])).nice();
  r.domain([0, d3.max(peers, d => d.metrics[sKey])]);

  // Grid
  gridG.selectAll("*").remove();
  gridG.append("g").attr("class","grid")
    .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));
  gridG.append("g").attr("class","grid")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).tickSize(-innerH).tickFormat(""));

  // Quadrant median lines
  quadG.selectAll("*").remove();
  const xMid = d3.median(peers, d => d.metrics[xKey]);
  const yMid = d3.median(peers, d => d.metrics[yKey]);
  quadG.append("line")
    .attr("x1", x(xMid)).attr("x2", x(xMid))
    .attr("y1", 0).attr("y2", innerH)
    .attr("stroke","var(--ink-3)").attr("stroke-dasharray","3 4");
  quadG.append("line")
    .attr("x1", 0).attr("x2", innerW)
    .attr("y1", y(yMid)).attr("y2", y(yMid))
    .attr("stroke","var(--ink-3)").attr("stroke-dasharray","3 4");

  // Dots
  const dots = dotG.selectAll(".peer").data(peers, d => d.ticker);
  const dotsEnter = dots.enter().append("circle")
    .attr("class","peer")
    .style("cursor","pointer")
    .on("mouseover", function(evt, d) {
      const x_str = xMeta.fmt(d.metrics[xKey]);
      const y_str = yMeta.fmt(d.metrics[yKey]);
      const s_str = sMeta.fmt(d.metrics[sKey]);
      showTip(
        `<b>${d.ticker} — ${d.name}</b>${d.industry ? `<br><span style="color:var(--neutral);">${d.industry}</span>` : ""}
         <hr style="border:none;border-top:1px solid #444;margin:5px 0;">
         ${xMeta.label}: <span class="num">${x_str}</span><br>
         ${yMeta.label}: <span class="num">${y_str}</span><br>
         ${sMeta.label}: <span class="num">${s_str}</span>`,
        evt
      );
    })
    .on("mouseout", hideTip)
    .on("click", (evt, d) => {
      selected = (selected === d) ? null : d;
      applySelection();
    });

  dots.merge(dotsEnter)
    .transition().duration(250)
    .attr("cx", d => x(d.metrics[xKey]))
    .attr("cy", d => y(d.metrics[yKey]))
    .attr("r",  d => r(d.metrics[sKey]));

  applyDotStyling();
  dots.exit().remove();

  // Ticker labels
  const labels = labelG.selectAll(".peer-label").data(peers, d => d.ticker);
  labels.enter().append("text")
    .attr("class","data-label peer-label")
    .merge(labels)
    .transition().duration(250)
    .attr("x", d => x(d.metrics[xKey]) + r(d.metrics[sKey]) + 4)
    .attr("y", d => y(d.metrics[yKey]) + 4)
    .text(d => d.ticker);
  labels.exit().remove();
  applyLabelStyling();

  // Axes
  xAxisG.transition().duration(250)
    .call(d3.axisBottom(x).tickFormat(xMeta.fmt));
  yAxisG.transition().duration(250)
    .call(d3.axisLeft(y).tickFormat(yMeta.fmt));
  xLabelText.text(xMeta.label);
  yLabelText.text(yMeta.label);
}

function applyDotStyling() {
  dotG.selectAll(".peer")
    .attr("fill", d => {
      if (selected) return d === selected ? "var(--highlight)" : "var(--neutral)";
      return d.focal ? "var(--highlight)" : "var(--neutral)";
    })
    .attr("fill-opacity", d => {
      if (selected) return d === selected ? 0.85 : 0.2;
      return 0.55;
    })
    .attr("stroke", d => (selected === d || (!selected && d.focal)) ? "var(--highlight)" : "var(--ink-3)")
    .attr("stroke-width", d => (selected === d) ? 2 : 1);
}

function applyLabelStyling() {
  labelG.selectAll(".peer-label")
    .attr("fill", d => {
      if (selected) return d === selected ? "var(--highlight)" : "var(--ink-3)";
      return d.focal ? "var(--highlight)" : "var(--ink-2)";
    })
    .attr("font-weight", d => (selected === d || (!selected && d.focal)) ? 600 : 400);
}

function applySelection() {
  applyDotStyling();
  applyLabelStyling();
}

function clearSelection() {
  selected = null;
  applySelection();
}

xSel.addEventListener("change", () => { xKey = xSel.value; redraw(); });
ySel.addEventListener("change", () => { yKey = ySel.value; redraw(); });
sSel.addEventListener("change", () => { sKey = sSel.value; redraw(); });

redraw();
```

### Interactive gotchas

- **Animate transitions on axis change** — 250ms is enough for the eye to track which dot went where. Without animation, the chart appears to teleport and the connection is lost.
- **Don't change the dot order** on metric switch — D3 key function on `ticker` ensures stable identity. If you forget the key, dots get reassigned and the animation is meaningless.
- **Selected state should survive metric changes** — if you click AAPL on growth vs margin, then switch to ROIC vs FCF yield, AAPL should remain selected.
- **Tooltip should show the FULL metric set**, not just the displayed axes. The user often picks axes to scan but then wants to see everything for one company on hover.
- **Save current axes in URL hash** for shareable views: `#x=growth_3y&y=ebit_margin&s=mkt_cap`.
