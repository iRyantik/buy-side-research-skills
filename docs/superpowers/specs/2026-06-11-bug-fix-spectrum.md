# Bug Fix Spec — Buy-Side Research Plugin Infrastructure

> 状态: planned | 日期: 2026-06-11 | 目标: v5.19.0
> 来源: workspace BUG_TRACKER.md

---

## 总览

10 bugs，按依赖关系和共用代码分 4 轮。预计 ~2 个 CLI 文件 + ~4 个 Python 脚本 + ~2 个 hook。

---

## Round 1 — 简单 Python fix

**依赖**: 无  
**目标**: 消除首次研究公司的摩擦

### #4 — financial_data.py: auto-create company directory

**症状**: `--company-slug santec` → "Company directory not found...Run new-session first"

**根因**: `ensure_company_topic()` 只 search 不 create。

**修复** (`financial_data.py`):

```
def ensure_company_topic(workspace, company_slug):
    # 现有逻辑：search industry/*/companies/<slug>
    # 找不到 → 走新路径：
    
    # 1. 找行业目录（优先已存在的 industry dir）
    industry_dirs = list((workspace / "industry").iterdir())
    if industry_dirs:
        target_ind = industry_dirs[0]  # 首个行业
    else:
        target_ind = workspace / "industry" / "technology"
    
    # 2. mkdir -p
    company_dir = target_ind / "companies" / company_slug
    os.makedirs(company_dir, exist_ok=True)
    # 3. 创建 index.md stub（如不存在）
    # 4. 继续执行 fetch
```

**改动范围**: `financial_data.py` — `ensure_company_topic()` 函数（~15 行新增）

---

### #11 — evidence_ledger.py: `-t` 改为 optional

**症状**: `auto <artifact>` 报错，实际需 `-t TICKER`

**修复** (`evidence_ledger.py`):

```python
# 如果 -t 未提供，从 artifact path 推断
# artifact: industry/<slug>/companies/<ticker>/YYYY-MM-DD-*.md
# → parse ticker from path

def infer_ticker(artifact_path: Path) -> str | None:
    parts = artifact_path.parts
    # .../industry/<slug>/companies/<ticker>/YYYY-MM-DD-*.md
    if "companies" in parts:
        idx = parts.index("companies")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None
```

**改动范围**: `evidence_ledger.py` — argparse + `infer_ticker()` function（~12 行新增）

---

## Round 2 — 数据管道 fill 引擎

**依赖**: Round 1 完成后  
**共用代码**: 所有三个 bug 共享 `financial_data.py` 的 lite mode 收尾逻辑

### #7 — lite mode market_data 自动填充

**症状**: EDINET 拉完后 `market_data` 全 null

**根因**: lite mode edinet provider 跳出时不触发 market_data fill

**修复** (`financial_data.py`):

```python
# lite mode 收尾统一 fill
def _fill_market_data(actuals, market, identifier):
    chain = [
        ("yfinance",  _try_yfinance),
        ("longbridge", _try_longbridge_mcp),
        ("web_search", _try_web),
    ]
    for name, fn in chain:
        result = fn(market, identifier)
        if result:
            return result
    return None  # all failed → leave null
```

**现有 fill 逻辑**: CLI 在 `_run_lite()` 末尾已调用 fill 引擎，但 edinet provider 在 `fetch()` 中提前 return 导致 fill 被跳过。修复：确保 fill 在 `finally` 或 unified exit 点。

**改动范围**: `financial_data.py` — `_run_lite()` closeout block（~20 行调整）

---

### #9 — lite mode revenue_split persist to canonical actuals

**症状**: FORM lite actuals 无 revenue_split（full mode 有）

**根因**: lite mode 只 extract 不 persist

**修复** (`financial_data.py`):

```python
# lite mode 收尾：检测 revenue_split 是否可用
if revenue_split and not actuals.get("statements", {}).get("revenue_split"):
    actuals["statements"]["revenue_split"] = revenue_split
    # 重新写入 actuals-resolved.json
    write_canonical_pack(actuals)
```

**改动范围**: `financial_data.py` — `_run_lite()` 收尾（与 #7 同一处，~8 行新增）

---

### #5 — EDINET lite: supplement missing FY via yfinance

**症状**: Santec actuals 只有 FY2024/FY2023

**根因**: EDINET 有価証券報告書滞后 1-2 年

**修复** (`financial_data.py`):

```python
# lite mode edinet provider 收尾
if market == "jp" and len(fetched_periods) < 3:
    # yfinance snapshot 补最近 FY
    yf_periods = _yf_snapshot_income(identifier, count=2)
    supplement_actuals(yf_periods)
```

**简洁方案**: 不改变 edinet provider 本身——在 lite mode 收尾时做 unified 检查：所有 market 的 fetched_periods < 3 时，自动 yfinance supplement。

**改动范围**: `financial_data.py` — shared supplement 逻辑（~25 行新增）

---

### 三者如何合并

`_run_lite()` closeout block 统一处理：

```python
# Lite mode unified cleanup (called after provider fetch)
def _lite_closeout(actuals, market, identifier):
    # 1. market_data fill（#7）
    _fill_market_data(actuals, market, identifier)
    
    # 2. revenue_split persist（#9）
    _persist_revenue_split(actuals)
    
    # 3. missing FY supplement（#5）
    _supplement_missing_fy(actuals, market, identifier)
    
    # 4. write actuals
    write_canonical_pack(actuals)
```

一个 closeout block 修三个 bug。

---

## Round 3 — Hook + 脚本

**依赖**: Round 2 完成后  
**范围**: Hook.py、fix-bare-anchors.py、table_render_integrity.py、verify-claim.py

### #3 — fix-bare-anchors.py table corruption

**修复**: detect merged pipe lines → split before inserting separator

```python
def fix_table_line(line):
    # 如果行包含 ||（双 pipe）→ split by ||
    # 恢复原有行边界，再正确插入 separator
    if "||" in line:
        return line.replace("||", "|")
    return line
```

**改动范围**: `fix-bare-anchors.py`（~10 行）

---

### #14 — source_contract hook: [UNVERIFIED] exclude list

**修复**:

```python
NON_SOURCE_LABELS = {
    "UNVERIFIED", "需查证", "推算", "缺图", "估算", "ND",
    "待查", "来源待补", "n/a", "TBD", "TODO",
}
# Hook: 跳过 NON_SOURCE_LABELS 中的 token
if label in NON_SOURCE_LABELS:
    continue
```

**改动范围**: `source_contract.py` hook rule（~6 行新增）

---

### #12 — table_render_integrity: column counting fix

**修复**: 统一用 pipe count

```python
# current: count cells (= pipes-1 for data row, = pipes for header)
# fix: always count pipes (= cells+1)
def pipe_count(line):
    return line.count("|")
```

**改动范围**: `table_render_integrity.py`（~5 行调整）

---

### #15 — verify-claim.py: 403 domain pre-routing

**修复**:

```python
KNOWN_403_DOMAINS = {
    "marketscreener.com", "tipranks.com", 
    "simplywall.st", "macrotrends.net",
    # ... 扩展
}

def tier1_should_skip(url):
    return any(d in url for d in KNOWN_403_DOMAINS)
```

**改动范围**: `verify-claim.py`（~10 行新增）

---

## Round 4 — Unicode 卫生

**依赖**: 无  
**目标**: 消除 Windows GBK 编码错误

### #10 — verify-claim.py ¥ symbol UnicodeEncodeError

**修复**:

```python
# financial_data.py + verify-claim.py: 统一入口
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
```

**改动范围**: verify-claim.py + any script missing this guard（~3 行/文件）

---

### #13 — Unicode minus sign (U+2212 → ASCII hyphen)

**修复**:

```python
# 在 financial_data.py 输出前做 safe encoding
def safe_ascii(s):
    return s.replace("−", "-")  # Unicode minus → ASCII hyphen
```

或者在 yfinance/edgar 取数后统一 strip。

**改动范围**: `financial_data.py` normalizer（~5 行）

---

## 文件改动汇总

| 文件 | Round | 行数 |
|---|---|---|
| `financial_data.py` | R1, R2 | +40 行（ensure_company + closeout block） |
| `evidence_ledger.py` | R1 | +12 行（infer_ticker） |
| `fix-bare-anchors.py` | R3 | +10 行 |
| `source_contract.py` | R3 | +6 行（exclude set） |
| `table_render_integrity.py` | R3 | +5 行 |
| `verify-claim.py` | R3, R4 | +13 行（403 + UTF-8） |

**总计**: ~85 行改动，6 个文件，1 个 release。
