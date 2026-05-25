# Cohort retention / unit economics

Cohort curves: one line per acquisition vintage (cohort), showing % of original cohort still active (or revenue retained) by months since acquisition. Older cohorts in `--neutral`, the most recent in `--accent` or `--highlight`. Reveals whether retention is improving, deteriorating, or stable across vintages — and whether mature cohorts plateau at a "core" retention level.

## When to use

User asks: "cohort curves", "retention", "unit economics", "LTV by vintage", "are newer cohorts better", "SaaS retention curves", "monthly active retention". Critical for SaaS, subscription, consumer DTC, gaming, neobanks — anywhere the unit of analysis is a customer who can churn.

## Required inputs

```js
// One row per cohort; values are % retained at month 0, 1, 2, ...
const cohorts = [
  { cohort: "2021-Q1", values: [1.00, 0.85, 0.78, 0.72, 0.68, 0.65, 0.62, 0.60, 0.58, 0.57, 0.56, 0.55, 0.54] },
  { cohort: "2021-Q3", values: [1.00, 0.87, 0.80, 0.74, 0.70, 0.67, 0.64, 0.62, 0.60, 0.59, 0.58, 0.57] },
  { cohort: "2022-Q1", values: [1.00, 0.88, 0.82, 0.76, 0.72, 0.69, 0.66, 0.64, 0.62, 0.61] },
  { cohort: "2022-Q3", values: [1.00, 0.89, 0.84, 0.78, 0.74, 0.71, 0.68, 0.66] },
  { cohort: "2023-Q1", values: [1.00, 0.91, 0.86, 0.81, 0.77, 0.74] },
  { cohort: "2023-Q3", values: [1.00, 0.92, 0.87, 0.83] },
  { cohort: "2024-Q1", values: [1.00, 0.93, 0.89] },
];
const metricLabel = "Customers retained";   // or "Revenue retained" for NRR-style
```

For revenue retention (NRR), the metric goes above 100% if expansion exceeds churn — same chart, just different y-axis range.

## Visual structure

- One line per cohort
- X axis: months since acquisition (0 to max observed)
- Y axis: % retained (0 to 100 typically; up to ~140 for NRR)
- Color: graduated from `--neutral` (oldest) to `--accent` (newest), with the most recent cohort in `--highlight` if it's a focal story
- Each line labeled at the end with its cohort name and current retention %
- Optional: a band showing the asymptote / "core retention" zone

## Core template

```js
const margin = { top: 32, right: 100, bottom: 44, left: 56 };
const width = 1088, height = 500;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const maxMonth = d3.max(cohorts, c => c.values.length - 1);
const x = d3.scaleLinear().domain([0, maxMonth]).range([0, innerW]);
const y = d3.scaleLinear().domain([0, 1.05]).range([innerH, 0]);

// grid
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// graduated color: oldest = light, newest = dark; most recent in highlight
const N = cohorts.length;
const cohortColor = (i) => {
  if (i === N - 1) return "var(--highlight)";
  return d3.scaleLinear()
    .domain([0, N - 2])
    .range(["#D4D4CE", "#1F3A5F"])
    .interpolate(d3.interpolateRgb)(i);
};

const line = d3.line()
  .x((d, i) => x(i))
  .y(d => y(d))
  .curve(d3.curveMonotoneX);

cohorts.forEach((c, i) => {
  g.append("path")
    .datum(c.values)
    .attr("fill", "none")
    .attr("stroke", cohortColor(i))
    .attr("stroke-width", i === N - 1 ? 2.2 : 1.4)
    .attr("d", line);

  // dots
  g.selectAll(`.dot-${i}`)
    .data(c.values).join("circle")
      .attr("cx", (d, j) => x(j))
      .attr("cy", d => y(d))
      .attr("r", 2.5)
      .attr("fill", cohortColor(i));

  // end label
  const lastIdx = c.values.length - 1;
  const lastVal = c.values[lastIdx];
  g.append("text")
    .attr("x", x(lastIdx) + 6)
    .attr("y", y(lastVal) + 4)
    .attr("class", "data-label")
    .attr("fill", cohortColor(i))
    .attr("font-weight", i === N - 1 ? 600 : 400)
    .text(`${c.cohort}  ${d3.format(".0%")(lastVal)}`);
});

// axes
g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).ticks(8));
g.append("text")
  .attr("class","axis-label")
  .attr("x", innerW/2).attr("y", innerH + 36)
  .attr("text-anchor","middle")
  .text("Months since acquisition");

g.append("g").attr("class","axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d3.format(".0%")));
g.append("text")
  .attr("class","axis-label")
  .attr("transform", `translate(${-margin.left + 16}, ${innerH/2}) rotate(-90)`)
  .attr("text-anchor","middle")
  .text(metricLabel);
```

## Variants

- **Net Revenue Retention (NRR)**: y-axis goes up to 130-150%. Each cohort's revenue line includes upsell/cross-sell, so it can rise above 100% even as logos churn.
- **Layered area "stacked cohorts"**: an absolute view where each cohort is stacked vertically — shows total ARR/customers by composition. Different chart; complementary, not replacement.
- **Survival curve** (Kaplan-Meier-style): for low-frequency data, this is more statistically honest than naive cohort %.
- **LTV / CAC ladder**: separate chart, not a cohort curve, but often paired — show LTV by cohort as a bar chart with CAC line overlay.
- **Two-panel: GR retention + NR retention**: classic SaaS framing. Gross logo retention on the left, net revenue retention on the right.

## Gotchas

- **State the unit clearly**: customers, logos, accounts, MAUs, $ARR retained, $ revenue retained. They're different. SaaS NRR ≠ logo retention.
- **Period censoring**: newer cohorts have fewer observations. Don't extrapolate them visually; let the line just end short.
- **Anonymize cohort names** if commercially sensitive — "Vintage 1, 2, 3..." with a note in source.
- **Asymptote matters**: the steady-state retention (typically months 18-36 in B2B SaaS) is the unit-economics number. If older cohorts haven't plateaued, the LTV math is speculative.
- **Don't smooth aggressively**: cohort curves can have non-monotonic bumps from re-engagement campaigns or holiday effects. `curveLinear` or `curveMonotoneX`, not `curveBasis`.
- **In consumer/DTC**, repeat purchase ≠ retention. Pick the metric carefully and state it.

---

## Interactive variant — hover cohort + GR/NR toggle + highlight individual cohort

Hover any cohort line for vintage info + retention at that month. Click a cohort to sticky-highlight it (others dim). Toggle between gross logo retention and net revenue retention (NRR — y-axis goes above 100%).

### Required input

```js
const cohorts = {
  gross: [ /* same shape as static */ ],
  nrr:   [ /* NRR values, can exceed 1.0 */ ],
};
```

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Metric</span>
    <div class="pills" id="metric-pills">
      <span class="pill active" data-metric="gross">Gross logo retention</span>
      <span class="pill" data-metric="nrr">Net revenue retention</span>
    </div>
  </div>
  <button class="btn" onclick="clearSelection()">Clear selection</button>
</div>
<div id="chart"></div>
```

### Core template

```js
let metric = "gross";
let selectedIdx = null;

const margin = { top: 32, right: 120, bottom: 44, left: 56 };
const width = 1088, height = 500;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().range([0, innerW]);
const y = d3.scaleLinear().range([innerH, 0]);

const gridG = g.append("g").attr("class","grid");
const refLineG = g.append("g").attr("class","ref");
const linesG = g.append("g").attr("class","lines");
const xAxisG = g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0,${innerH})`);
const yAxisG = g.append("g").attr("class","axis axis-num");
g.append("text").attr("class","axis-label")
  .attr("x", innerW/2).attr("y", innerH + 36)
  .attr("text-anchor","middle").text("Months since acquisition");

function cohortColor(i, N) {
  if (selectedIdx === i) return "var(--highlight)";
  if (selectedIdx !== null && selectedIdx !== i) return "var(--neutral)";
  if (i === N-1) return "var(--highlight)";
  return d3.scaleLinear().domain([0, N-2]).range(["#D4D4CE", "#1F3A5F"])
    .interpolate(d3.interpolateRgb)(i);
}

function redraw() {
  const arr = cohorts[metric];
  const maxMonth = d3.max(arr, c => c.values.length - 1);
  x.domain([0, maxMonth]);
  const maxVal = d3.max(arr.flatMap(c => c.values));
  y.domain([0, Math.max(1.05, maxVal * 1.05)]);

  gridG.call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

  refLineG.selectAll("*").remove();
  if (metric === "nrr") {
    refLineG.append("line")
      .attr("x1",0).attr("x2",innerW)
      .attr("y1",y(1.0)).attr("y2",y(1.0))
      .attr("stroke","var(--ink-2)").attr("stroke-dasharray","2 3");
    refLineG.append("text")
      .attr("x", innerW - 40).attr("y", y(1.0) - 4)
      .attr("class","data-label").attr("fill","var(--ink-2)")
      .text("100% NRR");
  }

  xAxisG.call(d3.axisBottom(x).ticks(8));
  yAxisG.call(d3.axisLeft(y).tickFormat(d3.format(".0%")));

  const N = arr.length;
  linesG.selectAll("*").remove();

  arr.forEach((c, i) => {
    const line = d3.line()
      .x((d, j) => x(j)).y(d => y(d))
      .curve(d3.curveMonotoneX);
    const color = cohortColor(i, N);
    const isSelected = selectedIdx === i || (selectedIdx === null && i === N-1);

    const path = linesG.append("path").datum(c.values)
      .attr("fill","none").attr("stroke", color)
      .attr("stroke-width", isSelected ? 2.2 : 1.4)
      .attr("d", line)
      .style("cursor","pointer")
      .on("click", () => {
        selectedIdx = selectedIdx === i ? null : i;
        redraw();
      });

    linesG.selectAll(`.dot-${i}`).data(c.values).join("circle")
      .attr("cx", (d, j) => x(j)).attr("cy", d => y(d))
      .attr("r", 2.5).attr("fill", color)
      .style("cursor","pointer")
      .on("mouseover", function(evt, d) {
        const j = c.values.indexOf(d);
        showTip(
          `<b>${c.cohort}</b> &middot; Month ${j}<br>
           Retained: <span class="num">${d3.format(".1%")(d)}</span>
           ${j > 0 ? `<br>Δ from month 0: <span class="num">${d3.format("+.1%")(d - c.values[0])}</span>` : ""}`,
          evt);
      })
      .on("mouseout", hideTip);

    const lastIdx = c.values.length - 1;
    const lastVal = c.values[lastIdx];
    linesG.append("text")
      .attr("x", x(lastIdx) + 6).attr("y", y(lastVal) + 4)
      .attr("class","data-label").attr("fill", color)
      .attr("font-weight", isSelected ? 600 : 400)
      .text(`${c.cohort}  ${d3.format(".0%")(lastVal)}`);
  });
}
redraw();

function clearSelection() { selectedIdx = null; redraw(); }
document.querySelectorAll("#metric-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#metric-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    metric = p.dataset.metric;
    redraw();
  });
});
```

### Interactive gotchas

- **NRR mode y-axis goes above 100%** — show a dashed reference at 100% so readers anchor.
- **Click-to-select dims others** to ~30% opacity — but don't hide them; the comparison context is the value.
- **Most recent cohort is highlighted by default**. When user clicks a different cohort, the "newest" highlight transfers — only one cohort is highlighted at a time.
- **Cohort name in tooltip matters more than the month** — readers usually want to know "which vintage was 80% at month 12" not "what value at this point".
