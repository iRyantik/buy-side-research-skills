# Multi-panel cycle chart

The Bernstein / Empirical Research-style chart: price on top, valuation multiple in the middle, fundamentals (EPS, revenue, margin) on the bottom — all sharing one time axis. Answers: was the rerating driven by multiple expansion or by fundamentals catching up?

## When to use

User asks: "is it multiple or fundamentals", "price vs EPS vs multiple", "rerating analysis", "track the resonance", "what's been driving the stock", "decompose the return". Three or four stacked panels with a shared x-axis.

## Required inputs

Same date range across all panels, monthly or quarterly:
```js
const data = [
  { date: "2018-12-31", price: 184, peFwd: 16.2, eps: 11.35, margin: 0.215 },
  { date: "2019-12-31", price: 219, peFwd: 17.8, eps: 12.30, margin: 0.232 },
  // ...
  { date: "2026-03-31", price: 412, peFwd: 22.0, eps: 18.75, margin: 0.281 },
];
```

The user picks which 3–4 series to stack. Default: price, forward PE, EPS (with optional 4th panel: gross margin or revenue growth YoY).

## Visual structure

Vertical stack of panels, each ~140px tall, shared x-axis at the bottom. Each panel has:
- A small label on the top-left (panel title in small caps)
- The data line in `--accent`
- Optionally a band (e.g. ±1σ on the multiple panel)
- Minimal y-axis (3–4 ticks)
- A focal dot on the rightmost point, labeled

## Core template

```js
const panels = [
  { key: "price",  label: "Price",                  fmt: d => "$" + d3.format(",")(d), band: false },
  { key: "peFwd",  label: "Fwd PE",                 fmt: d => d.toFixed(1) + "x",       band: true  },
  { key: "eps",    label: "Fwd EPS",                fmt: d => "$" + d.toFixed(2),        band: false },
  { key: "margin", label: "Gross margin",           fmt: d3.format(".1%"),                band: false },
];

const margin = { top: 24, right: 80, bottom: 32, left: 56 };
const panelH = 130;
const panelGap = 22;
const width = 1088;
const innerW = width - margin.left - margin.right;
const height = margin.top + panels.length * (panelH + panelGap) + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);

const x = d3.scaleTime()
  .domain(d3.extent(data, d => new Date(d.date)))
  .range([0, innerW]);

panels.forEach((p, i) => {
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top + i*(panelH+panelGap)})`);

  const y = d3.scaleLinear()
    .domain(d3.extent(data, d => d[p.key])).nice()
    .range([panelH, 0]);

  // band: ±1σ around mean (only on multiple panel by default)
  if (p.band) {
    const m = d3.mean(data, d => d[p.key]);
    const s = d3.deviation(data, d => d[p.key]);
    g.append("rect")
      .attr("x", 0).attr("y", y(m + s))
      .attr("width", innerW).attr("height", y(m - s) - y(m + s))
      .attr("fill", "var(--accent-ghost)").attr("opacity", 0.5);
    g.append("line")
      .attr("x1", 0).attr("x2", innerW)
      .attr("y1", y(m)).attr("y2", y(m))
      .attr("stroke", "var(--ink-2)").attr("stroke-dasharray", "2 3");
  }

  // grid (horizontal only)
  g.append("g").attr("class","grid")
    .call(d3.axisLeft(y).ticks(3).tickSize(-innerW).tickFormat(""));

  // the line
  const line = d3.line()
    .x(d => x(new Date(d.date)))
    .y(d => y(d[p.key]))
    .curve(d3.curveMonotoneX);
  g.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "var(--accent)")
    .attr("stroke-width", 1.5)
    .attr("d", line);

  // focal dot at the most recent point
  const last = data[data.length - 1];
  g.append("circle")
    .attr("class", "focal")
    .attr("cx", x(new Date(last.date)))
    .attr("cy", y(last[p.key]))
    .attr("r", 4);
  g.append("text")
    .attr("class", "data-label")
    .attr("x", innerW + 6)
    .attr("y", y(last[p.key]) + 4)
    .attr("fill", "var(--highlight)")
    .text(p.fmt(last[p.key]));

  // panel y-axis (sparse)
  g.append("g")
    .attr("class", "axis axis-num")
    .call(d3.axisLeft(y).ticks(3).tickFormat(p.fmt));

  // panel label (top-left, small caps)
  g.append("text")
    .attr("x", 0).attr("y", -8)
    .attr("font-family", "var(--font-sans)")
    .attr("font-size", 10)
    .attr("font-weight", 600)
    .attr("letter-spacing", "0.08em")
    .attr("text-transform", "uppercase")
    .attr("fill", "var(--ink-3)")
    .text(p.label.toUpperCase());
});

// shared x-axis at the bottom
const xAxis = svg.append("g")
  .attr("class", "axis axis-num")
  .attr("transform", `translate(${margin.left},${margin.top + panels.length*(panelH+panelGap) - panelGap + 4})`)
  .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
```

## Variants

- **Index everything to 100 at the start date** in the top panel — makes "rerating" vs "fundamentals" visually crisp. Add a second line for "what price would be if multiple was constant" (= EPS × starting PE).
- **Add YoY% growth strip** at the bottom as a fourth panel, with positive bars in `--pos` and negative in `--neg`. Highlights cycle inflection points.
- **Two-stock comparison**: same panel structure but `--accent` for one, `--highlight` for the other. Maximum two — three lines become unreadable in stacked panels.

## Gotchas

- **Align x-axes precisely** — readers compare across panels by drawing a mental vertical line. If panels misalign, the chart is useless.
- **Don't share y-axis** across panels with different units. Each panel has its own y-axis.
- **Match the multiple to the EPS**: forward PE pairs with forward EPS, trailing pairs with trailing. Don't mix.
- **Subtitle must state the resonance question**: "Did the rerating come from earnings or from multiple expansion?" — that frames the chart for the reader.
- **Avoid >4 panels** — readers lose the thread. If you need more series, split into two charts.

---

## Interactive variant — synchronized crosshair across panels + brush-to-zoom

The killer feature of cycle charts. Hover anywhere — all panels show their value at the same date. Drag to select a date range, all panels rescale simultaneously. This is the analytical move: "was the rerating concurrent with EPS expansion or did multiple expansion lead?"

### Controls

```html
<div class="controls">
  <span class="controls-label">Drag any panel to zoom · Double-click to reset</span>
  <button class="btn" onclick="resetZoom()">Reset</button>
</div>
<div id="chart"></div>
<div id="readout" style="font-family:var(--font-mono);font-size:11px;font-variant-numeric:tabular-nums;color:var(--ink-2);margin-top:6px;display:flex;gap:18px;flex-wrap:wrap;"></div>
```

### Core template

```js
// data, panels — same shape as static
let view = { x0: d3.min(data, d=>new Date(d.date)), x1: d3.max(data, d=>new Date(d.date)) };

const margin = { top: 24, right: 80, bottom: 32, left: 56 };
const panelH = 130, panelGap = 22;
const width = 1088;
const innerW = width - margin.left - margin.right;
const height = margin.top + panels.length * (panelH + panelGap) + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);

const x = d3.scaleTime().range([0, innerW]);

const panelStates = panels.map((p, i) => {
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top + i*(panelH+panelGap)})`);
  const y = d3.scaleLinear().range([panelH, 0]);

  // Layers
  const bandG = g.append("rect").attr("fill","var(--accent-ghost)").attr("opacity",0.5);
  const meanLineG = g.append("line")
    .attr("stroke","var(--ink-2)").attr("stroke-dasharray","2 3");
  const gridG = g.append("g").attr("class","grid");
  const linePath = g.append("path")
    .attr("fill","none").attr("stroke","var(--accent)").attr("stroke-width",1.5);
  const focalDot = g.append("circle").attr("class","focal").attr("r",4);
  const focalLabel = g.append("text").attr("class","data-label")
    .attr("fill","var(--highlight)");
  const yAxisG = g.append("g").attr("class","axis axis-num");
  const panelLabel = g.append("text")
    .attr("x",0).attr("y",-8)
    .attr("font-family","var(--font-sans)").attr("font-size",10)
    .attr("font-weight",600).attr("letter-spacing","0.08em")
    .attr("text-transform","uppercase").attr("fill","var(--ink-3)")
    .text(p.label.toUpperCase());

  // Crosshair (per panel, but synchronized via shared x)
  const ch = g.append("g").style("display","none").style("pointer-events","none");
  ch.append("line").attr("class","crosshair").attr("y1",0).attr("y2",panelH);
  const chDot = ch.append("circle").attr("r",3.5)
    .attr("fill","var(--paper)").attr("stroke","var(--highlight)").attr("stroke-width",1.5);

  return { g, y, bandG, meanLineG, gridG, linePath, focalDot, focalLabel,
           yAxisG, ch, chDot, panel: p };
});

const sharedXAxisG = svg.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(${margin.left},${margin.top + panels.length*(panelH+panelGap) - panelGap + 4})`);

function redraw() {
  const visible = data.filter(d => new Date(d.date) >= view.x0 && new Date(d.date) <= view.x1);
  x.domain([view.x0, view.x1]);

  panelStates.forEach(ps => {
    const p = ps.panel;
    ps.y.domain(d3.extent(visible, d => d[p.key])).nice();
    ps.gridG.call(d3.axisLeft(ps.y).ticks(3).tickSize(-innerW).tickFormat(""));

    if (p.band) {
      const m = d3.mean(visible, d => d[p.key]);
      const s = d3.deviation(visible, d => d[p.key]);
      ps.bandG.attr("x",0).attr("y",ps.y(m+s))
              .attr("width",innerW).attr("height", ps.y(m-s) - ps.y(m+s));
      ps.meanLineG.attr("x1",0).attr("x2",innerW)
                  .attr("y1",ps.y(m)).attr("y2",ps.y(m));
    } else {
      ps.bandG.attr("width",0).attr("height",0);
      ps.meanLineG.attr("x1",0).attr("x2",0);
    }

    const line = d3.line()
      .x(d => x(new Date(d.date))).y(d => ps.y(d[p.key]))
      .curve(d3.curveMonotoneX);
    ps.linePath.datum(visible).attr("d", line);

    const last = visible[visible.length-1];
    ps.focalDot.attr("cx", x(new Date(last.date))).attr("cy", ps.y(last[p.key]));
    ps.focalLabel.attr("x", innerW + 6).attr("y", ps.y(last[p.key]) + 4)
      .text(p.fmt(last[p.key]));

    ps.yAxisG.call(d3.axisLeft(ps.y).ticks(3).tickFormat(p.fmt));
  });

  sharedXAxisG.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
}
redraw();

// ── Shared crosshair + brush overlay ──────────────────────────
const readout = document.getElementById("readout");
const bisect = d3.bisector(d => new Date(d.date)).left;

function moveCrosshair(date) {
  const visible = data.filter(d => new Date(d.date) >= view.x0 && new Date(d.date) <= view.x1);
  const i = Math.min(visible.length-1, Math.max(0, bisect(visible, date)));
  const d = visible[i];
  const sx = x(new Date(d.date));

  panelStates.forEach(ps => {
    const sy = ps.y(d[ps.panel.key]);
    ps.ch.style("display", null);
    ps.ch.select("line").attr("x1", sx).attr("x2", sx);
    ps.chDot.attr("cx", sx).attr("cy", sy);
  });

  readout.innerHTML = [
    `<span style="color:var(--ink-3);">${d3.timeFormat("%d %b %Y")(new Date(d.date))}</span>`,
    ...panels.map(p => `<span>${p.label}: <b>${p.fmt(d[p.key])}</b></span>`)
  ].join("&nbsp;&nbsp;&middot;&nbsp;&nbsp;");
}

function hideCrosshair() {
  panelStates.forEach(ps => ps.ch.style("display", "none"));
  readout.innerHTML = "";
}

// Per-panel brush overlays (any panel can initiate zoom)
panelStates.forEach((ps, idx) => {
  const brush = d3.brushX()
    .extent([[0,0],[innerW, panelH]])
    .on("brush", ({selection, sourceEvent}) => {
      // hide crosshair while brushing
      if (selection) hideCrosshair();
    })
    .on("end", ({selection}) => {
      if (selection) {
        view = { x0: x.invert(selection[0]), x1: x.invert(selection[1]) };
        panelStates.forEach(p => p.g.select(".brush").call(brush.move, null));
        redraw();
      }
    });

  const brushG = ps.g.append("g").attr("class","brush").call(brush);

  brushG.selectAll(".overlay")
    .on("mousemove.crosshair", function(evt) {
      const mx = d3.pointer(evt, this)[0];
      moveCrosshair(x.invert(mx));
    })
    .on("mouseleave.crosshair", hideCrosshair)
    .on("dblclick.reset", () => resetZoom());
});

function resetZoom() {
  view = { x0: d3.min(data, d=>new Date(d.date)), x1: d3.max(data, d=>new Date(d.date)) };
  redraw();
}
```

### Interactive gotchas

- **All panels must share the same x scale instance** — that's how the crosshair stays aligned. If you create per-panel x scales, they'll drift on zoom.
- **Brush on any panel zooms ALL panels** — that's the point. Don't make brush per-panel-independent; the whole chart's argument depends on synchronized x.
- **Hide crosshair while brushing** — otherwise the visual is chaotic. Show it again on mouseleave from brush.
- **Readout strip** below the chart is the punchline — it lets the reader see all 4 panel values at the same date at a glance, which is exactly the question this chart is built to answer.
- **Y axes update on zoom** to fit the visible range — this is correct for showing relative moves within a sub-period. Mention this in the subtitle: "y-axes auto-scale to visible range".
