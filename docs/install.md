# 安装

仓库：`iRyantik/buy-side-research-skills`

插件可通过市场流程安装，也可从 release zip 安装。

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

运行 `init` 创建或修复 research workspace scaffold。`3.5.0` 中 `init` 会安装 workspace `CLAUDE.md` 和一个 pointer 版 `AGENTS.md` 供 Codex / agents 使用。

`init` 之后，如需创建或定位 topic session 再保存研究产物，使用 `new-session`。`new-session` 负责解析保存路径并轻量更新 topic `index.md`，不写研究结论。

## Ingest 依赖

`init` 将 ingest 辅助脚本复制到 research workspace 的 `_scripts/` 目录。先检查依赖：

```powershell
python _scripts/ingest.py --check-deps
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -CheckOnly
```

确认无误后再显式安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File _scripts/bootstrap-ingest-deps.ps1 -Yes -EdgarIdentity "Name email@domain.com"
```

Python 包默认安装到当前用户。Tesseract 是系统二进制文件；安装脚本优先尝试 `winget`，否则打印 Chocolatey / UB Mannheim 替代安装指引。此脚本不会在 `init` 期间自动运行。
