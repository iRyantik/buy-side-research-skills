# ingest 退场 + financial-data lite 提速 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** ingest 退场为基础设施 + financial-data lite 换 pdfplumber 引擎（5s 提表替代人工）

**Architecture:** ingest 能力收归 `_scripts/shared/` → pdfplumber 直接提表 → statement-line-items 模板做字段匹配 → agent 补缺

**Spec:** `docs/superpowers/specs/2026-06-06-ingest-financialdata-redesign.md`

---

## File Structure

```
skills/ingest/                                    # 🗑️ 删除
skills/financial-data/scripts/financial_data.py   # ✏️ Layer 2 加 pdfplumber
skills/financial-data/SKILL.md                     # ✏️ 文档更新
_scripts/shared/describe-figures.py                # 🆕 从 ingest/ 迁入 (已有)
_scripts/shared/verify-table-crosscheck.py          # 🆕 从 ingest/ 迁入 (已有)
_scripts/shared/pdf-extract.py                     # 不动
_scripts/shared/to-markdown.py                     # 不动
```

---

### Task 1: ingest 退场

**Files:**
- Delete: `plugins/.../skills/ingest/` (entire directory)
- Already done in cherry-pick: describe-figures.py, verify-table-crosscheck.py are in `_scripts/shared/`

Verify ingest skill is gone:

```bash
ls plugins/buy-side-research-skills/skills/ingest/ 2>/dev/null && echo "FAIL" || echo "PASS: ingest removed"
ls _scripts/shared/describe-figures.py && echo "PASS: describe-figures present"
ls _scripts/shared/verify-table-crosscheck.py && echo "PASS: verify-table-crosscheck present"
ls _scripts/shared/pdf-extract.py && echo "PASS: pdf-extract present"
ls _scripts/shared/to-markdown.py && echo "PASS: to-markdown present"
```

---

### Task 2: financial_data.py — Layer 2 加 pdfplumber 表提取

**Files:**
- Modify: `plugins/.../skills/financial-data/scripts/financial_data.py`
- Modify: workspace copy `_scripts/financial-data/financial_data.py`

**Step 1: 加 `_extract_tables_pdfplumber()` 函数**

在 `financial_data.py` 中 `# Central normalizer` 之前插入：

```python
def _extract_tables_pdfplumber(pdf_path: str) -> list[dict]:
    """Extract all tables from a PDF using pdfplumber. Returns list of {page, rows}."""
    try:
        import pdfplumber
    except ImportError:
        return []
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for tab in page.extract_tables():
                if tab and len(tab) >= 2:
                    rows = [[str(c) if c else "" for c in row] for row in tab]
                    tables.append({"page": i + 1, "rows": rows})
    return tables


def _match_tables_to_fields(tables: list[dict], market: str) -> dict:
    """Match extracted table rows to standard financial fields using statement-line-items template."""
    # Load cross-market label mappings
    LABEL_MAP = {
        "revenue": {
            "us": ["revenue", "sales", "net sales", "total revenue"],
            "jp": ["売上高", "revenue", "sales"],
            "cn": ["营业收入", "营业总收入", "revenue"],
            "kr": ["매출", "매출액", "revenue"],
            "eu": ["revenue", "net sales", "turnover"],
            "hk": ["收益", "收入", "revenue"],
            "se": ["net sales", "revenue"],
        },
        "gross_profit": {
            "us": ["gross profit", "gross margin"],
            "jp": ["売上総利益", "gross profit"],
            "cn": ["营业毛利", "gross profit"],
            "kr": ["매출총이익", "gross profit"],
            "eu": ["gross profit", "gross margin"],
            "hk": ["毛利", "gross profit"],
            "se": ["gross profit"],
        },
        "operating_income": {
            "us": ["operating income", "income from operations", "ebit"],
            "jp": ["営業利益", "operating profit"],
            "cn": ["营业利润", "operating profit"],
            "kr": ["영업이익", "operating profit"],
            "eu": ["operating profit", "ebit"],
            "hk": ["經營溢利", "operating profit"],
            "se": ["ebit", "operating profit"],
        },
        "net_income": {
            "us": ["net income", "net earnings", "net profit"],
            "jp": ["当期純利益", "net income", "profit attributable"],
            "cn": ["净利润", "归母净利润", "net profit"],
            "kr": ["당기순이익", "net income"],
            "eu": ["net profit", "net income", "profit for the year"],
            "hk": ["年內溢利", "net profit"],
            "se": ["net profit", "net income", "profit for the year"],
        },
        "total_assets": {
            "us": ["total assets"],
            "jp": ["総資産", "total assets"],
            "cn": ["资产总计", "总资产", "total assets"],
            "kr": ["자산총계", "total assets"],
            "eu": ["total assets"],
            "hk": ["總資產", "total assets"],
            "se": ["total assets"],
        },
        "total_equity": {
            "us": ["total equity", "stockholders' equity", "shareholders' equity"],
            "jp": ["純資産", "equity attributable to owners"],
            "cn": ["股东权益", "归母股东权益", "total equity"],
            "kr": ["자본총계", "지배기업소유주지분", "total equity"],
            "eu": ["total equity", "equity"],
            "hk": ["權益總額", "本公司擁有人應佔權益", "total equity"],
            "se": ["total equity", "equity"],
        },
        "cash": {
            "us": ["cash and cash equivalents", "cash & equivalents"],
            "jp": ["現金及び預金", "cash and cash equivalents"],
            "cn": ["货币资金", "cash"],
            "kr": ["현금및현금성자산", "cash"],
            "eu": ["cash and cash equivalents"],
            "hk": ["現金及現金等價物", "cash"],
            "se": ["cash and cash equivalents"],
        },
        "operating_cf": {
            "us": ["operating cash flow", "cash from operations", "net cash provided by operating"],
            "jp": ["営業活動によるキャッシュフロー", "operating cash flow"],
            "cn": ["经营活动现金流量", "operating cash flow"],
            "kr": ["영업활동현금흐름", "operating cash flow"],
            "eu": ["cash flow from operating activities"],
            "hk": ["經營活動現金流量", "operating cash flow"],
            "se": ["cash flow from operating activities"],
        },
        "capex": {
            "us": ["capital expenditure", "purchase of property", "pp&e"],
            "jp": ["有形固定資産の取得", "設備投資", "capital expenditure"],
            "cn": ["购建固定资产", "资本支出", "capital expenditure"],
            "kr": ["유형자산취득", "capital expenditure"],
            "eu": ["purchase of property, plant and equipment", "capital expenditure"],
            "hk": ["購置物業廠房設備", "capital expenditure"],
            "se": ["investments in property, plant and equipment"],
        },
        "dividends_paid": {
            "us": ["dividends paid", "dividend payment"],
            "jp": ["配当金の支払", "dividends paid"],
            "cn": ["分配股利", "dividends paid"],
            "kr": ["배당금지급", "dividends paid"],
            "eu": ["dividends paid", "dividends to shareholders"],
            "hk": ["已付股息", "dividends paid"],
            "se": ["dividends to shareholders"],
        },
        "order_intake": {
            "us": ["orders", "order intake", "bookings"],
            "jp": ["受注高", "order intake"],
            "cn": ["新签订单", "order intake"],
            "kr": ["수주", "신규수주", "order intake"],
            "eu": ["order intake", "orders received"],
            "hk": ["新訂單", "order intake"],
            "se": ["order intake"],
        },
        "order_backlog": {
            "us": ["backlog", "order backlog", "remaining performance obligations"],
            "jp": ["受注残高", "order backlog"],
            "cn": ["在手订单", "合同负债", "order backlog"],
            "kr": ["수주잔고", "order backlog"],
            "eu": ["order backlog", "backlog"],
            "hk": ["未完成合約", "訂單積壓", "order backlog"],
            "se": ["order backlog"],
        },
    }

    results = {}
    labels = LABEL_MAP
    market_labels = {k: v.get(market, v.get("us", [])) for k, v in labels.items()}

    for table in tables:
        rows = table["rows"]
        if len(rows) < 2:
            continue
        header_row = " ".join(str(c).lower() for c in rows[0] if c)
        for field, field_labels in market_labels.items():
            if field in results:
                continue  # already found
            for label in field_labels:
                if label in header_row:
                    # Find the data column (usually last numeric column after label column)
                    # Try columns 1 through N, find first numeric
                    for row_idx in range(1, len(rows)):
                        for col_idx in range(0, len(rows[row_idx])):
                            cell = str(rows[row_idx][col_idx]).strip().replace(",", "")
                            try:
                                val = float(cell)
                                if val != 0 and field not in results:
                                    results[field] = {
                                        "value": val,
                                        "source_layer": "ir-pdf",
                                        "source_detail": f"pdfplumber table p{table['page']}",
                                        "extraction_method": "pdfplumber",
                                    }
                                    break
                            except ValueError:
                                continue
                        if field in results:
                            break
                    break
    return results
```

**Step 2: 在 Lite mode 主流程中接入 pdfplumber**

找到 Lite mode fetch 中的 "WebSearch → WebFetch" 段落（约 Line 158-161 附近）。在 agent 下载 PDF 之后、agent 手动读表之前，插入 pdfplumber 提取：

```python
# After PDF download and to-markdown conversion, insert:
# NEW: Try pdfplumber direct table extraction first
pdf_tables = _extract_tables_pdfplumber(pdf_path)
pdf_fields = _match_tables_to_fields(pdf_tables, args.market)
if pdf_fields:
    write_to_actuals(pdf_fields)  # Fill what we got from tables
    gaps = [f for f in TARGET_FIELDS if f not in pdf_fields]
    # Agent fills remaining gaps
```

**Step 3: 验证 pdfplumber 提取**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"
python -c "
import importlib.util
spec = importlib.util.spec_from_file_location('fd', '_scripts/financial-data/financial_data.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Test on Anritsu PDF
tables = mod._extract_tables_pdfplumber('_inbox/anritsu-fy2024.pdf')
print(f'Tables extracted: {len(tables)}')
fields = mod._match_tables_to_fields(tables, 'jp')
print(f'Fields matched: {len(fields)}/{len(fields)}')
for k, v in sorted(fields.items()):
    print(f'  {k}: {v[\"value\"]:,.0f}')
" 2>&1
```

Expected: ≥5 fields matched from Anritsu PDF (revenue, operating_income, net_income, total_assets, total_equity).

---

### Task 3: financial-data SKILL.md 更新 + statement-line-items 引用

**Files:**
- Modify: `plugins/.../skills/financial-data/SKILL.md`
- Modify: `plugins/.../skills/financial-data/SKILL.en.md`

Lite mode 执行步骤中加 pdfplumber 说明：

```markdown
**Layer 2: pdfplumber table extraction (NEW)**
1. pdf-extract.py --tables → extract all tables from downloaded IR PDF
2. Match table headers to statement-line-items.md cross-market labels
3. Fill ~80% of standard fields automatically
4. Agent fills remaining gaps (custom labels, narrative-only numbers)
```

添加对 statement-line-items.md 的引用：

```markdown
Field labels are matched against `references/policy/statement-line-items.md` — the cross-market statement template.
```

---

### Task 4: 同步 workspace + 测试

**Step 1: 同步**

```bash
cp <plugin>/skills/financial-data/scripts/financial_data.py <ws>/_scripts/financial-data/
cp <plugin>/skills/financial-data/SKILL.md <ws>/...(cache)/
```

**Step 2: Smoke test**

```bash
python _scripts/financial-data/financial_data.py --market jp --identifier 6754 --company-slug anritsu -lite 2>&1
```

**Step 3: 端到端验证（Mycronic + Anritsu）**

```bash
# Test 1: Mycronic SE (cached PDF)
/financial-data --lite MYCR.ST
# Expected: pdfplumber → 8+ fields auto-filled

# Test 2: Anritsu JP (fresh download)
/financial-data --lite 6754.JP
# Expected: WebSearch → download → hook → pdfplumber → 10+ fields
```

---

### Task 5: 多市场完整测试

**目标**: 跑完整的 financial-data lite + full，对比实际产出。

**测试矩阵**:

| 市场 | Ticker | 公司 | 来源 |
|---|---|---|---|
| JP | 6754 | Anritsu | IR 直搜 有価証券報告書 |
| US | AAPL | Apple | SEC EDGAR 10-K |
| HK | 0700 | Tencent | IR 搜 Annual Report |
| KR | 005930 | Samsung | IR 搜 사업보고서 |
| CN | 300750 | CATL | 巨潮 年报 |
| SE | MYCR | Mycronic | IR 搜 Year-end Report |

**Step 1: 清缓存**

```bash
# Delete actuals-resolved.json for all test tickers
find industry/ -name "actuals-resolved.json" \( -path "*anritsu*" -o -path "*apple*" -o -path "*tencent*" -o -path "*samsung*" -o -path "*catl*" -o -path "*mycronic*" \) -delete

# Delete cached disclosure markdowns
find industry/ -path "*/_cache/disclosure/*" -name "*.md" -delete
```

**Step 2: 跑 lite 模式**

```bash
for ticker in "6754:jp:anritsu" "AAPL:us:apple" "0700:hk:tencent" "005930:kr:samsung" "300750:cn:catl" "MYCR.ST:se:mycronic"; do
  IFS=: read tkr mkt slug <<< "$ticker"
  echo "=== $mkt: $tkr ==="
  python _scripts/financial-data/financial_data.py \
    --market $mkt --identifier $tkr --identifier-type ticker \
    --company-slug $slug --output-scope canonical_company --mode lite
done
```

**Step 3: 清缓存再次**

```bash
# Delete actuals again to ensure clean full run
find industry/ -name "actuals-resolved.json" \( -path "*anritsu*" -o -path "*apple*" -o -path "*tencent*" -o -path "*samsung*" -o -path "*catl*" -o -path "*mycronic*" \) -delete
```

**Step 4: 跑 full 模式**

```bash
for ticker in "6754:jp:anritsu" "AAPL:us:apple" "0700:hk:tencent" "005930:kr:samsung" "300750:cn:catl" "MYCR.ST:se:mycronic"; do
  IFS=: read tkr mkt slug <<< "$ticker"
  echo "=== $mkt: $tkr (full) ==="
  python _scripts/financial-data/financial_data.py \
    --market $mkt --identifier $tkr --identifier-type ticker \
    --company-slug $slug --output-scope canonical_company --mode full
done
```

**Step 5: 对比验证**

对每个市场检查：

```
- actuals-resolved.json 是否存在？字段数？
- lite vs full 的字段数差异？
- PDF 是否被下载并缓存到 _cache/disclosure/？
- 耗时对比（lite vs full）
```

记录：

| 市场 | lite 字段 | lite 耗时 | full 字段 | full 产物 |
|---|---|---|---|---|
| JP | X/33 | Xs | X/33 | evidence-pack + full-filing |
| ... | | | | |
```
