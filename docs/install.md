# 安装

仓库：`iRyantik/buy-side-research-skills`

插件可通过市场流程安装，也可从 release zip 安装。

当前源码仓库使用 wrapper + nested payload 结构：源码里的 plugin payload 位于 `plugins/buy-side-research-skills/`。Release zip 仍是扁平安装包，解压后直接看到 `.claude-plugin/`、`.codex-plugin/`、`skills/` 和 `README.md`。

## Claude

市场可用时推荐方式：

```powershell
/plugin marketplace add iRyantik/buy-side-research-skills
/plugin install buy-side-research-skills
```

若市场不可用，从 GitHub Release 下载 zip，解压后通过 Claude Code 本地插件流程安装。

## Codex

Codex 支持通过 `.codex-plugin/plugin.json` 和同一套 `skills/` 目录提供。

```powershell
codex plugin marketplace add iRyantik/buy-side-research-skills
```

如果你的 Codex 环境使用本地插件而非市场安装，将 release zip 解压到 Codex 指定插件目录并确认 skills 已正确暴露。

## Release Zip

从 GitHub Release 下载最新版本 zip。

解压到 Claude 或 Codex 要求的插件位置，确认 `skills/` 目录下的 skills 已正确暴露。

## 第一次使用

运行 `init-workspace` 创建或修复 research workspace scaffold。`3.10.0` 中 `init-workspace` 会安装 workspace `CLAUDE.md` 和一个 pointer 版 `AGENTS.md` 供 Codex / agents 使用。

`init-workspace` 之后，如需创建或定位 topic root 再保存研究产物，使用 `new-session`。`new-session` 负责解析保存路径并轻量更新 topic `index.md`，不写研究结论。

## Ingest 依赖

`init-workspace` 将 ingest 辅助脚本复制到 research workspace 的 `_scripts/` 目录。先检查依赖：

```powershell
python _scripts/ingest.py --check-deps
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

确认无误后再显式安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

Python 包默认安装到当前用户。此脚本不会在 `init-workspace` 期间自动运行。

## Financial Data 依赖

`init-workspace` 也会把 `financial-data` 辅助脚本复制到 `_scripts/financial-data/`。先检查 provider 和 credential 状态：

```powershell
python _scripts/financial-data/financial_data.py --check-deps
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -CheckOnly
```

确认需要后再显式安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/financial-data/bootstrap-financial-data-deps.ps1 -Yes
```

US SEC route 需要 `EDGAR_IDENTITY`；韩国 DART route 需要 `DART_API_KEY`；日本 EDINET route 需要 `EDINET_API_KEY`。欧洲 ESEF route 使用 `openesef`，V1 可靠输入是 filing URL 或 local ESEF package，ticker-only discovery 仍是 experimental。

## 环境变量

`init-workspace` 会在 workspace 的 `_scripts/` 下生成 `env-setup.ps1.template`。复制为 `env-setup.ps1`，填入你的信息后运行一次：

```powershell
copy _scripts\env-setup.ps1.template _scripts\env-setup.ps1
notepad _scripts\env-setup.ps1    # 填入 API 信息
.\_scripts\env-setup.ps1          # 持久化到系统环境变量
```

或者直接把信息告诉 Claude，让它来配。
