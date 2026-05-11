# HANDOFF — v3.7.0 Release Prep

## Status: In Progress

本轮目标是把已完成的 `industry-quickread`、`consensus-map`、`primary-research-plan` 三个 workflow 作为 `v3.7.0` 稳定版发布。

## What changed for this release

- README、install / release docs、plugin manifests 已切到 `3.7.0`
- 所有 active `skill.yaml` 的 `system_generation` 已同步到 `3.7.0`
- validators 的 expected `system_generation` 已同步到 `3.7.0`
- README workflow 已明确 `industry-quickread`、`consensus-map`、`primary-research-plan` 的路由入口
- `docs/architecture.md` 已修正 release 包只包含 `.claude-plugin/`、`.codex-plugin/`、`skills/`、`README.md`

## Publish checklist

- 运行全部 validators 和 `git diff --check`
- 构建 `dist/buy-side-research-skills-3.7.0.zip`
- 提交 `Prepare v3.7.0 release`
- `git push origin main`
- 打 `v3.7.0` tag 并 push
- 创建 GitHub Release 并上传 zip
