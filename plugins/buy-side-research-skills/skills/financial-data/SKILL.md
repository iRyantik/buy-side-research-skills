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
- 不拉 consensus、price、EV、FX、peer multiples 或 market data。
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

触发语： 或 

Lite 模式不做 full filing 解析，不建 evidence pack。只抓 22 个三表核心科目 + 分部收入/利润 + 市场快照数据，写入 。目标是 **stock-quickread / bear-pre-mortem / comps-analysis / earnings-setup / consensus-map / alpha-thesis / cross-market-compare** 启动前的最少必要数据。

**数据获取逻辑**：



****Lite 写入的最小字段**：

| 类别 | 内容 | 状态 |
|---|---|---|
| 三表 | 22 个核心科目（IS/BS/CF） | 必填 |
| 分部 | 分部收入 + 利润（如有） | 必填 |
| 市场数据 | 股价、市值、PE/PB/PS、Beta | 必填——yfinance |
| 股价历史 | 1 年期日线（驱动因素分析） | 必填——yfinance |
| Consensus | EPS/Revenue 预期 | best-effort——缺则标 [ND] |
| 补充 | 股本、SBC、backlog | 有则抓 |


**数据完整性规则**：

- ADR/双重股权/H+A：写入  字段
- 数据新鲜度：存 ，超 6 个月标 
- 未覆盖市场（SG/AU/IN/SEA）：yfinance 先拉，缺的标 
- 单位归一化：AKShare 万元→元、EDINET 百万円→円、韩网 억원→원

**输出**（精简版）：



Lite 不写 、、、。


### Fill-Gaps Mode（补 Layer 3 缺口）

触发语：

读完  后，只对  的字段调 provider API 补填。不做 full filing 解析，不建 evidence pack。

流程：读 actuals → 遍历 null 字段 → 按 market 路由 provider（US→EdgarTools, CN→AKShare, JP→EDINET, KR→OpenDART, TW→FinMind, EU→openesef）→ 填值 → 写回。填不了的标 [ND]。5-10 秒/公司。

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

- `skills/financial-data/scripts/financial_data.py`
- `skills/financial-data/scripts/bootstrap-financial-data-deps.ps1`
- `skills/financial-data/scripts/providers/sec_provider.py`
- `skills/financial-data/scripts/providers/akshare_provider.py`
- `skills/financial-data/scripts/providers/edinet_provider.py`
- `skills/financial-data/scripts/providers/dart_provider.py`
- `skills/financial-data/scripts/providers/openesef_provider.py`
- `skills/financial-data/assets/requirements-financial-data.txt`

Provider matrix：

| Market | Provider | V1 status |
|---|---|---|
| US | EdgarTools / SEC | 三表 + filing markdown + SEC XBRL dimension `revenue_split` when available; split completeness is review-only |
| CN A-share | AKShare / Eastmoney | 三表 + `stock_zygc_em` 收入拆分；provider-normalized route |
| HK | Eastmoney HKF10 direct | 三表；正式披露频率通常是 FY + H1/H2，provider rows must keep `period_basis_by_period`; segment / geography split best-effort, prefer provider_api then official_web |
| JP | EDINET official / edinet-tools | EDINET-only route; no J-Quants/Yahoo fallback; `latest4q` can be partial but must not hang or fake complete coverage |
| KR | OpenDART official + local corp_code metadata cache | requires `DART_API_KEY`; ticker -> corp_code uses a 30-day local metadata cache, while statements and full filings are fetched live from official APIs |
| TW | FinMind public API | 三表 best-effort；segment / geography split best-effort, prefer provider_api then official_web |
| EU | openesef | ESEF/iXBRL parser route; ticker-only discovery experimental |

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
