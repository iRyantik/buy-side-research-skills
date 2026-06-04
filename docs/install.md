# 安装指南（Agent 执行版）

你是 Claude Code 或 Codex agent。按以下步骤为用户安装 buy-side-research-skills。

---

## 前置条件：裸机 → 就绪

Agent 在 `/init-workspace` 里会自动检查并安装缺失依赖。但用户如果需要手动准备，以下是分平台命令：

### Windows

```powershell
# 1. 安装 Python 3.12
winget install Python.Python.3.12 --accept-source-agreements

# 2. 安装 Node.js LTS（Playwright MCP 前置）
winget install OpenJS.NodeJS.LTS --accept-source-agreements

# 3. 重启终端，验证
python --version   # 应显示 Python 3.12.x
node --version     # 应显示 v20.x 或更高
npx --version      # 应显示版本号
curl --version     # Windows 10+ 自带
```

### macOS

```bash
# 1. 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Python 3.12
brew install python@3.12

# 3. 安装 Node.js LTS
brew install node

# 4. 验证
python3 --version  # 应显示 Python 3.12.x
node --version     # 应显示 v20.x 或更高
npx --version      # 应显示版本号
curl --version     # macOS 自带
```

---

## Step 1: 安装插件

检查当前环境是否已安装 `buy-side-research-skills` 插件。如果没有：

- **Claude Code**：执行 `/plugin marketplace add iRyantik/buy-side-research-skills` 然后 `/plugin install buy-side-research-skills`
- **Codex**：执行 `codex plugin marketplace add iRyantik/buy-side-research-skills` 然后按提示安装

如果市场不可用，从 https://github.com/iRyantik/buy-side-research-skills/releases 下载最新 zip，解压到插件目录。

---

## Step 2: 一键初始化 Workspace

在目标文件夹执行：

```
/init-workspace
```

**这会自动完成**：
- ✅ 检查 Python 3.10+ / Node.js ≥18 / npx / curl → 缺什么装什么（winget/brew 自动执行）
- ✅ 创建 `.venv` + 安装 6 个核心 Python 包
- ✅ 部署 hooks、settings、references、scripts
- ✅ 配置 `.claude/mcp.json`（Playwright MCP，merge 策略不覆盖已有配置）
- ✅ 运行 `verify-runtime.py` — 12 项全部通过才完成
- ✅ 交互式配置 Provider 环境变量

**如果任何步骤失败**：Agent 会打印精确的修复命令，照着跑就行，然后重执行 `/init-workspace`。

---

## Step 3: 验证

```
/financial-data --lite AAPL
```

返回三表 + 市场快照 → 安装完成。

如果失败：
1. `python _scripts/verify-runtime.py` — 检查 12 项依赖
2. 按输出提示修复
3. 重试 `/financial-data --lite AAPL`

---

## 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `python: command not found` | Python 未安装或未加入 PATH | 重新安装 Python，勾选 "Add to PATH" |
| `node: command not found` | Node.js 未安装 | `winget install OpenJS.NodeJS.LTS`（Win）/ `brew install node`（Mac） |
| `npx: command not found` | Node.js 安装不完整 | 重新安装 Node.js LTS，重启终端 |
| `pip install yfinance` 超时 | 网络问题 | 重试，或 `pip install yfinance -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| `@playwright/mcp` 下载失败 | 网络/代理问题 | 检查 npm 网络：`npm config get registry` |
| Playwright MCP 启动超时 | 端口冲突 | 重启终端，检查是否有其他 MCP server 占用 |
| `.claude/mcp.json` 不存在 | `/init-workspace` 未完成 | 重跑 `/init-workspace`，会自动 merge playwright key |
| `verify-runtime.py` 报错 | 依赖缺失 | 脚本会自动安装缺失依赖，失败则按提示手动装 |
| `financial-data` 拉不到美股数据 | 未配置 EDGAR | 重跑 `/init-workspace` Step 8 配置 `EDGAR_IDENTITY` |

---

## Step 4: 配置 Provider（按覆盖市场）

如果 Step 2 跳过了 provider 配置，也可以直接编辑 `.env`：

| 市场 | 环境变量 | 申请地址 |
|---|---|---|
| US 美股 | `EDGAR_IDENTITY=Name email@domain.com` | https://efts.sec.gov/ |
| KR 韩股 | `DART_API_KEY=your_key` | https://opendart.fss.or.kr/ |
| JP 日股 | `EDINET_API_KEY=your_key` | https://disclosure2.edinet-fsa.go.jp/ |
| TW 台股 | `FINMIND_TOKEN=your_token` | https://finmindtrade.com/ |

---

现在可以开始研究了。试试 `用 industry-landscape 看 [你关注的行业]` 或 `用 stock-quickread 看 [你关注的股票]`。
