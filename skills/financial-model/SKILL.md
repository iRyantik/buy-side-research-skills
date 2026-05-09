---
name: financial-model
description: Use when building or updating buy-side financial models, DCF, comps, reverse DCF, valuation bridge, Excel workbook updates, or turning driver-map output into model assumptions.
---

# Financial Model

把 `driver-map` 里的业务实质和 driver 转成可用的 buy-side model、DCF、comps 和 reverse DCF。**核心价值不是做一个漂亮 Excel 模板**，而是让研究员知道：哪些 driver 真正在控制 revenue、margin、FCF 和估值，哪些假设只是未验证 proxy。

如果输出停留在收入拆分，应该回到 `driver-map`；如果输出直接跳到 price target 但没有 driver-to-valuation bridge，本 skill 就失败了。

## 心法

建模不是录数，也不是把三表填满。买方 model 的价值在于把少数关键 driver 连接到投资判断：收入如何形成、margin 为什么变、FCF 怎么释放、当前估值隐含什么预期。

本 skill 的工作逻辑是 **mechanism when needed + driver-map first + valuation bridge + workbook respect**：
- 新建模型时，若模型依赖设备链条、产能单位、工程约束或行业 know-how，先消费 `mechanism-map`；再消费或产出 `driver-map`，最后搭 operating model、DCF、comps、reverse DCF。
- 更新旧模型时，先尊重原 workbook 的 sheet、公式、格式和手工逻辑，再用 update map 精准定位。
- 做估值时，不允许 DCF/comps 和 driver 脱节；每个关键 valuation assumption 都要能回到 driver 或 source。

## Source 政策

本 skill 不维护独立 source policy。执行时必须遵守 `CLAUDE.md §3`；若局部说明与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。

特别强调：
- **财报 actuals、segment data、guidance、consensus、price、EV、FX、share count、net debt、peer multiples 必须有 source / as-of**。
- **每个 forecast assumption 要标来源类型**：company guidance / consensus / researcher assumption / placeholder。
- **Sell-side model 是观点和结构参考，不是事实 source**；其中数字仍需回到 filing、transcript、IR、数据终端或明确 source。
- **Workbook 内旧数字不是 source**；它只是 prior model state，除非有对应 source note。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **Excel 结构识别不可靠** | 可能误判 actual / forecast boundary、hidden sheet、named ranges、断链公式 | 编辑前必须先给 update map；定位不可靠时只做 review |
| **机制误读风险** | 会把没搞清楚的设备链条、产能单位或工程约束直接写进模型 | 先回到 `mechanism-map`，再进入 `driver-map` |
| **Driver 编造风险** | 会把行业常识写成公司披露事实 | 未披露 driver 回到 `driver-map`，标 `[来源待补]` / proxy |
| **DCF 伪精确** | WACC、terminal growth、terminal value 可能给人虚假精确感 | 必须给 sensitivity，并提示 terminal value 占 EV 比例 |
| **Comps cherry-picking** | 容易选看起来支持结论的 peer | 必须说明 peer set、calendarization、accounting adjustment、premium / discount |
| **Market data stale** | price、EV、FX、consensus、multiples 可能过期 | 所有 market data 标 as-of |
| **Workbook 手工逻辑** | 直接覆盖公式会破坏模型 | 不批量覆盖公式，不迁移成标准模板 |

## 触发场景

### Mode A: Build New Model
- "帮我给 BKR 搭 model，重点拆 IET 收入，再做 DCF/comps"
- "给 X 做 financial model"
- "把 driver-map 转成 operating model"
- "这个设备链条 / 工程机制讲清楚后，帮我转成 model"
- "做一个 revenue-first model"
- "搭一个 DCF / comps valuation model"
- "反推现在股价隐含什么预期"
- "先不要 Excel，给我 model outline"

### Mode B: Update Existing Model
- "根据新财报更新这个已有 Excel model"
- "把新 quarter actuals 放进模型"
- "refresh model from earnings"
- "更新已有 model，但别改格式"
- "先给我 update map，不要直接改"
- "这个 workbook 很乱，帮我找哪些地方要更新"

### 不应触发
- "只想拆收入 driver / bucket 为什么怪" → `driver-map`
- "刚出了财报怎么看" → `earnings-setup`
- "快速看一家公司值不值得研究" → `stock-quickread`
- "写 long / short thesis" → `alpha-thesis`

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **任务类型** | 新建模型 / 更新已有模型 / 只要估值框架 | 有 workbook path 则 Update，否则 Build |
| **Driver-map 状态** | 是否已有 `driver-map` 或需要先产出 | 没有则先产出 driver-map 结构 |
| **Mechanism-map 状态** | 关键设备链条、工艺流程、产能单位、工程约束是否已经清楚 | 不清楚则先消费或触发 `mechanism-map` |
| **Workbook path** | 是否有现成 Excel 文件 | 无 path 时只输出 model note / update map |
| **编辑权限** | 是否允许实际修改 workbook | 默认不编辑，只输出 update map |
| **模型范围** | revenue / operating model / FCF / DCF / comps / reverse DCF | revenue-first + valuation bridge |
| **估值方法** | DCF / comps / reverse DCF / SOTP | DCF + comps，必要时 reverse DCF |
| **时间尺度** | 季度 / 年度 / 3-5 年 forecast | 3-5 年年度 + 必要季度 actuals |
| **Source cutoff** | 使用哪份财报、价格和 market data as-of | 最新可验证 source；不确定标 `[来源待补]` |

如果用户只说"搭 model"，至少确认：公司 / ticker、是否已有 workbook、是否需要实际创建 Excel、是否需要 DCF/comps。

## Mode A: Build New Model

### Step 1: Driver-map first

先读取用户提供的 `driver-map`，或在输出中先产出最小 driver-map。不要直接从 reported segment 跳到 forecast。

| Reported bucket | Business reality | Model driver | Source / as-of | Gap |
|---|---|---|---|---|

若 driver-map 里出现 Low confidence 或怪异 bucket，必须在模型中保留为 sensitivity 或 `[来源待补]`，不能硬塞成 base case。

### Step 2: Operating model

把 driver 转成 line item：

| Driver / assumption | Model line | Forecast handle | Source type | Confidence |
|---|---|---|---|---|
| Backlog conversion | Revenue | backlog × conversion rate | filing / call | Medium |
| Service mix | EBITDA margin | service revenue mix × margin spread | IR / researcher assumption | Low |

最低 operating model 应覆盖：
- Revenue build
- Gross margin / EBITDA margin
- D&A / EBIT（如适用）
- Tax
- Capex
- NWC
- FCF
- Net debt / share count（估值需要时）

### Step 3: Valuation Bridge

DCF/comps 必须从 driver 出发，不允许独立漂浮。

| Driver / assumption | Model line | DCF impact | Comps metric impact | Source / as-of | Confidence |
|---|---|---|---|---|---|

这一表是本 skill 的核心。它回答：哪个 driver 变了，会影响 DCF 哪条线、comps 哪个 metric、市场应该给 premium 还是 discount。

### Step 4: DCF

DCF 至少说明：
- Revenue / margin / FCF bridge
- WACC 或 discount rate 来源 / assumption
- Terminal value 方法：exit multiple 或 terminal growth
- Terminal value 占 EV 比例
- Sensitivity：WACC、terminal growth / exit multiple、key driver

硬规则：
- Terminal value > 80% of EV 必须提示模型高度依赖远期假设。
- WACC / terminal growth 不得给伪精确小数，除非有明确依据。
- FCF conversion 要能回到 operating model，不要直接填一个长期 margin。

### Step 5: Comps

Comps 至少说明：
- Peer set 为什么可比 / 不可比
- Calendarization 是否一致
- Accounting / Non-GAAP adjustment
- 使用 EV/EBITDA、P/E、EV/Sales、FCF yield 等 metric 的理由
- 目标公司应 premium / discount 的原因

硬规则：
- 不能只列 multiples；必须给 "why this peer set" 和 "why premium/discount"。
- 跨市场 peer 涉及币种、会计、流动性、准入差异时，联动 `cross-market-compare`。

### Step 6: Reverse DCF

当用户关心 priced-in 或市场预期时，反推当前价格隐含：
- revenue CAGR
- terminal margin / FCF margin
- FCF conversion
- terminal growth / exit multiple
- 哪个 driver 最不现实

Reverse DCF 结论必须回到 driver-map：市场隐含的是哪个业务 bucket、margin bridge 或 backlog conversion 的假设。

## Mode B: Update Existing Model

### Step 1: Inspect workbook

先识别：
- sheet names
- period columns
- actual / forecast boundary
- formula blocks
- hardcodes
- source notes
- valuation tabs
- hidden sheets / named ranges / checks

### Step 2: Identify update items

把新财报变化拆成：
- reported actuals
- segment / KPI disclosure changes
- guidance changes
- consensus changes
- assumption changes
- price / FX / market data refresh
- one-offs

### Step 3: Build update map before editing

```markdown
## Update Map

| Workbook area | Line item | Old value | New value | Type | Source / as-of | Action |
|---|---:|---:|---:|---|---|---|
| [sheet / row / section] | [metric] | [old] | [new] | actual / guidance / assumption | [source] | update / review / do not touch |
```

Action 定义：
- `update`：定位可靠，可以更新。
- `review`：需要用户确认，公式、period boundary 或口径不确定。
- `do not touch`：看似相关，但不是本轮应该改的区域。

### Step 4: Valuation update map

如果 workbook 有 DCF / comps tab，必须单独说明估值输入更新：

| Valuation area | Input | Old value | New value | Source / as-of | Impact | Action |
|---|---:|---:|---|---|---|---|

### Step 5: Edit only if safe

只有在用户明确允许且定位可靠时才编辑 workbook：
- 不重命名 sheet。
- 不移动 model blocks。
- 不批量覆盖公式。
- 不删除 hidden sheets、named ranges、checks、source notes。
- 不迁移成标准模板。

## 输出结构

### Build New Model

```markdown
## Model Build Outline

**结论先行**
[这个 model 应该由哪些 driver 驱动，估值最敏感的假设是什么]

## Driver Map Used

| Reported bucket | Business reality | Model driver | Source / as-of | Gap |
|---|---|---|---|---|

## Operating Model

| Line item | Driver / assumption | Source type | Confidence | Notes |
|---|---|---|---|---|

## Valuation Bridge

| Driver / assumption | Model line | DCF impact | Comps metric impact | Source / as-of | Confidence |
|---|---|---|---|---|---|

## DCF

[FCF bridge, WACC, terminal value, sensitivity]

## Comps

[peer set, normalized multiples, premium/discount rationale]

## Reverse DCF

[current price implied assumptions]

## Model-Driver Gaps

- [最影响模型质量的缺口]

## 可以问 AI

- [1-2 个下一步问题]
```

### Update Existing Model

```markdown
## Model Update

**结论先行**
[哪些地方要更新，是否足以改变研究判断]

## Workbook Inspection

| Area | Finding | Risk |
|---|---|---|

## Update Map

| Workbook area | Line item | Old value | New value | Type | Source / as-of | Action |
|---|---:|---:|---:|---|---|---|

## Valuation Update Map

| Valuation area | Input | Old value | New value | Source / as-of | Impact | Action |
|---|---:|---:|---|---|---|---|

## Model Integrity Risks

- [公式 / 链接 / hardcode / boundary 风险]

## Research Read-Through

- [是否改变 driver / thesis / next-step]
```

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| 只需要拆 revenue / margin / backlog driver | `driver-map` |
| 模型依赖工程机制、设备链条、产能单位或 know-how | `mechanism-map` → `driver-map` |
| 财报刚出但用户没说 model | `earnings-setup` |
| quickread 后需要把业务落成 driver | `driver-map` → `financial-model` |
| model 暴露 revenue-driver gap | `next-step` |
| model driver 形成 variant view | `alpha-thesis` |
| peer driver 可校准模型 | `peer-deep-dive` / `driver-map` |
| 跨市场 comps 口径复杂 | `cross-market-compare` |
| 模型澄清了机制 / 关键数据 | `research-journal` |

## 反模式自查

### Source 类
- ❌ Workbook 内旧数字没有 source note，却当作事实。
- ❌ Sell-side model assumption 被当成 company disclosure。
- ❌ Consensus / price / FX / EV / multiples 没有 as-of。
- ❌ 未披露 driver 被写成精确数字。

### Logic 类
- ❌ 没有 `driver-map` 就直接做 DCF / comps。
- ❌ 估值结论无法回到 driver assumption。
- ❌ 用历史 CAGR 作为默认 forecast 逻辑。
- ❌ 更新 actuals 后不解释研究含义。
- ❌ Comps 只列 multiple，不解释 peer set 和 premium/discount。
- ❌ Reverse DCF 没说明当前价格隐含哪个 driver。

### Valuation 类
- ❌ Terminal value > 80% of EV 但没有提示。
- ❌ WACC / terminal growth 写得过度精确。
- ❌ 跨市场 peer 未处理币种、会计、流动性或准入差异。
- ❌ FCF margin 直接填长期目标，不接 operating model。

### Workbook 类
- ❌ 没有 update map 就直接改 workbook。
- ❌ 重命名 sheet、移动 block、覆盖公式。
- ❌ 无法定位 actual / forecast boundary 仍硬改。
- ❌ 把已有模型迁移成标准模板。

## 篇幅基准

- Driver-to-model outline：1200-2000 字 + 3-5 张表。
- DCF/comps valuation note：900-1600 字 + valuation bridge / DCF / comps 表。
- Existing workbook update map：700-1400 字，按 workbook 复杂度放大。
- 如果只需要 400-700 字 driver 拆分，应改用 `driver-map`。

## 与相邻 skill 的边界

- `mechanism-map` 拆行业机制、工程原理、设备链条和 know-how；本 skill 只消费这些结论，不在模型里重写科普。
- `driver-map` 拆 business reality 和 model driver；本 skill 把 driver 转成 model、DCF、comps。
- `earnings-setup` 看 print 和 setup；本 skill 把 print 变成 model line updates。
- `stock-quickread` 快速理解公司；本 skill 量化关键假设。
- `alpha-thesis` 写投资论点；本 skill提供可量化假设和 valuation read-through。
- `cross-market-compare` 处理跨市场估值差；本 skill 在 comps 需要跨市场 normalization 时调用它。
