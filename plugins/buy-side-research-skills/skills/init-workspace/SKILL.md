---
name: init-workspace
description: Initialize or repair a buy-side research workspace root scaffold — cross-platform (Windows + macOS), Python unified.
---

# Init Workspace

`init-workspace` turns a normal folder into a usable buy-side research workspace. It creates the root scaffold, deploys platform-owned runtime assets (hooks, configs, references, shared utility scripts), copies skill scripts from ingest/financial-data/reddit-sentiment/research-viz/coverage-monitor into `.scripts/`, installs core Python packages globally (no venv, no sudo), and interactively configures data-provider environment variables.

It does not update the installed Claude Code or Codex plugin runtime itself; host/plugin upgrades and latest-release workspace sync belong to `update-agent-runtime`.

It is an operations skill, not a research skill.

## 心法

The invariant is separation of concerns:

- `init-workspace` creates or repairs the root workspace shell + environment.
- Each skill (ingest, financial-data, etc.) bootstraps heavy dependencies on first use via its own `bootstrap.py`.
- `update-agent-runtime` keeps the workspace in sync with the latest plugin release.
- Topic scaffolding (industry directories, company directories, index.md, coverage registration) happens automatically when research skills save artifacts. See workspace `.references/policy/research-policy-baseline.md` §9 Topic Scaffolding Convention.

## Responsibilities

### Responsible for

**Directories:**
- Creating root `_inbox/` and `.scripts/`.

**A类 — Platform-owned assets** (from `init-workspace/assets/`, copied verbatim to workspace root):

| Source | Destination | Strategy |
|---|---|---|
| `.claude/hooks/` (full tree) | `.claude/hooks/` | Overwrite |
| `.claude/settings.json` | `.claude/settings.json` | Overwrite |
| `.claude/mcp.json` | `.claude/mcp.json` | Merge（确保 `playwright` key 存在，不动用户其他 MCP 配置；JSON 不合法则备份后覆盖） |
| `.codex/hooks.json` | `.codex/hooks.json` | Overwrite |
| `.codex/mcp.example.json` | `.codex/mcp.example.json` | Overwrite |
| `.references/` (full tree) | `.references/` | Overwrite |
| `.scripts/shared/` (full tree) | `.scripts/shared/` | Overwrite |
| `.scripts/verify-runtime.py` | `.scripts/verify-runtime.py` | Overwrite |
| `.vscode/settings.json` | `.vscode/settings.json` | Overwrite |
| `CLAUDE.md.template` or `CLAUDE.en.md.template` | `CLAUDE.md` | 按语言：中文→ZH 模板，English→EN 模板，Copy if missing |
| `AGENTS.md.template` or `AGENTS.en.md.template` | `AGENTS.md` | 同上 |
| `coverage.md.template` or `coverage.en.md.template` | `COVERAGE.md` | 同上 |
| `.env.template` or `.env.en.template` | `.env.template` | 同上 |
| `.env.template` | `.env.template` | Copy if missing |

**B类 — Skill workspace assets** (auto-discovered; formal spec in `meta-skill` Skill Directory Spec):

> **Self-registration rule**: Each skill self-registers what it needs in the workspace by putting files in `scripts/` or `assets/`. Adding a file → automatically deployed. Zero changes to this skill.

```
for each skill_dir in skills/*/:
    if .platform exists → skip (platform skill, deployed by A类)

    dst = .scripts/<skill-name>/

    if scripts/ exists:
        cp -r scripts/* → dst/

    if assets/ exists:
        for each file in assets/ (recursive):
            if file is under assets/templates/:
                cp → dst/  (copy if missing — user may have customized)
            else:
                cp → dst/  (overwrite — canonical plugin version)

    # references/ and examples/ are NOT deployed.
    # Agent reads them directly from the plugin cache when executing the skill.
```

> **The rule**: `scripts/` + `assets/` → workspace `.scripts/<skill>/`. No per-file mapping. No per-skill registration.  |

**Environment setup:**
- Check Python 3.10+ availability.
- Install core dependencies globally with `--user`（no venv, no sudo）: `python -m pip install --user yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx`。
- Run `pip install --user -r` for each `.scripts/*/requirements*.txt` found (glob discovery). Failures warn, do not block — heavy dependencies (Docling, etc.) are handled by each skill's `bootstrap.py` on first use.
- **ffmpeg**: Check availability (`ffmpeg -version`). If missing → download portable ffmpeg.exe from https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip and extract to `.scripts/shared/ffmpeg.exe`. On macOS: `brew install ffmpeg`.
**Interactive provider configuration:**
- Display a single table of 4 data-provider options (SEC EDGAR, DART, EDINET, FinMind) with their env var names and application URLs.
- User replies with which providers to configure and their keys. Agent writes `.env` (merges with existing `.env` if present).
- Unconfigured providers stay as commented lines in `.env`.
- Coverage-monitor delivery env placeholders (`SMTP_*`, `COVERAGE_EMAIL_TO`, `WECOM_WEBHOOK_URL`) are shipped in `.env.template` only; they are optional and not part of provider credential setup.

**Cleanup:**
- Delete `.scripts/init-assets/` if present (legacy ps1-era artifacts).

### Not responsible for

- Installing Docling, Tesseract, onnx, torch, or other heavy dependencies — each skill's `bootstrap.py` handles these on first use.
- Running `git init`.
- Creating topic directories — handled automatically by research skills on artifact save (see policy baseline §9).
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

Execute the same steps. Skip root template files that already exist (CLAUDE.md, AGENTS.md, .references/edge-radar.md, COVERAGE.md). Platform-owned assets (hooks, settings, references, `.gitignore`) are overwritten. Skill scripts (B类) are overwritten. User-created files in `.scripts/` that are not in the B类 list are left untouched.

## Execution Flow

```
Step 0  Validate workspace path — must not be inside a plugin repo or install directory
Step 1  Detect language: Chinese conversation → ZH templates, English conversation → EN templates
Step 2  Check system dependencies: Python 3.10+, Node.js ≥18, npx, curl
        ★ ALL BLOCK — missing any → auto-install (winget/brew), fail → print manual command + STOP
Step 3  Install core Python packages globally (no venv, no sudo):
          python -m pip install --user yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx
        ★ pip install failure → BLOCK (core packages required for all skills)
Step 4  Deploy A类 files (platform assets from init-workspace/assets/)
        ★ mcp.json: merge strategy (see below)
        ★ Templates: use language from Step 1 (ZH → .template, EN → .en.template)
Step 5  Deploy B类 files (skill scripts to .scripts/<skill>/)
Step 6  pip install --user -r .scripts/*/requirements*.txt (failures warn, do not block)
Step 7  Interactive provider configuration (see Provider Configuration below)
Step 8  MCP server setup — Longbridge Bridge (market data, US/HK):
          Claude Code: claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp
          Codex:       codex mcp add longbridge --url https://openapi.longbridge.com/mcp
          ★ 安装后需 OAuth 认证：CC → /mcp → longbridge → Authenticate, Codex → codex mcp login longbridge
          ★ 用户可跳过，不影响基础功能（Bridge 层不可用时自动降级到 yfinance + WebSearch）
Step 9  ★ python .scripts/verify-runtime.py — one-click smoke test
        ★ 12 checks across 3 layers, ALL BLOCK, auto-install missing, fail → STOP
Step 10 Delete .scripts/init-assets/ if present (legacy cleanup)
Step 11 Print deployment summary table
```

### Step 1 Detail: System Dependency Check

Agent checks 4 system tools. **任一缺失 → 直接帮用户装**（winget on Windows, brew on macOS）。安装失败 → 打印手动命令 + **STOP**（不继续后续步骤）。

| 检查项 | 验证命令 | 自动安装 (Windows) | 自动安装 (macOS) | 手动 fallback |
|---|---|---|---|---|
| Python ≥3.10 | `python --version` | `winget install Python.Python.3.12 --accept-source-agreements` | `brew install python@3.12` | https://python.org |
| Node.js ≥18 | `node --version` | `winget install OpenJS.NodeJS.LTS --accept-source-agreements` | `brew install node` | https://nodejs.org |
| npx | `npx --version` | 随 Node.js（重装 Node 即可） | 同左 | 重装 Node.js LTS |
| curl | `curl --version` | `winget install curl.curl --accept-source-agreements` | macOS 自带 | 系统包管理器 |

Agent 检测平台：`sys.platform == "win32"` → Windows；`sys.platform == "darwin"` → macOS。

Linux 不自动安装——打印手动命令 + STOP，提示用户用系统包管理器安装后重跑 `/init-workspace`。

### Step 4 Detail: mcp.json Merge

Agent 处理 `.claude/mcp.json` 的流程：

```
1. if 文件不存在:
      → 直接写入 assets/.claude/mcp.json
2. else:
      → try json.load
      → if JSONDecodeError:
            → 备份为 .claude/mcp.json.bak
            → 覆盖写入 assets/.claude/mcp.json
            → 提示用户 "旧文件 JSON 不合法，已备份"
      → if "mcpServers" not in data:
            → data["mcpServers"] = {}
      → if "playwright" not in data["mcpServers"]:
            → data["mcpServers"]["playwright"] = {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]}
            → json.dump(data, indent=2) 写回
      → else:
            → 跳过（用户已配）
```

### Step 9 Detail: Runtime Verification

Agent 运行 `python .scripts/verify-runtime.py`（Step 2 装完的全局环境）。

检查 12 项（3 层）：
- Layer 1 系统：Python、Node.js、npx、curl
- Layer 2 Python 包：yfinance、openpyxl、requests、python-dotenv、pyyaml、lxml
- Layer 3 配置：`.claude/mcp.json` 含 playwright key、`.claude/hooks/` 可 import

**任一项 ❌ → 自动装 → 再查 → 还不行 → 打印手动命令 + STOP。**

全部 ✅ 才报告 "workspace ready"，继续 Step 10-11。

### Core dependencies

```bash
pip install yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx
```

### Platform detection

Agent uses `sys.platform`:
- `win32` → Windows: Python = `python`
- `darwin` / other → Unix: Python = `python3`

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
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 5    │ Whisper   │ WHISPER_API_KEY               │ 用户自备 OpenAI 兼容端点        │
│      │ (转录)    │ WHISPER_API_BASE              │ 如有默认 key 直接贴入 .env       │
│      │           │ WHISPER_MODEL                 │                                │
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

# Whisper（转录，OpenAI 兼容 API）
# WHISPER_API_KEY=sk-xxx
# WHISPER_API_BASE=https://api.vveai.com/v1
# WHISPER_MODEL=whisper-large-v3-turbo
```

`.gitignore` already includes `.env` — the file stays local and is never committed.

## File Safety

- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md` — copy from template only if missing.
- Do not overwrite `COVERAGE.md` or `.references/edge-radar.md` if already present.
- `.claude/mcp.json`: merge strategy — preserve existing MCP server keys, ensure `playwright` key exists. If file is invalid JSON, backup to `.claude/mcp.json.bak` then overwrite.
- Do not overwrite `.scripts/` files that are not in the B类 source list (user-added scripts are preserved).
- Do not run inside the plugin dev repo or plugin install directory.

## Workflow Links

| Scenario | Handling |
|---|---|
| User wants to upgrade plugin + sync workspace | Use `update-agent-runtime` |
| User wants to create a new topic | Automatic — save artifact to target path, scaffolding auto-creates directories |
| User wants to fix workspace runtime only | Use `update-agent-runtime` (or re-run init-workspace in repair mode) |
| User wants daily coverage briefs or intraday alerts | Use `coverage-monitor` after init finishes |

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
- Legacy `.scripts/init-assets/` cleaned up.
- Did not create research artifacts.
