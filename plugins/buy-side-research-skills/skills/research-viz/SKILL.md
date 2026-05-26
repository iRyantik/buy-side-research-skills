---
name: research-viz
description: Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.
---

# Research Viz

Create memo-ready and screenshot-ready HTML research visualizations paired with a saved topic artifact.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `skills/_shared/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for analysis method, sequencing, and routing judgment; unresolved facts stay as gap, hypothesis, or follow-up.

## 定位

`research-viz` 是 **supporting visualization skill**，不是主 research flow skill。它服务 `stock-quickread`、`mechanism-map`、`peer-deep-dive`、`alpha-thesis`、`research-journal` 等研究产物的可视化后处理，让已有研究更容易被 PM / IC 快速读懂。

它可以把：

- 研究文里的 peer table 变成 scatter
- mechanism / value-chain 说明变成 structure diagram
- valuation / sensitivity 结果变成 band / heatmap / SOTP
- price / event / consensus / revisions 结果变成更适合 memo 的 HTML 图

它**不替代**主研究文，也不应该在没有基准研究 artifact 的情况下自己发明完整 thesis。

## 图表类型

支持以下 18 类图表；默认静态 HTML，用户明确要求时可做 interactive 版：

| # | Chart | Reference file | 常见触发 |
|---|---|---|---|
| 1 | Global operations / footprint map | `references/global-map.md` | “画工厂/业务分布图” |
| 2 | Valuation band | `references/valuation-band.md` | “做 PE / EV-EBITDA band” |
| 3 | Waterfall / bridge | `references/waterfall-bridge.md` | “做 FCF / EBITDA / YoY bridge” |
| 4 | Sensitivity heatmap | `references/sensitivity-heatmap.md` | “做 DCF sensitivity” |
| 5 | SOTP stack | `references/sotp-stack.md` | “做 sum-of-the-parts 图” |
| 6 | Multi-panel cycle | `references/cycle-multipanel.md` | “multiple 还是 fundamentals” |
| 7 | Catalyst timeline | `references/catalyst-timeline.md` | “做 12 个月 catalyst roadmap” |
| 8 | Price + events overlay | `references/price-events-overlay.md` | “把股价和事件叠起来” |
| 9 | Peer scatter | `references/peer-scatter.md` | “做 growth vs margin / valuation scatter” |
| 10 | Business structure / value chain | `references/business-structure.md` | “画 value chain / segment structure” |
| 11 | Sankey | `references/sankey.md` | “做 flow / revenue source 图” |
| 12 | Correlation matrix | `references/correlation-matrix.md` | “做相关性热图” |
| 13 | Beat/miss heatmap | `references/beat-miss-heatmap.md` | “做 earnings beat / miss 热图” |
| 14 | Debt maturity + capital stack | `references/debt-maturity.md` | “做 debt ladder / capital stack” |
| 15 | Margin walk | `references/margin-walk.md` | “做 margin walk” |
| 16 | Consensus revisions | `references/consensus-revisions.md` | “做 estimate revision 图” |
| 17 | Concentration / Pareto | `references/concentration-pareto.md` | “做 concentration / pareto 图” |
| 18 | Cohort retention | `references/cohort-retention.md` | “做 cohort retention / NRR 图” |

无论哪一类，先加载 `references/design-tokens.md`；interactive 版再额外加载 `references/interaction-patterns.md`。

## 什么时候用

当用户已经有研究产物或明确研究问题，并且想：

- “把这篇研究文做成图”
- “把 mechanism-map 配一张系统图 / capability map”
- “把 peer compare 变成可贴 memo 的 chart”
- “把 DCF / SOTP / sensitivity 结果可视化”
- “把 price action、催化剂、估值 band 或 consensus 变化画出来”

不要用于：

- 替代主研究文：先有研究主文，再谈图
- 没有 source 的拍脑袋“做个好看的图”
- 纯品牌/营销/landing page 视觉
- 实时 dashboard、streaming monitor、交易终端

## 保存规则

本 skill 的 topic-side 保存 contract 固定如下：

- 必须绑定一个**基准 markdown 研究产物**
- 默认复用同一 stem，只把扩展名从 `.md` 换成 `.html`

例如：

```text
2026-05-25-mechanism-map-korea-vs-global-system-dossier.md
2026-05-25-mechanism-map-korea-vs-global-system-dossier.html
```

如果同一篇基准研究需要多张不同图，用最小 qualifier 追加在 stem 后，再保留 `.html`：

```text
2026-05-25-mechanism-map-korea-vs-global-system-dossier-peer-scatter.html
2026-05-25-mechanism-map-korea-vs-global-system-dossier-global-map.html
2026-05-25-mechanism-map-korea-vs-global-system-dossier-global-map-interactive.html
```

默认不要发明平行命名，如 `research-viz.html` 或 `YYYY-MM-DD-research-viz.html`。

如果用户没给明确基准研究 artifact，先解析或要求一个基准 markdown 主文，再保存 HTML。

## 输出 contract

- 产物是 **self-contained HTML**
- 默认从 `assets/template.html` 开始；interactive 时用 `assets/template-interactive.html`
- 图表必须有：
  - 标题
  - 副标题（单位 / 时间 / ticker / 口径）
  - source line
- 数字统一用 tabular numerals；单位写清 `%`、`x`、`bps`、货币代码等
- 缺失数据标 `n/a` 或在图底说明
- 如果图表依赖 topic 内某篇研究文的事实判断，图底 source line 与旁边的 markdown 说明必须能回到同一组 source

## 工作流

1. 识别图表类型：把用户请求映射到 18 类之一。
2. 识别基准研究 artifact：优先用用户指定的 `.md`；否则从当前 topic 最近相关主文里选一个明确基准。
3. 收集数据：优先复用基准研究文、topic `_cache/`、已有 source-backed tables；必要时才补 source。
4. 加载 `references/design-tokens.md` 和目标 chart reference；interactive 时再加载 `references/interaction-patterns.md`。
5. 从相应 template 起稿，不从零乱搭。
6. 写标题、副标题、source line、必要 callout。
7. 保存为绑定基准 stem 的 `.html` topic artifact。
8. 对话里只给简短说明：这张图画了什么、服务哪篇研究、存到哪里。

## 反模式自查

- 没有基准研究文，却自己补出完整 thesis
- 图表上的数字或结论没有 source
- 为了“好看”牺牲 buy-side 可读性
- 把 marketing 页面、hero、渐变卡片当研究图
- 直接输出 `research-viz.html` 而不绑定研究 stem
- 交付一个 HTML，但没有标题 / subtitle / source line
- 图比文更先下结论，甚至和基准研究文不一致

## 运行时资源

```text
skills/research-viz/
  SKILL.md
  skill.yaml
  assets/template.html
  assets/template-interactive.html
  references/design-tokens.md
  references/interaction-patterns.md
  references/*.md
  examples/*.html
```
