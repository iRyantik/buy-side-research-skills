---
name: init-workspace
description: Initialize or repair a buy-side research workspace root scaffold — cross-platform (Windows + macOS), Python unified.
---

# Init Workspace

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

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

**Class A — Platform-owned assets** (from `init-workspace/assets/`, copied verbatim to workspace root):

| Source | Destination | Strategy |
|---|---|---|
| `.claude/hooks/` (full tree) | `.claude/hooks/` | Overwrite |
| `.claude/settings.json` | `.claude/settings.json` | Overwrite |
| `.claude/mcp.json` | `.claude/mcp.json` | Merge (ensure `playwright` key exists; preserve user's other MCP config; if invalid JSON, backup then overwrite) |
| `.codex/hooks.json` | `.codex/hooks.json` | Overwrite |
| `.codex/mcp.example.json` | `.codex/mcp.example.json` | Overwrite |
| `references/` | `references/` | Overwrite |
| `references/` (full tree) | `references/` | Overwrite |
| `.scripts/shared/` (full tree) | `.scripts/shared/` | Overwrite |
| `.scripts/verify-runtime.py` | `.scripts/verify-runtime.py` | Overwrite |
| `CLAUDE.md.template` | `CLAUDE.md` | Copy if missing (patch managed sections only) |
| `AGENTS.md.template` | `AGENTS.md` | Copy if missing |
| `
| `coverage.md.template` | `COVERAGE.md` | Copy if missing |
| `
| `.env.template` | `.env.template` | Copy if missing |

**Class B — Skill workspace assets** (auto-discovered; formal spec in `meta-skill` Skill Directory Spec):

> **Self-registration rule**: Each skill self-registers what it needs in the workspace by putting files in `scripts/` or `assets/`. Adding a file → automatically deployed. Zero changes to this skill.

```
for each skill_dir in skills/*/:
    if .platform exists → skip (platform skill, deployed by Class A)

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

> **The rule**: `scripts/` + `assets/` → workspace `.scripts/<skill>/`. No per-file mapping. No per-skill registration.

**Environment setup:**
- Check Python 3.10+ availability.
- Install core Python packages globally with `--user` (no venv, no sudo): `python -m pip install --user yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx`.
- Run `pip install --user -r` for each `.scripts/*/requirements*.txt` found (glob discovery). Failures warn, do not block — heavy dependencies (Docling, etc.) are handled by each skill's `bootstrap.py` on first use.
- Write `.gitignore`.

**Interactive provider configuration:**
- Display a single table of 4 data-provider options (SEC EDGAR, DART, EDINET, FinMind) with their env var names and application URLs.
- User replies with which providers to configure and their keys. Agent writes `.env` (merges with existing `.env` if present).
- Unconfigured providers stay as commented lines in `.env`.
- Coverage-monitor delivery placeholders (`SMTP_*`, `COVERAGE_EMAIL_TO`, `WECOM_WEBHOOK_URL`) ship in `.env.template` only; they are optional and not part of provider credential setup.

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
- "setup research"
- "bootstrap workspace"
- "create research folder"

Required input:

- `WorkspacePath`: an explicit user-owned research workspace path.
- The target path must not be the plugin repo, a plugin install directory, or any folder containing plugin markers such as `.claude-plugin/`, `.codex-plugin/`, or `skills/`.

## Modes

### New Workspace Scaffold

Execute full Steps 0-10 (see Execution Flow below). All files are created.

### Repair Existing Workspace

Execute the same steps. Skip root template files that already exist (CLAUDE.md, AGENTS.md, 

## Execution Flow

```
Step 0  Validate workspace path — must not be inside a plugin repo or install directory
Step 2  Check system dependencies: Python 3.10+, Node.js ≥18, npx, curl
        ★ ALL BLOCK — missing any → auto-install (winget/brew), fail → print manual command + STOP
Step 3  Install core Python packages globally (no venv, no sudo):
          python -m pip install --user yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx
        ★ pip install failure → BLOCK (core packages required for all skills)
Step 4  Deploy Class A files (platform assets from init-workspace/assets/)
        ★ mcp.json: merge strategy (see below)
Step 5  Deploy Class B files (skill scripts to .scripts/<skill>/)
Step 6  pip install --user -r .scripts/*/requirements*.txt (failures warn, do not block)
Step 1  Detect language: Chinese conversation → ZH templates, English conversation → EN templates
Step 7  Interactive provider configuration (see Provider Configuration below)
Step 8  MCP server setup — Longbridge Bridge (market data, US/HK):
          Claude Code: claude mcp add --transport http --scope user longbridge https://openapi.longbridge.com/mcp
          Codex:       codex mcp add longbridge --url https://openapi.longbridge.com/mcp
          ★ OAuth required: CC → /mcp → longbridge → Authenticate, Codex → codex mcp login longbridge
          ★ Skippable — Bridge layer falls back to yfinance + WebSearch if unavailable
Step 9  ★ python .scripts/verify-runtime.py — one-click smoke test
        ★ 12 checks across 3 layers, ALL BLOCK, auto-install missing, fail → STOP
Step 10  Delete .scripts/init-assets/ if present (legacy cleanup)
Step 11 Print deployment summary table
```

### Step 1 Detail: System Dependency Check

Agent checks 4 system tools. **Any missing → auto-install** (winget on Windows, brew on macOS). If install fails → print manual command + **STOP** (do not continue).

| Check | Verify | Auto-install (Windows) | Auto-install (macOS) | Manual fallback |
|---|---|---|---|---|
| Python ≥3.10 | `python --version` | `winget install Python.Python.3.12 --accept-source-agreements` | `brew install python@3.12` | https://python.org |
| Node.js ≥18 | `node --version` | `winget install OpenJS.NodeJS.LTS --accept-source-agreements` | `brew install node` | https://nodejs.org |
| npx | `npx --version` | Comes with Node.js (reinstall Node) | Same | Reinstall Node.js LTS |
| curl | `curl --version` | `winget install curl.curl --accept-source-agreements` | Built-in on macOS | System package manager |

Agent detects platform: `sys.platform == "win32"` → Windows; `sys.platform == "darwin"` → macOS.

Linux: print manual command + STOP (auto-install not supported). User installs via package manager then re-runs `/init-workspace`.

### Step 4 Detail: mcp.json Merge

Agent handles `.claude/mcp.json` as follows:

```
1. if file does not exist:
      → write assets/.claude/mcp.json directly
2. else:
      → try json.load
      → if JSONDecodeError:
            → backup as .claude/mcp.json.bak
            → overwrite with assets/.claude/mcp.json
            → tell user "Old file was invalid JSON; backed up"
      → if "mcpServers" not in data:
            → data["mcpServers"] = {}
      → if "playwright" not in data["mcpServers"]:
            → data["mcpServers"]["playwright"] = {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]}
            → json.dump(data, indent=2) write back
      → else:
            → skip (user already configured)
```

### Step 9 Detail: Runtime Verification

Agent runs `python .scripts/verify-runtime.py` (uses globally-installed packages from Step 2).

12 checks across 3 layers:
- Layer 1 System: Python, Node.js, npx, curl
- Layer 2 Python packages: yfinance, openpyxl, requests, python-dotenv, pyyaml, lxml
- Layer 3 Config: `.claude/mcp.json` has playwright key, `.claude/hooks/` is importable

**Any ❌ → auto-install → re-check → still fails → print manual command + STOP.**

All ✅ → report "workspace ready", continue to Step 10-11.

### Core dependencies

```bash
python -m pip install --user yfinance openpyxl requests python-dotenv pyyaml lxml python-docx python-pptx
```

### Platform detection

Agent uses `sys.platform`:
- `win32` → Windows: Python = `python`, 
- `darwin` / other → Unix: Python = `python3`, 

## Provider Configuration

After file deployment, display a single table and ask the user to configure data providers:

```
[Provider Configuration]

Choose from the 4 data source providers below based on your coverage markets.
Paste the keys for providers you want to configure, or reply "skip" for those you don't need.

┌──────┬───────────┬──────────────────────────────┬────────────────────────────────┐
│ #    │ Provider  │ Env Variable                  │ Registration URL               │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 1    │ SEC EDGAR │ EDGAR_IDENTITY                │ https://efts.sec.gov/          │
│      │ (US)      │ Format: "Name email@domain.com"│ Fill in Name+Email, done       │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 2    │ DART      │ DART_API_KEY                  │ https://opendart.fss.or.kr/    │
│      │ (Korea)   │                               │ Free registration for API Key  │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 3    │ EDINET    │ EDINET_API_KEY                │ https://disclosure2.           │
│      │ (Japan)   │                               │ edinet-fsa.go.jp/              │
├──────┼───────────┼──────────────────────────────┼────────────────────────────────┤
│ 4    │ FinMind   │ FINMIND_TOKEN                 │ https://finmindtrade.com/      │
│      │ (Taiwan)  │                               │ Free registration for Token    │
└──────┴───────────┴──────────────────────────────┴────────────────────────────────┘

If you don't have a key yet, register at the URL listed. If you have one, paste it now.
```

Agent parses the user's free-form reply and writes `.env` (merging with existing `.env` if present). Provider env vars supplied by the user are set; unconfigured providers remain as commented lines.

### .env format

```env
# SEC EDGAR (US stocks)
EDGAR_IDENTITY=Name email@domain.com

# DART (Korean stocks)
# DART_API_KEY=

# EDINET (Japanese stocks)
EDINET_API_KEY=your_key_here

# FinMind (Taiwan stocks)
# FINMIND_TOKEN=
```

`.gitignore` already includes `.env` — the file stays local and is never committed.

## File Safety

- Do not overwrite whole workspace `CLAUDE.md` or `AGENTS.md` — copy from template only if missing.
- Do not overwrite `COVERAGE.md` or `
- `.claude/mcp.json`: merge strategy — preserve existing MCP server keys, ensure `playwright` key exists. If file is invalid JSON, backup to `.claude/mcp.json.bak` then overwrite.
- Do not overwrite `.scripts/` files that are not in the Class B source list (user-added scripts are preserved).
- Do not run inside the plugin dev repo or plugin install directory.

## Workflow Links

| Scenario | Handling |
|---|---|
| User wants to upgrade plugin + sync workspace | Use `update-agent-runtime` |
| User wants to create a new topic | Automatic — save artifact to target path, scaffolding auto-creates directories |
| User wants to fix workspace runtime only | Use `update-agent-runtime` (or re-run init-workspace in repair mode) |
| User wants daily coverage briefs or intraday alerts | Use `coverage-monitor` after init completes |

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
