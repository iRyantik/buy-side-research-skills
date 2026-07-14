---
schema_version: 1
document_type: peer_deep_dive
peer_set_id: kr-defense
created_at: 2026-05-15
source_policy: "Sub-Agent Evidence Protocol: evidence cards only; main-agent synthesis and URL spot-check required"
runtime_note: "Example run completed by main agent using evidence-card discipline; no sub-agent wrote conclusions."
companies:
  - Hanwha Aerospace (012450.KS)
  - Hyundai Rotem (064350.KS)
  - Korea Aerospace Industries / KAI (047810.KS)
  - LIG Defense&Aerospace / LIG Nex1 (079550.KS)
  - Hanwha Systems (272210.KS)
---

# 韩国防务上市公司 Peer Deep Dive

**结论先行**：这组 Korean defense 不是简单同质化军工篮子，而是同一个出口周期下的五个不同变现口径。**Hyundai Rotem** 当前最像“利润率已经兑现、订单仍有可见度”的执行型标的；**Hanwha Aerospace** 是规模和产业整合锚，但集团化后包含 shipbuilding / aerospace / ground defense，纯防务读数要拆；**LIG Defense&Aerospace** 和 **Hanwha Systems** 更偏 missile / radar / C4I / defense electronics optionality，市场给的是稀缺性和高端化溢价；**KAI** 是 aircraft / KF-21 / FA-50 长周期订单兑现，2026 可能更像 revenue inflection，而不是 2025 已经完全利润化。

| 公司 | 初步方向 | 一句话理由 |
|---|---|---|
| Hyundai Rotem | 优先加深 | 2025 OP margin 约 17.2%，order backlog 接近 KRW 29.8T，K2 / rail 同时进入交付兑现期。 |
| Hanwha Aerospace | 核心锚，需拆分 | 2025 consolidated revenue / OP 最大，但 Hanwha Ocean 并表后必须分开看 ground defense、aerospace、shipbuilding。 |
| LIG Defense&Aerospace | 第二梯队高质量候选 | guided weapons / air-defense 出口带动增长，但市值已接近 Rotem，需验证 backlog 质量和 missile margin 可持续性。 |
| KAI | 中长期 watchlist | backlog 约 KRW 27.3T，KF-21 / FA-50 是核心变量；2025 margin 仍低于 Rotem / Hanwha ground defense。 |
| Hanwha Systems | 谨慎观察 | defense electronics 很有战略价值，但 2025 OP margin 约 3.4%，Philly Shipyard / PPA 成本拖累，估值需要更强盈利兑现。 |

第一优先行动：先做 **Hyundai Rotem defense vs rail standalone driver-map**，确认 K2 出口订单的毛利率、交付节奏、政策融资和 rail backlog 是否一起支撑当前估值；第二步再拆 Hanwha Aerospace 的 ground defense 与 Hanwha Ocean 并表影响。

## 0. 任务定义

- **公司列表**：Hanwha Aerospace、Hyundai Rotem、KAI、LIG Defense&Aerospace、Hanwha Systems。
- **研究目的**：建立 Korean defense 横向坐标系，筛出后续值得做 driver-map / model 的优先级。
- **时间预算假设**：smoke example，不做完整 DART 拉数；本稿使用公开网页和公司/市场数据入口做源头化证据卡，下一步可由 `financial-data` / DART 做三表和 valuation pack。
- **口径说明**：财务数字以 FY2025 或最新可得 as-of 为主，货币单位为 KRW；市值为 2026-05-07 至 2026-05-14 附近快照，不能直接当实时交易输入。

## 0A. 横向比较 Preflight

| 检查项 | 结论 | 处理 |
|---|---|---|
| Mechanism / value capture | 可比但不完全同质。五家公司都受益于 K-defense export cycle，但价值链位置不同：ground systems、aircraft OEM、guided weapons、defense electronics。 | 可以做 peer-deep-dive，但必须按业务环节解释 spread。 |
| KPI 定义 | 部分可比。Revenue / OP / backlog 可横比；segment margin、funded backlog、book-to-bill、export mix 口径不完全统一。 | 矩阵只把可靠公开口径列出，未源头化的 ROIC / FCF / EV/EBITDA 暂不硬填。 |
| Driver 口径 | 可映射到 export backlog、delivery cadence、program margin、policy financing、localization / MRO。 | 下一步 handoff 给 `driver-map` 拆订单兑现和 margin waterfall。 |
| Peer group 合理性 | 合理作为 Korean defense export-cycle peer set；不合理作为纯 play 同质篮子。 | Ranking 是研究资源排序，不是组合建议。 |

## 1. 行业 Lens

当前 regime 是 **K-defense export cycle 从“订单故事”进入“利润兑现 + 本地化交付能力”验证期**。2025 年韩国防务出口回升到 USD 15.4B，DAPA/行业口径显示同比增长 60.4%，主要由 Poland Chunmoo、Romania K9/K10、中东 Cheongung-II、以及 Philippines / Vietnam 等项目拉动；同时媒体引用 DAPA 和行业数据称，Big Four defense firms 2025 合计 revenue 达 KRW 40.45T、OP 达 KRW 4.63T，均为新高。[Seoul Economic Daily / DAPA export tally](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further)

这个周期的关键不是“韩国军工都增长”，而是三件事：第一，出口订单的 pricing freedom 高于韩国国内政府项目，韩国媒体报道国内项目利润率通常只有约 2-5%，海外项目则能通过议价和规模效应改善 margin；第二，订单兑现是多年度，booked backlog 到 revenue / cash 的节奏比 headline order 更重要；第三，欧洲和中东客户开始要求 localization、financing、MRO 和 supply-chain transplant，强者不是只卖装备，而是能复制生产与服务体系。[Seoul Economic Daily / K-defense structure shift](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further)

## 2. 横向矩阵

### 2A. 核心财务和订单口径

| 公司 | 市值快照 | FY2025 revenue | FY2025 OP / margin | backlog / order signal | 横向 takeaway | Source |
|---|---:|---:|---:|---:|---|---|
| Hanwha Aerospace | KRW 67.3T，2026-05-14 | KRW 26.6078T | KRW 3.0345T / 11.4% | ground defense backlog about KRW 37.2T | 最大规模，但并表 Hanwha Ocean 后 consolidated numbers 不能直接当 pure defense。Ground defense 自身 FY2025 revenue KRW 8.1331T、OP KRW 2.0129T，才是更像防务核心的高 margin 口径。 | [AJU Press citing regulatory filing](https://www.ajupress.com/view/20260209154570192); [FnGuide market cap](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A012450) |
| Hyundai Rotem | KRW 23.2T，2026-05-14 | KRW 5.839T | KRW 1.0056T / 17.2% | year-end backlog KRW 29.7735T | 本组最清晰的“订单兑现成利润”案例；K2 tanks + rail 项目同时贡献，但也意味着 defense-only quality 仍需拆。 | [Hyundai Rotem official financial summary](https://www.hyundai-rotem.co.kr/en/invest/finance/summary/content.do); [ChosunBiz backlog report](https://biz.chosun.com/en/en-industry/2026/01/30/I5AGFTDVU5CDTJS6ND5OJ4W2UM/); [FnGuide market cap](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A064350) |
| KAI | KRW 16.8T，2026-05-14 | KRW 3.6964T | KRW 269.2B / 7.3% | backlog KRW 27.3437T | backlog 不小，但利润率尚未像 Rotem 那样完全上台阶；核心是 KF-21 mass production / FA-50 export 后续兑现。 | [AJU Press / KAI FY2025](https://www.ajupress.com/view/20260205170070150); [FnGuide market cap](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A047810) |
| LIG Defense&Aerospace | KRW 19.3T，2026-05-14 | about KRW 4.3T | about KRW 322.9B / 7.5% | 2025 source found did not give full year backlog; 2024 year-end backlog was KRW 20.1419T in prior reporting | guided weapons / missile defense 是高质量 exposure，但当前市值高于 KAI、接近 Rotem，必须验证 backlog 是否继续扩张。 | [Yonhap / LIG FY2025](https://en.yna.co.kr/view/AEN20260213007851320?section=economy-finance%2Feconomy); [Asia Business Daily / 2024 backlog](https://www.asiae.co.kr/en/article/2025021414192879779); [FnGuide market cap](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A079550) |
| Hanwha Systems | KRW 21.8T，2026-05-07 | KRW 3.6642T | KRW 123.6B / 3.4% | Q1 2026 backlog reported at KRW 12.1963T, with defense KRW 9.2457T | strategic electronics exposure is valuable, but 2025 profit quality is weakest in this peer set; market is paying for defense electronics / space / shipyard optionality before margin proof. | [ChosunBiz / FY2025](https://biz.chosun.com/en/en-industry/2026/02/06/Z7UEMMBYVRE4TPNDN5EOYHGZOA/?outputType=amp); [ChosunBiz / Q1 backlog](https://biz.chosun.com/en/en-industry/2026/04/27/LAQSSEFVGJEYZFWWKKAG4HBTQE/); [StockAnalysis market cap](https://stockanalysis.com/quote/krx/272210/market-cap/) |

**矩阵 takeaway**：市值排序和利润兑现排序不一致。Hanwha Aerospace 市值最大合理，因为它是集团级产业整合锚；但在剩余四家里，Rotem 的 2025 OP / market cap 匹配最强，LIG 和 Hanwha Systems 更像市场在提前资本化 missile / radar / defense electronics scarcity premium。

### 2B. 行业特定 KPI

| KPI | Hanwha Aerospace | Hyundai Rotem | KAI | LIG Defense&Aerospace | Hanwha Systems | 解释 |
|---|---|---|---|---|---|---|
| Backlog visibility | ground defense about KRW 37.2T | total backlog KRW 29.7735T | backlog KRW 27.3437T | 2025 source gap; prior year-end 2024 backlog KRW 20.1419T | Q1 2026 total KRW 12.1963T | backlog 是本行业最重要的 revenue runway，但各公司披露口径不同，不能直接当 fully comparable funded backlog。 |
| Export / overseas mix | 2025 defense exports exceeded 50% of defense segment revenue per Seoul Economic Daily | K2 Poland and other overseas defense orders are key driver | FA-50 / KF-21 export pipeline | Cheongung-II UAE and guided weapons exports are key driver | UAE / Saudi Cheongung-II radar, Poland K2 fire-control systems | export mix 是 margin driver；国内项目利润率通常低，海外议价空间更大。 |
| Margin quality | consolidated 11.4%; ground defense implied much higher | 17.2% group OP margin | 7.3% | about 7.5% | 3.4% | Rotem 已经兑现，Hanwha ground defense 很强但 consolidated mix 被 Ocean/Aerospace 稀释，Systems 需要等待成本正常化。 |
| Program concentration | K9 / Chunmoo / L-SAM plus shipbuilding | K2 / rail projects | KF-21 / FA-50 / helicopters | Cheongung-II / guided weapons | radar / TICN TMMR / fire control / Philly Shipyard | concentration 是 upside 和 risk 的同一来源；delivery delays or financing issues 会显著影响估值。 |

## 3. Differential Profile

### Hanwha Aerospace

**一句话定位**：规模最大、但必须拆分的集团级 defense anchor。

关键 differential：
- FY2025 consolidated revenue KRW 26.6078T、OP KRW 3.0345T，是组内绝对规模最大；但这包含 Hanwha Ocean 全年并表，不能把 consolidated growth 简单等同于 defense organic growth。[AJU Press](https://www.ajupress.com/view/20260209154570192)
- ground defense FY2025 revenue KRW 8.1331T、OP KRW 2.0129T，implied margin 约 24.8%，显著高于 consolidated margin。[AJU Press](https://www.ajupress.com/view/20260209154570192)
- ground defense order backlog about KRW 37.2T，是本组最高 backlog 口径之一，但注意它是 segment backlog，不是全集团 funded backlog。[AJU Press](https://www.ajupress.com/view/20260209154570192)

特有驱动：K9 / Chunmoo export backlog、Hanwha Ocean 并表后的 naval / shipbuilding story、aerospace unit turnround。

当前最大争议：市场到底该按 pure defense prime、shipbuilding-defense conglomerate，还是 Korean industrial champion 给 multiple。

Thesis 苗头：**多，但要等拆分**。先拆 ground defense standalone，再判断 Ocean 并表是估值加成还是口径污染。

### Hyundai Rotem

**一句话定位**：利润兑现最清楚的 K2 / rail execution play。

关键 differential：
- 官方 financial summary 显示 FY2025 sales KRW 5.839T、operating profit KRW 1.0056T，OP margin 约 17.2%，明显高于 KAI / LIG / Hanwha Systems。[Hyundai Rotem official financial summary](https://www.hyundai-rotem.co.kr/en/invest/finance/summary/content.do)
- 年末 backlog reported at KRW 29.7735T，约等于 FY2025 revenue 的 5.1x；这给多年度交付可见度，但需要拆 defense vs rail。[ChosunBiz](https://biz.chosun.com/en/en-industry/2026/01/30/I5AGFTDVU5CDTJS6ND5OJ4W2UM/)
- FnGuide 2026-05-14 market cap KRW 23.2T，低于 Hanwha Aerospace，也仅略高于 LIG / Hanwha Systems；用 2025 OP 粗看，估值/盈利匹配更好。[FnGuide](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A064350)

特有驱动：Poland K2 execution, export financing, rail project delivery, defense segment mix。

当前最大争议：高 margin 是可持续 export mix，还是订单集中释放导致的一段高峰。

Thesis 苗头：**优先多头研究**。它最适合先做 driver-map，因为盈利、订单、估值三者之间的张力最大。

### KAI

**一句话定位**：backlog 足够大，但利润兑现更靠后。

关键 differential：
- FY2025 revenue KRW 3.6964T、OP KRW 269.2B，OP margin 约 7.3%，低于 Rotem 和 Hanwha ground defense。[AJU Press](https://www.ajupress.com/view/20260205170070150)
- FY2025 orders rose 30.4% to KRW 6.3946T，year-end backlog KRW 27.3437T，说明收入 runway 不差。[AJU Press](https://www.ajupress.com/view/20260205170070150)
- 2026 company forecast revenue KRW 5.7306T、orders KRW 10.4383T，关键在 KF-21 mass production 和 FA-50 export follow-on 是否按期兑现。[AJU Press](https://www.ajupress.com/view/20260205170070150)

特有驱动：KF-21 mass production / first export、FA-50 Philippines / Malaysia / Poland support, aircraft-structure recovery。

当前最大争议：订单和战略价值很清楚，但 aircraft programs 的 working capital、learning curve、delivery risk 会压住短期 margin。

Thesis 苗头：**中长期 watchlist**。适合跟踪 program milestones，不适合作为本轮第一模型对象。

### LIG Defense&Aerospace

**一句话定位**：missile / precision-guided weapons scarcity premium。

关键 differential：
- FY2025 sales about KRW 4.3T、OP about KRW 322.9B，Yonhap 报道称 operating profit YoY +44.5%，主要受 weapons production and exports 拉动。[Yonhap](https://en.yna.co.kr/view/AEN20260213007851320?section=economy-finance%2Feconomy)
- 公司把增长归因于 Cheongung-II to UAE、guided weapons mass production、TMMR command-and-control systems 等，这和 Rotem/KAI 的平台装备逻辑不同。[Yonhap](https://en.yna.co.kr/view/AEN20260213007851320?section=economy-finance%2Feconomy)
- Market cap KRW 19.3T as of 2026-05-14，已经高于 KAI、接近 Rotem，但利润规模明显小于 Rotem。[FnGuide](https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode=A079550)

特有驱动：air-defense / missile demand, Middle East export cadence, unmanned / space / aviation expansion after name change。

当前最大争议：市场是否已经把 missile scarcity 和 future-domain expansion 充分资本化。

Thesis 苗头：**质量好但需估值核查**。下一步要补官方 2025 backlog、export mix、contract duration，再决定是否能进 model。

### Hanwha Systems

**一句话定位**：战略 electronics exposure，但盈利兑现最弱。

关键 differential：
- FY2025 revenue KRW 3.6642T、OP KRW 123.6B，revenue +30.7% 但 OP -43.7%；公司解释为 Philly Shipyard normalization costs、PPA amortization、Gumi/Jeju investments 等拖累。[ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/06/Z7UEMMBYVRE4TPNDN5EOYHGZOA/?outputType=amp)
- 2025 revenue 增长由 defense exports 支撑，包括 Cheongung-II multifunction radar to UAE/Saudi、K2 fire-control system to Poland、TICN TMMR mass production。[ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/06/Z7UEMMBYVRE4TPNDN5EOYHGZOA/?outputType=amp)
- Market cap KRW 21.8T as of 2026-05-07，显著高于 KAI、接近 Rotem，但 2025 OP margin 仅约 3.4%。[StockAnalysis](https://stockanalysis.com/quote/krx/272210/market-cap/)

特有驱动：radar / C4I / satellite / shipyard optionality, defense electronics export attach rate。

当前最大争议：市场给的是“未来 defense electronics platform”估值，但当前财务仍被非核心成本和投资周期拖累。

Thesis 苗头：**谨慎观察 / 可做 short-side diligence**。不是直接做空，而是先问：如果 Philly / PPA 正常化不够快，当前 multiple 是否缺少盈利保护。

## 4. Cross-Cut Insight

### 4A. 矛盾信号：利润兑现最强的不一定是市值最贵的

Rotem 2025 OP KRW 1.0056T、市值约 KRW 23.2T；LIG 2025 OP 约 KRW 0.32T、市值约 KRW 19.3T；Hanwha Systems 2025 OP 约 KRW 0.12T、市值约 KRW 21.8T。这个 spread 暗示市场不是单纯按当期 OP 定价，而是在给 missile / electronics / future domain optionality 溢价。问题不是“LIG/Systems 贵不贵”，而是这些 optionality 有没有足够 source-backed backlog 和 margin path。

### 4B. Export mix 是 margin driver，不只是 revenue driver

K-defense 2025 出口恢复到 USD 15.4B，报道同时指出海外交易相对国内项目有更自由定价空间，这解释了为什么 Rotem 和 Hanwha ground defense margin 能显著抬升。[Seoul Economic Daily](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further) 下一步模型不应只输入 backlog，要把 backlog 按 domestic/export、platform/munition/electronics、finished-product/local-production/MRO 切开。

### 4C. “Backlog 大”不是同一种质量

Hanwha Aerospace 的 KRW 37.2T 是 ground defense backlog；Rotem 的 KRW 29.8T 是 total backlog，含 rail；KAI 的 KRW 27.3T 是 aircraft/program backlog；Hanwha Systems Q1 2026 backlog 包括 defense、ICT、Philly Shipyard。把这些直接相加或按 backlog/revenue 排序会误导，必须先定义 funded backlog、remaining performance obligations、delivery schedule 和 margin band。

## 5. 研究排序和资源分配

| 优先级 | 公司 | 建议动作 | 为什么现在做 |
|---:|---|---|---|
| 1 | Hyundai Rotem | `driver-map` + quick DCF / scenario model | 订单、利润、估值张力最大，最容易形成可检验 variant view。 |
| 2 | Hanwha Aerospace | segment-level driver-map | 规模最大但口径最复杂；拆出 ground defense 后才能判断是否比 Rotem 更有吸引力。 |
| 3 | LIG Defense&Aerospace | backlog / missile margin diligence | 高质量但溢价明显；需要验证 2025/2026 订单能否支持 premium multiple。 |
| 4 | KAI | milestone tracker | backlog 大但 margin inflection 更靠 program delivery；适合等 KF-21 / FA-50 milestone。 |
| 5 | Hanwha Systems | cost normalization watch | electronics strategic value 高，但当前 OP 和 valuation mismatch 最大，先看 Philly/PPA 是否消退。 |

## 6. Cross-Company Questions

- K2 / K9 / Chunmoo / Cheongung-II / FA-50 的 export backlog 中，多少是 firm order、多少依赖 government financing 或 follow-on options？
- 海外订单 margin 是否已经在 FY2025 peak，还是随着 localization / MRO 会进一步改善？
- Rotem 的 rail backlog 与 defense backlog 是否共享产能、working capital 或 execution risk？
- Hanwha Aerospace 并表 Hanwha Ocean 后，投资者应按 defense prime、shipbuilding-defense conglomerate，还是 Korean industrial champion 估值？
- LIG 和 Hanwha Systems 的 missile/radar/electronics exposure 是否有足够 repeatable export attach rate，还是一次性项目驱动？

## 7. Evidence Protocol Notes

### Evidence cards used

| Claim | Source | Confidence | Caveat | Suggested use |
|---|---|---|---|---|
| Korea defense exports reached USD 15.4B in 2025; Big Four revenue / OP reached record levels. | [Seoul Economic Daily / DAPA](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further) | source-found | AI-translated media page; figures attributed to DAPA / industry sources. | Industry lens |
| Hanwha Aerospace FY2025 revenue / OP and ground defense backlog. | [AJU Press citing regulatory filing](https://www.ajupress.com/view/20260209154570192) | source-found | Media translation of regulatory filing; use DART for model-ready pack. | Matrix / differential |
| Hyundai Rotem FY2025 revenue / OP. | [Hyundai Rotem official financial summary](https://www.hyundai-rotem.co.kr/en/invest/finance/summary/content.do) | source-found | Official company page, unit is KRW 100mn. | Matrix / differential |
| KAI FY2025 revenue / OP / backlog. | [AJU Press / KAI FY2025](https://www.ajupress.com/view/20260205170070150) | source-found | Media report; use company IR / DART for model-ready. | Matrix / differential |
| LIG FY2025 revenue / OP. | [Yonhap](https://en.yna.co.kr/view/AEN20260213007851320?section=economy-finance%2Feconomy) | source-found | FY2025 backlog not found in this quick pass. | Matrix / differential |
| Hanwha Systems FY2025 revenue / OP and cost caveat. | [ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/06/Z7UEMMBYVRE4TPNDN5EOYHGZOA/?outputType=amp) | source-found | AI-translated media page; exact segment details need company IR. | Matrix / differential |

### Main-agent spot checks

- Spot-check 1: Hanwha Aerospace revenue / OP / backlog claim matched the AJU page lines for FY2025 consolidated revenue, OP, ground defense revenue/OP and backlog.
- Spot-check 2: Hyundai Rotem official page directly lists FY2025 sales KRW 58,390 hundred million and OP KRW 10,056 hundred million.
- Spot-check 3: Seoul Economic Daily page ties the industry regime to DAPA export tally, Big Four revenue / OP, and export-margin explanation.

### Known gaps before investment use

- Not model-ready: ROIC, FCF yield, EV/EBITDA, net debt, and segment-level backlog were not fully source-normalized.
- Not fully comparable: backlog definitions differ across companies.
- Required next skill: `driver-map` for Rotem and Hanwha Aerospace before `dcf-model` or `comps-analysis`.
