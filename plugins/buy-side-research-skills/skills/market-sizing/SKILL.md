---
name: market-sizing
description: Bottom-up TAM SAM SOM estimation — structured breakdown with source tier, confidence, and alternative scenarios per segment.
---

# Market Sizing

Turn "how big is this market" into a structured estimate where every row has a source, a tier, a confidence level, and an alternative scenario. The output is not one number — it's a breakdown table plus a visual pyramid. Feeds directly into `scenario-model`, which now acts as the downstream odds memo skill.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **数据管道**：调用 `/financial-data --lite <ticker>` 当需要公司-level baseline 时使用。
- **数据验证**：Claim Fill Pipeline — Tier 0(actuals)→1(WebFetch)→2(Playwright)→3(curl)→4([需查证])。见  §3.2。
- Sub-agent outputs: evidence_cards_only; main agent synthesizes.

## 心法

TAM 估算的真正难题不是"找不到数据"——是"找到的数据到底信不信"。招股书引用 Frost & Sullivan 的数字，Frost 是收费报告、客户是 IPO 公司——天然有向上 bias。券商报告的行业空间章节可能是实习生从 Frost 抄的。公司 IR 说的 "addressable market $10B" 是 PR 数字。

Agent 最容易犯的错：搜到一个数就引用。应该做的是：找至少两个独立源 → 交叉验证 → 如果分歧 >2x，标 `[分歧大]` 并取中间。如果一个源比其他大 5x，标 `[可能虚高, 源: xxx]`。

另一个死穴：不分 TAM/SAM/SOM。TAM 是"全世界所有可能买这个东西的市场"、SAM 是"我们能触达的"、SOM 是"我们实际能拿到的"。混淆了会导致 scenario-model 把 TAM 直接当 SAM 用——高估 upside。

## 触发场景

- "CPO 设备市场有多大"
- "光模块 burn-in test TAM 拆一下"
- "这个细分赛道的 SAM 多少"
- "xxx 行业的 TAM 拆解"

## 方法论

### 两条路径，选对是关键

| 路径 | 做法 | 什么时候用 | 陷阱 |
|---|---|---|---|
| **Bottom-up** | 可触达客户数 × ASP × 渗透率 | 有 granular 数据时（特定设备品类、已知客户群） | ASP 不准会放大误差。客户数容易高估（把"可能买"算成"一定买"） |
| **Top-down** | 行业报告总量 × 目标细分占比 × 调整系数 | 只有宏观数据、细分太新没报告 | 行业报告的细分切法和你需要的不一样。占比是拍出来的 |

**选择规则**：如果一个市场可以用 bottom-up 做（客户数量 <100 且已知），优先 bottom-up。如果客户数是"所有 datacenter"这种没法数的 → top-down 并标 `[top-down, 来源]`。

### 数据源可信度

| 源类型 | 通常偏大还是偏小 | 为什么 | 用法 |
|---|---|---|---|
| 招股书里的第三方报告 | 偏大 20-30% | 第三方报告的客户是 IPO 公司，利益冲突 | 作为上限参考，向下调 20% |
| Gartner/IDC 等中立机构 | 偏保守 | 服务买方，怕被 challenge | 作为基准 |
| 券商报告 | 因券商而异 | 没人 audit 他们的 TAM 数字 | 交叉验证用，不作为主源 |
| 公司 IR | 偏大 | PR 倾向 | 作为"他们自己说的"，标 [公司自估] |
| 学术/政府 | 最可靠但可能过时 | 独立、公开 | 主源 |

### Tier 判断

| Tier | 定义 | 例 | 可进 scenario-model 吗 |
|---|---|---|---|
| **Tier 0** | 机器验证数据 | actuals 里的 segment revenue | auto pass |
| **Tier 1** | 可信第三方报告，citable | Gartner 2025 semiconductor equipment report | auto pass |
| **Tier 2** | Agent 推算，有 clear derivation | "50 HPC DC × $20M × 60% penetration" | 需研究员确认 |
| **Tier 3** | 无源 / 无法复现 | — | 禁止 |

## 输出结构

> **Source contract**：以下所有表格中涉及估值、概率、评分、回报、市场规模数字的列，每行必须带 source anchor（[S#](url) 或 [I#](url)）。
>
> **密度表**：
>
> | Section | 强制标 source | 豁免 |
> |---|---|---|
> | TAM Breakdown 表 | 每行的 Method/Source/Tier 列——Source 列必须可点击 | Segment 名称 |
> | Bottom-up 推算 | 每个 input 参数的数字来源 | 研究员选用的 method |
> | 交叉验证 | 每个替代估算的出处 | — |
>
> **完成 Gate**：写完扫 TAM 表 → 每行 Source 列有 link → Tier 1-2 行做过 WebFetch 验证 → Resources 展开所有 source。

~~~markdown
## TAM Breakdown

| Segment | Method | 2026 | 2028E | Growth | Source | Tier | Confidence |
|---|---|---|---|---|---|---|---|
| CPO burn-in test | Bottom-up | $0.2B | $1.2B | 145% | Frost via 猎奇招股书 | 1 | Medium |
| CPO coupling | Top-down | $0.5B | $2.8B | 136% | Yole report, cross-checked w/券商 | 1 | Medium |
| CPO die bonding | Agent 推算 | $0.3B | $1.5B | 124% | 5 OSAT × $300M capex × 20% CPO alloc | 2 | Low |

## Breakdown Dimensions

按 [segment/region/customer-type/technology] 维度拆解。（选 1-2 个最相关的维度。）

## SAM (addressable by Company)

| Company | Addressable Segment | SAM | Share Rationale | Ev |
|---|---|---|---|
| AEHR | CPO burn-in test | $720M | 当前唯一晶圆级 Burn-in 供应商 |

## Key Assumptions

| 假设 | 值 | 替代情景 | 为什么 | Ev |
|---|---|---|---|
| HPC DC count 2028 | 50 | 30–70 | AMD/NVDA roadmaps suggest 50-60; if ASIC-only, could be 30 |
| CPO penetration | 15% by 2028 | 5–25% | Broadcom Bailly 2027; if delayed, 5% |
| ASP per DC | $20M | $10M–$30M | varies by DC scale; large hyperscaler = $30M |

## Visual

- TAM Pyramid (ASCII): TAM → SAM → SOM 三层
~~~

- Segment Pie: 如果 TAM 按多 segment 拆，可选 pie chart（description only, actual chart via research-viz）

### TAM Pyramid（产出示例）

        ┌──────┐
        │ TAM  │  $1.2B  全世界 CPO burn-in test 设备需求
        │      │
        ┌──────┐
        │ SAM  │  $720M   AEHR 能触达的市场（晶圆级，不是模块级）
        │      │
        ┌──────┐
        │ SOM  │  $360M   AEHR 实际能拿到的（假设 50% of SAM，Teradyne 可能进入）
        └──────┘

## 反模式

- ❌ 只有一个数字没有拆解表
- ❌ 只有一个源没有交叉验证
- ❌ 不分 Bottom-up vs Top-down
- ❌ 不分 TAM/SAM/SOM
- ❌ 拿招股书数字直接用，不调 bias
- ❌ 用 smooth CAGR 掩盖 non-linear adoption curve
- ❌ 不标 Tier——下游 scenario-model 不知道能不能用
- ❌ 关键假设不写替代情景
- ❌ TAM 只切一个维度（至少给 segment + 另一个维度）
- ❌ 没有 as-of 日期

## 篇幅基准

500-1200 字 + 1 TAM 拆解表 + 1 SAM 表 + 1 TAM pyramid (ASCII)。

## Workflow 联动

| 下游 | 场景 |
|---|---|
| `scenario-model` | 优先喂 TAM 给 deep-work odds memo / 场景测算 |
| `candidate-screener` | 给行业排序提供市场规模语境 |
| `industry-landscape` | TAM 可写入行业 index |

## 与相邻 skill 的边界

- 不做场景测算或赔率判断 → `scenario-model`
- 不做行业全景 → `industry-landscape`
- 不做公司收入 forecast → `driver-map`


## Appendix: actuals-resolved.json

完整字段清单 -> `references/actuals-data-catalog.md`。

结构：`meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`。

消费规则：先读 actuals -> source_map 取 [S#]/[I#] 标签（不写 [actuals]）-> ratio 只用 actuals 真实值（不用 forward estimate）。
