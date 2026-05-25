# Sankey diagram

Flow diagram where the width of a band represents the volume of flow between source and destination nodes. Used for capital flows, customer migration, M&A paths, revenue decomposition by source-and-destination, supply-chain logistics.

## When to use

User asks: "flow of capital", "customer migration", "revenue by source and destination", "deal path", "logistics flow", "where does money come from and go to". Sankey shines when there are 2–4 stages with many-to-many connections; less great for simple A→B flows (use a bridge instead).

## Required inputs

```js
const sankeyData = {
  nodes: [
    { name: "North America" },     // 0
    { name: "Europe" },             // 1
    { name: "Asia ex-China" },      // 2
    { name: "China" },              // 3
    // products (middle layer)
    { name: "iPhone" },             // 4
    { name: "Services" },           // 5
    { name: "Mac" },                // 6
    { name: "Wearables" },          // 7
    // channels (right layer)
    { name: "Direct retail" },      // 8
    { name: "Carrier / partner" },  // 9
    { name: "Online" },             // 10
  ],
  links: [
    { source: 0, target: 4, value: 80 },
    { source: 0, target: 5, value: 60 },
    { source: 1, target: 4, value: 45 },
    // ...
    { source: 4, target: 8, value: 40 },
    { source: 4, target: 9, value: 80 },
    { source: 4, target: 10, value: 50 },
  ],
};
```

Nodes can be 2 columns (simple flow) or 3+ columns (multi-stage). Links must be acyclic.

## Visual structure

- 2–4 vertical columns of nodes (rectangles), each column representing a stage
- Links: filled curved bands, width ∝ value
- Node fill in `--accent` (column 1) shifting to `--accent-soft` and `--neutral` for downstream
- Link fill: link-source color at low opacity (0.25–0.35), so the eye follows the upstream
- Labels on each node, with value annotation

## Core template — uses d3-sankey

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12"></script>
```

```js
const margin = { top: 24, right: 80, bottom: 24, left: 80 };
const width = 1088, height = 580;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const sankey = d3.sankey()
  .nodeWidth(14)
  .nodePadding(14)
  .extent([[0, 0], [innerW, innerH]]);

const graph = sankey({
  nodes: sankeyData.nodes.map(d => ({...d})),
  links: sankeyData.links.map(d => ({...d})),
});

// links
g.append("g")
  .attr("fill", "none")
  .selectAll("path")
  .data(graph.links).join("path")
    .attr("d", d3.sankeyLinkHorizontal())
    .attr("stroke", "var(--accent)")
    .attr("stroke-opacity", 0.25)
    .attr("stroke-width", d => Math.max(1, d.width));

// nodes
g.append("g")
  .selectAll("rect")
  .data(graph.nodes).join("rect")
    .attr("x", d => d.x0)
    .attr("y", d => d.y0)
    .attr("height", d => d.y1 - d.y0)
    .attr("width", d => d.x1 - d.x0)
    .attr("fill", "var(--accent)");

// node labels
g.append("g")
  .selectAll("text")
  .data(graph.nodes).join("text")
    .attr("x", d => d.x0 < innerW / 2 ? d.x1 + 6 : d.x0 - 6)
    .attr("y", d => (d.y0 + d.y1) / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", d => d.x0 < innerW / 2 ? "start" : "end")
    .attr("font-family", "var(--font-sans)")
    .attr("font-size", 11)
    .attr("fill", "var(--ink)")
    .text(d => d.name);

// value labels (mono, alongside name)
g.append("g")
  .selectAll("text")
  .data(graph.nodes).join("text")
    .attr("x", d => d.x0 < innerW / 2 ? d.x1 + 6 : d.x0 - 6)
    .attr("y", d => (d.y0 + d.y1) / 2 + 14)
    .attr("text-anchor", d => d.x0 < innerW / 2 ? "start" : "end")
    .attr("class", "data-label")
    .attr("font-size", 10)
    .attr("fill", "var(--ink-3)")
    .text(d => d3.format(",")(d.value));
```

## Variants

- **Color links by category**: e.g. color each link by the source node's color. Useful for tracking "where does each region's revenue go".
- **Animated flow** (only if interactive context): pulses along link paths. NOT for memo screenshots — restraint.
- **Two-stage waterfall hybrid**: combine sankey on the left (revenue mix) with a vertical bar on the right (waterfall down to EBITDA). Custom layout — niche.

## Gotchas

- **Don't use Sankey for fewer than 3 sources or 3 destinations** — it's overkill. A stacked bar communicates better.
- **Total in must equal total out** at every interior node. If it doesn't, your data has gaps; flag it.
- **Avoid >25 nodes** — readability collapses fast. If your data is bigger, aggregate.
- **Label every node with both name and value**. Sankey is rich; readers need the anchor numbers.
- **Don't cross link bundles unnecessarily**. d3-sankey does its best automatically; if it still crosses heavily, reorder your nodes manually using `node.fixedValue` or rearrange the data.
- **Pick a sensible direction**: source on left, destination on right. Don't reverse without a clear reason.

---

## Interactive variant — hover link + click node to filter flow paths

Hover any link for the source→destination pair and value. Click any node to filter the entire Sankey to only the paths that flow through that node (others fade). Click again to clear.

### Controls

```html
<div class="controls">
  <span class="controls-label">Hover links for detail · Click a node to filter paths</span>
  <button class="btn" onclick="clearNodeFilter()">Clear filter</button>
</div>
<div id="chart"></div>
```

### Core template

```js
let selectedNode = null;

const margin = { top: 24, right: 80, bottom: 24, left: 80 };
const width = 1088, height = 580;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const sankey = d3.sankey()
  .nodeWidth(14).nodePadding(14)
  .extent([[0,0],[innerW, innerH]]);

const graph = sankey({
  nodes: sankeyData.nodes.map(d => ({...d})),
  links: sankeyData.links.map(d => ({...d})),
});

// Compute which nodes are reachable from a starting node (both directions)
function reachableFrom(node) {
  const reachable = new Set([node]);
  // Downstream
  const downQueue = [node];
  while (downQueue.length) {
    const n = downQueue.shift();
    (n.sourceLinks || []).forEach(l => {
      if (!reachable.has(l.target)) { reachable.add(l.target); downQueue.push(l.target); }
    });
  }
  // Upstream
  const upQueue = [node];
  while (upQueue.length) {
    const n = upQueue.shift();
    (n.targetLinks || []).forEach(l => {
      if (!reachable.has(l.source)) { reachable.add(l.source); upQueue.push(l.source); }
    });
  }
  return reachable;
}

function linkInFlow(link, node) {
  if (!node) return true;
  const reachable = reachableFrom(node);
  return reachable.has(link.source) && reachable.has(link.target) &&
         (link.source === node || link.target === node ||
          // link is on a path through the node — check if source and target are both in flow
          isOnPath(link, node));
}
function isOnPath(link, node) {
  // Simplified: link is in flow if its source can reach node OR node can reach its target
  const reach = reachableFrom(node);
  return reach.has(link.source) || reach.has(link.target);
}

// Draw links
const linksG = g.append("g").attr("fill","none");
const linkPaths = linksG.selectAll("path").data(graph.links).join("path")
  .attr("class","sankey-link")
  .attr("d", d3.sankeyLinkHorizontal())
  .attr("stroke","var(--accent)")
  .attr("stroke-opacity", 0.25)
  .attr("stroke-width", d => Math.max(1, d.width))
  .style("cursor","pointer")
  .on("mouseover", function(evt, d) {
    d3.select(this).attr("stroke-opacity", 0.55);
    showTip(
      `<b>${d.source.name}</b> → <b>${d.target.name}</b><br>
       Flow: <span class="num">${d3.format(",")(d.value)}</span>`, evt);
  })
  .on("mouseout", function() {
    d3.select(this).attr("stroke-opacity", linkInFlow(d3.select(this).datum(), selectedNode) ? 0.25 : 0.04);
    hideTip();
  });

// Draw nodes
const nodesG = g.append("g");
const nodeRects = nodesG.selectAll("rect").data(graph.nodes).join("rect")
  .attr("x", d => d.x0).attr("y", d => d.y0)
  .attr("height", d => d.y1 - d.y0).attr("width", d => d.x1 - d.x0)
  .attr("fill","var(--accent)")
  .style("cursor","pointer")
  .on("mouseover", function(evt, d) {
    d3.select(this).attr("fill","var(--highlight)");
    showTip(
      `<b>${d.name}</b><br>
       Total flow: <span class="num">${d3.format(",")(d.value)}</span>
       ${selectedNode === d ? "" : `<br><i style="color:var(--highlight-soft);font-size:10.5px;">Click to filter</i>`}`, evt);
  })
  .on("mouseout", function(evt, d) {
    d3.select(this).attr("fill", d === selectedNode ? "var(--highlight)" : "var(--accent)");
    hideTip();
  })
  .on("click", function(evt, d) {
    selectedNode = (selectedNode === d) ? null : d;
    applyFilter();
  });

// Node labels
g.append("g").selectAll("text").data(graph.nodes).join("text")
  .attr("class","node-label")
  .attr("x", d => d.x0 < innerW/2 ? d.x1 + 6 : d.x0 - 6)
  .attr("y", d => (d.y0 + d.y1) / 2).attr("dy","0.35em")
  .attr("text-anchor", d => d.x0 < innerW/2 ? "start" : "end")
  .attr("font-size", 11).attr("fill","var(--ink)")
  .style("pointer-events","none")
  .text(d => d.name);

g.append("g").selectAll("text").data(graph.nodes).join("text")
  .attr("class","data-label node-val")
  .attr("x", d => d.x0 < innerW/2 ? d.x1 + 6 : d.x0 - 6)
  .attr("y", d => (d.y0 + d.y1) / 2 + 14)
  .attr("text-anchor", d => d.x0 < innerW/2 ? "start" : "end")
  .attr("font-size", 10).attr("fill","var(--ink-3)")
  .style("pointer-events","none")
  .text(d => d3.format(",")(d.value));

function applyFilter() {
  linkPaths.attr("stroke-opacity", d => linkInFlow(d, selectedNode) ? 0.4 : 0.04);
  nodeRects.attr("fill", d => {
    if (!selectedNode) return "var(--accent)";
    return d === selectedNode ? "var(--highlight)"
      : reachableFrom(selectedNode).has(d) ? "var(--accent)" : "var(--neutral)";
  });
}

function clearNodeFilter() { selectedNode = null; applyFilter(); }
```

### Interactive gotchas

- **Hover on link increases opacity** (0.25 → 0.55) — gives a tactile feel without changing color. Don't switch to `--highlight` on link hover; it conflicts visually with selected state.
- **Path filtering uses BFS upstream AND downstream** from the clicked node — so the filter shows the complete flow that touches that node, both where it comes from and where it goes.
- **Dimmed links go to 4% opacity** (almost invisible but still there as a hint that the chart is complete). Don't fully hide — the global context matters.
- **The Sankey computes positions once** on initial layout; filtering doesn't reflow the diagram (would be disorienting). Just dims/highlights existing geometry.
