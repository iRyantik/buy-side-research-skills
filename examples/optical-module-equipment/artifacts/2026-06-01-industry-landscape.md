# 光模块设备产业链 — Industry Landscape

> **artifact**: `industry-landscape` | **as-of**: 2026-06-01
> **related**: [[2026-06-01-teach-in-optical-module]] | [[2026-06-01-mechanism-insight-die-bonding-equipment]] | [[2026-06-01-mechanism-insight-pcb-test-equipment]]

---

## 1. Verdict

光模块设备是 AI 基础设施链条里**最有结构性 alpha 的设备赛道**——不是"AI 好了所以设备卖多了"的线性逻辑，而是"每一代光模块速率升级都把制造精度门槛往上抬一档，旧设备直接报废，必须换新"。这个行业当前该投，但**不是所有段都该投**。

**核心判断**：耦合设备 > 贴片设备（高端） > 测试设备（晶圆级） >> 中端贴片 >> 模块级老化。利润最肥的段是耦合（壁垒最高、CPO 时代价值量跳升最大），其次是高端贴片（MRSI/Besi 的地盘）。中端贴片（猎奇等）量最大但利润薄。模块级老化测试面临 CPO 的结构性降级风险。

**最大风险**：CPO 渗透率从 5%→15%→30% 的时间线如果大幅慢于预期，耦合设备的价值量跳升会被推迟，行业超额收益回归均值。

---

## 2. 产业链地图

```
  ┌──────────────┐      ┌─────────────────────┐      ┌──────────────┐      ┌──────────┐
  │  上游材料     │      │     设备制造         │      │  光模块厂     │      │ 终端客户  │
  │  ─────────── │  →   │  ───────────────── │  →   │  ──────────  │  →   │          │
  │  FPGA 芯片    │      │  固晶机    18.9%    │      │  中际旭创     │      │ Google   │
  │  精密导轨     │      │  耦合机    23.3%    │      │  新易盛       │      │ Meta     │
  │  机器视觉     │      │  键合机    ~10%     │      │  Coherent     │      │ 英伟达   │
  │  探针/焊料    │      │  老化/Burn-in 31.4% │      │  光迅科技     │      │ Amazon   │
  │               │      │  自动化整线  ~15%    │      │               │      │ Microsoft│
  │  ─────────── │      │  ───────────────── │      │  ──────────  │      │          │
  │  壁垒：低     │      │  壁垒：最高          │      │  壁垒：中     │      │          │
  │  利润：薄     │      │  利润：最肥          │      │  利润：中     │      │          │
  │  集中度：分散 │      │  集中度：高          │      │  集中度：高   │      │          │
  └──────────────┘      └─────────────────────┘      └──────────────┘      └──────────┘
     材料供应商              设备公司                   模块制造商            数据中心
     国产替代有进展          投资价值最高               享受产能扩张          最终需求方
```

### 价值分配总结

```
整个光模块设备链条 ~CNY 51.8B（2024）

  ┌──────────────────────────────────────────────────┐
  │  31.4%  老化/测试    ← 最大块，但 CPO 时代分化     │
  │  23.3%  耦合         ← 最肥的肉，壁垒最高          │
  │  18.9%  贴片/固晶    ← 增速快，精度壁垒深          │
  │ ~15%    自动化/整线   ← 量最大但利润薄              │
  │ ~10%    键合/封装     ← 技术成熟，不是瓶颈          │
  └──────────────────────────────────────────────────┘

利润在往两端迁移：
  → 高端（耦合的 ±0.05μm + 贴片的 ±1μm）越来越肥
  → 低端（中端贴片、自动化线体）越来越卷
```

---

## 3. 竞争格局

| 设备段 | 价值量 | 格局 | 进入壁垒 | 国产替代 | 竞争趋势 |
|---|---|---|---|---|---|
| 固晶/贴片 | 18.9% | 高端寡头（MRSI/Besi/ASMPT），中端分散 | **高**（±1-3μm 精度） | 中端 70%，高端 20% | 代际升级在筛人——每次精度跳变筛掉一批低端 |
| 光学耦合 | 23.3% | 镭神 27%（台数 #1）+ ficonTEC + 猎奇 18% | **最高**（±0.05μm + 算法 + 客户锁入） | ~45% 台数，金额可能更低 | CPO 会让耦合从"加分项"变成"及格线"——需求爆炸 |
| 引线键合 | ~10% | K&S/ASMPT/Shinkawa 寡头 | 中 | — | 技术成熟，格局稳定 |
| 老化/Burn-in | 31.4% | Keysight/Chroma/AEHR 海外主导 | 中高 | 联讯 9.9%（前五唯一中国） | **CPO 最大风险点**——模块级老化可能被晶圆级替代 |
| 模块终测 | 含在 31.4% | Keysight/VIAVI/Anritsu >80% | 中高（平台+协议绑定） | 联讯 #1 | 1.6T 让测试复杂度跳变，短期利好 |
| 自动化整线 | ~15% | 罗博特科/博众，较分散 | 低（系统集成） | — | 会做自动化 ≠ 能吃到核心利润 |

### 关键竞争动态

- **贴片高端段是 MRSI/Besi 两家的游戏**。猎奇 21% 台数份额但精度段在 ±5-7μm。1.6T 要求 ±3μm，猎奇进不来。
- **耦合的壁垒在客户锁入**。ficonTEC 绑了博通/英伟达，MRSI-A-L 在推进 CPO 项目。一旦客户把耦合工艺和你的设备深度绑定，换供应商的成本极高。
- **测试的分化刚刚开始**。Keysight 两头下注（模块测试 + 晶圆测试），AEHR 纯晶圆级 Burn-in（受益于 CPO）。纯模块级测试小厂面临生存危机。

---

## 4. 行业驱动力

### 需求端

- **每 GPU 带宽必须跟上算力**：GPU 算力每代翻倍（H100→B200→Rubin），每 GPU 出口带宽从 400G→800G→1.6T。不是"GPU 多了所以光模块多了"，是"每张 GPU 要的光模块速率翻倍"。
- **800G→1.6T 出货量跳升**：800G 约 18M 只（2025）→41M 只（2026E），1.6T 从刚商用→11M 只（2026E）。每百万只新增产能 = CNY 4-6B 设备投资。
- **ASIC 集群的额外增量**：Google/Meta/Amazon/MSFT 自研 ASIC 在 2026-27 大规模部署，ASIC 之间的互联也需要光模块。

### 供给端瓶颈

- **FPGA 芯片 52 周交期**：Xilinx FPGA 是贴片/耦合/测试设备的核心控制芯片，交期从 8-10 周暴增到 52 周。设备商产能被上游芯片卡住。
- **高端精度产能有限**：±1μm 固晶全球只有 3-4 家能做（MRSI/Besi/ASMPT/Finetech），±0.05μm 耦合只有 2-3 家（ficonTEC/MRSI-A-L/镭神部分产品线）。
- **熟练技工短缺**：设备生产/验收需要熟练技工，短期无法缓解。

### 代际升级（最强驱动力）+ 需求弹性测算

**为什么耦合是唯一需求弹性超过 3 倍的设备段**：

```
Pluggable 时代：一个 800G 光模块 = 8 个光口 = 8 根光纤需要耦合
CPO 时代：      一个 CPO 引擎   = 16-64 个光口 = 16-64 根光纤需要耦合

  耦合点数：  8 → 16-64     = 2-8x
  每点精度：  ±1μm → ±0.05μm = 20x（精度跳变）
  耦合时间：  单端口串行 → 多端口并行 = 设备复杂度 3-5x

  需求弹性 = 点数 × 复杂度 = 保守 3x，CPO 全规格 8x+
```

| 设备段 | Pluggable（800G）| CPO | 弹性 | 为什么 |
|---|---|---|---|---|
| **固晶** | 1 模块 = 贴 2-4 颗光芯片 | 1 引擎 = 贴 4-8 颗 | **~2x** | 光芯片数量涨，但精度也涨 → 台数+ASP 双涨 |
| **耦合** | 1 模块 = 耦合 1-2 根光纤 | **1 引擎 = 耦合 16-64 根** | **3-8x** | 端口数跳升是耦合独有的杠杆 |
| **老化/测试** | 模块级老化 24-96h | 晶圆级替代模块级 | **分化** | 总量不一定涨，结构剧变 |

**耦合是唯一一个"CPO 让工作量指数级增加"的设备段**——固晶工作量线性增加（多几颗芯片），耦合工作量乘数级增加（多几十根光纤+每根精度更高+需要同时做）。

### 代际升级（最强驱动力）

```
400G:  贴片 ±5μm, 耦合 ±1μm     → 设备精度要求低，国产线够用
800G:  贴片 ±5μm, 耦合 ±0.5μm   → 耦合开始有壁垒
1.6T: 贴片 ±3μm, 耦合 ±0.1μm   → 贴片壁垒跳升，猎奇被筛掉
3.2T: 贴片 ±1μm, 耦合 ±0.05μm  → 只有 MRSI/Besi/ficonTEC 能做
CPO:  异质集成, 多端口并行耦合    → 耦合价值量爆炸，模块测试萎缩
```

---

## 5. 投资判断

### 行业 regime：结构性扩张期的非对称受益

不是"行业在增长所以都受益"。设备精度要求每代翻倍 = **精度不够的设备直接出局**。这是设备行业最理想的格局——不是在分一个变大的饼，而是饼变大了**同时**桌上的玩家变少了。

### 多空分歧

| 多方论点 | 空方论点 |
|---|---|
| AI 集群规模指数增长 → 光模块速率升级加速 → 设备换机周期从 5 年缩到 2-3 年 | 1.6T/CPO 渗透速度可能慢于预期（技术难度 + 客户验证周期长） |
| 国产替代 + 精度升级 = 中国设备商双受益 | 猎奇 MRSI/ASMPT 专利诉讼如果败诉，国产替代逻辑打折 |
| 耦合设备是下一个"光刻机"级别的壁垒赛道 | FPGA 缺货卡住设备商产能 → 订单好但收入转化不了 |

### 我的看法

**偏向多方，但选段比选方向重要。**

最看好的三段：
1. **耦合设备**（CPO 时代最确定受益，多端口并行耦合是刚需）
2. **高端贴片**（±1μm 俱乐部不会扩大，MRSI/Besi 享受卖方定价）
3. **晶圆级测试**（CPO 创造的全新品类，从零到一的增量）

### Kill criteria

- 如果 Q2-Q3 2026 GT 订单回落到 Sek 300M 以下 → 设备超级周期被证伪
- 如果 Broadcom Bailly CPO 交换机 2027 年还没有规模出货 → CPO 时间线需要重估
- 如果猎奇在 MRSI 专利诉讼中胜诉 → 高端精度段的国产替代会提前

---

## 6. 公司注册表

### A 股

| 公司 | 代码 | 产业链位置 | Exposure | 为什么在表里 |
|---|---|---|---|---|
| 罗博特科 | 300757 CH | 耦光+整线 | direct | 并表 ficonTEC，A 股最纯的耦合设备标的 |
| 博众精工 | 688097 CH | 贴片+自动化 | direct | 400G/800G 贴片批量订单，1.6T 在研 |
| 普源精电 | 688337 CH | 测试仪表 | indirect | 国产示波器龙头，向光模块测试延伸 |
| 光库科技 | — | 铌酸锂调制器 | thematic | 薄膜铌酸锂是 3.2T 调制方案 |

### 海外上市

| 公司 | 代码 | 产业链位置 | Exposure | 为什么在表里 |
|---|---|---|---|---|
| Mycronic | MYCR SS | 固晶+耦合 | direct | MRSI LEAP ±1μm + A-L 有源耦合，固晶+耦合成套全球唯一 |
| ASMPT | 0522 HK | 贴片+键合+封装 | direct | MEGA 系列 1.6T 固晶，AMICRA NANO CPO bonding |
| Besi | BESI NA | 贴片+hybrid bonding | direct | 全球 die attach 绝对龙头（~39%），D2W hybrid bonding 给 TSMC COUPE/NVIDIA CPO |
| Keysight | KEYS US | 测试 | direct | 1.6T 制造测试场景定义者，晶圆级+模块级双覆盖 |
| VIAVI | VIAV US | 测试 | direct | 800G/1.6T/3.2T 验证链条 |
| AEHR | AEHR US | 晶圆级 Burn-in | direct | 全球半导体晶圆级老化测试龙头，CPO 受益 |

### 未上市/拟 IPO

| 公司 | 产业链位置 | 为什么在表里 |
|---|---|---|
| 猎奇智能 | 贴片+耦合 | 2024 年贴片全球 #1（21% 台数），拟创业板 IPO。MRSI/ASMPT 专利诉讼未决是最大风险 |
| 镭神技术 | 耦合 | 2024 年耦合全球 #1（27% 台数），华为哈勃投资，C 轮 |
| ficonTEC | 耦合 | 罗博特科并表，博通/英伟达独家供应商。理解罗博特科必须理解 ficonTEC |

### 已上市（A 股补充）

| 公司 | 代码 | 产业链位置 | 为什么在表里 |
|---|---|---|---|
| 联讯仪器 | 688808 CH | 老化/测试 | 2026-04-24 科创板上市，国产光模块测试仪表 #1，覆盖 800G/1.6T，市值 ~1700 亿。光模块封测链条 A 股市值最大的纯正标的 |

---

## 7. Routing

| 想做什么 | Skill |
|---|---|
| 深挖固晶设备机制和 MRSI vs Besi vs ASMPT 竞争 | `/mechanism-insight die-bonding` |
| 深挖 PCB 测试设备（Mycronic atg） | `/mechanism-insight pcb-test` |
| 筛选公司优先级、排研究顺序 | `/candidate-screener` |
| 快速扫 Mycronic 这家公司 | `/stock-quickread MYCR SS` |
| 快速扫罗博特科 | `/stock-quickread 300757` |
| 横向比较 Mycronic vs ASMPT vs Besi | `/peer-deep-dive` |
| 拆 Mycronic revenue/margin driver | `/driver-map` |

---

## Resources

- [猎奇智能招股说明书（申报稿）](https://data.eastmoney.com/notices/detail/A25297/AN202512261808657383.html) — 弗若斯特沙利文行业数据、市场份额、专利诉讼
- [Mycronic MRSI Die Bonding](https://www.mycronic.com/product-areas/die-bonding/)
- [Mycronic CIOE 2025：LEAP 1.6T](https://www.mycronic.com/fr/product-areas/die-bonding/news--events/news/mrsi-at-cioe-2025-showcasing-the-mrsi-leap-die-bonder/)
- [C-FOL 2026-04：MRSI 1.6T 批量订单](https://c-fol.net/news/238_202604/20260403113532.html)
- [ficonTEC Photonic Device Assembly](https://www.ficontec.com/photonic-device-assembly/)
- [ASMPT Co-Packaged Optics](https://www.asmpt.com/en/innovation/co-packaged-optics/)
- [Besi Hybrid Bonding](https://www.besi.com/)
- [联讯仪器高速光模块测试机](https://cn.semight.com/high-speed-transceiver-ate)
- [Keysight 1.6T Manufacturing Test](https://www.keysight.com/mx/en/use-cases/optimize-1-6t-optical-transceiver-manufacturing-tests.html)
- [VIAVI High-Speed Networks](https://www.viavisolutions.com/en-us/products/high-speed-networks)
- [镭神技术 C 轮融资](https://www.donews.com/news/detail/4/5461286.html)
- [博众精工 2025H1](https://dataclouds.cninfo.com.cn/shgonggao/2025/2025-08-27/e93b336b826d11f09cadfa163e957f7a.pdf)
- [罗博特科 2025 年年报](https://disc.static.szse.cn/disc/disk03/finalpage/2026-03-31/8ef27e36-d90d-4ec2-8530-8a714b180238.PDF)
- [LightCounting Optical Transceiver Forecast 2025](https://www.lightcounting.com/)
