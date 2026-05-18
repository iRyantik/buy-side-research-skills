---
name: financial-data
description: Use when fetching or parsing structured company financial data by market and identifier, including SEC, AKShare, EDINET, DART, or openesef/ESEF routes, before modeling or research analysis.
---

# Financial Data

`financial-data` 把各市场可机器读取的财务数据变成 source-tracked evidence pack。它是 operations skill，不是研究 skill：只负责拉取、解析、标准化、标注完整性和写入 `_cache/datasets/financial-data/`，不解释投资含义、不做 forecast、不替代 `driver-map` 或 `3-statement-model / dcf-model / comps-analysis / model-update`。

核心产物不是“看起来完整的三表”，而是“哪些字段真的可用、来自哪里、能不能进模型”。如果 provider 没有 segment revenue、geography split、share count 或 net debt，本 skill 必须把缺口写进 `completeness.json` 和 `financials.md`，不能用推断补齐。

## 心法

财务数据拉取最容易出错的地方，不是 API 报错，而是数据看起来太整齐：provider-normalized label 被误当作公司原始披露，segment bucket 被自动合并，ticker-only 路由找错实体，或三表可得但模型真正需要的 revenue split 缺失。

本 skill 的工作逻辑是 **provenance first + completeness before model use**。先保存 raw provider payload，再保存 normalized evidence pack；日常外显只给 `financial-data-summary.md`，机器输入和审计文件进入 `internal/`；先告诉研究员缺什么，再让 `driver-map` 和 `3-statement-model / dcf-model / comps-analysis / model-update` 判断能否建模。

`financial-data` 服务 topic-centric 架构：单公司数据默认落在 `topics/company/<company-slug>/`；theme / industry topic 只保存 snapshot 或 links，不变成第二套公司主档。

## 职责边界

负责：

- 按 `market`、`identifier`、`identifier_type`、`company_slug` 拉取或解析结构化财务数据。
- 默认写入 canonical company topic：`topics/company/<company-slug>/_cache/datasets/financial-data/<market>/<canonical-id>/<run-id>/`。
- 保存 raw provider payload 到 `_raw/datasets/financial-data/`，保存 normalized evidence pack 到 `_cache/datasets/financial-data/`。
- raw evidence 层至少包含 `provider_payload.json`、`identity-source.json`；存在真实 filing source 时还要写 `filings/<filing-id>/source.*`、`source-metadata.json`、`source.sha256`。
- 生成 public `financial-data-summary.md`；机器文件进入 `internal/`，包括 `evidence-pack.json`、`actuals-resolved.json`、`full-filing.md`、`manifest.json`、`financials.md`、`financials.normalized.json`、`completeness.json`、`source-map.json` 和 `cross-check.json`。
- 输出字段级 completeness matrix：三表、segment revenue、geography split、share count、net debt 分开标状态。
- 支持 current topic snapshot：`topics/<topic>/_cache/datasets/financial-data-snapshot/<run-id>/`。
- 对 dependency gap、credential gap、provider gap fail honestly。

不负责：

- 不做公司业务解释、driver 判断、revenue split 推断或 segment 真实经济含义判断；交给 `company-primer` / `driver-map`。
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
| `market` | `us` / `cn` / `hk` / `jp` / `kr` / `eu` | 必填 |
| `identifier` | ticker、CIK、EDINET code、DART corp code、LEI、filing URL 等 | 必填 |
| `identifier_type` | `ticker` / `isin` / `lei` / `cik` / `edinet_code` / `dart_corp_code` / `filing_url` / `local_esef_package` | 默认 `ticker` |
| `periods` | `latest`、`FY2021-FY2025`、`quarterly` 等 | 默认 `latest` |
| `items` | 三表、segment revenue、geography split、share count、net debt | 默认全取 |
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
topics/company/<company-slug>/
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

`_cache/financial-data/financial-data-summary.md` 是人和 LLM 的默认入口。`_cache/financial-data/internal/actuals-resolved.json` 是 `3-statement-model`、`dcf-model`、`comps-analysis` 和 `model-update` 读取 historical actuals 的推荐机器入口；missing / unmapped 字段不得写成 0。`internal/evidence-pack.json` 聚合 completeness、source map 和 cross-check；只有审计或 debug 时才直接打开 run-id pack。

如果 `topics/company/<company-slug>/index.md` 不存在，block 并提示先用 `new-session` 创建 company topic；不要静默创建复杂 topic 树。

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
| US | EdgarTools / SEC | dependency + credential gated |
| CN / HK | AKShare | provider-normalized route |
| JP | edinet-tools | EDINET route; field coverage may be partial |
| KR | dart-fss | requires `DART_API_KEY` |
| EU | openesef | ESEF/iXBRL parser route; ticker-only discovery experimental |

## 文件安全

- 不覆盖已有 run-id 目录；同一时间重复运行必须生成新 run-id 或 fail。
- 不写空的 successful pack；数据缺失时写 `provider-gap` / `partial`，或 hard fail，不伪装完整。
- 不创建 `research-journal.md`、`company-primer.md`、`driver-map.md` 或 workbook。
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

`available / partial / unavailable / provider-gap` 必须按字段写清。特别是三表、segment revenue、geography split、share count、net debt 分开标状态。

## 失败处理

- 缺 dependency：输出缺什么和 bootstrap 命令，不写 successful cache。
- 缺 `EDGAR_IDENTITY`：US SEC route failed，不声称 SEC/XBRL 可用。
- 缺 `DART_API_KEY`：KR route failed，不写假 DART 数据。
- EU ticker-only 无法 discovery：输出 `provider-gap`，提示改用 `filing_url` 或 `local_esef_package`。
- Topic 不存在：block，提示先用 `new-session` 创建 `topics/company/<company-slug>/` 或目标 topic。
- Provider 返回字段缺失：写 partial pack 和 completeness matrix，不推断未披露 revenue split。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| 用户只有本地 PDF / XLSX / CSV | 交给 `ingest` |
| 用户要按 ticker / filing package 拉结构化财报 | 使用 `financial-data` |
| 用户要解释 revenue bucket 或 driver | `financial-data` 后交给 `driver-map` |
| 用户要建模、DCF、comps、更新 workbook | `financial-data` 可作为 optional input 给 `3-statement-model / dcf-model / comps-analysis / model-update` |
| theme / industry 需要一篮子公司数据 | 用 `current_topic_snapshot`，并链接 canonical company pack |
| 数据缺口影响模型或研究优先级 | `next-step` / `driver-map` / `company-primer` |

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
