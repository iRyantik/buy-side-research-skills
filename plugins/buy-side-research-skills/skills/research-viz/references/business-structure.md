# Business structure / value chain

A tree or value-chain diagram showing how a company's segments, products, and upstream/downstream activities connect. Used for orienting the reader to "what does this company actually do".

## When to use

User asks: "org tree", "value chain", "supply chain", "segments and products", "business map", "how is it structured", "draw the company". Two main patterns:

- **Tree** (top-down): parent company → segments → product lines / regions. Useful for a conglomerate or multi-segment business.
- **Value chain** (left-to-right): raw materials → manufacturing → distribution → customer. Useful for industrial/commodity names.

Pick by question: "what does the company do" → tree. "Where in the chain does it play" → value chain.

## Required inputs

For a tree:
```js
const tree = {
  name: "TSMC",
  meta: "$95bn revenue, FY25E",
  children: [
    { name: "Advanced (≤7nm)", meta: "55% of rev", children: [
      { name: "3nm (N3 family)", meta: "$24bn" },
      { name: "5nm (N5 family)", meta: "$18bn" },
      { name: "7nm", meta: "$10bn" },
    ]},
    { name: "Mature (≥10nm)",  meta: "35% of rev", children: [
      { name: "10/16/20nm", meta: "$12bn" },
      { name: "28/40nm",    meta: "$15bn" },
      { name: "≥65nm",      meta: "$6bn" },
    ]},
    { name: "Packaging & test", meta: "10% of rev" },
  ]
};
```

For a value chain:
```js
const stages = [
  { name: "Wafer raw materials",    role: "Supplier",       co: ["SUMCO","Shin-Etsu"], plays: false },
  { name: "Equipment",              role: "Supplier",       co: ["ASML","AMAT","TEL"],  plays: false },
  { name: "Foundry (fab)",          role: "Where TSMC plays", co: ["TSMC","Samsung"],   plays: true  },
  { name: "Design / IP",            role: "Customer",       co: ["Apple","NVIDIA","AMD"], plays: false },
  { name: "Packaging (OSAT)",       role: "Adjacent",       co: ["ASE","Amkor"],         plays: false },
  { name: "Device OEM",             role: "End customer",   co: ["Apple","Dell"],        plays: false },
];
```

## Visual structure — tree

- Top-down hierarchical tree
- Each node: a rectangle (or rounded-corner with 2px radius) with the name in serif and `meta` in mono below
- Edges: 1px solid `--ink-3` lines, orthogonal (right-angle elbows, not curved)
- The company's "core" segments in `--accent`; supporting/adjacent in `--neutral`
- One focal segment may use `--highlight`

## Core template — tree (using d3.hierarchy)

```js
const margin = { top: 60, right: 24, bottom: 40, left: 24 };
const width = 1088, height = 520;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const root = d3.hierarchy(tree);
const layout = d3.tree()
  .size([innerW, innerH - 60])
  .separation((a, b) => a.parent === b.parent ? 1 : 1.3);
layout(root);

// orthogonal links
const linkPath = d3.linkVertical().x(d => d.x).y(d => d.y);
g.selectAll(".link")
  .data(root.links()).join("path")
    .attr("class", "link")
    .attr("d", linkPath)
    .attr("fill", "none")
    .attr("stroke", "var(--ink-3)")
    .attr("stroke-width", 1);

// nodes
const node = g.selectAll(".node")
  .data(root.descendants()).join("g")
    .attr("class", "node")
    .attr("transform", d => `translate(${d.x},${d.y})`);

const boxW = 160, boxH = 44;
node.append("rect")
  .attr("x", -boxW/2).attr("y", -boxH/2)
  .attr("width", boxW).attr("height", boxH)
  .attr("fill", "var(--paper)")
  .attr("stroke", d => d.depth === 0 ? "var(--accent)" : "var(--ink-3)")
  .attr("stroke-width", d => d.depth === 0 ? 2 : 1)
  .attr("rx", 2);

node.append("text")
  .attr("text-anchor", "middle").attr("y", -2)
  .attr("font-family", "var(--font-serif)")
  .attr("font-size", 12).attr("font-weight", 600)
  .attr("fill", "var(--ink)")
  .text(d => d.data.name);

node.append("text")
  .attr("text-anchor", "middle").attr("y", 12)
  .attr("class", "data-label")
  .attr("fill", "var(--ink-3)")
  .attr("font-size", 10)
  .text(d => d.data.meta || "");
```

## Core template — value chain (left-to-right)

```js
const stageW = 170, stageH = 80, gap = 22;
const totalW = stages.length * stageW + (stages.length - 1) * gap;
const startX = (1088 - totalW) / 2;
const y0 = 200;

stages.forEach((s, i) => {
  const x0 = startX + i * (stageW + gap);
  const isCore = s.plays;

  // stage box
  svg.append("rect")
    .attr("x", x0).attr("y", y0)
    .attr("width", stageW).attr("height", stageH)
    .attr("fill", isCore ? "var(--accent)" : "var(--paper)")
    .attr("stroke", isCore ? "var(--accent)" : "var(--hairline)")
    .attr("stroke-width", isCore ? 2 : 1)
    .attr("rx", 2);

  // role tag (small caps, above box)
  svg.append("text")
    .attr("x", x0 + stageW/2).attr("y", y0 - 8)
    .attr("text-anchor", "middle")
    .attr("font-size", 9).attr("font-weight", 600)
    .attr("letter-spacing", "0.08em")
    .attr("fill", isCore ? "var(--highlight)" : "var(--ink-3)")
    .text(s.role.toUpperCase());

  // stage name
  svg.append("text")
    .attr("x", x0 + stageW/2).attr("y", y0 + 28)
    .attr("text-anchor", "middle")
    .attr("font-family", "var(--font-serif)")
    .attr("font-size", 13).attr("font-weight", 600)
    .attr("fill", isCore ? "#FFF" : "var(--ink)")
    .text(s.name);

  // company examples
  s.co.forEach((c, j) => {
    svg.append("text")
      .attr("x", x0 + stageW/2).attr("y", y0 + 48 + j*13)
      .attr("text-anchor", "middle")
      .attr("class", "data-label")
      .attr("font-size", 10)
      .attr("fill", isCore ? "#FFF" : "var(--ink-2)")
      .text(c);
  });

  // arrow to next
  if (i < stages.length - 1) {
    const ax = x0 + stageW;
    svg.append("path")
      .attr("d", `M${ax},${y0+stageH/2} l${gap-4},0 m-6,-4 l6,4 l-6,4`)
      .attr("fill", "none")
      .attr("stroke", "var(--ink-3)").attr("stroke-width", 1);
  }
});
```

## Variants

- **Revenue-weighted segments**: in a tree, scale rectangle width ∝ revenue. Treemap-flavored hybrid.
- **Geographic overlay**: add small country flag chips or text labels to indicate where each segment operates.
- **Customer concentration on the chain**: annotate the customer stage with top customers and % of revenue.

## Gotchas

- **Don't reproduce the org chart from the 10-K verbatim**. The reader doesn't need every legal entity. Focus on revenue-meaningful segments only.
- **Limit depth to 3 levels** for trees — past that, readers lose orientation. If you need depth 4, break into multiple charts.
- **Avoid curved edges** — they look like a marketing infographic. Orthogonal / right-angle / straight is the buy-side look.
- **Don't color-code by "Claude's choice"** — let color encode meaning (focal segment, where the company plays, where they don't).
- **For value chains, be explicit about where the company plays** with the role tag. Don't make readers infer.

---

## Interactive variant — collapse/expand tree + hover detail

For trees: click any node with children to collapse/expand. Click again to re-expand. Hover any node for fuller detail (description, key metrics, etc).

### Required input (richer tree)

```js
const tree = {
  name: "TSMC",
  meta: "$95bn revenue, FY25E",
  description: "World's largest dedicated semiconductor foundry.",
  children: [
    {
      name: "Advanced (≤7nm)", meta: "55% of rev",
      description: "Leading-edge process nodes, primary growth engine.",
      children: [/* ... */]
    },
    // ...
  ],
};
```

### Controls

```html
<div class="controls">
  <span class="controls-label">Click nodes to expand or collapse</span>
  <button class="btn" onclick="expandAll()">Expand all</button>
  <button class="btn" onclick="collapseAll()">Collapse to level 1</button>
</div>
<div id="chart"></div>
```

### Core template

```js
const margin = { top: 60, right: 24, bottom: 40, left: 24 };
const width = 1088, height = 520;
const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const root = d3.hierarchy(tree);
root.x0 = innerW / 2;
root.y0 = 0;

function toggle(d) {
  if (d.children) { d._children = d.children; d.children = null; }
  else if (d._children) { d.children = d._children; d._children = null; }
}

function expandAll() {
  root.descendants().forEach(d => { if (d._children) { d.children = d._children; d._children = null; } });
  update();
}
function collapseAll() {
  root.descendants().forEach(d => { if (d.depth >= 1 && d.children) { d._children = d.children; d.children = null; } });
  update();
}

function update() {
  const layout = d3.tree()
    .size([innerW, innerH - 60])
    .separation((a,b) => a.parent === b.parent ? 1 : 1.3);
  layout(root);

  const links = g.selectAll(".link").data(root.links(), d => d.target.data.name + (d.target.parent ? "::" + d.target.parent.data.name : ""));
  const linkEnter = links.enter().append("path").attr("class","link")
    .attr("fill","none").attr("stroke","var(--ink-3)").attr("stroke-width", 1);
  linkEnter.merge(links)
    .transition().duration(250)
    .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));
  links.exit().transition().duration(250).attr("opacity",0).remove();

  const nodes = g.selectAll(".node").data(root.descendants(), d => d.data.name);
  const nodeEnter = nodes.enter().append("g").attr("class","node")
    .attr("transform", d => `translate(${d.parent ? d.parent.x0 : d.x},${d.parent ? d.parent.y0 : d.y})`)
    .style("cursor", d => (d.children || d._children) ? "pointer" : "default")
    .on("click", function(evt, d) {
      if (d.children || d._children) {
        toggle(d);
        update();
      }
    })
    .on("mouseover", function(evt, d) {
      d3.select(this).select("rect").attr("stroke", "var(--highlight)").attr("stroke-width", 2);
      if (d.data.description || d.data.meta) {
        showTip(
          `<b>${d.data.name}</b>
           ${d.data.meta ? `&nbsp;<span style="color:var(--neutral);">${d.data.meta}</span>` : ""}
           ${d.data.description ? `<br><span style="font-size:10.5px;color:var(--paper-edge);max-width:260px;display:block;margin-top:3px;">${d.data.description}</span>` : ""}
           ${(d.children || d._children) ? `<br><i style="color:var(--highlight-soft);font-size:10.5px;">Click to ${d.children ? "collapse" : "expand"}</i>` : ""}`,
          evt);
      }
    })
    .on("mouseout", function(evt, d) {
      d3.select(this).select("rect")
        .attr("stroke", d.depth === 0 ? "var(--accent)" : "var(--ink-3)")
        .attr("stroke-width", d.depth === 0 ? 2 : 1);
      hideTip();
    });

  const boxW = 160, boxH = 44;
  nodeEnter.append("rect")
    .attr("x", -boxW/2).attr("y", -boxH/2)
    .attr("width", boxW).attr("height", boxH)
    .attr("fill","var(--paper)")
    .attr("stroke", d => d.depth === 0 ? "var(--accent)" : "var(--ink-3)")
    .attr("stroke-width", d => d.depth === 0 ? 2 : 1)
    .attr("rx", 2);
  nodeEnter.append("text")
    .attr("text-anchor","middle").attr("y", -2)
    .attr("font-family","var(--font-serif)").attr("font-size", 12)
    .attr("font-weight",600).attr("fill","var(--ink)")
    .style("pointer-events","none")
    .text(d => d.data.name);
  nodeEnter.append("text")
    .attr("text-anchor","middle").attr("y", 12)
    .attr("class","data-label").attr("fill","var(--ink-3)").attr("font-size",10)
    .style("pointer-events","none")
    .text(d => d.data.meta || "");
  // Expand indicator (+) on collapsed nodes
  nodeEnter.append("text").attr("class","expand-indicator")
    .attr("text-anchor","middle").attr("y", boxH/2 + 14)
    .attr("font-family","var(--font-mono)").attr("font-size",14)
    .attr("fill","var(--highlight)").attr("font-weight",600)
    .style("pointer-events","none");

  nodeEnter.merge(nodes)
    .transition().duration(250)
    .attr("transform", d => `translate(${d.x},${d.y})`)
    .select(".expand-indicator")
      .text(d => d._children ? `+ ${d._children.length}` : "");

  nodes.exit().transition().duration(250)
    .attr("transform", d => `translate(${d.parent ? d.parent.x : d.x},${d.parent ? d.parent.y : d.y})`)
    .attr("opacity",0).remove();

  // Save current positions for next transition origin
  root.descendants().forEach(d => { d.x0 = d.x; d.y0 = d.y; });
}

update();
```

### Interactive gotchas

- **Visual indicator for collapsed nodes** — show "+ 3" below collapsed parents so users know more is hidden. Without this, depth-2+ content seems missing.
- **Animate transitions** — smooth expand/collapse helps users track which branch they're modifying.
- **Tooltip is the right place for long descriptions** — keep node labels short ("Cloud", "Advanced (≤7nm)"), put the paragraph in hover.
- **Click on the box, not the label** — make the entire rect clickable, not just the text. Set `pointer-events:none` on the text elements.
