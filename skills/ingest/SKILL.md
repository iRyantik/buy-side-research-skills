---
name: ingest
description: Use when converting raw research materials such as PDF, XLSX, PPTX, DOCX, TXT, CSV, or markdown files into workspace _cache markdown before analysis.
---

# Ingest

`ingest` 把 research workspace 里的 raw material 转成 `_cache/` 下的 LLM-friendly markdown，并写清 source path、hash、modified time、converter、converted time、document type、route 和 precision caveat。

它是 operations skill，不是研究 skill。它不生成投资结论，不把 `_cache/` 当 original source，不写 `research-journal`，不静默安装依赖。转换失败时必须 fail honestly，不写假 cache。

## 心法

`ingest` 的核心 invariant 是材料可读性和可追溯性。很多幻觉不是发生在 thesis 阶段，而是发生在最前面：PDF 表格错读、Excel 公式和值混在一起、PPT notes 丢失、扫描件被当成文本层。

能安全转换就转换；不能安全转换就失败并说明缺什么。`_cache/` 永远只是 operational cache，关键数字、引语和页码仍然必须回查原始 source。

## 职责边界

负责：
- 检测 TXT / Markdown / CSV / PDF / DOCX / PPTX / XLSX / XLSM / XLS 格式。
- 调用 `ingest.py`、`ingest_xlsx.py`、`ingest_table_crosscheck.py`。
- 写入 `_cache/[bucket]/[source-filename].md`。
- 输出 converted / skipped / failed summary。
- 报告 dependency gap 和 precision caveat。

不负责：
- 不移动、删除、重命名 raw source。
- 不验证 claim 是否真实；claim check 交给 `information-impact`。
- 不解释公司业务；公司基础交给 `company-primer`。
- 不拆 driver；driver gap 交给 `driver-map`。
- 不沉淀 earned insight；memory 交给 `research-journal`。
- 不自动安装 Docling、EdgarTools、Tesseract、MarkItDown 或 Python packages。

## 触发与输入

触发语：
- “ingest this”
- “消化这个文件”
- “转成 markdown”
- “处理 `_inbox/`”
- “把 PDF / XLSX / PPTX / DOCX 放进 `_cache/`”

输入确认：
- `source_path`：文件或目录路径；除非用户要求 `--recursive`，目录默认只处理第一层。
- `workspace`：默认从 source path 向上寻找含 `_cache/` 且含 `_raw/` 或 `_inbox/` 的 workspace；找不到时要求 `--workspace`。
- `bucket`：默认从 `_raw/[category]/[bucket]/...` 推断，否则用 `inbox` 或 `unclassified`。
- `force`：默认已有 cache 且 hash 一致就 skip；只有用户要求重跑才 overwrite。

## 执行模式

### Dependency Check

运行：

```powershell
python _scripts/ingest.py --check-deps
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

用户显式确认后才运行 `_scripts/bootstrap-ingest-deps.ps1 -Yes`。

### Single File Ingest

单文件转换。PDF 用 Docling primary；SEC filing 检查 EdgarTools / EDGAR_IDENTITY readiness；扫描 PDF 需要 Tesseract OCR；XLSX / XLSM 用 openpyxl；legacy `.xls` 可用 MarkItDown fallback。

### Directory Ingest

处理 `_inbox/` 或 `_raw/` 目录。单个文件失败不阻塞其他文件，但最后必须列出 failed files。

### Cache Reuse Check

检查 cache 是否存在，并用 source hash 判断是否可复用。hash 不一致时提示 `--force` 重跑。

## 工具资源

本 skill 使用：
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.ps1`
- `skills/ingest/assets/requirements-ingest.txt`

核心依赖包括 Docling、EdgarTools、MarkItDown、openpyxl、python-pptx、python-docx、PDFPlumber、pypdf、pytesseract 和 Pillow。依赖安装必须由用户显式 opt in。

## 文件安全

- 不删除、不移动、不重命名 raw source。
- 不写空 cache 或假 cache。
- 不把 `_cache/` 写进 topic session。
- 不把 `_cache/` 当 original source。
- 默认不 recursive；用户明确要求时才递归。
- 缺 OCR、Docling、EdgarTools、MarkItDown 或 parser dependency 时，必须报告 dependency gap。

每个 cache header 必须包含：
- `source_path`
- `source_sha256`
- `source_modified_utc`
- `converter`
- `converted_at_utc`
- `precision`
- `precision_level`
- `document_type`
- `route`

## 运行输出契约

```markdown
## Ingest Result

**结论先行**
[converted / skipped / failed 的一句话结论]

| Source | Cache | Status | Converter | Precision |
|---|---|---|---|---|
| [...] | [...] | [...] | [...] | [...] |

## Route / Dependency
- document_type: [...]
- route: [...]
- precision_level: [...]
- page_count / table_count: [...]
- dependency_status: [...]

## Caveats
- [...]
```

## 失败处理

- 缺 dependency：输出缺什么、如何 `-CheckOnly` / `-Yes`，不写 cache。
- source path 不存在：直接 failed。
- workspace 无法发现：要求传 `--workspace` 或先运行 `init`。
- 扫描 PDF 缺 Tesseract：failed，不写 `[no extractable text]` cache。
- SEC filing 缺 `EDGAR_IDENTITY`：标记 SEC route 不完整；不要声称 XBRL route 已完成。
- Docling 失败且没有安全 fallback：failed，不写假 markdown。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| workspace 还没有 `_cache/` / `_raw/` | 先用 `init` |
| dependency 缺失 | `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly`，用户确认后 `-Yes` |
| cache 生成后要判断 claim 可信度 | `information-impact` |
| cache 是 annual report / 10-K / 20-F | `company-primer` 或 `driver-map` |
| cache 是 industry report / technical paper | `mechanism-map` |
| cache 是 financial model workbook | `financial-model` |
| 研究已经想清楚 | `research-journal` |

Artifact policy：
- `save_policy`: `cache_artifact`
- `default_artifact`: `[source-filename].md`
- `canonical_location`: `_cache/[bucket]/[source-filename].md`

## 安全自查

- ❌ 缺 dependency 还说转换完成。
- ❌ 自动静默安装依赖。
- ❌ 把 cache markdown 当原始 source。
- ❌ 在 ingest 阶段总结投资结论。
- ❌ 自动删除、移动、改名 raw 文件。
- ❌ 默认递归整个 workspace。
- ❌ 把 `_cache/` 内容写进 `research-journal`。
- ❌ PDF / Excel 数字不写 precision caveat。
- ❌ 扫描 PDF 缺 OCR 还写假 cache。
- ❌ SEC filing 缺 `EDGAR_IDENTITY` 还声称 XBRL route 完整。
