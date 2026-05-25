# Catalyst timeline

A 12–24 month forward calendar of upcoming events: earnings, product launches, regulatory decisions, capital allocation announcements, expiration of lockups, etc. Each event has a date, a category, and an importance.

## When to use

User asks: "what are the catalysts", "catalyst roadmap", "12-month outlook", "event calendar", "upcoming milestones". This is a forward-looking chart — past events go in `price-events-overlay.md` instead.

## Required inputs

```js
const events = [
  { date: "2026-04-24", label: "1Q26 earnings",          category: "Earnings",   importance: 3 },
  { date: "2026-05-15", label: "FDA AdCom on XYZ-100",   category: "Regulatory", importance: 5 },
  { date: "2026-06-30", label: "Lockup expiry (45m shares)", category: "Capital", importance: 4 },
  { date: "2026-07-22", label: "2Q26 earnings",          category: "Earnings",   importance: 3 },
  { date: "2026-09-15", label: "Investor day",           category: "Disclosure", importance: 4 },
  { date: "2026-11-05", label: "EU CMA decision",        category: "Regulatory", importance: 5 },
];
```

Importance: 1–5 (5 = highest). Used for marker size and label prominence.

## Visual structure

- Horizontal timeline running left to right, from today to end of window
- Quarter-end gridlines (vertical hairlines)
- Today marker (vertical line in `--highlight`)
- Each event is a marker on the timeline, sized by importance, colored by category
- Labels stagger above/below to avoid overlap
- Optional: lane swimlanes if there are many events and the user wants them grouped by category

## Core template — single-row timeline with staggered labels

```js
const start = new Date("2026-04-01");
const end   = new Date("2027-06-30");
const today = new Date();   // or provided explicitly

const margin = { top: 60, right: 40, bottom: 50, left: 40 };
const width = 1088, height = 320;
const innerW = width - margin.left - margin.right;
const axisY = 160;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime().domain([start, end]).range([0, innerW]);

// quarter-end gridlines
const quarters = d3.timeMonths(d3.timeMonth.floor(start), end).filter(d => d.getMonth() % 3 === 0);
g.selectAll(".qgrid")
  .data(quarters).join("line")
    .attr("class", "qgrid")
    .attr("x1", d => x(d)).attr("x2", d => x(d))
    .attr("y1", axisY - 80).attr("y2", axisY + 80)
    .attr("stroke", "var(--grid)").attr("stroke-dasharray", "1 3");

// main baseline
g.append("line")
  .attr("x1", 0).attr("x2", innerW)
  .attr("y1", axisY).attr("y2", axisY)
  .attr("stroke", "var(--ink-2)").attr("stroke-width", 1);

// today marker
g.append("line")
  .attr("x1", x(today)).attr("x2", x(today))
  .attr("y1", axisY - 90).attr("y2", axisY + 90)
  .attr("stroke", "var(--highlight)").attr("stroke-width", 1.5);
g.append("text")
  .attr("class", "callout")
  .attr("x", x(today) + 6).attr("y", axisY - 80)
  .attr("fill", "var(--highlight)")
  .text("Today");

// category palette
const catColor = {
  "Earnings":    "var(--cat-1)",
  "Regulatory":  "var(--cat-2)",
  "Capital":     "var(--cat-3)",
  "Disclosure":  "var(--cat-4)",
  "Other":       "var(--cat-5)",
};

// markers — alternate above/below to reduce overlap
events.forEach((e, i) => {
  const above = i % 2 === 0;
  const ex = x(new Date(e.date));
  const ey = above ? axisY - 28 : axisY + 28;
  const labelY = above ? axisY - 44 : axisY + 52;
  const r = 4 + e.importance;   // 5–9px

  // lead line from baseline to marker
  g.append("line")
    .attr("x1", ex).attr("x2", ex)
    .attr("y1", axisY).attr("y2", ey)
    .attr("stroke", "var(--hairline)").attr("stroke-width", 1);

  // marker
  g.append("circle")
    .attr("cx", ex).attr("cy", ey).attr("r", r)
    .attr("fill", catColor[e.category] || "var(--cat-5)")
    .attr("stroke", "#FFF").attr("stroke-width", 1.5);

  // label
  g.append("text")
    .attr("class", "data-label")
    .attr("x", ex).attr("y", labelY)
    .attr("text-anchor", "middle")
    .attr("font-family", "var(--font-sans)")
    .text(e.label);
  // date underneath label
  g.append("text")
    .attr("class", "data-label")
    .attr("x", ex).attr("y", labelY + (above ? -14 : 14))
    .attr("text-anchor", "middle")
    .attr("fill", "var(--ink-3)")
    .attr("font-size", 10)
    .text(d3.timeFormat("%d %b")(new Date(e.date)));
});

// x axis (quarter labels)
g.append("g")
  .attr("class", "axis")
  .attr("transform", `translate(0,${axisY + 90})`)
  .call(d3.axisBottom(x).ticks(d3.timeMonth.every(3)).tickFormat(d3.timeFormat("%qQ%y")));

// category legend (top-left)
const legendG = g.append("g").attr("transform", "translate(0, -40)");
Object.entries(catColor).forEach(([cat, color], i) => {
  const lx = i * 130;
  legendG.append("circle").attr("cx", lx).attr("cy", 0).attr("r", 5).attr("fill", color);
  legendG.append("text").attr("x", lx + 12).attr("y", 4).attr("class","axis-label").text(cat);
});
```

## Variants

- **Swimlanes by category**: instead of staggering labels, give each category its own horizontal row. Cleaner when there are many events.
- **Probability-weighted catalysts**: add `probability` to the data and render marker opacity ∝ probability. Useful for binary regulatory events.
- **With expected price impact**: annotate each event with the analyst's expected ±% on the stock (e.g. "+8% / -15%"). Lets the PM see asymmetry.

## Gotchas

- **Today is always shown** — without it the chart loses urgency.
- **Don't include events past 18–24 months** — the chart becomes speculative and loses signal.
- **Group similar events**: if there are 4 routine quarterly earnings, mark them but keep labels short. Save real-estate for the non-routine catalysts.
- **Importance scoring should be the analyst's view**, not market consensus. State this in the source line.
- **Avoid >12 events**. Use the swimlane variant if you really need more.

---

## Interactive variant — category filter + hover detail expansion

Click category pills to filter visible events. Hover events for full description (including probability, expected impact, analyst's view). Useful when you have 8–15 catalysts and want to filter to "just the regulatory ones" or "just binary events".

### Required input (richer events)

```js
const events = [
  {
    date: "2026-05-15", label: "FDA AdCom on XYZ-100",
    category: "Regulatory", importance: 5,
    probability: 0.55,
    expectedImpact: "+25% / -40%",
    description: "Outcome binary — positive vote opens $2bn+ market; negative likely sinks the platform thesis.",
  },
  // ...
];
```

### Controls

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Category</span>
    <div class="pills" id="cat-pills"></div>
  </div>
  <button class="btn" onclick="resetFilter()">Show all</button>
</div>
<div id="chart"></div>
```

### Core template

```js
const start = new Date("2026-04-01");
const end   = new Date("2027-06-30");
const today = new Date();

const catColor = {
  "Earnings": "var(--cat-1)", "Regulatory": "var(--cat-2)",
  "Capital": "var(--cat-3)", "Disclosure": "var(--cat-4)", "Other": "var(--cat-5)",
};
const allCats = [...new Set(events.map(e => e.category))];
const active = new Set(allCats);

// Pills
const pillsEl = document.getElementById("cat-pills");
allCats.forEach(c => {
  const p = document.createElement("span");
  p.className = "pill active";
  p.dataset.cat = c;
  p.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${catColor[c]||'var(--cat-5)'};margin-right:6px;vertical-align:1px;"></span>${c}`;
  p.addEventListener("click", () => {
    if (active.has(c)) { active.delete(c); p.classList.remove("active"); }
    else               { active.add(c); p.classList.add("active"); }
    redraw();
  });
  pillsEl.appendChild(p);
});

function resetFilter() {
  active.clear();
  allCats.forEach(c => active.add(c));
  document.querySelectorAll("#cat-pills .pill").forEach(p => p.classList.add("active"));
  redraw();
}

const margin = { top: 60, right: 40, bottom: 50, left: 40 };
const width = 1088, height = 340;
const innerW = width - margin.left - margin.right;
const axisY = 170;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleTime().domain([start, end]).range([0, innerW]);

// Static elements
const quarters = d3.timeMonths(d3.timeMonth.floor(start), end).filter(d => d.getMonth() % 3 === 0);
g.selectAll(".qgrid").data(quarters).join("line")
  .attr("class","qgrid")
  .attr("x1", d => x(d)).attr("x2", d => x(d))
  .attr("y1", axisY - 90).attr("y2", axisY + 90)
  .attr("stroke", "var(--grid)").attr("stroke-dasharray", "1 3");

g.append("line")
  .attr("x1", 0).attr("x2", innerW).attr("y1", axisY).attr("y2", axisY)
  .attr("stroke", "var(--ink-2)").attr("stroke-width", 1);

g.append("line")
  .attr("x1", x(today)).attr("x2", x(today))
  .attr("y1", axisY - 100).attr("y2", axisY + 100)
  .attr("stroke", "var(--highlight)").attr("stroke-width", 1.5);
g.append("text").attr("class","callout")
  .attr("x", x(today) + 6).attr("y", axisY - 88)
  .attr("fill", "var(--highlight)").text("Today");

g.append("g").attr("class","axis")
  .attr("transform", `translate(0,${axisY + 100})`)
  .call(d3.axisBottom(x).ticks(d3.timeMonth.every(3)).tickFormat(d3.timeFormat("%qQ%y")));

const eventsG = g.append("g").attr("class","events");

function redraw() {
  const visible = events.filter(e => active.has(e.category));

  eventsG.selectAll("*").remove();

  visible.forEach((e, i) => {
    const above = i % 2 === 0;
    const ex = x(new Date(e.date));
    const ey = above ? axisY - 32 : axisY + 32;
    const labelY = above ? axisY - 50 : axisY + 60;
    const r = 4 + e.importance;

    eventsG.append("line")
      .attr("x1", ex).attr("x2", ex).attr("y1", axisY).attr("y2", ey)
      .attr("stroke", "var(--hairline)").attr("stroke-width", 1);

    const marker = eventsG.append("circle")
      .attr("cx", ex).attr("cy", ey).attr("r", r)
      .attr("fill", catColor[e.category] || "var(--cat-5)")
      .attr("stroke", "#FFF").attr("stroke-width", 1.5)
      .attr("fill-opacity", e.probability != null ? Math.max(0.35, e.probability) : 1)
      .style("cursor", "pointer")
      .on("mouseover", function(evt) {
        d3.select(this).attr("stroke", "var(--highlight)").attr("stroke-width", 2);
        showTip(
          `<b>${e.label}</b> &middot; <span style="color:var(--neutral);">${d3.timeFormat("%d %b %Y")(new Date(e.date))}</span><br>
           <span style="color:var(--paper-edge);font-size:10.5px;display:block;margin-top:3px;max-width:260px;">${e.description || ""}</span>
           <div style="margin-top:4px;display:flex;gap:10px;font-size:10.5px;">
             ${e.probability != null ? `<span>Prob: <b>${(e.probability*100).toFixed(0)}%</b></span>` : ""}
             ${e.expectedImpact ? `<span>Impact: <b>${e.expectedImpact}</b></span>` : ""}
           </div>`,
          evt);
      })
      .on("mouseout", function() {
        d3.select(this).attr("stroke","#FFF").attr("stroke-width", 1.5);
        hideTip();
      });

    eventsG.append("text").attr("class","data-label")
      .attr("x", ex).attr("y", labelY).attr("text-anchor","middle")
      .style("pointer-events","none")
      .text(e.label);
    eventsG.append("text").attr("class","data-label")
      .attr("x", ex).attr("y", labelY + (above ? -14 : 14))
      .attr("text-anchor","middle").attr("fill","var(--ink-3)").attr("font-size",10)
      .style("pointer-events","none")
      .text(d3.timeFormat("%d %b")(new Date(e.date)));
  });
}
redraw();
```

### Interactive gotchas

- **Use probability to modulate marker opacity** — gives a visual sense of "this one's likely, that one's a coin-flip" without adding clutter.
- **Show expected impact symmetrically** ("+25% / -40%") so the asymmetry of binary events is visible.
- **Filter pills should be tinted** with the category color so the user can map filter to dots visually. Use a small color dot inside the pill.
- **When filtering removes all events**, show a friendly empty state ("No events match the selected categories") rather than a blank timeline.
