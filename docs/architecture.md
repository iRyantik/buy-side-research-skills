# Architecture

This repo is the source wrapper for the `buy-side-research-skills` plugin. Runtime research work happens in a user-owned research workspace created by `init-workspace`.

macOS support assumes PowerShell 7 (`pwsh`) is installed. Workspace hook adapters use a cross-platform Python launcher (`.claude/hooks/py` / `.claude/hooks/py.cmd`) that auto-locates Python across machines.

## Source Layout

The canonical plugin payload lives under `plugins/buy-side-research-skills/`:

```text
repo-root/
  .claude-plugin/
    marketplace.json
  .agents/
    plugins/
      marketplace.json
  plugins/
    buy-side-research-skills/
      .claude-plugin/
        plugin.json
      .codex-plugin/
        plugin.json
      skills/
        <skill-name>/
          SKILL.md
          SKILL.en.md
          skill.yaml
          scripts/       (optional — deployed to workspace .scripts/<skill>/)
          assets/        (optional — deployed to workspace .scripts/<skill>/)
  docs/
  examples/
  CLAUDE.md
  README.md
```

## Active Skill Layout

Active skills remain flat inside the payload:

```text
plugins/buy-side-research-skills/skills/<skill-name>/SKILL.md
plugins/buy-side-research-skills/skills/<skill-name>/skill.yaml
```

### Operations Skills

| Skill | Purpose |
|---|---|
| `init-workspace` | Create or repair workspace root scaffold |
| `update-agent-runtime` | Update plugin runtime + sync workspace assets |
| `ingest` | Convert raw materials to markdown cache |
| `financial-data` | Structured financial statements + market snapshots |
| `trusted-market-bridge` | Longbridge MCP: quote, valuation, filings (US/HK/SH/SZ/SG) |
| `meta-skill` | Skill authoring governance |
| `integrate` | Whole-topic directory merge |
| `research-viz` | Research → memo-ready HTML charts |
| `research-journal` | Capture and organize research insights |
| `coverage-monitor` | Track coverage status across companies |

## Workspace Shape

`init-workspace` creates the workspace shell. Topic scaffolding happens automatically when research skills save artifacts.

```text
research-workspace/
  CLAUDE.md
  COVERAGE.md
  _inbox/
  .scripts/
    shared/               ← Platform-owned shared scripts
      browser-cdp.py      ← Real Chrome CDP bridge
      verify-claim.py     ← Source verification (HTTP→CDP→Playwright→curl)
      web-extract.py      ← Web text extraction (--cdp for JS pages)
      pdf-extract.py
      search.py
      ...
    browser-cdp/          ← CDP recipes (twitter, xiaohongshu, etc.)
    financial-data/
    driver-map/
    ingest/
  .references/
  industry/
    <industry-slug>/
      panorama/            ← Industry-wide artifacts by skill
      companies/
        <ticker>/
          [YYYY-MM-DD]-*.md
          .cache/
      RESEARCH.md           ← Industry overview + company registry
      .cache/
```

### Built-in Shared Scripts

| Script | Purpose |
|---|---|
| `shared/browser-cdp.py` | Real Chrome CDP wrapper — bypasses Cloudflare, handles JS rendering |
| `shared/verify-claim.py` | 5-tier source verification: HTTP → CDP → Playwright → curl → UNVERIFIED |
| `shared/web-extract.py` | Clean text extraction (HTTP or `--cdp` for JS pages) |
| `shared/pdf-extract.py` | PDF text + table extraction |
| `shared/search.py` | DDG news search (bilingual, no API key) |
| `verify-runtime.py` | One-click 13-item dependency check + auto-install |

### Cross-Machine Sync

The workspace supports switching between multiple machines. Key rules:

- Workspace and plugin source are **two independent git repos** — both must be committed/pushed
- `python .scripts/verify-runtime.py` auto-installs missing dependencies on each machine
- Chrome remote debugging must be enabled on each machine: `chrome://inspect/#remote-debugging`
- `browser-cdp.py` uses `pip show` fallback for cross-machine Python path detection

## Cache And Modeling Inputs

`financial-data` canonical company cache:

```text
industry/<industry>/companies/<ticker>/.cache/financial-data/
  financials.normalized.json
  actuals-resolved.json
  evidence-pack.json
  source-map.json
  completeness.json
```

`driver-map` canonical company cache:

```text
industry/<industry>/companies/<ticker>/.cache/driver-map/
  driver-map.md
  internal/
    driver-map.json
```

Model workbooks:

```text
industry/<industry>/companies/<ticker>/_models/
  <ticker>-3statement-model.xlsx
  <ticker>-dcf-model.xlsx
  <ticker>-comps-analysis.xlsx
```

## Release Package

Release packages remain flat even though the source repo is nested:

```text
.claude-plugin/
.codex-plugin/
skills/
README.md
```

Release packages must not contain `plugins/`, root `CLAUDE.md`, `docs/`, `examples/`, `.git/`, `dist/`, or local machine state.
