# Quantum Computing - 行业 KPI 模板

> ⚠️ **Pre-Commercial 行业警告**：本行业绝大多数公司处于 R&D 阶段，没有有意义的运营 financial KPI。本模板提供**技术里程碑、cash burn、option value 评估方法**——而非传统 fundamental KPI。如果你期待 DCF / EBITDA 横向比较，传统框架在这里基本失效。

## 行业边界

本模板覆盖：

### Pure-Play Quantum 公司（上市）

- **Superconducting qubits（超导）**：
  - **IBM Quantum**（part of IBM，spillover exposure，最 advanced commercial deployment）
  - **Rigetti Computing (RGTI)**：上市 pure-play，超导路线
  - **D-Wave Systems (QBTS)**：上市 pure-play，annealing （量子退火）路线（注：annealing 不是 universal quantum computing）
  
- **Trapped Ion（离子阱）**：
  - **IonQ (IONQ)**：上市 pure-play，离子阱路线，相对 advanced
  - **Quantinuum**（Honeywell 50%+ + Cambridge Quantum 合并；Honeywell 是上市的 partial proxy）
  
- **Photonic（光量子）**：
  - **Xanadu**（private）
  - **PsiQuantum**（private，Microsoft / Microsoft Azure ecosystem）
  
- **Neutral Atom / Cold Atom**：
  - **Atom Computing**（private）
  - **Pasqal**（private，欧洲）
  - **QuEra**（private）
  - **Infleqtion (ColdQuanta)**（拟上市）

### Spillover / Adjacent Public Plays

- **IBM**：Quantum One Hub、Q System One、Q System Two（Heron processor），最 visible commercial deployment
- **Google**：Quantum AI（Willow processor，2024 milestone）
- **Microsoft**：Azure Quantum platform、Majorana 1 (2025) 拓扑量子声明
- **Amazon**：AWS Braket platform
- **Intel**：Tunnel Falls 硅基 quantum chip
- **Nvidia**：CUDA-Q 量子计算软件

### Quantum-Adjacent Hardware / Components

- **Cryogenics**：Bluefors（private）、Oxford Instruments（PLC，OXIG.L）
- **Lasers / Optics（for ion trap、photonic）**：MKS Instruments、Coherent

不在本模板：
- **Quantum Sensing / Quantum Communication / Quantum Cryptography**：相关但是不同应用，估值逻辑不同
- **Post-Quantum Cryptography (PQC)**：实际是 cybersecurity / software，参考 software-ai-applications.md

## 当前 regime 的典型变量（市场在 trade 什么）

**当前主流叙事（2024-2026）**：
- **Google Willow milestone (2024 Dec)**：105-qubit processor，below threshold for quantum error correction
- **IBM Quantum roadmap 进度**：Heron / Condor / Flamingo / Kookaburra processors
- **Microsoft Majorana 1 (2025 Feb)**：拓扑量子 claim，但学界质疑较多
- **Quantum Error Correction (QEC) 突破**：从 NISQ era 到 fault-tolerant era 的关键过渡
- **Government funding 加码**：US National Quantum Initiative、China 巨额投入、EU Quantum Flagship
- **Physical Qubits → Logical Qubits ratio**：当前 typically 1000:1，目标 100:1
- **Commercialization Timeline**：行业普遍认为 fault-tolerant 商业化 2030-2035+
- **NVIDIA / Classical Hybrid**：CUDA-Q、quantum-classical 混合 workload 趋势

**关键 caveats**：
- Pure-play quantum 上市公司（IonQ、Rigetti、D-Wave）reported revenue 多数来自 government grants、research collaborations、cloud access fees——不是 enterprise commercial scale
- 多数 milestone announcements 是 hype-driven，需要通过 peer-reviewed publications + community 反应判断真实性
- Stock prices 波动巨大（IonQ 单日 +/-30% 不罕见）

## 核心 KPI（极其有限，多数是 milestone-driven）

### 技术里程碑（最重要）

| Metric | 含义 | 警戒 / 解读 |
|---|---|---|
| Physical Qubit Count | 物理量子比特数 | 单看数量误导；要看 fidelity / coherence |
| Two-qubit Gate Fidelity | 双比特门保真度 | 当前 leader: ~99.9%；目标 99.99%+ for FTQC |
| T1 / T2 Coherence Times | 量子态相干时间 | 决定能执行多深电路 |
| Error Rate（per gate / per cycle） | 每门 / 周期错误率 | 决定 QEC overhead |
| Logical Qubits Demonstrated | 已 demo 的逻辑比特数 | 当前 SOTA: < 10 logical qubits |
| Quantum Volume (IBM 定义) | 综合性能指标 | 但仅 IBM 主推，跨公司可比性差 |
| Algorithmic Qubits (IonQ 定义) | IonQ 综合指标 | 同上，IonQ 自定义 |
| 是否实现 Quantum Advantage | 在某具体问题上 demo 比经典快 | Google 2019、2024 都 claim 过；scientific value vs commercial value 不同 |

### Cash & Survival（pure-play 至关重要）

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Cash Position | 现金余额 | 决定生存窗口 |
| Quarterly Cash Burn | 季度烧钱 | typical $30-80M for pure-play |
| Runway (months) | 现金 / 月烧钱 | < 18 月警惕；< 12 月需融资 |
| Government Grant Revenue | 政府合同收入 | 多数 pure-play "revenue" 主要来自此 |
| Equity Dilution (Share Count YoY) | 股本稀释 | quantum 公司频繁增发；YoY +30% 是 typical |

### "Commercial" 信号（当前阶段勉强可看的）

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Cloud Access / Subscription Revenue | 客户通过 cloud 访问 quantum 收入 | 早期阶段，多数客户在 R&D 用 |
| Enterprise Pilot Customers | 大企业 pilot 数量 | 多数仍 PoC，无 production deployment |
| Government Contract Wins | DARPA、DOE、NSF 合同 | 关键收入来源；区分 grant vs procurement |
| Public Sector vs Private 收入占比 | Customer mix | 当前 typical 60-80% government/public |

### IBM / Google / Microsoft / Amazon Cloud Quantum

不要期待这些大公司单独披露 quantum revenue：
- **IBM Quantum Network**：> 250 organizations，但具体 revenue contribution 极小（< 1% of IBM total）
- **Microsoft Azure Quantum**：通过 Azure 提供 access；revenue 嵌入 Azure
- **Google Quantum AI**：纯 R&D，no separate revenue
- **AWS Braket**：cloud 平台费用，不单独披露

**研究方法**：把 quantum 视作大公司的 long-term R&D investment，类似 Project Loon / Calico——估值时基本给 0 直接价值，但承认 option value。

### Hardware Component Suppliers

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Cryogenics 出货量（dilution refrigerators） | 给 quantum 的关键设备 | Bluefors、Oxford Instruments 主导市场 |
| Quantum 相关收入占比 | Bluefors / Oxford 等公司的 quantum exposure | typical < 10% 总收入；但 quantum segment 高 growth |

## 行业特定实证驱动因素（股价跟着什么动）

- **重大科学发表**（Nature、Science 论文 announcement）
- **里程碑公告**（Google Willow、Microsoft Majorana、IBM Quantum Centennial）
- **政府合同 wins**（DARPA、DOE、NSF）
- **DARPA Quantum Benchmarking Initiative 选拔**（2024 选出 18 家进入 stage A）
- **Funding rounds（pure-play 上市 / private）**：极大波动事件
- **Roadmap delivery / miss**：尤其 IBM 的 annual roadmap update
- **Tech press 突发新闻**（"breakthrough" claims）

注意：quantum 股票对**新闻情绪**反应远大于对 fundamentals 反应——单条 Twitter / Reddit post 可触发 20%+ 单日波动。

## 估值锚点（传统方法基本失效）

| 类型 | 估值方法 | 注意事项 |
|---|---|---|
| Pure-play 上市（IonQ、Rigetti、D-Wave） | EV / Cash + Option Value | 当前估值多基于 market cap = cash + IP option |
| 上市后 funding round 估值 | Market cap vs runway | IonQ 等多次低估值 PIPE 融资 |
| 大公司 spillover (IBM、Google、Microsoft) | 嵌入主业 multiple，不单独 quantify | Quantum value 多数 not priced |
| Hardware suppliers (Bluefors、Oxford) | EV/EBITDA、segment growth premium | 受 quantum 主题部分溢价 |

**用 EV/Revenue 比较 quantum pure-play 公司基本没有意义**——revenue 数字小、组成复杂（grants vs commercial）、商业化阶段太早。

## Cross-cut 注意事项 / 重要不确定性

### 不同技术路线的根本差异

不是 head-to-head 竞争——五种主要技术路线各有优劣：

| 路线 | 优点 | 缺点 | 代表 |
|---|---|---|---|
| Superconducting | Fast gates、SDSF（半导体 fabrication）兼容 | 需要 mK 温度（cryogenics 重）、qubit fidelity 中等 | IBM、Google、Rigetti |
| Trapped Ion | 高 fidelity、长 coherence | Slow gates、scaling 难 | IonQ、Quantinuum |
| Photonic | 室温运行、scaling 潜力大 | Photon loss、component 复杂 | Xanadu、PsiQuantum |
| Neutral Atom | 高 connectivity、scaling 潜力 | 早期阶段、控制难 | Atom Computing、QuEra、Pasqal |
| Topological | （理论上）天然 fault-tolerant | 仍未确认实验性证明 | Microsoft（争议） |

**Cross-cut 横向比较时，记得：不能直接比"qubit count"——不同 routes qubit 含义完全不同**。

### 商业化 Timeline 极不确定

- 行业 base rate：每个 5 年承诺都被 push out
- 当前 community consensus（2024 量子顶级 conference）：fault-tolerant quantum advantage in valuable problems 2030-2035+
- 但 valuable specific applications（drug discovery、cryptography breaking、optimization）可能 5-10 年后
- **不要 anchor on Roadmap announcements 的 timeline**——历史 90%+ 都 delay

### "Quantum Advantage" Claims 的真实性

- "Quantum Supremacy"（Google 2019）= 在 contrived problem 上比 classical 快——无商业价值
- "Quantum Advantage" 在 useful problem 上还没真正实现
- 学术 vs 商业意义差异巨大
- 横向比较时区分：是 narrow scientific milestone 还是 commercial breakthrough?

### Hype Cycle 的反复

- 2019：Google Quantum Supremacy → IonQ SPAC + Rigetti SPAC
- 2021：Quantum SPAC mania → IonQ 估值 $10B+
- 2022-2023：Disillusionment → 股价 -80%+
- 2024：Google Willow + AI / quantum convergence → 新一波 hype
- 横向比较时识别：现在是 hype cycle 哪个阶段？

### Pure-Play 公司的 Survival Risk

- 多数 pure-play quantum 公司未必能撑到商业化
- 历史 base rate：pre-commercial deep-tech 公司 80%+ 最终消失或被收购
- IonQ / Rigetti / D-Wave 的"成功 path" 多数是被大公司收购，而非 stand-alone 商业化
- 横向比较时：buyer attractiveness（IP、talent、客户关系）可能比 standalone fundamentals 重要

### "Real Customers" vs "Research Partnerships"

- 当前 IonQ / Rigetti 等公布的"客户"多数是 research partnerships
- 真正 "production use" 的企业部署数量极少
- 看 cloud access usage、API call volume（如有披露）比 customer count 信息更多

### Government Funding 依赖

- 多数 pure-play 公司收入主要来自 DARPA、DOE 等政府合同
- 美国 vs 中国 vs 欧洲 funding 强度不同
- 政府预算优先级变化（quantum vs AI vs other）影响行业 funding pool
- "Commercial revenue"和"government revenue"的可比性低

### NVIDIA Hybrid Quantum-Classical 的影响

- NVIDIA CUDA-Q + quantum simulation 模糊了 "quantum hardware vs classical simulation" 边界
- 短期可能延后真实 quantum hardware 的商业化（because classical can simulate well enough for now）
- 长期可能加速生态建设（developer ecosystem）
- 横向比较 quantum hardware 公司时，要意识到：classical simulation 是当前主要竞争对手

### 估值波动性

- 量子股票单日 20-30% 波动 normal
- Earnings 财报后波动大但 fundamentals 信息含量低
- 不适合 pair trade（高 idiosyncratic noise）
- Sizing 建议：极小（thematic basket，单 position < 1% portfolio）

## 研究方法建议

由于传统 fundamental KPI 基本失效，建议：

1. **承认估值是 option value-driven**——不要硬套 DCF 或 EV/EBITDA
2. **聚焦三个维度比较**：
   - **Technical milestones**（上面的 fidelity、qubit count、QEC progress）
   - **Cash runway**（决定能否撑到下一阶段）
   - **Commercial proof points**（pilot → production 转化）
3. **跟踪 base rate**：每个 quantum company 历史里程碑是否 deliver on roadmap?
4. **了解 5 个技术路线的优劣**：不能简单认为"qubit 多就好"
5. **承认信息劣势**：quantum 是高度专业化领域，普通 analyst 难判断真实技术进展，依赖独立专家访谈
6. **以 thematic exposure 而非 single-name conviction**：quantum thematic basket 比 single bet 风险低
7. **Cross-cut 重点**：哪些公司是真正在做 quantum、哪些是"quantum-washed"（add quantum to name 但 substance 有限）

## 这个模板会快速过时

- 商业化 breakthrough 后 KPI 体系会重写
- 即使 5 年后回看，技术 leader 可能完全不同
- 持续关注 quantum 领域学术 publications + 主要科学会议（QIP、APS March Meeting、Q2B）

如果你的目的是 **thematic exposure / pair trade catalyst plays**，本模板提供了基本判断框架。
如果是 **deep fundamental investment thesis**，量子领域目前不适合 traditional methodology——这是个 honest answer 而非 cop-out。
