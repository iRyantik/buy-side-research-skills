# 安装指南（Agent 执行版）

你是 Claude Code 或 Codex agent。按以下步骤为用户安装 buy-side-research-skills。

---

## Step 1: 安装插件

检查当前环境是否已安装 `buy-side-research-skills` 插件。如果没有：

- **Claude Code**：执行 `/plugin marketplace add iRyantik/buy-side-research-skills` 然后 `/plugin install buy-side-research-skills`
- **Codex**：执行 `codex plugin marketplace add iRyantik/buy-side-research-skills` 然后按提示安装

如果市场不可用，从 https://github.com/iRyantik/buy-side-research-skills/releases 下载最新 zip，解压到插件目录。

## Step 2: 创建 Workspace

1. 让用户创建一个空文件夹（如果还没有）
2. 在 Claude / Codex 里打开这个文件夹
3. 执行 `/init-workspace`

这会创建：`CLAUDE.md`、`AGENTS.md`、`.claude/hooks/`、`_scripts/`、`.gitignore`。

## Step 3: 确认 Browser Runtime

推荐**两个** browser runtime：

| Runtime | 用途 | 需要什么 |
|---|---|---|
| **Playwright MCP** | 图片下载、页面 fallback extraction | 插件已包含，`/init-workspace` 自动配置 |
| **browser-harness CDP** | JS 渲染页面、Cloudflare 反爬绕过 | `pip install browser-harness` + Chrome 远程调试 |

安装顺序固定为：**安装插件 → `/init-workspace` → 确认 browser runtime 可用 → 再跑 skill smoke test**。

### Playwright MCP

- 当前 Claude / Codex 宿主有可用的 Playwright MCP
- `.claude/mcp.json` 包含 `playwright` key（`/init-workspace` 自动配置）

### browser-harness CDP

browser-harness 连接你的真实 Chrome，继承登录态和浏览器指纹，能访问 Playwright 打不开的页面（如 Perplexity Finance、小红书等 Cloudflare 保护站点）。

```bash
# 安装
pip install browser-harness

# 开启 Chrome 远程调试
# 在 Chrome 地址栏输入 chrome://inspect/#remote-debugging → 勾选 Allow
```

## Step 4: 检查依赖

一键检查 + 自动安装所有缺失依赖：

```
python .scripts/verify-runtime.py
```

（检查 13 项：Python / Node / curl / browser-harness / 8 个 Python 包 / Playwright MCP / hooks）

也可单独检查 financial-data 依赖：

```
python .scripts/financial-data/financial_data.py --check-deps
```

## Step 5: 配置 Credential（按用户覆盖的市场）

逐项问用户是否需要，只配用户需要的：

| 市场 | 需要什么 | 怎么配 |
|---|---|---|
| US 美股 | `EDGAR_IDENTITY`（姓名,邮箱） | 设环境变量 |
| JP 日股 | `edinet-tools` Python 包 | 安装即可，数据免费来自 [disclosure.edinet-fsa.go.jp](https://disclosure.edinet-fsa.go.jp) |
| KR 韩股 | `DART_API_KEY` | 从 [dart.fss.or.kr](https://dart.fss.or.kr) 免费申请，设环境变量 |
| EU 欧股 | ESEF 包 | 用户从公司 IR 页下载 annual report（iXBRL，.zip），拉数据时提供文件路径 |
| 所有市场 | Longbridge（可选） | 市场快照（股价/PE/共识）优先走 Longbridge API。覆盖 US/HK/SH/SZ。帮助用户注册并连接 |

Playwright 不在这张表里。它属于共享 browser/runtime 能力，不属于 market credential。

## Step 6: 验证

拉一个美股测试：

```
/financial-data --lite AAPL
```

如果能返回三表 + 市场快照，安装完成。

告诉用户：现在可以开始研究了。试试 `用 industry-landscape 看 [你关注的行业]` 或 `用 stock-quickread 看 [你关注的股票]`。
