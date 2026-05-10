# AGENTS.md - Codex Dev Entry Point

> 本文件只是 Codex / agents 在 plugin source repo 的兼容入口，不是独立宪法，也不进入用户安装包。
> 本目录的开发维护 source of truth 是 [`CLAUDE.md`](CLAUDE.md)。

## Required Workflow

- 在本目录或子目录工作前，先读取并遵守 root `CLAUDE.md`。
- 若 `AGENTS.md`、`CLAUDE.md`、任何 `SKILL.md` 或其他局部指令冲突，以 root `CLAUDE.md` 为准。
- 不要在本文件复制 source policy、反流水账规则、skill trigger 表或文件组织细节；这些规则分别维护在 root `CLAUDE.md`、`skills/_shared/global-rules.md`、各 `SKILL.md` 和 workspace `CLAUDE.md.template`。

## Boundary

- 本文件只服务 plugin source repo。
- 用户 research workspace 由 `init-workspace` 安装自己的 `CLAUDE.md` 和 pointer 版 `AGENTS.md`。
- plugin release package 不应包含 root `AGENTS.md`。

**Version**: v3.6.0
**Last updated**: 2026-05-10
