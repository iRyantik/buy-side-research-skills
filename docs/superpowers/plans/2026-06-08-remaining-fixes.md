# 剩余三个改动 实现计划

> 基于 v5.13.11

---

## Task 1: `get_fields()` consumer helper

**文件**: `financial_data.py`

**插入点**: `LITE_FIELDS` 定义之后（~line 100）

```python
def get_fields(statements: dict, mode: str = "lite") -> dict:
    """Filter provider statements to lite or full field set.
    
    Lite mode: keeps only fields in LITE_FIELDS (46 fields).
    Full mode: passes through all fields.
    Consumer skills call this before reading actuals.
    """
    if mode == "full":
        return statements
    
    # Build flat allowed set
    allowed = set()
    for field_set in LITE_FIELDS.values():
        allowed.update(field_set)
    
    # Load concept map for XBRL→standard name translation
    concept_map = _load_concept_map()
    
    filtered = {}
    for stmt_name, rows in statements.items():
        kept_rows = []
        for row in rows:
            if not isinstance(row, dict):
                kept_rows.append(row)
                continue
            concept = (row.get("concept") or row.get("label") or "").lower()
            std_name = _map_concept(concept, concept_map)
            if std_name in allowed:
                kept_rows.append(row)
        if kept_rows:
            filtered[stmt_name] = kept_rows
    return filtered
```

**验证**:

```bash
python -c "
from financial_data import get_fields, LITE_FIELDS
# Mock actuals with known concepts
mock = {'income_statement': [
    {'concept': 'Revenues', 'values': {'FY 2025': 100}},
    {'concept': 'SellingGeneralAndAdministrativeExpense', 'values': {'FY 2025': 20}},
    {'concept': 'ShareBasedCompensation', 'values': {'FY 2025': 5}},
]}
filtered = get_fields(mock, 'lite')
# Revenues → revenue (in LITE_FIELDS) ✅  
# SG&A → sg_and_a (in LITE_FIELDS) ✅
# SBC → sbc (NOT in LITE_FIELDS) ❌ should be filtered out
assert len(filtered.get('income_statement', [])) == 2
print('PASS')
"
```

---

## Task 2: `_load_concept_map()` + `_map_concept()`

**文件**: `financial_data.py`

**说明**: 从 `statement-line-items.md` 动态解析出 `{xbrl_label: standard_field}` 映射。避免手写死 mapping dict。

```python
_concept_map_cache = None

def _load_concept_map(workspace: Path = None) -> dict[str, str]:
    """Parse statement-line-items.md → {concept_alias: standard_field}.
    
    Cached globally after first call.
    """
    global _concept_map_cache
    if _concept_map_cache is not None:
        return _concept_map_cache
    
    if workspace is None:
        workspace = discover_workspace()
    
    template = workspace / "references" / "policy" / "statement-line-items.md"
    if not template.exists():
        _concept_map_cache = {}
        return {}
    
    text = template.read_text(encoding="utf-8")
    mapping = {}
    
    # Standard field name aliases
    FIELD_ALIASES = {
        "revenue": "revenue", "cogs": "cogs", "cost_of_revenue": "cogs",
        "gross_profit": "gross_profit", "sg&a": "sg_and_a", "r&d": "r_and_d",
        "operating_income": "operating_income", "ebit": "ebit", "ebitda": "ebitda",
        "interest_expense": "interest_expense", "income_tax": "income_tax",
        "pre-tax_income": "pre_tax_income", "net_income": "net_income", "eps": "eps",
        "sbc": "sbc",
        "cash": "cash", "accounts_receivable": "accounts_receivable",
        "inventory": "inventory", "total_current_assets": "total_current_assets",
        "goodwill": "goodwill", "intangible_assets": "intangible_assets",
        "total_assets": "total_assets", "short-term_debt": "short_term_debt",
        "long-term_debt": "long_term_debt", "total_debt": "total_debt",
        "total_liabilities": "total_liabilities", "total_equity": "total_equity",
        "market_cap": "market_cap", "bonds_payable": "bonds_payable",
        "operating_cf": "operating_cf", "capex": "capex",
        "d&a": "d_and_a", "dividends": "dividends_paid", "buybacks": "buybacks",
        "order_backlog": "order_backlog", "orders": "order_intake",
        "book-to-bill": "book_to_bill", "installed_base": "installed_base",
        "employees": "employees", "customer_count": "customer_count",
    }
    
    # Parse each table row — col indices: 1=name, 3=US, 4=CN, 5=HK, 6=JP, 7=KR
    for line in text.split("\n"):
        if not line.startswith("|") or "---" in line or "科目" in line or "数据点" in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 5:
            continue
        
        raw_name = cols[1].strip().lower()
        raw_name = raw_name.replace(" ", "_").replace("/", "_")
        raw_name = raw_name.replace("(", "").replace(")", "").replace(".", "")
        if not raw_name or raw_name in ("?", "—", "数据点", "符号", "标记"):
            continue
        
        std_name = FIELD_ALIASES.get(raw_name, raw_name)
        
        # Extract all language-specific labels
        for col_idx in (3, 4, 5, 6, 7):
            if col_idx >= len(cols):
                continue
            cell = cols[col_idx].strip()
            if not cell or cell == "—":
                continue
            # Split on "/" and "or" to get individual label variants
            parts = re.split(r'\s*/\s*|\s+or\s+', cell)
            for part in parts:
                key = part.strip().lower()
                # Normalize: remove spaces, special chars
                key = re.sub(r'[^a-z0-9一-鿿぀-ゟ゠-ヿ가-힯]', '', key)
                if key and len(key) >= 2:
                    mapping.setdefault(key, std_name)
    
    _concept_map_cache = mapping
    return mapping


def _map_concept(concept: str, concept_map: dict = None) -> str:
    """Map a provider concept/label to standard field name.
    
    Examples:
        'Revenues' → 'revenue'
        'RevenuesFromContractWithCustomer' → 'revenue' (via mapping)
        'SellingGeneralAndAdministrativeExpense' → 'sg_and_a'
        '売上高' → 'revenue' (JP label from statement-line-items)
    """
    if concept_map is None:
        concept_map = _concept_map_cache or {}
    
    # Direct lookup
    key = concept.lower().replace(" ", "").replace("_", "")
    if key in concept_map:
        return concept_map[key]
    
    # Fuzzy lookup: strip common suffixes from XBRL concepts
    key_clean = re.sub(r'(calculated|usd|atcarryingvalue|net|current|noncurrent|'
                       r'afterallowance|forcreditloss|parent|attributableto)$', '', key)
    if key_clean in concept_map:
        return concept_map[key_clean]
    
    # Return normalized concept name as fallback
    fallback = concept.lower().replace(" ", "_")
    return fallback
```

**验证**:

```bash
python -c "
from financial_data import _load_concept_map, _map_concept
import discover_workspace

ws = discover_workspace()
cm = _load_concept_map(ws)
print(f'Concept map size: {len(cm)} entries')

# Test US XBRL concepts
assert _map_concept('Revenues', cm) == 'revenue'
assert _map_concept('SellingGeneralAndAdministrativeExpense', cm) == 'sg_and_a'

# Test JP labels
assert _map_concept('売上高', cm) == 'revenue'
assert _map_concept('営業利益', cm) == 'operating_income'

print('PASS')
"
```

---

## Task 3: SKILL.md 时间段描述更新

### 3.1 `financial-data/SKILL.md`

**Lite Mode Fetch** 节（~line 136-185）:

将：
```
触发语：`/financial-data --lite <ticker>` 或 "快速拉 <ticker> 数据"
触发语（3Y 模式）：`/financial-data --lite <ticker> --periods 3Y` 或 "拉 3 年完整数据"
```

改为：
```
触发语：`/financial-data <ticker>`（默认 lite）或 "拉 <ticker> latest 数据"  
触发语：`/financial-data <ticker> --mode full`（full 模式，多期+全字段）
触发语：`/financial-data <ticker> --periods FY2020-FY2025`（灵活指定期间）
```

**Consumer contract** 节（~line 182）:

将：
```
消费 skill 默认调用 `--lite` 获取 `latest_fy` + `latest_quarter`。
需要 sell-side 风格多期 appendix 时加 `--periods 3Y`
（写入 `fy_y2/y1/y0` + `sub_0/1/2/3`）
```

改为：
```
- Lite（默认）：`/financial-data <ticker>` → latest FY + latest Q/H（~46 字段）
- Full：`/financial-data <ticker> --mode full` → 5 FY + 4 Q/H（~72 字段）
- 灵活：`--periods FY2020-FY2025` 或 `--periods Q1-FY2026`
- 期间 key 从 provider values dict 动态读取（如 "FY 2025"），不硬编码
```

**Lite 写入最小字段** 节（~line 229）：保留——从 actuals 按 LITE_FIELDS 取字段。

### 3.2 `financial-data/SKILL.en.md`

同上英文翻译。

### 3.3 consumer skill SKILL.md 中残留的 `3Y` 或 `fy_y0` 引用

搜索并替换：
```
--periods 3Y → --periods 5Y（或删除，改为 full mode）
fy_y2/y1/y0 → 动态 FY key（按 values dict 读取）
```

---

## 执行顺序

```
1. _load_concept_map + _map_concept（Task 2）
2. get_fields()（Task 1，依赖 Task 2 的 concept map）
3. 测试 concept mapping on Keysight actuals
4. SKILL.md 时间段描述更新（Task 3）
5. CPR v5.13.12
```
