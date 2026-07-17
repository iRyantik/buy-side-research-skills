# CLAUDE.md - Buy-Side Research Workspace 宪法模板

> 本文件是当前 research workspace 的本地宪法。
> 它负责 workspace 高层原则、topic 结构和 source stance，不负责每个 skill 的细 procedure。
> 如果本文件与被调用 skill 的具体执行细则冲突，采用更严格且更贴近 runtime 的 skill 规则。

---

## 1. Workspace Context

- Workspace path: `{{WORKSPACE_PATH}}`
- Created by: `buy-side-research-skills init`
- Created date: `{{DATE}}`
- Current system generation: `5.0.0`

本 workspace 用于 buy-side equity research。目标不是"了解公司"，而是形成可追溯、有 edge、能支持投资判断和下一步研究优先级的输出。

---

## 2. Researcher Context

- **身份**：Buy-side equity researcher，hedge fund / long-short 语境。
- **主要覆盖**：industrials、aerospace and defense、advanced manufacturing、oil & gas、renewable、nuclear、emerging tech themes。
- **工作目标**：判断要不要投、怎么投、何时退；不是写 sell-side 风格公司介绍。

---

## 3. Output Style

### 3.1 Language

> `LANG-default = zh`

默认中文自然语言输出。

**始终保留英文（不翻译）**：

- **股票代码**：`2330 TT`、`AAPL US`、`9988.HK`、`005930 KS`、`7203.T`
- **财务比率 / 科目缩写**：PE、P/B、EV/EBITDA、EV/Sales、FCF、ROIC、ROE、ROA、NRR、GRR、ARR、GMV、LTV、CAC、IRR、WACC、NPV、SOTP、DCF
- **会计 / 流程缩写**：GAAP、Non-GAAP、IFRS、M&A、IPO、SPAC、LBO、PIPE、ESOP、CapEx、OpEx、D&A
- **行业 / 技术 jargon**：SaaS、IaaS、DTC、BNPL、Fab、EUV、ASIC、HBM、CoWoS、LLM、RAG（圈内默认英文或无统一中译的术语保留英文）
- **货币代码**：USD、JPY、KRW、CNY、EUR、SGD、HKD、TWD、INR、GBP
- **监管 / 政府机构**：SEC、FDA、CFIUS、FOMC、ECB、MAS、PBoC、CSRC、CMA、JFTC、FSC
- **单位**：`x`（倍数）、`bps`、`pp`（百分点）、`bn`、`m`、`k`、`tn`、`wpm`、`kwh`
- **路径 / 系统识别**：source title、URL、文件路径、YAML / JSON key、skill name、产品代号
- **Buy-side jargon**：batting average、refi wall、underwater、guide-down、whisper number、tape、book、bid、ask、long、short、cover、squeeze、bagger、re-rate

**公司名**：

- 有公认中文名 → 用中文名：苹果、三星、丰田、台积电、宁德时代、腾讯、阿里巴巴、丰田、本田、索尼、现代、起亚
- 圈内默认说英文 / 无标准中译 / 翻了拗口 → 直接英文：Salesforce、Shopify、Snowflake、Datadog、LVMH、Hermès、Nvidia、AMD、Stripe、Cloudflare、Atlassian、Palantir
- 中国大陆 / 港 / 台公司 → 用原中文名：台积电、宁德时代、腾讯、阿里巴巴、美团、京东、比亚迪
- 日韩公司用汉字写法 → 用原汉字：任天堂、三菱商事、三井物産、現代自動車（也可写"现代汽车"）、三星電子（也可写"三星电子"）
- 日韩公司用假名 / 谚文 → 首次出现 `中文名（原文）`，后续仅中文：迅销（ファーストリテイリング）→ 后续 "迅销"；起亚（기아）→ 后续 "起亚"；尼得科（ニデック）→ 后续 "尼得科"

**非中文 / 英文公司披露项**：按最小必要原则保留源语言锚点。首次出现的官方 segment、product、KPI、project、program、披露 bucket、订单 / backlog 分类、监管 / 合同术语、客户 / 终端市场名、source title，以及任何后续可能回源检索的词，写成 `源语言（中文译名）`；后续默认用中文短名，除非同一表内存在多个易混淆原文 bucket。

**全中文即可**：普通分析句、takeaway、通用会计 / 商业概念、已在前文定义过的重复项、非关键 source wording、图表标题 / 副标题 / 坐标轴 / tooltip / callout / 控件按钮等 user-facing 文本（财务术语本身除外，按上文规则保留英文）。

**管理层原话**：只有措辞本身影响判断时保留短原文并贴 source；否则用中文概述并贴 source。

**override**：用户明确说 "用英文输出" / "use English" 时切换英文，覆盖范围至本轮对话结束（除非用户再次声明）。用户在某一段明示用日 / 韩 / 其他语言时，仅该段切换。

**Agent 新闻搜索语言**：搜特定市场股票新闻时，优先本地语言：

| 市场后缀 | 搜索语言 |
|---|---|
| `.HK` `.SS` `.SZ` | 简体中文 |
| `.TW` | 繁体中文 |
| `.JP` | 日本語 |
| `.KS` `.KQ` | 한국어 |
| `.US` `.AS` `.DE` `.L` `.ST` `.KL` | English |

### 3.2 Directness

- 所有分析必须结论先行：第一段先给判断 / action / verdict，再给依据。
- 不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`。

### 3.3 Data First

- 判断必须有数字、数据表、source-backed evidence 或明确推理链支撑。
- 无 source 的事实不能伪装成事实，只能 honest degrade。
- 数据表必须有 takeaway；takeaway 必须给结构性洞察，不要复读表格。

### 3.4 Numbers, Currency, Dates, Units

> `NUM-default = western`

**数字**：千位分隔符西式 `1,234,567`。默认不用"万 / 亿 / 万亿"为单位；用户明示用中式单位（"几十亿"、"万亿规模"、"市值几千亿"）或语境上明显是中文金融行话时才切。

**货币**：

- 美元 → `$24bn`、`$45m`、或 `USD 28.5bn`
- 非美元 → ISO 货币代码前缀：`JPY 3,200bn`、`CNY 12bn`、`KRW 4,500bn`、`HKD 850m`、`TWD 1,250bn`、`EUR 2.4bn`
- 多币种对比 / 跨市场公司时，统一注明换算汇率与日期：`USD 24bn（以 JPY/USD = 152、2024-09-30 汇率换算）`

**百分比 / 倍数 / bps**：`14.2%`、`+45bps`、`22.4x`、`0.8x`、`-3.1pp`。注意 `pp`（百分点）≠ `%`（相对变化）。

**日期 / 期间**：

- prose 中文："2024 年 3 月"、"2024 财年"、"上半年"、"季度环比"
- 表格 / 图表 axis / 数据列保留英文简写：`Mar '24`、`1Q24`、`FY24E`、`4Q23A`、`CY2024`、`YTD`
- 财年口径不明时显式标注："（CY24 ≈ AAPL FY24，对应 2023-09 至 2024-09）"
- 用户提到的相对时间 ("过去一年"、"最近一个季度") 转成绝对期间再分析，避免回看时间锚点漂移

**数量级简写**：`bn` / `m` / `k` 而非 `B` / `M` / `K`（避免与 mega- 等单位前缀混淆）。`tn` 用于 trillion。

**精度**：

- 百分比 1 位小数为默认（`14.2%`），margin 类要紧时给 2 位（`28.45%`）
- 倍数 1 位小数（`22.4x`），ROIC / ROE 类指标可给 2 位
- 不要假装精度：调研 / 估算来的数 round 到合理 sig fig，例如 `~$2bn` 而非 `$2.13bn`，并标 `[估算]` 或来源

---

## 4. Source Stance

- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。
- 每个 truth-like claim 默认使用 inline clickable short anchor。
- 每篇 research artifact 文末统一保留一个 `## Resources`。
- source quality follows two tracks：
  - 披露事实轨：`topic-local evidence cache > primary public > Bridge > web`
  - 市场快照轨：`actuals market_data（fresh <180天）> Bridge > yfinance > WebSearch / WebFetch`
- 同一质量层级内，优先 `home-market / local-language source`。
- `financial-data` CLI 是 source-of-record——写入 `actuals-resolved.json`（含 structured financials + market_data snapshot）；artifact 财务数据必须从 actuals 取，Bridge 是快照补充不是替代。
- Bridge 是 trusted third-party 市场数据聚合层（当前实现：Longbridge MCP，覆盖 US/HK/SH/SZ/SG）。详情见 §4.1。
- `internet source` 只补 market-snapshot track 的缺口，不冒充 company-disclosed fact；公司/披露事实仍优先 `primary public`。

更完整的 claim-level source contract、fallback taxonomy、shared hook law 和 skill-specific judgment / workflow delta，由被调用的 active skill 与 workspace hooks 共同决定。

### 4.1 Unified Data Routing（`route.py`）

本 workspace 的数据路由由 `capability-matrix.json` 统一管理。Agent **不手动判断优先级**——每个数据请求前调 `route.py` 获取完整 chain，按序执行。

```bash
python .scripts/shared/route.py <TICKER.MARKET> <capability>
```

Agent 行为：数据请求 → `route.py` → 拿到 chain → 按序执行 → 失败自动下一个。详细 capability 列表见 `.references/routing/capability-matrix.json`。

**Bridge 当前实现：Longbridge MCP**（145 工具，覆盖 US/HK/SH/SZ/SG），后续扩展新 source 不改上层路由逻辑。

#### 路由决策：三重判断

Agent 收到涉及特定公司/市场的数据请求时，按以下顺序判断：

```
1. 问的是哪种数据？── 市场快照 / 财务快照 / 结构化三表
2. actuals 是否已缓存？── 先扫 industry/*/companies/<ticker>/.cache/financial-data/actuals-resolved.json
3. 上下文是什么？   ── 日常对话（秒回优先）/ 写 artifact（准确性优先）
```

#### 路由表

```
┌─────────────────────┬───────────────────────┬───────────────────────┐
│ 问什么                │ actuals 已有           │ actuals 没有           │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ 报价/K线/日内        │ Bridge               │ Bridge                │
│                      │ → yfinance            │ → yfinance            │
│                      │ → WebSearch           │ → WebSearch           │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ 估值/新闻/评级       │ Bridge               │ Bridge                │
│ /日历/汇率/资金       │ → yfinance            │ → yfinance            │
│ /股息/情绪/异动       │ → WebSearch           │ → WebSearch           │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ 财务快照             │ ① Read actuals        │ Bridge                │
│ (日常对话：           │    历史FY → 本地缓存   │  financial_report_    │
│  收入多少/EPS/ROE)    │ ② Bridge              │  latest 秒回          │
│                      │    financial_report_  │ → yfinance snapshot   │
│                      │    latest（最新Q）     │ → 用户追问多条时      │
│                      │ ③ 不一致 prefer       │   建议拉 CLI           │
│                      │    Bridge（时效性）     │                       │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ 结构化三表           │ 读 actuals            │ /financial-data       │
│ (artifact Step 1)    │ → /financial-data     │ --lite（强制，        │
│                      │   --lite 增量更新     │  skill Pipeline 不可   │
│                      │   （artifact 管道     │  跳过）               │
│                      │    强制步骤）          │                       │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ 多期FY对比           │ 读 actuals            │ /financial-data       │
│ (--periods 3Y等)     │ → 过期 >180天 提醒    │ --lite                │
│                      │                      │ --periods FY20-FY25    │
└─────────────────────┴───────────────────────┴───────────────────────┘
```

#### Fallback 链（统一）

```
Bridge（US/HK/SH/SZ/SG 首选）
  ↓ 不可用 / 超时 / 未覆盖该市场
yfinance（market data 兜底 + quick financial snapshot）
  ↓ 也不可用
WebSearch / WebFetch（最后兜底）
```

Bridge 挂了 + actuals 不存在时的行为：yfinance 先给快照 + `[建议拉 financial-data CLI]`。

#### Agent 行为摘要

1. 收到涉及特定公司的问题 → 先检查 `actuals-resolved.json` 是否已存在
2. 市场数据类（报价/估值/新闻/日历）→ Bridge → yfinance → WebSearch
3. 财务快照类（日常对话"收入多少"）→ actuals 已有则双查（本地+最新Q），无则 Bridge 秒回
4. 写 artifact 时 → `/financial-data --lite` 是 skill Pipeline Step 1，不可跳过
5. Bridge 不可用 → yfinance snapshot + 建议拉 CLI

#### Bridge 当前实现

**Longbridge MCP**（`https://openapi.longbridge.com/mcp`）：145 工具，覆盖 US/HK/SH/SZ/SG。
详细工具映射见 `trusted-market-bridge` skill 的 MCP Tool Mapping 表（已验证 34 个 domain，2026-06-09）。

#### `financial-data` CLI 不可替代的场景

- 结构化三表（IS/BS/CF）的 source-tracked actuals pack
- 多期 FY data（`--periods FY2020-FY2025`）
- `actuals-resolved.json` 写入（artifact 的财务数据源）
- 需要 SEC/DART/EDINET/AKShare 等 primary public provider（Bridge 不替代 primary disclosure）

Bridge 的 `financial_report_latest` / `financial_statement` 是快照辅助，不能替代 `financial-data` CLI 的 source-of-record 地位。

---

## 5. Workspace Structure

本 workspace 以行业 topic 为核心组织，公司是行业子目录：

```text
industry/
  <industry-slug>/
    panorama/                 # 行业全景产出（按 skill 分类）
      teach-in/
      industry-landscape/
      mechanism-insight/
      peer-deep-dive/
      candidate-screener/
      scenario-model/
      consensus-map/
      market-sizing/
      other/                  # 非 skill 产出的行业分析
    companies/
      <ticker>/               # 公司深掘——一个公司一个窝
        [YYYY-MM-DD]-*.md
        .cache/
    RESEARCH.md               # 行业 overview + 公司注册表 + Source/Thsis/事实/研究轨迹
    .cache/
COVERAGE.md                   # 覆盖公司状态跟踪表（thesis stage / priority / next catalyst）
```

基本约束：
- 公司 artifact 落 `industry/<industry>/companies/<ticker>/`，行业 artifact 落行业根
- 跨行业公司在多个行业 `RESEARCH.md` 注册 reference，文件不搬
- `.cache/` 存放 source-tracked 解析材料、evidence pack、结构化数据
- topic artifact 命名由 `new-session` 统一解析
- workspace hooks 属于 runtime contract，不要手改或删除

---

## 5.5 Plugin Built-In Capabilities

以下能力由 buy-side-research-skills 插件内置，无需调用 skill 即可直接使用。

### 共享脚本（`.scripts/`）

| 脚本 | 用途 | 调用示例 |
|---|---|---|
| `shared/verify-claim.py` | 来源验证链（HTTP→Playwright→curl→[UNVERIFIED]） | `python .scripts/shared/verify-claim.py <url> --json` |
| `shared/download-image.py` | 图片下载（产品图，workspace 级缓存跨 skill 共享） | `<url> --output <slug>` |
| `shared/verify-runtime.py` | 一键检查 12 项运行时依赖 | `python .scripts/verify-runtime.py` |
| `shared/web-extract.py` | 网页正文提取（去导航/广告/脚本） | `<url> [--markdown]` |
| `shared/pdf-extract.py` | PDF 文本+表格提取（pymupdf→pdfplumber→pypdf） | `<file_or_url> [--tables]` |
| `financial-data/actuals-to-appendix.py` | 从 actuals-resolved.json 生成 sell-side 风格附录 | `--tickers T1,T2,...` |
| `shared/describe-figures.py` | 图表描述提取（从 docling/pymupdf 缓存 markdown 中提取 figure 并生成带编号描述） | `<markdown_path>` |
| `shared/verify-table-crosscheck.py` | 表格数值交叉验证（PDFPlumber vs Docling/cache markdown） | `<markdown_path> [--pdf <pdf_path>]` |
| `evidence_ledger.py` | 证据分类账管理 | 跟踪 claim 验证状态 |
| `shared/search.py` | DDG HTML 新闻搜索（无需 API key，双语搜 + 行情页过滤） | `from search import ddg_search_news; ddg_search_news("query")` → list[dict] |

### 自动 Hook 防御（`pre_write_gate` 13 CHECKS）

每次 Write/Edit 研究 artifact 时自动触发，无需手动调用：

| CHECK | 拦截什么 |
|---|---|
| 1 | Bare anchor（[S1] 无 URL） |
| 2 | Double URL 拼接 |
| 3 | 非标准 inline label |
| 4 | Resources 格式不合法 |
| 5 | 段落 source 密度不足（≥3 个数字零 source anchor） |
| 6 | 引用图片不在磁盘上 |
| 6a | 用 `browser_take_screenshot` 代替图片下载 |
| 7 | `[缺图]` 无 download attempt 记录 |
| 8 | `[需查证]` 超过 8 个 |
| 9 | Pipeline header 与实际不符 |
| 10 | actuals 数据过期（>180 天） |
| 11 | Evidence 验证覆盖率 <80% |
| 12 | Mermaid diagram type 无效（如 `scatterchart`） |
| 13 | 表格列数不匹配 / 缺分隔行 / >12 列未拆分 |

### 其他自动 Hook

| Hook | 触发时机 | 检查内容 |
|---|---|---|
| `source_contract` | PostToolUse / Stop | Source anchor 完整性 |
| `table_render_integrity` | PostToolUse | 表格结构合法性 |
| `mermaid_syntax` | PostToolUse | Mermaid 图类型验证 |
| `skill_structure_contract` | PostToolUse | 必填 section 存在 |
| `evidence_ledger_floor` | Stop | 证据验证覆盖率 ≥80% |
| `workspace_guard` | PreToolUse | 禁止在非 workspace 目录写 artifact |

### 数据管道

| 操作 | 命令 |
|---|---|
| 拉取财务数据 | `/financial-data <TICKER>` |
| 拉取多期数据 | `/financial-data <TICKER> --periods FY2020-FY2025` |
| 检查运行时 | `python .scripts/verify-runtime.py` |
| 更新插件+同步 workspace | `/update-agent-runtime` |

### Actuals ↔ Artifact 同步规则

> `actuals-resolved.json` 的任何字段被更新后，**必须**找到所有引用该 ticker 数据的 artifact，同步更新数字、结论和估值。

- **触发**：actuals-resolved.json 被 Write/Edit 或 external script 修改
- **动作**：`grep -r "<ticker>" industry/*/companies/` 找所有引用 artifact → 逐文件扫描是否用到被修改的字段 → 同步改写
- **验证**：写完 artifact 后，artifact 里每个数字必须能从 actuals-resolved.json 复算——能对上才能过
- **反模式**：actuals 更新了但 artifact 里留着旧推算数。artifact 里出现「~350」但 actuals 里是「225」→ 拦截

### 图片规则

- 产品图：`download-image.py <url> --output <slug>`
- 产品图：`download-image.py <url> --output <slug>`
- **禁止** `browser_take_screenshot` 代替下载——hook CHECK 6a 直接 block
- `[缺图]` 仅在所有 tier（HTTP→Playwright）失败后允许

### 缓存优先

下载外部文件前先检查本地缓存：
- 公司披露 → `industry/<slug>/companies/<ticker>/.cache/`
- 行业报告 → `industry/<slug>/.cache/`
- 命中直接用，未命中再上网。下载后 hook 自动缓存一手资料 PDF。

### 来源验证规则

- 每个 `[I#]` source 必须至少经过 Tier 1-2 验证
- Tier 链：HTTP GET → Playwright MCP (`browser_navigate`+`browser_snapshot`) → curl → [UNVERIFIED]
- `[UNVERIFIED]` 仅在所有 tier 失败后标记

### Canvas 文件

worktree 操作、`references/runtime/research-runtime.md`（五链全文档）、`references/policy/`（策略基线）、`references/kpi-drivers/`（KPI 模板）、`.references/cache-contract.md`（缓存写契约与删除规则）。

### Research Memory 系统

每个行业和公司目录下有一个 `RESEARCH.md`（命名固定大写），记录四层信息：
1. **Source 地图** — 所有关键披露/第三方文件的 URL 和本地缓存路径
2. **Thesis 状态** — 当前多空倾向、核心假设及验证状态
3. **事实基线** — 速查卡（thesis 盯的 5-8 个数）+ 完整表 + 已推翻认知
4. **研究轨迹** — 已完成 artifact、下一步 5 问、已排除方向、上次读到哪

**自动加载**：`memory/research/` 下的薄卡片由 `generate-memory-cards.py` 从 RESEARCH.md 自动生成，CC session 启动时自动注入。

**Agent 行为**：
- 新 session 提到公司/ticker → 先 `Read` 对应公司 RESEARCH.md + 行业 RESEARCH.md
- 每次产出 artifact 后 → 更新对应 RESEARCH.md 的相关 section（≤5 分钟，增量维护）
- Hook 会在写 artifact 后提醒更新，但最终由 agent 负责
- RESEARCH.md 是覆盖更新（非 append），只保留最新状态

---

## 6. Routing Stance

skill 是决策工具，不是装饰性模板。

高层 routing 提示：
- 零基础建立行业物理直觉 -> `teach-in`
- 陌生公司 first pass -> `stock-quickread`
- 行业全景 / 投资判断 -> `industry-landscape`
- 业务 / 分部 / 披露历史 -> `company-history`
- 行业机制 / 工程原理 / 设备链条 -> `mechanism-insight`
- 市场规模 / TAM 估算 -> `market-sizing`
- revenue / margin / backlog / price-volume-mix driver -> `driver-map`
- 市场预期 / priced-in / variant-view gap -> `consensus-map`
- 分场景 L/S 排序 -> `candidate-screener`
- 横向比较（同/跨市场） -> `peer-deep-dive`
- 竞争壁垒量化 -> `moat-analysis`
- 催化剂时间线 -> `catalyst-map`
- 管理层资本配置 -> `capital-allocation`
- bull/base/bear odds memo / 假设溯源 -> `scenario-model`
- 财报前 setup -> `earnings-setup`
- 财报后快速判断 -> `post-earnings-quick`
- LS pair -> `pair-trade`
- 三表/结构化 actuals -> `financial-data`
- 模型 / DCF / comps -> `driver-map` / `driver-map` / `driver-map`
- 跟踪覆盖状态 -> `coverage-tracker`
- 沉淀认知 -> `research-journal`
- 更新插件 / 同步 workspace -> `update-agent-runtime`

具体 procedure、fallback 边界和并行策略，以被调用 skill 为准。

---

## 7. UTF-8 文本纪律

中文或多语言文本文件统一使用 **UTF-8 无 BOM**。

- `.md` / `.yaml` / `.json` 默认按 UTF-8 无 BOM 维护。
- 修改中文文件时必须显式使用 UTF-8 写回。
- 批量脚本改写文本时必须指定 UTF-8，避免 mojibake。

---

## 8. Boundary

- 本文件服务用户 research workspace。
- 插件开发治理维护在 plugin dev repo root `CLAUDE.md`，不在本文件展开。

