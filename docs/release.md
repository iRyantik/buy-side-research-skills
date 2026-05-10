# 发布

本文件面向插件源码仓库的维护者。日常使用插件不需要阅读本文件。

当前发布版本：`3.6.0`。正式稳定版本应打 tag 并通过 GitHub Releases 发布。

## Release 包结构

Release zip 只包含用户安装和运行时必需材料：

- `.claude-plugin/`
- `.codex-plugin/`
- `skills/`
- `README.md`

`docs/` 和 `examples/` 不进入 release zip——插件运行时不读取这两个目录。

Release zip 不得包含源码仓库维护文件：

- root `CLAUDE.md`
- root `AGENTS.md`
- root `scripts/`
- `.git/`
- `.claude/`
- `RTK.md`
- `dist/`
- 本地编辑器或 agent 状态

Release zip 必须包含 skill 内置的运行时资源，尤其是：

```text
skills/init-workspace/assets/CLAUDE.md.template
skills/init-workspace/assets/AGENTS.md.template
skills/init-workspace/scripts/init-research-workspace.ps1
skills/ingest/assets/requirements-ingest.txt
skills/ingest/scripts/bootstrap-ingest-deps.ps1
skills/ingest/scripts/ingest.py
skills/ingest/scripts/ingest_xlsx.py
skills/ingest/scripts/ingest_table_crosscheck.py
```

## 发布前检查

生成 zip 前必须运行全部 validator：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-global-rules.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-primitive-routing.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-metadata.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-skill-structure.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-plugin-tree.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-artifact-policy.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-company-primer.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-init-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-ingest-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-meta-skill.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-new-session-skill.ps1
git diff --check
```

## 构建

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1 -Version 3.6.0
```

构建产物：

```text
dist/buy-side-research-skills-3.6.0.zip
```

构建脚本会在生成 zip 后调用 release package validator 验证。

## 依赖策略

包不应预装 Docling、EdgarTools、Tesseract、MarkItDown 或其他解析器。用户在 research workspace 中通过运行 `_scripts/bootstrap-ingest-deps.ps1` 显式选择安装。
