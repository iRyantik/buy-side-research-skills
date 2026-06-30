---
name: driver-map
description: Decompose revenue margin backlog price volume mix and segment drivers before modeling.
---

# Driver Map

Decompose revenue margin backlog price volume mix and segment drivers before modeling.

## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§2.1（资料收集）§2.2（Source 纪律）§2.5（图片下载链）§4（产出合约）§5（保存合约）

**自动 Hook 防御：** `pre_write_gate`（source/tables/mermaid/image/cell-style CHECK 17）`source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action. All runtime rules in that file + hooks — capsule only states what is unique to this skill.

## 心法

很多投研错误不是发生在 DCF、comps 或 thesis 结论，而是发生在更前面：你以为你知道这家公司靠什么增长，但其实只是接受了公司给的 bucket 名称。`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。

举个例子：公司披露叫 "Industrial Solutions"，实际是燃气轮机设备+长期服务捆在一起。坏的分析写 "Industrial Solutions 收入 $3.2bn"——那是复读财报。好的分析拆出来：设备销售 $1.3bn 毛利率 22%、服务 $1.9bn 毛利率 45%，服务装机利用率是核心 driver。这才是 `driver-map` 的价值。

**最重要的纪律**：不披露的 driver 不能编；只能写成 `[来源待补]`、`[需查证]` 或 researcher assumption。没有 source 的 driver map 是假精确。

## Financial-Data 联动

弹性 KPI 先查 workspace `.references/kpi-drivers/` 按 business model 路由。从 `actuals-resolved.json` 取数据，按 revenue_split 状态分类处理：

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

### Step 1: Reported Bucket → Business Reality

先把公司披露的 bucket 翻译成真实业务，不要直接接受命名。

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
| [segment] | [实际卖什么 / 做什么] | [客户或应用] | [S1](url) | [缺口] |

| [segment / product] | [实际卖什么 / 做什么] | [客户或应用] | [S1](./_cache/sources/company-annual-report.md) | [缺口] |

> 每个核心 segment 配产品/设备图：下载到公司 `_cache/images/`。
>
> **下载方法**：`python .scripts/shared/download-image.py <url> --output <slug> --company <ticker>` — HTTP Tier 1 → Playwright Tier 2 `--base64` → `[缺图]` if all tiers fail。
> artifact 引用：`![描述](../../../../_cache/images/<slug>.png)`

遇到 `GTE / GTS / Industrial Products / Industrial Solutions / CTS` 这类拆分时，要直接触发 Senior Analyst Radar：这可能不是普通并列 segment，而是 gas turbine 系统价值链、产品本体、配套设备、service、controls 或 end-market 维度的混合拆分。

### Step 2: Business Reality → Model Driver

把每个业务 bucket 映射到可观察 driver。

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

### Step 5: Driver Cascade Tree（驱动传导树）

**每个 business bucket 必须配一棵 ASCII 树**，从宏观 driver → 量/价/产能/政策 → 收入贡献。树的目标不是重复表格数据——是**显示因果链**。读者看完树应该能回答：这条业务线增长来自量还是价？哪个分支最脆弱？周期因素占多少？

格式：

```
业务线收入 ¥XX亿 (FY20XX, +XX%, OPM XX%)
│
├─ 子业务/产品线 A ~XX%  ← 一句话定位
│   ├─ 量：[具体数字 + source]
│   │     → 传导路径（宏观→中观→公司）
│   ├─ 价：[ASP 区间 + 方向]
│   │     → 传导路径（换代/mix/定价权）
│   ├─ 产能/并购：[扩产 timeline 或收购贡献]
│   └─ 结构性风险：[如 CPO design-out——方向标注 🟢/🔴/⚪]
│
├─ 子业务/产品线 B ~XX%
│   └─ ...
│
└─ 注意事项：[周期因素占比、一次性因素、最脆的假设]
```

**强制规则**：
- 每个叶子节点必须有 source 或标 `[推算]`
- 量/价必须分叉——禁止"量价齐升"糊弄过去
- 结构性风险（CPO、技术替代、监管变化）必须在树里标注方向
- 如果某子业务的量/价驱动和部门整体不同——必须分叉说明

### Step 6: Management Tone Tracker（管理层措辞追踪 — 按需）

**如果覆盖了 ≥2 个季度的 IR 材料**（tanshin、transcript、earnings call summary），必须追踪管理层定性措辞的方向变化。这不是锦上添花——管理层措辞的方向性 escalation/de-escalation 往往领先实际数据 1-2 个季度。

格式：

```
Q1 (日期): "[原话]"  → 情绪判断（谨慎/坚挺/乐观）
Q2 (日期): "[原话]"  → 情绪变化方向
  ↓
FY Full (日期): "[原话]" → 最终判断
  ↓
指引：FY+1 +XX%

解读：[1-2 句——措辞变化是否对应实际数据变化？是领先指标还是滞后确认？]
```

**强制规则**：
- 每个引语必须有 source（tanshin 页数或 transcript timestamp）
- 情绪判断不能凭空——必须是措辞的明确变化（堅調→良好、回復→拡大）
- 如果措辞和数据方向背离——必须在"解读"里指出矛盾

### Step 7: Growth Decomposition（增速拆解）

把 headline 增速拆成结构件，回答"增长质量"问题。

```
整体收入增速 +XX%
│
├─ 量贡献 +Xpp     （出货量/产能增长——可跟踪）
├─ 价/mix 贡献 +Xpp （ASP 上行/高利润品类占比提升——结构性还是周期性？）
├─ 并购贡献 +Xpp   （M&A inorganic——必须可追溯到 acquisition disclosure）
├─ 周期贡献 +Xpp   （去库存恢复/一次性因素——不可持续）
└─ 汇率贡献 +Xpp   （如有显著敞口——标汇率假设）
```

**强制规则**：
- 每项必须有数字或标 `[推算]`
- 周期贡献必须说明"从什么恢复到什么"（如：光モニター去库存→恢复正常订货）
- 并购贡献必须引用 acquisition date + first consolidation quarter

## 输出结构

```markdown
## Driver Map

**结论先行**
[一句话说明这家公司 / 业务最应该按什么 driver 理解，最大披露缺口在哪里]

## 1. Reported Bucket → Business Reality [→ Bridge: valuation_snapshot] [→ Bridge: valuation_snapshot]

| Reported bucket | Business reality | End-market / customer | Ev | Gap |
|---|---|---|---|---|
> 每个核心 segment 配产品/设备图：下载到公司 `_cache/images/`。
>
> **下载方法**：`python .scripts/shared/download-image.py <url> --output <slug> --company <ticker>` — HTTP Tier 1 → Playwright Tier 2 `--base64` → `[缺图]` if all tiers fail。
> artifact 引用：`![描述](../../../../_cache/images/<slug>.png)`

## 2. Business Reality → Model Driver

**本节由两部分组成：驱动传导树（必填）+ 驱动表（选填——当树不足以容纳所有细节时补表）。**

### 2.x [业务线] —— 驱动传导树

```
[业务线] 收入 XX (FY20XX, +XX%, OPM XX%)
│
├─ 子业务 A ~XX%  ← 一句话定位
│   ├─ 场景：[装在哪/谁在用/干什么用——≤20 字]
│   ├─ 量：[具体数字 + source]
│   │     → 传导路径（宏观→中观→公司）
│   ├─ 价：[ASP 区间 + 方向]
│   │     → 传导路径（换代/mix/定价权）
│   ├─ 产能/并购：[扩产 timeline 或收购贡献]
│   └─ 结构性风险：[方向标注 🟢/🔴/⚪]
│
├─ 子业务 B ~XX%
│   ├─ 场景：[...]
│   └─ ...
│
└─ 注意事项：[周期因素占比、一次性因素、最脆的假设]
```

**强制规则**：
- 每个产品级节点必须有 `场景：`——读者不需要光学知识就能理解这东西用在哪
- 每个叶子节点必须有 source 或标 `[推算]`
- 量/价必须分叉——禁止"量价齐升"
- 结构性风险必须标注方向
- 树覆盖不到的数据细节 → 补表

### 2.y [选填——驱动表]

| Business bucket | Primary driver | Secondary driver | Observable KPI | Confidence |
|---|---|---|---|---|

## 3. Driver Quality

| Driver | Rating | Why | Ev | What would improve confidence |
|---|---|---|---|---|

## 4. Disclosure vs Inference / Proxy Strategy

| Driver claim | Evidence status | Proxy to use | Risk of proxy | Model treatment |
|---|---|---|---|---|

## 5. Management Tone Tracker（如有 ≥2 季度 IR 材料）

```
Q1 (日期): "[原话]"  → 情绪
Q2 (日期): "[原话]"  → 变化方向
  ↓
FY Full: "[原话]"
  ↓
指引：FY+1 +XX%

解读：[措辞变化是否对应数据？领先还是滞后？]
```

## 6. Weird Buckets / Senior Analyst Radar

**这里值得深挖**
- 怪异点：[披露 / bucket / KPI 哪里不自然]
- 可能说明：[1-2 个解释]

## 7. Growth Decomposition & Synthesis（增速拆解与合成）

```
整体收入增速 +XX%
│
├─ 量贡献 +Xpp     （出货量/产能增长）
├─ 价/mix 贡献 +Xpp （ASP 上行/品类 mix）
├─ 并购贡献 +Xpp   （M&A inorganic）
├─ 周期贡献 +Xpp   （去库存恢复等一次性因素）
└─ 汇率贡献 +Xpp   （如有显著敞口）
```

```
FY+1 增速路径：
├─ 业务线 A 继续增长 → XX-XX 增量
├─ 业务线 B 正常化   → XX-XX 增量
└─ 汇率敏感性：XX 前提 → ±XX
```

## 8. Implications

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
- ❌ 只有表格没有驱动传导树——读者看不到因果链、只能自己从表里推导量价关系
- ❌ 量/价写在一起（"量价齐升"）——必须分叉说明各自贡献和不确定性
- ❌ 增速拆解不做——headline +31% 混在一起，分不清结构性增长 vs 周期性反弹 vs 并购贡献
- ❌ 有多季度 IR 材料但不追踪管理层措辞变化——漏掉领先指标（措辞 escalation 往往领先数据 1-2 季度）
- ❌ agent 手动调 q_history → rebuild → check Δ → 循环——build() 已内置 driver 分配自动保证 Revenue 收敛，无需人工调参
- ❌ 看到 GP/OP Check 列有残余差就继续调参数试图消除——这是实际 Q 利润率 vs 年度模型假设的结构性差异，Blend 已收窄，残余差是信息不是 bug

## 篇幅基准

- 标准：80-140 行 + 3-4 张表 + 每业务线 1 棵驱动树。低于 60 行常漏 proxy strategy 或驱动树；超过 160 行应收窄到核心 segment 或把细节移入附录。

## Model Pipeline（5 GATEs）

在研究 Step 1-7（业务翻译→driver 映射→增速拆解）完成后，进入建模阶段。

`build()` 内部自动完成：Reconcile（全 A 财年）→ Blend（实际 Q 利润率混入年度假设）→ Q Driver Distribution（季节权重分配）→ Render。Agent 无需干预 Q 配平——Revenue 数学保证收敛。

### ⛔ GATE 0: Actuals 强制补全

**Read 本 skill 的 references 前：先确保 actuals 完整。**

1. 读 existing `actuals-resolved.json`
2. 缺口检测：
   - `opex` (fy-2/fy-1/fy0) 缺失？→ `/financial-data --lite --periods FY{bfyr-2}-FY{bfyr}Q{latest}`
   - `da` 缺失？→ 同上
   - segment rev/cost/gp/gm 缺失？→ 爬年报/WebSearch
   - actuals 超过 180 天未更新？→ 强制刷新
3. 分部数据必须全——找不到标 `not-disclosed`
4. 补全后 Write actuals-resolved.json

**⛔ STOP — 等用户确认 actuals 数字，再继续。**

### ⛔ GATE 1: JSON 行列视图 + 估值方法

**逐个 Read，不准凭记忆：**
`references/json-schema.md` `references/modules.md` `references/calibration.md` `references/pitfalls.md` `references/valuation.md`

**输出**（不是 JSON blob——按逻辑线逐条展开的行列表）：

```
§1 Segments FY{bfyr}A
| Segment | Rev | Cost | GP | GM | OP? | NI? | Logic Lines |

§2 Logic Lines — 每条单独一个表
| R1 MLCC Powder | FY25 | FY26 | FY27 | FY28 | FY29 | FY30 |
|---|---|---|---|---|---|---|
| Volume | 7,000 | 8,000 | ... |
| Nameplate Capacity | 10,000 | 10,000 | ... |
| AI Share% | 5% | 15.6% | ... |
| AI ASP Base | 26 | 30 | ... |
| ... (所有 tier 的 Share + ASP BBE) |
| Revenue (验算) | 450M | ... |
| GM | 40% | 45% | ... |

估值方法
| Logic Line | Method | Multiple | 理由 |
```

- vol_asp 线：手动验算 FY25A Revenue，gap<1%
- 估值方法按决策树自选（`references/valuation.md`）
- JSON 自查：跑 `references/pitfalls.md` checklist

**⛔ STOP — 等用户调数 + 确认估值方法，再继续。**

### ⛔ GATE 1.5: 公司脚本副本（Company-Specific Script Copy）

**每个公司必须有自己的 build 脚本副本**，放在 `<ticker>/.cache/scripts/`。不改 workspace 通用脚本。

```bash
# 首次生成前，一次性 copy：
TICKER_DIR="industry/<industry>/companies/<ticker>"
mkdir -p "$TICKER_DIR/.cache/scripts/modules"
cp .scripts/driver-map/build-logic-model.py "$TICKER_DIR/.cache/scripts/"
cp .scripts/driver-map/audit_style.py "$TICKER_DIR/.cache/scripts/"
cp .scripts/driver-map/modules/*.py "$TICKER_DIR/.cache/scripts/modules/"
```

**强制规则**：
- 每个公司独立副本，改自己的不影响其他公司
- 通用脚本（`.scripts/driver-map/`）只在新公司首次 copy 时使用
- 已生成模型的公司后续 rebuild 用公司自己的脚本副本
- **禁止**多个公司共用同一份脚本——改了量纲/参数会互相污染

### Blend 步骤（build 内部自动执行）

对每个有 M∈{1,2,3} 的投影年，实际 Q 的利润率（GM、OM）混入年度模型假设：

```
GM_blended   = M/4 × GM_actual_Q   + (1−M/4) × GM_model
OM_blended   = M/4 × OM_actual_Q   + (1−M/4) × OM_model
```

- M/4 = 实际 Q 的权重（M=1→25%，M=3→75%）
- GM_actual_Q = Σ(S1实际Q_GP) / Σ(S1实际Q_Rev)（从 seg_quarters 取）
- OM_actual_Q = Σ(S1实际Q_GP − S1实际Q_OP) / Σ(S1实际Q_Rev)
- 写回 `gm['proj'][idx]` 和 `opex_rates[idx]`
- Revenue 不动——只 blend 利润率
- 效果：GP/OP Δ 收窄 65-80%，但不强制为 0（残余差 = 季节性信息）

### ⛔ GATE 2: 生成 Excel

```bash
python <ticker>/.cache/scripts/build-logic-model.py <json> [-o output.xlsx]
python <ticker>/.cache/scripts/audit_style.py <output.xlsx>
```

build 自动执行：Reconcile → Blend → Q Driver Distribution → Render。Q 配平无需 agent 手动干预。生成 → audit → 0 errors 方可交付。参数见 `references/cli.md`。生成后用户打开 Excel 审。

**量纲规则**：

- **div**：存储单位 → 显示单位 的换算。`sc(v) = v / div`，只用于 A() 和 I() 格
- **unit_scale**：Vol×ASP 原始乘积 → 显示财务单位，**已含 div**。公式 = `Vol×ASP/unit_scale`
- CF() 公式不走 sc()，unit_scale 保证公式产出 = 显示单位

| 市场 | 存储 | 显示 | div | unit_scale 示例 |
|---|---|---|---|---|
| US/CN/EU/HK | M | M | 1 | 1 |
| JP/KR/TW | M | bn | 1000 | 1000 |

驱动分配内部（ann、remaining_vol、remaining_asp）全部用原始单位，不碰 div 和 unit_scale。

### ⛔ GATE 2.5: Q→FY Check

Q 列生成后，X 列 Check = `(Annual−ΣQ)/Annual` %。

**收敛保证**：
- **Revenue Δ→0%**：build 内 driver 分配（季节权重或二分搜索 r）数学保证 ΣQ_Rev = Annual_Rev
- **Volume Δ→0%**：权重 Σw=1 保证 ΣQ_Vol = Vol_year
- **GP/OP Δ** 是结构性残余：实际 Q1 的 S1 利润率 ≠ 年度模型假设（Blend 步骤已收窄但不强制为 0）
- **D&A Δ**：实际 Q1 D&A 来自披露 ≠ 模型季度均分

**不再需要** agent 手动调 q_history 循环 rebuild。Revenue 自动收敛。GP/OP/D&A 残余差是信息，供分析师判断季度异常。详见 `references/calibration.md` §Quarterly Calibration。

## Schema + Reference

完整 schema → `references/json-schema.md`
Module 契约 → `references/modules.md`
视觉层级 → `references/visual-hierarchy.md`


