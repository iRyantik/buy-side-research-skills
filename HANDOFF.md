# HANDOFF — Ingest 工具链替换 (DONE)

## Status: Complete

所有改动已合并到 v3.6.0 release。

## What was done

- `ingest.py` + `describe-figures.py` 已移入 `skills/ingest/scripts/`
- `requirements-ingest.txt` 已更新（去 markitdown[all]/pytesseract，加 pymupdf4llm + 按市场工具）
- `bootstrap-ingest-deps.ps1` 重写（Windows，跨平台零故障逻辑）
- `bootstrap-ingest-deps.sh` 新建（macOS）
- 版本 3.5.0 → 3.6.0 已同步到所有文件
- Validators 已更新（skill count 19→20, system_generation 3.6.0）
- Release zip 已重建并发布到 GitHub Releases v3.6.0
