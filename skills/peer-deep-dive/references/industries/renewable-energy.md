# Renewable Energy - 行业 KPI 模板

## 行业边界

本模板覆盖：
- **Solar Manufacturers**：组件、电池、硅片（First Solar、JinkoSolar、Canadian Solar、隆基、晶科、晶澳、天合）
- **Solar Inverters / BOS**：Enphase、SolarEdge、SMA、Sungrow、阳光电源、固德威
- **Solar Trackers**：Array、NEXTracker
- **Wind Turbine Manufacturers**：Vestas、GE Vernova（wind segment）、Siemens Gamesa（part of Siemens Energy）、Goldwind、远景、明阳
- **Battery Storage System Integrators**：Fluence、Tesla（energy storage segment）、Stem
- **IPP / Renewable Developers**：NextEra Energy、Brookfield Renewable、AES、Iberdrola、Enel Green Power、Constellation（含核+再生）、Avangrid
- **Green Hydrogen**：Plug Power、Bloom Energy、Linde（H2 segment）、Air Liquide
- **Geothermal**：Ormat Technologies

不在本模板：
- 电力 utility（含火电主导的传统 utility）→ utility 框架不同
- EV 整车 → Auto 板块
- EV 充电桩 → 自行扩展或参考 Industrial 框架
- Biofuels (corn ethanol、palm oil) → 接近农业，不太适用本框架

## 当前 regime 的典型变量（市场在 trade 什么）

**当前主流叙事**：
- 政策依赖：IRA tax credits（PTC、ITC、AMPC）、Inflation Reduction Act（45X manufacturing credit）实际落地速度
- Trump 2.0 政策风险：IRA 是否会被 partial repeal、tariff（中国组件）、permitting reform 是否推进
- LCOE 竞争力：Solar/wind LCOE vs natural gas baseload（gas 价格走低削弱 economic case）
- AI / Datacenter 电力 demand：AI 数据中心建设触发 power 短缺，对 renewable + storage 利好
- 利率：高利率对资本密集 IPP 项目融资压力大
- 中国产能过剩：solar 组件价格暴跌 → 安装商受益，制造商受损

## 核心 KPI（按子板块）

### Solar Manufacturers (Module / Cell / Wafer)

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Module ASP (US$/W) | 组件平均售价 | 过去 2 年从 $0.20 跌到 $0.10——价格通缩是 dominate driver |
| Cell efficiency (%) | 转换效率 | TOPCon 主流 23-25%，HJT/BC 26%+；落后 1-2% 价格折价 |
| Shipments (GW) | 出货量 | YoY 增长 + market share |
| Cost / W | 单瓦成本 | 中国 typical < $0.10，美国 $0.20+（不含 IRA credits） |
| Inventory days | 库存天数 | > 90 days = 库存过剩警告 |
| US 制造份额 + IRA AMPC 收入 | 美国本土制造 | AMPC = $0.07 / W cell + $0.04/W module 是中国制造商无法获得的关键溢价 |
| Capacity utilization | 产能利用率 | < 70% 警惕 |
| Net Debt / EBITDA | 杠杆 | 高 capex 行业，> 3x 警戒 |

### Solar Inverters / BOS

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Inverter shipments (MW) | 出货量 | 关键周期信号 |
| 库存周转 / Channel inventory | 渠道库存 | Enphase / SolarEdge 在 2023 都因 channel inventory 暴跌 |
| 美国 vs 海外 收入占比 | 区域结构 | 美国市场 IRA / NEM 3.0 / 利率敏感度高 |
| Residential vs Commercial vs Utility 占比 | 终端市场 | Residential 受家庭利率敏感；Utility 大项目稳定 |
| Service / 软件附加收入 | Recurring | Enphase 模式，未来 margin 锚点 |

### Wind Turbine Manufacturers

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Order Intake (MW) | 新签订单 | 年度 / 季度趋势 |
| Order book / Backlog | 在手订单 | 多年项目周期 |
| ASP (€ or $ /MW) | 单 MW 售价 | 海上 typical 比陆上高 60-80% |
| 海上 vs 陆上 mix | 产品结构 | 海上 margin 历史上有问题（Siemens Gamesa、Vestas warranty 损失） |
| Service revenue 占比 | After-market | 长期合同、稳定 margin、是估值溢价来源 |
| Warranty provisions / charge 历史 | 质量问题成本 | Wind manufacturers 历史上巨亏的常见来源 |
| EBIT margin (Turbine + Service) | 利润率 | Turbine business 长期 margin 压力，Service 是 stable |

### Battery Storage Integrators

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Deployments (MWh) | 部署量 | YoY 高速增长，但 Q-on-Q lumpy |
| Backlog (MWh) | 储备项目 | 决定未来 6-18 个月收入 |
| ASP ($/kWh) | 单位价格 | 受锂电池价格驱动，与电池厂 trend 一致 |
| Gross margin trend | 毛利率 | 行业普遍亏损，盈利路径未明 |
| 软件 / Service 占比 | 经常性收入 | 区分纯硬件玩家和 software-enabled 玩家 |

### IPP / Renewable Developers

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Operating Capacity (MW / GW) | 运营容量 | 当前发电能力 |
| Development Pipeline (MW) | 开发管线 | 按阶段（early、construction、COD-ready）分层 |
| PPA pricing (avg $/MWh) | 售电合同价格 | 关键收入决定 |
| PPA 平均剩余期限 | Contract duration | 长合同提供 visibility |
| Capacity Factor | 实际发电 / 理论发电 | Solar typical 20-25%，Wind typical 30-50% |
| AFFO (Adjusted Funds From Operations) | 调整后运营现金流 | 类似 REIT 的核心指标 |
| Net Debt / EBITDA | 杠杆 | IPP typical 5-7x（高 leverage 行业） |
| 利率敏感度 | 利率变动对项目 IRR 的冲击 | 利率每 +100bps 项目 IRR 损失 ~1-2% |

### Green Hydrogen / Fuel Cell

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Electrolyzer deployments (MW) | 电解槽部署 | 早期阶段，绝对值还小 |
| Cost per kg H2 | 单位生产成本 | 当前 $4-8/kg，需降到 < $2/kg 才有大规模商业化 |
| Government grant / loan dependence | 政府资助依赖度 | 极高，DOE 87 个 Hub funding 是关键 |
| Cash burn rate / Runway | 现金消耗 | 早期阶段必看 |
| Customer pipeline 真实订单 vs LOI/MOU | 真实订单质量 | 行业里 LOI 多、real order 少，区分关键 |

## 行业特定实证驱动因素（股价跟着什么动）

**Solar / Wind / Storage 制造**：
- 月度 SEIA / GWEC 安装数据
- 中国 solar 出口数据（PV InfoLink、BNEF 周报）
- 美国 import 数据 + tariff 决定
- IRA guidance（IRS final rules on AMPC、prevailing wage 等）

**IPP / Developers**：
- 利率（10Y Treasury、Fed 决议）
- 关键 IPP 政策（State RPS、PJM capacity auction、ERCOT）
- AI / datacenter 重大公告（推动电力 demand）

**Green H2**：
- DOE Hub funding 公告
- IRS 45V Final Rules（关键 tax credit 规则）
- Major HC offtake 协议

## 典型估值锚点

| 子板块 | 估值方法 | 注意事项 |
|---|---|---|
| Solar / Wind 制造 | EV/EBITDA、P/E（cyclical） | 周期性强，看 mid-cycle |
| Inverters | EV/EBITDA、Forward Revenue multiple | 软件溢价 |
| Battery Storage | EV/Sales（多数还在亏损） | 早期，看市场份额 + 路径 to profitability |
| IPP / Developers | EV/EBITDA、Distribution Yield、AFFO yield、SOTP（按项目阶段） | 类 REIT 估值 |
| Green H2 | EV/Sales、cash position | 早期，主要看 funded runway + 政策 catalyst |

## Cross-cut 注意事项（这个行业最容易翻车的地方）

### IRA 政策依赖度判断

- **Manufacturers**：AMPC（45X production credit）是关键收入项，但中国制造商不享有
- **Developers**：PTC vs ITC 选择影响 NPV，依赖项目类型
- **横向比较时**：必须区分 "如果 IRA 不变 vs IRA partial repeal vs IRA full repeal" 三种 scenario
- 中国制造商 vs 美国制造商不可直接比较 margin（IRA AMPC 占大头）

### LCOE 比较的口径差异

- LCOE 数字依赖 assumption（capex、capacity factor、discount rate、project life）
- BNEF / Lazard / Wood Mackenzie 三家给的数字可能差 30%+
- 横向比较时必须用同一来源，不要 mix-and-match

### Solar 价格通缩对 thesis 的影响

- **Module manufacturers**：价格通缩 → margin 压缩 → 多数公司亏损
- **Downstream installers / IPPs**：价格通缩 → 项目 IRR 上升 → 利好
- 同一个 trend 对不同子板块影响相反，横向 cross-cut 时要明确

### 中国 vs 西方 玩家

- 中国制造商通常 cost lower，但被 IRA + tariff 排除在美国市场
- 估值倍数上中国制造商 typical 比美国低 30-50%（折价反映政策风险）
- 不能用同样的 multiple framework 比较

### Wind 业务的 warranty 风险

- Wind turbines 历史上有大量 warranty charge（Vestas、Siemens Gamesa）
- Reported Service margin 看起来好，但要看是否包含 warranty provisions 调整
- 横向比较 Wind segment EBIT 时要小心 warranty noise

### IPP 利率敏感度

- IPP 公司 typical net debt / EBITDA 5-7x，利率上升直接打击 IRR
- Brookfield Renewable / NextEra 等大型 IPP 在 2022-2023 利率周期中遭重创
- "Renewable energy growth thesis" 在高利率环境下需要重大 caveat

### Hydrogen 真实需求 vs 政策预期

- 大部分 H2 demand 来自工业脱碳（refining、ammonia、steel）
- 商业化 timeline 受 carbon pricing 政策驱动，10+ 年 visibility 极有限
- 区分 "IRA-funded 项目" 和 "未来真实 demand" 是关键

### 季节性和 lumpy 收入

- Solar / Wind 制造商 Q4 typically 是出货高峰（年底税收激励）
- IPP 季度收入受天气 / 风资源 / 检修影响波动大
- Battery storage deployments 单个项目大，季度可能 30%+ 波动
- 不要直接 Q1 vs Q1 比较 YoY，要看年化 / TTM
