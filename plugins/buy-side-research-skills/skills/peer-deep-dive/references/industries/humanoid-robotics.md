# Humanoid Robotics - 行业 KPI 模板

> ⚠️ **Emerging 行业警告**：本行业大部分公司处于 pre-revenue 阶段，KPI 体系仍在演化。本模板提供**当前可获得的有限指标 + 重要不确定性 + 研究方法建议**。3 年后回看，这些 KPI 可能完全不同。

## 行业边界

本模板覆盖：

### 直接 humanoid 玩家（多数 private）
- **Pure-play humanoid（多 private）**：Figure AI、Apptronik (Apollo)、1X Technologies、Sanctuary AI、Agility Robotics (Digit)、Persona Care、Unitree、Fourier Intelligence、宇树（Unitree）
- **混合 exposure 上市公司**：
  - **Tesla**：Optimus 是 part of company；不是 pure play 但是市场最大 humanoid theme
  - **Xiaomi**：CyberOne / 小米机器人
  - **NVIDIA**：Isaac、GR00T platform；spillover beneficiary
  - **小鹏**：第二代 Iron 机器人 

### Supply Chain（更适合上市投资）
- **减速器（关键、瓶颈零件）**：
  - 哈默纳科（Harmonic Drive Systems，日本）
  - 纳博特斯克（Nabtesco，日本）
  - 中国：绿的谐波、来福谐波（part of 双环传动）
- **伺服电机 / 驱动**：
  - Maxon（瑞士 private）、Faulhaber、Nidec、安川电机
  - 中国：汇川、鸣志电器、雷赛智能
- **传感器（力觉、视觉、IMU）**：
  - Ati Industrial Automation (Novanta)、Bota Systems
  - Cognex、Keyence（视觉）
- **滚珠丝杠 / 直线运动**：
  - THK、NSK（日本）
  - 中国：南方精工、贝斯特
- **执行器 / Actuator 整体方案**：
  - 中国：拓普集团、三花智控（Tesla 供应链）

不在本模板：
- **AGV / AMR (移动机器人 non-humanoid)**：仓储 / 物流机器人，应该参考 Advanced Manufacturing 模板
- **传统工业机器人**：FANUC、ABB、KUKA → Advanced Manufacturing
- **服务机器人 (扫地、配送)**：商业模式完全不同

## 当前 regime 的典型变量（市场在 trade 什么）

**当前主流叙事（2024-2026）**：
- **Tesla Optimus mass production timeline**：Musk 声称 2026 内部使用、2027 外销；市场对 timeline 高度敏感
- **Figure / Apptronik / 1X 商业部署进度**：Figure 与 BMW、Apptronik 与 Mercedes / GXO 的 pilot 进展
- **NVIDIA GR00T platform / Isaac**：是否成为 humanoid 行业 standard
- **AI Foundation Model 突破**：generalist robotic foundation models（如 Google RT-2、π0、Physical Intelligence）的能力突破
- **中国 supply chain 在哪一层胜出**：减速器（绿的谐波）、电机（汇川）、整体方案（拓普）
- **Cost trajectory**：Optimus 目标 $20K-30K vs 当前估算 $50K-100K BOM
- **TAM 想象空间**：Musk 声称 long-term humanoid TAM > all other Tesla products combined（10亿+ unit）

## 核心 KPI（极其有限，多数定性）

### 直接 Humanoid 公司（pure-play 多 private；上市 hybrid 主要看相关业务进展）

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Production Plan / Roadmap | 公布的量产时间表 | 历史 base rate：robotics 公司 90% delay |
| Customer Pilot Pipeline | Pilot deployment 数量 + 质量 | Figure-BMW、Agility-GXO 等是当前最 advance pilot |
| Pilot → Production 转化 | Pilot 完成后是否进入实际部署 | 关键 inflection signal |
| Technical Capability Demonstrations | 公开 demo 视频 / 论文 / benchmark | 但 demo 和真实环境 deployment 差异巨大 |
| 量产成本 (BOM) Trajectory | 单台机器人零件成本 | 关键经济性 driver；Tesla 目标 $20-30K |
| Funding Rounds (private) / Cash Position (public) | 融资 / 现金 | private 公司估值跃升信号；public 公司 runway |
| 主要客户 pipeline 公告 | Enterprise deployment 协议 | 区分 LOI/MOU vs Firm Order |

### Supply Chain Public Plays（更可分析）

#### 减速器（关键瓶颈零件）

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Humanoid 相关收入 / 订单披露 | 公司在 humanoid 业务的具体进展 | 多家披露"为 X humanoid 客户供货"但口径模糊 |
| 关节产能（每月减速器产能） | 月产能 + 产能扩张计划 | 一台 humanoid ~14-40 个减速器 |
| 价格 ASP | 单台减速器价格 | Harmonic 高端 $300-500，国产 $100-200，价差缩小 |
| 良品率 | 产品质量稳定性 | 国产替代关键 |
| 研发投入 / 占收入比 | R&D 强度 | 中国厂商在 catch-up 阶段 R&D 比例上升 |

#### 电机 / 驱动

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| Humanoid 相关电机 mix | 用于 humanoid 的电机收入占比 | 多数公司还是工业 + auto + 家电主导 |
| 力矩密度 (torque density) | 关键技术指标 | Humanoid 要求高于工业机器人 |
| Frameless / hollow shaft motor 占比 | 高端规格占比 | 决定能否进 humanoid 供应链 |

#### 传感器 / 关节单元 / 执行器整体

| KPI | 含义 | 警戒 / 解读 |
|---|---|---|
| 总成 vs 零件供应商 | 业务定位 | 总成提供商（如三花、拓普）value-add 更高 |
| 主要客户披露 | 与哪个 humanoid 公司签约 | 当前阶段 Tesla / Figure 供应链最受关注 |

### Tesla / NVIDIA / Xiaomi 等 Hybrid Exposure

这些公司的"Humanoid value"基本是**option value**，不直接计入当前 financials：

| 维度 | 评估方法 |
|---|---|
| Tesla Optimus value | 多数 sell-side 给 0 但允许 SOTP 加 $50-200B option value（与 BYD 比较等） |
| NVIDIA Robotics segment | < 5% 当前 revenue，但平台战略价值高 |
| 中国新势力（小鹏 Iron、小米 CyberOne） | 多数 still concept，几乎无 financial impact |

## 行业特定实证驱动因素

- **Tesla AI Day / Investor Day announcements**
- **Figure / Apptronik / 1X 重大 funding rounds 或 customer 公告**
- **Foundation model robotics 突破公告**（Google RT、π0、Physical Intelligence）
- **NVIDIA GTC + 季度财报中的 robotics commentary**
- **中国厂商重大订单公告**（特别是 Tesla 供应链 win）
- **量产成本里程碑**（如 Tesla 公布 actual unit cost）

## 典型估值锚点（极不稳定）

| 类型 | 估值方法 | 注意事项 |
|---|---|---|
| Pure humanoid 公司（private） | Funding round implied valuation | Figure 已估值 $26B（2025 sense）；多基于 AI 类比 |
| Tesla Optimus value | Option value + SOTP（独立 valuation） | 多数 sell-side 给 $0-200B 范围（极大 dispersion） |
| NVIDIA Robotics | Embedded in NVIDIA blended multiple | 单独 quantify 困难 |
| 中国 supply chain（绿的谐波等） | EV/Revenue、PE | 主题溢价 + 国产替代溢价；EV/Revenue typical 8-15x，远高于工业 peer |
| 拓普集团等 Tesla 供应链 | Tesla 供应链溢价 + auto parts 倍数 | 主题驱动 + 客户绑定 |

## Cross-cut 注意事项 / 重要不确定性

### 商业化 Timeline 高度不确定

- Musk 历史上 timeline 严重 over-promise（Robotaxi、Solar Roof、Cybertruck 都 delay 多年）
- "Mass production by 2026/2027"是 best-case，base case 可能 2028-2030+
- "Mass production"定义模糊：1万台 / 10万台 / 100万台 是完全不同 milestone
- 横向比较时要 normalize：每家公司 "production"的具体含义

### "Humanoid Play"实际 Exposure 程度差异巨大

- 真实 pure-play：上市的几乎没有
- 大部分"Humanoid concept stocks"实际 humanoid 收入 < 5% 总收入
- 中国 supply chain 公司（绿的谐波、汇川）真正 humanoid 收入也仅 1-3%
- 横向比较时要明确：是 "thematic exposure" 还是 "current revenue contribution"
- 不要假设 "X 公司是 Tesla 供应链"= "X 公司 humanoid value 已 priced"

### Foundation Model 风险

- 当前 humanoid 能力依赖 generalist robotic AI（如 NVIDIA GR00T、Google RT-2）
- 如果 foundation model 商品化（commodity），价值在硬件层面捕获
- 如果 foundation model 仍是 winner-take-all（NVIDIA-style），价值在软件层面
- 这个判断决定 supply chain 公司 vs Tesla / NVIDIA 谁是赢家

### 中国 supply chain 国产替代 narrative

- 中国厂商在减速器、电机等关键零件 catch-up 速度快
- 但 Tesla 对中国供应链使用程度受 geopolitics 影响（CHIPS Act 类似限制）
- 国产替代溢价：当前已部分 priced in 估值
- "国产替代"成功 + Tesla 减少中国采购 = 双向风险

### Demo 和真实部署的 gap

- 公开 demo 视频是高度 controlled environment（人为 setup、最佳 take）
- 真实 deployment 需要 robustness、battery life、safety、cost
- Figure / Optimus 的 Demo 看起来已经能"工作"，但实际 deployment 仍是 narrow tasks
- 不要从 demo 推断商业化进度

### "Pilot"的真实意义

- 多数"customer pilot"是 R&D collaboration、PR exercise
- 真正的 production deployment（替代实际人类工作）凤毛麟角
- 区分 "1 台 robot 在客户工厂跑测试" vs "100 台在 production 持续工作"

### Tesla Optimus 的 Optionality

- Tesla 估值已经包含一些 Optimus value（市场预期 已 priced in）
- 但具体多少 Optimus value 是 priced 是高度 subjective
- Sell-side 估算 from $0 to $1T+（极大 dispersion）
- "买 Tesla 是为了 Optimus" 是常见但 risky thesis（同时承担 EV business 风险）

### 估值倍数的"主题溢价"持续多久

- 中国 humanoid supply chain（绿的谐波等）estimated 60%+ 当前估值是 humanoid 主题溢价
- 主题褪色（如 Optimus delayed、Figure 商业化失败）→ 估值快速 de-rate
- 每次"主题溢价"持续 6-24 个月，然后或者 fundamentals catch up，或者 collapse

### 研究方法建议

由于 KPI 有限，建议：

1. **不要假装可以做传统 fundamental 估值**——多数 humanoid 公司不能用 DCF
2. **以 milestone 跟踪为主**：customer pilot、technical capability、cost reduction、产能扩张
3. **Cross-cut 主要看"主题暴露程度差异"**：哪些公司是 pure thematic exposure，哪些是 spillover beneficiary
4. **承认 high uncertainty + 适当 sizing**：humanoid thesis 不应该单一 position，而是 thematic basket
5. **Pair trade 思路**：long 强 thesis 公司 / short weak thesis 公司或主题代理（如 long Tesla / short legacy auto）
6. **Catalyst-driven trades**：财报、AI Day、重大 customer 公告作为 catalyst
7. **极度小心估值倍数比较**：不同公司的"humanoid premium"权重不同，倍数直接比较失真

## 这个模板的主要不确定性

- **3 年后 KPI 体系会大变**：pilot count → deployment count → unit count → revenue 等会逐步标准化
- **现在的 leader 不一定是 long-term winner**：technology / cost / scaling 决定，多数早期 leader 会 disappear
- **整体 TAM 的 high uncertainty**：可能远大于市场想象（Musk vision），也可能远小于（如果 use case 始终是 narrow industrial 任务）

如果你的研究目的是 thematic exposure，本模板已足够。如果是 deep fundamental 价值评估，**承认局限**比强行套框架更负责任。
