# RKLB Driver Map

**结论先行**

RKLB 不应该按“火箭发射公司”单一 driver 建模。更稳的拆法是两条主线：`Launch Services = Electron/HASTE 发射节奏 + ASP/mix + Neutron option`，`Space Systems = spacecraft/components/manufacturing contracts + backlog conversion + project milestone timing`。最大披露缺口是 backlog、orders 和 delivery schedule 没有按 segment 拆开，不能把 $1.847bn backlog 机械分配给 Launch 或 Space Systems。

Source base: RKLB FY2025 10-K, filed 2026-02-26, SEC accession `0001819994-26-000013`; local evidence pack at `examples/financial-data-pull/us/rklb/`.

## Recommended model type

- Primary model artifact: DCF with integrated 3-statement forecast and separate `Revenue Build` sheet.
- Cross-check model artifact: comps can be added later, but peer lens should be split between Launch access / infrastructure and Space Systems / spacecraft components.
- Not recommended: a single consolidated-revenue CAGR model. It hides Space Systems project timing, Launch cadence / ASP uncertainty, and Neutron scenario risk.
- Machine driver input: `internal/driver-map/driver-map.json`.

## Reported Bucket -> Business Reality

| Reported bucket | Business reality | End-market / customer | Source / as-of | Gap |
|---|---|---|---|---|
| Launch Services | Electron dedicated/rideshare orbital launch, HASTE/suborbital and launch-related services; Neutron still development-stage option, not yet a historical revenue line. | Government and commercial spacecraft operators. | 10-K says Launch Services provides launch and launch-related services on dedicated or ride-share missions; Electron up to 300 kg to LEO; Neutron under development with expected 13,000 kg reusable LEO payload. `internal/financial-data/full-filing.md:247`, `internal/financial-data/full-filing.md:253`, `internal/financial-data/full-filing.md:258`, `internal/financial-data/full-filing.md:193`. | Annual launch count / ASP not in this extracted financial pack; use external launch manifest only as sourced operating KPI. |
| Space Systems | Spacecraft components, spacecraft manufacturing, optical systems, spacecraft design and on-orbit management; mostly product/project revenue, not recurring software-like revenue. | Commercial, aerospace prime contractors, U.S. government and international customers. | 10-K says Space Systems includes spacecraft components and manufacturing; used on over 1,800 missions as of Dec. 31, 2025. `internal/financial-data/full-filing.md:223`, `internal/financial-data/full-filing.md:249`, `internal/financial-data/full-filing.md:3385`. | Segment includes acquired assets and different product types; model needs product/service and contract timing, not a single unit driver. |
| Backlog | Contracted remaining performance obligations across the company. | Mostly government/commercial space programs; not segment-disclosed. | Backlog was $1.847bn as of Dec. 31, 2025; ~37% expected within 12 months. `internal/financial-data/full-filing.md:2462`. | No segment split. Treat as company-level visibility, not as segment backlog. |
| Geography | Customer billing location, not necessarily launch location or end-user demand. | U.S. is dominant; Japan rose sharply in FY2025; Canada fell after FY2024. | FY2025 revenue by billing location: U.S. $475.4m / 79%, Japan $65.6m / 11%, Canada $20.2m / 3%, rest of world $40.6m / 7%. `internal/financial-data/full-filing.md:3464`. | Do not treat geography as market demand by launch site. It is billing location. |

## Business Reality -> Model Driver

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| Launch Services | Launch cadence x average revenue per mission. | Dedicated vs rideshare, mission complexity/orbit, HASTE/suborbital mix, launch pad availability, Neutron timing. | Segment revenue, segment gross margin, cumulative successful missions, external annual launch count, announced multi-launch agreements. | Medium: segment revenue and margin are disclosed, but launch count/ASP are not in the pack. |
| Space Systems products | Contract awards and backlog conversion into spacecraft/component delivery milestones. | Product mix, MDA/defense/customer program timing, supply chain execution, GEOST contribution. | Space Systems product revenue, over-time revenue, contract assets/liabilities, backlog, major customers. | Medium-High: product/service revenue and recognition model are disclosed; orders by product are not. |
| Space Systems services | Services/on-orbit management and design/service work. | Installed mission base, customer renewals, integration with spacecraft/launch contracts. | Space Systems services revenue and gross profit. | Medium: services revenue is disclosed but service KPIs are not. |
| Gross margin | Segment mix and execution cost curve. | Launch utilization, mission mix, manufacturing scale, project cost-to-complete revisions, Space Systems product mix. | Launch gross margin, Space Systems gross margin, cumulative catch-up adjustments, contract loss provisions. | Medium: segment GP disclosed, but cost drivers require project detail. |
| Working capital / cash burn | Contract milestone billing, inventory build, capex, Neutron/R&D and equity/debt financing. | Customer advances, contract assets, inventory, PPE, R&D intensity. | Contract liabilities, inventory, capex, R&D, operating cash flow. | Medium-High for financial statement linkage; lower for operational root cause. |

## Driver Quality

| Driver | Rating | Why | Source / as-of | What would improve confidence |
|---|---|---|---|---|
| Segment revenue split | High | Launch and Space Systems revenue disclosed for FY2023-FY2025. Launch grew from $71.9m to $199.0m; Space Systems from $172.7m to $402.8m. | 10-K segment table. `internal/financial-data/full-filing.md:3385`; `internal/financial-data/financials.normalized.json`. | Quarterly segment trend and FY2026 guide. |
| Product/service split inside Space Systems | High | Space Systems product revenue disclosed separately from services: FY2025 products $371.6m, services $31.1m. | 10-K product/service table. `internal/financial-data/full-filing.md:3403`. | More granular component/manufacturing mix. |
| Launch cadence / ASP | Low-Medium | Company discloses cumulative successful missions and launch infrastructure capacity, but not extracted annual launch count or ASP by mission. | Cumulative missions and LC capacity in 10-K. `internal/financial-data/full-filing.md:189`, `internal/financial-data/full-filing.md:191`, `internal/financial-data/full-filing.md:216`. | Annual mission list, payload/customer mix and launch revenue per mission. |
| Backlog conversion | Medium | Backlog and 12-month expected recognition are disclosed at company level, but not by segment. | $1.847bn backlog and 37% within 12 months. `internal/financial-data/full-filing.md:2462`. | Backlog by segment and new order intake. |
| Customer concentration | Medium-High | FY2025 Government Customer was 28% of revenue; FY2024 MDA was 23%; FY2023 MDA and Northrop each 13%. | Customer concentration table. `internal/financial-data/full-filing.md:3452`. | Named contract-level schedule and renewal status. |
| Organic vs acquisition growth | Medium | GEOST contributed FY2025 revenue and operating loss; goodwill allocated to Space Systems. | GEOST acquisition note. `internal/financial-data/full-filing.md:2479`, `internal/financial-data/full-filing.md:2543`, `internal/financial-data/full-filing.md:2545`. | Ex-GEOST organic segment revenue and backlog. |

## Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| Launch Services revenue should be driven by mission cadence and ASP/mix. | company implied | Segment revenue + external annual launch manifest + announced mission mix. | ASP can be distorted by milestone timing, HASTE, launch-related services and customer financing. | Base case only after sourcing annual launches; otherwise sensitivity. |
| Space Systems should be modeled as contract/backlog conversion, not simple unit volume. | company disclosed / implied | Space Systems revenue, over-time revenue, backlog and contract balances. | Company-level backlog cannot be allocated by segment. | Base case at segment level; segment backlog split as scenario only. |
| Neutron is an option on future Launch revenue, not current historical actuals. | company disclosed | Separate Neutron module with launch date/ramp/ASP assumptions. | Folding Neutron into Electron growth hides development and timing risk. | Scenario module, not historical run-rate. |
| Government program timing is a major revenue risk. | company disclosed | Customer concentration and government-customer revenue share. | One unnamed Government Customer may represent multiple programs or one large program; disclosure is limited. | Sensitivity around award timing, shutdown/delay and concentration. |
| Geography mix indicates demand geography. | company disclosed but weak interpretation | Billing-location revenue only. | Billing location may not equal end user, launch location, or demand origin. | Use for disclosure context, not primary driver. |

## Weird Buckets / Senior Analyst Radar

**这里值得深挖**

- 怪异点：`Space Systems` 是最大 revenue bucket，但它混合了 spacecraft components、manufacturing、optical systems、design and on-orbit services。产品收入还是大量 over-time recognition，所以“产品”不等于一次性硬件销售。
- 可能说明：RKLB 的真实 model driver 更接近 defense/aerospace project execution + constellation/customer program awards，而不是纯“发射次数”。
- 可以问 AI：
  - FY2025 Space Systems 增长中，GEOST、MDA、Japanese customer/program 和 organic component demand 各贡献多少？
  - Launch Services 的 FY2025 revenue/mission 和 mission mix 是否说明 ASP 上行，还是只是 contract timing / HASTE / multi-launch financing影响？

## Implications for model / thesis

- 3-statement model：先按 `Launch Services` 和 `Space Systems` 建收入/毛利，别只用 consolidated revenue CAGR。
- DCF：Base case 用 backlog conversion + segment margin，而 Neutron 单独做 scenario / option value。
- Comps：RKLB 不能只跟 small launch 或 defense hardware比；需要至少两组 peer lens：Launch access / launch infrastructure、Space Systems / spacecraft components。
- Model update：每次财报优先更新 backlog、contract liabilities、segment revenue/gross profit、customer concentration、R&D/capex，而不是只 plug consolidated revenue。

## 可以问 AI

- “RKLB FY2025 Space Systems revenue growth ex-GEOST and ex-MDA 是多少？”
- “Electron annual launches、Launch Services revenue、gross profit 三者的 relationship 是否支持 ASP/margin expansion thesis？”
- “Neutron ramp 应该作为 base case、upside case 还是 option module？”

