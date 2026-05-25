# Consensus revisions trend

Track of how sell-side consensus EPS or revenue estimates have moved over time. Each line represents the consensus estimate for one fiscal year (FY26E, FY27E), plotted by the date on which the estimate was current. Tells you "is the street getting more optimistic or more pessimistic" — a critical secondary indicator for momentum and quality strategies.

## When to use

User asks: "estimate revisions", "where is consensus heading", "sell-side upgrades", "earnings revision trend", "is the street walking up numbers", "consensus drift". Watch for inflection points: a steady upward drift breaking down often precedes share underperformance.

## Required inputs

```js
// Each row is a snapshot of consensus on a given date, for each forward year
const data = [
  { date: "2024-01-15", FY24: 12.85, FY25: 14.20, FY26: 15.75 },
  { date: "2024-04-30", FY24: 13.10, FY25: 14.55, FY26: 16.15 },
  { date: "2024-07-31", FY24: 13.25, FY25: 14.85, FY26: 16.60 },
  { date: "2024-10-31", FY24: 13.40, FY25: 15.10, FY26: 17.05 },
  { date: "2025-01-31", FY24: 13.58, FY25: 15.42, FY26: 17.50 },  // FY24 actual reported here
  { date: "2025-04-30", FY25: 15.65, FY26: 18.00, FY27: 20.50 },
  { date: "2025-07-31", FY25: 15.85, FY26: 18.45, FY27: 21.10 },
  { date: "2025-10-31", FY25: 16.05, FY26: 18.90, FY27: 21.85 },
  { date: "2026-01-31", FY25: 16.20, FY26: 19.10, FY27: 22.40 },  // FY25 actual reported
  { date: "2026-03-31", FY26: 19.45, FY27: 22.95, FY28: 26.10 },
];
// Optional: most recent actual reported, for anchor
const actuals = { FY24: 13.58, FY25: 16.20 };
```

Each fiscal year line begins ~24M before that year's end and ends after it reports.

## Visual structure

- X axis: date
- Y axis: EPS in $ (or whatever the metric is)
- One line per FY estimate, in graduated shades of `--accent` (oldest = lightest, latest = darkest)
- Once a year reports (actual lands), show a focal dot with `--highlight` and small label "FY24A: $13.58"
- Optional: shaded period — last 6M revisions — to show recent trend
- Right end labels: each line labeled "FY26E", "FY27E" etc

## Core template

```js
const margin = { top: 32, right: 80, bottom: 36, left: 48 };
const width = 1088, height = 460;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// reshape data: one array per FY
const fyKeys = [...new Set(data.flatMap(d => Object.keys(d).filter(k => k.startsWith("FY"))))];
const series = fyKeys.map(fy => ({
  key: fy,
  points: data.filter(d => d[fy] != null).map(d => ({ date: new Date(d.date), value: d[fy] })),
}));

const x = d3.scaleTime()
  .domain(d3.extent(data, d => new Date(d.date)))
  .range([0, innerW]);
const y = d3.scaleLinear()
  .domain([
    d3.min(series.flatMap(s => s.points), d => d.value) * 0.92,
    d3.max(series.flatMap(s => s.points), d => d.value) * 1.05
  ]).nice()
  .range([innerH, 0]);

// grid
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// graduated colors — earliest year is lightest
const fyColors = d3.scaleLinear()
  .domain([0, fyKeys.length - 1])
  .range(["#C8D2DE", "#1F3A5F"])
  .interpolate(d3.interpolateRgb);

const line = d3.line()
  .x(d => x(d.date))
  .y(d => y(d.value))
  .curve(d3.curveMonotoneX);

series.forEach((s, i) => {
  g.append("path")
    .datum(s.points)
    .attr("fill", "none")
    .attr("stroke", fyColors(i))
    .attr("stroke-width", 1.7)
    .attr("d", line);

  // dots at each revision date
  g.selectAll(`.rev-${s.key}`)
    .data(s.points).join("circle")
      .attr("cx", d => x(d.date))
      .attr("cy", d => y(d.value))
      .attr("r", 2.5)
      .attr("fill", fyColors(i));

  // end label
  const last = s.points[s.points.length - 1];
  const isActual = actuals[s.key] != null;
  g.append("text")
    .attr("x", x(last.date) + 6)
    .attr("y", y(last.value) + 4)
    .attr("class", "data-label")
    .attr("fill", isActual ? "var(--highlight)" : fyColors(i))
    .attr("font-weight", isActual ? 600 : 400)
    .text(`${s.key}${isActual ? "A" : "E"}  $${last.value.toFixed(2)}`);
});

// axes
g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %y")));
g.append("g").attr("class","axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d => "$" + d.toFixed(2)));
```

## Variants

- **% change from initial estimate**: rebase each line to 100 at its first data point. Tells you "consensus for FY26 has been revised up 18% since 24M ago" — cleaner than absolute $.
- **Earnings momentum strip**: separate small panel below showing the # of analysts up-revising minus down-revising over rolling 4 weeks. Standard quant signal.
- **Revenue + EPS in two panels**: same chart structure stacked. Useful when revenue is going one way and EPS the other (margin pressure or expansion story).
- **Add the price line in a top panel** to see whether the stock has tracked or diverged from the revision pattern.

## Gotchas

- **Define "consensus"**: Bloomberg BEST, FactSet, IBES, Refinitiv. They differ slightly; state which.
- **Watch for fiscal year-end resets**: when FY24 reports, it transitions from estimate to actual. Mark this visually.
- **Don't compare across reporting standards** — calendar year vs fiscal year vs broken fiscal periods (e.g. AAPL Sep FYE vs CY).
- **Currency**: state reporting currency in subtitle if it's not USD.
- **Revisions tell you direction, not magnitude** — a 1% revision from $5.00 to $5.05 looks tiny but moves price targets meaningfully. Add a secondary % change panel if helpful.

---

## Interactive variant — hover trajectory + indexed/absolute toggle

Hover any revision point to see the exact estimate and the revision delta from the previous month. Toggle between absolute $ and indexed (rebased to 100 at first estimate) — the indexed view makes "consensus drifted up 18% over 24 months" instantly visible.

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Display</span>
    <div class="pills" id="mode-pills">
      <span class="pill active" data-mode="absolute">Absolute $</span>
      <span class="pill" data-mode="indexed">Indexed (initial = 100)</span>
      <span class="pill" data-mode="vs-initial">% change vs initial</span>
    </div>
  </div>
</div>
<div id="chart"></div>
```

### Core template

```js
let mode = "absolute";

const margin = { top: 32, right: 80, bottom: 36, left: 56 };
const width = 1088, height = 460;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const fyKeys = [...new Set(data.flatMap(d => Object.keys(d).filter(k => k.startsWith("FY"))))];
const series = fyKeys.map(fy => ({
  key: fy,
  points: data.filter(d => d[fy] != null).map(d => ({
    date: new Date(d.date),
    raw: d[fy],
    initial: null,    // filled in below
  }))
})).filter(s => s.points.length > 0);

// Fill in initial value for indexed mode
series.forEach(s => {
  const init = s.points[0].raw;
  s.points.forEach(p => p.initial = init);
});

const x = d3.scaleTime()
  .domain(d3.extent(data, d => new Date(d.date)))
  .range([0, innerW]);
const y = d3.scaleLinear().range([innerH, 0]);

const N = series.length;
const fyColor = i => i === N-1 ? "var(--highlight)"
  : d3.scaleLinear().domain([0, N-2]).range(["#C8D2DE","#1F3A5F"]).interpolate(d3.interpolateRgb)(i);

const gridG = g.append("g").attr("class","grid");
const linesG = g.append("g").attr("class","lines");
const xAxisG = g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0,${innerH})`);
const yAxisG = g.append("g").attr("class","axis axis-num");

const ch = g.append("g").style("display","none").style("pointer-events","none");
ch.append("line").attr("class","crosshair").attr("y1",0).attr("y2",innerH);

function valueOf(p) {
  if (mode === "absolute")   return p.raw;
  if (mode === "indexed")    return (p.raw / p.initial) * 100;
  if (mode === "vs-initial") return (p.raw / p.initial) - 1;
}
function fmt(v) {
  if (mode === "absolute")   return "$" + v.toFixed(2);
  if (mode === "indexed")    return v.toFixed(1);
  if (mode === "vs-initial") return d3.format("+.1%")(v);
}

function redraw() {
  const allVals = series.flatMap(s => s.points.map(valueOf));
  if (mode === "absolute") {
    y.domain([d3.min(allVals) * 0.92, d3.max(allVals) * 1.05]).nice();
  } else if (mode === "indexed") {
    y.domain([Math.min(95, d3.min(allVals)), d3.max(allVals) * 1.05]).nice();
  } else {
    y.domain([Math.min(0, d3.min(allVals)), d3.max(allVals) * 1.1]).nice();
  }

  gridG.call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));
  xAxisG.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %y")));
  yAxisG.call(d3.axisLeft(y).tickFormat(
    mode === "vs-initial" ? d3.format("+.0%") :
    mode === "indexed"    ? d3.format(".0f")  :
                            (d => "$" + d.toFixed(2))));

  // Reference line at baseline (100 for indexed, 0% for vs-initial)
  linesG.selectAll(".ref-line").remove();
  if (mode === "indexed") {
    linesG.append("line").attr("class","ref-line")
      .attr("x1",0).attr("x2",innerW).attr("y1",y(100)).attr("y2",y(100))
      .attr("stroke","var(--ink-3)").attr("stroke-dasharray","2 3");
  } else if (mode === "vs-initial") {
    linesG.append("line").attr("class","ref-line")
      .attr("x1",0).attr("x2",innerW).attr("y1",y(0)).attr("y2",y(0))
      .attr("stroke","var(--ink-3)").attr("stroke-dasharray","2 3");
  }

  linesG.selectAll(".series").remove();
  series.forEach((s, i) => {
    const line = d3.line()
      .x(d => x(d.date)).y(d => y(valueOf(d)))
      .curve(d3.curveMonotoneX);
    const sg = linesG.append("g").attr("class","series");
    sg.append("path").datum(s.points)
      .attr("fill","none").attr("stroke", fyColor(i))
      .attr("stroke-width", i === N-1 ? 2.0 : 1.5)
      .attr("d", line);
    sg.selectAll("circle").data(s.points).join("circle")
      .attr("cx", d => x(d.date)).attr("cy", d => y(valueOf(d)))
      .attr("r", 2.8).attr("fill", fyColor(i))
      .style("cursor","pointer")
      .on("mouseover", function(evt, d) {
        const idx = s.points.indexOf(d);
        const prev = idx > 0 ? s.points[idx-1] : null;
        const delta = prev ? d3.format("+.1%")(d.raw/prev.raw - 1) : "—";
        showTip(
          `<b>${s.key}E</b> &middot; ${d3.timeFormat("%b %y")(d.date)}<br>
           Estimate: <span class="num">$${d.raw.toFixed(2)}</span><br>
           vs prior: <span class="num" style="color:${delta.startsWith('-') ? 'var(--neg-soft)' : 'var(--pos-soft)'}">${delta}</span><br>
           vs initial: <span class="num">${d3.format("+.1%")(d.raw/d.initial - 1)}</span>`,
          evt);
      })
      .on("mouseout", hideTip);

    const last = s.points[s.points.length-1];
    sg.append("text")
      .attr("x", x(last.date) + 6).attr("y", y(valueOf(last)) + 4)
      .attr("class","data-label").attr("fill", fyColor(i))
      .attr("font-weight", i === N-1 ? 600 : 400)
      .text(`${s.key}E ${fmt(valueOf(last))}`);
  });
}
redraw();

// Crosshair overlay
const overlay = g.append("rect")
  .attr("width", innerW).attr("height", innerH).attr("fill","transparent")
  .style("cursor","crosshair");
overlay
  .on("mouseenter", () => ch.style("display", null))
  .on("mouseleave", () => ch.style("display","none"))
  .on("mousemove", function(evt) {
    const mx = d3.pointer(evt, this)[0];
    ch.select("line").attr("x1", mx).attr("x2", mx);
  });

document.querySelectorAll("#mode-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#mode-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    mode = p.dataset.mode;
    redraw();
  });
});
```

### Interactive gotchas

- **Indexed view exaggerates relative moves** — that's the feature, not a bug. But state in the subtitle so readers don't read indexed as absolute.
- **Reference line at baseline** is essential for the % change modes — readers anchor visually against 0% or 100.
- **Show vs-prior and vs-initial both in the tooltip** — the analyst cares about both ("did they walk it up this month" AND "has it drifted up over 24 months").
- **Color the delta in tooltip** by sign — readers process color faster than the `+` or `−` sign.
