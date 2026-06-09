# Financial-Data MCP Server

> 状态: spec
> 日期: 2026-06-09
> 目标: v5.16.0

---

## 背景

现有 `financial_data.py` 是 CLI 脚本——agent 通过 `python .scripts/financial-data/financial_data.py --market us --identifier AAPL --mode lite` 调用。MCP 化后：Agent 直接调 `mcp__financial_data__fetch(market="us", identifier="AAPL", mode="lite")`，工具内部跑同样的 provider 逻辑，写同样的文件，返回操作摘要。

## 架构

```
Agent
  │ mcp__financial_data__fetch("us", "AAPL", "lite")
  ▼
MCP Server (Python, stdio transport)
  │ 调用 existing financial_data.py core logic
  ▼
Provider (SEC / DART / EDINET / AKShare / FinMind / OpenESEF)
  │ 写文件
  ▼
Workspace
  _cache/financial-data/actuals-resolved.json
  _raw/financial-data/<market>/<id>/<run_id>/
```

## 工具设计

### 1. `fetch` — 拉取财务数据

```
mcp__financial_data__fetch(market, identifier, mode, company_slug, periods)
```

**输入**:

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `market` | string | ✅ | — | `us`/`cn`/`hk`/`jp`/`kr`/`tw`/`eu` |
| `identifier` | string | ✅ | — | ticker / CIK / filing URL |
| `mode` | string | — | `"lite"` | `lite` / `full` / `latest_core` |
| `company_slug` | string | — | 自动 | 公司目录 slug |
| `periods` | string | — | `"latest"` | `latest` / `FY2020-FY2025` |

**内部执行**：
1. `discover_workspace()` → 找到 workspace 根目录
2. `ensure_company_topic()` → 确保公司目录存在
3. `load_provider(market)` → 路由到对应 provider
4. `provider.fetch(request)` → 拉取原始数据
5. `normalize_result()` → 标准化
6. `write_canonical_pack()` → 写文件 (`actuals-resolved.json`, `_raw/`, `_cache/`)
7. Lite mode: yfinance 补市场快照

**返回**：
```json
{
  "status": "success",
  "actuals_path": "_cache/financial-data/actuals-resolved.json",
  "market": "us",
  "identifier": "AAPL",
  "provider": "edgartools",
  "completeness": {
    "income_statement": "available",
    "balance_sheet": "available",
    "cash_flow": "available",
    "revenue_split": "provider-gap"
  },
  "periods_fetched": ["FY 2025", "FY 2024", "FY 2023", "FY 2022"],
  "errors": [],
  "market_data_filled": true
}
```

### 2. `get_actuals` — 读取现有数据

```
mcp__financial_data__get_actuals(ticker, fields)
```

**输入**: `ticker` (string), `fields` (string, `"lite"` / `"full"`)

**返回**: `statements` + `market_data` 的 JSON 摘要（lite 模式只返回 LITE_FIELDS）

### 3. `list_providers` — 查询可用市场

```
mcp__financial_data__list_providers()
```

**返回**：
```json
{
  "markets": {
    "us": {"provider": "SEC EdgarTools", "status": "available", "credential": "EDGAR_IDENTITY"},
    "cn": {"provider": "AKShare", "status": "available", "credential": null},
    "hk": {"provider": "AKShare", "status": "available", "credential": null},
    "jp": {"provider": "EDINET", "status": "available", "credential": "EDINET_API_KEY"},
    "kr": {"provider": "DART", "status": "available", "credential": "DART_API_KEY"},
    "tw": {"provider": "FinMind", "status": "available", "credential": "FINMIND_TOKEN"},
    "eu": {"provider": "OpenESEF", "status": "available", "credential": null}
  }
}
```

### 4. `check_deps` — 依赖检查

```
mcp__financial_data__check_deps()
```

**返回**: 同 `financial_data.py --check-deps` 输出

## 实现

### 技术选型

- **语言**: Python（复用现有 `financial_data.py` + providers）
- **协议**: MCP stdio transport
- **依赖**: 现有 Python 包（yfinance、edgartools、akshare 等）
- **安装**: 在 workspace venv 内运行，或者全局安装 Python 包

### MCP Server 入口

```python
# financial_data_mcp_server.py
# 放在 skills/financial-data/scripts/

from mcp.server import Server
from mcp.server.stdio import stdio_server

# Import existing logic
from financial_data import (
    discover_workspace, ensure_company_topic, load_provider,
    normalize_result, write_canonical_pack, LITE_FIELDS, get_fields,
    dependency_matrix
)

server = Server("financial-data")

@server.tool()
async def fetch(market: str, identifier: str, mode: str = "lite",
                company_slug: str = None, periods: str = "latest") -> dict:
    # 1. discover workspace
    # 2. route provider  
    # 3. fetch + normalize + write
    # 4. return summary
    pass

@server.tool()
async def get_actuals(ticker: str, fields: str = "lite") -> dict:
    pass

@server.tool()
async def list_providers() -> dict:
    pass

@server.tool()
async def check_deps() -> dict:
    pass
```

### 安装

```bash
claude mcp add --scope user financial-data -- python .scripts/financial-data/financial_data_mcp_server.py
```

## 改动范围

| 文件 | 动作 |
|---|---|
| `financial_data_mcp_server.py` | 新增（~200行） |
| `stock-quickread/SKILL.md` Step 1 | 加 MCP 调用方式（A 方案） |
| `comps-analysis/SKILL.md` Step a | 同上 |
| `financial-data/SKILL.md` | 加 MCP 调用说明 |
| `init-workspace/SKILL.md` | Step 8 加 financial-data MCP 安装 |
| 其他 consumer skills | 不改——仍读 actuals-resolved.json |

## 不做

- 不改 `financial_data.py` 核心逻辑——MCP 是调用方
- 不改成纯数据返回——文件 contract 不变
- 不删 CLI 调用方式——MCP 和 CLI 共存
- 不要求 consumer skills 切换到 MCP——`Stock-quickread` Step 1 的 CLI fallback 保留

## 风险

| 风险 | 缓解 |
|---|---|
| stdio MCP 只能在本机运行 | 和 workspace 同机，够用 |
| Python 包依赖（yfinance 等）必须在 MCP 进程可 import | verify-runtime 检查，init-workspace 安装 |
| MCP 进程超时（拉 EDGAR 可能 30s+） | fetch 是 async，可设置长 timeout |
