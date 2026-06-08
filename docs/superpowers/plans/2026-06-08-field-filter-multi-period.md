# 字段过滤 + 多期提取 实现计划（修订版）

## Part A: 字段过滤

### 核心决策

- **全量写入，读取时过滤**。actuals-resolved.json 永远包含 provider 返回的全部字段。lite/full 模式只在 agent 消费时区分——consumer skill 只读各自需要的字段集。避免"先过滤再后悔"。
- **用 statement-line-items.md 做概念映射**。Provider XBRL concept（如 `Revenues`、`GrossProfit_Calculated`）→ 标准字段名（如 `revenue`、`gross_profit`）。statement-line-items.md 已有 7 市场标签对照表——解析它的表格行来生成映射，不手写 dict。

### A1. `_load_concept_map()` —— 从 statement-line-items.md 解析概念→标准字段映射

**输入**：workspace path
**输出**：`{concept_lower: standard_field}`

```python
def _load_concept_map(workspace: Path) -> dict[str, str]:
    """Parse statement-line-items.md → {concept_alias: standard_field} mapping."""
    template_path = workspace / "references" / "policy" / "statement-line-items.md"
    if not template_path.exists():
        return {}
    
    text = template_path.read_text(encoding="utf-8")
    result = {}
    
    # Standard field names from the table rows
    FIELD_ROW_RE = re.compile(
        r'^\|\s*(\w[\w\s/()-]*?)\s*\|'  # col 1: standard name
    )
    
    # Section headers tell us which market columns to read
    # US col=3, CN col=4, HK col=5, JP col=6, KR col=7, EU col=8
    MARKET_COLS = {"us": 3, "cn": 4, "hk": 5, "jp": 6, "kr": 7, "eu": 8}
    
    for line in text.split("\n"):
        if not line.startswith("|") or "---" in line or "科目" in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 4:
            continue
        
        # Derive standard field name from col 1
        # e.g. "Revenue" → "revenue", "Operating Income" → "operating_income"
        raw_name = cols[1].strip().lower().replace(" ", "_").replace("/", "_")
        if not raw_name or raw_name in ("?", "—"):
            continue
        
        # Add aliases from all language columns
        for market, col_idx in MARKET_COLS.items():
            if col_idx >= len(cols):
                continue
            cell = cols[col_idx].strip()
            if not cell or cell == "—":
                continue
            for alias in re.split(r'\s*/\s*|\s+or\s+', cell):
                alias_key = alias.strip().lower().replace(" ", "")
                if alias_key and len(alias_key) >= 2:
                    result[alias_key] = raw_name
    
    return result
```

### A2. 消费端过滤

**不改 `write_canonical_pack()`**。全量写入 actuals。在 `SKILL.md` 的 consumer contract 中定义：

```markdown
**Consumer contract**: 消费 skill 读取 `actuals-resolved.json` 时：
- stock-quickread / candidate-screener / peer → 只读取 Lite 字段集（见 `LITE_FIELDS`）
- 3-statement-model / dcf / comps → 读取全部字段（Full）
```

Agent 读取 actuals 后按需过滤——不依赖脚本。

### A3. 验证

```bash
# Lite mode: verify ~46 IS/BS/CF fields in actuals
python financial_data.py --mode lite --market us --identifier KEYS ...
# Check actuals-resolved.json — provider writes ALL fields
# Agent filters to lite set when reading

# Full mode: verify provider still writes all fields  
python financial_data.py --mode full --market us --identifier KEYS ...
# Same actuals content as lite — mode only affects agent behavior + yfinance call
```

---

## Part B: 多期提取

### 核心决策

- **Provider 已经返回多期**。SEC/DART/EDINET 的 `values` dict 包含 4+ FY key。不需要改 provider 调用——只需要 agent 在 full 模式下提取多个 FY key。
- **yfinance 只补 provider 缺失的期间**。不覆盖 provider 已有数据。

### B1. Provider 多期（代码不改行为）

**现状**：`filter_financials_by_period()` 已经支持按年度范围过滤。provider 返回的 values dict 保留全部期间。

**full 模式行为**：agent 读取 actuals 时，从 `statements.income_statement[].values` 中取 FY-2/FY-1/FY0 + 最近 4 个子期间。这些 key 已存在——只需 agent 读取。

### B2. yfinance 历史期间补充（新代码）

**触发**：`--mode full --periods 3Y`

```python
def _bootstrap_yfinance_historical(actuals_path: str, ticker: str):
    """Fill yfinance historical periods only where provider data is missing."""
    import yfinance as yf
    
    t = yf.Ticker(ticker)
    
    # Read existing actuals to find gaps
    with open(actuals_path, encoding="utf-8") as f:
        actuals = json.load(f)
    
    existing_periods = set()
    for stmt_type in ("income_statement", "balance_sheet", "cash_flow"):
        for row in actuals.get("statements", {}).get(stmt_type, []):
            existing_periods.update(row.get("values", {}).keys())
    
    # yfinance historical — only fill gaps
    annual = t.income_stmt  # 4 years
    quarterly = t.quarterly_income_stmt  # 4 quarters
    
    YF_FIELD_MAP = {
        "Total Revenue": "revenue",
        "Cost Of Revenue": "cogs",
        "Gross Profit": "gross_profit",
        "Operating Income": "operating_income",
        "Net Income": "net_income",
        # ... (existing map from fill_gaps.py)
    }
    
    for yf_label, std_field in YF_FIELD_MAP.items():
        if yf_label not in annual.index:
            continue
        for fy_label in annual.columns:
            if fy_label in existing_periods:
                continue  # Skip — provider already has this
            value = annual.loc[yf_label, fy_label]
            if value and not (isinstance(value, float) and math.isnan(value)):
                _merge_yf_value(actuals, std_field, str(fy_label), float(value))
```

**关键**：`if fy_label in existing_periods: continue` —— 永远不覆盖 provider 数据，只补缺。

### B3. `--periods 3Y` 语法

```bash
/financial-data <ticker> --mode full --periods 3Y
  → provider API → yfinance history → actuals with FY-2/FY-1/FY0 + sub-0/1/2/3
```

---

## 文件变更总结

| 文件 | 改动 | 复杂度 |
|---|---|---|
| `financial_data.py` | A1: `_load_concept_map()` | 小 |
| `financial_data.py` | B2: `_bootstrap_yfinance_historical()` | 中 |
| `financial-data/SKILL.md` | consumer contract 更新 | 小 |
| `_scripts/financial-data/fill_gaps.py` | YF_FIELD_MAP 复用（已有） | 0 |

---

## 不做

- 不写死 concept dict——从 statement-line-items.md 动态解析
- 不在写入时过滤——全量写，消费端按需取
- yfinance 不覆盖 provider 数据
- PDF 多期提取（本 plan 范围外）
