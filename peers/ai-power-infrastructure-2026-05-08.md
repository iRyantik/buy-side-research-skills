---
schema_version: 1
document_type: peer_deep_dive
peer_set_id: ai-power-infrastructure
created_at: 2026-05-08
source_policy: "CLAUDE.md §3"
input_screen: "screens/ai-data-center-power-2026-05-08.md"
companies:
  - VRT
  - ETN
  - GEV
  - CAT
  - GNRC
---

# AI 电力基础设施横向比较

**结论先行**：这不是一个干净的同质 peer set，而是 AI data-center power capex 的五个不同切面。**VRT** 是最纯直接受益，**ETN** 是质量更均衡的电气设备受益，**GEV/CAT/GNRC** 分别偏发电设备、power generation/备电、C&I backup power。当前只建议做 watchlist / quickread 收口，不建议直接形成 pair trade。

## 1. 横向矩阵

| 公司 | 暴露类型 | 最相关证据 | 需要相信什么 | 核心风险 |
|---|---|---|---|---|
| VRT | 直接 critical digital infrastructure | Q1 2026 organic sales +23.3%，adjusted operating profit +57.0%，FY2026 organic growth guide 上调到 +29% 到 +31%。来源：[Vertiv Q1 2026](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx)。 | AI data-center buildout 持续拉动 power / thermal content，且 pricing / margins 能守住。 | 估值和预期风险；市场可能已经 price in 高增长。 |
| ETN | 直接 electrical equipment，业务更分散 | Electrical Americas Q1 2026 sales +11%，margin 29.8%，data-center orders 按 trailing twelve-month 口径 +240%。来源：[Eaton Q1 2026](https://www.eaton.com/content/dam/eaton/company/investor-relations/quarterly-earnings/2026/q1/EatonReportsFirstQuarterEarningsPerShareof$2.45,RecordAdjustedEarningsPerShareof$2.72,Up13PercentOvertheFirstQuarterof2025.pdf)。 | Electrical backlog 能转收入，且不牺牲 margin。 | 业务分散降低纯度；order growth 正常化时 multiple 可能压缩。 |
| GEV | Grid / generation equipment | Q1 2026 equipment backlog 达 $164B，环比增加超过 $13B。来源：[GE Vernova Q1 2026](https://www.gevernova.com/news/press-releases/ge-vernova-reports-first-quarter-2026-financial-results)。 | Power bottleneck 持续拉动 generation 和 grid equipment demand。 | 长周期交付、turbine capacity、政策和 permitting 节奏。 |
| CAT | Power generation + broader machinery | Q1 2026 total sales/revenue 同比持平、operating margin 下降，但 Power & Energy sales 主要因 power generation turbines 增长。来源：[CAT Q1 2026](https://www.caterpillar.com/en/news/corporate-press-releases/h/1q-2026-financial-results.html), [CAT Q1 PDF](https://s7d2.scene7.com/is/content/Caterpillar/CM20260429-99f7c-e9118)。 | Power generation 能抵消 broader machinery cyclicality。 | 非 power 业务稀释 AI data-center signal。 |
| GNRC | C&I backup power，小市值 optionality | Q1 2026 C&I product sales +28%，其中包含向大型全球 data-center customers 的 shipments 增长。来源：[Generac Q1 2026](https://investors.generac.com/news/news-details/2026/Generac-Reports-First-Quarter-2026-Results/default.aspx)。 | Data-center C&I backlog 有持续性且对 margin 有利。 | Customer concentration、backlog quality、residential / cyclical mix。 |

## 2. Pair / No-Pair 判断

**基础判断**：本次 smoke run 没有足够干净的 pair trade。

原因：这 5 个 name monetization 的 value-chain 位置不同。VRT 是数据中心场内 power / thermal；ETN 是 diversified electrical；GEV 是 generation / grid equipment；CAT 是 broader machinery 里带 power generation；GNRC 是 backup power。除非进一步用模型把 exposure 标准化，否则 spread 会混进 factor、cycle 和 market-cap risk。

## 3. 后续可测试的 pair 候选

| Pair 候选 | 初步逻辑 | 为什么还没 ready |
|---|---|---|
| Long ETN / Short CAT | ETN 的 data-center electrical order evidence 更清楚；CAT 有更广的周期暴露和 margin pressure。 | CAT power generation 可能是被低估的 offset；需要 segment margin 和 order bridge。 |
| Long VRT / Short GNRC | VRT 的 critical infrastructure exposure 更直接；GNRC 更小、更混合。 | VRT valuation risk 可能主导；GNRC data-center backlog 还需要更多 source work。 |
| Long GEV / Short generic utility basket | Generation equipment 可能比 regulated utilities 更直接受益于 power bottleneck。 | 需要定义 utility basket，并补 rate-base / PPA data 和政策风险控制。 |

## 4. Recommended Funnel Outcome

Proceed with **VRT quickread** as the top direct exposure. Keep ETN as the quality comp and GEV/GNRC/CAT as read-through checks. Do not create pair-state artifacts until a relative-view thesis is supported by valuation, exposure normalization, and spread data.

## 5. 来源

- [Vertiv Q1 2026 results](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx)
- [Eaton Q1 2026 results](https://www.eaton.com/content/dam/eaton/company/investor-relations/quarterly-earnings/2026/q1/EatonReportsFirstQuarterEarningsPerShareof$2.45,RecordAdjustedEarningsPerShareof$2.72,Up13PercentOvertheFirstQuarterof2025.pdf)
- [GE Vernova Q1 2026 results](https://www.gevernova.com/news/press-releases/ge-vernova-reports-first-quarter-2026-financial-results)
- [Caterpillar Q1 2026 results](https://www.caterpillar.com/en/news/corporate-press-releases/h/1q-2026-financial-results.html)
- [Caterpillar Q1 2026 PDF](https://s7d2.scene7.com/is/content/Caterpillar/CM20260429-99f7c-e9118)
- [Generac Q1 2026 results](https://investors.generac.com/news/news-details/2026/Generac-Reports-First-Quarter-2026-Results/default.aspx)
