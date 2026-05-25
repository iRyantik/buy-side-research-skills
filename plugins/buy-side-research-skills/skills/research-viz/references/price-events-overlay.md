# Price + events overlay

Stock price line with past events annotated — the chart you put in the body of a memo to tell the story of how the stock got here. Different from the catalyst timeline, which is forward-looking.

## When to use

User asks: "annotate the stock chart", "tell the story with the price", "price with milestones", "what happened at each event", "stock chart for the memo". 3–8 events max — more becomes noise.

## Required inputs

```js
const price = [
  { date: "2022-01-03", close: 184.50 },
  // weekly or daily, doesn't matter — line will smooth
  ...
  { date: "2026-03-31", close: 412.30 },
];

const events = [
  { date: "2022-03-15", label: "Activist letter (Engaged Capital)",   side: "above" },
  { date: "2022-11-08", label: "CEO transition",                       side: "below" },
  { date: "2023-06-22", label: "New product cycle (Q3)",               side: "above" },
  { date: "2024-02-14", label: "Capital return announced ($5bn buyback)", side: "above" },
  { date: "2025-09-30", label: "Margin reset / guide-down",            side: "below" },
];
```

`side: "above"` puts the annotation arm above the price line; `"below"` puts it below. Mix to avoid label overlap.

## Visual structure

- Standard price line in `--accent`, no fill
- 5-year average price as a horizontal dotted line (optional)
- Each event: a small filled dot on the price line at the event date, plus a lead line (1px solid) rising/dropping to a serif italic label
- Today / most recent price marked with a focal dot in `--highlight`

## Core template

```js
// price: [{date: Date, close: number}], events: [{date: Date, label, side}]

const margin = { top: 64, right: 80, bottom: 36, left: 56 };
const width = 1088, height = 540;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime()
  .domain(d3.extent(price, d => new Date(d.date)))
  .range([0, innerW]);
const y = d3.scaleLinear()
  .domain([0, d3.max(price, d => d.close) * 1.05]).nice()
  .range([innerH, 0]);

// grid
g.append("g").attr("class","grid")
  .call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

// price line
const line = d3.line()
  .x(d => x(new Date(d.date)))
  .y(d => y(d.close))
  .curve(d3.curveMonotoneX);
g.append("path")
  .datum(price)
  .attr("fill", "none")
  .attr("stroke", "var(--accent)")
  .attr("stroke-width", 1.5)
  .attr("d", line);

// helper: find price on a date
const priceOn = (date) => {
  const t = new Date(date).getTime();
  let closest = price[0], bestDiff = Infinity;
  for (const p of price) {
    const diff = Math.abs(new Date(p.date).getTime() - t);
    if (diff < bestDiff) { bestDiff = diff; closest = p; }
  }
  return closest.close;
};

// events
events.forEach(e => {
  const ex = x(new Date(e.date));
  const ey = y(priceOn(e.date));
  const offset = e.side === "above" ? -56 : 56;
  const labelY = ey + offset;

  // event dot on the price line
  g.append("circle")
    .attr("cx", ex).attr("cy", ey).attr("r", 4)
    .attr("fill", "var(--paper)")
    .attr("stroke", "var(--accent)").attr("stroke-width", 1.5);

  // lead line to label
  g.append("line")
    .attr("x1", ex).attr("x2", ex)
    .attr("y1", ey + (e.side === "above" ? -5 : 5))
    .attr("y2", labelY + (e.side === "above" ? 4 : -4))
    .attr("stroke", "var(--ink-2)").attr("stroke-width", 1);

  // label
  g.append("text")
    .attr("class", "callout")
    .attr("x", ex)
    .attr("y", labelY)
    .attr("text-anchor", "middle")
    .text(e.label);

  // date sub-label
  g.append("text")
    .attr("x", ex)
    .attr("y", labelY + (e.side === "above" ? -14 : 14))
    .attr("text-anchor", "middle")
    .attr("font-size", 10)
    .attr("fill", "var(--ink-3)")
    .text(d3.timeFormat("%b '%y")(new Date(e.date)));
});

// focal dot — last price
const last = price[price.length - 1];
g.append("circle")
  .attr("class", "focal")
  .attr("cx", x(new Date(last.date)))
  .attr("cy", y(last.close))
  .attr("r", 5);
g.append("text")
  .attr("class","data-label")
  .attr("x", x(new Date(last.date)) + 8)
  .attr("y", y(last.close) + 4)
  .attr("fill", "var(--highlight)")
  .text("$" + last.close.toFixed(2));

// axes
g.append("g")
  .attr("class", "axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
g.append("g")
  .attr("class", "axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d => "$" + d3.format(",")(d)));
```

## Variants

- **Indexed performance vs peers**: replace absolute price with `(price / startPrice) * 100`, add 1–3 peer lines in `--neutral`. Useful for "relative outperformance" stories.
- **Log y-axis** for long histories (>10 years) where percentage moves matter more than absolute price.
- **Shaded regimes**: add background `<rect>` blocks for ownership periods, management tenures, cycles. Use `--paper-edge` fill at low opacity.

## Gotchas

- **Don't annotate everything** — 5 events max in a single chart. If the user wants 10, push back: split into two charts or use a swimlane format.
- **Event labels should be short and verbal**: "Activist letter", "CEO transition", "Buyback announced" — not full sentences. The label is a tag, not a paragraph.
- **Lead lines must not cross the price line** — keep them above/below cleanly.
- **The labels should describe what happened, not their interpretation**. "Margin reset" is fine; "Stock got crushed because margins reset" is editorial in the wrong place — that belongs in the memo body.
- **State the price series**: split-adjusted close, dividend-adjusted, etc., in the subtitle or source line.

---

## Interactive variant — crosshair + event hover-expand

Hover for exact price/date readout. Hover an event marker for the full event description (instead of cramming it on the chart). Click an event to pin its detail card.

### Required input (richer events)

```js
const events = [
  {
    date: "2022-03-15", label: "Activist letter",
    side: "above",
    description: "Engaged Capital files 13D with 4.5% stake, demands board refresh and capital return.",
    priceImpact: "+8.2% 1-day",
  },
  // ...
];
```

### Core template

```js
// price: [{date, close}], events: [{date, label, side, description, priceImpact}]

const margin = { top: 32, right: 80, bottom: 36, left: 56 };
const width = 1088, height = 540;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime()
  .domain(d3.extent(price, d => new Date(d.date)))
  .range([0, innerW]);
const y = d3.scaleLinear()
  .domain([0, d3.max(price, d => d.close) * 1.05]).nice()
  .range([innerH, 0]);

g.append("g").attr("class","grid").call(d3.axisLeft(y).tickSize(-innerW).tickFormat(""));

const line = d3.line()
  .x(d => x(new Date(d.date))).y(d => y(d.close))
  .curve(d3.curveMonotoneX);
g.append("path").datum(price)
  .attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 1.5)
  .attr("d", line);

const priceOn = (date) => {
  const t = new Date(date).getTime();
  let closest = price[0], bestDiff = Infinity;
  for (const p of price) {
    const diff = Math.abs(new Date(p.date).getTime() - t);
    if (diff < bestDiff) { bestDiff = diff; closest = p; }
  }
  return closest.close;
};

// Event dots — minimal label, full info on hover
events.forEach(e => {
  const ex = x(new Date(e.date));
  const ey = y(priceOn(e.date));
  const offset = e.side === "above" ? -36 : 36;
  const labelY = ey + offset;

  // Lead line
  g.append("line")
    .attr("x1", ex).attr("x2", ex)
    .attr("y1", ey + (e.side === "above" ? -5 : 5))
    .attr("y2", labelY)
    .attr("stroke", "var(--ink-2)").attr("stroke-width", 1);

  // Event dot (clickable)
  const dot = g.append("circle")
    .attr("cx", ex).attr("cy", ey).attr("r", 5)
    .attr("fill", "var(--paper)")
    .attr("stroke", "var(--accent)").attr("stroke-width", 1.5)
    .style("cursor", "pointer")
    .on("mouseover", function(evt) {
      d3.select(this).attr("r", 7).attr("stroke","var(--highlight)").attr("stroke-width", 2);
      showTip(
        `<b>${e.label}</b> &nbsp; <span style="color:var(--neutral);">${d3.timeFormat("%d %b %Y")(new Date(e.date))}</span><br>
         <span style="color:var(--paper-edge);font-size:10.5px;line-height:1.4;display:block;margin-top:4px;max-width:260px;">${e.description || ""}</span>
         ${e.priceImpact ? `<span style="color:var(--highlight-soft);font-family:var(--font-mono);font-size:10.5px;">${e.priceImpact}</span>` : ""}`,
        evt
      );
    })
    .on("mouseout", function() {
      d3.select(this).attr("r", 5).attr("stroke","var(--accent)").attr("stroke-width", 1.5);
      hideTip();
    });

  // Short label (just the title) at offset position
  g.append("text").attr("class","callout")
    .attr("x", ex).attr("y", labelY)
    .attr("text-anchor", "middle")
    .text(e.label);
});

// Crosshair on price line
const ch = g.append("g").style("display","none").style("pointer-events","none");
ch.append("line").attr("class","crosshair").attr("y1",0).attr("y2",innerH);
const chDot = ch.append("circle").attr("r",4)
  .attr("fill","var(--paper)").attr("stroke","var(--highlight)").attr("stroke-width",1.5);

const overlay = g.append("rect")
  .attr("width", innerW).attr("height", innerH)
  .attr("fill", "transparent")
  .style("cursor", "crosshair")
  .lower();  // sits below events so events get priority for hover

const bisect = d3.bisector(d => new Date(d.date)).left;
overlay
  .on("mouseenter", () => ch.style("display", null))
  .on("mouseleave", () => { ch.style("display","none"); hideTip(); })
  .on("mousemove", function(evt) {
    const mx = d3.pointer(evt, this)[0];
    const date = x.invert(mx);
    const i = Math.min(price.length-1, Math.max(0, bisect(price, date)));
    const d = price[i];
    const sx = x(new Date(d.date)), sy = y(d.close);
    ch.select("line").attr("x1", sx).attr("x2", sx);
    chDot.attr("cx", sx).attr("cy", sy);
    showTip(
      `<b>$${d.close.toFixed(2)}</b><br>${d3.timeFormat("%d %b %Y")(new Date(d.date))}`,
      evt
    );
  });

// Focal dot — last price
const last = price[price.length - 1];
g.append("circle").attr("class","focal")
  .attr("cx", x(new Date(last.date))).attr("cy", y(last.close)).attr("r", 5);

g.append("g").attr("class","axis axis-num")
  .attr("transform", `translate(0,${innerH})`)
  .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y")));
g.append("g").attr("class","axis axis-num")
  .call(d3.axisLeft(y).tickFormat(d => "$" + d3.format(",")(d)));
```

### Interactive gotchas

- **Z-order matters**: the crosshair overlay must sit BELOW the event dots so dots get hover priority. Use `.lower()` on the overlay.
- **Event label crowding**: in the interactive version, you can show shorter labels (just the title) since the full description is in the tooltip. This lets you fit more events without overlap.
- **Hover state on event dots** — increase radius and switch stroke to `--highlight` to make the interaction tactile.
- **`priceImpact` is the analyst's added value** — show "+8.2% 1-day" so the reader sees what the event did to the stock, not just what happened.
