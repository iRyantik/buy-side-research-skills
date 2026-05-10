# Edge Radar

> 用途：沉淀 senior analyst 式“哪里值得深挖”的识别信号和 AI 问法。这里只写可迁移的观察维度，不做状态追踪、不写具体研究日志。

## business-substance-misread

**识别信号**
- 披露名称像并列业务，但真实经济实质可能是同一 value chain 的不同环节。
- 市场或 AI 用公司自己的 label 直接理解业务，没有追问产品、客户、订单、margin driver。
- 同一个 segment 里可能混了设备、服务、控制系统、配套件或项目收入。

**可以这样问 AI**
- 这个披露 bucket 分别对应哪些产品 / 服务 / 收入 driver？
- 这些 bucket 是按 value chain、产品、客户、项目阶段，还是组织架构拆分？

## disclosure-anomaly

**识别信号**
- Segment / KPI / revenue bucket 名称看起来不自然。
- 公司把重要业务放进 `Solutions`, `Other`, `Industrial`, `Systems` 等泛化 label。
- 披露口径让 model driver 变模糊。

**可以这样问 AI**
- 公司在 10-K、IR deck、earnings call 中如何定义这些 bucket？
- 这些口径过去是否改过，是否影响历史可比性？

## model-driver-gap

**识别信号**
- 增长无法拆成 price / volume / mix / FX / M&A / backlog conversion。
- 模型里最重要的行其实没有可靠 driver。
- 管理层给了增长 narrative，但没有对应到可建模变量。

**可以这样问 AI**
- 这家公司最关键的 revenue / margin driver 是什么，哪些是披露数据、哪些只能估？
- 当前可用 source 能否把增长拆成 price、volume、mix、FX、M&A 或 backlog conversion？

## narrative-data-mismatch

**识别信号**
- 管理层讲需求强，但 orders / backlog / margin 没配合。
- 公司强调结构性增长，但数据看起来更像周期反弹或一次性项目。
- 财报 headline 和细分数据方向相反。

**可以这样问 AI**
- 管理层 narrative 和实际 orders、backlog、margin、cash flow 有哪些不一致？
- 哪个数据点最能验证 narrative 是结构性还是短期扰动？

## margin-revenue-mismatch

**识别信号**
- 收入增长但 margin 不扩张，或收入平但 margin 大幅波动。
- Mix、pricing、utilization、cost pass-through 没解释清楚。
- 公司把 margin 变化归因于 vague mix / timing。

**可以这样问 AI**
- margin 变化更可能来自 price、mix、utilization、cost、项目 timing 还是一次性因素？
- 哪个 segment / product mix 最能解释收入和 margin 的背离？

## market-misread

**识别信号**
- 市场把公司按热门主题定价，但 verified exposure 不清楚。
- Sell-side / 新闻叙事过度简化真实业务机制。
- 多数人讨论 TAM，但没人讨论 monetization path。

**可以这样问 AI**
- 市场当前最可能用什么框架理解这家公司，这个框架哪里可能错？
- 主题 exposure 到收入 / margin / cash flow 的传导链是否有 source 支撑？

## peer-mismatch

**识别信号**
- 公司被放进一个 peer group，但业务 driver、margin model、capital intensity 或 cyclicality 不同。
- 估值差被简单归因于贵 / 便宜，没有拆 peer quality。
- Cross-market 或跨行业比较没有 normalize business mix。

**可以这样问 AI**
- 这家公司真正应该和谁比，按 revenue driver、margin structure、capital intensity 分别看有哪些 peer？
- 当前市场 peer group 是否会导致估值或 thesis 错读？

## source-conflict

**识别信号**
- 10-K、IR deck、earnings call、新闻、卖方口径互相不一致。
- 同一指标在不同 source 中定义不同。
- 管理层后续澄清和原始披露不一致。

**可以这样问 AI**
- 这些 source 对同一指标 / 业务定义是否一致，不一致在哪里？
- 哪个 source 是最高优先级，哪些只能作线索？

## know-how-gap

**识别信号**
- 出现关键设备、工艺、工程术语，但没有解释它如何影响 economics。
- 术语听起来像科普，但其实决定 revenue driver、成本、产能或竞争壁垒。
- AI 或报告直接跳过机制，只给结论。

**可以这样问 AI**
- 这个术语 / 设备 / 工艺在产业链中具体做什么，谁付钱，收入如何形成？
- 这个 know-how 会影响成本、margin、capacity、交付周期还是竞争壁垒？
