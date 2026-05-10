---
name: ingest
description: Use when converting raw research materials such as PDF, XLSX, PPTX, DOCX, TXT, CSV, or markdown files into workspace _cache markdown before analysis.
---

## Global Rules Capsule (v1)

本 skill 独立运行时也必须遵守以下全局规则；维护源是 `skills/_shared/global-rules.md`，该文件尽量使用 `CLAUDE.md` 原文。

- 默认用中文自然语言输出；ticker、公司名、产品名、source title、URL、YAML / JSON key、财务和行业术语可以保留英文。所有分析必须结论先行，不要写 "Great question"、"你说得对"、"It depends" 这类空铺垫。
- 每一条事实声明、数字、引语必须有 source link 或明确 source 描述。财务数字、估值、市场数据、KPI、运营数据、行业数据、管理层引语、专家访谈、监管表态、第三方判断、历史事件和时间点必须有 source。研究员判断本身不需要 source，但判断依据的事实必须有 source。
- 能用一手原始 source 就不用二手；多个 source 冲突时必须标注冲突，不要挑一个顺手的用。不确定时直接说不确定，并标 `[需查证]` 或 `[来源待补]`；不确定 URL 是否存在时写 `[link 待补]`。
- 绝对不能编造 URL、页码、引语、数字、人名、日期。sub-agent 或其他 AI 给出的 URL 一律视为 `[agent-provided, 未验证]`，关键 link 必须人工抽查 URL 和 claim 是否匹配。
- 不要写 sell-side 流水账：公司历史、管理层履历、行业科普、通用 SWOT、无数据定性、表格复述。数据表必须有 takeaway，且 takeaway 必须给结构性洞察，不要复读表格。
- 主动执行 Senior Analyst Radar：当疑点可能改变业务实质理解、model driver、市场预期 / consensus framing、peer group / 估值框架或下一步研究优先级时，直接点破。
- 遇到行业机制、工程原理、设备链条、工艺流程、术语或 know-how gap，先 handoff / 触发 `mechanism-map`；遇到 revenue / margin / backlog / price-volume-mix driver、披露口径异常或 model-driver gap，先 handoff / 触发 `driver-map`。

# Ingest

`ingest` 负责把 research workspace 里的 raw material 转成 `_cache/` 下的 LLM-friendly markdown，并写清 source path、hash、转换工具、转换时间、文档类型、路由和精度 caveat。它是研究前的材料消化入口，不是研究结论生成器。

如果本 skill 在没有转换成功的情况下开始总结文件内容、把 OCR / PDF 表格当成 verified facts、把 `_cache/` 产物写进 `research-journal`，或在缺依赖时假装已经处理完成，它就失败了。

## 心法

`ingest` 的价值是把“材料能不能被 AI 安全读取”这件事从研究判断里拆出来。很多幻觉不是发生在 thesis 阶段，而是发生在最前面：PDF 表格没读准、Excel 公式和值混在一起、PPT speaker notes 丢了、扫描件被当成文本层。

本 skill 不追求一次性完美解析所有格式，而追求诚实、可复查、可缓存。能转的就转；不该转的就失败，不写假 cache；缺依赖时先引导用户运行 opt-in bootstrap，而不是偷偷安装。任何 `_cache/` 结果都只是中间材料，关键数字仍然必须回查原始 source。

## Source 政策

全局 source / anti-hallucination 规则已内嵌在 `Global Rules Capsule (v1)`。本节只补充 ingest-specific 要求。

特别强调：
- `_cache/` markdown 不是事实 source；事实 source 仍然是 `_raw/` 或用户提供的原始文件。
- 每个 cache 文件头部必须记录 `source_path`、`source_sha256`、`source_modified_utc`、`converter`、`converted_at_utc`、`precision`、`precision_level`、`document_type` 和 `route`。
- PDF / OCR / spreadsheet 转换结果必须带 precision caveat，不得把转换文本当成 verified financial data。
- 对财务表格、KPI、页码、管理层原话等关键 claim，后续研究必须回到原始文件核对。
- `Docling` / `EdgarTools` / `MarkItDown` / `Tesseract` 缺失时，必须输出 dependency gap；只有用户明确运行 `bootstrap-ingest-deps.ps1` 才安装依赖。

## AI 的局限

| 局限 | 影响 | Mitigation |
|---|---|---|
| **PDF 表格错读** | 数字、列名、单位可能错位 | `Docling` 主转换；必要时用 `PDFPlumber` 的 `ingest_table_crosscheck.py` |
| **SEC filing 数字污染** | PDF narrative 与 XBRL financials 混用 | 10-K / 10-Q / 8-K / 20-F 触发 `EdgarTools` readiness；财务数仍需回查 XBRL / filing |
| **扫描件无文本层** | 直接提取会失败或漏字 | 触发 `Docling` + `TesseractCliOcrOptions`；缺 Tesseract 时失败，不写 cache |
| **Excel 公式误读** | 公式和值、hidden sheet、单位可能混乱 | 用 `ingest_xlsx.py` 输出 sheet map、非空区域和 formula topology |
| **PPT notes 丢失** | 只读 slide text 会漏 speaker notes | `Docling` 主转换，`python-pptx` 补 notes；否则标 dependency gap |
| **缓存污染** | 旧 cache 被当成最新材料 | cache header 记录 hash 和 modified time；重复运行默认 skip |

## 触发场景

- “ingest this”
- “消化这个文件”
- “把这份材料转成 markdown”
- “处理 `_inbox/`”
- “把 PDF / XLSX / PPTX / DOCX 放进 `_cache/`”
- “转换这个 annual report / IR deck / model / transcript”

### 不应触发

- 用户要研究公司到底做什么 → `company-primer`。
- 用户要判断 claim 是否可信 → `information-impact`。
- 用户要拆 revenue / margin / backlog driver → `driver-map`。
- 用户要沉淀研究结论 → `research-journal`。
- 用户还没有 research workspace → 先 `init`。

## 输入澄清要求

| 输入 | 必需性 | 默认处理 |
|---|---|---|
| **source path** | 必需 | 文件或目录路径；目录默认只处理一层，除非用户要 recursive |
| **workspace path** | 可选 | 默认从 source path 向上寻找含 `_cache/` 的 workspace |
| **bucket** | 可选 | 默认从 `_raw/[category]/[bucket]/...` 推断；否则用 `unclassified` |
| **force** | 可选 | 默认若 cache 已存在就 skip；用户要求重跑才 overwrite |
| **format expectation** | 可选 | 默认按扩展名检测；source 类型不确定时标 unknown |

## 模式设计

运行入口：优先调用 `skills/ingest/scripts/ingest.py`；Excel 结构化由 `ingest_xlsx.py` 辅助，表格数值抽查由 `ingest_table_crosscheck.py` 辅助，依赖清单是 `requirements-ingest.txt`，依赖安装由用户显式运行 `bootstrap-ingest-deps.ps1`。

### Mode 0: Dependency Bootstrap / Check

用于用户刚初始化 workspace 或 ingest 失败提示缺依赖。

要求：
- 先运行 `python _scripts/ingest.py --check-deps` 或 `_scripts/bootstrap-ingest-deps.ps1 -CheckOnly`。
- 用户明确同意后才运行 `_scripts/bootstrap-ingest-deps.ps1 -Yes`。
- Python 包默认安装到 user site；Tesseract 走 winget / Chocolatey / UB Mannheim fallback；不要求管理员权限。
- 未提供 `EDGAR_IDENTITY` 时，只提示 SEC route 不完整，不阻塞非 SEC 文件。

### Mode A: Single File Ingest

用于用户给一个文件路径。

要求：
- 检测扩展名并选择 converter。
- 路由顺序：PDF 用 `Docling` 主转换；SEC filing 要检查 `EdgarTools` 和 `EDGAR_IDENTITY`；扫描 PDF 需要 `Tesseract` OCR；DOCX / PPTX 用 `Docling` 主转换并允许 lightweight fallback；XLSX / XLSM 用 `openpyxl` 双加载；`.xls` 用 `MarkItDown` fallback。
- 写 `_cache/[bucket]/[source-filename].md`。
- 输出 converted / skipped / failed summary。
- 若 dependency 缺失，输出 install hint，不写空 cache。

### Mode B: Inbox / Directory Ingest

用于用户给 `_inbox/` 或 `_raw/` 某个目录。

要求：
- 默认只处理目录第一层支持格式文件。
- 用户明确要求 recursive 时才递归。
- 单个文件失败不阻塞其他文件，但最后必须列出 failed files。
- 不移动 raw 文件，不删除 source 文件。

### Mode C: Cache Reuse Check

用于用户问“这个材料是不是已经消化过”。

要求：
- 检查目标 cache 文件是否存在。
- 对比 source hash；若 hash 一致则直接返回 cache path。
- 若 hash 不一致，提示需要 `--force` 重跑。

## 输出结构

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

## 下一步
- 如果要验证 claim：`information-impact`
- 如果要研究公司基础：`company-primer`
- 如果要沉淀已经研究清楚的 insight：`research-journal`
```

## Workflow 联动

| 场景 | 下一步 |
|---|---|
| workspace 还没有 `_cache/` / `_raw/` | `init` |
| dependency 缺失或同事首次使用 | `bootstrap-ingest-deps.ps1 -CheckOnly`，再由用户 opt-in `-Yes` |
| cache 生成后要判断 claim 靠不靠谱 | `information-impact` |
| cache 是公司 annual report / 10-K / 20-F | `company-primer` 或 `driver-map` |
| cache 是 industry report / technical paper | `mechanism-map` |
| cache 是 financial model workbook | `financial-model` |
| cache 里出现 source conflict | `information-impact` |
| 研究已经想清楚 | `research-journal` |

Artifact policy：
- `save_policy`: `cache_artifact`
- `default_artifact`: `[source-filename].md`
- `canonical_location`: `_cache/[bucket]/[source-filename].md`
- `_cache/` 是 operational cache，不是 earned memory，不进入 topic session。

## 反模式自查

- ❌ 缺 dependency 还说转换完成 → 必须失败并提示缺什么。
- ❌ 自动静默安装依赖 → 必须由用户显式运行 bootstrap，且默认 user-scope。
- ❌ 把 cache markdown 当成原始 source → 必须回查 `_raw/`。
- ❌ 在 ingest 阶段总结投资结论 → 越界。
- ❌ 自动删除、移动、改名 raw 文件 → 禁止。
- ❌ 默认递归整个 workspace → 太危险，必须用户明确要求 recursive。
- ❌ 把 `_cache/` 内容写进 `research-journal` → 未通过 Earned Insight Gate。
- ❌ 对 PDF / Excel 数字不写 precision caveat → 可能污染后续研究。
- ❌ 扫描 PDF 缺 OCR 还写 `[no extractable text]` cache → 必须失败并说明需要 Tesseract。
- ❌ SEC filing 缺 `EDGAR_IDENTITY` 还声称 XBRL route 完整 → 必须失败或明确标 dependency gap。

## 篇幅基准

- 单文件成功：120-220 字 + 1 行结果表 + route / precision caveat。
- 目录批量：150-300 字 + converted / skipped / failed 表。
- dependency 缺失：80-150 字，直接说明缺哪个包和未生成 cache。
- dependency bootstrap：80-180 字，给 `-CheckOnly` / `-Yes` 命令和 SEC identity caveat。
- 超过 400 字通常说明开始研究内容，应 handoff 到相邻 research skill。

## 边界

- `ingest` vs `init`：`init` 建 workspace；`ingest` 消化已有 raw files。
- `ingest` vs `information-impact`：`ingest` 只转换；claim 可信度判断交给 `information-impact`。
- `ingest` vs `company-primer`：`ingest` 不解释公司业务；公司基础交给 `company-primer`。
- `ingest` vs `research-journal`：`ingest` 生成 cache；`research-journal` 只写已研究、已验证、能改变判断的认知增量。
