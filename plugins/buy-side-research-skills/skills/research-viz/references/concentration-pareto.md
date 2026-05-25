# Concentration / Pareto chart

Top-N customers, products, suppliers, or geographies by share of revenue (or any concentration metric), with a cumulative-% line overlay. Shows "the top 5 customers = X% of revenue" at a glance.

## When to use

User asks: "customer concentration", "top 10 products", "supplier risk", "how concentrated is the revenue", "Pareto chart", "key account risk". This is a critical risk-side chart for thesis stress-testing.

## Required inputs

```js
const items = [
  { name: "Apple",        value: 0.265 },   // 26.5% of revenue
  { name: "Microsoft",    value: 0.142 },
  { name: "Amazon AWS",   value: 0.098 },
  { name: "Meta",         value: 0.071 },
  { name: "Alphabet",     value: 0.058 },
  { name: "Tesla",        value: 0.041 },
  { name: "Samsung",      value: 0.032 },
  { name: "Other (50+ customers)", value: 0.293 },
];
const categoryLabel = "Customer";   // or "Product", "Supplier", "Region"
```

Values must sum to 1.0 (100%). If they don't, either add an "Other" bucket or call out the gap in the source.

## Visual structure

- Horizontal bar chart, sorted by value descending
- Bars in `--accent`; the "Other" bucket in `--neutral`
- Cumulative % line overlay on a secondary right-side axis, in `--highlight`
- Each bar labeled with its % at the end
- Optional: a callout for "Top N = X%" annotation

## Core template

```js
// sort, computing cumulative
items.sort((a, b) => b.value - a.value);
const otherIdx = items.findIndex(d => d.name.toLowerCase().includes("other"));
// keep "Other" at the end even if it's large
if (otherIdx >= 0 && otherIdx !== items.length - 1) {
  const o = items.splice(otherIdx, 1)[0];
  items.push(o);
}
let cum = 0;
items.forEach(d => { d.cum = (cum += d.value); });

const margin = { top: 40, right: 60, bottom: 36, left: 180 };
const width = 1088;
const innerW = width - margin.left - margin.right;
const barH = 28;
const height = margin.top + items.length * barH + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().domain([0, d3.max(items, d => d.value) * 1.1]).range([0, innerW]);
const xCum = d3.scaleLinear().domain([0, 1]).range([0, innerW]);
const y = d3.scaleBand()
  .domain(items.map(d => d.name))
  .range([0, items.length * barH])
  .padding(0.32);

// grid (vertical hairlines on x)
g.append("g").attr("class","grid")
  .attr("transform", `translate(0, ${items.length * barH})`)
  .call(d3.axisBottom(x).tickSize(-(items.length * barH)).tickFormat(""));

// bars
g.selectAll(".bar")
  .data(items).join("rect")
    .attr("class", "bar")
    .attr("x", 0)
    .attr("y", d => y(d.name))
    .attr("height", y.bandwidth())
    .attr("width", d => x(d.value))
    .attr("fill", d => d.name.toLowerCase().includes("other") ? "var(--neutral)" : "var(--accent)");

// value labels at end of bar
g.selectAll(".bval")
  .data(items).join("text")
    .attr("class", "data-label")
    .attr("x", d => x(d.value) + 6)
    .attr("y", d => y(d.name) + y.bandwidth()/2 + 4)
    .text(d => d3.format(".1%")(d.value));

// row labels (left)
items.forEach(d => {
  g.append("text")
    .attr("x", -10).attr("y", y(d.name) + y.bandwidth()/2 + 4)
    .attr("text-anchor", "end")
    .attr("class", "axis-label")
    .text(d.name);
});

// cumulative line overlay (use point at right edge of each bar at y-mid)
// Use a separate axis at top
const cumLine = d3.line()
  .x(d => xCum(d.cum))
  .y(d => y(d.name) + y.bandwidth()/2);

g.append("path")
  .datum(items)
  .attr("fill", "none")
  .attr("stroke", "var(--highlight)")
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "2 3")
  .attr("d", cumLine);

g.selectAll(".cum-dot")
  .data(items).join("circle")
    .attr("cx", d => xCum(d.cum))
    .attr("cy", d => y(d.name) + y.bandwidth()/2)
    .attr("r", 3)
    .attr("fill", "var(--highlight)");

g.selectAll(".cum-label")
  .data(items).join("text")
    .attr("class","data-label")
    .attr("x", d => xCum(d.cum) + 6)
    .attr("y", d => y(d.name) - 2)
    .attr("fill", "var(--highlight)")
    .text(d => d3.format(".0%")(d.cum));

// axes
g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0, ${items.length * barH})`)
  .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format(".0%")));
g.append("text")
  .attr("class","axis-label")
  .attr("x", innerW/2).attr("y", items.length * barH + 30)
  .attr("text-anchor", "middle")
  .text(`Share of revenue, FY25  ·  Cumulative shown in dotted line`);

// callout: "Top 5 = X%"
const top5 = items.slice(0, 5).reduce((a, b) => a + b.value, 0);
g.append("text")
  .attr("class", "callout")
  .attr("x", innerW - 200).attr("y", -16)
  .attr("text-anchor", "start")
  .attr("fill", "var(--highlight)")
  .text(`Top 5 ${categoryLabel.toLowerCase()}s = ${d3.format(".0%")(top5)} of revenue`);
```

## Variants

- **Lorenz curve**: same data, plotted as cumulative % on y vs cumulative count on x. Shows the inequality shape clearly. Different chart, useful when comparing concentration across companies.
- **Concentration over time**: plot Top-5 share (or HHI) by year as a time series. Shows whether the company is becoming more or less concentrated.
- **HHI annotation**: compute and display the Herfindahl-Hirschman Index as a callout. Useful for antitrust / market-structure framing.
- **Side-by-side concentration**: customers on left, suppliers on right, same chart structure. Shows two-sided dependency at a glance.

## Gotchas

- **Always include an "Other" bucket** with the long tail. Without it, the chart misleads.
- **State the concentration metric** clearly: revenue, gross profit, EBITDA contribution, units, count of stores. Pick one, label it.
- **Disclose anonymization** if the company doesn't disclose customer names — use "Customer A, B, C..." and note in the source.
- **For supplier concentration**, "% of COGS" is usually the right denominator, not revenue.
- **Watch ASC 280 segment vs customer concentration disclosures** — they're different. Customer concentration > 10% is typically disclosed in 10-K; smaller customers are estimated.

---

## Interactive variant — metric switcher + hover detail

Switch the basis between revenue, gross profit, or EBITDA contribution. Hover any bar for the exact share, cumulative %, and absolute amount.

### Required input (per-item multi-metric)

```js
const items = [
  { name: "Apple",        revenue: 0.265, gp: 0.31, ebitda: 0.34, revAmount: 24500 },
  { name: "Microsoft",    revenue: 0.142, gp: 0.17, ebitda: 0.19, revAmount: 13100 },
  { name: "Other (50+)",  revenue: 0.293, gp: 0.21, ebitda: 0.15, revAmount: 27000 },
  // ...
];
```

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Concentration basis</span>
    <div class="pills" id="basis-pills">
      <span class="pill active" data-basis="revenue">Revenue</span>
      <span class="pill" data-basis="gp">Gross profit</span>
      <span class="pill" data-basis="ebitda">EBITDA contribution</span>
    </div>
  </div>
</div>
<div id="chart"></div>
```

### Core template

```js
let basis = "revenue";

const margin = { top: 40, right: 60, bottom: 36, left: 180 };
const width = 1088;
const innerW = width - margin.left - margin.right;
const barH = 28;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${margin.top + items.length * barH + margin.bottom}`)
  .attr("width", width);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().range([0, innerW]);
const xCum = d3.scaleLinear().domain([0,1]).range([0, innerW]);
const y = d3.scaleBand().range([0, items.length * barH]).padding(0.32);

const gridG = g.append("g").attr("class","grid");
const barsG = g.append("g").attr("class","bars");
const labelsG = g.append("g").attr("class","labels");
const cumG = g.append("g").attr("class","cumulative");
const xAxisG = g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0, ${items.length * barH})`);
const subtitleText = g.append("text").attr("class","axis-label")
  .attr("x", innerW/2).attr("y", items.length * barH + 30)
  .attr("text-anchor","middle");
const calloutText = g.append("text").attr("class","callout")
  .attr("x", innerW - 200).attr("y", -16)
  .attr("text-anchor","start").attr("fill","var(--highlight)");

const basisLabels = { revenue: "revenue", gp: "gross profit", ebitda: "EBITDA contribution" };

function redraw() {
  const sorted = [...items].sort((a, b) => b[basis] - a[basis]);
  const otherIdx = sorted.findIndex(d => d.name.toLowerCase().includes("other"));
  if (otherIdx >= 0 && otherIdx !== sorted.length - 1) {
    const o = sorted.splice(otherIdx, 1)[0];
    sorted.push(o);
  }
  let cum = 0;
  sorted.forEach(d => { d._cum = (cum += d[basis]); });

  x.domain([0, d3.max(sorted, d => d[basis]) * 1.1]);
  y.domain(sorted.map(d => d.name));

  gridG.selectAll("*").remove();
  gridG.attr("transform", `translate(0, ${items.length * barH})`)
    .call(d3.axisBottom(x).tickSize(-(items.length * barH)).tickFormat(""));

  const bars = barsG.selectAll(".bar").data(sorted, d => d.name);
  bars.enter().append("rect").attr("class","bar")
    .merge(bars)
    .style("cursor","pointer")
    .on("mouseover", function(evt, d) {
      showTip(
        `<b>${d.name}</b><br>
         ${basisLabels[basis]}: <span class="num">${d3.format(".1%")(d[basis])}</span><br>
         cumulative: <span class="num">${d3.format(".1%")(d._cum)}</span>
         ${d.revAmount && basis === "revenue" ? `<br>~ <span class="num">${d3.format(",")(Math.round(d.revAmount))}</span> in $m` : ""}`,
        evt);
    })
    .on("mouseout", hideTip)
    .transition().duration(300)
    .attr("x", 0).attr("y", d => y(d.name))
    .attr("height", y.bandwidth())
    .attr("width", d => x(d[basis]))
    .attr("fill", d => d.name.toLowerCase().includes("other") ? "var(--neutral)" : "var(--accent)");
  bars.exit().remove();

  const bvals = barsG.selectAll(".bval").data(sorted, d => d.name);
  bvals.enter().append("text").attr("class","data-label bval")
    .merge(bvals)
    .transition().duration(300)
    .attr("x", d => x(d[basis]) + 6).attr("y", d => y(d.name) + y.bandwidth()/2 + 4)
    .text(d => d3.format(".1%")(d[basis]));
  bvals.exit().remove();

  labelsG.selectAll(".rlabel").remove();
  sorted.forEach(d => {
    labelsG.append("text").attr("class","axis-label rlabel")
      .attr("x", -10).attr("y", y(d.name) + y.bandwidth()/2 + 4)
      .attr("text-anchor", "end").text(d.name);
  });

  cumG.selectAll("*").remove();
  const cumLine = d3.line()
    .x(d => xCum(d._cum))
    .y(d => y(d.name) + y.bandwidth()/2);
  cumG.append("path").datum(sorted)
    .attr("fill","none").attr("stroke","var(--highlight)").attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "2 3")
    .attr("d", cumLine);
  cumG.selectAll(".cdot").data(sorted).join("circle")
    .attr("class","cdot")
    .attr("cx", d => xCum(d._cum))
    .attr("cy", d => y(d.name) + y.bandwidth()/2)
    .attr("r", 3).attr("fill", "var(--highlight)");
  cumG.selectAll(".clabel").data(sorted).join("text")
    .attr("class","data-label clabel")
    .attr("x", d => xCum(d._cum) + 6).attr("y", d => y(d.name) - 2)
    .attr("fill","var(--highlight)")
    .text(d => d3.format(".0%")(d._cum));

  xAxisG.call(d3.axisBottom(x).ticks(5).tickFormat(d3.format(".0%")));
  subtitleText.text(`Share of ${basisLabels[basis]}  ·  Cumulative shown in dotted line`);
  const top5 = sorted.slice(0, 5).reduce((a, b) => a + b[basis], 0);
  calloutText.text(`Top 5 = ${d3.format(".0%")(top5)} of ${basisLabels[basis]}`);
}
redraw();

document.querySelectorAll("#basis-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#basis-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    basis = p.dataset.basis;
    redraw();
  });
});
```

### Interactive gotchas

- **Items reorder when basis changes** — a top-revenue customer might be a tail-EBITDA contributor. Make the reorder smooth (transitions) so the reader can track names.
- **"Other" stays at the bottom** by convention, even after reorder.
- **Cumulative % line transitions too** — re-draws but smoothly.
- **The headline callout** "Top 5 = X%" updates with the basis, so the reader gets a fresh punchline each toggle.
