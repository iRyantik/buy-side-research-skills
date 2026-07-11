---
schema_version: 1
document_type: peer_deep_dive
peer_set_id: kr-defense
created_at: 2026-05-15
source_policy: "Sub-Agent Evidence Protocol: spawned evidence collectors; evidence cards only; main-agent synthesis and URL spot-check required"
runtime_note: "Actual spawn_agent run: 5 sub-agents collected company-level evidence cards; main agent wrote all ranking, cross-cut insight, and final synthesis."
sub_agents:
  - Hanwha Aerospace evidence collector
  - Hyundai Rotem evidence collector
  - KAI evidence collector
  - LIG Defense&Aerospace evidence collector
  - Hanwha Systems evidence collector
companies:
  - Hanwha Aerospace (012450.KS)
  - Hyundai Rotem (064350.KS)
  - Korea Aerospace Industries / KAI (047810.KS)
  - LIG Defense&Aerospace / LIG Nex1 (079550.KS)
  - Hanwha Systems (272210.KS)
---

# 韩国防务上市公司 Peer Deep Dive

**结论先行**：这组 Korean defense peers 的核心分化不是“谁最像军工股”，而是谁已经把出口订单转成利润、谁还只是 backlog / optionality。**Hyundai Rotem** 是本轮优先深挖对象：2025 sales KRW 5.839T、OP KRW 1.0056T，OP margin 约 17.2%，且 end-2025 backlog KRW 29.77T，但其中 rail backlog 很大，必须拆 defense vs rail。**Hanwha Aerospace** 是规模和地位最强的 anchor，但 consolidated revenue / OP 被 Hanwha Ocean 并表放大，真正高质量口径是 ground defense：2025 revenue KRW 8.1331T、OP KRW 2.0129T、backlog about KRW 37.2T。**LIG** 是 missile / guided-weapons quality exposure，但 2025 backlog source 不够完整；**KAI** 是 aircraft program inflection，适合 milestone tracker；**Hanwha Systems** 是 defense electronics / radar optionality，但官方 2025 OP 只有 KRW 119.9B，盈利兑现远弱于估值叙事。

| 公司 | 初步方向 | 一句话理由 |
|---|---|---|
| Hyundai Rotem | 优先 deep-dive | 利润兑现最清楚，backlog 足够大；下一步关键是拆 K2 defense vs rail。 |
| Hanwha Aerospace | 核心锚，先拆 segment | 集团级规模最大，但 consolidated 与 ground defense 口径差异太大。 |
| LIG Defense&Aerospace | 高质量候选，先补 backlog | Guided weapons / Cheongung-II 驱动明确，但缺 FY2025 ending backlog source。 |
| KAI | 中长期 watchlist | Backlog 和 2026 target 强，但 2025 margin 仍低，核心看 KF-21 / FA-50 兑现。 |
| Hanwha Systems | 谨慎观察 | Radar / C5I / AESA optionality 强，但 2025 OP margin 约 3.3%，利润保护最弱。 |

第一优先动作：做 **Hyundai Rotem driver-map**，把 K2 Poland、rail backlog、local assembly / support package、margin sustainability 拆开。第二优先动作：做 **Hanwha Aerospace segment driver-map**，单独建 ground defense mini-model，避免被 Ocean / aerospace consolidated 口径污染。

## 0. 任务定义

- **公司列表**：Hanwha Aerospace、Hyundai Rotem、KAI、LIG Defense&Aerospace、Hanwha Systems。
- **研究目的**：建立 Korean defense export-cycle peer map，筛出后续值得建模和拆 driver 的优先级。
- **执行方式**：实际启动 5 个 sub-agent；每个只负责一家公司的 evidence cards，不写 ranking / thesis / final conclusion。
- **主 agent 职责**：URL/claim spot-check、口径冲突处理、横向矩阵、cross-cut insight、研究排序。
- **口径说明**：财务数字以 FY2025 或最新可得 source 为主；市值来自第三方 market-data 快照，只作 peer context，不是模型输入。

## 0A. 横向比较 Preflight

| 检查项 | 结论 | 处理 |
|---|---|---|
| Mechanism / value capture | 可比，但不是同质篮子。五家公司都受益于韩国防务出口，但位置不同：ground systems、aircraft OEM、guided weapons、radar / C5I / electronics。 | 可以横比，但要按 value-chain role 解释 spread。 |
| KPI 定义 | Revenue / OP 可比；backlog 不完全可比。Rotem backlog 含 rail，Hanwha Aerospace backlog 是 ground defense，Hanwha Systems backlog 含 defense / ICT / shipyard。 | Backlog 只能作 runway signal，不能直接相加或直接算 backlog/revenue ranking。 |
| Driver 口径 | 共同 driver 是 export backlog -> delivery cadence -> margin realization；公司特有 driver 差异很大。 | 后续 `driver-map` 要按 program / segment 拆。 |
| Peer group 合理性 | 合理作为 K-defense export-cycle peer set；不合理作为 pure-play valuation comps。 | 本文排名是研究资源排序，不是投资建议。 |

## 1. 行业 Lens

当前 regime 是 **K-defense export cycle 从“接单故事”进入“交付和利润兑现”阶段**。2025 年韩国防务出口达 USD 15.4B，同比 +60.4%，报道引用 DAPA / industry source 指出 Big Four defense firms 合计 revenue KRW 40.45T、OP KRW 4.63T，均创新高；出口项目包括 Poland Chunmoo、Romania K9/K10、Middle East Cheongung-II、Philippines / Vietnam 等。[Seoul Economic Daily / DAPA export tally](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further)

这批公司的共同变量不是韩国国防预算，而是 **海外订单的价格 / margin / 交付节奏**。同一篇 Seoul Economic Daily 报道提到，国内 defense procurement 项目利润率通常约 2-5%，海外项目定价自由度更高；这解释了为什么 Rotem、Hanwha ground defense、LIG 这种出口订单拉动的业务，margin signal 比 headline revenue 更重要。[Seoul Economic Daily / export margin context](https://en.sedaily.com/politics/2026/03/24/koreas-defense-exports-hit-154b-in-2025-set-to-grow-further)

## 2. 横向矩阵

### 2A. 财务 / backlog / 市值

| 公司 | 市值快照 | FY2025 revenue | FY2025 OP / margin | Backlog / order signal | 横向 takeaway | Source |
|---|---:|---:|---:|---:|---|---|
| Hanwha Aerospace | KRW 67.76T，2026-05-07 | KRW 26.6078T | KRW 3.0345T / 11.4% | Ground defense backlog about KRW 37.2T | 最大 anchor，但 consolidated 受 Hanwha Ocean 并表影响。Ground defense revenue KRW 8.1331T、OP KRW 2.0129T，才是高质量 defense 口径。 | [AJU Press](https://m.ajupress.com/amp/20260209154570192); [StockAnalysis](https://stockanalysis.com/quote/krx/012450/statistics/) |
| Hyundai Rotem | KRW 23.19T，2026-05-14 | KRW 5.8390T | KRW 1.0056T / 17.2% | End-2025 backlog KRW 29.77T | 利润兑现最清楚；但 backlog mix 有 rail，不能把 total backlog 当 pure defense。 | [Hyundai Rotem official financial summary](https://www.hyundai-rotem.co.kr/en/invest/finance/summary/content.do); [Yonhap](https://en.yna.co.kr/view/AEN20260130006151320); [StockAnalysis](https://stockanalysis.com/quote/krx/064350/market-cap/) |
| KAI | KRW 15.94T / 16.75T source range | KRW 3.6964T | KRW 269.2B / 7.3% | End-2025 backlog KRW 27.3437T; 2026 target sales KRW 5.7306T | Backlog 和 program ramp 明确，但 2025 margin 还没兑现到 Rotem / Hanwha ground defense 水平。 | [KAI official financial report](https://m.koreaaero.com/KO/Ir/FinancialReport.aspx); [ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/05/G75UTFDOFVHSVJPNMH7LVVCT5M/?outputType=amp); [StockAnalysis](https://stockanalysis.com/quote/krx/047810/) |
| LIG Defense&Aerospace | KRW 18.91T，2026-05-07 | about KRW 4.3T | KRW 322.9B / about 7.5% | FY2025 ending backlog not verified; 1Q25 backlog KRW 22.883T | Missile / guided-weapons quality high, but current valuation needs backlog and margin duration proof. | [Yonhap](https://en.yna.co.kr/view/AEN20260213007851320); [Seoul Economic Daily](https://www.sedaily.com/NewsView/2GSPW58PTX); [StockAnalysis](https://stockanalysis.com/quote/krx/079550/) |
| Hanwha Systems | KRW 21.71T，2026-05-15 | KRW 3.6642T | KRW 119.9B / 3.3% | Q1 2026 backlog KRW 12.1963T | Defense electronics story attractive, but OP/mcap mismatch is biggest; media OP figure conflicts slightly with official IR. | [Hanwha Systems official financial info](https://www.hanwhasystems.com/en/investment/financial-info.do); [ChosunBiz](https://biz.chosun.com/en/en-industry/2026/04/27/LAQSSEFVGJEYZFWWKKAG4HBTQE/); [StockAnalysis](https://stockanalysis.com/quote/krx/272210/statistics/) |

**矩阵 takeaway**：Rotem 是最干净的 “already earning” setup；Hanwha Aerospace 是最强 “scale + backlog” setup；LIG / Hanwha Systems 是 “premium optionality” setup；KAI 是 “program milestone” setup。不能直接按 market cap 排研究优先级，因为市值已经把不同 future-domain optionality 资本化进去了。

### 2B. 行业特定 KPI

| KPI | Hanwha Aerospace | Hyundai Rotem | KAI | LIG Defense&Aerospace | Hanwha Systems | 主 agent 口径 |
|---|---|---|---|---|---|---|
| Backlog visibility | Ground defense about KRW 37.2T | Total KRW 29.77T; Q3 2025 defense > KRW 10T and rail about KRW 18T | KRW 27.3437T | 1Q25 KRW 22.883T; FY2025 ending source gap | Q1 2026 KRW 12.1963T | 可比性弱；必须拆 funded / segment / delivery schedule。 |
| Export driver | K9 Norway, Chunmoo Estonia / Poland localization | K2 Poland, plus rail international projects | FA-50, KF-21 first export target, Philippines upgrade/support | Cheongung-II UAE / Iraq, guided weapons | Cheongung-II MFR, K2 fire-control, AESA radar | Export mix 是 margin driver，不只是 revenue driver。 |
| Margin quality | Consolidated 11.4%; ground defense implied 24.8% | 17.2% group OP margin | 7.3% | about 7.5% FY2025; 1Q25 OPM 12.5% | 3.3% consolidated | Rotem / Hanwha ground defense 已兑现；Systems 仍是 optionality。 |
| Model caveat | Ocean consolidation | Rail vs defense split | Program ramp / learning curve | Backlog source gap | Official vs media OP conflict; ICT / shipyard cost drag | 先做 driver-map，不要直接 comps。 |

## 3. Differential Profile

### Hanwha Aerospace

**一句话定位**：规模最大、但必须拆 segment 的集团 defense anchor。

关键 differential：
- FY2025 consolidated revenue KRW 26.6078T、OP KRW 3.0345T，创纪录，但公司把增长归因于 ground defense、aerospace 和 Hanwha Ocean 全年并表，不是 pure organic defense。[AJU Press](https://m.ajupress.com/amp/20260209154570192)
- Ground defense FY2025 revenue KRW 8.1331T、OP KRW 2.0129T，implied OP margin 约 24.8%，显著强于 consolidated margin。[AJU Press](https://m.ajupress.com/amp/20260209154570192)
- Ground defense backlog about KRW 37.2T，且 2025 export signals 包括 K9 Norway、Chunmoo Estonia、Chunmoo missile production in Poland。[AJU Press](https://m.ajupress.com/amp/20260209154570192); [Hanwha Aerospace newsroom / Norway](https://www.hanwhaaerospace.com/eng/media/newsroom/view.do?seq=577); [Hanwha Aerospace newsroom / Estonia](https://m.hanwhaaerospace.com/eng/media/newsroom/view.do?seq=589)

特有驱动：K9 / Chunmoo export backlog、ground defense margin、Hanwha Ocean 并表后的 naval / shipbuilding valuation framing。

当前最大争议：应按 defense prime、integrated defense/shipbuilding group，还是 Korean industrial champion 估值。

Thesis 苗头：**多，但先拆分**。不拆 ground defense standalone，任何 DCF / comps 都会混入口径噪音。

### Hyundai Rotem

**一句话定位**：利润兑现最强，但 backlog 不是 pure defense。

关键 differential：
- 官方 financial summary 显示 FY2025 sales KRW 5.8390T、OP KRW 1.0056T，OP margin 约 17.2%。[Hyundai Rotem official financial summary](https://www.hyundai-rotem.co.kr/en/invest/finance/summary/content.do)
- End-2025 backlog KRW 29.77T，YoY +58.7%；但 Yonhap 报道同时说明 growth 来自 Defense Solutions 和 Rail Solutions，不能把全部 backlog 当 K2 defense。[Yonhap](https://en.yna.co.kr/view/AEN20260130006151320)
- Q3 2025 口径显示 defense backlog exceeded KRW 10T，rail backlog about KRW 18T；这解释了为什么 Rotem 要先拆 segment。[Yonhap Q3](https://en.yna.co.kr/view/AEN20251103005051320)
- Poland second K2 contract reported KRW 8.9814T，contract period to 2033-12-31；另有 defense-media source 指向 2026-2030 delivery phasing。[Asia Business Daily](https://view.asiae.co.kr/en/article/2025080409294912911); [Breaking Defense](https://breakingdefense.com/2025/08/with-6-7-billion-in-new-tanks-and-vehicles-its-armor-week-in-poland/)

特有驱动：K2 Poland delivery cadence、local assembly / support package economics、rail backlog margin、working capital。

当前最大争议：17% OP margin 是 export mix 可持续改善，还是订单集中交付造成的一段高峰。

Thesis 苗头：**优先多头研究**。这是最适合先用 `driver-map` 拆、再用轻 DCF / scenario model 验证的公司。

### KAI

**一句话定位**：program backlog 很大，但盈利兑现更靠后。

关键 differential：
- KAI 官方 IR 页显示 FY2025 revenue KRW 3.696379T、OP KRW 269.190B、net income KRW 187.313B。[KAI official financial report](https://m.koreaaero.com/KO/Ir/FinancialReport.aspx)
- End-2025 backlog KRW 27.3437T，2026 company target sales KRW 5.7306T、orders KRW 10.4383T，主要看 KF-21 / LAH mass production 和 FA-50 follow-on。[ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/05/G75UTFDOFVHSVJPNMH7LVVCT5M/?outputType=amp)
- KAI 2025 segment table shows T-50/KF-21 family and KUH/LAH family are large defense buckets, but margin by program is not disclosed on this page。[KAI official financial report](https://m.koreaaero.com/KO/Ir/FinancialReport.aspx)

特有驱动：KF-21 first export / mass production, FA-50PH support / upgrades, LAH mass production。

当前最大争议：market 是否已经把 2026 ramp 预先资本化，而 2025 margin 仍只有约 7.3%。

Thesis 苗头：**watchlist / milestone tracker**。不适合本轮第一建模对象，但适合跟踪 KF-21 export 与 2026 target 兑现。

### LIG Defense&Aerospace

**一句话定位**：guided-weapons scarcity exposure，质量不错但要补 backlog。

关键 differential：
- FY2025 sales about KRW 4.3T、OP KRW 322.9B，OP +44.5% YoY，company/regulatory filing 口径由 Yonhap 转引。[Yonhap](https://en.yna.co.kr/view/AEN20260213007851320)
- OP improvement attributed to exports including Cheongung-II UAE sales；mass production of guided weapons and TMMR also drove revenue。[Yonhap](https://en.yna.co.kr/view/AEN20260213007851320)
- 1Q25 backlog KRW 22.883T、new orders KRW 4.2147T，guided-weapons revenue +81.4% YoY；但 FY2025 ending backlog 在这次 quick pass 未拿到 model-ready source。[Seoul Economic Daily](https://www.sedaily.com/NewsView/2GSPW58PTX)
- Official IR site lists FY2025 annual results material, but this pass did not fully extract the PDF; next step should archive it via `financial-data` / DART / ingest。[LIG Defense&Aerospace IR](https://www.ligdefenseaerospace.com/ir/irResourceView.do?bbs_no=7335)

特有驱动：Cheongung-II export recognition、guided weapons mix、TMMR / C2 systems、future defense domain expansion。

当前最大争议：missile quality premium 是否已经反映进 valuation，还是 backlog/margin duration 仍被低估。

Thesis 苗头：**高质量但需补证据**。先补 FY2025 backlog、contract period、guided weapons margin，再决定是否进入 DCF / comps。

### Hanwha Systems

**一句话定位**：defense electronics optionality 强，但利润兑现最弱。

关键 differential：
- 官方 financial page 显示 FY2025 consolidated sales KRW 3.6642T、OP KRW 119.9B、net income KRW 209.1B。[Hanwha Systems official financial info](https://www.hanwhasystems.com/en/investment/financial-info.do)
- Media / preliminary reports cite FY2025 OP KRW 123.6B，和 official IR 的 KRW 119.9B 有小冲突；本稿采用官方 IR 数字，并把 media number 标为 conflict。[Yonhap](https://en.yna.co.kr/view/AEN20260206007100320); [Hanwha Systems official financial info](https://www.hanwhasystems.com/en/investment/financial-info.do)
- FY2025 revenue growth came from Cheongung-II MFR exports to UAE/Saudi, K2 fire-control supply for Poland, and TICN TMMR mass production；profit was pressured by Philly Shipyard normalization costs, PPA amortization, Gumi site and Jeju Space Center investments。[ChosunBiz](https://biz.chosun.com/en/en-industry/2026/02/06/Z7UEMMBYVRE4TPNDN5EOYHGZOA/?outputType=amp)
- Q1 2026 backlog KRW 12.1963T; defense segment Q1 revenue KRW 471.2B and OP KRW 69B in media report, but exact segment terminology needs IR PDF verification。[ChosunBiz Q1](https://biz.chosun.com/en/en-industry/2026/04/27/LAQSSEFVGJEYZFWWKKAG4HBTQE/)

特有驱动：MFR radar, AESA, C5I, TICN, K2 fire control, space / shipyard optionality。

当前最大争议：market cap 约 KRW 21.71T 对应 very high multiple，但 current consolidated OP margin 只有约 3.3%；是否能靠 cost normalization 和 defense electronics backlog 填上。

Thesis 苗头：**谨慎观察 / short-side diligence candidate**。不是直接做空，但最需要验证“高战略价值”何时变成“高利润”。

## 4. Cross-Cut Insight

### 4A. 当期利润 vs optionality 的错位最明显

Rotem 的 2025 OP 约 KRW 1.006T、市值约 KRW 23.19T；Hanwha Systems 2025 official OP 约 KRW 0.120T、市值约 KRW 21.71T；LIG 2025 OP 约 KRW 0.323T、市值约 KRW 18.91T。这说明 market 不是按当期 OP 排序，而是在给 defense electronics / missile / future domain optionality 溢价。机会和风险都在这里：如果 optionality 能转 backlog / margin，LIG / Systems 合理；如果不能，Rotem 的当前盈利保护更强。

### 4B. Backlog 大不等于同一种质量

Hanwha Aerospace 的 KRW 37.2T 是 ground defense backlog；Rotem 的 KRW 29.77T 是 total backlog，且 Q3 2025 rail backlog about KRW 18T；KAI 的 KRW 27.34T 是 aircraft/program backlog；LIG 的 1Q25 backlog KRW 22.883T 是 missile / systems-heavy；Hanwha Systems Q1 2026 backlog KRW 12.1963T 包含 defense / ICT / shipyard. 直接按 backlog/revenue 排名会误导，正确做法是先拆 **firmness、delivery schedule、margin band、localization economics**。

### 4C. 出口订单正在改变 margin，但每家公司兑现路径不同

Hanwha ground defense 和 Rotem 已经在 2025 OP 里看到明显兑现；LIG 看到 guided weapons / Cheongung-II 的收入和 OP acceleration；KAI 更多是 2026 target / program milestone；Hanwha Systems 看到 revenue growth 和 Q1 defense momentum，但 consolidated OP 仍被 Philly / PPA / capex-like investment drag down。换句话说，这个板块已经不是“谁有出口订单”的问题，而是“谁的出口订单最先、最干净地转成 OP / FCF”。

## 5. 研究排序和资源分配

| 优先级 | 公司 | 建议动作 | 为什么现在做 |
|---:|---|---|---|
| 1 | Hyundai Rotem | `driver-map` + defense/rail split model | 2025 OP 已兑现，backlog 大，但 defense vs rail 口径决定估值质量。 |
| 2 | Hanwha Aerospace | ground defense standalone model | 规模最大、backlog 最大，但 consolidated 口径被 Ocean 并表污染。 |
| 3 | LIG Defense&Aerospace | backlog / missile margin diligence | 高质量 missile exposure，但 FY2025 ending backlog 和 margin duration 需要补。 |
| 4 | KAI | KF-21 / FA-50 milestone tracker | 2026 target 很强，但 2025 margin 未完全兑现。 |
| 5 | Hanwha Systems | cost normalization + valuation stress test | Strategic electronics 强，但 OP / market cap mismatch 最大。 |

## 6. Cross-Company Questions

- Rotem 的 KRW 29.77T backlog 中，year-end defense / rail / plant 分别是多少？K2 Poland second implementation contract 如何分年确认？
- Hanwha Aerospace ground defense KRW 37.2T backlog 的 funded / option / export / domestic 结构是什么？
- LIG FY2025 ending backlog 是多少？Cheongung-II UAE / Iraq / domestic contracts 的 revenue recognition curve 如何？
- KAI 的 2026 sales target KRW 5.7306T 中，KF-21、LAH、FA-50 / support 分别贡献多少？
- Hanwha Systems 的 Philly / PPA / site investment cost drag 是否会在 2026 消退？Defense electronics margin 是否足以覆盖非防务拖累？

## 7. Evidence Protocol Notes

### Actual sub-agent run

| Worker scope | Returned evidence type | Used in final artifact? | Main-agent treatment |
|---|---|---|---|
| Hanwha Aerospace | FY2025 actuals, ground defense revenue/OP/backlog, K9 / Chunmoo order evidence, market cap | Yes | Used AJU / company newsroom / StockAnalysis; flagged IR/DART archive gap. |
| Hyundai Rotem | Official financial summary, Yonhap backlog, K2 Poland evidence, market cap | Yes | Spot-checked official financial table; kept rail-vs-defense caveat. |
| KAI | Official financial page, backlog / 2026 target, KF-21 / FA-50 sources, market cap | Yes | Spot-checked official KAI financial table; used media for backlog/target. |
| LIG Defense&Aerospace | FY2025 Yonhap actuals, 1Q25 backlog, guided-weapons / Cheongung-II evidence | Yes, with caveat | Used FY2025 actuals and 1Q25 backlog; flagged FY2025 ending backlog source gap. |
| Hanwha Systems | Official financial page, OP source conflict, Q1 backlog, export electronics evidence | Yes | Used official OP KRW 119.9B and flagged media KRW 123.6B conflict. |

### Main-agent spot checks

- **Hyundai Rotem official financial table**: page lists 2025 Sales 58,390 and Operating profit 10,056 in KRW 100mn, matching KRW 5.8390T and KRW 1.0056T.
- **KAI official financial table**: page lists 2025 revenue KRW 3,696,379mn and OP KRW 269,190mn.
- **Hanwha Systems official financial page**: page lists 2025 sales 36,642 and OP 1,199 in KRW 100mn, so official OP is KRW 119.9B.
- **Hanwha Aerospace AJU page**: page states FY2025 revenue KRW 26.6078T, OP KRW 3.0345T, ground defense revenue KRW 8.1331T, OP KRW 2.0129T, backlog about KRW 37.2T.
- **LIG Yonhap page**: page states FY2025 OP KRW 322.9B and sales KRW 4.3T, with OP improvement attributed to exports including Cheongung-II.

### Source conflicts and gaps

- **Hanwha Systems OP conflict**: official IR says KRW 119.9B; Yonhap / media preliminary says KRW 123.6B. Final artifact uses official IR and flags conflict.
- **LIG backlog gap**: 1Q25 backlog source found, FY2025 ending backlog not fully verified in this run.
- **Market cap sources**: StockAnalysis snapshots have different as-of dates and are not model-ready. Use KRX / Bloomberg / FactSet / FnGuide for investment deck.
- **Not model-ready yet**: ROIC, FCF yield, EV/EBITDA, net debt, and segment-level margins are intentionally omitted until `financial-data` / DART pack is created.
