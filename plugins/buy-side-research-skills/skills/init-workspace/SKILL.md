---
name: init-workspace
description: Initialize or repair a research workspace using the manifest-managed runtime payload.
---

# Init Workspace

`init-workspace` 是 operations skill。Plugin release 中的 `runtime/managed-assets.json` 是唯一部署清单；不得扫描或递归复制 `skills/*/scripts`、`skills/*/assets`。

## 执行合同

1. 验证目标是用户 research workspace，不是 plugin repo、cache 或 install directory。
2. 运行 `python _scripts/runtime-manager.py init --workspace <path>`；若 public CLI 尚未存在，直接从当前 plugin release 的 `runtime/` 调用同一 CLI。
3. 先展示 plan；存在 conflict 时停止，不覆盖用户修改。
4. apply 使用 `stage → validate → backup → apply → verify → rollback`。
5. 运行 `python _scripts/runtime-manager.py verify --workspace <path>`。
6. 可选配置 provider secrets；不得覆盖已有 `.env`、`.claude/mcp.json`、`.codex/config.toml`、`COVERAGE.md`。

## Runtime Surface

- `_scripts/source-intake.py`
- `_scripts/financial-data.py`
- `_scripts/runtime-manager.py`
- `.research-runtime/packages/`
- `.research-runtime/installed-manifest.json`
- `.claude/hooks/hook_entry.py`

旧 `_scripts/ingest.py`、`_scripts/shared/to-markdown.py`、`_scripts/financial-data/financial_data.py` 只是一版本兼容 wrapper。

## Safety

- 只部署 manifest 明确登记的文件。
- tests、fixtures、PDF、DB、临时文件、`__pycache__` 不得进入 payload。
- stale 文件仅在 installed manifest 登记且 hash 未被用户修改时删除。
- 未知文件和用户脚本始终保留。
- `verify` 默认只检查，不安装依赖或修改系统。
