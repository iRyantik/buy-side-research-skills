# ingest 退场 + financial-data 重塑 设计

> 状态: draft
> 日期: 2026-06-06
> 基准: v5.13.6 + infra cherry-pick

---

## 1. 问题

ingest 和 financial-data 的 PDF→数据链太慢。ingest 用 Docling 重型 OCR 每页跑模型，financial-data lite 靠 agent 手动从 markdown 读数字。整个链路冗余、慢、错误率高。

## 2. 目标

1. **ingest 退场**——能力收归 `_scripts/shared/`，不再作为独立 skill
2. **financial-data lite 提速**——pdfplumber 直接提表替代人工 markdown 读数字
3. **PDF→markdown 双保险**——pdf_auto_cache hook 自动拦截 + financial-data 兜底调用

## 3. 设计

### 3.1 ingest → _scripts/shared/

```
/ingest skill 删除
├── PDF: 已有 pdf-extract.py + to-markdown.py — 不动
├── DOCX/PPTX/XLSX: 已有 extract-docx.py / extract-pptx.py / extract-xlsx.py — 不动
├── WEB: 已有 web-extract.py — 不动
├── CSV: to-markdown.py 已支持 — 不动
├── describe-figures.py → _scripts/shared/ (保留)
├── verify-table-crosscheck.py → _scripts/shared/ (保留)
└── ingest_xlsx.py → _scripts/shared/extract-xlsx.py (已存在，合并)
```

### 3.2 financial-data lite 新引擎

```
/financial-data --lite <ticker>
  │
  ├─ Layer 1: Provider API (~5s)
  │   SEC/DART/EDINET/akshare/FinMind → structured IS/BS/CF
  │
  ├─ Layer 2: pdfplumber direct table extraction (~5-10s) [NEW]
  │   2a. WebSearch → download PDF (hook auto-intercepts → markdown cached)
  │   2b. pdf-extract.py --tables → structured JSON tables
  │   2c. Match tables to statement-line-items template → fill fields
  │   2d. Agent LLM fills remaining gaps (custom labels, narrative numbers)
  │
  ├─ Layer 3: Market snapshot (~5s)
  │   yfinance → price/mcap/PE/PB/EV/EBITDA
  │
  └─ Write actuals-resolved.json
```

### 3.3 full/lite 不变

- **lite**（默认）: Layer 1-3，产出 actuals-resolved.json。用于 stock-quickread/candidate-screener/peer
- **full**: lite + evidence-pack.json + full-filing.md。用于 modeling/DCF/comps

### 3.4 PDF→markdown 双保险

- **主路径**: pdf_auto_cache hook——Bash/browser 下载 PDF 时自动触发，转 markdown → 缓存 → 删 PDF
- **兜底**: financial-data 在 Layer 2 检查缓存——未命中时手动调 to-markdown.py
- **拖入 inbox**: agent session 启动时扫 `_inbox/` → 手动调 to-markdown → 缓存

## 4. 文件变更

| 文件 | 动作 | 说明 |
|---|---|---|
| `skills/ingest/` | 🗑️ 删除 | 能力已全收归 `_scripts/shared/` |
| `_scripts/shared/pdf-extract.py` | 不动 | fitz+pdfplumber+pypdf 引擎链 |
| `_scripts/shared/to-markdown.py` | 不动 | 统一入口 |
| `_scripts/shared/extract-docx/pptx/xlsx/web` | 不动 | 已存在 |
| `skills/financial-data/scripts/financial_data.py` | ✏️ | Layer 2 加 pdfplumber 表提取 |
| `skills/financial-data/SKILL.md` | ✏️ | 更新 lite 文档 |

## 5. 非目标

- 不动 Docling——已在 v5.13.6 保留，不删不增
- 不动 actuals_schema.json——保持 v1
- 不动 provider API（SEC/DART/EDINET）——保持原逻辑
- 不动 fill_gaps.py——保持原增量填充
