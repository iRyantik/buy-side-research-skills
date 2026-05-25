# Sensitivity heatmap

Two-way scenario table for DCF, M&A returns, breakeven analysis — shows how an output (price target, IRR, equity value) responds to two inputs (e.g. terminal growth × WACC, multiple × EBITDA).

## When to use

User asks: "DCF sensitivity", "two-way table", "what if growth is X and margin is Y", "scenario grid", "matrix of outcomes". Classic 7×7 or 9×9 grid.

## Required inputs

```js
const xVar = { label: "Terminal growth", values: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], unit: "%" };
const yVar = { label: "WACC",            values: [10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0], unit: "%" };
// matrix[yIdx][xIdx] = output value
const matrix = [
  [85, 92, 101, 112, 126, 145, 170],
  [92, 100, 109, 121, 137, 158, 188],
  [99, 108, 119, 132, 150, 175, 211],
  [107, 117, 130, 145, 166, 195, 240],   // base case row
  [115, 127, 142, 161, 186, 222, 280],
  [125, 139, 156, 178, 209, 254, 333],
  [136, 153, 174, 200, 239, 296, 409],
];
const focal = { yIdx: 3, xIdx: 3 };   // base case to highlight
const currentPrice = 124;             // optional, draws a contour
```

Y axis values usually go **highest at top** so that "more conservative" (higher WACC, lower growth) is upper-left. Stick to convention.

## Visual structure

- Heatmap rectangle, x cols × y rows
- Color: diverging from `--neg-soft` (low) through `--paper` (median or current price) to `--pos-soft` (high)
- Cell labels: mono tabular-nums, sized to fit
- Focal cell: bold border in `--ink`
- Optional: contour line where output equals current price (the "break-even" curve)

## Core template

```js
const cellW = 90, cellH = 38;
const margin = { top: 64, right: 24, bottom: 32, left: 96 };
const width = margin.left + cellW * xVar.values.length + margin.right;
const height = margin.top + cellH * yVar.values.length + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const flat = matrix.flat();
const mid = currentPrice ?? d3.median(flat);
const color = d3.scaleDiverging()
  .domain([d3.min(flat), mid, d3.max(flat)])
  .interpolator(t => d3.interpolate("#D4A5A5", "#A8C4B0")(t));   // neg-soft → pos-soft
// For more nuance:
const lin = d3.scaleLinear()
  .domain([d3.min(flat), mid, d3.max(flat)])
  .range(["#D4A5A5", "#FAFAF7", "#A8C4B0"])
  .interpolate(d3.interpolateRgb);

// cells
matrix.forEach((row, yi) => {
  row.forEach((v, xi) => {
    g.append("rect")
      .attr("x", xi * cellW)
      .attr("y", yi * cellH)
      .attr("width", cellW)
      .attr("height", cellH)
      .attr("fill", lin(v))
      .attr("stroke", "#FFF")
      .attr("stroke-width", 1);

    g.append("text")
      .attr("class", "data-label")
      .attr("x", xi * cellW + cellW / 2)
      .attr("y", yi * cellH + cellH / 2 + 4)
      .attr("text-anchor", "middle")
      .text(d3.format(",")(v));
  });
});

// focal cell border
if (focal) {
  g.append("rect")
    .attr("x", focal.xIdx * cellW)
    .attr("y", focal.yIdx * cellH)
    .attr("width", cellW)
    .attr("height", cellH)
    .attr("fill", "none")
    .attr("stroke", "var(--ink)")
    .attr("stroke-width", 2);
}

// x axis labels (top)
xVar.values.forEach((v, xi) => {
  g.append("text")
    .attr("class", "axis-label")
    .attr("x", xi * cellW + cellW / 2)
    .attr("y", -12)
    .attr("text-anchor", "middle")
    .text(v + xVar.unit);
});
g.append("text")
  .attr("class", "axis-label")
  .attr("x", (xVar.values.length * cellW) / 2)
  .attr("y", -32)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(xVar.label + " →");

// y axis labels (left)
yVar.values.forEach((v, yi) => {
  g.append("text")
    .attr("class", "axis-label")
    .attr("x", -10)
    .attr("y", yi * cellH + cellH / 2 + 4)
    .attr("text-anchor", "end")
    .text(v + yVar.unit);
});
g.append("text")
  .attr("class", "axis-label")
  .attr("transform", `translate(${-margin.left + 16}, ${(yVar.values.length * cellH)/2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(yVar.label + " →");
```

## Variants

- **Implied upside heatmap**: color by `(value / currentPrice - 1)` instead of absolute value. Diverging at 0% upside.
- **Probability-weighted**: overlay scenario probabilities (e.g. bull/base/bear) as small annotations on the cells.
- **Contour line at break-even**: draw a polyline through cells whose value crosses `currentPrice`. Tells you the input combinations that imply fair value.

## Gotchas

- **Y axis order**: highest WACC (most conservative) at top. Stick to convention or readers will get disoriented.
- **Don't use too many cells**. 7×7 is comfortable; 11×11 is the absolute max for a memo column.
- **Color should serve readability**, not aesthetics. If the eye is drawn to the wrong cell, the diverging midpoint is mis-set.
- **Always show the focal cell** (base case) with a bold border. The reader needs an anchor.
- **State the unit clearly** in the subtitle: "DCF-implied price per share, USD" — not just "DCF output".

---

## Interactive variant — clickable cells + display mode toggle

Three interactive layers, each adds value:

1. **Hover any cell** → tooltip with exact value, upside vs current price, and the cell's (x, y) inputs
2. **Click a cell** → moves the focal anchor to that cell (rebases the upside calculation)
3. **Display mode toggle** → switch the displayed values and colors between (a) absolute output, (b) upside vs current price, (c) upside vs clicked focal cell

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Show</span>
    <div class="pills" id="mode-pills">
      <span class="pill active" data-mode="absolute">Absolute</span>
      <span class="pill" data-mode="vs-current">Upside vs current</span>
      <span class="pill" data-mode="vs-focal">Upside vs focal cell</span>
    </div>
  </div>
  <button class="btn" onclick="resetFocal()">Reset focal</button>
</div>

<div id="chart"></div>
<p id="cell-detail" class="callout" style="margin-top:8px;"></p>
```

### Core template

```js
// xVar = {label, values, unit}, yVar = {label, values, unit}, matrix[y][x], focal={yIdx,xIdx}, currentPrice
let mode = "absolute";              // "absolute" | "vs-current" | "vs-focal"
let userFocal = { ...focal };       // mutable focal; user clicks change it

const cellW = 90, cellH = 38;
const margin = { top: 64, right: 24, bottom: 32, left: 96 };
const width  = margin.left + cellW * xVar.values.length + margin.right;
const height = margin.top + cellH * yVar.values.length + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Flatten for scales
const flat = matrix.flat();
const detailEl = document.getElementById("cell-detail");

function getDisplayValue(v) {
  if (mode === "absolute") return v;
  if (mode === "vs-current") return v / currentPrice - 1;
  if (mode === "vs-focal") return v / matrix[userFocal.yIdx][userFocal.xIdx] - 1;
}
function getColorScale() {
  if (mode === "absolute") {
    const mid = currentPrice;
    return d3.scaleLinear()
      .domain([d3.min(flat), mid, d3.max(flat)])
      .range(["#D4A5A5","#F4F3EE","#A8C4B0"])
      .interpolate(d3.interpolateRgb);
  } else {
    // Diverging at 0% upside
    const upsides = flat.map(v => mode === "vs-current" ? (v/currentPrice - 1)
                                                         : (v/matrix[userFocal.yIdx][userFocal.xIdx] - 1));
    const maxAbs = d3.max(upsides.map(Math.abs));
    return d3.scaleLinear()
      .domain([-maxAbs, 0, maxAbs])
      .range(["#8B2635", "#F4F3EE", "#2D5F3F"])
      .interpolate(d3.interpolateRgb);
  }
}
function fmtCell(v) {
  return mode === "absolute" ? d3.format(",")(v) : d3.format("+.1%")(v);
}

// ── Build cells once, update on mode/focal change ─────────────
const cellG = g.append("g");
matrix.forEach((row, yi) => {
  row.forEach((v, xi) => {
    const cellGroup = cellG.append("g")
      .attr("class", "cell")
      .attr("transform", `translate(${xi*cellW},${yi*cellH})`)
      .style("cursor", "pointer")
      .on("mouseover", (evt) => {
        const dv = getDisplayValue(v);
        showTip(
          `<b>${yVar.label}</b>: <span class="num">${yVar.values[yi]}${yVar.unit||""}</span><br>
           <b>${xVar.label}</b>: <span class="num">${xVar.values[xi]}${xVar.unit||""}</span><br>
           <b>Output</b>: <span class="num">${d3.format(",")(v)}</span>
           ${currentPrice ? `<br>vs current: <span class="num">${d3.format("+.1%")(v/currentPrice - 1)}</span>` : ""}`,
          evt
        );
      })
      .on("mouseout", hideTip)
      .on("click", () => {
        userFocal = { yIdx: yi, xIdx: xi };
        detailEl.textContent = `Focal moved to ${yVar.label} = ${yVar.values[yi]}${yVar.unit||""}, ${xVar.label} = ${xVar.values[xi]}${xVar.unit||""}. Output ${d3.format(",")(v)}.`;
        redraw();
      });

    cellGroup.append("rect")
      .attr("class", "cell-rect")
      .attr("width", cellW).attr("height", cellH)
      .attr("stroke", "#FFF").attr("stroke-width", 1);

    cellGroup.append("text")
      .attr("class", "cell-label data-label")
      .attr("x", cellW/2).attr("y", cellH/2 + 4)
      .attr("text-anchor", "middle");
  });
});

// Focal border (single rect, repositioned)
const focalBorder = g.append("rect")
  .attr("class", "focal-border")
  .attr("width", cellW).attr("height", cellH)
  .attr("fill", "none")
  .attr("stroke", "var(--ink)").attr("stroke-width", 2)
  .attr("pointer-events", "none");

// ── X axis labels (top) ───────────────────────────────────────
xVar.values.forEach((v, xi) => {
  g.append("text")
    .attr("class", "axis-label")
    .attr("x", xi*cellW + cellW/2).attr("y", -12)
    .attr("text-anchor", "middle")
    .text(v + (xVar.unit||""));
});
g.append("text")
  .attr("class", "axis-label")
  .attr("x", (xVar.values.length * cellW)/2).attr("y", -32)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(xVar.label + " →");

// ── Y axis labels (left) ──────────────────────────────────────
yVar.values.forEach((v, yi) => {
  g.append("text")
    .attr("class", "axis-label")
    .attr("x", -10).attr("y", yi*cellH + cellH/2 + 4)
    .attr("text-anchor", "end")
    .text(v + (yVar.unit||""));
});
g.append("text")
  .attr("class", "axis-label")
  .attr("transform", `translate(${-margin.left+16}, ${(yVar.values.length*cellH)/2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("font-weight", 600)
  .text(yVar.label + " →");

// ── Redraw on mode / focal change ─────────────────────────────
function redraw() {
  const color = getColorScale();
  const upsidesNow = flat.map(v => getDisplayValue(v));
  const maxAbs = d3.max(upsidesNow.map(v => Math.abs(typeof v === "number" ? v : 0)));

  cellG.selectAll(".cell-rect")
    .data(flat)
    .attr("fill", (d, i) => {
      const dv = getDisplayValue(d);
      return color(dv);
    });

  cellG.selectAll(".cell-label")
    .data(flat)
    .text(d => fmtCell(getDisplayValue(d)))
    .attr("fill", (d, i) => {
      const dv = getDisplayValue(d);
      const intensity = mode === "absolute"
        ? Math.abs(d - d3.median(flat)) / (d3.max(flat) - d3.min(flat))
        : Math.abs(dv) / maxAbs;
      return intensity > 0.45 ? "#FFF" : "var(--ink)";
    });

  // Position focal border
  focalBorder
    .attr("transform", `translate(${userFocal.xIdx*cellW},${userFocal.yIdx*cellH})`);
}

function resetFocal() {
  userFocal = { ...focal };
  detailEl.textContent = "";
  redraw();
}

// ── Mode pills ────────────────────────────────────────────────
document.querySelectorAll("#mode-pills .pill").forEach(p => {
  p.addEventListener("click", () => {
    document.querySelectorAll("#mode-pills .pill").forEach(x => x.classList.remove("active"));
    p.classList.add("active");
    mode = p.dataset.mode;
    redraw();
  });
});

redraw();
```

### Interactive gotchas

- **Mode toggle should change BOTH color and label** — readers expect the colors to mean what the labels say. Don't show absolute values with upside-colored cells.
- **The diverging midpoint shifts** between modes (in absolute mode it's `currentPrice` or median; in upside modes it's 0). This is correct behavior — but include a tiny legend showing where the midpoint sits in each mode.
- **Click feedback** — when the user clicks a new focal cell, briefly flash the border or fade-in animation so the click registers. ~150ms transition is enough.
- **Save focal cell in URL hash** if you want shareable scenarios: `#focal=3,3` — parse on load.
- **Don't let users break the chart** with extreme focal cells — if the focal cell's value is very small, "vs focal" upsides explode. Display capped at ±200% and label cells beyond as "+200%+".
