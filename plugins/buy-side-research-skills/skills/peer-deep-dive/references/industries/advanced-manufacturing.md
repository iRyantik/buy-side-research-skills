# Advanced Manufacturing - 行业 KPI 模板

## 行业边界

本模板覆盖：
- **Industrial Automation**：Rockwell Automation、Honeywell（PMT segment）、Emerson、Schneider Electric、Yokogawa
- **Robotics (非人形)**：FANUC、ABB Robotics、Kawasaki Heavy、Yaskawa、KUKA（part of Midea）、Universal Robots（Teradyne）；中国：埃斯顿、汇川（part）、新时达
- **Capital Equipment（除半导体）**：日本机床（DMG MORI、Yamazaki Mazak、Okuma）、德国（GROB、Trumpf private）、Haas Automation
- **Industrial 3D Printing / Additive**：3D Systems、Stratasys、Velo3D、Desktop Metal（合并）、Markforged
- **Industrial Sensors / Test & Measurement**：Keyence、Cognex、Hexagon、Fortive、Teledyne、Trimble、Garmin (Marine、Aviation)
- **Material Handling / Smart Factory**：Daifuku、Murata Machinery、Honeywell Intelligrated、Symbotic
- **Electronics Manufacturing Services (EMS)**：Hon Hai (Foxconn)、Jabil、Flex Ltd、Celestica、Sanmina

不在本模板：
- **半导体设备**（ASML、Applied Materials、LAM、KLA、TEL）→ 应有独立模板（待用户需要时建）
- **人形机器人**（Tesla Optimus、Figure、Apptronik）→ 见 humanoid-robotics.md
- **传统制造业**（钢铁、有色、建材）→ 不在 advanced 范畴
- **Auto OEM / Tier 1**（Toyota、福特、Bosch）→ Auto 框架

## 当前 regime 的典型变量（市场在 trade 什么）

**当前主流叙事（2024-2026）**：
- **Reshoring / Friend-shoring**：US CHIPS Act / IRA / EU Net-Zero Industry Act 推动制造业回归 → 设备订单 surge
- **AI-Powered Factory**：generative AI 集成到 machine vision、predictive maintenance、process control
- **机器人 deflation**：协作机器人 (Cobot) 价格下降，扩展中小制造商市场
- **中国 demand 周期**：中国制造业 capex 是 industrial automation 全球关键变量
- **能源转换 capex**：EV battery factory、solar gigafactory、新能源车产线
- **库存调整周期**：2023-2024 行业普遍经历去库存（特别是 distributors / 渠道）
- **服务化转型**：硬件 → 硬件 + 软件 + 服务 + 订阅（Rockwell Plex、Emerson Movicon）

## 核心 KPI

### 通用 Advanced Manufacturing KPI

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Order Intake (Bookings) | 单季度新订单 | YoY trend + Q-on-Q 是关键周期信号 |
| Book-to-Bill Ratio | 订单 / 收入 | > 1.0 增长，持续 < 0.95 警戒 |
| Backlog | 在手订单 | Backlog / 季度收入 = visibility months |
| Backlog Quality | Margin profile of backlog | 不同 vintage / 区域 / 产品 margin 不同 |
| 短周期 vs 长周期产品比例 | Short-cycle (sensors、components) vs Long-cycle (automation systems) | 短周期反映当前 demand，长周期 lag 12-18 月 |
| Distribution / Channel inventory | 渠道库存水平 | 关键周期信号——destock 周期影响 6-12 月 |
| 自有工厂 Utilization | 自身产能利用率 | 反映 demand + 工厂投资合理性 |

### 区域 / 客户结构

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| 区域分布（NA / Europe / China / Asia ex-China） | 收入地理分布 | 中国 typical 15-30%，对中国制造 cycle 敏感 |
| China 收入 + YoY | 中国市场表现 | 关键波动来源；中国 typical 比全球 cycle leading |
| Process vs Discrete Industries 占比 | 工业类型 | Process（化工、O&G、电力）更稳；Discrete（auto、electronics）更 cyclical |
| End-Market Mix | 终端市场（auto / electronics / oil&gas / food&bev / pharma 等） | 决定特定 macro 暴露 |
| Top 5 / 10 客户集中度 | 客户集中度 | 分销商主导 vs 直销决定不同 dynamics |

### 服务 / 软件转型（关键长期 thesis driver）

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Service / Aftermarket 收入占比 | 服务收入占比 | typical 25-40%，越高 margin 越稳 |
| Software / SaaS 收入占比 | 软件收入占比 | Rockwell Plex、PTC 模式；< 10% 早期，> 25% mature |
| Recurring Revenue 占比 | 经常性收入 | 越高 visibility 越好 |
| Connected Devices (IoT) | 联网设备数量 | Service 业务增长 leading indicator |
| Software ARR YoY | 软件 ARR 增速 | 区分 hardware 和 software business 健康度 |

### 创新 / R&D

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| R&D % of Revenue | 研发强度 | typical 5-8%，> 10% 是 tech-leaning 公司 |
| New Product Vitality | 近 3-5 年新产品收入占比 | 衡量创新活力 |
| Patent 数量 | IP 产出 | 不是高质量信号，但相对趋势可用 |

### 财务结构

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Gross Margin | 毛利率 | typical 40-55%（Keyence 极端值 50%+）；高 margin = pricing power 信号 |
| EBIT Margin | EBIT 率 | typical 15-25%；20%+ best-in-class |
| ROIC | 资本回报率 | > 20% 优秀，> 15% 健康 |
| Capex / D&A | 资本强度 | typical 0.8-1.2x（轻资产）；mfg 公司 > 1.5x 重投资 |
| FCF Conversion (FCF / Net Income) | 现金转化 | > 80% 健康，< 70% 警惕 |
| 海外现金占比 | Cash overseas | 对税收 repatriation 政策敏感 |

### 3D Printing / Additive 特有

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Printers Installed Base | 累计装机量 | 决定 future material / service 收入 |
| Material Revenue 占比 | 耗材收入占比 | razor-and-blade 模式核心 |
| 工业 vs Desktop 客户结构 | 工业客户 = 高 ASP + 服务粘性 | Desktop 是商品化战场 |
| 平均 ASP | 单台价格 | 工业级 $200K-2M；desktop < $20K |

## 行业特定实证驱动因素（股价跟着什么动）

- **PMI 数据（每月）**：Manufacturing PMI > 50 = 扩张，是行业 demand 同步指标
- **机床订单数据**：JMTBA（日本）、AMT（美国）月度订单
- **工业生产指数（IP）**：美国 Fed、欧洲、中国 NBS
- **客户 capex announcement**：大型客户（auto OEM、半导体厂、电池厂）capex
- **关税 / 贸易事件**：US-China tariff、欧洲 CBAM 等
- **CHIPS Act / IRA / EU Industrial Plan funding**：资金 disbursement 推动设备订单

## 典型估值锚点

| 子板块 | 估值方法 | 典型区间 |
|---|---|---|
| Industrial Automation 一线（Rockwell、Emerson、Schneider） | EV/EBITDA、P/E | EV/EBITDA 14-20x、P/E 20-30x |
| 服务 / 软件转型成功（Keyence、Hexagon、Fortive） | EV/EBITDA、Rule of 40 | EV/EBITDA 18-30x（软件溢价） |
| 周期性 capital equipment（机床、工业机器人） | Mid-cycle EBITDA、P/E | 周期定价，看 mid-cycle |
| EMS 服务（Jabil、Flex） | EV/EBITDA、P/E | 6-10x（低 margin 业务） |
| 3D Printing | EV/Revenue（多数亏损） | 2-5x（行业 disappointed） |
| Cobot / 工业机器人纯 play | EV/EBITDA、Forward Revenue | 受周期高度影响，看 mid-cycle |

## Cross-cut 注意事项（这个行业最容易翻车的地方）

### Backlog Mix 的隐藏信息

- 不同 vintage 的 backlog margin 差异大（早期高价签的 vs 通胀压力期签的）
- Backlog 中 "delayed shipments due to supply chain" 占比可能很大
- 横向比较 backlog 时要追问：什么时间签的？
- 公司有时通过 push-out shipments 推高 backlog 数字

### Channel / Distributor 库存

- 行业销售很多通过 distributor（Grainger、MSC、Fastenal）
- Distributor 的 channel inventory 是关键 leading indicator
- 2023 年许多 industrial 公司因 channel destock 业绩低预期
- 公司 reported revenue ≠ end-customer demand

### China Exposure 的两面性

- 中国市场 typical 占 industrial automation 公司 15-30% 收入
- 中国 capex cycle vs 全球 cycle 有 6-12 月领先
- 但中国本土玩家（汇川、埃斯顿）持续抢占外资份额
- 横向比较时不仅要看 China 收入，还要看 China 市占率 trend

### 设备订单的"前置"和"后视"

- 大型 capital equipment 订单可能从 RFQ → Quote → PO → Shipment → Revenue 持续 12-18 个月
- 当前 quarter 的 revenue 反映 12 个月前的 demand
- 当前的 order 反映 6-12 个月后的 revenue
- 横向比较时混淆这两个时点是常见错误

### 服务收入的"质量"差异

- "Service revenue" 包括 break-fix、preventive maintenance、software subscription、consulting
- 不同 service business 的 margin 和 stickiness 差异巨大
- Software-related service (e.g. Rockwell Plex) margin 60%+
- Break-fix service margin 20-30%
- 横向比较 "service margin" 时不能直接比，要看 mix

### Gross Margin 比较的陷阱

- Keyence 50%+ GM 是 outlier（直销 + 高 ASP + 软件含量高）
- 中国本土工业自动化公司 GM 通常 25-35%（vs 国际同行 40-50%）—— 差异反映商业模式 + 产品定位
- 横向比较 GM 必须 normalize 商业模式（直销 vs 分销 vs OEM）

### "Software 转型"的真实进度

- 多家工业公司声称"软件 + 服务转型"——但实际 software ARR 仍 < 5% 收入
- 区分：硬件附带的 software 收入 vs 真正 standalone SaaS
- 横向比较时要追问：standalone software ARR 是多少？

### EMS / 制造服务的 razor-thin margin

- Foxconn / Jabil / Flex EBIT margin typical 4-6%
- 单点 customer concentration 高（如 Apple 占 Foxconn 70% revenue）
- 不能直接对比 OEM-style industrial 公司

### 3D Printing 行业的"period of disillusionment"

- 2014-2015 hyped → 2018 collapse → 2020 SPAC re-hype → 2022-2024 disappointing
- 当前期权值多过 fundamental value
- 横向比较时要承认：这是 emerging market，传统 KPI 解释力有限

### Cobot / 协作机器人的市场定义模糊

- "Cobot" 包括 Universal Robots（Teradyne 持有）、AUBO、Doosan 等
- 总体市场规模数据（IFR）容易高估实际可投资 TAM
- 横向比较 Cobot 公司收入时要看终端 application（轻型组装 vs heavy industrial）

### 中国本土 vs 国际玩家估值差

- 国际 industrial automation 一线 EV/EBITDA 15-20x
- 中国本土玩家（汇川等）EV/EBITDA 20-25x（增长溢价 + 国产替代主题）
- 不能直接 cross-compare 估值倍数——increment growth 假设不同

### 周期定位判断

- Industrial 是高度 cyclical 行业
- 看 PMI、ISM、book-to-bill 等多个 leading indicator
- 历史 base rate：每 5-7 年一次主要 down-cycle
- 周期顶部（high book-to-bill + high backlog + high margin）做多 = 经典反向风险
