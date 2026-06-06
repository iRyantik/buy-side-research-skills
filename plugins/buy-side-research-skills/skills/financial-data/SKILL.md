---
name: financial-data
description: Acquire evidence and commit source-tracked canonical financial facts.
---

# Financial Data

`financial-data` 是统一采集与 canonical facts pipeline。Provider、PDF extractor、网页补缺和 hook 只能生成 candidates；只有 `FactsRepository` 可以写 canonical store。`actuals-resolved.json` 永久保留，但只是生成式只读兼容视图。

## CLI

```powershell
python _scripts/financial-data.py fetch <ticker> --profile lite
python _scripts/financial-data.py fetch <ticker> --profile full
python _scripts/financial-data.py fetch <ticker> --profile lite --from FY2018 --to FY2025
python _scripts/financial-data.py fetch <ticker> --profile full --from 2022-01-01 --to latest
python _scripts/financial-data.py render <ticker>
python _scripts/financial-data.py migrate <ticker|--all>
python _scripts/financial-data.py check-deps [--group <name>]
```

不传 `--market` 时，CLI 会按常见 ticker suffix/形态做 best-effort market inference；fresh workspace 没有 company topic 时，`fetch` 会创建 `industry/uncategorized/companies/<ticker>/` 作为默认落点，避免 `stock-quickread` 的 0→1 流程卡在手工建目录。

## Lite / Full

Lite/Full 只控制字段宽度、文档深度、evidence 和验证强度，不控制时间范围。

| 维度 | Lite | Full |
|---|---|---|
| 默认期间 | 最新完整 FY + 最新 interim | 最近 5 个完整 FY + 当前 FY interim |
| 自定义期间 | 任意 `--from/--to` | 任意 `--from/--to` |
| 字段 | 核心三表、主要 segments、关键 supplementary | 请求范围内全部可映射标准字段 |
| 文档 | 定向补缺 | 完整获取、转换、索引 |
| 验证 | 核心 gate、期间、单位、主要冲突 | 全字段 reconciliation、完整性、审计 |

`--from/--to` 按 `period_end` 包含式筛选，支持 `earliest`、`latest`、`YYYY-MM-DD`、`FY2024`。旧 `--periods 3Y` 只保留一版本，解释为最近三个可用完整 FY 加当前 interim。

## Stores

```text
_cache/financial-data/internal/
  facts-store.json
  market-snapshots.jsonl
  consensus-snapshots.jsonl
  actuals-resolved.json

_cache/datasets/financial-data/<provider>/<run-id>/
_raw/datasets/financial-data/<provider>/<run-id>/
```

Canonical fact 必须包含 metric、period_id、value、unit、currency、dimensions、source_id、source_layer、status、confidence。缺失不得填零；derived 必须标记；低信任来源不得静默覆盖高信任来源；冲突必须保留。

## Pipeline

```text
resolve identity
→ resolve requested time range
→ acquire provider/source evidence
→ normalize fact candidates
→ merge by trust/period/unit policy
→ reconcile and validate
→ atomically commit canonical stores
→ generate compatibility and human views
```

本地 PDF/XLSX/CSV 先交给 Source Intake 注册和转换，再作为带 source ID、页码/原始标签、期间、单位和 confidence 的 candidates 进入 pipeline。
