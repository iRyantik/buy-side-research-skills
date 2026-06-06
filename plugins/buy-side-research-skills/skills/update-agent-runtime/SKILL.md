---
name: update-agent-runtime
description: Update installed host runtimes from a packaged release payload and transactionally sync the current workspace.
---

# Update Agent Runtime

`update-agent-runtime` 是唯一的用户级 update 入口。它不做手工 `cp -r`，也不再从 `init-workspace/assets` 或 `skills/*/scripts` 递归发现部署文件；所有 host 和 workspace 更新都必须来自 packaged release payload 里的 `runtime/managed-assets.json`。

> 术语：CPR 指最后的 `commit -> push -> release` 收尾动作，不指本地 payload 目录。本 skill 消费的是 release payload。

## Source Of Truth

- 默认 source：本地 release payload 目录，例如 `_dist/buy-side-research-skills/6.0.0-rc.2/`。
- 发布后兼容 source：latest GitHub release，但下载/解包后的内容仍必须先通过 `runtime-manager verify-release`。
- release payload 只允许包含 `.claude-plugin/`、`.codex-plugin/`、`skills/`、`runtime/`、`README.md`、manifest/hash/report。
- 不允许把 tests、fixtures、PDF、DB、临时文件或 `__pycache__` 带进 release payload。

## Execution Contract

1. 解析 release payload source 和 runtime version；没有显式 source 时，优先使用当前 dev repo 最新 `_dist/buy-side-research-skills/<version>/`。
2. 运行 `python _scripts/runtime-manager.py verify-release --source <release-payload>`；失败则停止。
3. 运行 `python _scripts/runtime-manager.py update-hosts --source <release-payload>`，默认更新所有已安装 host：
   - Claude Code cache version dir 和 `installed_plugins.json` pointer。
   - Codex version dir、flat `~/.codex/plugins/cache/buy-side-research-skills/skills/` 和 plugin metadata。
   - `.agents/plugins/marketplace.json` 的 local path。
4. 在当前 workspace 运行：
   - `python _scripts/runtime-manager.py plan --runtime-root <release-payload>/runtime`
   - 如存在 plugin-owned conflict，先仅对明确 target 运行 `adopt`；禁止 global force。
   - `python _scripts/runtime-manager.py update --runtime-root <release-payload>/runtime`
   - `python _scripts/runtime-manager.py verify`
5. 运行 runtime dependency checks：
   - `python _scripts/financial-data.py check-deps`
   - `python _scripts/source-intake.py check-deps`
6. 输出 host/cache/workspace/verification summary，并明确提示当前 Codex/Claude session 需要重启，skill discovery 才会重新加载新版本。

## File Safety

- installed manifest 决定哪些 workspace 文件受管。
- 只删除旧 installed manifest 中登记且 hash 未被用户修改的 stale 文件。
- `.claude/mcp.json`、`.codex/config.toml`、`COVERAGE.md` 和未知 `_scripts/` 用户脚本默认保留。
- `adopt` 只能按 `--target` 显式接管当前 plan 中的 conflict；接管前必须备份并记录 hash。
- Source Intake、Financial Data、hooks 和 providers 只从 `.research-runtime/packages/` 运行，`_scripts/` 只保留稳定 CLI/wrapper。

## Output Contract

成功或部分成功后必须输出：

```markdown
## Update Runtime Result

**结论先行**
已从 release payload `<version>` 更新 host cache，并同步 workspace runtime。当前 session 需要重启后才会重新发现新 skill。

## Hosts
| Host | Status | Version |
|---|---|---|
| Claude Code | updated / not installed / failed | 6.0.0-rc.2 |
| Codex | updated / not installed / failed | 6.0.0-rc.2 |
| .agents marketplace | updated / skipped / failed | 6.0.0-rc.2 |

## Workspace
- plan: clean / conflicts
- adopted: explicit targets only / none
- update: ok / conflicts preserved / failed
- verify: ok / failed

## Verification
- verify-release: ok / failed
- financial-data check-deps: ok / failed
- source-intake check-deps: ok / failed
- restart_required: yes
```

## Failure Handling

- release payload 验证失败：停止，不更新 host 或 workspace。
- host 缺失：标记 `not installed`，继续处理其他 host。
- workspace 指向 plugin repo 或 plugin install/cache 目录：停止 workspace sync，避免污染 dev repo/cache。
- update 后仍有 conflict：保留用户文件，输出 target 列表；不得使用全局覆盖。

Artifact policy:

- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`
