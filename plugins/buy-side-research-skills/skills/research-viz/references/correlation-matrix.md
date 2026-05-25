# Correlation matrix

A symmetric heatmap of pairwise correlations across a set of stocks, factors, or sectors. Diagonal is 1.0; off-diagonal is the correlation coefficient.

## When to use

User asks: "pairwise correlation", "factor exposure heatmap", "how correlated", "rolling correlation snapshot", "matrix of stock pairs". Common uses: book-level risk view, pair trade setup, factor concentration check.

## Required inputs

```js
const labels = ["AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "TSLA"];
// symmetric matrix, diagonal = 1
const matrix = [
  [1.00, 0.72, 0.68, 0.61, 0.59, 0.55, 0.38],
  [0.72, 1.00, 0.71, 0.64, 0.62, 0.57, 0.36],
  [0.68, 0.71, 1.00, 0.69, 0.55, 0.51, 0.34],
  [0.61, 0.64, 0.69, 1.00, 0.58, 0.50, 0.31],
  [0.59, 0.62, 0.55, 0.58, 1.00, 0.48, 0.35],
  [0.55, 0.57, 0.51, 0.50, 0.48, 1.00, 0.42],
  [0.38, 0.36, 0.34, 0.31, 0.35, 0.42, 1.00],
];
const period = "1Y daily returns, ending Mar 2026";
```

State the period and frequency in the subtitle — "1Y daily returns" vs "5Y monthly returns" produce very different numbers.

## Visual structure

- Square heatmap, N×N
- Diverging color scale: `--neg-soft` (−1) through `--paper-edge` (0) through `--accent` (+1)
- Cell values overlaid in mono tabular-nums (only if N ≤ 12 — past that, labels become unreadable, drop them)
- Row labels left, column labels top (rotated 45°) — use ticker codes
- Diagonal: filled but unlabeled (always 1.00)

## Core template

```js
const N = labels.length;
const cellSize = Math.min(560 / N, 64);   // shrink for large matrices
const margin = { top: 80, right: 32, bottom: 24, left: 80 };
const width = margin.left + cellSize * N + margin.right;
const height = margin.top + cellSize * N + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// diverging color: -1 (--neg-soft) → 0 (--paper-edge) → +1 (--accent)
const color = d3.scaleLinear()
  .domain([-1, 0, 1])
  .range(["#D4A5A5", "#F4F3EE", "#1F3A5F"])
  .interpolate(d3.interpolateRgb);

// cells
matrix.forEach((row, i) => {
  row.forEach((v, j) => {
    g.append("rect")
      .attr("x", j * cellSize).attr("y", i * cellSize)
      .attr("width", cellSize).attr("height", cellSize)
      .attr("fill", color(v))
      .attr("stroke", "#FFF").attr("stroke-width", 1);

    // label only if cell is large enough and not on diagonal
    if (N <= 12 && i !== j) {
      g.append("text")
        .attr("class", "data-label")
        .attr("x", j * cellSize + cellSize/2)
        .attr("y", i * cellSize + cellSize/2 + 4)
        .attr("text-anchor", "middle")
        .attr("font-size", N > 8 ? 9 : 11)
        .attr("fill", Math.abs(v) > 0.6 ? "#FFF" : "var(--ink)")
        .text(v.toFixed(2));
    }
  });
});

// row labels
labels.forEach((lab, i) => {
  g.append("text")
    .attr("x", -8).attr("y", i * cellSize + cellSize/2 + 4)
    .attr("text-anchor", "end")
    .attr("class", "axis-label")
    .attr("font-family", "var(--font-mono)")
    .text(lab);
});

// column labels (rotated)
labels.forEach((lab, j) => {
  g.append("text")
    .attr("transform", `translate(${j * cellSize + cellSize/2}, -8) rotate(-45)`)
    .attr("text-anchor", "start")
    .attr("class", "axis-label")
    .attr("font-family", "var(--font-mono)")
    .text(lab);
});

// color legend at bottom
const legendG = svg.append("g")
  .attr("transform", `translate(${margin.left}, ${margin.top + cellSize * N + 24})`);
const legendW = 200, legendH = 8;
const lg = legendG.append("defs").append("linearGradient")
  .attr("id", "corrgrad").attr("x1", "0").attr("x2", "1");
lg.append("stop").attr("offset", "0").attr("stop-color", "#D4A5A5");
lg.append("stop").attr("offset", "0.5").attr("stop-color", "#F4F3EE");
lg.append("stop").attr("offset", "1").attr("stop-color", "#1F3A5F");
legendG.append("rect").attr("width", legendW).attr("height", legendH).attr("fill", "url(#corrgrad)");
[-1, 0, 1].forEach((v, i) => {
  legendG.append("text").attr("x", i * legendW/2).attr("y", legendH + 14)
    .attr("text-anchor", "middle").attr("class","axis-label").text(v.toFixed(1));
});
```

## Variants

- **Triangular** — show only the lower (or upper) triangle since the matrix is symmetric. Cleaner for medium-to-large N.
- **Hierarchically clustered** — reorder rows/cols by similarity using `d3.cluster` or pre-computed dendrogram order. Reveals correlation blocks (e.g. mega-cap tech vs financials).
- **Rolling correlation strip** — instead of a matrix snapshot, plot 1 pair's rolling correlation over time. Different chart entirely; this lives in `cycle-multipanel.md` style.
- **Factor exposure variant**: rows = stocks, columns = factors (mkt, size, value, momentum, quality, low-vol). Not symmetric. Otherwise identical rendering.

## Gotchas

- **Symmetric → diagonal is 1.0** by construction. Make it visually distinct (label "—" or leave the cell empty) to remind the reader.
- **Avoid red/green correlation legends** — high correlation is not "good" or "bad"; it's just high. Use the diverging tones in the design tokens.
- **State period and frequency** in subtitle. A correlation of 0.7 over 1M daily ≠ 0.7 over 5Y monthly.
- **Cluster if N is large**. An unsorted 30×30 matrix is noise. Reorder by dendrogram so the structure is visible.
- **Don't over-interpret single cells** — bake the period and noise level into the source line so the reader doesn't false-precision the numbers.

---

## Interactive variant — hover cell + click row/col to highlight

Hover any cell for the exact correlation and labeled pair. Click a row or column label to highlight that asset's row + column (dims everything else). Click again to clear.

### Controls

```html
<div class="controls">
  <span class="controls-label">Click row or column label to highlight</span>
  <button class="btn" onclick="clearHighlight()">Clear</button>
</div>
<div id="chart"></div>
```

### Core template

```js
let highlighted = null;   // index of highlighted row/col

const N = labels.length;
const cellSize = Math.min(560 / N, 64);
const margin = { top: 80, right: 32, bottom: 24, left: 80 };
const width = margin.left + cellSize * N + margin.right;
const height = margin.top + cellSize * N + margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const color = d3.scaleLinear()
  .domain([-1, 0, 1])
  .range(["#D4A5A5","#F4F3EE","#1F3A5F"])
  .interpolate(d3.interpolateRgb);

matrix.forEach((row, i) => {
  row.forEach((v, j) => {
    g.append("rect")
      .attr("class", "corr-cell")
      .attr("data-i", i).attr("data-j", j)
      .attr("x", j*cellSize).attr("y", i*cellSize)
      .attr("width", cellSize).attr("height", cellSize)
      .attr("fill", color(v))
      .attr("stroke","#FFF").attr("stroke-width", 1)
      .style("cursor","pointer")
      .on("mouseover", function(evt) {
        if (i === j) {
          showTip(`<b>${labels[i]}</b><br>Self-correlation = 1.00`, evt);
        } else {
          showTip(
            `<b>${labels[i]} ↔ ${labels[j]}</b><br>
             Correlation: <span class="num">${v.toFixed(3)}</span>
             <br><span style="color:var(--neutral);font-size:10.5px;">${
               Math.abs(v) > 0.7 ? "Very strong" :
               Math.abs(v) > 0.4 ? "Moderate" :
               Math.abs(v) > 0.2 ? "Weak" : "Negligible"
             }</span>`,
            evt);
        }
      })
      .on("mouseout", hideTip);

    if (N <= 12 && i !== j) {
      g.append("text").attr("class","corr-label data-label")
        .attr("data-i", i).attr("data-j", j)
        .attr("x", j*cellSize + cellSize/2).attr("y", i*cellSize + cellSize/2 + 4)
        .attr("text-anchor","middle")
        .attr("font-size", N > 8 ? 9 : 11)
        .attr("fill", Math.abs(v) > 0.6 ? "#FFF" : "var(--ink)")
        .style("pointer-events","none")
        .text(v.toFixed(2));
    }
  });
});

// Row + column labels — clickable
labels.forEach((lab, i) => {
  g.append("text").attr("class","row-label")
    .attr("data-i", i)
    .attr("x", -8).attr("y", i*cellSize + cellSize/2 + 4)
    .attr("text-anchor","end").attr("class","axis-label row-label")
    .attr("font-family","var(--font-mono)")
    .style("cursor","pointer")
    .text(lab)
    .on("click", () => toggleHighlight(i));
});
labels.forEach((lab, j) => {
  g.append("text").attr("class","col-label")
    .attr("data-j", j)
    .attr("transform", `translate(${j*cellSize + cellSize/2}, -8) rotate(-45)`)
    .attr("text-anchor","start").attr("class","axis-label col-label")
    .attr("font-family","var(--font-mono)")
    .style("cursor","pointer")
    .text(lab)
    .on("click", () => toggleHighlight(j));
});

function toggleHighlight(idx) {
  highlighted = (highlighted === idx) ? null : idx;
  applyHighlight();
}
function clearHighlight() { highlighted = null; applyHighlight(); }

function applyHighlight() {
  g.selectAll(".corr-cell").attr("opacity", function() {
    if (highlighted === null) return 1;
    const i = +this.getAttribute("data-i"), j = +this.getAttribute("data-j");
    return (i === highlighted || j === highlighted) ? 1 : 0.18;
  });
  g.selectAll(".corr-label").attr("opacity", function() {
    if (highlighted === null) return 1;
    const i = +this.getAttribute("data-i"), j = +this.getAttribute("data-j");
    return (i === highlighted || j === highlighted) ? 1 : 0.18;
  });
  g.selectAll(".row-label").attr("font-weight", function() {
    return (+this.getAttribute("data-i") === highlighted) ? 600 : 400;
  }).attr("fill", function() {
    return (+this.getAttribute("data-i") === highlighted) ? "var(--highlight)" : "var(--ink-2)";
  });
  g.selectAll(".col-label").attr("font-weight", function() {
    return (+this.getAttribute("data-j") === highlighted) ? 600 : 400;
  }).attr("fill", function() {
    return (+this.getAttribute("data-j") === highlighted) ? "var(--highlight)" : "var(--ink-2)";
  });
}
```

### Interactive gotchas

- **Cursor pointer on labels** signals they're clickable. Without it users won't discover the interaction.
- **Highlight dims the rest** rather than hiding it — comparison context matters. ~18% opacity is the sweet spot (visible but clearly secondary).
- **Verbal interpretation in tooltip** ("Very strong" / "Moderate" / "Weak") is a small touch but very useful for users who don't read correlations daily.
