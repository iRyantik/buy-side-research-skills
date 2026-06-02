---
name: financial-data
description: Fetch or parse source-tracked company financial data by market and identifier.
---

# Financial Data

`financial-data` 把各市场可机器读取的财务数据变成 source-tracked evidence pack。它是 operations skill，不是研究 skill：只负责拉取、解析、标准化、标注完整性和写入 `_cache/datasets/financial-data/`，不解释投资含义、不做 forecast、不替代 `driver-map` 或 `3-statement-model / dcf-model / comps-analysis / model-update`。

核心产物不是“看起来完整的三表”，而是“哪些字段真的可用、来自哪里、能不能进模型”。V1 默认抓三表；如果 provider 能结构化抓到收入拆分，就把它写进 `actuals-resolved.json` 的 `statements.revenue_split`；如果不能，就只标 `revenue_split = provider-gap` 并保留 filing / annual report 原文供 `driver-map` 用 LLM 抽。不能用推断补齐。

## 心法

财务数据拉取最容易出错的地方，不是 API 报错，而是数据看起来太整齐：provider-normalized label 被误当作公司原始披露，segment bucket 被自动合并，ticker-only 路由找错实体，或三表可得但模型真正需要的 revenue split 缺失。

本 skill 的工作逻辑是 **provenance first + completeness before model use**。先保存 raw provider payload，再保存 normalized evidence pack；日常外显只给 `financial-data-summary.md`，机器输入和审计文件进入 `internal/`；先告诉研究员缺什么，再让 `driver-map` 和 `3-statement-model / dcf-model / comps-analysis / model-update` 判断能否建模。

`financial-data` 服务 topic-centric 架构：单公司数据默认落在 `industry/<industry>/companies/<ticker>/`；theme / industry topic 只保存 snapshot 或 links，不变成第二套公司主档。

## 职责边界

负责：

- 按 `market`、`identifier`、`identifier_type`、`company_slug` 拉取或解析结构化财务数据。
- 默认写入 canonical company topic：`industry/<industry>/companies/<ticker>/_cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/`。
- 保存 raw provider payload 到 `_raw/datasets/financial-data/`，保存 normalized evidence pack 到 `_cache/datasets/financial-data/`。
- raw evidence 层至少包含 `provider_payload.json`、`identity-source.json`；存在真实 filing source 时还要写 `filings/<filing-id>/source.*`、`source-metadata.json`、`source.sha256`。
- 生成 public `financial-data-summary.md`；机器文件进入 `internal/`，包括 `evidence-pack.json`、`actuals-resolved.json`、`full-filing.md`、`manifest.json`、`financials.md`、`financials.normalized.json`、`completeness.json`、`source-map.json` 和 `cross-check.json`。
- 输出字段级 completeness matrix：三表和 `revenue_split` 分开标状态。
- 支持 current topic snapshot：`topics/<topic>/_cache/datasets/financial-data-snapshot/<run-id>/`。
- 对 dependency gap、credential gap、provider gap fail honestly。

不负责：

- 不做公司业务解释、driver 判断、revenue split 推断或 segment 真实经济含义判断；交给 `company-history` / `driver-map`。
- 不做 forecast、DCF、comps、reverse DCF 或 workbook 更新；交给 `3-statement-model / dcf-model / comps-analysis / model-update`。
- Full / Lite 均自动拉市场快照数据（股价、市值、PE/PB/PS/EV/EBITDA 等），走统一增量 fill 引擎：`yfinance(全量) → Bridge(覆盖US/HK/SH/SZ) → WebSearch(逐字段) → Google Finance(兜底)`。详见市场数据段。
- Bridge 在 actuals 里只做 cross-check（不替代 provider_api）；在市场数据里做 US/HK/SH/SZ primary。
- 不把 `_cache/` 写成 earned memory；沉淀认知交给 `research-journal`。
- 不创建 dated research Markdown artifact。
- 不承诺所有市场都能 ticker-only 自动 discovery。

## 触发与输入

触发语：

- “拉一下 GE 的结构化财报”
- “fetch financial data”
- “按 ticker 拉三表”
- “DART 拉韩国财报”
- “用 openesef 解析这份 ESEF”
- “把 ASML 的 ESEF package 转成 financial-data evidence pack”
- “给这个 theme 拉一篮子公司财务 snapshot”

输入字段：

| 输入 | 用途 | 默认 / 缺失处理 |
|---|---|---|
| `output_scope` | `canonical_company` / `current_topic_snapshot` | 默认 `canonical_company` |
| `company_slug` | 公司 canonical topic slug | canonical 输出必填 |
| `topic` | 当前 topic slug | snapshot 输出必填 |
| `market` | `us` / `cn` / `hk` / `jp` / `kr` / `tw` / `eu` | 必填 |
| `identifier` | ticker、CIK、EDINET code、DART corp code、LEI、filing URL 等 | 必填 |
| `identifier_type` | `ticker` / `isin` / `lei` / `cik` / `edinet_code` / `dart_corp_code` / `filing_url` / `local_esef_package` | 默认 `ticker` |
| `periods` | `latest`、`FY2021-FY2025`、`quarterly` 等 | 默认 `latest` |
| `items` | 三表、`revenue_split`、filing / full text | 默认全取 |
| `source_mode` | `auto` / `filing_only` / `provider_normalized` | 默认 `auto` |
| `financial_data_pack_path` | 给 snapshot 或 `3-statement-model / dcf-model / comps-analysis / model-update` 指向已有 pack | 可选 |

欧洲特殊规则：

- `openesef` 支持 ESEF/iXBRL parsing。
- `identifier_type = filing_url` 或 `local_esef_package` 是可信路线。
- `identifier_type = ticker` 属于 ticker-only discovery，V1 标 `experimental`；无法定位 filing 时输出 `provider-gap`。

## 执行模式

### Dependency Bootstrap / Check

运行：

```powershell
python _scripts/financial-data/financial_data.py --check-deps
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly
```

用户显式确认后才运行：

```powershell
_scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes
```

### Canonical Company Fetch

默认写入：

```text
industry/<industry>/companies/<ticker>/
  _raw/datasets/financial-data/<market>/<canonical-id>/<run-id>/
    provider_payload.json
    identity-source.json
    filings/<filing-id>/
      source.*
      source-metadata.json
      source.sha256
  _cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/
    manifest.json
    identity.json
    filing-index.json
    financials.md
    financials.normalized.json
    full-filing.md
    full-filing.chunks.jsonl
    full-filing.index.json
    completeness.json
    source-map.json
    cross-check.json
  _cache/financial-data/
    financial-data-summary.md
    internal/
      evidence-pack.json
      actuals-resolved.json
      full-filing.md
      manifest.json
      identity.json
      financials.normalized.json
      completeness.json
      source-map.json
      cross-check.json
```

`_cache/financial-data/financial-data-summary.md` 是人和 LLM 的默认入口。`_cache/financial-data/internal/actuals-resolved.json` 是 `driver-map`、`3-statement-model`、`dcf-model`、`comps-analysis` 和 `model-update` 读取 historical actuals 的推荐机器入口；其中 `statements` 可包含 `income_statement`、`balance_sheet`、`cash_flow` 和可选 `revenue_split`。missing / unmapped 字段不得写成 0。`internal/evidence-pack.json` 聚合 completeness、source map 和 cross-check；只有审计或 debug 时才直接打开 run-id pack。

如果 `industry/<industry>/companies/<ticker>/index.md` 不存在，block 并提示先用 `new-session` 创建 company topic；不要静默创建复杂 topic 树。


### Lite Mode Fetch（研究前置快速抓取）

触发语：`/financial-data --lite <ticker>` 或 "快速拉 <ticker> 数据"

Lite 模式不做 full filing 解析，不建 evidence pack。只抓 22 个三表核心科目 + 分部收入/利润 + 市场快照数据，写入 `actuals-resolved.json`。目标是 **stock-quickread / candidate-screener / peer-deep-dive / consensus-map / earnings-setup / alpha-thesis / bear-pre-mortem / pair-trade** 启动前的最少必要数据。

**Consumer contract**：消费 skill 只需调用 `--lite` 然后直接从 `actuals-resolved.json` 取数。所有 provider 路由、trust 排序、市场数据降级链均在 financial-data 内部执行。消费 skill 的 Runtime Capsule 不得复读 provider 名、trust chain 或 subagent 数据获取流程。

**三表获取逻辑**：按市场路由 provider，缺则 official_web → yfinance → trusted_web → broad_web 逐层降级。规则与 Full mode 相同的 provider_api + official_web 优先原则。

**市场数据获取逻辑**（unified incremental fill engine）：

Trust 排名：`yfinance > Bridge > WebSearch > Google Finance`

引擎逻辑：每层一次尽可能填多 → 填完立即标记缺口 → 下层只补剩余缺口。

```
Layer 1: yfinance(全量) → ticker.info 一次返回 ~50 字段，零额外成本
  填入: price, mcap, PE TTM, PE NTM, PB, PS, EV/EBITDA, EV/Sales, Dividend Yield, Beta
  → 检查点: 填了 N1/11，缺口列表

Layer 2: Bridge(覆盖 US/HK/SH/SZ) → 高 trust 覆盖 yfinance 已填字段
  补: consensus EPS, Target Price, FX
  → 检查点: 填了 N2/11，缺口列表

Layer 3: WebSearch(逐字段补缺) → 只搜剩余缺口
  - 优先本地语言：CN→中文+英文，JP→日本語+English，KR→한국어+English，欧美→English
  - 多缺口合并 query（同页 PE+PB）→ 一次搜填多字段
  - 单缺口精准搜
  - 拿到即填，标 [WebSearch | as-of | source site]
  → 检查点: 填了 N3/11，缺口列表

Layer 4: Google Finance(一次 fetch 补多 gap) → URL 兜底
  仍缺 → [估值待补]
```

每层检查点示例：
```
yfinance:  8/11, 缺 EV/EBITDA, PEG, Target Price
Bridge:    9/11, 剩 PEG, Target Price
WebSearch: 10/11, 剩 PEG
→ PEG = [估值待补]
```

不设 official_web 层：交易所官网只发交易数据 PDF，不计算 PE/PB。

拉完后写入 `actuals-resolved.json` 的 `market_data`（审计锚，不替代下次拉取）。

**Lite 写入的最小字段**：

| 类别 | 内容 | 状态 | Trust Layer |
|---|---|---|---|
| 三表 | 22 个核心科目（IS/BS/CF） | 必填 | provider_api > official_web > yfinance |
| 分部 | 分部收入 + 利润（如有） | 必填 | provider_api |
| 股价 | 最新收盘价 | 必填 | Bridge > yfinance > WebSearch > Google Finance |
| 市值 | 总市值（本地货币） | 必填 | 同上 |
| PE TTM | 追踪市盈率 | 必填 | Bridge > yfinance > WebSearch > Google Finance |
| PE NTM | 远期市盈率（1Y Forward） | 必填 | Bridge(consensus) > WebSearch > yfinance |
| PB | 市净率 | 必填 | Bridge > yfinance > WebSearch > Google Finance |
| PS | 市销率 | 必填 | Bridge > yfinance > Google Finance |
| EV/EBITDA | 企业价值/EBITDA | 必填 | Bridge > yfinance > WebSearch |
| EV/Sales | 企业价值/营收 | 必填 | Bridge > yfinance |
| PEG | 市盈率/盈利增速 | best-effort | WebSearch > yfinance |
| Dividend Yield | 股息率 | 选填 | yfinance > WebSearch |
| Target Price | 一致预期目标价 | best-effort | Bridge(consensus) > WebSearch |
| Consensus EPS | EPS 预期（NTM） | best-effort | Bridge > WebSearch |
| Beta | 波动率 | 选填 | yfinance |
| 股价历史 | 1 年期日线（驱动因素分析） | 必填 | yfinance |
| 补充 | 股本、SBC、backlog | 有则抓 | provider_api > official_web |
| orders | 当期新签订单（流量，区别于 backlog 存量） | 设备制造公司必填——有则抓，无披露标 [未披露] | official_web > IR |
| growth_rates | revenue_yoy_fy, revenue_yoy_q | 必填——agent 拉完两期数据后计算（FY 对比 FY-1，Q/H 对比同季度） | derived |

**数据完整性规则**：

- ADR/双重股权/H+A：写入 `share_class` 字段
- 数据新鲜度：每个字段标 `[source_layer | as-of 日期]`，不设全局 TTL
- 未覆盖市场（SG/AU/IN/SEA）：yfinance → WebSearch → Google Finance 逐层降级
- 单位归一化：AKShare 万元→元、EDINET 百万円→円、韩网 억원→원
- 非数字占位符（NaN/inf/—/N/A）→ null，不计入已填

**输出**（精简版）：

- `actuals-resolved.json`：三表 + 分部 + `market_data` 审计快照
- 不输出 `financial-data-summary.md`

Lite 不写 `evidence-pack.json`、`full-filing.md`、`completeness.json`、`source-map.json`。


### Fill-Gaps Mode（补 Layer 3 缺口）

触发语：`/financial-data --fill-gaps <ticker>` 或 "补全 xxx 的财务数据"

流程：读 actuals → 遍历 null 字段 → **分两轨补填**：

**三表补缺**：按 market 路由 provider（US→EdgarTools, CN→AKShare, JP→EDINET, KR→OpenDART, TW→FinMind, EU→openesef）→ 填值。provider 缺时按以下 web fallback 策略逐层搜索。填不了的标 [ND]。

**市场数据补缺**：走统一增量 fill 引擎（yfinance → Bridge → WebSearch → Google Finance），只补 actuals 里缺失的字段。已有字段不覆盖。5-15 秒/公司。

**Web Fallback 策略（通用规则）**：先用 `site:` 限定首选域名 → 不加 site 用关键词 → 还搜不到标 `[ND]`。每个 query 同时用**本地语言 + 英文**各搜一次。

| 市场 | 三表 | 收入拆分 | 估值 | Consensus |
|---|---|---|---|---|
| **US** | `site:sec.gov <ticker> 10-K` → `site:stockanalysis.com <ticker> financials` → 裸搜 | `site:sec.gov <ticker> segment revenue` → 裸搜 | `site:yahoo.com <ticker> statistics` | `site:marketscreener.com <ticker> consensus` |
| **CN** | `site:eastmoney.com <ticker> 利润表` → `site:10jqka.com.cn <公司名>` → 裸搜 | `site:cninfo.com.cn <ticker> 营业收入构成` → 裸搜 | `site:eastmoney.com <ticker> PE PB 市值` | `site:eastmoney.com <ticker> 盈利预测` |
| **HK** | `site:aastocks.com <code> 利润表` → `site:xueqiu.com <code> 财务` → 裸搜 | `site:hkexnews.hk <code> 分部收入` → 裸搜 | `site:aastocks.com <code>` | `site:marketscreener.com <ticker>.HK consensus` |
| **JP** | `site:finance.yahoo.co.jp <code> 決算` → `site:kabutan.jp <code> 業績` → 裸搜 | `<code> セグメント別売上高` → `<code> 決算説明会` | `site:finance.yahoo.co.jp <code>` → `site:kabutan.jp <code>` | `site:marketscreener.com <code>.T consensus` |
| **KR** | `site:comp.fnguide.com <gicode>` → `site:finance.naver.com <code> 재무제표` → 裸搜 | `site:dart.fss.or.kr <code> 사업부문별` → 裸搜 | `site:comp.fnguide.com <gicode>` → `site:markets.hankyung.com <code>` | `site:comp.fnguide.com <gicode>` → `site:marketscreener.com <ticker>.KS` |
| **TW** | `site:goodinfo.tw <code>` → `site:mops.twse.com.tw <code> 财务报告` → 裸搜 | `<code> 營收 產品別 部門別` | `site:goodinfo.tw <code>` | `site:marketscreener.com <code>.TW consensus` |
| **EU** | `site:yahoo.com <ticker> financials` → 裸搜 | `<ticker> revenue by segment` → 裸搜 | `site:yahoo.com <ticker> statistics` | `site:marketscreener.com <ticker> consensus` |

跨市场通用：Consensus 首选 MarketScreener，估值首选 stockanalysis.com > yahoo.com。未覆盖市场（SG/IN/AU/SEA）按英文裸搜 → `[ND]`。

### Current Topic Snapshot

用于 theme / industry / peer 工作流：

```text
topics/<topic-slug>/_cache/datasets/financial-data-snapshot/<run-id>/
  snapshot-index.md
  peer-completeness.json
```

Snapshot 可以链接 canonical company pack，但不把单公司 canonical data 复制成第二套主档。

## 工具资源

本 skill 使用：

- 如果你只是想先知道 workspace 里哪些共享环境变量需要配置，先看 `init-workspace` 提供的统一环境入口与 `_scripts/init-assets/env-setup.ps1.template`。本节仍然保留 `financial-data` 自己的完整 provider / dependency / bootstrap 细节，不被那份总入口替代。

- `skills/financial-data/scripts/financial_data.py`
- `skills/financial-data/scripts/bootstrap-financial-data-deps.ps1`
- `skills/financial-data/scripts/providers/sec_provider.py`
- `skills/financial-data/scripts/providers/akshare_provider.py`
- `skills/financial-data/scripts/providers/edinet_provider.py`
- `skills/financial-data/scripts/providers/dart_provider.py`
- `skills/financial-data/scripts/providers/openesef_provider.py`
- `skills/financial-data/assets/requirements-financial-data.txt`

Provider matrix：

| Market | Financial Provider | V1 status | Bridge / Longbridge role |
|---|---|---|---|
| US | EdgarTools / SEC | 三表 + filing markdown + SEC XBRL dimension `revenue_split` when available | **市场数据 primary**。财务：`financial_snapshot` 做 cross-check，不替代 EdgarTools |
| CN A-share | AKShare / Eastmoney | 三表 + `stock_zygc_em` 收入拆分 | **市场数据 primary**。财务：cross-check only |
| HK | Eastmoney HKF10 direct | 三表；prefer provider_api then official_web | **市场数据 primary**（含 AH premium）。财务：cross-check only |
| JP | EDINET official / edinet-tools | EDINET-only route; no J-Quants/Yahoo fallback | 不支持 |
| KR | OpenDART official + local corp_code metadata cache | requires `DART_API_KEY` | 不支持 |
| TW | FinMind public API | 三表 best-effort | 不支持 |
| EU | openesef | ESEF/iXBRL parser route; ticker-only discovery experimental | 不支持 |

**Market Data Provider Matrix**（Lite mode 四层降级链：`Bridge → yfinance → WebSearch → Google Finance`）：

| Market | Layer 1: Bridge | Layer 2: yfinance | Layer 3: WebSearch | Layer 4: Google Finance |
|---|---|---|---|---|
| **US** | ✅ primary — 全字段 | fallback | 兜底 | 兜底 |
| **HK** | ✅ primary — 全字段 + AH premium | fallback | 兜底 | 兜底 |
| **SH/SZ** | ✅ primary — 全字段 | fallback | 兜底 | 兜底 |
| **JP** | ❌ 跳过 | primary — 可接受 | 兜底（搜 `8035 PER 時価総額`） | 兜底 |
| **KR** | ❌ 跳过 | primary — 经常缺字段 | 兜底（搜 `005930 PER 시가총액`） | 兜底 |
| **TW** | ❌ 跳过 | primary — 不稳定 | 兜底（搜 `2330 本益比 市值`） | 兜底 |
| **SE/NL/DE** | ❌ 跳过 | primary — small cap 缺字段 | 兜底（搜 `MYCR PE ratio`） | 兜底 |
| **SG/IN/AU** | ❌ 跳过 | primary | 兜底 | 兜底 |

每个字段独立标 `[source_layer | as-of 日期]`，不设全局 TTL。低层不覆盖高层。

KR / JP source policy:

- KR uses OpenDART official APIs only: a local 30-day metadata cache may store ticker -> corp_code identity mapping under `%LOCALAPPDATA%\buy-side-research-skills\financial-data-cache\dart-corp-code\`, but `fnlttSinglAcntAll.json` statements and `document.xml` full filing ZIP/Markdown are always fetched live. Set `BSRS_DART_CORP_CACHE_REFRESH=1` to force a corp_code metadata refresh. Do not cache KR statements, filing receipt numbers, ZIPs, Markdown, or research results.
- JP uses EDINET official APIs only. Daily document-list metadata may be cached locally to avoid repeated discovery scans, but the source filing remains the EDINET type=1 ZIP and full filing Markdown is only evidence-ready when that ZIP exists.
- Yahoo/yfinance is not a source-tracked `financial-data` provider for JP/KR three statements or filings.
- HK statements use Eastmoney HKF10 direct as the formal statement route. Do not use Longbridge as the HK statement source; Longbridge may supplement market data or consensus only.
- Layer 3 web fallback is priority-split into `official_web -> trusted_web -> broad_web`. `official_web` includes company IR/results pages plus official filing portals such as SEC, EDINET, DART, MOPS, and CNINFO when they are found via search/browser/PDF parsing rather than fetched through a stable provider route.
- Query-chain precedence must reflect that contract: for example `site:sec.gov`, `site:hkexnews.hk`, `site:disclosure.edinet-fsa.go.jp`, `site:dart.fss.or.kr`, `site:mops.twse.com.tw`, and `site:cninfo.com.cn` belong in `official_web`, not `trusted_web`.
- EU `openesef` currently requires a local ESEF package or explicit filing URL for deterministic parsing. If no local ESEF package is available, Lite should skip the `openesef` Layer 2 route and move directly to `official_web` fallback instead of treating the missing local package as a normal statement-provider failure.
- Source-trust ranking is formal: `provider_api + official_web > yfinance > trusted_web + broad_web`. Lower-trust sources must not overwrite higher-trust sources. Provider-fetched official filing caches remain `provider_api`; official company IR/results pages and official filing portals discovered via search remain `official_web`.
- Non-finite numeric placeholders such as `NaN` / `inf` are invalid in `actuals-resolved.json` and must be normalized back to missing before coverage, overwrite, or consumer use. They must not count as filled fields.
- `official_web` may also be materialized as a curated machine-readable cache at `industry/<industry>/companies/<ticker>/_cache/financial-data/internal/_raw/official_web_cache.json` when a company IR/results page or attached official PDF has already been source-read and normalized. Those cache entries stay `official_web`, not `provider_api`, and may carry scalar fields plus structured `segments.status` / `segments.segments`.
- `yfinance` may bootstrap statement fields when provider routes are absent, but only as a lower-trust fill layer. It should not displace existing `provider_api` or `official_web` values.
- Lite consumer-success coverage should optimize `provider_api + official_web` first. Do not rely on `trusted_web` / `broad_web` to make surface-level coverage look complete.
- `provider-gap` must be reasoned rather than generic. Use `provider_unavailable`, `official_source_available_not_extracted`, or `not_disclosed` instead of a single ambiguous gap label.
- Growth-first consumer profile: prioritize revenue, margin, segments, geography, `operating_cf`, and `capex`. Coarse usable debt fields such as `short_term_debt` and `long_term_debt` still matter when they change funding risk or runway; only finer debt detail should be treated as best-effort. Treat `supplementary.order_backlog` as sector-conditional, and treat `supplementary.sbc`, `cash_flow.*.dividends_paid`, `cash_flow.*.share_buybacks`, and fine debt detail as best-effort rather than universal Lite blockers.

Segment rule:

- 只要公司披露了可结构化的 split，优先写回 `actuals-resolved.json` 的 `segments.status` + `segments.segments`，不要只留 pending query。
- `segments.segments` 是通用容器，允许同时承载 `business_line`、`geography`、`end_market` 等不同维度，由 `type` 区分。
- `segments.segments` 可选携带 `pct_of_total`、`yoy_pct`、`sequential_pct`、`margin_pct`、`ratio` 等数量型辅助字段。如果官方披露给的是比例、同比、环比或 margin 而不是绝对值，允许先按这些字段落盘；当 period total、prior-year、prior-period 或 denominator 已知时，runtime 应尽量做可逆推算并补齐缺失锚点。
- `supplementary.revenue_by_geography` 是 geography split 的 consumer convenience view；若披露 geography split，应同步写回或派生。
- 不能结构化抓到时，不新增假 split；明确标 `pending_official_extraction`、`provider_unavailable` 或 `not_disclosed`，不要把不同缺口原因混成单一 `provider-gap`。

## 文件安全

- 不覆盖已有 run-id 目录；同一时间重复运行必须生成新 run-id 或 fail。
- 不写空的 successful pack；数据缺失时写 `provider-gap` / `partial`，或 hard fail，不伪装完整。
- 不创建 `research-journal.md`、`company-history.md`、`driver-map.md` 或 workbook。
- 不把 current topic snapshot 当 canonical company data。
- 不移动用户已有 `_raw/` 文件。
- 缺 dependency 或 credential 时不写假 cache。

## 运行输出契约

```markdown
## Financial Data Result

**结论先行**
[available / partial / provider-gap / failed，一句话说明能否给 3-statement-model / dcf-model / comps-analysis / model-update 使用]

| Data item | Status | Source/provider | Period coverage | Model usable? | Caveat |
|---|---|---|---|---|---|
| Income statement | available / partial / unavailable / provider-gap | [...] | [...] | yes / review / no | [...] |

## Output
- raw: [...]
- cache: [...]
- summary: `_cache/financial-data/financial-data-summary.md`
- internal_machine_inputs: `_cache/financial-data/internal/`
- financial_data_pack_path: [...]

## Provider / Credential
- market: [...]
- identifier_type: [...]
- provider: [...]
- credential_status: [...]

## Caveats
- [...]
```

`available / partial / unavailable / provider-gap` 必须按字段写清。特别是三表和 `revenue_split` 分开标状态。

## 失败处理

- 共享环境入口可先看 `init-workspace`，但本节仍是财务数据环境配置与 honest-fail 边界的细 source of truth。
- 缺 dependency：输出缺什么和 bootstrap 命令，不写 successful cache。
- 缺 `EDGAR_IDENTITY`：US SEC route failed，不声称 SEC/XBRL 可用。
- 缺 `DART_API_KEY`：KR route failed，不写假 DART 数据。
- EU ticker-only 无法 discovery：输出 `provider-gap`，提示改用 `filing_url` 或 `local_esef_package`。
- Topic 不存在：block，提示先用 `new-session` 创建 `industry/<industry>/companies/<ticker>/` 或目标 topic。
- Provider 返回字段缺失：写 partial pack 和 completeness matrix，不推断未披露 revenue split。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| 用户只有本地 PDF / XLSX / CSV | 交给 `ingest` |
| 用户要按 ticker / filing package 拉结构化财报 | 使用 `financial-data` |
| 用户要解释 revenue bucket 或 driver | `financial-data` 后交给 `driver-map` |
| 用户要建模、DCF、comps、更新 workbook | `financial-data` 可作为 optional input 给 `3-statement-model / dcf-model / comps-analysis / model-update` |
| theme / industry 需要一篮子公司数据 | 用 `current_topic_snapshot`，并链接 canonical company pack |
| 数据缺口影响模型或研究优先级 | `next-step` / `driver-map` / `company-history` |

Artifact policy：

- `save_policy`: `cache_artifact`
- `default_artifact`: `financials.md`
- `canonical_location`: `topics/company/[company-slug]/_cache/datasets/financial-data/[market]/[canonical-id]/[run-id]/`

## 安全自查

- ❌ 把 provider-normalized field 写成 company disclosed fact。
- ❌ 不推断未披露 revenue split，却在缺 segment 时用历史比例补齐。
- ❌ 三表 available 就默认 model-ready。
- ❌ EU ticker-only 找不到 filing 还声称 openesef 支持完整欧洲股票拉取。
- ❌ 缺 `DART_API_KEY` 还写韩国财报 cache。
- ❌ 缺 `EDGAR_IDENTITY` 还声称 SEC route 完整。
- ❌ 把 theme snapshot 当 canonical company data。
- ❌ 写 research conclusion、forecast、DCF 或 price target。
- ❌ 不输出 `completeness.json` 或 `source-map.json`。
- ❌ 有官方 filing source 却不写 `identity-source.json`、`source-metadata.json` 或 `source.sha256`。
- ❌ 覆盖已有 run-id 目录。
