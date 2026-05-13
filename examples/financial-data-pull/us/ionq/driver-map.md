## Driver Map

**结论先行：IONQ 是一个 pre-revenue 规模的量子平台公司，收入来源高度混合（QCaaS + hardware project + acquired entity contribution + services），但披露层面完全不拆分。最大建模缺口是无法追踪 any volume / price / backlog conversion KPI；$370M RPO 是目前唯一可用的前瞻指标。Model 架构只能走 bookings-driven scenario 路线，无法 single base case。**

## Reported Bucket → Business Reality

IONQ 为单 operating segment（10-K Note on Segment），不披露任何业务线收入拆分。以下业务现实从 10-K Item 1 和 MD&A 推断：

| Reported bucket | Business reality | End-market / customer | Source / as-of | Gap |
|---|---|---|---|---|
| QCaaS（quantum-computing-as-a-service） | 客户通过 AWS Braket / Azure Quantum / Google Cloud Marketplace / IonQ 自有云平台按使用付费访问 trapped-ion QPU | 企业 R&D teams、学术机构、政府实验室 | 10-K Item 1, p.4 | 无 qubit-hour 用量、pricing、utilization rate、客户数披露 |
| Direct Access / Preferred Compute Agreements | 与 select customers 签订年化 commitment，含 reserved 执行窗口、concierge 级应用支持、early access 下一代硬件 | 政府 / defense、大型企业 | 10-K Item 1, p.7–8 | 无客户数、合同价值、renewal rate 披露 |
| Specialized quantum computing hardware sales | 向客户销售 partial 或完整 on-premises 量子计算系统，含安装、集成、维护 | 政府 / defense、大型企业、national labs | 10-K Item 1, p.7; MD&A 2025 revenue increase driver | 不披露交付数量、ASP、backlog |
| Quantum networking / security / sensing products（收购组合） | id Quantique（QKD + 网络安全）、Vector Atomic（原子钟）、Capella Space（SAR 卫星成像）、Skyloom（量子网络）的产品组合 | 政府 / defense、金融、通信 | 10-K Item 1, p.5; FY2025 收购披露 | 不按 acquisition entity 拆分收入；Capella DaaS 为新增收入线 |
| Professional services | 算法开发协助、use case 识别、应用集成支持 | 与上面客户重叠 | 10-K Item 1, p.4 | 不单独披露 services revenue |
| Data-as-a-Service（Capella Space） | SAR 卫星成像数据产品，通过 satellite network 交付 | 政府 / defense、ISR、地理空间 | 10-K Item 1, p.4; 10-K p.60（satellite depreciation mentioned） | 刚在 FY2025 通过收购获得，极度早期 |

## Business Reality → Model Driver

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| **QCaaS** | 活跃客户数 × 平均 consumption（qubit-hours） | # of cloud partners、tier-1 客户 onboarding | 无（公司不披露）；proxy = cloud marketplace reviews / gov contract wins | **Low** |
| **Direct Access / Preferred Agreements** | 新签年化合同价值（ACV） | 客户留存率 / 续约率 | 无直接披露；proxy = RPO change（$370M as of Dec 2025） | **Low** （existential RPO 含 hardware + service 混合） |
| **Hardware sales（on-premises）** | 交付项目数 × contract value | 政府 / defense procurement cycle | 无直接披露；proxy = RPO change、MD&A 定性归因 | **Low** |
| **Acquired products（networking / sensing / security / DaaS）** | 各标的独立 revenue run-rate | 收购整合进度、cross-sell 协同 | 无；acquisition 均未单独披露 revenue | **Low** （收购主动机为获取技术和人才，非即期收入贡献） |
| **Professional services** | 人员规模 × billable utilization | 合同 scope 变化 | 无 | **Low** |
| **Total Revenue** | Bookings / contract wins（hardware project 驱动）+ acquisitions step-in | 政府 contract 节奏（不规律、大额） | RPO、Cash from operations、S&M spend vs. new bookings ratio | **Medium** （RPO 为唯一可观察 total revenue proxy） |

### Revenue Trend & Growth Composition（from financials.md）

| FY | Revenue | YoY | 增长归因（MD&A 原文） | 隐含逻辑 |
|---|---|---|---|---|
| 2022 | $11.1M | — | — | 早期 QCaaS + 少量 services |
| 2023 | $22.0M | +98% | — | 云渠道扩张 |
| 2024 | $43.1M | +96% | — | QCaaS + 开始有 hardware project |
| 2025 | $130.0M | +202% | "progress on arrangements to build specialized quantum computing hardware, as well as increased revenue as a result of acquisitions" | 硬件项目交付（可能含 AQSOA / government contract）+ 收购合并收入 |

FY2025 的大幅跳升推测来自：
- 与政府 / defense 的大额硬件 build contract 进入 revenue recognition
- id Quantique、Vector Atomic、Capella Space、Lightsynq 等 acquisition 的合并收入贡献（4+ entities 合计贡献应达 $30–50M 级别）
- 但 10-K 不拆分 organic vs. acquired revenue growth，无法确认

## Driver Quality

| Driver | Rating | Why | Source / as-of | What would improve confidence |
|---|---|---|---|---|
| **RPO as forward revenue proxy** | Medium | $370M total RPO（funded + unfunded）是 IONQ 唯一硬数字；但含长期 government contracts，转换为收入的 timing 高度不确定 | 10-K Note, p.F-XX | 公司分拆 funded vs. unfunded、或披露 backlog conversion timing |
| **Customer concentration risk** | Medium | "much of our revenue is concentrated in a few customers" — risk factor，与 RPO 集中在少数合同一致 | 10-K Risk Factors, p.16 | 前 5 / 前 10 客户收入占比 |
| **QCaaS as % of revenue** | Low | 公司不披露云收入占比；'Forte' / 'Tempo' 商用系统投入云渠道，但 utilization 未知 | N/A | QCaaS 单独披露 |
| **Organic vs. acquired growth** | Low | '25 并购前后拉无法剥离；至少 4 个 acquisition entities 在 '25 贡献 >6 个月收入 | N/A | Organic revenue disclosure |
| **Gross margin trajectory** | Low | Cost of revenue 增长（+276%）快于 revenue（+202%），gross margin 在恶化；但 mix shift（hardware vs. cloud vs. services）不明 | financials.md; MD&A | Segment-level margin |
| **SBC as real cost** | High | SBC $317M vs. revenue $130M，是 operating loss 最大驱动；稀释效应体现在 share count（197M → 280M） | financials.md | —（事实，非低质量） |
| **Bookings / qualified pipeline** | Low | 公司不披露订单指标；无 pipeline visibility | N/A | 订单量 / book-to-bill |

## Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| RPO 代表可观测的前瞻收入指标 | company disclosed | RPO change + 40% / 12-month conversion | 含 unfunded 订单；government contracts 可能被取消或延迟 | **Scenario only**：按 40% / 12-month 实现 + 剩余分 2-3 年 |
| Hardware sales 为主要 FY2025 增长驱动 | company implied（MD&A） | MD&A 定性表述；RPO 增量（$370M 较上期） | 无法量化 hardware vs. acquired vs. QCaaS 各自贡献 | Base case 不做 allocation；sensitivity 设 organic step-up 范围 |
| FY2026 revenue 依赖 SkyWater 等收购合并 | researcher assumption | 已披露 pending acquisitions + 历史 acquisitive growth pattern | 收购可能不完成或不协同 | **Scenario only**：区分 organic 和 acquired |
| QCaaS consumption 按 qubit-hour 定价 | researcher assumption | 行业 proxy（Rigetti $/sec、IBM $/min） | IonQ 实际 pricing 模型不同 | 不作为 model line；只在 qualitative 层面讨论 |
| Capella DaaS 和 quantum sensing 短期贡献低 | researcher assumption | 刚收购、无业绩记录；类比早期 satellite data 公司 | 低估上行 | 放在 upside scenario；base case ~$0 |

## Senior Analyst Radar

**这里值得深挖**

- **怪异点**：FY2025 Revenue 从 $43M 跳升到 $130M（+202%），但公司 MD&A 归因给的定性描述（"progress on arrangements to build specialized quantum computing hardware, as well as increased revenue as a result of acquisitions"）没有 split acquired vs organic、没有 contract award 规模、没有 backlog 变化解释。$370M RPO 是年底余额，缺乏年初对比。
- **可能说明**：公司可能有意不拆分收入构成，以避免暴露 organic QCaaS 增长不够快（2024 年 $43M → 2025 年假设剔除 acquisitions 可能仅 $50–60M），或硬件销售本身是 lumpy project-based 而非 recurring。
- **可以问 AI**：用 edgartools 对比 FY2024 10-K 的 RPO 和 FY2025 的 RPO，算出 annual RPO 增量；这个增量比 reported revenue 更能反映真实 booking traction。
- **可以问 AI**：对比 IONQ vs. Rigetti / D-Wave 的 revenue 披露 granularity，看同业是否在做 segment 拆分。

## Implications for model / thesis

- **Model 不能做 standard revenue build**：无 customer count、无 ACV、无 pricing、无 utilization。RPO 驱动的 revenue model（booking-driven）是唯一路线。
- **Cost structure modeling**：R&D 和 S&M 以 SBC 为绝对大部分（SBC/total opex ~60%），cash opex 相对小；model 必须区分 cash vs non-cash opex。
- **Acquisition accounting complexity**: FY2025 及 FY2026 的 Revenue 含多个 acquisition step-in；model 应要求 'organic' vs 'acquired' pro-forma 调整。
- **Valuation 极其困难**：无正利润、无正 FCF、无可靠 peer comp（Rigetti/D-Wave 同样 pre-revenue）；market cap 由 quantum theme sentiment + cash balance 而非 fundamentals 驱动。
- **推荐 model architecture**：
  - Section 1: RPO bridge（opening + new bookings − recognized revenue = closing）
  - Section 2: Revenue scenario（optimistic → conservative，top-down 源于 RPO burn）
  - Section 3: Cost structure（cash vs non-cash）
  - Section 4: Balance sheet focus（cash run-rate / dilution）
  - Section 5: Reverse DCF（当前 EV 隐含的 2030 revenue × margin 假设）

## 可以问 AI

- 对比 FY2024 和 FY2025 的 RPO、deferred revenue、unearned revenue 变化，量化 annual bookings implied。
- 查看 IONQ 的 8-K / 合同公告（与 AWS/Azure/Google 的 agreement 更新、material definitive agreements）。
- 对比 Rigetti Computing（RGTI）和 D-Wave Quantum（QBTS）的 revenue 披露 granularity，看行业标准是否允许更细拆分。
