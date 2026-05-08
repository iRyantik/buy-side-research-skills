# Industry KPI Framework — 横向研究的元方法论

> 当 `references/industries/` 没有对应行业模板时使用本文件**现场推导 KPI**。
> 这不是模板的替代品，是模板**未覆盖时的构建工具**。
> 任何新行业（商业航天、合成生物、空中出行、urban farming、稀土永磁、core SMR 等）都能用这套方法处理——不需要穷举行业模板。

## 核心原则：任何行业的横向研究都在回答 5 个问题

不论行业多新、多 emerging，要做有意义的 cross-cut，必须回答下面 5 个问题。每个问题用该行业**最 informative** 的 1-2 个 KPI 回答。

### 问题 1: 这家公司靠什么赚钱（收入来源）
- 收入是 unit-driven 还是 contract-driven？
- 单一收入流还是多元？
- 买家是政府 / 企业 / 消费者？
- 收入是 recurring 还是 one-time？

### 问题 2: 赚钱的效率如何（unit economics）
- Unit economics 是否成立？
- Margin 结构（gross / operating / net）？
- 规模效应是否存在？
- 横向 spread 是基本面差异还是会计 artifact？

### 问题 3: 资本投入如何（capital cycle 位置）
- 重投资期 / 维持 / 收割？
- Capex 强度 vs 同业？
- ROIC 是否高于 WACC？
- Capital allocation 是否合理（过去 5 年）？

### 问题 4: 风险结构如何
- Idiosyncratic 风险（项目 / 客户 / 监管 / 技术）
- Systematic 暴露（macro / commodity / 利率）
- 单点失败 mode 是什么

### 问题 5: 商业化进度如何（如适用）
- Pre-commercial / Early scale / Mature / Decline 哪个阶段？
- 关键 milestone 是什么？
- 距离下一个 inflection point 多远？

**横向比较时，N 家公司应在每个问题上都能给出可比答案——不能可比的问题要明确说"该问题在 N 家公司间不可比，因为 ...."。**

---

## 4 个推导维度

判断行业在 4 个维度的位置，决定每个问题应该用什么 KPI 回答。

### 维度 1: 商业模式类型

| 模式 | 特征 | KPI 推导倾向 |
|---|---|---|
| **Commodity producer** | 产品价格由外部市场决定（油、气、矿、农产品） | 单位生产成本、产量增长、储量、对冲覆盖、breakeven price |
| **Capital equipment / 设备制造** | 卖大件设备（机床、火箭、卫星、风机） | Backlog、book-to-bill、产能利用率、ASP、单位成本下降曲线 |
| **Project-based** | 一次性大项目执行（EPC、construction、定制工程） | Project margin、cost overrun 历史、合同结构、working capital |
| **Recurring service / SaaS / Subscription** | 持续收费 | ARR / NRR / CAC / churn / LTV |
| **IP licensing / royalty** | 授权 IP 收费 | License revenue、royalty rate、专利组合质量 |
| **Platform / Network** | 双边或多边市场 | Take rate、GMV、用户增长、network effect 强度 |
| **Pre-commercial deep tech** | 还没有商业化收入（quantum、early space、fusion、early humanoid） | **不要硬套财务 KPI**——看里程碑、cash runway、技术指标、客户 pipeline 质量 |
| **Hybrid** | 多种模式混合（很多大公司） | 必须按 segment 拆分用不同 KPI，否则混合 KPI 失真 |

**关键**：识别 hybrid 公司——很多上市公司是 hybrid。比如 Rocket Lab 是 launch service + spacecraft manufacturing 双业务，必须分别看。

### 维度 2: 周期性

| 等级 | 含义 | KPI 推导倾向 |
|---|---|---|
| **Highly cyclical** | 业绩与商品 / macro 高度相关（O&G、建筑、半导体、机床） | 必看 mid-cycle 估值、book-to-bill、库存、capacity utilization |
| **Moderate cyclical** | 部分相关（部分 industrial、部分消费） | Aftermarket / service 占比是稳定 anchor |
| **Stable / Defensive** | 跨周期稳定（utility、必需消费、医药） | 关注增长 driver 而非周期；recurring revenue 占比 |
| **Secular growth** | 长期结构性增长（云、AI 应用、新能源、emerging tech） | 渗透率、TAM 占比、growth durability |
| **Pre-cycle** | 还没建立周期（新行业） | 看 leading indicators 而非 cycle metrics |

### 维度 3: 政策依赖

| 等级 | 含义 | 必加监控指标 |
|---|---|---|
| **高度依赖** | 收入 / margin 显著依赖政策（renewable、nuclear、defense、商业航天、医药 reimbursement） | 政策事件日历、补贴 / tax credit 收益、监管 milestone |
| **中度依赖** | 部分受政策影响（auto emissions、化工 environmental） | 关键监管节点 |
| **低依赖** | 政策影响有限（消费、软件、纯商业 B2B） | 不必单列政策 KPI |

### 维度 4: 商业化阶段

| 阶段 | 特征 | KPI 推导倾向 |
|---|---|---|
| **Pre-commercial** | 无收入 / 收入主要 grants / 还在 R&D | Cash burn、runway、技术里程碑、customer pipeline (LOI vs firm)、政府合同 wins |
| **Early scale** | 商业化早期，收入 ramp 但 lumpy | Order book、production cadence、unit cost trajectory、客户多元化进度 |
| **Mature** | 行业地位稳定，份额竞争 | 市占率、margin defense、aftermarket、price/cost 传导 |
| **Decline / disruption** | 被替代或衰退中 | FCF return / capital return、cost cutting、是否进入 last man standing |

---

## 推导步骤

### Step 1: 定位 4 个维度

回答：
- 商业模式类型是 [A]
- 周期性等级是 [B]
- 政策依赖等级是 [C]
- 商业化阶段是 [D]

如果是 **hybrid 公司**：拆分到 segment 级别分别定位，每个 segment 走一套推导。

如果 N 家公司在维度上**显著不同**（比如 long X early-scale + long Y mature）：警告用户这不是合理的对比组，建议重新分组。

### Step 2: 填空 5 个问题

基于 4 个维度的位置，针对每个问题选择最 informative 的 KPI：

| 问题 | 默认 KPI 来源 |
|---|---|
| 1. 收入来源 | 维度 1（商业模式）+ 维度 4（商业化阶段） |
| 2. Unit economics | 维度 1 + 维度 2（周期性） |
| 3. Capital cycle | 维度 2 + 维度 4 |
| 4. 风险结构 | 维度 3（政策）+ 维度 4 |
| 5. 商业化进度 | 维度 4（直接） |

### Step 3: 加入行业 idiosyncratic KPI

通用框架推导出的 5-7 个 KPI 之上，加 1-3 个**该行业特有**的 KPI（这些是从行业实际研究中获得的，不可推导）。

例如：
- 商业航天：mission success rate、reusability metrics
- 量子：qubit fidelity、quantum advantage demonstration
- Renewable IPP：capacity factor、PPA pricing
- 医药：FDA approval timeline、临床试验 milestone

如果你不确定行业的 idiosyncratic KPI，**主动告知用户并请教**——这是研究员独有的领域知识，AI 不应假装专家。

### Step 4: 精炼到 5-10 个 KPI

- 太少（< 5）：覆盖不全
- 太多（> 10）：变成噪音，cross-cut 时反而模糊

如果初步推导出 15+ KPI，砍掉冗余的（多个 KPI 测量同一件事的，留最 informative 的一个）。

### Step 5: 告知用户思路 + 请校准

**这一步是元方法论的关键**——不要悄悄推导后就开始写报告。明确告知用户：

```
该行业 (X) 没有现成模板。我根据：
  - 商业模式：[A]
  - 周期性：[B]
  - 政策依赖：[C]
  - 商业化阶段：[D]

推导出关键 KPI：
  1. [KPI 1] — 回答问题 [N]
  2. [KPI 2] — 回答问题 [N]
  ...

你想要：
  (a) 用这套继续做 cross-cut
  (b) 调整 KPI（你来增 / 删 / 替换）
  (c) 我推导有误，重新讨论
  (d) 推导后保存为新模板（references/industries/[name].md）以便复用
```

---

## Worked Example: 商业航天（含 SpaceX、Rocket Lab、Iridium、AST SpaceMobile、Planet、Intuitive Machines 等）

完整展示从 0 到 KPI 的推导过程。

### Step 1: 定位 4 个维度

商业航天**不是单一行业**，是 cluster。先识别 N 家具体属于哪个子细分：

| 子细分 | 上市玩家 | 商业模式 | 周期 | 政策依赖 | 商业化阶段 |
|---|---|---|---|---|---|
| Launch providers | Rocket Lab、SpaceX (private)、Astra (退市)、Relativity (private) | Capital equipment + service hybrid | Pre-cycle | 高（NASA/DoD/ITAR） | Early scale |
| Satellite operators (LEO) | Iridium、AST SpaceMobile、Planet、BlackSky | 部分 capital equipment + 部分 recurring service | Pre-cycle | 高 | Early scale |
| Lunar / Deep Space | Intuitive Machines | Project-based + government services | Pre-cycle | 极高（NASA 主） | Pre-commercial |
| Earth observation / imagery | Planet、BlackSky、Maxar (private) | Recurring service | Pre-cycle | 高（DoD / NGA 主客户） | Early scale |
| Space tourism | Virgin Galactic | One-time / capital equipment | Pre-cycle | 中（FAA） | Pre-commercial |
| Space components | Redwire、Mynaric | Capital equipment | Pre-cycle | 中（ITAR） | Early scale |
| In-space services / manufacturing | Varda (private)、Axiom (private) | TBD | Pre-cycle | 高 | Pre-commercial |

**关键观察**：商业航天 N 家公司在 4 个维度上差异巨大——Iridium（已盈利的 satellite operator）和 Intuitive Machines（pre-commercial lunar lander） 不应直接比较。**先确认 N 家是否在合理的子组**。

### Step 2: 假设我们在做 Launch Providers 子组（Rocket Lab、SpaceX-比较参考、Astra-退市参考）

定位：Capital equipment + service hybrid + Pre-cycle + 政策依赖高 + Early scale

填空 5 个问题：

**问题 1: 收入来源**
- 商业模式（capital equipment + service）+ 商业化阶段（early scale）→ 用 launch 数 × 单 launch 价格 + 后续 service contract
- 推导出 KPI：
  - **Launch cadence (per quarter / per year)**
  - **平均 launch 价格 / Mission**
  - **Government vs Commercial 收入占比**

**问题 2: Unit economics**
- Capital equipment + 早期 → 不指望 mature 的 EBITDA margin。看 unit cost trajectory
- 推导出 KPI：
  - **Cost per kg to orbit** （行业标杆指标，SpaceX Falcon 9 ~$3000/kg、Rocket Lab Electron ~$30000/kg、Starship target $100/kg）
  - **每次发射的 gross margin**（多数早期 launch provider gross margin 仍负或 marginal positive）
  - **Reusability metrics** — Falcon 9：100+ flights per booster；Electron：尝试 reuse 进度（idiosyncratic）

**问题 3: Capital cycle**
- 早期 + 资本密集 → 看 cash burn + 下一代车型 development capex
- 推导出 KPI：
  - **Cash burn / Quarterly**
  - **Cash position + Runway (months)**
  - **Next-gen vehicle development capex**（Rocket Lab Neutron、SpaceX Starship、Relativity Terran R）
  - **R&D 占收入 %**（早期阶段 typically 高于 50%）

**问题 4: 风险结构**
- 政策依赖高 + early scale → 加监管 + 客户集中度
- 推导出 KPI：
  - **Mission success rate**（单次失败成本巨大；Rocket Lab 历史 95%+，Astra 历史 50%）
  - **Top 5 客户集中度**（Iridium 之前 NASA 占 60%）
  - **ITAR / 出口许可监控** — 重大事件触发短期股价波动

**问题 5: 商业化进度**
- Early scale → 看 backlog 和 cadence ramp
- 推导出 KPI：
  - **Backlog (launches signed)** — 决定未来 6-18 月可见性
  - **Backlog / 年化 launches** — 覆盖率
  - **Production capacity (rockets / quarter)** — 是否能 scale

### Step 3: Idiosyncratic KPI（行业特有）

Launch industry 特有：
- **Reusability flight count**（同一硬件复用次数）
- **Payload accuracy** （是否进入正确 orbit）
- **Time from contract to launch**（行业平均 12-24 月，决定 backlog 转化速度）

### Step 4: 精炼到 5-10 个核心 KPI

Launch Providers 推导出的 KPI 列表：
1. Launch cadence (quarterly + annual)
2. Backlog + Backlog / 年化 launches
3. Cost per kg to orbit
4. Cash burn / Runway
5. Government vs Commercial mix
6. Reusability metrics
7. Mission success rate
8. Next-gen vehicle progress
9. R&D 占收入 %（cap intensity proxy）

精简到 9 个，覆盖 5 个问题 + idiosyncratic。每个都和 cross-cut 直接相关。

### Step 5: 告知用户

输出到用户的内容：

```
"商业航天" 暂无现成模板。N 家公司中：
- Rocket Lab、Astra（退市）、SpaceX 是 Launch providers
- Iridium、AST SpaceMobile、Planet 是 Satellite operators
- Intuitive Machines 是 Lunar deep-space services

这三个子组在维度上差异较大，建议**先选定一个子组**做 cross-cut。

假设你要做 Launch providers 子组：
推导出的关键 KPI 如下（覆盖收入 / 经济性 / 资本 / 风险 / 商业化 5 个问题）：
1. ... (列 9 个)

你想：
(a) 用这套继续 (b) 调整 (c) 重选子组 (d) 保存为 references/industries/space-launch.md 以便复用
```

如果用户选 (a)，开始 cross-cut。如果选 (d)，**保存为新模板就是研究的副产品**——下次不用再推导。

### Worked Example 关键 takeaway

- 元方法论**不是查表**，是**推理**
- 每一步**告诉用户思路**，请用户校准
- 推导后选择保存模板是**用户决定**，不是强制
- 即使从零开始，5 步推导能 30 分钟内得到一份合理的 KPI 列表

---

## 当现有模板"接近但不完全匹配"的处理

经常遇到的情况：用户研究的行业**部分**重叠现有模板。处理原则：

### 情况 A: 当前模板的子细分

例：用户在研究 LNG carriers（液化天然气运输船）。
- O&G 模板覆盖 midstream，但 carriers 不在 O&G 模板里
- Shipping / Marine 不在现有模板列表

处理：明确告知"O&G midstream 提供部分参考（合同结构、take-or-pay 等），但 LNG carriers 还需补：船队规模、charter rate、新造船成本、orderbook。这些不在 O&G 模板里，建议现场推导。"

### 情况 B: 跨模板的 hybrid 公司

例：Tesla 同时是 Auto + Energy Storage + AI/Humanoid + Space (option) 多业务。
- 不要试图找一个完美模板
- 拆分 segment，每个 segment 走最匹配的模板（或元方法论）
- Cross-cut 时按 segment 比，不按公司整体比

### 情况 C: 边缘行业

例：水务、垃圾处理、Specialty Chemicals、稀土。
- 现有模板都不直接匹配
- 用元方法论推导
- 推导后选择保存模板

---

## 反模式

写完后必须自检：

- ❌ 找一个最近的模板就硬套（"商业航天 ≈ A&D，用 A&D 模板"）→ 错，KPI 体系不同
- ❌ 推导但不告诉用户思路 → 失去校准机会，KPI 错了用户不知道
- ❌ 推导出 15+ KPI 直接用 → 太多，砍到 5-10
- ❌ 强行用通用 KPI（margin、ROIC、leverage）回答所有问题 → 对 pre-commercial 行业失效
- ❌ N 家公司在维度上差异巨大但不警告用户 → cross-cut 没意义
- ❌ Pre-commercial 行业硬套 EV/EBITDA → 这个 multiple 没意义
- ❌ 维度判断错误（把 secular growth 当 cyclical 等）→ KPI 推导跟着错
- ❌ 推导后用户没确认就开始写 cross-cut → 用户失去 own 这套 KPI 的机会
- ❌ 推导后不问"是否保存为模板" → 错失累积新模板的机会

## 总结

**元方法论的核心**：4 维定位 → 5 问题填空 → 5-10 个 KPI → 告知用户校准。

**不需要穷举行业**——任何新行业都能用这套推导出合理 KPI。

**模板是副产品**——研究中现场构建，用户选择是否保存。3 年后回看，新增的模板可能比现有 9 个还多——但不是负担，是研究累积。

**最重要的承认**：AI 不是所有行业的专家。元方法论给的是**推理框架**，行业 idiosyncratic KPI 仍需研究员的领域知识——主动询问而非假装。
