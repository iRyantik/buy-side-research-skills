# Global operations / footprint map

For showing where a company physically operates — factories, mines, retail stores, data centers — or how revenue is distributed across geographies.

## When to use this specifically

| User says | Pattern to use |
|---|---|
| "Map where A公司 has factories" | Markers (sized by capacity) |
| "Show TSMC's global fabs" | Markers (sized by capacity, color by node/process) |
| "Where does Shopify make its revenue" | Choropleth (countries shaded by revenue %) |
| "Map Tesla's gigafactories with capacity" | Markers + labels |
| "Show the supply chain from China to US" | Markers + arcs (great-circle paths) |
| "Stores by country for LVMH" | Markers (sized by store count), or choropleth |
| "Geographic concentration of Apple's revenue" | Choropleth + top-N callout box |

Pick the pattern by the question:
- **How big is each location?** → markers, sized by metric
- **How much revenue comes from each country?** → choropleth
- **Where does stuff move?** → arcs
- **All three** → markers on top of choropleth (works, but only if data warrants it)

## Required inputs

For markers:
```js
[
  { name: "Hsinchu Fab 12", lat: 24.78, lon: 121.00, value: 130000, category: "5nm" },
  { name: "Phoenix Fab 21", lat: 33.45, lon: -112.07, value: 20000, category: "4nm" },
  ...
]
```

For choropleth:
```js
[
  { iso3: "USA", value: 0.42 },   // 42% of revenue
  { iso3: "CHN", value: 0.18 },
  ...
]
```
ISO-3166-1 alpha-3 codes match the world-atlas TopoJSON. If the user gives 2-letter codes or country names, convert first.

For arcs (origin → destination flows):
```js
[
  { from: [121.00, 24.78], to: [-112.07, 33.45], value: 50 },   // [lon, lat]
  ...
]
```

If the user does not provide coordinates, web-search them. Use the city centroid for facilities. For revenue-by-country, no coordinates needed.

## Projection choice

| Projection | Use for | D3 |
|---|---|---|
| **Robinson** | Default global view — balanced, looks like an editorial map | `d3.geoRobinson()` (needs d3-geo-projection) — or use Natural Earth, which D3 has built-in |
| **Natural Earth 1** | Same vibe as Robinson, built-in to D3 | `d3.geoNaturalEarth1()` ← **default choice** |
| **Equal Earth** | If you need equal-area (e.g. for choropleth where size matters) | `d3.geoEqualEarth()` |
| **Mercator** | Avoid for global maps — distorts polar areas — unless the map is regional | `d3.geoMercator()` |

For regional zoom (e.g. only Asia, only EU+US), fitSize will scale automatically. Just filter `features` before projecting.

## Template — markers on global map

This is the workhorse. Edit `data` at top, edit title/source at bottom.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Global operations map</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
<style>
  /* ↓ paste the design-tokens :root block here ↓ */
  :root {
    --paper:#FAFAF7; --paper-edge:#F4F3EE; --ink:#1A1A1A; --ink-2:#4A4A4A; --ink-3:#6B6B6B;
    --hairline:#D4D4CE; --grid:#E8E7E1;
    --accent:#1F3A5F; --accent-soft:#4A6B8A; --accent-ghost:#C8D2DE;
    --highlight:#8B2635; --highlight-soft:#C77E3A;
    --land:#EAE8E0; --ocean:#FAFAF7;  /* map-specific */
    --font-serif:'Source Serif 4','Source Serif Pro',Georgia,serif;
    --font-sans:'Inter','Helvetica Neue',Arial,sans-serif;
    --font-mono:'JetBrains Mono','Source Code Pro',Menlo,monospace;
  }
  html,body{margin:0;background:var(--paper);color:var(--ink);
    font-family:var(--font-sans);font-size:13px;
    font-feature-settings:"tnum" 1,"lnum" 1;}
  .figure-slide{width:1200px;margin:32px auto;padding:48px 56px 40px 56px;
    background:var(--paper);border:1px solid var(--hairline);}
  .chart-eyebrow{font-size:10px;font-weight:600;letter-spacing:.12em;
    text-transform:uppercase;color:var(--ink-3);margin:0 0 6px 0;}
  .chart-title{font-family:var(--font-serif);font-size:24px;font-weight:600;
    line-height:1.2;margin:0 0 6px 0;}
  .chart-subtitle{font-size:13px;color:var(--ink-2);margin:0 0 20px 0;}
  .chart-source{font-size:10.5px;color:var(--ink-3);font-style:italic;
    margin-top:16px;border-top:1px solid var(--hairline);padding-top:8px;}
  .country{fill:var(--land);stroke:#FFF;stroke-width:.4;}
  .marker{fill:var(--accent);fill-opacity:.55;stroke:var(--accent);stroke-width:1;}
  .marker.focal{fill:var(--highlight);fill-opacity:.65;stroke:var(--highlight);}
  .marker-label{font-family:var(--font-mono);font-variant-numeric:tabular-nums;
    font-size:10px;fill:var(--ink);}
  .legend text{font-size:11px;fill:var(--ink-2);}
  .legend-title{font-size:10px;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;fill:var(--ink-3);}
</style>
</head>
<body>

<div class="figure-slide">
  <p class="chart-eyebrow">TSMC · 2330 TT · Operations</p>
  <h1 class="chart-title">Global wafer-fab footprint, by installed capacity</h1>
  <p class="chart-subtitle">Marker area ∝ 12-inch equivalent monthly wafer capacity (kwpm), FY2025E</p>
  <div id="chart"></div>
  <p class="chart-source">Source: Company filings; TrendForce. As of 31 Mar 2026.</p>
</div>

<script>
// ─── DATA — replace with real values ────────────────────────────
const data = [
  { name:"Hsinchu (Fab 12, 14, 15, 18)", lat:24.78, lon:121.00, value:850, region:"Taiwan", focal:false },
  { name:"Tainan (Fab 6, Fab 18)",       lat:23.00, lon:120.22, value:520, region:"Taiwan", focal:false },
  { name:"Kumamoto JASM",                lat:32.83, lon:130.62, value:55,  region:"Japan",  focal:true  },
  { name:"Phoenix Fab 21",               lat:33.45, lon:-112.07,value:50,  region:"USA",    focal:true  },
  { name:"Dresden ESMC",                 lat:51.05, lon:13.74,  value:40,  region:"Germany",focal:true  },
  { name:"Nanjing",                      lat:32.06, lon:118.80, value:40,  region:"China",  focal:false },
  { name:"Shanghai",                     lat:31.23, lon:121.47, value:90,  region:"China",  focal:false },
];

// ─── LAYOUT ─────────────────────────────────────────────────────
const width = 1088;        // 1200 - 56 - 56 padding
const height = 540;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);

// ─── PROJECTION ─────────────────────────────────────────────────
const projection = d3.geoNaturalEarth1();
const path = d3.geoPath(projection);

// ─── LOAD WORLD & DRAW ─────────────────────────────────────────
d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json")
  .then(world => {
    const countries = topojson.feature(world, world.objects.countries);
    projection.fitSize([width, height], countries);

    // countries
    svg.append("g")
      .selectAll("path")
      .data(countries.features)
      .join("path")
        .attr("class", "country")
        .attr("d", path);

    // marker scale — area proportional to value
    const rScale = d3.scaleSqrt()
      .domain([0, d3.max(data, d => d.value)])
      .range([0, 28]);

    // markers (back to front by value so small ones don't hide)
    const markers = svg.append("g")
      .selectAll("circle")
      .data(data.sort((a,b) => b.value - a.value))
      .join("circle")
        .attr("class", d => d.focal ? "marker focal" : "marker")
        .attr("cx", d => projection([d.lon, d.lat])[0])
        .attr("cy", d => projection([d.lon, d.lat])[1])
        .attr("r",  d => rScale(d.value));

    // labels for focal markers only — avoid label noise on all markers
    svg.append("g")
      .selectAll("text")
      .data(data.filter(d => d.focal))
      .join("text")
        .attr("class", "marker-label")
        .attr("x", d => projection([d.lon, d.lat])[0] + rScale(d.value) + 5)
        .attr("y", d => projection([d.lon, d.lat])[1] + 4)
        .text(d => `${d.name}  ${d.value}k`);

    // ─── LEGEND (bottom-left, size scale) ──────────────────────
    const legendData = [50, 200, 800];   // pick 3 representative values
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(40, ${height - 90})`);

    legend.append("text")
      .attr("class", "legend-title")
      .attr("y", -16)
      .text("Capacity (kwpm, 12-inch eq.)");

    legendData.forEach((v, i) => {
      const cx = i * 60 + 14;
      const r  = rScale(v);
      legend.append("circle")
        .attr("class", "marker")
        .attr("cx", cx).attr("cy", 28 - r)
        .attr("r", r);
      legend.append("text")
        .attr("x", cx).attr("y", 50)
        .attr("text-anchor", "middle")
        .attr("font-family", "var(--font-mono)")
        .attr("font-size", 10)
        .text(v);
    });
  });
</script>
</body>
</html>
```

## Variant — choropleth (revenue by country)

Replace the marker section with:

```js
// after countries are drawn, add fill scale:
const revData = new Map([
  ["USA", 0.42],
  ["CHN", 0.18],
  ["JPN", 0.09],
  // ...
]);

const colorScale = d3.scaleSequential()
  .domain([0, d3.max(revData.values())])
  .interpolator(d3.interpolate("var(--paper-edge)", "var(--accent)"));
  // Equivalent custom: d3.interpolate("#F4F3EE", "#1F3A5F")

svg.selectAll(".country")
  .attr("fill", d => {
    const v = revData.get(d.properties.iso_a3);   // depends on TopoJSON id field
    return v != null ? d3.interpolate("#F4F3EE","#1F3A5F")(v / 0.42) : "var(--land)";
  });
```

**Note**: world-atlas@2 TopoJSON uses **numeric ISO codes**, not alpha-3, by default. You need a lookup. The simplest fix:

```js
import { feature } from "topojson-client";
// Map ISO-3 codes from a lookup array; or use a richer source like:
// https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson
```

For most cases, easier to use a GeoJSON source that already has alpha-3 codes:
```js
d3.json("https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson")
  .then(world => {
    projection.fitSize([width, height], world);
    svg.append("g").selectAll("path")
       .data(world.features).join("path")
       .attr("class","country")
       .attr("d", path)
       .attr("fill", d => {
         const v = revData.get(d.properties.iso_a3);
         return v != null ? colorScale(v) : "var(--land)";
       });
  });
```

Add a horizontal color-ramp legend at bottom — see standard D3 sequential legend.

## Variant — arcs (supply chain or capital flow)

After markers are drawn, add great-circle paths:

```js
const arcs = [
  { from:[121.00, 24.78], to:[-112.07, 33.45], value: 50 },   // TW → AZ
  { from:[121.00, 24.78], to:[130.62, 32.83],  value: 30 },   // TW → JP
];

const arcGen = d3.geoPath(projection);

svg.append("g")
  .selectAll("path")
  .data(arcs)
  .join("path")
    .attr("d", d => arcGen({
      type: "LineString",
      coordinates: [d.from, d.to]
    }))
    .attr("fill", "none")
    .attr("stroke", "var(--highlight)")
    .attr("stroke-width", d => Math.sqrt(d.value) * 0.5)
    .attr("stroke-opacity", 0.65);
```

## Variant — regional zoom (e.g. only Asia-Pacific)

Filter `countries.features` before `fitSize`:

```js
const apacIso = new Set([392, 156, 158, 410, 360, 458, 702, 704, 360, 608, 36]);
const apac = {...countries, features: countries.features.filter(d => apacIso.has(d.id))};
projection.fitSize([width, height], apac);
```

This zooms to the bounding box of the filtered features.

## Common gotchas

- **TopoJSON `id` is numeric ISO**, not alpha-3. Either use a richer source or maintain a numeric→alpha-3 lookup.
- **Hong Kong, Taiwan, Macau** are politically sensitive. Default world-atlas does not show Taiwan as separate; some users will care. Document the source's treatment in the source line if it matters.
- **Mercator distorts** badly at high latitudes — never use it for "global" if the company operates near the poles (mining cos in Canada, oil in Norway, etc.). Use Natural Earth.
- **Marker overlap** at high density (e.g. multiple fabs in Hsinchu). Either jitter or use one marker per region with stacked sub-bars beside.
- **Don't label every marker** — labels turn the map into noise. Label the focal 3–5 only; let the reader hover or read the table beside.
- **Color the country fill by data, not by aesthetics.** If you fill countries arbitrarily, you imply meaning that isn't there.

## Pair with a side panel

For dense maps (more than 6 markers), pair the map with a small ranked table on the right showing top-N locations, value, % of total. The map shows geography; the table shows magnitude. Two-column figure: map (66% width) + table (34% width).

---

## Interactive variant — Leaflet + Carto Positron tiles

For exploratory use (sharing with PM, live presentation): swap the static D3 + topojson map for a real tile-based map with pan/zoom/hover. Use this when the deliverable is a standalone HTML link the recipient will open and poke at — not when it's going into a memo as a screenshot.

### Tech stack additions

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.js"></script>
<!-- Only if >30 markers: -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5/dist/MarkerCluster.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5/dist/leaflet.markercluster.js"></script>
```

Set the map container height explicitly in CSS — Leaflet renders 0px tall otherwise:
```css
#map { width: 100%; height: 540px; border: 1px solid var(--hairline); }
.leaflet-control-attribution {
  font-size: 9px !important;
  background: rgba(250,250,247,0.85) !important;
  color: var(--ink-3) !important;
}
```

### Why Carto Positron

Three tile-set options for editorial work:

| Tile set | URL | Use when |
|---|---|---|
| **Carto Positron** ← default | `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png` | Light grey, low-contrast, the workhorse — matches buy-side aesthetic |
| Carto Positron (no labels) | `https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png` | When markers are dense and you want minimum visual competition |
| Stadia Stamen Toner Lite | `https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png` | High-contrast B&W; very editorial, but harsh — only when the basemap is conceptually secondary |

Carto Positron is the default. Don't use Carto Dark, Carto Voyager, OSM standard, or anything with saturated colors — they fight the markers and look retail.

### Core template — markers on Leaflet

```js
// data: [{name, lat, lon, value, region, focal, unit?}]

const map = L.map("map", {
  center: [25, 100],          // initial center [lat, lon]
  zoom: 2,
  zoomControl: true,
  scrollWheelZoom: true,
  zoomSnap: 0.5,
  worldCopyJump: true,        // wraps markers across the dateline
});

// Tile layer
L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
  {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
  }
).addTo(map);

// Marker size scale (sqrt so area encodes value, not radius)
const rScale = d3.scaleSqrt()
  .domain([0, d3.max(data, d => d.value)])
  .range([5, 28]);

// Draw markers
const markerLayer = L.layerGroup().addTo(map);

data.forEach(d => {
  const m = L.circleMarker([d.lat, d.lon], {
    radius: rScale(d.value),
    fillColor: d.focal ? "#8B2635" : "#1F3A5F",
    fillOpacity: 0.55,
    color:     d.focal ? "#8B2635" : "#1F3A5F",
    weight: 1.5,
    opacity: 1,
  }).addTo(markerLayer);

  // Hover tooltip
  m.on("mouseover", (evt) => {
    showTip(
      `<b>${d.name}</b><br>
       <span class="num">${d3.format(",")(d.value)}</span> ${d.unit || "kwpm"}
       ${d.region ? `<br><span style="color:var(--neutral);">${d.region}</span>` : ""}`,
      evt.originalEvent
    );
  });
  m.on("mouseout", hideTip);
  m.on("mousemove", (evt) => positionTip(evt.originalEvent));

  // Click popup
  m.bindPopup(
    `<div style="font-family:var(--font-sans);font-size:11.5px;line-height:1.5;min-width:160px;">
       <strong style="font-family:var(--font-serif);font-size:14px;">${d.name}</strong><br>
       <span style="font-family:var(--font-mono);">${d3.format(",")(d.value)} ${d.unit || "kwpm"}</span><br>
       <span style="color:#6B6B6B;font-size:10.5px;">${d.region || ""}</span>
     </div>`,
    { closeButton: false, autoPan: true, maxWidth: 240 }
  );
});

// Fit bounds to data extent on load
const bounds = L.latLngBounds(data.map(d => [d.lat, d.lon]));
map.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 });

// Reset button (in the controls bar)
function resetView() { map.fitBounds(bounds, { padding: [40, 40], maxZoom: 5 }); }

// Legend — bottom-right corner, native Leaflet control
const legend = L.control({ position: "bottomright" });
legend.onAdd = function() {
  const div = L.DomUtil.create("div", "map-legend");
  div.style.background = "rgba(250,250,247,0.92)";
  div.style.padding = "8px 10px";
  div.style.border = "1px solid #D4D4CE";
  div.style.fontFamily = "var(--font-sans)";
  div.style.fontSize = "10px";
  div.style.color = "#4A4A4A";
  div.style.lineHeight = "1.5";
  const legendVals = [50, 200, d3.max(data, d => d.value)].filter(v => v);
  div.innerHTML = `
    <div style="font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
                color:#6B6B6B;margin-bottom:4px;">Capacity (kwpm)</div>
    ${legendVals.map(v => `
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="display:inline-block;width:${rScale(v)*2}px;height:${rScale(v)*2}px;
                     background:#1F3A5F;opacity:0.55;border-radius:50%;
                     border:1px solid #1F3A5F;"></span>
        <span style="font-family:var(--font-mono);">${d3.format(",")(v)}</span>
      </div>`).join("")}
    <div style="margin-top:6px;color:#8B2635;font-style:italic;">— Burgundy = focal</div>
  `;
  return div;
};
legend.addTo(map);
```

### Add filter pills (optional)

Filter markers by region using pills above the map:

```html
<div class="controls">
  <div class="controls-section">
    <span class="controls-label">Region</span>
    <div class="pills" id="region-pills"></div>
  </div>
  <button class="btn" onclick="resetView()">Reset view</button>
</div>
```

```js
// build pills from unique regions
const regions = [...new Set(data.map(d => d.region))];
const active = new Set(regions);
const pillsEl = document.getElementById("region-pills");
regions.forEach(r => {
  const p = document.createElement("span");
  p.className = "pill active";
  p.dataset.region = r;
  p.textContent = r;
  p.addEventListener("click", () => {
    if (active.has(r)) { active.delete(r); p.classList.remove("active"); }
    else               { active.add(r);    p.classList.add("active"); }
    redrawMarkers();
  });
  pillsEl.appendChild(p);
});

function redrawMarkers() {
  markerLayer.eachLayer(m => {
    const reg = m.options._region;   // see modification below
    if (active.has(reg)) m.setStyle({ opacity: 1, fillOpacity: 0.55 });
    else                 m.setStyle({ opacity: 0.05, fillOpacity: 0.05 });
  });
}

// In the marker creation loop, attach region as a custom option:
// L.circleMarker(..., { ..., _region: d.region })
```

### Clustering for dense maps (>30 markers)

```js
const cluster = L.markerClusterGroup({
  showCoverageOnHover: false,
  spiderfyOnMaxZoom: true,
  maxClusterRadius: 50,
  iconCreateFunction: function(c) {
    return L.divIcon({
      html: `<div style="background:#1F3A5F;color:#FAFAF7;
                         border-radius:50%;width:32px;height:32px;
                         display:flex;align-items:center;justify-content:center;
                         font-family:var(--font-mono);font-size:11px;font-weight:500;
                         border:2px solid #FAFAF7;box-shadow:0 1px 4px rgba(0,0,0,0.2);">
              ${c.getChildCount()}
            </div>`,
      className: "",
      iconSize: [32, 32],
    });
  },
});
data.forEach(d => cluster.addLayer(L.circleMarker([d.lat, d.lon], { /* ... */ })));
map.addLayer(cluster);
```

### Choropleth on Leaflet

For revenue-by-country, use GeoJSON polygons with colored fills. Heavier than the marker version — use only if shading countries is the message.

```js
// Load a richer GeoJSON with iso_a3 codes
d3.json("https://cdn.jsdelivr.net/gh/holtzy/D3-graph-gallery@master/DATA/world.geojson")
  .then(world => {
    const revData = new Map([["USA", 0.42], ["CHN", 0.18], ["JPN", 0.09]]);
    const colorScale = d3.scaleLinear()
      .domain([0, d3.max(revData.values())])
      .range(["#F4F3EE", "#1F3A5F"]);

    L.geoJSON(world, {
      style: f => ({
        fillColor: revData.has(f.properties.iso_a3)
                   ? colorScale(revData.get(f.properties.iso_a3))
                   : "#EAE8E0",
        weight: 0.5,
        color: "#FFF",
        fillOpacity: 0.8,
      }),
      onEachFeature: (f, layer) => {
        const v = revData.get(f.properties.iso_a3);
        if (v != null) {
          layer.on("mouseover", evt => showTip(
            `<b>${f.properties.name}</b><br><span class="num">${d3.format(".1%")(v)}</span> of revenue`,
            evt.originalEvent
          ));
          layer.on("mouseout", hideTip);
        }
      },
    }).addTo(map);
  });
```

### Arcs (supply-chain / capital flow) on Leaflet

Use `L.polyline` with a simple curve approximation, or `leaflet-arc` plugin for true great-circle arcs:

```js
const arcs = [
  { from: [24.78, 121.00], to: [33.45, -112.07], value: 50 },
];

arcs.forEach(a => {
  // Simple curved line (interpolated midpoint, offset up)
  const lat1 = a.from[0], lng1 = a.from[1];
  const lat2 = a.to[0],   lng2 = a.to[1];
  const midLat = (lat1 + lat2) / 2 + 10;   // bow upward
  const midLng = (lng1 + lng2) / 2;
  const points = [];
  for (let t = 0; t <= 1; t += 0.02) {
    // quadratic Bezier
    const lat = (1-t)*(1-t)*lat1 + 2*(1-t)*t*midLat + t*t*lat2;
    const lng = (1-t)*(1-t)*lng1 + 2*(1-t)*t*midLng + t*t*lng2;
    points.push([lat, lng]);
  }
  L.polyline(points, {
    color: "#8B2635",
    weight: Math.sqrt(a.value) * 0.5,
    opacity: 0.65,
  }).addTo(map);
});
```

### Interactive gotchas (in addition to the static ones above)

- **Map height must be set in CSS** before init — Leaflet measures the container on creation. If you set height after, call `map.invalidateSize()`.
- **Attribution is required** by Carto/OSM license. Make it small, but never remove it. Replace with empty string only if using a paid tile provider with different licensing.
- **`circleMarker` vs `marker`**: `circleMarker` size is in screen pixels (constant on zoom — what we want); `marker` size depends on tile zoom. Use `circleMarker` for data-driven dots.
- **Tooltip flicker**: bind `mouseover`/`mouseout` to the marker itself, not to a parent layer.
- **Pan/zoom resets data filters silently**: if a filter is active, redraw markers on `map.on("zoomend")` to ensure layer visibility persists.
- **Popups vs hover tooltips**: hover is for quick scanning; popup is for clicking through to detail. Don't show both at once — disable popup on hover via `closePopupOnClick: false` if needed.
- **Save dimensions before screenshot**: if the user needs to embed the dynamic map in a memo, advise them to set a fixed viewport before screenshot; the dynamic state doesn't carry into PNG.
