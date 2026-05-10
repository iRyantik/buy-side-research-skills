---
name: ingest
description: Use when converting raw research materials such as PDF, XLSX, PPTX, DOCX, TXT, CSV, or markdown files into workspace _cache markdown before analysis.
---

# Ingest

`ingest` 把 research workspace 里的 raw material 转成 `topics/<topic>/_cache/` 下的 LLM-friendly markdown，并写清 source path、hash、modified time、converter、converted time、document type、route 和 precision caveat。

它是 operations skill，不是研究 skill。它不生成投资结论，不把 `_cache/` 当 original source，不写 `research-journal`，不静默安装依赖。转换失败时必须 fail honestly，不写假 cache。

## 心法

`ingest` 的核心 invariant 是材料可读性和可追溯性。很多幻觉不是发生在 thesis 阶段，而是发生在最前面：PDF 表格错读、Excel 公式和值混在一起、PPT notes 丢失、扫描件被当成文本层。

能安全转换就转换；不能安全转换就失败并说明缺什么。`_cache/` 永远只是 operational cache，关键数字、引语和页码仍然必须回查原始 source。

## 职责边界

负责：
- 检测 TXT / Markdown / CSV / PDF / DOCX / PPTX / XLSX / XLSM / XLS 格式。
- 调用 `ingest.py`、`ingest_xlsx.py`、`ingest_table_crosscheck.py`。
- 写入 `topics/<topic>/_cache/[source-filename].md`。
- 输出 converted / skipped / failed summary。
- 报告 dependency gap 和 precision caveat。
- **ingest 成功后自动将源文件从 `_inbox/` 移至 `topics/<topic>/_raw/<ext>/`。**

不负责：
- 不移动、删除、重命名已在 `topics/<topic>/_raw/` 下的源文件。
- 不验证 claim 是否真实；claim check 交给 `information-impact`。
- 不解释公司业务；公司基础交给 `company-primer`。
- 不拆 driver；driver gap 交给 `driver-map`。
- 不沉淀 earned insight；memory 交给 `research-journal`。
- 不自动安装 Docling、PyMuPDF4LLM、EdgarTools、AKShare、edinet-tools、dart-fss、openesef 或 Python packages。

## 触发与输入

触发语：
- “ingest this”
- “消化这个文件”
- “转成 markdown”
- “处理 `_inbox/`”
- “把 PDF / XLSX / PPTX / DOCX 放进 `_cache/`”

### Pre-condition

**ingest 前 topic 必须已存在。** 若 `topics/<topic>/index.md` 不存在 → block，提示先运行 `new-session` 创建 topic scaffold。例外：workspace root `_inbox/` 的未分类文件不 block（topic = `unclassified`）。

输入确认：
- `source_path`：文件或目录路径。**优先使用 `topics/<topic>/_inbox/`**（将文件放入对应 topic 的 inbox）；workspace root `_inbox/` 仅用于未分类文件。
- `workspace`：默认从 source path 向上寻找含 `topics/` 且含 `_inbox/` 的 workspace；找不到时要求 `--workspace`。
- `topic`：Topic slug，用于组织 `topics/<topic>/_raw/` 和 `topics/<topic>/_cache/`（如 `aerospace`）。从 `topics/<topic>/_inbox/` 路径自动推断，或用 `--topic` 显式传入。
- `category`：文档类别（`filings`、`transcripts`、`sellside`、`industry`、`irdecks`、`datasets`）。默认自动推断（文件名 + 内容检测），也可显式传入 `--category`。
- `force`：默认已有 cache 且 hash 一致就 skip；只有用户要求重跑才 overwrite。

### Topic 分类

1. 用户显式传入 `--topic` → 直接使用。
2. `source_path` 在 `topics/<topic>/_inbox/` 下 → 自动推断 topic slug。
3. 当前有活跃 topic session → 自动推断。
4. 以上都不可用 → 使用 `"unclassified"` 作为 fallback。

### 文档类别推断

| 优先级 | 逻辑 |
|---|---|
| 1 | 用户显式传 `--category filings` |
| 2 | 文件名含 `10-K/10-Q/20-F/8-K/annual` → `filings` |
| 3 | 文件名含 `transcript/call/earnings` → `transcripts` |
| 4 | 文件名含 `deck/presentation/investor` → `irdecks` |
| 5 | 文件名含 `initiation/rating/target` → `sellside` |
| 6 | 文件名含 `industry/market report/outlook` → `industry` |
| 7 | 扩展名 `.xlsx/.xls/.csv` → `datasets` |
| 8 | SEC filing header 检测 → `filings` |
| 9 | fallback → `unclassified` |

## 执行模式

### Dependency Check

运行：

```powershell
python _scripts/ingest.py --check-deps
_scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

用户显式确认后才运行 `_scripts/bootstrap-ingest-deps.ps1 -Yes`。

### Single File Ingest

单文件转换。PDF 文字为主用 PyMuPDF4LLM，表格密集用 docling；SEC filing 检查 EdgarTools / EDGAR_IDENTITY readiness；扫描 PDF 尝试 docling → PyMuPDF4LLM fallback，标注 Claude Vision review caveat；XLSX / XLSM 用 openpyxl；legacy `.xls` 需先转为 `.xlsx`。

### Directory Ingest

处理 `_inbox/` 或 `topics/<topic>/_raw/` 目录。单个文件失败不阻塞其他文件，但最后必须列出 failed files。

### Cache Reuse Check

检查 cache 是否存在，并用 source hash 判断是否可复用。hash 不一致时提示 `--force` 重跑。

## 工具资源

本 skill 使用：
- `skills/ingest/scripts/ingest.py`
- `skills/ingest/scripts/ingest_xlsx.py`
- `skills/ingest/scripts/ingest_table_crosscheck.py`
- `skills/ingest/scripts/bootstrap-ingest-deps.ps1`
- `skills/ingest/assets/requirements-ingest.txt`

核心依赖：Docling、PyMuPDF4LLM、EdgarTools、AKShare、edinet-tools、dart-fss、openesef、openpyxl、python-pptx、python-docx、PDFPlumber、pypdf、Pillow。依赖安装必须由用户显式 opt in。

### PDF 双层路由

| 文档特征 | 工具 | 说明 |
|---|---|---|
| 文字为主（transcripts、IR deck 文本页） | **PyMuPDF4LLM** | CPU 即可，10-50x 速度优势 |
| 表格密集（10-K、招股书、含并格表格） | **docling** | 258M VLM，MIT 许可证 |
| SEC filing | **docling + EdgarTools** | EdgarTools XBRL 就绪后走 docling narrative |
| 扫描件（OCR required） | **docling → PyMuPDF4LLM fallback** | 标注 precision caveat，关键文件建议 Claude Vision review |

### 按市场结构化数据

| 市场 | 工具 | 状态 |
|---|---|---|
| A股 + 港股 | AKShare | 19.1k stars，活跃 |
| 日本 | edinet-tools | EDINET 公司财务数据 |
| 韩国 | dart-fss | DART 披露系统 |
| 欧洲 | Arelle + openesef | ESMA 使用，ESEF XBRL |
| 台湾 | mops-financial-api | 原型，iXBRL only `[gap]` |
| 英国 | 无成熟工具 | `[gap]`，需 Arelle DIY |
| 美股 | EdgarTools | 成熟 |

## 文件安全

- 不删除、不重命名 `topics/<topic>/_raw/` 内已有源文件。
- ingest 成功后将 `_inbox/` 内的源文件自动移至 `topics/<topic>/_raw/<ext>/`。
- 不写空 cache 或假 cache。
- 不把 `_cache/` 写进 topic session。
- 不把 `_cache/` 当 original source。
- 默认不 recursive；用户明确要求时才递归。
- 缺 Docling、PyMuPDF4LLM、EdgarTools、openpyxl 等 parser dependency 时，必须报告 dependency gap。

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
- workspace 无法发现：要求传 `--workspace` 或先运行 `init-workspace`。
- 扫描 PDF 缺 docling 和 pymupdf4llm：failed，标注建议 Claude Vision review。
- SEC filing 缺 `EDGAR_IDENTITY`：标记 SEC route 不完整；不要声称 XBRL route 已完成。
- Docling 和 PyMuPDF4LLM 均失败且无 pypdf fallback：failed，不写假 markdown。

## Workflow 联动

| 场景 | 处理 |
|---|---|
| workspace 还没有 `topics/` | 先用 `init-workspace` |
| dependency 缺失 | `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly`，用户确认后 `-Yes` |
| cache 生成后要判断 claim 可信度 | `information-impact` |
| cache 是 annual report / 10-K / 20-F | `company-primer` 或 `driver-map` |
| cache 是 industry report / technical paper | `mechanism-map` |
| cache 是 financial model workbook | `financial-model` |
| 研究已经想清楚 | `research-journal` |
| 研究 skill 需要发现已 ingest 材料 | 检查 `topics/<topic-slug>/_cache/` |

Artifact policy：
- `save_policy`: `cache_artifact`
- `default_artifact`: `[source-filename].md`
- `canonical_location`: `topics/[topic]/_cache/[source-filename].md`

## 安全自查

- ❌ 缺 dependency 还说转换完成。
- ❌ 自动静默安装依赖。
- ❌ 把 cache markdown 当原始 source。
- ❌ 在 ingest 阶段总结投资结论。
- ❌ 移动、删除、改名 `topics/<topic>/_raw/` 下已有文件。
- ❌ 默认递归整个 workspace。
- ❌ 把 `_cache/` 内容写进 `research-journal`。
- ❌ PDF / Excel 数字不写 precision caveat。
- ❌ 扫描 PDF 缺 converter 还写假 cache。
- ❌ SEC filing 缺 `EDGAR_IDENTITY` 还声称 XBRL route 完整。
- ❌ 不传 `--topic` 且无法推断时静默使用 `unclassified`，应提示用户确认。
