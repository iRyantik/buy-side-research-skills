# Workspace 重组 + 反馈修复 总计划

> 状态: 最终计划
> 日期: 2026-06-08
> 目标版本: v5.14.0

---

## Part A: 文件树收口

### A1. 目标结构

```
workspace/
├── .claude/              ← hook 运行时
├── .codex/               ← Codex hook
├── .scripts/             ← 所有脚本
├── .references/          ← 参考文档（policy + runtime + kpi-drivers + templates）
├── .memory/              ← Research memory
├── .vscode/              ← VSCode 文件隐藏规则
│   └── settings.json
├── _cache/               ← 图片等缓存（artifact 链接 _cache/images/，不能改名）
├── _inbox/               ← 分析师拖文件用（可见）
├── .env                  ← 凭据
│
├── CLAUDE.md             ← 分析师可见
├── AGENTS.md             ← 分析师可见
├── COVERAGE.md           ← 分析师可见
└── industry/             ← 分析师可见——研究产出全在这
```

### A2. 重命名映射

| 原名 | 新名 | 原因 |
|---|---|---|
| `references/` | `.references/` | 分析师不需要看 |
| `memory/` | `.memory/` | 同上 |
| `_scripts/` | `.scripts/` | 同上 |
| `edge-radar.md` | `.references/edge-radar.md` | 归入参考文档 |
| `_inbox/` | 不动 | 分析师拖文件 |
| `_cache/` | 不动 | artifact 内 `_cache/images/` 链接不能断 |

### A3. .vscode/settings.json（新增 A 类资产）

```json
{
  "files.exclude": {
    ".claude/": true,
    ".codex/": true,
    ".scripts/": true,
    ".references/": true,
    ".memory/": true,
    ".vscode/": true,
    "_cache/": true,
    ".env": true
  }
}
```

策略：覆盖。分析师在 VSCode 里只看到 CLAUDE.md、AGENTS.md、COVERAGE.md、_inbox/、industry/。

### A4. 删 gitignore

- 删 `init-workspace/assets/gitignore.template`
- init 流程去掉 Step "Write .gitignore"
- `.vscode/settings.json` 不隐藏 `.git` / `.gitignore`（没有）
- 理由：不给分析师配 git

### A5. 牵连文件（路径引用同步）

| 层 | 文件数 | 改动 |
|---|---|---|
| `init-workspace/assets/` | ~15 目录 | 改名 + 去 gitignore + 加 .vscode + 加 EN 模板 |
| `init-workspace/SKILL.md` + `SKILL.en.md` | 2 | 路径表 + 去 gitignore step + 双语逻辑 |
| `update-agent-runtime/scripts/update_agent_runtime.py` | 1 | 路径 |
| `update-agent-runtime/SKILL.md` + `SKILL.en.md` | 2 | 路径 |
| 所有 research SKILL.md Capsule | ~25 | `_scripts/` → `.scripts/`、`references/` → `.references/`、加 GATE |
| 所有 research SKILL.en.md Capsule | ~25 | 同上 |
| `meta-skill/SKILL.md` + `SKILL.en.md` | 2 | Skill Directory Spec |
| `verify-runtime.py` | 1 | 路径 + 编码 |
| `evidence_ledger.py` | 1 | 路径 + 命名修正 |
| `download-image.py` | 1 | 路径 + 编码 |
| `financial_data.py` | 1 | 路径 |
| `ingest.py` | 1 | 路径 + 编码 |
| `research-runtime.md` + `research-runtime.en.md` | 2 | 内部路径 |
| `CLAUDE.md.template` | 1 | 路径 |
| `AGENTS.md.template` | 1 | 路径 |
| Hook 规则 `.py` | ~5 | 路径 |

---

## Part B: 双语 Init

### B1. 规则

- Agent 检测对话语言：
  - 中文 → 用 `CLAUDE.md.template`（中文）→ `CLAUDE.md` + `AGENTS.md.template`（中文）→ `AGENTS.md`
  - English → 用 `CLAUDE.en.md.template` → `CLAUDE.md` + `AGENTS.en.md.template` → `AGENTS.md`

### B2. 新增文件

| 文件 | 内容 |
|---|---|
| `init-workspace/assets/CLAUDE.en.md.template` | 全英文 workspace constitution |
| `init-workspace/assets/AGENTS.en.md.template` | 全英文 AGENTS |

中文模板（`CLAUDE.md.template`、`AGENTS.md.template`）保持不变。

---

## Part C: 反馈修复

### C1. #2 Windows 编码错误

所有输出到 stdout/stderr 的 Python 脚本，在 `from __future__ import annotations` 之后加：

```python
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
```

范围：`verify-runtime.py`、`download-image.py`、`evidence_ledger.py`、`verify-claim.py`、`actuals-to-appendix.py`、`ingest.py`、`financial_data.py`、`to-markdown.py`、`pdf-extract.py`、`describe-figures.py`、`generate-memory-cards.py`、`update_agent_runtime.py`、`fix-bare-anchors.py`

### C2. #1 Agent 跳过 pipeline

**stock-quickread SKILL.md 心法加硬门**：

```markdown
**GATE (不可跳过)**：触发 quickread 后，必须先做三件事再写任何内容：
1. Read workspace CLAUDE.md §5.5 + workspace .references/runtime/research-runtime.md
2. 跑 /financial-data <ticker> 获取 actuals-resolved.json
3. 跑 evidence_ledger.py init <artifact-path>

三项全部完成前，不得 Write 任何 artifact。
```

所有 research skill Runtime Capsule 统一加：

```markdown
**GATE**: Read workspace .references/runtime/research-runtime.md BEFORE any action.
```

### C3. #3 bare anchor 逐个报

新增 `.scripts/shared/fix-bare-anchors.py`：

```
python .scripts/shared/fix-bare-anchors.py <artifact.md>
```

逻辑：扫 artifact → 找所有 `[S#]`/`[I#]` bare anchor → 在 `## Resources` 中找对应 URL → 替换为 `[S#](url)` → 输出修改后的文件。

Agent 流程：写完 artifact → hook 报 bare anchor → **跑一次脚本批量修**，不再逐行 Edit。

### C4. #4 evidence_ledger 命名不一致

`evidence_ledger.py init` 改为按 artifact stem 命名：

- 旧：`688808.evidence.json`
- 新：`2026-06-08-stock-quickread-semight.md.evidence.json`

`evidence_ledger_floor` hook 同步对齐查找逻辑。

### C5. #6 actuals-to-appendix

路径确认：`_scripts/financial-data/actuals-to-appendix.py`（重组后 `.scripts/financial-data/actuals-to-appendix.py`）

Ticker 归一化：`688808` / `688808.SS` / `688808 CH` → 统一抽取数字主体匹配。

---

## Part D: 执行顺序

```
Phase 1: init-workspace/assets/ 目录重组
  1a. references/ → .references/、memory/ → .memory/、_scripts/ → .scripts/
  1b. edge-radar.md → .references/edge-radar.md
  1c. 删 gitignore.template
  1d. 加 .vscode/settings.json
  1e. 加 CLAUDE.en.md.template + AGENTS.en.md.template
  1f. 更新 CLAUDE.md.template + AGENTS.md.template 内部路径引用
  1g. 更新 init-workspace SKILL.md + SKILL.en.md（路径表 + 去 gitignore step + 双语逻辑 + 步骤重新编号）

Phase 2: 脚本路径 + 编码更新
  2a. verify-runtime.py、evidence_ledger.py、download-image.py
  2b. update_agent_runtime.py（路径 + 编码）
  2c. financial_data.py、ingest.py
  2d. 所有 shared/ 小脚本（to-markdown、pdf-extract、describe-figures、generate-memory-cards、verify-claim）
  2e. 新增 fix-bare-anchors.py

Phase 3: SKILL.md 批量更新
  3a. 所有 Capsule: references/ → .references/、_scripts/ → .scripts/
  3b. 所有 Capsule: 加 **GATE** 行
  3c. meta-skill: Skill Directory Spec 路径
  3d. stock-quickread: 硬门强化
  3e. update-agent-runtime: 路径
  3f. research-runtime.md + research-runtime.en.md: 内部路径

Phase 4: evidence_ledger + actuals-to-appendix 专项
  4a. evidence_ledger.py 命名修正 + hook 对齐
  4b. actuals-to-appendix.py ticker 归一化

Phase 5: 验证 + CPR
  5a. 语法检查所有 .py
  5b. verify-runtime.py
  5c. 版本号 → v5.14.0
  5d. CPR

Phase 6: 清理已有 workspace
  6a. /update-agent-runtime → 自动重建
```

---

## Part E: 影响面

| 组件 | 改动量 | 风险 |
|---|---|---|
| 目录结构 | 4 改名 + 2 新增 - 1 删 | 低 |
| SKILL.md | ~55 文件 | 低——文本替换 |
| Python 脚本 | ~16 文件 | 中——逐文件测 |
| 双语模板 | 2 新文件 | 低 |
| fix-bare-anchors | 1 新脚本 | 低 |
| evidence_ledger | 命名逻辑 | 中——hook 对齐 |
