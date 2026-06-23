---
name: driver-map
description: Decompose revenue margin backlog price volume mix and segment drivers before modeling.
---

# Driver Map

Decompose revenue margin backlog price volume mix and segment drivers before modeling.

## Research Runtime Capsule

- Hook-enforced legality, source boundary, structure floor, and table rendering rules live in workspace hooks and are not restated here.
- Shared runtime/source baseline lives in `references/policy/research-policy-baseline.md` and the installed workspace `CLAUDE.md`.
- Use this skill for business reality translation and model driver mapping; unresolved facts stay as gap, hypothesis, or follow-up.
- **Actuals-only**: margin breakdowns, price/volume/mix ratios, and all quantitative driver ratios use actuals-resolved.json disclosed data. No forward estimate as ratio input.
- Sub-agent outputs must be evidence_cards_only; main agent synthesizes, cross-checks URLs, and resolves source conflicts.

把公司披露口径翻译成真实业务和可建模 driver。**核心价值不是写一个收入拆分表**，而是防止研究员和 AI 把会计 segment、管理层 narrative、卖方分类或概念股标签误当成经济实质。

如果输出只是在复述公司 segment 名称，或者把未披露的 driver 编成事实，本 skill 就失败了。

## 心法

很多投研错误不是发生在 DCF、comps 或 thesis 结论，而是发生在更前面：你以为你知道这家公司靠什么增长，但其实只是接受了公司给的 bucket 名称。`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。

举个例子：公司披露叫 "Industrial Solutions"，实际是燃气轮机设备+长期服务捆在一起。坏的分析写 "Industrial Solutions 收入 $3.2bn"——那是复读财报。好的分析拆出来：设备销售 $1.3bn 毛利率 22%、服务 $1.9bn 毛利率 45%，服务装机利用率是核心 driver。这才是 `driver-map` 的价值。

**最重要的纪律**：不披露的 driver 不能编；只能写成 `[来源待补]`、`[需查证]` 或 researcher assumption。没有 source 的 driver map 是假精确。

## Financial-Data 联动

弹性 KPI 先查 `references/kpi-drivers/` 按 business model 路由。从 `actuals-resolved.json` 取数据，按 revenue_split 状态分类处理：

1. revenue_split 存在 → 按 source_type 归类：`official-xbrl-dimension` = provider-structured，`filing-table-extracted` = provider-table-review → 转 model bucket
2. revenue_split 缺失 → 读 `full-filing.md`，LLM 抽 disclosed split → 标 `llm-extracted-review`
3. 原文无披露 → 标 `not-disclosed`，不编造

`review_required: true` 的 row 需 LLM 解释 axis/member 映射，不能直接当最终口径。不覆盖 `financial-data` 的 completeness。

## 触发场景

- "帮我拆一下这家公司 revenue driver"
- "这家公司收入怎么拆"
- "这个 segment / bucket 到底是什么业务"
- "某业务 bucket 为什么这么拆"
- "这个 reported bucket 对应什么业务实质"
- "这家公司靠什么增长"
- "为什么收入涨了但 margin 没涨"
- "backlog / orders 怎么进收入"
- "price / volume / mix 哪个在驱动"
- "这个业务口径是不是有点怪"

## 输入澄清要求

| 维度 | 含义 | 默认假设 |
|---|---|---|
| **对象** | 公司 / segment / 产品线 / 行业 bucket | 用户给 ticker 时按公司；给业务名时按 segment |
| **研究目的** | model / thesis / peer compare / earnings / journal | 默认服务 model 和 thesis |
| **时间口径** | 最新年报、最新季度、过去 3-5 年趋势 | 最新可验证披露 + 必要历史对比 |
| **driver 范围** | revenue / margin / backlog / price-volume-mix / installed base | revenue-first，必要时扩到 margin |
| **source cutoff** | 使用哪份 filing / call / IR deck | 最新可验证 source；不确定标 `[来源待补]` |
| **保存需求** | 写入 company driver-map cache + topic artifact | 默认保存；外显 `driver-map.md`，机器 JSON 写 `internal/driver-map.json` |

如果用户只说"拆 driver"，至少确认公司 / 业务范围；如果用户明确给出业务 bucket，则直接开始拆，不要把问题扩大成完整公司研究。

## 工作流

### Step 0: 识别独立增长逻辑线

在拆任何分部之前，先回答：**这家公司到底靠什么增长？** 不靠公司给的 bucket 名称——靠独立的、可验证的增长逻辑。

**画出驱动总图**（ASCII tree），每条逻辑线一句话：

```
公司 = 逻辑线 A × 逻辑线 B × ... + 无关项
```

逻辑线分类：
- **结构性逻辑**（如稀土管制受益、排放升级）——同因多线并发
- **独立增长逻辑**（如市场份额提升、品类扩张）——各有独立 driver
- **无关项**（如建筑陶瓷、电子浆料）——不参与估值

每条逻辑线标注类型（`rare-earth` / `organic` / `non-core`）。如果多个逻辑线共享同一个宏观催化剂，在树里标注因果链。

### Step 1: Reported Bucket → Business Reality

先把公司披露的 bucket 翻译成真实业务，不要直接接受命名。

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
| [segment] | [实际卖什么 / 做什么] | [客户或应用] | [S1](url) | [缺口] |

| [segment / product] | [实际卖什么 / 做什么] | [客户或应用] | [S1](./_cache/sources/company-annual-report.md) | [缺口] |

> 每个核心 segment 配产品/设备图：下载到当前 topic 的 `_cache/images/<slug>-<product>.<ext>`，`<ext>` 使用脚本返回的 `extension`。
>
> **下载方法**：读 `_scripts/download-product-image.js` → 替换 `{{TARGET_URL}}` → 调用当前 session 的 Playwright MCP `browser_run_code_unsafe` → Windows 用 PowerShell 解码、macOS 用 `python3` 解码写文件。图片来源优先级：① 公司 Media Kit → ② 产品页 hero → ③ web search → ④ 行业代表图 → ⑤ `[缺图]`。详见 `stock-quickread` SKILL.md。

遇到 `GTE / GTS / Industrial Products / Industrial Solutions / CTS` 这类拆分时，要直接触发 Senior Analyst Radar：这可能不是普通并列 segment，而是 gas turbine 系统价值链、产品本体、配套设备、service、controls 或 end-market 维度的混合拆分。

**逻辑线→分部收入归集**：完成 Step 0 逻辑线识别和 Step 1 Bucket 翻译后，必须把分部收入按逻辑线重新分配。每个分部拆成其承载的逻辑线 + 残差（不属于任何逻辑线的剩余收入）：

| 分部 | FY0A 收入 | 逻辑线分解 | 残差 |
|---|---|---|---|
| Electronic | 693 | R1(450) + G4(28) | 215（浆料，不参与估值） |

逻辑线 FY0A 收入 = 分部收入 × Split%（Agent 预设，Analyst 在 Excel 蓝格里调）。残差 = 分部收入 − Σ逻辑线收入（自动算，只存残差 GM）。

### Step 2: Logic Line → Model Driver（逻辑线优先）

**每条逻辑线独立建模**，输入三个参数：

| 参数 | 含义 | 值示例 |
|---|---|---|
| **Base Revenue (FY0A)** | 最新完整财年的逻辑线收入 | 450（¥M） |
| **YoY Growth** (Bull/Base/Bear × 5 年) | 三档情景假设 | Bull: 60%…, Base: 51%…, Bear: 35%… |
| **GM** (FY0A + 5 年投影) | 毛利率轨迹 | 40% → 42% → 45%… |
| **利润层级** | NI > EBITDA > EBIT > GP | GP（仅分部披露 GM） |

**Revenue 不是输入**——是 `= Prior × (1 + Active YoY)` 滚动算出来的。FY0A 是锚，YoY 是 driver，Revenue 是输出。

每逻辑线的驱动传导树（ASCII）：

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|
| Equipment | units / MW / MTPA / orders | price / mix | orders, backlog, shipments | High / Medium / Low |
| Services | installed base | utilization / attach rate | service revenue, fleet hours | High / Medium / Low |

常用 driver 速查：

| 类型 | 指标 | 适用场景 |
|---|---|---|
| Volume | unit shipment、capacity、MW、MTPA、rig count、installed base | 制造/能源/设备 |
| Price | ASP、contract escalation、commodity pass-through | 定价权分析 |
| Mix | equipment vs services、newbuild vs aftermarket、project vs recurring | 利润率结构 |
| Backlog/orders | order intake、book-to-bill、backlog conversion | 项目制/长周期 |
| Utilization | fleet utilization、factory load、service hours、capacity factor | 服务/运维 |
| Installed base | service attach rate、replacement cycle、parts intensity | aftermarket |
| End-market proxy | LNG FID、data center power demand、aerospace build rate | 需求前瞻 |

### Step 3: Driver Quality

每个 driver 必须评级，但评级不能凭感觉：

| Rating | Hard standard |
|---|---|
| **High** | 公司直接披露 KPI / bucket revenue / backlog / margin，且定义清楚、可跟踪 |
| **Medium** | 公司部分披露，需用 peer / industry proxy 补足，但方向可验证 |
| **Low** | 主要靠推断、卖方拆分或主题关联，必须标 `[来源待补]` / `[需查证]` |

### Step 4: Disclosure vs Inference / Proxy Strategy

每个关键 driver claim 都必须标清证据状态。合理推断可以写，但不能写成公司事实；proxy 可以用，但必须说明 proxy 风险和模型处理方式。

Evidence status 只能用：
- `company disclosed`：公司直接披露该 driver / KPI / bucket。
- `company implied`：公司语言或披露结构暗示该 driver，但没有完整 KPI。
- `peer proxy`：用同业或行业 proxy 近似。
- `researcher assumption`：研究员假设，必须可被后续验证。
- `unknown`：还不知道，不能进入 base-case model。

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|
| [driver 判断] | company disclosed / company implied / peer proxy / researcher assumption / unknown | [proxy or none] | [proxy 可能误导之处] | base case / sensitivity / scenario only / exclude |

Hard rule：`Low` confidence 或 `unknown` driver 不能进入单一 base case；只能进入 sensitivity、scenario 或标 `[来源待补]`，直到有更强 source。

### Step 7: 产出 driver-model.json

从 MD 的表格提取结构化数据，写入同目录同前缀的 JSON 文件（`driver-map-<ticker>.json`）。JSON 是 Excel 脚本的输入——只含 Agent 初始预设，Analyst 在 Excel 里调。

自动取数（不需 Agent 填）：
- `meta` (ticker, market, base_fy)：从 actuals-resolved.json 映射
- `actuals` (FY-2, FY-1 P&L 行)：从 actuals-resolved.json 取
- `segments[].fy0`：从年报/WebSearch 取分部披露

Agent 预设（从 MD 研究结论提取）：
- `segments[].logic_lines[].split`：FY0A 逻辑线收入占比
- `segments[].residual.gm`：残差毛利率
- `logic_lines[].yoy`：Bull/Base/Bear 三档 YoY
- `logic_lines[].gm.proj`：未来 5 年 GM
- `logic_lines[].sotp_pe`：估值倍数
- `logic_lines[].type`：`rare-earth` / `organic`
- `global.opex_rate` / `global.tax_rate`

JSON 文件与 driver-map.md 同目录同日期前缀（只换后缀 `.json`）。

### Step 8: 生成 Excel 模型

```bash
python .scripts/shared/build-logic-model.py <path/to/driver-map.json>
```

脚本从 JSON 读取配置，yfinance 拉实时市场数据，生成单 sheet 公式联动 Excel：
- Section 1: 原始披露分部（FY25A hardcode，FY26E+ = 逻辑线 reaggregate）
- Section 2: 逻辑线假设（YoY Bull/Base/Bear，Revenue=Prior×(1+YoY)，GM/GP）
- P&L: 含残差聚合行
- SOTP: 双轨——逻辑线 PE + 分部 PE（加权自动算）
- Scenario Summary: Bull/Base/Bear 三套独立公式
- Market Data: yfinance 实时 mcap/price/shares/PE/52W

Excel 格式规范：无网格线/无边框/全 Calibri/假设格黄底蓝字/冻结 D2/年份只 Row 1/B1 下拉切换场景。Analyst 改蓝格即全表自动联动。

## 输出结构

```markdown
## Driver Map

**结论先行**
[一句话说明这家公司最应该按什么 driver 理解，最大披露缺口在哪里]

## 0. 驱动总图

```
公司 = 逻辑线 A × 逻辑线 B × ... + 无关项
         │
    分类标注（rare-earth / organic / non-core）
```
[ASCII tree 显示每条逻辑线 + 因果链]

### 原始披露分部

| 分部 | FY0A Rev | GM | 映射到逻辑线 |

### 逻辑线 → 分部收入归集

| 逻辑线 | 类型 | 隶属分部 | FY0A Rev | YoY | GM | PE |

## 1. Reported Bucket → Business Reality

[现有格式保留]

## 2. Logic Line Growth Estimates

每条逻辑线独立表：

| | FY0A | FY+1E | FY+2E | FY+3E | FY+4E | FY+5E |
|---|---|---|---|---|---|---|
| YoY Growth | — | +51% | +54% | +29% | +26% | +21% |
| Revenue (¥M) | 450 | 680 | 1,050 | ... | ... | ... |
| GM | 40.0% | 42.0% | 45.0% | ... | ... | ... |
| GP (¥M) | 180 | 286 | 473 | ... | ... | ... |

**Profit tier**: GP（NI > EBITDA > EBIT > GP，取可得最高层级）

## 3. 催化剂时间线

| 时间 | 逻辑线 | 事件 | 可验证性 |

## 4-6. Driver Quality / Disclosure / Weird Buckets

[现有格式保留]

## 7. Implications
- 怪异点：[披露 / bucket / KPI 哪里不自然]
- 可能说明：[1-2 个解释]

## 6. Implications

- [这个 driver map 会如何改变 model / thesis / peer compare]

```



## Artifact / 保存策略

写入行业 topic：
    industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md

路径不明 → agent 按 policy baseline §11 自动创建。

## Growth Quality（200 字）

基于上述 driver 拆解，回答三个增长质量问题：

| 维度 | 判断 | 证据 |
|---|---|---|
| Organic vs M&A | 过去 3Y 增长中 ~X% organic | M&A 贡献 ~Y%（acquisition disclosure 推算） |
| Leading Indicator | [Backlog YoY / Orders YoY / Capacity ramp] | [具体数字] |
| Margin Trajectory | [扩张/稳定/压缩] | EBIT margin FY N-2 X% → FY N Y% |

## 反模式自查

- ❌ 只复述 segment 名称，没有翻译 business reality——看到 Solutions / Systems / Industrial 不追问。
- ❌ Reported bucket、revenue、margin、backlog 没有 source / as-of；用卖方拆分替代公司披露未标 assumption。
- ❌ 把 peer proxy 或 researcher assumption 写成 company disclosed fact。
- ❌ Low confidence driver 直接进入 base case，没有进入 sensitivity / scenario。
- ❌ 只写 revenue driver，不问 margin driver 是否不同；用历史 CAGR 代替 driver。
- ❌ 把 theme association 写成 direct revenue driver。
- ❌ sub-agent evidence card 未经主 agent 抽查 URL 和口径统一直接当 final driver tree。
- ❌ 用户只要 driver-map 却输出 DCF / comps；要搭 model 却不 handoff 到 modeling skills。
- ❌ driver confidence Low 被后续 thesis 当核心事实；清楚认知未进 `research-journal`。
- ❌ 只做分部不做逻辑线——把会计口径当成经济实质。
- ❌ Revenue 输入绝对值而非 YoY——改了 FY26E 不影响 FY27E+。
- ❌ 脚本含公司特定逻辑——应全部在 JSON 里，脚本纯通用。

## Appendix A: driver-model.json Schema

Agent 在 Step 7 产出此文件，与 driver-map.md 同目录同日期前缀。所有"初始预设"值研究员在 Excel 蓝格里调。

```json
{
  "meta": {"ticker": "300285.SZ", "company": "Sinocera", "market": "cn",
           "base_fy": 2025, "proj_years": 5, "sotp_offset": 2},
  "units": {"rev": "M"},
  "actuals": {
    "fy-2": {"rev": 3859, "gp": 1492, "op": 755, "tax": 93, "ni": 605},
    "fy-1": {"rev": 4047, "gp": 1606, "op": 775, "tax": 93, "ni": 610}
  },
  "segments": [{
    "name": "Electronic Materials",
    "fy0": {"rev": 693, "cost": 454, "gp": 239, "gm": 0.345},
    "logic_lines": [{"name": "R1 MLCC Powder", "split": 0.65}],
    "residual": {"gm": 0.25}
  }],
  "logic_lines": [{
    "name": "R1 MLCC Powder", "type": "rare-earth", "profit_tier": "gp",
    "yoy": {"bull": [0.60,...], "base": [0.51,...], "bear": [0.35,...]},
    "gm": {"fy0": 0.40, "proj": [0.42,0.45,0.46,0.47,0.48]},
    "sotp_pe": 40,
    "drivers": [
      {"label": "Volume", "fy0": {"value": 7000, "unit": "tons"}}
    ]
  }],
  "global": {"opex_rate": [0.22,...], "tax_rate": 0.15}
}
```

字段说明：
- `meta.market`: cn/us/jp/kr/tw — 用于自动单位检测（jp/kr/tw 或 mcap>1e6M → B 单位）
- `segments[].logic_lines[].split`: FY0A 收入占比，残差=1−Σsplit（自动算）
- `logic_lines[].profit_tier`: gp/ebit/ebitda/ni — SOTP 取最高可得层级
- `logic_lines[].type`: rare-earth / organic / non-core — 用于 Excel 配色
- `logic_lines[].drivers`: 可选——每个 driver 一行纯展示，不参与公式
- `global.opex_rate`: 数组长度 = 实际年数 + 投影年数
- 单位统一用"百万本币"（M），脚本自动转 B

## Appendix B: Excel 结构

`build-logic-model.py` 从 JSON 生成单 sheet 公式联动 Excel：

| Section | 行 | 内容 | 输入/输出 |
|---|---|---|---|
| 1 | 5- | 原始披露分部（Rev/Cost/GP/GM/Split%/残差%） | FY25A hardcode, FY26E+=公式 |
| 2 | 50- | 逻辑线假设（YoY Bull/Base/Bear→Active→Revenue→GM→GP） | 蓝格输入 |
| — | — | Global Opex/Tax | 蓝格输入 |
| 3 | — | P&L + 残差聚合行 | 公式 |
| 4 | — | SOTP Logic（GP→NI share→PE→Mkt Cap→SUM TOTAL） | PE 蓝格输入 |
| 5 | — | SOTP Segments（分部 PE 加权自动算） | PE 蓝格输入 |
| 6 | — | Market Data（yfinance mcap/price/shares/PE/52W）+ Implied ratios | 展示 |
| 7 | — | Scenario Summary（三套独立公式，不依赖 B1 下拉） | 公式 |

格式规范：无网格线、无边框、全 Calibri、假设格黄底蓝字(#FFFFCC/#0000CC)、年份右对齐/标签左对齐、冻结 D2、B1 下拉切换场景。PE 格式 `0.0x`，比率 `0.0%`，货币 `¥#,##0.00`。

## 篇幅基准

- 标准：900-1600 字 + 3-4 张表。低于 700 字常漏 proxy strategy；超过 1800 字应收窄到核心 segment。


## Appendix: actuals-resolved.json

完整字段清单 -> `references/actuals-data-catalog.md`。

结构：`meta` / `market_data` (15 field) / `statements.income_statement` (13 field) / `statements.balance_sheet` (10 field) / `statements.cash_flow` (4 field) / `segments` / `supplementary` / `source_map`。

消费规则：先读 actuals -> source_map 取 [S#]/[I#] 标签（不写 [actuals]）-> ratio 只用 actuals 真实值（不用 forward estimate）。
