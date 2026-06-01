# 固晶设备竞争格局 — Mechanism Insight

> **artifact**: `mechanism-insight` | **qualifier**: `die-bonder-competitive-landscape` | **as-of**: 2026-06-01
> **related**: [[2026-06-01-industry-landscape]] | [[2026-06-01-teach-in-optical-module]] | [[2026-06-01-mechanism-insight-die-bonding-equipment]]

---

## 结论先行

固晶设备（Die Bonder）是光模块封装三道核心工序中**精度壁垒最深、代际升级最确定受益、但也是竞争最容易被误判**的一段。第一个误判是"猎奇全球 #1"——按台数是，但按金额不是，1.6T 以上根本进不来。第二个误判是"Besi 是龙头"——在通用半导体固晶是（~39%），但在光模块专用固晶只是 Top 3。**真正在光模块固晶高端段吃肉的就三家：MRSI（精度天花板）、Besi（规模+hybrid bonding）、ASMPT（封装生态）。猎奇吃量不赚钱。**

---

## Insight in one sentence

固晶设备的竞争不是"谁的机器多"，而是**每代光模块速率升级都在把精度门槛往上抬——800G 能用 ±5μm，1.6T 必须 ±3μm，3.2T/CPO 需要 ±1μm。每一次代际升级筛掉一批低端玩家，剩下的三家精度天花板越抬越高。**

---

## Terms that matter

| Term | Plain meaning | Why it matters |
|---|---|---|
| 固晶精度 | 把芯片贴到基板上时允许的最大位置偏差 | ±5μm → ±3μm → ±1μm 的跳变是竞争格局的根本驱动力 |
| 共晶焊 (Eutectic) | 金锡合金 280°C 熔化焊死芯片 | 高速光模块必须共晶，共晶机 ASP 是环氧机的 2-3 倍 |
| 台数份额 vs 金额份额 | 按出货台数 vs 按收入计算的市场份额 | 猎奇 21% 台数但 ASP 低→金额份额远低于台数 |
| Sync eutectic | 多芯片同时拾取、一次回流完成所有共晶 | MRSI-LEAP 的核心壁垒——解决 1.6T 4-PD 共晶痛点 |
| Hybrid bonding | 晶圆级铜柱对铜柱直接键合，±100nm 精度 | Besi 的 CPO 赛道专长——不是传统 die bonding |

---

## How it works：代际升级如何重塑竞争

```
800G  Pluggable → 精度 ±5μm   → 猎奇/博众/新益昌都能做 → 卷价格
1.6T  Pluggable → 精度 ±3μm   → 猎奇被筛掉            → 剩 5-6 家
3.2T  Pluggable → 精度 ±1μm   → 只剩 MRSI/Besi/ASMPT → 3 家
CPO              → 路线之争    → Hybrid bond（Besi）vs Die bond+Coupling（ficonTEC/MRSI）| 不是一家独大，是两条路线在竞争
```

每一次代际升级，精度门槛上抬一档，玩家减少一半。这不是市场在增长——是市场在**浓缩**。

---

## 逐家深挖

### MRSI（Mycronic，MYCR SS）

| 维度 | 数据 | Ev |
|---|---|---|
| **市场份额** | 光模块固晶 Top 5，台数 ~10-15% | [猎奇招股书](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) 弗若斯特沙利文 |
| **精度演进** | **2020 年 S-HVM 已达 ±0.5μm**（硅光子/CPO 专用，低速）；**2025 年 LEAP ±1μm @ 3σ 量产高速**（>1000 UPH）。精度 2020 就有了，LEAP 的突破是精度+速度兼得 | [MRSI S-HVM 2020](https://www.mycronic.com/product-areas/die-bonding/news--events/press-releases/mrsi-launches-submicron-die-bonding-solution-for-silicon-photonics-co-packaging-and-wafer-level-packaging/), [LEAP 2025](https://www.mycronic.com/fr/product-areas/die-bonding/news--events/news/mrsi-at-cioe-2025-showcasing-the-mrsi-leap-die-bonder/) |
| **核心技术壁垒** | 4-PD 同步共晶（一次回流贴 4 颗），多芯片拾取头+独立力控。**精度不是新能力——高速量产精度才是** | [C-FOL 2026-04](https://c-fol.net/news/238_202604/20260403113532.html) |
| **客户** | "头部光模块企业批量订单"（未具名） | 同上 |
| **出货量** | Mycronic 不单独披露 MRSI 出货，GT 部门 Q1 2026 订单 Sek 915M（+260% YoY，含 ATG PCB 测试） | [Mycronic Q1 2026](https://www.tipranks.com/news/company-announcements/mycronic-lifts-2026-sales-target-after-record-first-quarter-earnings/) |
| **ASP** | $300K-800K（估算，设备商不公开报价） | `[估算，行业口径]` |
| **独特优势** | **固晶+耦合成套**（LEAP + A-L），CPO 时代固晶耦合无缝衔接的最大受益者 | — |
| **最大风险** | FPGA 缺货卡出货；Mycronic 不拆 MRSI vs ATG → 市场无法独立估值 | — |

---

### Besi（BESI NA）

| 维度 | 数据 | Ev |
|---|---|---|
| **市场份额** | 通用半导体固晶 **~39%**（绝对龙头）；光模块固晶 Top 3（~15-20% 金额） | [Besi 2023 IR](https://www.besi.com/investor-relations/press-releases/2024/details/be-semiconductor-industries-nv-announces-q2-24-results/) |
| **精度段** | ±1.5-3μm（2200 evo plus 平台）+ **±100nm**（hybrid bonding） | [Besi Investor Day 2025](https://finnhub.io/api/news?id=e64be378c8abda2d4c6575a17f12631abe05d10bf93c7a0b5f628586decba732) |
| **核心技术壁垒** | D2W hybrid bonding——TSMC COUPE 硅光引擎的核心 bonding 设备 | 同上 |
| **客户** | TSMC、Intel、Samsung（hybrid bonding）；光模块厂（2200 evo plus） | Besi Q4 2025 orders |
| **出货量** | 2023 年底 40 台 hybrid bonding 系统安装在 9 个客户处；Q2-24 获 29 台新订单 | [Besi Q2-24](https://www.besi.com/investor-relations/press-releases/2024/details/be-semiconductor-industries-nv-announces-q2-24-results/) |
| **ASP** | 标准 die bonder ~$200-400K；hybrid bonder **~€200M**（不是拼错，hybrid bonding 一台顶 1000 台标准机） | Besi IR |
| **独特优势** | **CPO 时代唯一能做 wafer 级 hybrid bonding 的量产供应商**——这是比 die bonding 高一个维度的赛道 | — |
| **最大风险** | Hybrid bonding 出货量极低（几十台级别），如果 CPO 渗透慢，高估值难以维持 | — |

---

### ASMPT（0522 HK）

| 维度 | 数据 | Ev |
|---|---|---|
| **市场份额** | 通用半导体固晶 ~12-15%；光模块固晶 Top 3 | [猎奇招股书](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) 弗若斯特沙利文 |
| **精度段** | MEGA 系列 **±1.5μm** | [ASMPT MEGA 2025-01](https://semi.asmpt.com/de/news-center/press-releases/accelerating-the-future-of-optical-interconnects-with-asmpt-mega-series/) |
| **核心技术壁垒** | CPO 封装全线（AMICRA NANO die bonder + wire bonder + AOI）——不是单台机器，是封装整线 | [ASMPT CPO](https://www.asmpt.com/en/innovation/co-packaged-optics/) |
| **客户** | 全球头部光模块厂 + OSAT（日月光、安靠） | — |
| **出货量** | 不单独披露光模块固晶出货 | — |
| **ASP** | ~$200-500K（MEGA 系列，估算） | `[估算]` |
| **独特优势** | **封装设备全线覆盖**（固晶+键合+AOI），客户一站式采购 | — |
| **最大风险** | 光模块固晶是其 SEMI 部门的小头——不是纯光模块设备股，逻辑不够纯 | — |

---

### 猎奇智能（拟 IPO，A25297）

| 维度 | 数据 | Ev |
|---|---|---|
| **市场份额** | 光模块贴片设备台数 **21%（全球 #1）** | [猎奇招股书](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) p.26 弗若斯特沙利文 |
| **精度段** | **±5-7μm**（中端） | 招股书技术章节 |
| **核心技术壁垒** | 中端性价比——价格是进口 50%，服务 24h 响应 | — |
| **客户** | **中际旭创（53% 收入）**、光迅科技 | 招股书客户集中度披露 |
| **出货量** | 产销率 100%，发出商品 >4 亿元积压 | 招股书财务章节 |
| **ASP** | ~$100-200K（中端，估算） | `[估算]` |
| **2024 收入** | CNY 5.43B，归母净利润 CNY 1.81B | 招股书 |
| **独特优势** | 中际旭创深度绑定 + IPO 募资扩产（拟募 CNY 9.13B） | — |
| **最大风险** | **MRSI + ASMPT 两起专利诉讼未决**（涉诉产品占毛利 34.6%）；**1.6T 进不来**——±5μm 精度不够；**客户高度集中** | 招股书 p.20 诉讼披露 |

---

### 博众精工（688097 CH）

| 维度 | 数据 | Ev |
|---|---|---|
| **市场份额** | 国产第二梯队，不属于全球前五 | — |
| **精度段** | 可做 ±3-5μm（共晶贴片机） | [博众精工 2025H1](https://dataclouds.cninfo.com.cn/shgonggao/2025/2025-08-27/e93b336b826d11f09cadfa163e957f7a.pdf) |
| **核心技术壁垒** | 400G/800G 批量订单，1.6T 在研 | 同上 |
| **客户** | "全球领军企业"（未具名，批量订单） | 同上 |
| **出货量** | 未单独披露光模块贴片出货 | — |
| **最大风险** | 纯 A 股逻辑——光模块贴片不是主业，自动化整线才是 | — |

---

## CPO 时代各家技术储备

以上分析是"当前静态精度段"。CPO 时代大幕已拉开——**各家对 CPO 的技术储备才是未来 3-5 年格局的决胜变量。**

| 厂商 | CPO 技术路线 | 产品/平台 | 精度 | CPO 量产进展 | 要害 |
|---|---|---|---|---|---|
| **Besi** | Wafer 级 hybrid bonding（D2W） | 8800 Hybrid G2/G3 | ±50→±25nm | ✅ **已规模量产**。15 家客户、>100 台订单。TSMC COUPE + NVIDIA Spectrum-X/Quantum-X CPO 交换机 | **CPO 封装的最激进路线**——铜柱直接键合，不走传统 die bond。如果成为主流，传统 die bonder 在 CPO 会被边缘化 |
| **ASMPT** | 传统 die bond + 贴片（走传统路线 + 超高精度） | AMICRA NANO + NOVA Pro + MEGA-P | **±0.2μm**（标称精度业内最高） | ⚠️ 2025 送样/验证中，2026 OFC 称"已赋能 CPO 制造" | 精度数据比 MRSI 还高，但 AMICRA NANO 是低速 R&D 机，量产能力待验证 |
| **ficonTEC**| die bond + 有源耦合 + 整线 | BL500 + AL300 + AA600 | 耦合 ±0.3μm | ✅ **CPO 全球最早量产验证**——博通 Bailly CPO 交换机唯一耦合供应商，已交付 14 台；英伟达核心供应商 | Broadcom Bailly 验证了"传统 die bond + 耦合"的 CPO 路线可行。**这意味着 Besi 的 hybrid bonding 不是唯一解** |
| **MRSI** | 传统 die bond + 有源耦合（固晶+耦合打包） | LEAP + A-L | 固晶 ±1μm，耦合亚微米 | ⚠️ CPO 项目中（"与业内头部合作推进，部分已获订单"），未具名。LEAP 的 ±1μm 对 CPO 光子芯片贴装够用 | **固晶+耦合成套协同**——CPO 需要贴完立即耦合，MRSI 是唯一能同时供这两台的。如果 ficonTEC 验证的路线成为主流，MRSI 是二号受益者 |
| **猎奇智能** | 目前没有公开 CPO 技术储备 | — | ±5-7μm | ❌ | **精度段差太远**——CPO 光子芯片需要 ±1μm 以下。短期内不可能跳两档 |
| **镭神技术** | 耦合为核心，CPO 多端口耦合在研 | — | ±0.5-1μm | ❌ 未公开 CPO 量产用例 | 耦合台数 #1 但精度偏中高端，CPO 超高端可能被 ficonTEC 拉开 |

### CPO 路线之争：决定设备格局的唯一变量

```
路线 A：Hybrid Bonding（Besi 独大）
  TSMC COUPE + NVIDIA Spectrum-X 走这条路
  → Besi 一家吃，传统 die bonder 被边缘化

路线 B：传统 Die Bond + Active Coupling（ficonTEC/MRSI）
  Broadcom Bailly 走这条路 ← 已验证可行！
  → ficonTEC（耦合）+ MRSI（固晶+耦合成套）受益

路线 C：Fan-out / Interposer（ASMPT 路线）
  还在验证中，介于 A 和 B 之间
```

**目前 B 路线最领先**——Broadcom Bailly 是唯一已经在 Google/Meta 数据中心试用的 CPO 交换机。所以 ficonTEC 和 MRSI 的 CPO 位置可能比市场认为的更好。

---

### 其他值得知道的

| 公司 | 上市 | 定位 | 为什么提 |
|---|---|---|---|
| **Finetech**（德国） | ❌ 未上市 | 高端共晶，实验室/R&D 为主 | 猎奇招股书列为主要境外对手，精度高但量不大 |
| **Four-Technos**（日本） | ❌ 未上市 | 高精度 die bonder | 猎奇招股书列为主要境外对手 |
| **微见智能**（中国） | ❌ 未上市 | 中端固晶 | 猎奇招股书列为主要境内对手 |
| **新益昌**（中国） | ✅ A 股 688383 CH | 中低端固晶，中际旭创客户 | ~10-15% 台数份额 |
| **智立方**（中国） | ✅ A 股 301312 CH | 固晶+自动化 | — |
| **凯格精机**（中国） | ✅ A 股 301338 CH | SMT+固晶设备 | — |

---

## Where value is captured

| 价值池 | 谁在吃 | 利润率 | 增长性 | MRSI 吃到多少 |
|---|---|---|---|---|
| **<±1μm 超高端** | MRSI、Besi 旗舰、**ficonTEC**（BL500 固晶） | **极高**（卖方定价） | CPO 驱动 | ✅ **主力战场** |
| **±3-5μm 高端** | ASMPT、Besi 标准款 | 高 | 1.6T 驱动 | ⚠️ 部分覆盖 |
| **±5-7μm 中端** | 猎奇、博众、新益昌 | 中（卷价格） | 800G 驱动 | ❌ 不做 |
| **±7μm+ 低端** | 国产分散 | 薄 | 存量 | ❌ 不做 |
| **Hybrid bonding** | Besi（独家量产） | **畸形高**（€200M/台） | CPO 爆发 | ❌ 不做 |

---

## Research read-through

| 洞察 | Driver-map 含义 | 对 MRSI 的 read-through | Confidence |
|---|---|---|---|
| 每次代际升级筛掉 40-50% 玩家 → 精度每代翻倍 = 壁垒越来越深 | MRSI 的定价权随代际递增 | GT 利润率可能从当前 ~20% 稳步上移 | **High**（精度要求来自物理定律，不可逆） |
| Besi 的 hybrid bonding 和 MRSI 的 die bonding 不是同一个赛道 | 不要把 Besi 当 MRSI 的同行可比 | CPO 时代两者可能互补而非竞争 | **High** |
| 猎奇 1.6T 进不来 → 中端增量全被海外三家吃掉 | 高端段增速 > 行业均值 | MRSI 收入增速可能跑赢设备行业大盘 | **Medium**（需验证猎奇 1.6T 产品进展） |
| FPGA 52 周交期卡所有设备商 | 订单 ≠ 收入，backlog conversion 是核心 KPI | Q2 2026 Mycronic GT 收入是关键验证点 | **High** |

---

## What not to infer

- ❌ MRSI 台数份额小 = 竞争力弱 → **不是。高端段按金额是 Top 3，且精度天花板意味着最高的 ASP 和利润率。**
- ❌ Besi 通用固晶 39% = 光模块固晶也第一 → **不是。光模块固晶是 Besi 的非核心业务，hybrid bonding 才是 CPO 时代 Besi 的王牌。**
- ❌ 猎奇台数 #1 = 对 MRSI 构成威胁 → **不是。不同精度段，不同客户群。1.6T 时代猎奇被筛掉。**
- ❌ 出货量可精确对比 → **不能。MRSI 不拆 MRSI vs ATG；ASMPT 不拆光模块 vs 通用；Besi 不拆 die bonder vs hybrid。出货量对不上。**

---

## Routing

- 拆 Mycronic/MRSI 的 revenue/margin driver → `/driver-map`
- 横向对比 Mycronic vs ASMPT vs Besi 估值 → `/peer-deep-dive`
- 形成 Mycronic long thesis → `/alpha-thesis`
- 回到行业全景 → `/industry-landscape`

---

## Resources

- [猎奇智能招股说明书 p.26](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) — 弗若斯特沙利文：贴片设备台数份额 21%
- [猎奇智能招股说明书 p.20](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) — MRSI/ASMPT 专利诉讼
- [Mycronic CIOE 2025](https://www.mycronic.com/fr/product-areas/die-bonding/news--events/news/mrsi-at-cioe-2025-showcasing-the-mrsi-leap-die-bonder/) — LEAP 1.6T 定位
- [C-FOL 2026-04](https://c-fol.net/news/238_202604/20260403113532.html) — MRSI 批量订单
- [ASMPT MEGA Series 2025-01](https://semi.asmpt.com/de/news-center/press-releases/accelerating-the-future-of-optical-interconnects-with-asmpt-mega-series/) — ±1.5μm，1.6T roadmap
- [ASMPT CPO](https://www.asmpt.com/en/innovation/co-packaged-optics/) — AMICRA NANO
- [Besi Q2-24 Results](https://www.besi.com/investor-relations/press-releases/2024/details/be-semiconductor-industries-nv-announces-q2-24-results/) — hybrid bonding 29 台订单
- [Besi Investor Day 2025](https://finnhub.io/api/news?id=e64be378c8abda2d4c6575a17f12631abe05d10bf93c7a0b5f628586decba732) — TSMC COUPE, NVIDIA CPO
- [博众精工 2025H1](https://dataclouds.cninfo.com.cn/shgonggao/2025/2025-08-27/e93b336b826d11f09cadfa163e957f7a.pdf) — 400G/800G 批量订单
- [中信证券 2026-04-23](https://finance.sina.cn/hkstock/gsxw/2026-04-23/detail-inhvmvzh5044355.d.html) — 弗若斯特沙利文价值量占比
