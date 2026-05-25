# Interaction patterns — for dynamic charts

This file is the common vocabulary for interactive variants. Each pattern is a small, drop-in code block that the 18 reference files reference. Don't reinvent these per chart; copy from here.

The static skill remains unchanged. Interactive variants live in the "Interactive variant" section of each reference file. The static version is still the default for memo screenshots.

## Six interaction primitives

| Primitive | Used by | Purpose |
|---|---|---|
| **Hover tooltip** | All | Show exact value / metadata for the hovered element |
| **Crosshair** | Time series | Vertical line follows mouse, syncs across panels |
| **Brush to zoom** | Time series | Drag to select date range, all series re-scale |
| **Slider for recompute** | SOTP, sensitivity, debt | Drag to change input, output recomputes live |
| **Click to highlight / sticky select** | Scatter, correlation, tree | Click stays highlighted until next click |
| **Filter pills** | Catalyst, Pareto, peer | Toggle category visibility |

Plus one special: **Leaflet tile map** for the global map.

## Universal: hover tooltip

A single floating div, positioned absolutely, updated on mousemove over chart elements. Use one tooltip element per page, shared across all charts on it.

```html
<div id="tt" class="tt"></div>
<style>
  .tt {
    position: fixed;
    pointer-events: none;
    background: var(--ink);
    color: var(--paper);
    padding: 8px 10px;
    border-radius: 3px;
    font-family: var(--font-sans);
    font-size: 11px;
    line-height: 1.4;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    opacity: 0;
    transition: opacity 120ms;
    z-index: 1000;
    max-width: 260px;
  }
  .tt.show { opacity: 1; }
  .tt b { font-weight: 600; }
  .tt .num { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .tt .sep { color: var(--neutral); margin: 0 4px; }
</style>
```

```js
const tt = document.getElementById("tt");
function showTip(html, evt) {
  tt.innerHTML = html;
  tt.classList.add("show");
  positionTip(evt);
}
function positionTip(evt) {
  const x = evt.clientX, y = evt.clientY;
  const rect = tt.getBoundingClientRect();
  // Position to upper-right of cursor by default; flip if would clip
  let left = x + 14, top = y - rect.height - 10;
  if (left + rect.width > window.innerWidth - 8) left = x - rect.width - 14;
  if (top < 8) top = y + 14;
  tt.style.left = left + "px";
  tt.style.top = top + "px";
}
function hideTip() { tt.classList.remove("show"); }
```

Use:
```js
chart.selectAll(".bar")
  .on("mousemove", (evt, d) => showTip(
    `<b>${d.label}</b><br><span class="num">${d3.format(",")(d.value)}</span>`, evt))
  .on("mouseleave", hideTip);
```

## Time series: crosshair

Vertical line that follows mouse on time-series charts. For multi-panel layouts, share one crosshair across panels by listening on a top-level overlay rect.

```js
function attachCrosshair(g, xScale, dataAccessor, innerW, innerH, onMove) {
  const ch = g.append("g").style("display", "none");
  ch.append("line")
    .attr("class", "crosshair")
    .attr("y1", 0).attr("y2", innerH)
    .attr("stroke", "var(--ink-2)")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "2 3");

  const overlay = g.append("rect")
    .attr("class", "overlay")
    .attr("width", innerW).attr("height", innerH)
    .attr("fill", "transparent")
    .style("cursor", "crosshair");

  const bisect = d3.bisector(d => d.date).left;

  overlay
    .on("mouseenter", () => ch.style("display", null))
    .on("mouseleave", () => { ch.style("display", "none"); hideTip(); })
    .on("mousemove", function(evt) {
      const data = dataAccessor();
      const mx = d3.pointer(evt, this)[0];
      const date = xScale.invert(mx);
      const i = Math.min(data.length - 1, Math.max(0, bisect(data, date)));
      const d0 = data[Math.max(0, i - 1)];
      const d1 = data[i];
      const d  = !d0 ? d1 : (!d1 ? d0 : (date - d0.date > d1.date - date ? d1 : d0));
      const sx = xScale(d.date);
      ch.select("line").attr("x1", sx).attr("x2", sx);
      onMove(d, evt);
    });
}
```

For multi-panel sync: store the current x in a shared variable, redraw all panels' crosshairs on every move.

## Time series: brush to zoom

```js
const brush = d3.brushX()
  .extent([[0, 0], [innerW, innerH]])
  .on("end", ({ selection }) => {
    if (!selection) {                 // double-click clears
      x.domain(d3.extent(data, d => d.date));
    } else {
      const [x0, x1] = selection.map(x.invert);
      x.domain([x0, x1]);
    }
    redraw();
    g.select(".brush").call(brush.move, null);
  });

g.append("g").attr("class", "brush").call(brush);
```

Pair with a reset button: `<button onclick="resetZoom()">Reset</button>`.

## Slider for live recompute

Standard HTML range input, styled to match. Each slider has a label, value display, and reactive callback.

```html
<div class="slider-row">
  <label>Cloud EV/EBITDA</label>
  <input type="range" min="10" max="35" step="0.5" value="22" id="cloud-mult">
  <span class="slider-value" id="cloud-mult-out">22.0x</span>
</div>
```

```css
.slider-row {
  display: grid;
  grid-template-columns: 140px 1fr 60px;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  font-family: var(--font-sans);
  font-size: 11px;
}
.slider-row label { color: var(--ink-2); }
.slider-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  color: var(--highlight);
  text-align: right;
}
input[type="range"] {
  -webkit-appearance: none;
  background: transparent;
  height: 18px;
}
input[type="range"]::-webkit-slider-runnable-track {
  background: var(--hairline);
  height: 2px;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px; height: 12px;
  background: var(--accent);
  border-radius: 50%;
  margin-top: -5px;
  cursor: pointer;
}
input[type="range"]::-moz-range-track { background: var(--hairline); height: 2px; }
input[type="range"]::-moz-range-thumb {
  width: 12px; height: 12px;
  background: var(--accent);
  border: none;
  border-radius: 50%;
  cursor: pointer;
}
```

```js
const slider = document.getElementById("cloud-mult");
const out = document.getElementById("cloud-mult-out");
slider.addEventListener("input", () => {
  const v = parseFloat(slider.value);
  out.textContent = v.toFixed(1) + "x";
  recompute({ cloudMultiple: v });
});
```

## Click to highlight / sticky select

For scatter, correlation matrix, tree. A clicked element stays highlighted until another click (or explicit unselect).

```js
let selected = null;

function applySelection(g) {
  g.selectAll(".dot")
    .attr("fill-opacity", d => selected == null ? 0.55 : (d === selected ? 0.85 : 0.2))
    .attr("stroke-width", d => d === selected ? 2 : 1);
}

g.selectAll(".dot")
  .on("click", (evt, d) => {
    selected = (selected === d) ? null : d;
    applySelection(g);
  });
```

For correlation matrix: clicking a row highlights the row + col, dims the rest.

## Filter pills

Categorical filters above the chart. Click toggles, multi-select.

```html
<div class="pills">
  <span class="pill active" data-cat="Earnings">Earnings</span>
  <span class="pill active" data-cat="Regulatory">Regulatory</span>
  <span class="pill active" data-cat="Capital">Capital</span>
  <span class="pill active" data-cat="Disclosure">Disclosure</span>
</div>
```

```css
.pills { display: flex; gap: 6px; margin-bottom: 12px; }
.pill {
  font-family: var(--font-sans);
  font-size: 11px;
  padding: 3px 10px;
  border: 1px solid var(--hairline);
  border-radius: 12px;
  cursor: pointer;
  user-select: none;
  color: var(--ink-3);
  background: transparent;
}
.pill.active {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-ghost);
}
.pill:hover { border-color: var(--ink-2); }
```

```js
const active = new Set([...document.querySelectorAll(".pill.active")].map(p => p.dataset.cat));
document.querySelectorAll(".pill").forEach(p => {
  p.addEventListener("click", () => {
    const cat = p.dataset.cat;
    if (active.has(cat)) { active.delete(cat); p.classList.remove("active"); }
    else                 { active.add(cat);    p.classList.add("active"); }
    redrawWithFilter(active);
  });
});
```

## Leaflet tile map — special case

For the global map only. Replaces D3 + topojson with a real tile map.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.js"></script>
```

```js
// Carto Positron tile layer — light grey, editorial-friendly, no API key
const map = L.map("map", {
  center: [25, 100],
  zoom: 2,
  zoomControl: true,
  scrollWheelZoom: true,
  attributionControl: true,
});

L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
  {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
  }
).addTo(map);

// Style the attribution to be unobtrusive
const attr = document.querySelector(".leaflet-control-attribution");
if (attr) attr.style.fontSize = "9px";
```

Markers (data-driven, sized by value):
```js
const rScale = d3.scaleSqrt()
  .domain([0, d3.max(data, d => d.value)])
  .range([4, 26]);

data.forEach(d => {
  const marker = L.circleMarker([d.lat, d.lon], {
    radius: rScale(d.value),
    fillColor: d.focal ? "#8B2635" : "#1F3A5F",
    fillOpacity: 0.55,
    color: d.focal ? "#8B2635" : "#1F3A5F",
    weight: 1.5,
  }).addTo(map);

  marker.on("mouseover", evt => {
    showTip(
      `<b>${d.name}</b><br><span class="num">${d3.format(",")(d.value)}</span> ${d.unit || ""}`,
      evt.originalEvent
    );
  });
  marker.on("mouseout", hideTip);

  // Optional popup on click
  marker.bindPopup(
    `<div style="font-family:var(--font-sans);font-size:11px;">
       <strong>${d.name}</strong><br>
       <span style="font-family:var(--font-mono);">${d3.format(",")(d.value)} ${d.unit || ""}</span><br>
       <span style="color:#6B6B6B;">${d.region || ""}</span>
     </div>`,
    { closeButton: false, autoPan: true }
  );
});
```

Marker clustering (when >30 markers):
```html
<script src="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5/dist/leaflet.markercluster.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5/dist/MarkerCluster.css">
```
```js
const cluster = L.markerClusterGroup({ showCoverageOnHover: false });
markers.forEach(m => cluster.addLayer(m));
map.addLayer(cluster);
```

## Pitfalls to avoid

- **Don't put hover behavior on the whole chart group** — bind only to data elements (bars, dots, lines, cells). Otherwise the tooltip flickers as the mouse crosses gaps.
- **Don't recompute the whole DOM** on slider change — D3's enter/update/exit or `.attr()` re-application on existing elements is faster and avoids flicker.
- **Single tooltip element**, not one per chart — otherwise clicking around leaves orphan tooltips on screen.
- **Throttle slider input handlers** if the recompute is heavy (>50ms). Use `requestAnimationFrame` instead of debounce for visual smoothness.
- **Leaflet container needs explicit height** in CSS or it renders 0px tall. Set `#map { height: 480px; }`.
- **Pointer-events on overlays**: brush and crosshair overlays must have `pointer-events: all` (or use the default `<rect>` behavior, which is interactive).
- **Don't hide attribution** on Leaflet maps — it's a license requirement for OSM/Carto. Just make it small (9–10px) and gray.
- **Color in interactive states**: use `--highlight` for hover/selected, never bright red/green. Restraint applies to interactive states too.
