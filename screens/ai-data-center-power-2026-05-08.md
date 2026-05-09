---
schema_version: 1
document_type: candidate_screen
hypothesis_slug: ai-data-center-power
created_at: 2026-05-08
market_scope: US equities first
coverage_scope:
  - industrials
  - electrical_equipment
  - power_infrastructure
  - energy_exposure
source_policy: "CLAUDE.md §3"
input_prompt: "找 AI 数据中心电力基础设施受益股，美股优先，LS 双向，区分 direct exposure / indirect exposure / theme association。"
recommended_next_steps:
  stock_quickread: VRT
  peer_deep_dive:
    - VRT
    - ETN
    - GEV
    - CAT
    - GNRC
  claim_check: "Nvidia 是否和公用事业公司合作建设更灵活的 AI factory / data center power model"
---

# AI 数据中心电力基础设施候选筛选

**结论先行**：这条主题成立，但第一层应该筛直接 monetizing 的电气设备、热管理、备电和电力设备公司，而不是泛化成“所有电力股”。本轮样例建议进入横向比较的 5 个美股 name 是 **VRT, ETN, GEV, CAT, GNRC**；最适合单标的 quickread 的 top name 是 **VRT**。

## 1. 投资假设拆解

AI 数据中心扩张带来三类增量需求：

| 层级 | 需求 | 可验证指标 | 研究含义 |
|---|---|---|---|
| 数据中心场内 | 配电、UPS、热管理、机柜级 power chain | data-center orders, backlog, organic sales, margin | 最直接，适合先筛 long candidates |
| 电网 / 发电场外 | 并网、电网升级、燃气轮机、备用电源 | utility capex, equipment backlog, turbine orders | 可能大，但从需求到收入的时滞更长 |
| 主题联想 | “AI 用电”概念、泛能源叙事 | 需要具体订单或客户证明 | 默认不能当作 verified exposure |

宏观前提有来源支撑：IEA 预计全球 data center 电力消费到 2030 年可能较当前翻倍以上，达到约 945 TWh；EIA 也指出美国 data centers 在 2023 年约占美国总用电 4.4%，且新建数据中心推升局部电力需求压力。来源：[IEA Energy and AI](https://www.iea.org/reports/energy-and-ai), [EIA Today in Energy](https://www.eia.gov/todayinenergy/detail.php?id=65074)。

## 2. 候选漏斗

| 排序 | Ticker | 公司 | 暴露类型 | 已找到证据 | 来源质量 | 初步判断 |
|---:|---|---|---|---|---|---|
| 1 | VRT | Vertiv | 直接暴露 | Q1 2026 organic sales +23.3%，adjusted operating profit +57.0%，并把 FY2026 organic sales growth 指引上调到 +29% 到 +31%；公司定位是 data centers 的 critical digital infrastructure。 | A | 最纯的 data-center power / thermal public comp，适合 top quickread。 |
| 2 | ETN | Eaton | 直接 / electrical equipment | Q1 2026 Electrical Americas sales +11%，operating margin 29.8%，data center orders 按十二个月滚动口径 +240%。 | A | 质量更均衡，直接受益但集团更分散。 |
| 3 | GEV | GE Vernova | 间接 / generation and grid equipment | Q1 2026 equipment backlog 达 $164B，环比增加超过 $13B；管理层提到美国客户电力需求带来的 equipment orders。 | A | 电力瓶颈受益，但不是纯数据中心设备公司。 |
| 4 | CAT | Caterpillar | 准直接 / backup generation + 周期暴露 | Q1 2026 total sales/revenue 同比持平、operating margin 下降，但 Power & Energy sales 主要因 power generation turbines 增长。 | A | 有 data-center backup / power generation angle，但集团周期暴露稀释。 |
| 5 | GNRC | Generac | 准直接 / backup power | Q1 2026 C&I product sales +28%，管理层提到向大型全球 data center customers 的 shipments 增长。 | A | 小市值、高 beta 的 data-center backup angle，需验证 backlog quality。 |
| Watch | PWR | Quanta Services | 间接 / grid services | Q1 2026 revenue $6.2B，backlog 创纪录达 $35.3B；公司支持 electric infrastructure，但本次样例没有拆出 data-center-specific revenue。 | A | 适合作为电网建设受益监控项，暂不放入 top quickread。 |

本节来源：[Vertiv Q1 2026 results](https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx), [Vertiv company overview](https://investors.vertiv.com/), [Eaton Q1 2026 results](https://www.eaton.com/content/dam/eaton/company/investor-relations/quarterly-earnings/2026/q1/EatonReportsFirstQuarterEarningsPerShareof$2.45,RecordAdjustedEarningsPerShareof$2.72,Up13PercentOvertheFirstQuarterof2025.pdf), [GE Vernova Q1 2026 results](https://www.gevernova.com/news/press-releases/ge-vernova-reports-first-quarter-2026-financial-results), [Caterpillar Q1 2026 results](https://www.caterpillar.com/en/news/corporate-press-releases/h/1q-2026-financial-results.html), [Caterpillar Q1 2026 release PDF](https://s7d2.scene7.com/is/content/Caterpillar/CM20260429-99f7c-e9118), [Generac Q1 2026 results](https://investors.generac.com/news/news-details/2026/Generac-Reports-First-Quarter-2026-Results/default.aspx), [Quanta Services Q1 2026 results](https://investors.quantaservices.com/news-events/press-releases/detail/396/quanta-services-reports-first-quarter-2026-results/).

## 3. Direct / Indirect / Theme Classification

| 分组 | 标的 | 理由 |
|---|---|---|
| 直接暴露 | VRT, ETN | Data-center electrical / power / thermal orders 和 revenue 能直接对应公司披露。 |
| 准直接但业务混合 | GNRC, CAT | Backup generation / power generation 暴露存在，但 segment mix 和周期暴露更重要。 |
| 间接暴露 | GEV, PWR | 受益于 grid、generation 和 infrastructure bottleneck；收入链条隔了一层。 |
| 仅主题联想 | 没有具体 AI/data-center contract 证据的 utilities | 没有 filings、官方公告或具名合同时，不当作 verified exposure。 |

## 4. LS Direction

**Long candidates**: VRT, ETN, GEV, GNRC. VRT has the cleanest exposure, ETN has better diversified quality, GEV has grid/generation bottleneck leverage, GNRC has smaller-cap optionality.

**Short candidates**: No clean short clears the evidence bar in this smoke run. A real LS build should look for either valuation-only AI beneficiaries without order proof, or companies with weak electrical backlog versus priced-in AI expectations. Mark as `[需查证]` until a short thesis has direct source support.

## 5. Claim Check 边界测试

Claim tested: “Nvidia is working with Constellation, NextEra, and Vistra on more flexible, grid-supportive AI factories/data centers.”

**Verdict**: 合作本身 Likely；但“已经有签约收入、PPA 或可确认 revenue”这个外推 Unsupported。

| Claim 拆分项 | 已找到证据 | 来源质量 | 可外推程度 |
|---|---|---|---|
| Nvidia + utilities collaboration | Axios 报道 Nvidia 正在和 Constellation、NextEra、Vistra 合作探索更灵活的 AI factories / data centers。 | B | 合作 claim 可采信；不是直接收入证据。 |
| Signed supply / PPA / revenue | 本次快查没有找到签约、定价、量、revenue recognition 证据。 | D / none | 不能外推 monetization。 |

Source: [Axios, 2026-03-23](https://www.axios.com/2026/03/23/utilities-nvidia-emerald-ai-data-centers).

**Next action**: Do not log by default. Revisit only if an A-quality source appears or the claim becomes directly relevant to an active research topic.

## 6. 输出路由检查

| 步骤 | 结果 |
|---|---|
| `candidate-screener` | 产出本 screen，并把 universe 收窄到 5 个相关美股 name。 |
| `peer-deep-dive` | 使用 VRT, ETN, GEV, CAT, GNRC 做轻量矩阵和 pair/no-pair 判断。 |
| `stock-quickread` | 对 top-ranked direct exposure VRT 跑 quickread。 |
| `information-impact` | 已完成 Claim Check；因为 monetization 未确认，不写 inbox。 |
