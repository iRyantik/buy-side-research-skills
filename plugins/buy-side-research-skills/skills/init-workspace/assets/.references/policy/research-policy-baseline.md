# 研究规则维护基线

> 本文件是 research skill authoring / review / batch sync 的维护基线，不是 runtime authority。
> skill 运行时不能假设会自动读取本文件；真正的 runtime truth 在被调用的 `SKILL.md`。
> 本文件现在同时承担 shared runtime/source baseline：research skill 不再本地复制长版 source policy、No Orphan Truth Claim 或 Sub-Agent Evidence Protocol。

## 0. 角色与同步顺序

- 本文件负责：完整 research policy baseline、authoring 对照底稿、capsule 批量同步基线。
- 本文件不负责：单独决定 runtime 行为。
- 公共 research 规则变更时，固定顺序是：
  1. 改本文件
  2. 同步所有受影响的 active research `SKILL.md`
  3. 如影响 workspace 高层原则，再改 `CLAUDE.md.template`

## 0.1 UTF-8 文本纪律

中文或多语言文本资产统一使用 **UTF-8 无 BOM**。

- `.md` / `.yaml` / `.json` 默认按 UTF-8 无 BOM 维护。
- 修改中文文件时必须显式使用 UTF-8 写回。
- 批量脚本改写文本时必须指定 UTF-8，避免 mojibake。
- 如果出现中文异常，先区分是控制台显示问题还是文件内容真的被写坏，再继续修改。

## 1. 研究上下文

- **身份语境**：Buy-side equity researcher，偏 hedge fund / long-short 研究语境。
- **主要覆盖**：industrials, aerospace and defense, advanced manufacturing, oil & gas, renewable, nuclear, emerging tech themes。
- **v3 核心目标**：不是维护交易状态，而是像 senior analyst 一样发现高价值研究问题，并把真正想清楚的认知增量沉淀成 topic journal / Boss Brief。

## 2. 全局输出规则

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。
- 非中文 / 英文公司披露项使用“源语言锚点 + 中文解释”的最小必要原则：首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。
- 全中文即可：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording。管理层原话只有在措辞本身影响判断时保留短原文；否则用中文概述并贴 source。
- 所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。
- 数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。

## 2.5 Hooks-First Runtime Law

- binary / machine-checkable runtime law 优先进 workspace hooks，不再分散复制进单个 research skill。
- skill-level `Research Runtime Capsule` 只保留极短提醒和 non-binary delta。
- 一旦某条 source / boundary / structure rule 进入 hook，对应 `SKILL.md` 的同类 prose 必须删除。

## 3. Source 政策

每一条事实声明、数字、引语必须有 source link 或明确 source 描述。研究员判断本身不需要 source，但判断依据的事实必须有 source。

必须有 source：
- 财务数字、估值、市场数据、价格、as-of 数据。
- KPI / 运营数据：产量、客户数、ARR、库存、orders、backlog 等。
- 行业数据：市占率、价格、产能、需求量、TAM。
- 管理层引语、专家访谈、监管表态、第三方判断。
- 历史事件和时间点。

### 3.0 Claim-Level Source Contract（shared baseline, not skill-local boilerplate）

- `truth-like claim` = 任何可验证或可反驳的事实、数字、引语、业务关系、市场数据、行业事实、历史事件、披露口径变化。
- 每个 `truth-like claim` 必须紧跟 inline clickable short source anchor；可见文本保持短码，但短码本身必须带真实 link，例如 `[S1](./source.md)`、`[L1](./_cache/source.md)`、`[P1](https://...)` 或 `[I1](https://...)`，不要在可见文本里塞日期或长 URL。
- 正文示例：`FY25 revenue grew 18%, while segment EBIT margin expanded 120 bps. [S1](./source.md)`
- 每篇 research artifact 文末必须有且只有一个 `## Resources`，重复使用同一个 clickable short anchor，并展开 source type、title/provider、as-of / filed date、page / table / URL location、fallback reason（如适用）。正文和表格里的短码必须可直接点击；不要在表格下方默认展开完整 source metadata。
- 多个 source 写成 `[S1](./source.md) [I1](https://...)`，不要写成 `[S1][I1]`；只有同一篇里同一个 source code 出现多版本冲突时，才升级成 `[S1a](...)` / `[S1b](...)`。
- `judgment` / `synthesis` / `概率判断` 不强制逐句挂 source，但其依据的事实 claim 必须已经 source-backed。
- 没有 source 的 claim 只能写成 `[需查证]` / `[来源待补]` / `not disclosed` / `working hypothesis`，不得伪装成事实。

### 3.1 Source hierarchy and controlled fallback

- Use two source tracks rather than one flat hierarchy.
- Disclosure-fact track: `topic-local evidence cache > primary public > trusted third-party > web`. Use this for company facts, segment / KPI disclosure, customer / project / supply-chain relationship facts, management quotes, and regulatory / filing facts.
- Market-snapshot track: `topic-local evidence cache / financial-data > trusted third-party > web`. Use this for `market_quote`, `valuation_snapshot`, `price_action`, `kline_snapshot`, `consensus`, `financial_snapshot`, `fx_snapshot`, `adr_ah_premium`, and clearly market-data-like liquidity / market-context fields.
- `financial-data` is the highest-value reusable structured cache inside `topic-local evidence cache`. It takes priority over trusted third-party providers for market / snapshot fields, but it does not replace `primary public` when wording, segment definition, or disclosure truth must be checked.
- Optional provider bridge rule: when a skill explicitly invokes `trusted-market-bridge`, A-share / Hong Kong / US market-snapshot fields may use Longbridge as the default trusted third-party layer before generic internet fallback. Supported bridge domains now include market data, price action, valuation, FX, ADR/AH premium, consensus, financial snapshots, and high-level `market_screen` signals. This does not upgrade Longbridge into `primary public source` or company-truth authority.
- `topic-local evidence cache` means this research workspace's topic `_cache/`, company `financial-data`, source-tracked ingest markdown, and saved internal data packs; it is different from home-market / local-language source priority.
- Within the same quality tier, prefer `home-market / local-language source`: local-language news / event sources for the issuer, main listing venue, regulator, or operating country; primary listing / trading-market data for price, valuation, liquidity, borrow, FX, and cross-market fields.
- Do not maintain market-specific provider whitelists in global or skill rules. If a global, English, or non-home-market fallback is used because the local-language / home-market source is unavailable or weaker, the final `## Resources` list must state the fallback reason.

- 简写顺序不是单行总顺序，而是双轨：披露事实轨 `topic-local evidence cache > primary public > trusted third-party > web`；市场快照轨 `topic-local evidence cache / financial-data > trusted third-party > web`。
- `topic-local evidence cache`：当前 topic `_cache/`、company `financial-data`、ingest 后 source-tracked markdown、已保存的内部数据包；不包含 research artifacts，它们只能作为导航、routing 和待复核线索。
- `primary public source`：filing、IR、交易所、监管、政府、协会、公司官网等可公开验证原始 source。
- `trusted third-party`：Longbridge 等 provider 聚合层；当前统一入口优先是 `trusted-market-bridge`，但它只服务 market / snapshot 字段，不上升为 company truth。
- `internet source`：公开网页上的 market/provider 数据、财经站点、交易页面、公开新闻页、公开数据库页面。
- `internet source` 只能在 **本地缺失** 且 **字段本来就属于 market-snapshot track** 时自动 fallback。
- If `trusted-market-bridge` is used, preserve provider-specific anchors such as `[LBG1](https://longbridge.example.com/quote/NVDA.US)` and expand provider, symbol, market, as-of, and fallback reason in the final `## Resources` list.
- `internet source` 不能冒充 company-disclosed fact。业务事实、分部利润、公司披露 KPI、客户 / 项目 / 供应链关系、管理层原话、未披露 driver 缺口，缺 source 时继续写 `[需查证]` / `[来源待补]` / `not disclosed`。
- fallback 成功后可以进入主表 / 主文，但必须显式标 `internet source`、provider、as-of、URL / source location。
- `internet source` 与 local / primary public source 冲突时，必须保留冲突说明，不得静默覆盖。
- 即使允许 fallback，如果公开网页也拿不到可靠 source，继续 honest degrade：`[需查证]` / `[来源待补]` / `not disclosed`。

Source 质量：
- 一手原始：SEC filings、交易所公告、公司 IR、earnings call、监管 / 政府数据。
- 二手权威：transcripts、Bloomberg / FactSet / CapIQ / Visible Alpha、行业研究机构、专家访谈平台。
- 三手解读：Reuters、Bloomberg News、FT、WSJ、日经、卖方报告、行业媒体。
- 仅作线索：社媒、论坛、聊天记录、传闻截图、个人博客、券商转述。

能用一手就不用二手。多个 source 冲突时必须标注冲突，不要挑一个顺手的用。

### 3.1 Source 优先级（所有 Research Skill 共享）

```
1. actuals-resolved.json   本地缓存，机器采集，最高置信
   → 22核心科目 + Market Cap/PE/EV/EBITDA/Beta/52w
   → skill里标 [actuals]，不挂 [S#]/[I#]

2. [S#] 公司披露            IR PDF、年报、AGM、earnings transcript
   → actuals 没有的字段 → WebFetch/Playwright 验证 → [S1-S9]

3. [I#] 第三方              行业报告、新闻媒体、Yahoo Finance、卖方报告
   → actuals 和公司披露都覆盖不到 → WebFetch/Playwright 验证 → [I1-I20]

同一 claim 只引用最高优先级。Revenue已在actuals→不标[S1]。Q1订单不在actuals→[S1]。市占率→[I1]。
```

### 3.2 RAG Source 验证管线（所有 Research Skill 共享）

**纪律**: 禁止用 WebSearch AI 摘要数字直接写 claim。每个外部 claim 必须来自原文页面。

**二层数据层**: 0-Actuals（本地，0s）→ 1-External（WebFetch/Playwright/curl，需验证）

**页面抓取 Fallback 链**:

```
Tier 1  WebFetch(url)                           — 静态页面
   ↓ fail
Tier 2  Playwright MCP browser_navigate + snapshot  — JS渲染/auth墙
   ↓ fail
Tier 3  bash: curl -sL url | python 提取正文       — 原始HTML
   ↓ fail
Tier 4  标 [需查证] + Resources 记录尝试过的URL    — honest degradation
```

**平台兼容**:
| 工具 | Claude Code | Codex |
|---|---|---|
| WebFetch | `WebFetch` tool | 无 — skip Tier 1 |
| Playwright MCP | `mcp__playwright__browser_*` | MCP server |
| curl | `Bash` | `run_shell_command` |

**页级 density 规则**: 打开一页 → 提取全部可用 claims。一整页 10 个数字全拿，不回头再拉。

**跨 artifact 证据复用**: 同一 ticker 的 evidence ledger 为永久账本。后续 skill 先读 ledger → 已有 verified claims 直接复用 → 只 fetch 新增。

**跨 ticker claim**: 涉及两个 ticker 的对比 claim（如 "BESI 市占 70% vs ASMPT TCB 15%"）——归属到其中**数据较全的 ticker**的 ledger。两个 ticker 分别在各自 ledger 里有对应的对比数据时，claim 同时写入双方 ledger 的 provenances 字段。

**Source 编号**: [S1-S9] 公司披露, [I1-I20] 第三方, URL 页面级, 同一 URL 复用同一编号。

### 3.3 Source Completion Gate（所有 Research Skill 共享）

写完 artifact 后必须通过以下检查才能视为完成：

1. **Anchor scan**：`python .scripts/evidence_ledger.py scan <artifact> -t <TICKER>` 扫描所有 [S#]/[I#] anchor。
2. **Lint gate**：`python .scripts/evidence_ledger.py lint <artifact> -t <TICKER>` 检查裸 anchor、死链、Resources 对齐。
3. **Density self-check**：各 skill 自行定义其高密度段（见 skill-specific density table），写完逐段扫：
   - 每段 factual claim 句尾是否有 anchor？
   - 连续 3 句以上事实 claim 中间无 source → 密度不够。
4. **待查 cap**：`[待查]` 数量超过 10 个 → 警告。超过 20 个 → artifact 标 `coverage <80%`。
5. **Resources completeness**：文末 `## Resources` 必须列出正文中出现的所有 [S#]/[I#] 标签，含 source type、title/provider、as-of、URL。

linter 报错 → 修到 pass 才交付。

## 4. 反幻觉硬规则

- 绝对不能编造 URL、页码、引语、数字、人名、日期。
- 不确定 URL 是否存在时，写 `[link 待补]`，不要造链接。
- sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`；关键 link 必须人工抽查 URL 和 claim 是否匹配。

### 4.1 No Orphan Truth Claim self-check

- 输出前检查是否有数字、业务事实、客户关系、segment claim、行业事实、历史事件没有 source anchor。
- 检查是否有 `market expects` / `management said` / `company disclosed` / `consensus implies` 等表述但没有 anchor。
- 检查是否只有文末 `## Resources`、但正文或表格内多个 claim 无法逐一对应到 anchor。
- 发现 orphan claim 时，必须补 source anchor、降级为 `[需查证]` / `[来源待补]` / `not disclosed` / `working hypothesis`，或删除该 claim。

## 4.5 紧凑证据显示

- 表格优先用 `Ev` 或 `证据` 短列承载 inline clickable short source anchor 和例外状态。默认格式是 `[S1](./_cache/sources/company-annual-report.md)`；如果不是干净 source-backed 值，再追加状态：`[S1](./_cache/sources/company-annual-report.md):REV`。
- 状态码只用于例外：`REV` = 需复核，`GAP` = 来源缺口，`ND` = 未披露，`EST` = 估算 / 假设，`CON` = 来源冲突。干净值不写 `OK`。
- 每篇 artifact 文末用 `## Resources` 保持可追溯性，例如：`- [S1](./annual-report.md) = local source | company annual report | filed 2026-03-18 | p.42`。如果全表 as-of 相同，只在 `## Resources` 写一次；只有行级差异进入 `Ev`。
- 启用 internet market data fallback 的 section，`Ev` / `证据` 要直接体现可点击来源层级：`[L1](./_cache/market/quote-pack.md)` = topic-local evidence cache，`[P1](https://www.hkexnews.hk/example)` = primary public source，`[I1](https://example.com/quote)` = internet source。
- `[I1](https://example.com/quote)` registry 必须展开 provider、as-of、`internet source` 标签和 fallback reason，例如：`- [I1](https://example.com/quote) = internet source | provider quote page | as-of 2026-05-21 | fallback reason: home-market field unavailable`；正文短码与 `## Resources` 必须双写同 target。
- 某 section 首次使用 internet fallback 时，正文加一句：`以下标记为 internet source 的字段为本地 cache 缺失后的公开网页 fallback，不等同于公司披露原文。`

## 5. Sub-Agent Evidence Protocol（shared baseline, not skill-local boilerplate）

- 默认执行 Parallel Evidence Pass 的 research skill 现在只保留：`peer-deep-dive`、`candidate-screener`、`pair-trade`、`driver-map`。这些 shortlist skill 默认启动 sub-agent / delegate worker 并行查 source；以下 8 个 company-level skill 的 financial-data 获取**默认委托 subagent 执行**（不等待用户显式授权）：`stock-quickread`、`company-history`、`driver-map`、`alpha-thesis`、`consensus-map`、`earnings-setup`、`bear-pre-mortem`、`comps-analysis`。其它 research skill 默认单线执行，只有用户明确要求 `sub-agent`、`delegate` 或 `并行` 时才开启并行。sub-agent 只能返回 evidence card，不得写最终结论、ranking、thesis、valuation 或 model treatment。Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- Evidence card 必须包含 claim、source title、URL 或 source location、quote / metric、as-of、confidence、caveat 和 suggested use；缺任一关键项时只能作为线索。
- 主 agent 必须完成 URL/claim spot check、source conflict handling 和最终 synthesis；未经主 agent 抽查的 sub-agent 输出不得进入最终 artifact 的结论层。
- If a default-parallel shortlist skill or a user-explicit parallel request cannot spawn sub-agents on the current host / runner, the main agent must state `sub-agent unavailable`, the reason, the single-thread evidence-card fallback used instead, and the resulting source coverage caveat. Do not silently downgrade.

## 6. Model Sub-Agent Protocol

- `3-statement-model`, `dcf-model`, `comps-analysis`, and `model-update` use a separate Model Sub-Agent Protocol, not the evidence-card-only research protocol.
- Modeling sub-agents may return model QA notes / work-packet findings, including actuals mapping audits, formula checks, peer multiple checks, and update-map QA.
- Main agent owns the final workbook, valuation verdict, price target, model treatment, and delivery decision.
- Runtime cap: no per-skill sub-agent count limit; max 6-8 active sub-agents globally; parallel within one skill but serial across skills; close sub-agents immediately after evidence cards or QA notes return.
- Before using modeling inputs, check `actuals-resolved.json`, `evidence-pack.json`, source-map, and completeness; missing or unmapped actuals must not be written as 0.

## 7. Senior Analyst Radar

当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。

高价值维度：
- 业务实质错读。
- 披露口径异常。
- model-driver gap。
- narrative-data mismatch。
- margin / revenue mismatch。
- market misread。
- peer mismatch。
- source conflict。
- know-how gap。

提醒格式：

```markdown
**这里值得深化**
- 怪异点：[哪里不自然]
- 可能说明：[1-2 个解释]
- 可以问 AI：[1-2 个最关键问题]
```

## 8. Primitive Routing

- Workspace routing: 研究 skill 保存 artifact 时自动创建缺失目录（`mkdir -p`）；`ingest` creates `_raw/<category>/` and `_cache/` on first conversion。Industry/theme topics may hold single-company workbench files named `YYYY-MM-DD-<company-slug>-<artifact>.md`。`integrate` remains whole-topic directory merge。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-insight`。
- 遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。
- ingest 前确保 topic root 已存在（`industry/<industry>/index.md` 必须存在）。若缺失，agent 自动创建——无需单独调用 skill。
- 研究 skill 启动时，先检查 `industry/<industry-slug>/_cache/` 是否存在已 ingest 的相关材料。如有，优先引用 cache 中的 source-tracked markdown，而非重新获取原始文件。若是单公司研究，同时检查相关 `industry/<industry>/companies/<ticker>/_cache/financial-data/financial-data-summary.md`；需要审计或机器输入时再进入 `internal/evidence-pack.json`、`internal/actuals-resolved.json`、`internal/source-map.json`。

## 9. 单行业归属规则（Single-Industry Primary Residence）

**一支股票的主研究路径只落在一个行业目录。其他行业仅引用，不重复保存 artifact。**

### 9.1 Primary 判定：最早研究优先

**Primary = 该股票最早有 research artifact 的行业目录。**

判定依据按客观时间戳（`index.md` 首次注册该公司的日期），不做业务判断。理由：
- **客观可查**：不需要争论"PG 利润占比更大"还是"GT 增长叙事更强"。
- **可追溯**：git blame / index.md 日期即答案。
- **防漂移**：不会因为公司业务转型或 agent 判断不同而反复更换 primary。

**判定流程**：
1. 新开一家公司时，**先扫描所有 `industry/*/index.md`**——确认该公司是否已在其他行业有 artifact。
2. 如果已存在 → 当前行业只做交叉引用，artifact 写入已有的 primary 目录。
3. 如果不存在 → 当前行业即为 primary，artifact 正常写入。

### 9.2 Artifact 纪律

- **主研究 artifact**（quickread、driver-map、moat-analysis、alpha-thesis、earnings-setup、scenario-model、consensus-map、bear-pre-mortem 等）**只写入 primary 行业目录**。
- **跨行业 artifact**（如 mechanism-insight 涉及某公司在特定设备段的价值捕获）可以落在交叉行业目录，但 artifact 内必须显式引用 primary 行业路径。
- **teach-in / industry-landscape** 等纯行业级 artifact 不在本规则管辖范围（它们不"归属"某家公司）。

### 9.3 index.md 引用格式

**交叉行业**的 `index.md` 按以下格式注册：

```markdown
- 公司名 (TICKER) → **主研究在 [industry-slug](../path/companies/ticker/)**。<一句话说明本行业为什么关注它，哪个业务段/产品线相关>。
```

**Primary 行业**的 `index.md` 在正常列出 artifact 的同时，加一行标注跨行业关联：

```markdown
- **跨行业引用**：该公司旗下 <业务段> 同时服务于 <行业名> → 详见 [industry-slug](../path/)
```

### 9.4 Cache 共享

- `_cache/financial-data/` 和 `_cache/images/` 属于只读数据层，**可以在多个行业目录保留副本**。这不是"重复 artifact"。
- Primary 行业目录的 cache 为主副本（数据最全、最先更新）。
- 交叉行业如需本地 actuals 加速查询，从 primary 复制，并标注 `_synced_from: <primary_path>`。
- **禁止在交叉行业目录创建 dated research artifact**——`YYYY-MM-DD-*.md` 只能出现在 primary 目录。

### 9.5 迁移流程

如果 primary 行业判定错误需要纠正：

1. 确认最早 artifact 日期——以 `index.md` 首次注册日期为准，不依赖文件修改时间。
2. 将全部 `YYYY-MM-DD-*.md` 从错误目录迁移到正确目录。
3. 更新两个行业的 `index.md`。
4. 合并 `_cache/`（保留较全的数据）。
5. 错误目录删除 dated artifact，仅保留 `_cache/` + index.md 引用行。
6. 如果有 evidence ledger，更新 `_cache/evidence/<TICKER>.evidence.json` 路径引用。

### 9.6 已知跨行业公司清单

| 公司 | Primary（最早 artifact 所在行业） | 交叉行业 | 交叉业务段 |
|---|---|---|---|
| Mycronic (MYCR SS) | optical-module-equipment (2026-05-29) | pcb-equipment | ATG 飞针测试、GT PCB 电测段 |
| Keysight (KEYS US) | optical-module-equipment | pcb-equipment | ICT 针床测试、TDR 阻抗模块 |

> **维护规则**：每新增一家跨行业公司，在此表追加一行。每年审计一次：如果某公司的 revenue/profit thesis 已明显迁移到另一个行业，讨论是否启动 §9.5 迁移流程。

## 10. 分部数据优先级（Segment Data Priority）

**financial-data 采集分部数据时：业务分部 > 地理分部。**

- **优先级**：business segments (PG/GT/AS-HF/AS-HV) > geographical segments (Asia/EMEA/Americas)。两者都有则都保留在 `actuals-resolved.json` 的 `segments` 数组中，按 `type: "business"` 和 `type: "geography"` 区分。
- **§3 分部表**：stock-quickread 的 §3 关键财务数据表优先展示业务分部。只有在公司不披露业务分部时（如单分部公司），才用地理分部替代。
- **actuals-resolved.json segments 字段规范**：每个 segment 对象必须含 `type` 字段（`"business"` | `"geography"`），方便 agent 区分优先级。

## 11. Topic Scaffolding Convention（自动脚手架）

> 研究 skill 保存 artifact 时自动完成以下脚手架——无需研究员感知。

### 触发条件

任何 research skill（`stock-quickread`、`driver-map`、`teach-in` 等）按 save policy 写 artifact 到 `industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md` 时，agent 自动执行：

### 检查清单（agent 保存 artifact 前 30 秒完成）

1. **行业目录**：`industry/<industry>/` 不存在 → `mkdir -p` + 创建 `index.md`（含行业名 + 当前问题 + 研究产出 + 待解决问题占位）
2. **公司目录**：`industry/<industry>/companies/<ticker>/` 不存在 → `mkdir -p`
3. **COVERAGE.md 注册**：公司不在 `COVERAGE.md` → 追加一行 `| <ticker> | <公司名> | <行业> | T3 | A3 | building | <YYYY-MM-DD> |  |  | auto-registered |`
4. **行业 index.md 注册**：artifact 不在行业 `index.md` 研究产出列表 → 追加一行时间倒序 artifact link
5. **不要做的事**：不创建 `_inbox/`（不需要了）、不创建 `_cache/`（financial-data 按需自建）、不预建目录、不阻塞主流程

### Agent 执行伪代码

```
def save_artifact(industry, ticker, artifact_path):
    ensure_dir(f"industry/{industry}/") + touch index.md if missing
    ensure_dir(f"industry/{industry}/companies/{ticker}/")
    register_in_coverage(industry, ticker) if not already
    register_in_industry_index(industry, artifact) if not already
    write artifact
```

### 与旧版脚手架的区别

> 此前有独立  skill（已移除）。当前版本中，所有研究 skill 保存 artifact 时自动完成脚手架——无需用户感知。
