# 安装指南（Agent 执行版）

你是 Claude Code 或 Codex agent。按以下步骤为用户安装 buy-side-research-skills。

## 傻瓜式安装

用户只需说一句：

```
按照 https://github.com/iRyantik/buy-side-research-skills/blob/main/docs/install.md 安装 buy-side-research-skills
```

Agent 收到后自动执行下面全部步骤。

---

## Step 1: 安装插件

```
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

如果市场不可用，从 https://github.com/iRyantik/buy-side-research-skills/releases 下载最新 zip，解压到插件目录。

## Step 2: 创建 Workspace

1. 让用户创建一个空文件夹（如果还没有）
2. 在 Claude Code / Codex 里打开这个文件夹
3. 执行 `/init-workspace`

## Step 3: 检查依赖

```
python .scripts/verify-runtime.py
```

（Python / Node.js / npx / curl / 8 个 Python 包 / Playwright MCP / hooks。失败项自动安装。）

## Step 4: 可选组件

Agent 逐项问用户是否需要，不要默认安装：

| 组件 | 用途 | 怎么装 |
|---|---|---|
| **browser-harness CDP** | JS 渲染页面、Cloudflare 绕过 | `pip install browser-harness` + Chrome 远程调试（`chrome://inspect` → Allow） |
| **ffmpeg** | 音频转写（meeting-minutes 等） | `winget install ffmpeg` 或 `choco install ffmpeg` |

## Step 5: 配置 Credential（按需）

逐项问用户：

| 市场 | 需要什么 |
|---|---|
| US 美股 | `EDGAR_IDENTITY`（姓名,邮箱） |
| JP 日股 | `pip install edinet-tools`，免费 |
| KR 韩股 | `DART_API_KEY`，[dart.fss.or.kr](https://dart.fss.or.kr) 免费申请 |
| EU 欧股 | 公司 IR 页下载 ESEF 包（iXBRL .zip） |
| Longbridge（可选） | 市场快照，US/HK/SH/SZ |

## Step 6: 验证

```
/financial-data --lite AAPL
```

返回三表 + 市场快照 = 安装完成。
