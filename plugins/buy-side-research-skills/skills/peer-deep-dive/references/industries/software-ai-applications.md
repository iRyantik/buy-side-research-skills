# Software / AI Applications - 行业 KPI 模板

## 行业边界

本模板覆盖：
- **Horizontal SaaS**：Salesforce、ServiceNow、Workday、HubSpot、Atlassian、Asana、Monday、Box
- **Vertical SaaS**：Veeva (Life Sciences)、Procore (Construction)、Toast (Restaurant)、Tyler Tech (Government)、Olo
- **AI-Native Applications**：Klarna AI、Glean、Harvey、Sierra (private 多)、Hippocratic AI；上市的：Palantir (AIP)、C3.ai
- **AI Infrastructure (B2B)**：MongoDB (Atlas Vector)、Snowflake (Cortex)、Databricks (private)、Confluent
- **DevTools**：GitHub (MSFT)、GitLab、JFrog、Datadog、New Relic、Sentry、HashiCorp
- **Cybersecurity**：CrowdStrike、Palo Alto、Zscaler、Cloudflare、Fortinet、SentinelOne、Wiz (private)、Okta
- **Foundation Model 公司（部分上市）**：暂无纯 play 上市（Anthropic、OpenAI 都是 private）；adjacent：Microsoft / Google / Meta / Amazon

不在本模板：
- 传统 IT services（Accenture、TCS、Infosys）→ 服务公司，不同框架
- Hardware-heavy AI 公司（NVIDIA、AMD、TSMC）→ 半导体框架
- Telecom / Comm 软件 → 自行扩展

## 当前 regime 的典型变量（市场在 trade 什么）

**当前主流叙事**：
- **AI revenue 占比和增速**：公司 AI 收入是真实增长还是 marketing？
- **Compute spend / COGS 压力**：AI 应用层的 GM 因 inference cost 而压缩
- **AGI / 模型能力跃升对 SaaS 的颠覆**：哪些 SaaS 的 moat 真实，哪些会被 AI 直接替代
- **Seat-based vs Consumption-based 定价转型**：Salesforce、Veeva 等都在向 consumption / outcomes 模型迁移
- **Rule of 40 重新成为门槛**：高增长但烧钱不再被市场买账
- **Enterprise AI deployment**：Pilot → Production 的转化率
- **Cybersecurity 整合**：Vendor consolidation thesis（Palo Alto、Cloudflare、Wiz）
- **Snowflake / Databricks / MongoDB 数据分层格局**

## 核心 KPI（按子板块）

### 通用 SaaS / Software KPI（所有子板块都看）

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| ARR (Annual Recurring Revenue) | 年化经常性收入 | 当前规模 + YoY 增长 |
| ARR YoY 增长 | 增速 | 大公司 > 20% 优秀，小公司 > 40% |
| Net New ARR | 单季度新增 ARR | 衡量增长动能（绝对数 + YoY 趋势） |
| Net Retention Rate (NRR / NDR) | 老客户净留存 | > 120% 优秀，> 110% 健康，< 100% 流失警告 |
| Gross Retention Rate (GRR) | 老客户毛留存 | 衡量 churn，> 90% 健康 |
| Customer Count + Cohort Mix | 客户数 + 大客户占比 | $100K+ ARR、$1M+ ARR 客户增长是健康信号 |
| RPO (Remaining Performance Obligations) | 已签未确认收入 | 类似 backlog，cRPO（current）更敏感 |

### 增长效率指标

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Magic Number / Sales Efficiency | (Q-on-Q 新 ARR × 4) / 上季度 S&M 支出 | > 1.0 高效，< 0.7 低效 |
| CAC Payback (months) | 客户获取成本回收期 | < 18 月健康，> 24 月警惕 |
| LTV / CAC | 客户生命周期价值 / 获客成本 | > 3 健康，> 5 优秀 |
| S&M 占收入 % | 销售营销占比 | 高增长公司 typical 40-50%，成熟期 25-35% |
| R&D 占收入 % | 研发占比 | typical 20-30% |

### 盈利能力 / 现金流

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Gross Margin | 毛利率 | 纯 SaaS 75-85%；AI 应用 50-70%（受 inference cost 拖累）；AI infra 40-60% |
| Free Cash Flow Margin | FCF 利润率 | 成熟 SaaS 30%+，growth 公司 10-20% |
| Rule of 40 | (收入增速 + FCF margin) | > 40 健康；< 30 警惕 |
| Stock-Based Comp 占收入 % | SBC 强度 | typical 15-25%，> 30% 是稀释警告 |

### AI-Specific KPI（关键，区分纯 AI 应用 vs 传统 SaaS）

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| AI Revenue 占总收入 % | AI 业务规模 | 关键是定义——什么算"AI revenue"各家口径不同 |
| AI Revenue YoY | AI 业务增速 | 与总公司增速的 spread 反映 AI mix shift 程度 |
| Compute / Inference Cost / Revenue | 推理成本占收入比 | AI 应用层关键 margin driver；> 30% 是 margin 压力大 |
| Tokens / API Calls 增长 | 使用量增长 | 区分 "growing usage" 和 "growing customers" |
| Inference Cost 单位下降率 | $/M tokens 下降 | 决定 long-term margin trajectory |
| 是否依赖 third-party foundation models | OpenAI / Anthropic 客户依赖度 | 高依赖意味着 margin 可能被上游挤压 |
| 自研 model vs 调用 API | 战略选择 | 自研 = capex 重 + tech moat；API = 灵活但 margin 受限 |
| Enterprise AI deployment：Pilot vs Production 比例 | 商业化进度 | 大量 pilot 但少 production 是警告 |

### Cybersecurity 特有

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| Module Adoption (modules per customer) | 单客户模块数 | Cross-sell 健康度 |
| Platform consolidation thesis 进度 | 客户从单 vendor 迁移到 multi-vendor 的反向 | 一线（Palo Alto、CrowdStrike、Cloudflare）受益 |
| ARR by Module | 各产品线 ARR | 新模块（XDR、SASE、Cloud Sec）增速 |
| 零信任 / Cloud Security 专业度 | 产品定位 | 主流 vs niche |

### Vertical SaaS 特有

| KPI | 含义 | 警戒阈值 / 解读 |
|---|---|---|
| 行业渗透率 | 目标行业的客户覆盖 | Veeva 在 Life Sciences pharma top 20 几乎 100% 覆盖 |
| ACV (Annual Contract Value) | 单客户年合同价值 | Vertical 通常 ACV 高于 horizontal |
| 行业逆周期性 | 受垂直行业景气影响 | Toast 受 restaurant industry 影响；Procore 受 construction |
| Payments / Fintech 嵌入 | 嵌入支付收入 | Toast、Olo 等 take rate 是关键 |

## 行业特定实证驱动因素（股价跟着什么动）

**所有 SaaS**：
- 季度 ARR / Net New ARR / NRR 数据
- Guidance 调整（cRPO 是 forward indicator）
- 客户公告（hyperscaler / 大客户）
- 利率（高 multiple SaaS 受利率冲击大）

**AI Applications**：
- AI revenue 数字披露（每季度市场 obsessed）
- Customer case studies 具体披露（如 CrowdStrike Charlotte AI、Palantir AIP）
- Foundation model 价格变化（影响 COGS）
- Enterprise AI surveys（KeyBanc、Morgan Stanley、Goldman 季度调查）

**Cybersecurity**：
- 重大网络事件（推动行业整体 demand）
- Vendor consolidation 公告（如 Palo Alto Bundle、CrowdStrike Falcon 平台）

## 典型估值锚点

| 子板块 | 主要倍数 | 典型区间 |
|---|---|---|
| 高增长 SaaS（>30% growth） | EV/Revenue (NTM)、EV/Forward ARR | 8-15x（ZIRP 时代曾 20-40x） |
| 成熟 SaaS（10-20% growth） | EV/Revenue、Rule of 40 调整 | 5-10x |
| 盈利 SaaS / Mature | P/E、FCF yield、EV/EBITDA | P/E 25-40x，FCF yield 3-5% |
| AI-native（Palantir、C3.ai） | EV/Revenue（高溢价）、option value | 15-30x（市场 AI 溢价显著） |
| Cybersecurity 一线 | EV/Revenue、Rule of 40 | 10-18x |
| Vertical SaaS（成熟） | EV/EBITDA、P/E | EV/EBITDA 25-40x（粘性溢价） |

## Cross-cut 注意事项（这个行业最容易翻车的地方）

### "AI Revenue" 定义不一致

- 各公司 AI revenue 口径完全不同：
  - Microsoft: Copilot + Azure OpenAI services
  - Salesforce: Einstein + Agentforce
  - ServiceNow: Now Assist add-on
  - Palantir: AIP-related contracts
- **横向比较时必须 normalize 或明确区分**——不要把不同口径的 "AI revenue %" 直接比较
- 当前阶段：AI revenue 多数包含 "embedded AI 功能"，不一定是 incremental 收入

### Compute / Inference COGS 处理

- 一些 AI 应用公司把 compute 计入 R&D（不冲击 GM），一些计入 COGS（直接压 GM）
- Anthropic / OpenAI 的 API cost：客户的 COGS，对 OpenAI/Anthropic 是 revenue
- 横向比较 GM 时必须看 COGS 定义；不一致时不能直接比较

### Seat-based vs Consumption-based 定价

- Seat-based（Salesforce、Workday）：稳定但增长有 cap
- Consumption-based（Snowflake、Databricks、MongoDB Atlas）：增速更快但更 lumpy，受客户 cost optimization 影响（2023 都遭重创）
- 不同模式的 ARR / NRR 可比性差——consumption-based 公司的 NRR 看起来更高但是 commodity-driven

### 大客户依赖度

- 部分 SaaS 公司单一大客户占 10%+（特别是政府客户：Palantir、Booz Allen 等）
- 客户流失 / 降级 = 单季度 -10% 收入
- 横向比较时关注 customer concentration 风险溢价

### NRR > 100% 的"自然"水平不同

- 高 ARPU SaaS（Snowflake、Datadog）NRR 130%+ typical（usage-based 自然增长）
- Low ARPU horizontal SaaS（HubSpot、Asana）NRR 105-115% typical
- 不能 cross-comparison 直接说"X 公司 NRR 110%，Y 公司 130%，所以 Y 更好"

### Cybersecurity 的"事件 demand spike"

- 重大事件（SolarWinds、Log4j、CrowdStrike outage）后行业 demand 短期 surge
- 但这种 spike 会过度推升 next-quarter expectations
- 看是否是 "structural demand" vs "event-driven demand"

### 利率敏感度差异

- 高 multiple SaaS（EV/Revenue > 10x）对利率高度敏感
- 盈利 SaaS（FCF yield > 3%）相对抗压
- 横向比较时要 risk-adjust，不能纯看 growth rate

### Foundation Model 上游风险

- 调用 OpenAI / Anthropic API 的 AI 应用：随时面临 model price change、capability shift、上游集成下游
- 自建 model 的公司（如 Anthropic、OpenAI）：capex 重，但有独立 moat
- 不同战略下的 AI 应用公司不可直接 cross-compare

### Enterprise AI 部署的"pilot → production gap"

- 当前 enterprise AI 部署：80%+ 还在 pilot 阶段，production 转化率约 20-30%
- 公司公告的 "AI customer count" 多数是 pilot
- ARR 实际贡献远低于 pilot count 暗示
- 横向比较 AI customer 数量时必须问：什么阶段的客户？

### 季节性

- 大型 enterprise SaaS Q4 是最大季度（fiscal year-end purchasing）
- Cybersecurity Q4 也是高峰（年度预算 utilization）
- 单季度 trend 推断要 normalize

### Stock-Based Comp 稀释

- 软件公司 SBC 历史上很高（>20% 收入 typical）
- "Adjusted EBITDA"、"Adjusted EPS" 完全 ignore SBC
- 横向比较时建议看 GAAP earnings、Diluted Share Count YoY 增长
- Diluted Share Count YoY 增长 > 5% = 显著稀释警告
