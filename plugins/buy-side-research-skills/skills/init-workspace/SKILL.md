---
name: init-workspace
description: Initialize or repair a buy-side research workspace root scaffold — cross-platform (Windows + macOS), Python unified.
---

# Init Workspace

`init-workspace` turns a normal folder into a usable buy-side research workspace. It creates the root scaffold, deploys platform-owned runtime assets (hooks, configs, references, shared utility scripts), copies skill scripts from ingest/financial-data/reddit-sentiment/research-viz into `_scripts/`, sets up a Python virtual environment with core dependencies, and interactively configures data-provider environment variables.

It does not update the installed Claude Code or Codex plugin runtime itself; host/plugin upgrades and latest-release workspace sync belong to `update-agent-runtime`.

It is an operations skill, not a research skill.

## Mental Model

The invariant is separation of concerns:

- `init-workspace` creates or repairs the root workspace shell + environment.
- `new-session` creates or locates a topic root with `index.md` and `_inbox/`.
- Each skill (ingest, financial-data, etc.) bootstraps heavy dependencies on first use via its own `bootstrap.py`.
- `update-agent-runtime` keeps the workspace in sync with the latest plugin release.

## Responsibilities

### Responsible for

**Directories:**
- Creating root `_inbox/`, `_scripts/`, and `topics/`.

**A类 — Platform-owned assets** (from `init-workspace/assets/`, copied verbatim to workspace root):

| Source | Destination | Strategy |
|---|---|---|
| `.claude/hooks/` (full tree) | `.claude/hooks/` | Overwrite |
| `.claude/settings.json` | `.claude/settings.json` | Overwrite |
| `.claude/mcp.json` | `.claude/mcp.json` | Copy if missing |
| `.codex/hooks.json` | `.codex/hooks.json` | Overwrite |
| `.codex/mcp.example.json` | `.codex/mcp.example.json` | Overwrite |
| `references/` | `references/` | Overwrite |
| `_scripts/download-product-image.js` | `_scripts/download-product-image.js` | Overwrite |
| `CLAUDE.md.template` | `CLAUDE.md` | Copy if missing (patch managed sections only) |
| `AGENTS.md.template` | `AGENTS.md` | Copy if missing |
| `edge-radar.md` | `edge-radar.md` | Copy if missing |
| `coverage.md.template` | `COVERAGE.md` | Copy if missing |
| `gitignore.template` | `.gitignore` | Overwrite |
| `.env.template` | `.env.template` | Copy if missing |

**B类 — Skill scripts** (copied from each skill's canonical `scripts/` and `assets/` directory into workspace `_scripts/<skill>/`):

| Source | Destination |
|---|---|
| `skills/ingest/scripts/*.py` | `_scripts/ingest/` |
| `skills/ingest/assets/requirements-ingest.txt` | `_scripts/ingest/` |
| `skills/financial-data/scripts/**/*.py` | `_scripts/financial-data/` |
| `skills/financial-data/assets/requirements-financial-data.txt` | `_scripts/financial-data/` |
| `skills/reddit-sentiment/scripts/*.py` | `_scripts/reddit-sentiment/` |
| `skills/reddit-sentiment/assets/requirements-reddit-sentiment.txt` | `_scripts/reddit-sentiment/` |
| `skills/research-viz/assets/template*.html` | `_scripts/research-viz/` |

**Environment setup:**
- Check Python 3.10+ availability.
- Create `.venv/` (Python virtual environment).
- Install core dependencies into venv: `yfinance openpyxl requests python-dotenv pyyaml lxml`.
- Run `pip install -r` for `_scripts/ingest/requirements*.txt`, `_scripts/financial-data/requirements*.txt`, `_scripts/reddit-sentiment/requirements*.txt`. Failures warn, do not block — heavy dependencies (Docling, etc.) are handled by each skill's `bootstrap.py` on first use.
- Write `.gitignore`.

**Interactive provider configuration:**
- Display a single table of 4 data-provider options (SEC EDGAR, DART, EDINET, FinMind) with their env var names and application URLs.
- User replies with which providers to configure and their keys. Agent writes `.env` (merges with existing `.env` if present).
- Unconfigured providers stay as commented lines in `.env`.

**Cleanup:**
- Delete `_scripts/init-assets/` if present (legacy ps1-era artifacts).

### Not responsible for

- Installing Docling, Tesseract, onnx, torch, or other heavy dependencies — each skill's `bootstrap.py` handles these on first use.
- Running `git init`.
- Creating topic directories — use `new-session`.
- Creating topic-level `_raw/`, `_cache/`, or `_models/`.
- Initializing inside the plugin dev repo or plugin install directory.
- Running `update-agent-runtime` host/plugin upgrades.

## Trigger And Input

Trigger phrases:

- "init research workspace"
- "初始化研究工作区"
- "创建研究文件夹"
- "setup research"
- "bootstrap workspace"
- "补齐 research workspace"

Required input:

- `WorkspacePath`: an explicit user-owned research workspace path.
- The target path must not be the plugin repo, a plugin install directory, or any folder containing plugin markers such as `.claude-plugin/`, `.codex-plugin/`, or `skills/`.

## Modes

### New Workspace Scaffold

Execute full Steps 0-10 (see Execution Flow below). All files are created.

### Repair Existing Workspace

Execute the same steps. Skip root template files that already exist (CLAUDE.md, AGENTS.md, edge-radar.md, COVERAGE.md). Platform-owned assets (hooks, settings, references, `.gitignore`) are overwritten. Skill scripts (B类) are overwritten. User-created files in `_scripts/` that are not in the B类 list are left untouched.

## Execution Flow

```
Step 0  Validate workspace path — must not be inside a plugin repo or install directory
Step 1  Check Python 3.10+ is available
Step 2  Create .venv/ (python -m venv .venv)
Step 3  Activate venv + pip install core dependencies:
          pip install yfinance openpyxl requests python-dotenv pyyaml lxml
Step 4  Deploy A类 files (platform assets from init-workspace/assets/)
Step 5  Deploy B类 files (skill scripts to _scripts/<skill>/)
Step 6  pip install -r _scripts/*/requirements*.txt (failures warn, do not block)
Step 7  Write .gitignore
Step 8  Interactive provider configuration (see Provider Configuration below)
Step 9  Delete _scripts/init-assets/ if present (legacy cleanup)
Step 10 Print deployment summary table
```

### Core dependencies

```bash
pip install yfinance openpyxl requests python-dotenv pyyaml lxml
```

### Platform detection

Agent uses `sys.platform`:
- `win32` → Windows: Python = `python`, venv = `.venv/Scripts/python`
- `darwin` / other → Unix: Python = `python3`, venv = `.venv/bin/python`

## Provider Configuration

After file deployment, display a single table and ask the user to configure data providers:

```
[Provider 配置]

以下 4 个数据源 provider 按你的覆盖市场选配。
需要配置的把 key 贴给我，不需要的回复"跳过"。

┌──────┬───────────┬──────────────────────────────┬────────────────────────────────┐
│ #    │ Provider  │ 环境变量                      │ 申请地址                        │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 1    │ SEC EDGAR │ EDGAR_IDENTITY                │ https://efts.sec.gov/          │
│      │ (美股)    │ 格式: "Name email@domain.com"  │ 填 Name+Email 即生效            │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 2    │ DART      │ DART_API_KEY                  │ https://opendart.fss.or.kr/    │
│      │ (韩股)    │                               │ 免费注册获取 API Key            │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 3    │ EDINET    │ EDINET_API_KEY                │ https://disclosure2.           │
│      │ (日股)    │                               │ edinet-fsa.go.jp/              │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 4    │ FinMind   │ FINMIND_TOKEN                 │ https://finmindtrade.com/      │
│      │ (台股)    │                               │ 免费注册获取 Token              │
└──────┴───────────┴──────────────────────────────┴────────────────────────────────┘

还没有 key 的去对应地址申请，有 key 的直接贴给我。
```

Agent parses the user's free-form reply and writes `.env` (merging with existing `.env` if present). Provider env vars supplied by the user are set; unconfigured providers remain as commented lines.

### .env format

```env
# SEC EDGAR（美股）
EDGAR_IDENTITY=Name email@domain.com

# DART（韩股）
# DART_API_KEY=

# EDINET（日股）
EDINET_API_KEY=your_key_here

# FinMind（台股）
# FINMIND_TOKEN=
```

`.gitignore` already includes `.env` — the file stays local and is never committed.

## File Safety

- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md` — copy from template only if missing.
- Do not overwrite `COVERAGE.md` or `edge-radar.md` if already present.
- Do not overwrite `.claude/mcp.json` if already present (user may have customized).
- Do not overwrite `_scripts/` files that are not in the B类 source list (user-added scripts are preserved).
- Do not run inside the plugin dev repo or plugin install directory.

## Workflow Links

| Scenario | Handling |
|---|---|
| User wants to upgrade plugin + sync workspace | Use `update-agent-runtime` |
| User wants to create a new topic | Use `new-session` |
| User wants to fix workspace runtime only | Use `update-agent-runtime` (or re-run init-workspace in repair mode) |

Artifact policy:

- `save_policy`: `none`
- `default_artifact`: `conversation-only`
- `canonical_location`: `conversation-only`

## Safety Self-Check

- Validated workspace path is not a plugin directory.
- Core dependencies installed (no heavy packages).
- Platform-owned assets deployed.
- Skill scripts copied from canonical plugin locations.
- Provider configuration offered interactively.
- Legacy `_scripts/init-assets/` cleaned up.
- Did not create research artifacts.
