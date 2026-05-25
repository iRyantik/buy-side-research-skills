# Debt maturity ladder + capital structure

Two complementary views of leverage: (1) a year-by-year bar chart of debt maturities (the "wall"), stacked by seniority; (2) a vertical capital-structure stack showing the order of claims from senior secured down to common equity.

## When to use

User asks: "debt maturity wall", "refinancing risk", "capital stack", "senior vs sub", "where does the equity sit", "what does the balance sheet look like", "leverage analysis". Use this for any leveraged name, distressed/event-driven situation, or whenever capital structure is a thesis driver.

## Required inputs

```js
// Maturity schedule
const maturities = [
  { year: 2026, senior: 850, sub: 0,    other: 120 },   // values in $m
  { year: 2027, senior: 0,   sub: 0,    other: 0   },
  { year: 2028, senior: 1200, sub: 400, other: 80  },
  { year: 2029, senior: 0,   sub: 0,    other: 0   },
  { year: 2030, senior: 600, sub: 0,    other: 0   },
  { year: 2031, senior: 0,   sub: 750,  other: 0   },
  { year: "2032+", senior: 1500, sub: 0, other: 0  },
];

// Capital structure (top to bottom = senior to junior)
const capStack = [
  { tier: "Senior secured (RCF)",       amount:  500, rate: "SOFR+275",   ev: true  },
  { tier: "Senior secured (Term B)",    amount: 2400, rate: "SOFR+325",   ev: true  },
  { tier: "Senior unsecured notes",     amount: 1200, rate: "5.875%",     ev: true  },
  { tier: "Subordinated notes",         amount: 1150, rate: "8.25%",      ev: true  },
  { tier: "Preferred",                  amount:  400, rate: "6.5% PIK",   ev: true  },
  { tier: "Common equity",              amount: 3850, rate: "—",          ev: true  },
];

// Reference values
const cash = 850;        // for net debt
const ebitda = 1450;     // for leverage ratios
```

## Visual structure

Memo column (800×1100) is the natural format — both views are vertical-friendly. Two-column layout in slide format works too.

- **Left / top — maturity ladder**:
  - X axis: years (categorical, including a "2032+" bucket for the tail)
  - Y axis: $m
  - Stacked bars by tranche, using `--cat-*` palette (senior in `--accent`, sub in `--highlight`, other in `--neutral`)
  - Total label above each bar
  - Optional: a horizontal "available liquidity" line for context

- **Right / bottom — capital stack**:
  - Vertical stacked bar, top = most senior, bottom = equity
  - Width ∝ amount; label inside or beside each tranche with name, amount, rate
  - A leverage ladder on the side: `Total debt / EBITDA`, `Net debt / EBITDA`, `Sr. debt / EBITDA`

## Core template — maturity ladder

```js
const margin = { top: 32, right: 24, bottom: 48, left: 56 };
const width = 1088, height = 360;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const keys = ["senior", "sub", "other"];
const stack = d3.stack().keys(keys)(maturities);

const x = d3.scaleBand()
  .domain(maturities.map(d => d.year))
  .range([0, innerW])
  .padding(0.32);

const yMax = d3.max(maturities, d => d.senior + d.sub + d.other);
const y = d3.scaleLinear()
  .domain([0, yMax * 1.12]).nice()
  .range([innerH, 0]);

const colors = { senior: "var(--accent)", sub: "var(--highlight)", other: "var(--neutral)" };

g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

g.selectAll(".series").data(stack).join("g")
  .attr("fill", d => colors[d.key])
  .selectAll("rect")
  .data(d => d).join("rect")
    .attr("x", d => x(d.data.year))
    .attr("y", d => y(d[1]))
    .attr("width", x.bandwidth())
    .attr("height", d => y(d[0]) - y(d[1]));

// total label above each bar
maturities.forEach(d => {
  const total = d.senior + d.sub + d.other;
  if (total === 0) return;
  g.append("text")
    .attr("class", "data-label")
    .attr("x", x(d.year) + x.bandwidth() / 2)
    .attr("y", y(total) - 6)
    .attr("text-anchor", "middle")
    .text(d3.format(",")(total));
});

g.append("g").attr("class","axis")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x));
g.append("g").attr("class","axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d3.format(",")));

// legend (top-right)
const legendG = g.append("g").attr("transform", `translate(${innerW - 280}, 0)`);
keys.forEach((k, i) => {
  legendG.append("rect")
    .attr("x", i * 100).attr("y", 0)
    .attr("width", 12).attr("height", 12)
    .attr("fill", colors[k]);
  legendG.append("text")
    .attr("x", i * 100 + 18).attr("y", 10)
    .attr("class", "axis-label")
    .text(k === "senior" ? "Senior" : k === "sub" ? "Subordinated" : "Other");
});
```

## Core template — capital stack (vertical)

```js
const stackW = 360, stackH = 480;
const startX = 60, startY = 80;
const totalDebt = d3.sum(capStack, d => d.amount);

const svgStack = d3.select("#chart-stack").append("svg")
  .attr("viewBox", `0 0 ${stackW + 280} ${stackH + 100}`)
  .attr("width", stackW + 280).attr("height", stackH + 100);

const yScale = d3.scaleLinear()
  .domain([0, totalDebt]).range([0, stackH]);

let cum = 0;
const tierColors = ["#1F3A5F", "#4A6B8A", "#6B7F8A", "#8B2635", "#C77E3A", "#B5B5AE"];

capStack.forEach((t, i) => {
  const h = yScale(t.amount);
  svgStack.append("rect")
    .attr("x", startX).attr("y", startY + cum)
    .attr("width", stackW).attr("height", h)
    .attr("fill", tierColors[i % tierColors.length])
    .attr("stroke", "#FFF").attr("stroke-width", 1);

  // tier label inside
  svgStack.append("text")
    .attr("x", startX + 12).attr("y", startY + cum + h/2 - 2)
    .attr("fill", "#FFF")
    .attr("font-family", "var(--font-sans)")
    .attr("font-size", 12).attr("font-weight", 600)
    .text(t.tier);
  svgStack.append("text")
    .attr("x", startX + 12).attr("y", startY + cum + h/2 + 14)
    .attr("fill", "#FFF").attr("font-size", 10)
    .attr("font-family", "var(--font-mono)")
    .text(`$${d3.format(",")(t.amount)}m  ·  ${t.rate}`);

  // leverage ladder (right side)
  const cumLev = cum + h;
  const debtAbove = capStack.slice(0, i+1).filter(x => x.tier.toLowerCase().includes("senior") || x.tier.toLowerCase().includes("sub") || x.tier.toLowerCase().includes("preferred"))
    .reduce((a,b) => a + b.amount, 0);
  svgStack.append("text")
    .attr("x", startX + stackW + 24).attr("y", startY + cumLev + 4)
    .attr("class","data-label")
    .attr("fill", "var(--ink-2)")
    .text(`${(debtAbove/ebitda).toFixed(1)}x EBITDA`);

  cum += h;
});

// horizontal hairlines connecting tier boundaries to leverage labels
// (optional polish — keep simple)
```

## Variants

- **Net debt view**: subtract cash from the most senior tranche to show "net leverage"; flag as such in the subtitle.
- **Rates / interest expense overlay**: show weighted-average cost of debt as a secondary panel.
- **Refinancing window**: highlight bars within the next 24 months in `--highlight` to flag near-term refi risk.
- **Convertibles** as a sub-tranche between sub and equity, shown in a striped fill.

## Gotchas

- **Always show cash and the resulting net debt** explicitly. Gross leverage alone misleads if the company has $1bn of cash.
- **Don't forget the tail bucket** — "2032+" or "Beyond 5Y" bucket prevents underrepresenting long-dated debt.
- **State the source of rates**: indenture rate vs all-in YTM. Different numbers.
- **Preferred is not common equity** — give it its own tier. PIK preferred especially compounds outside the income statement.
- **For revolvers**, label as drawn / undrawn separately if material. An undrawn $1bn RCF is liquidity, not leverage.

---

## Interactive variant — refi scenario sliders + hover detail

For each maturity year with debt outstanding, a slider lets the user push that maturity out by N years to model a refi. Leverage ratios and the chart update live. Most valuable for credit/distressed work and event-driven situations.

### Required input (richer maturity data)

```js
const maturities = [
  {
    year: 2026, items: [
      { id: "rcf",       name: "RCF",          tranche: "senior", amount:  500, rate: "SOFR+275" },
      { id: "tb1",       name: "Term B 2026",  tranche: "senior", amount:  350, rate: "SOFR+325" },
    ]
  },
  { year: 2027, items: [] },
  {
    year: 2028, items: [
      { id: "tb2",       name: "Term B 2028",  tranche: "senior", amount: 1200, rate: "SOFR+325" },
      { id: "sub2028",   name: "Sub notes",    tranche: "sub",    amount:  400, rate: "8.25%"    },
    ]
  },
  // ...
];

const ebitda = 1450;   // for leverage
const cash = 850;      // for net leverage
```

Each individual tranche is independently movable.

### Controls (dynamic per tranche)

```html
<div class="controls" id="refi-controls">
  <span class="controls-label" style="margin-right:auto;">Push out maturities to model refinancing</span>
  <button class="btn" onclick="resetRefi()">Reset all</button>
</div>
<div id="chart"></div>
<div id="metrics" style="display:flex;gap:24px;margin-top:8px;font-size:11px;"></div>
```

### Core template

```js
// Flatten all tranches
const allTranches = maturities.flatMap(m => m.items.map(it => ({...it, originalYear: m.year, year: m.year})));

const margin = { top: 32, right: 24, bottom: 48, left: 56 };
const width = 1088, height = 360;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const colors = { senior: "var(--accent)", sub: "var(--highlight)", other: "var(--neutral)" };

// Build slider per tranche
const controlsEl = document.getElementById("refi-controls");
const slidersContainer = document.createElement("div");
slidersContainer.style.cssText = "display:grid;grid-template-columns:repeat(2,1fr);gap:4px 24px;width:100%;margin-top:8px;";
controlsEl.appendChild(slidersContainer);

allTranches.forEach(t => {
  const row = document.createElement("div");
  row.className = "slider-row";
  row.innerHTML = `
    <label>${t.name} ($${d3.format(",")(t.amount)}m)</label>
    <input type="range" min="${t.originalYear}" max="${t.originalYear + 7}" step="1" value="${t.originalYear}" data-id="${t.id}">
    <span class="slider-value" id="ry-${t.id}">${t.originalYear}</span>
  `;
  slidersContainer.appendChild(row);
  row.querySelector("input").addEventListener("input", (evt) => {
    const newYear = parseInt(evt.target.value);
    t.year = newYear;
    document.getElementById(`ry-${t.id}`).textContent =
      newYear === t.originalYear ? `${newYear}` : `${newYear} (+${newYear - t.originalYear})`;
    document.getElementById(`ry-${t.id}`).style.color =
      newYear === t.originalYear ? "var(--ink-3)" : "var(--highlight)";
    redraw();
  });
});

function resetRefi() {
  allTranches.forEach(t => {
    t.year = t.originalYear;
    document.querySelector(`[data-id="${t.id}"]`).value = t.originalYear;
    document.getElementById(`ry-${t.id}`).textContent = t.originalYear;
    document.getElementById(`ry-${t.id}`).style.color = "var(--ink-3)";
  });
  redraw();
}

function redraw() {
  g.selectAll("*").remove();

  // Group by current year
  const yearMap = new Map();
  allTranches.forEach(t => {
    if (!yearMap.has(t.year)) yearMap.set(t.year, { year: t.year, senior:0, sub:0, other:0, tranches:[] });
    const row = yearMap.get(t.year);
    row[t.tranche] = (row[t.tranche] || 0) + t.amount;
    row.tranches.push(t);
  });
  const years = [...yearMap.keys()].sort((a,b) => a-b);
  // Fill in empty years
  const minY = Math.min(...years), maxY = Math.max(...years);
  const filledYears = [];
  for (let y = minY; y <= maxY; y++) {
    filledYears.push(yearMap.get(y) || { year: y, senior:0, sub:0, other:0, tranches:[] });
  }

  const stack = d3.stack().keys(["senior","sub","other"])(filledYears);

  const x = d3.scaleBand().domain(filledYears.map(d => d.year)).range([0, innerW]).padding(0.32);
  const yMax = d3.max(filledYears, d => d.senior + d.sub + d.other);
  const y = d3.scaleLinear().domain([0, yMax * 1.12]).nice().range([innerH, 0]);

  g.append("g").attr("class","grid")
    .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

  g.selectAll(".series").data(stack).join("g")
    .attr("fill", d => colors[d.key])
    .selectAll("rect").data(d => d).join("rect")
      .attr("x", d => x(d.data.year))
      .attr("y", d => y(d[1]))
      .attr("width", x.bandwidth())
      .attr("height", d => y(d[0]) - y(d[1]))
      .style("cursor","pointer")
      .on("mouseover", function(evt, d) {
        const row = d.data;
        showTip(
          `<b>${row.year}</b><br>
           ${row.tranches.map(t => `${t.name}: <span class="num">${d3.format(",")(t.amount)}</span>${t.year !== t.originalYear ? ` <span style="color:var(--highlight-soft);">(from ${t.originalYear})</span>` : ""}`).join("<br>")}<br>
           Total: <span class="num">${d3.format(",")(row.senior + row.sub + row.other)}</span>`,
          evt);
      })
      .on("mouseout", hideTip);

  // Total labels above bars
  filledYears.forEach(d => {
    const total = d.senior + d.sub + d.other;
    if (total === 0) return;
    g.append("text").attr("class","data-label")
      .attr("x", x(d.year) + x.bandwidth()/2)
      .attr("y", y(total) - 6).attr("text-anchor","middle")
      .text(d3.format(",")(total));
  });

  g.append("g").attr("class","axis")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x));
  g.append("g").attr("class","axis axis-num")
    .call(d3.axisLeft(y).tickFormat(d3.format(",")));

  // Update metrics strip
  const totalDebt = d3.sum(allTranches, t => t.amount);
  const totalSr = d3.sum(allTranches.filter(t => t.tranche === "senior"), t => t.amount);
  const next24M = allTranches.filter(t => t.year <= new Date().getFullYear() + 2).reduce((a,b) => a + b.amount, 0);
  const next24M_base = allTranches.filter(t => t.originalYear <= new Date().getFullYear() + 2).reduce((a,b) => a + b.amount, 0);
  document.getElementById("metrics").innerHTML = `
    <span style="color:var(--ink-3);">Total debt: <b style="color:var(--ink);font-family:var(--font-mono);">${d3.format(",")(totalDebt)}</b></span>
    <span style="color:var(--ink-3);">Net debt / EBITDA: <b style="color:var(--ink);font-family:var(--font-mono);">${((totalDebt - cash)/ebitda).toFixed(1)}x</b></span>
    <span style="color:var(--ink-3);">Sr. / EBITDA: <b style="color:var(--ink);font-family:var(--font-mono);">${(totalSr/ebitda).toFixed(1)}x</b></span>
    <span style="color:var(--ink-3);">Refi wall ≤2Y: <b style="color:${next24M < next24M_base ? 'var(--pos)' : 'var(--ink)'};font-family:var(--font-mono);">${d3.format(",")(next24M)}</b> ${next24M_base !== next24M ? `<span style="color:var(--highlight);font-size:10px;">(was ${d3.format(",")(next24M_base)})</span>` : ""}</span>
  `;
}
redraw();
```

### Interactive gotchas

- **Track baseline state per tranche** — the slider should clearly show "(+3)" when moved, so the analyst sees what they've changed. Reset returns everything.
- **The refi wall ≤2Y metric is the punchline** — it visually shrinks as the user pushes maturities out, showing the "what if we extended" scenario in one number.
- **Don't recompute interest expense** unless you have rate-curve data — the rates field is informational, not the basis for a live recalc.
- **Order tranches sensibly** in the control list — by maturity year then by seniority. Random order is confusing.
