# Waterfall / bridge

YoY revenue bridge, FCF bridge, EBITDA walk — anything that decomposes a delta between two totals into positive and negative components.

## When to use

User asks: "what drove the change", "YoY bridge", "FCF bridge", "EBITDA walk", "gross to net", "starting cash to ending cash". This is the right chart when there is a clear start point, a clear end point, and 3–8 contributing line items in between.

If there are >10 items, group small ones into "Other" — readers can't track more than 8 bars.

## Required inputs

```js
[
  { label: "FY24 Revenue",   value: 28400, type: "total"  },     // starting bar
  { label: "Price",          value:  +850, type: "delta"  },     // positive
  { label: "Volume",         value: +1320, type: "delta"  },
  { label: "Mix",            value:  -210, type: "delta"  },     // negative
  { label: "FX",             value:  -640, type: "delta"  },
  { label: "M&A",            value:  +480, type: "delta"  },
  { label: "FY25 Revenue",   value: 30200, type: "total"  },     // ending bar
]
```

`type: "total"` bars start at zero. `type: "delta"` bars are floating, starting where the previous bar ended.

## Visual structure

- X axis: categorical (label per bar)
- Y axis: numeric, anchored at zero
- Total bars: solid `--accent`
- Positive deltas: `--pos` solid
- Negative deltas: `--neg` solid
- Connector lines between bars: thin dotted `--hairline`
- Data labels above (or below for negatives) each bar in mono tabular-nums

## Core template

```js
// data: [{label, value, type: "total"|"delta"}]

const margin = { top: 32, right: 16, bottom: 60, left: 56 };
const width = 1088, height = 480;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

// compute running positions
let running = 0;
const bars = data.map((d, i) => {
  if (d.type === "total") {
    const b = { ...d, y0: 0, y1: d.value };
    running = d.value;
    return b;
  } else {
    const b = { ...d, y0: running, y1: running + d.value };
    running += d.value;
    return b;
  }
});

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleBand()
  .domain(data.map(d => d.label))
  .range([0, innerW])
  .padding(0.32);

const yMax = d3.max(bars, d => Math.max(d.y0, d.y1));
const yMin = Math.min(0, d3.min(bars, d => Math.min(d.y0, d.y1)));
const y = d3.scaleLinear()
  .domain([yMin, yMax * 1.08]).nice()
  .range([innerH, 0]);

// grid
g.append("g").attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// bars
g.selectAll(".bar")
  .data(bars).join("rect")
    .attr("class", "bar")
    .attr("x", d => x(d.label))
    .attr("y", d => y(Math.max(d.y0, d.y1)))
    .attr("width", x.bandwidth())
    .attr("height", d => Math.abs(y(d.y0) - y(d.y1)))
    .attr("fill", d =>
      d.type === "total" ? "var(--accent)" :
      d.value >= 0 ? "var(--pos)" : "var(--neg)"
    );

// connector lines
g.selectAll(".connector")
  .data(bars.slice(0, -1)).join("line")
    .attr("class", "connector")
    .attr("x1", (d, i) => x(d.label) + x.bandwidth())
    .attr("x2", (d, i) => x(bars[i+1].label))
    .attr("y1", d => y(d.y1))
    .attr("y2", d => y(d.y1))
    .attr("stroke", "var(--hairline)")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "2 3");

// labels above each bar
g.selectAll(".label")
  .data(bars).join("text")
    .attr("class", "data-label")
    .attr("x", d => x(d.label) + x.bandwidth() / 2)
    .attr("y", d => y(Math.max(d.y0, d.y1)) - 6)
    .attr("text-anchor", "middle")
    .text(d => d.type === "total"
      ? d3.format(",")(Math.round(d.value))
      : d3.format("+,")(d.value));

// x axis with rotated labels if needed
g.append("g")
  .attr("class", "axis")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x))
  .selectAll("text")
    .attr("transform", "rotate(-20)")
    .style("text-anchor", "end");

// y axis
g.append("g")
  .attr("class", "axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d3.format(",")));
```

## Variants

- **Vertical column waterfall** (above) for revenue/EBITDA YoY — default
- **Horizontal bar waterfall** for FCF bridge from EBITDA down to FCF — readers track top-to-bottom easier
- **Stacked waterfall** when each delta has sub-components (e.g. Price × Volume → split each into segments) — use sparingly; readability degrades

## Gotchas

- **Don't reorder bars** to make the story "look better". Order by chronology or by user-stated business logic, not by impact magnitude.
- **Always include the start total and end total** as bars — without them the chart is just a column chart of deltas.
- **Show signs**: `+850`, `-210`. The reader's eye should not have to compute.
- **Sum check**: assert that start + Σdeltas = end. If they don't match, the user gave you bad data — flag it; don't silently fudge.
- **Don't use this for >10 line items**. Group small contributions into "Other" with a footnote.

---

## Interactive variant — hover for exact values + drill-down on grouped bars

Hover any bar for the exact contribution and its share of the total delta. If a bar represents a grouped "Other" or aggregated category, click it to drill into sub-components.

### Required input (optional sub-components)

```js
const data = [
  { label: "FY24 Revenue",   value: 28400, type: "total"  },
  { label: "Price",          value:  +850, type: "delta"  },
  { label: "Volume",         value: +1320, type: "delta"  },
  {
    label: "Geographic mix", value:  -210, type: "delta",
    subComponents: [        // optional — enables drill-down
      { label: "Americas",   value: +180 },
      { label: "EMEA",       value: -290 },
      { label: "APAC",       value: -100 },
    ]
  },
  { label: "FX",             value:  -640, type: "delta"  },
  { label: "FY25 Revenue",   value: 30200, type: "total"  },
];
```

### Controls

```html
<div class="controls">
  <span class="controls-label" id="drill-status" style="margin-right:auto;">Hover for detail. Click a grouped bar to drill in.</span>
  <button class="btn" id="back-btn" style="display:none;" onclick="exitDrill()">← Back</button>
</div>
<div id="chart"></div>
```

### Core template

```js
let view = data;
let drilling = null;

const margin = { top: 32, right: 16, bottom: 60, left: 56 };
const width = 1088, height = 480;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

function computeBars(arr) {
  let running = 0;
  return arr.map(d => {
    if (d.type === "total") {
      const b = { ...d, y0: 0, y1: d.value };
      running = d.value;
      return b;
    } else {
      const b = { ...d, y0: running, y1: running + d.value };
      running += d.value;
      return b;
    }
  });
}

function redraw() {
  g.selectAll("*").remove();

  const bars = computeBars(view);
  const totalDelta = bars.filter(b => b.type === "delta").reduce((a,b) => a + b.value, 0);

  const x = d3.scaleBand()
    .domain(view.map(d => d.label))
    .range([0, innerW]).padding(0.32);

  const yMax = d3.max(bars, d => Math.max(d.y0, d.y1));
  const yMin = Math.min(0, d3.min(bars, d => Math.min(d.y0, d.y1)));
  const y = d3.scaleLinear().domain([yMin, yMax * 1.08]).nice().range([innerH, 0]);

  g.append("g").attr("class","grid")
    .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

  g.selectAll(".bar").data(bars).join("rect")
    .attr("class","bar")
    .attr("x", d => x(d.label))
    .attr("y", d => y(Math.max(d.y0, d.y1)))
    .attr("width", x.bandwidth())
    .attr("height", d => Math.abs(y(d.y0) - y(d.y1)))
    .attr("fill", d =>
      d.type === "total" ? "var(--accent)"
      : d.value >= 0 ? "var(--pos)" : "var(--neg)")
    .style("cursor", d => d.subComponents ? "pointer" : "default")
    .style("stroke", d => d.subComponents ? "var(--highlight)" : "none")
    .style("stroke-width", d => d.subComponents ? 1.5 : 0)
    .style("stroke-dasharray", d => d.subComponents ? "3 3" : "none")
    .on("mouseover", function(evt, d) {
      d3.select(this).attr("opacity", 0.85);
      const share = d.type === "delta" && totalDelta !== 0
        ? d3.format("+.1%")(d.value / totalDelta) : "";
      showTip(
        `<b>${d.label}</b><br>
         <span class="num">${d.type === "delta" ? d3.format("+,")(d.value) : d3.format(",")(d.value)}</span>
         ${share ? `<br><span style="color:var(--neutral);font-size:10.5px;">${share} of net change</span>` : ""}
         ${d.subComponents ? `<br><i style="color:var(--highlight-soft);font-size:10.5px;">Click to drill in</i>` : ""}`,
        evt);
    })
    .on("mouseout", function() { d3.select(this).attr("opacity", 1); hideTip(); })
    .on("click", function(evt, d) {
      if (d.subComponents) enterDrill(d);
    });

  g.selectAll(".connector").data(bars.slice(0, -1)).join("line")
    .attr("class","connector")
    .attr("x1", (d) => x(d.label) + x.bandwidth())
    .attr("x2", (d, i) => x(bars[i+1].label))
    .attr("y1", d => y(d.y1)).attr("y2", d => y(d.y1))
    .attr("stroke","var(--hairline)").attr("stroke-width", 1)
    .attr("stroke-dasharray","2 3");

  g.selectAll(".label").data(bars).join("text")
    .attr("class","data-label")
    .attr("x", d => x(d.label) + x.bandwidth()/2)
    .attr("y", d => y(Math.max(d.y0, d.y1)) - 6)
    .attr("text-anchor","middle")
    .text(d => d.type === "total"
      ? d3.format(",")(Math.round(d.value))
      : d3.format("+,")(d.value));

  g.append("g").attr("class","axis")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
      .attr("transform","rotate(-20)")
      .style("text-anchor","end");

  g.append("g").attr("class","axis axis-num")
    .call(d3.axisLeft(y).tickFormat(d3.format(",")));
}

function enterDrill(item) {
  drilling = item;
  // Build a mini-bridge for the sub-components, with start = 0 and total = item.value
  const subBars = [
    { label: `${item.label} →`, value: 0, type: "total" },
    ...item.subComponents.map(s => ({ ...s, type: "delta" })),
    { label: `Net: ${item.label}`, value: item.value, type: "total" },
  ];
  view = subBars;
  document.getElementById("back-btn").style.display = "";
  document.getElementById("drill-status").textContent = `Drilling into: ${item.label}`;
  redraw();
}

function exitDrill() {
  drilling = null;
  view = data;
  document.getElementById("back-btn").style.display = "none";
  document.getElementById("drill-status").textContent = "Hover for detail. Click a grouped bar to drill in.";
  redraw();
}

redraw();
```

### Interactive gotchas

- **Visual affordance for drillable bars** — dashed `--highlight` border so the user knows "this one's clickable" without instructions.
- **"Share of net change"** in the tooltip is the most useful derived value — turns absolute numbers into intuition: "Volume contributed 60% of the YoY growth".
- **Drill view shows a mini-bridge** with start at 0, sub-deltas, and ending total matching the parent — preserves the bridge metaphor at every level.
- **Don't auto-zoom into drill** — keep the same y-scale conventions so users don't get disoriented. Use the "Back" button to return.
