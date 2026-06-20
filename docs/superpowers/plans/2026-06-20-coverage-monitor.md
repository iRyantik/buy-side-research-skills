# Coverage Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a plugin-native coverage monitoring workflow that turns workspace research coverage into objective tiers, sends a daily coverage brief by email/WeCom, and can run intraday alerts for material events.

**Architecture:** Keep `coverage-tracker` as the source of workspace coverage state, add a new `coverage-monitor` operations skill for reports/alerts, and ship shared Python scripts through the existing `update-agent-runtime` skill-script sync path. The first version uses local `COVERAGE.md` plus workspace artifact discovery as the canonical universe, optional market/news providers as inputs, and graceful degradation when live data or delivery credentials are missing.

**Tech Stack:** Python stdlib-first, optional `yfinance` for price snapshots if installed, SMTP for email, WeCom webhook for WeChat-style delivery, Markdown/HTML report output, pytest/compileall validation, existing plugin release workflow.

---

## File Structure

- Create `plugins/buy-side-research-skills/skills/coverage-monitor/SKILL.md`, `SKILL.en.md`, and `skill.yaml` for the new operations skill.
- Create `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/` modules:
  - `coverage.py` parses and normalizes `COVERAGE.md` and discovers researched companies.
  - `tiering.py` derives objective research and alert tiers.
  - `market_data.py` fetches optional quotes/news and fails honestly.
  - `reports.py` renders the five-section daily brief and intraday alert cards.
  - `delivery.py` sends email and WeCom webhook messages.
  - `state.py` stores dedupe/run state under workspace `.cache/coverage-monitor/`.
  - `cli.py` implements `daily`, `intraday`, `doctor`, and `normalize-coverage`.
- Create `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/run_coverage_monitor.py` as the workspace-facing entrypoint copied by `update-agent-runtime`.
- Add tests under `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/`.
- Modify `coverage-tracker` docs only to make tiering objective and explicitly feed `coverage-monitor`.
- Modify `init-workspace` templates so new workspaces get the objective coverage table columns and monitor env placeholders.
- Modify README/release/manifests for the new skill and release version.
- Do not edit user research workspace files directly. Do not overwrite the existing dirty `plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md` change unless the diff proves it is part of this task.

## Task 1: Preflight And Dirty-File Protection

**Files:**
- Inspect: repo root git state
- Inspect: `plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md`

- [ ] **Step 1: Confirm current branch and dirty files**

Run:

```powershell
git status --short
git branch --show-current
```

Expected:

```text
 M plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md
```

If additional files appear, inspect them before editing and do not revert user changes.

- [ ] **Step 2: Snapshot the dirty stock-quickread diff**

Run:

```powershell
git diff -- plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md
```

Expected: review-only output. Do not modify this file unless the implementation explicitly needs to add a coverage-monitor handoff; if it does, preserve all existing dirty hunks.

- [ ] **Step 3: Confirm release version baseline**

Run:

```powershell
rg -n '"version": "5\.36\.0"|v5\.36\.0|Current release version: `5\.36\.0`' README.md docs/release.md .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/buy-side-research-skills/.claude-plugin/plugin.json plugins/buy-side-research-skills/.codex-plugin/plugin.json
```

Expected: version references are `5.36.0`. Use `5.37.0` for this release unless `git tag --list v5.37.0` already exists; if it exists, use `5.37.1`.

## Task 2: Build Shared Coverage Table Parser

**Files:**
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/coverage.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_coverage_table.py`

- [ ] **Step 1: Write tests for old and new coverage tables**

Create tests covering:

```python
from coverage_monitor.coverage import parse_coverage_markdown, render_coverage_markdown


def test_parse_legacy_coverage_table():
    text = """# Coverage Map

| 行业 | 公司 | Ticker | 主行业 | 文件位置 | 最新 artifact | 状态 |
|---|---|---|---|---|---|---|
| optical-module-equipment | Mycronic | MYCR.ST | equipment | industry/optical-module-equipment/companies/mycronic | 2026-05-30-stock-quickread-mycronic.md | active |
"""
    rows = parse_coverage_markdown(text)
    assert rows[0].ticker == "MYCR.ST"
    assert rows[0].company == "Mycronic"
    assert rows[0].industry == "optical-module-equipment"
    assert rows[0].stage == "active"


def test_render_normalized_columns():
    rows = parse_coverage_markdown("""## Coverage
| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 6777.T | santec | optical-module-equipment | T1 | A1 | active | 2026-06-01 | earnings | yes | core |
""")
    output = render_coverage_markdown(rows)
    assert "| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |" in output
    assert "| 6777.T | santec | optical-module-equipment | T1 | A1 | active | 2026-06-01 | earnings | yes | core |" in output
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_coverage_table.py -q
```

Expected: FAIL because `coverage_monitor` does not exist.

- [ ] **Step 3: Implement parser and renderer**

Implement a dataclass with these stable fields:

```python
@dataclass
class CoverageEntry:
    ticker: str
    company: str
    industry: str = ""
    research_tier: str = ""
    alert_tier: str = ""
    stage: str = ""
    last_review: str = ""
    next_trigger: str = ""
    monitor: str = ""
    notes: str = ""
    source_path: str = ""
    latest_artifact: str = ""
```

Rules:

- Parse both legacy columns (`行业`, `公司`, `主行业`, `文件位置`, `最新 artifact`, `状态`) and new columns.
- Normalize empty ticker/company to `""`; never fabricate a ticker.
- Render only the new canonical columns: `Ticker`, `Company`, `Industry`, `Research Tier`, `Alert Tier`, `Stage`, `Last Review`, `Next Trigger`, `Monitor`, `Notes`.
- Preserve row order.

- [ ] **Step 4: Re-run parser tests**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_coverage_table.py -q
```

Expected: PASS.

## Task 3: Implement Objective Tiering

**Files:**
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/tiering.py`
- Modify: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_coverage_table.py`
- Modify: `plugins/buy-side-research-skills/skills/coverage-tracker/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/coverage-tracker/SKILL.en.md`
- Modify: `plugins/buy-side-research-skills/skills/coverage-tracker/skill.yaml`

- [ ] **Step 1: Add tests proving tiering is objective**

Add tests:

```python
from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.tiering import derive_research_tier, derive_alert_tier


def test_research_tier_uses_artifacts_trigger_and_recency_not_conviction():
    entry = CoverageEntry(
        ticker="MYCR.ST",
        company="Mycronic",
        stage="active",
        last_review="2026-06-01",
        next_trigger="2026-07-15 earnings",
        notes="conviction unknown",
    )
    assert derive_research_tier(entry, today="2026-06-20", artifact_count=3) == "T1"

    entry.notes = "High conviction"
    entry.next_trigger = ""
    assert derive_research_tier(entry, today="2026-06-20", artifact_count=3) == "T2"


def test_alert_tier_is_separate_from_research_tier():
    entry = CoverageEntry(ticker="6777.T", company="santec", research_tier="T1", monitor="yes")
    assert derive_alert_tier(entry) == "A1"
    entry.monitor = "daily"
    assert derive_alert_tier(entry) == "A2"
    entry.monitor = "no"
    assert derive_alert_tier(entry) == "A3"
```

- [ ] **Step 2: Implement tiering**

Use these objective rules:

- `Research Tier`:
  - `T1` Core: ticker exists and either `monitor=core`, `next_trigger` is non-empty and `last_review` is within 90 days, or artifact count is at least 3 and `stage` is `active`/`testing`.
  - `T2` Active: ticker exists and either artifact count is at least 1, `last_review` is present, or `stage` is `building`/`monitoring`.
  - `T3` Radar: company exists but ticker is missing or only legacy coverage metadata exists.
  - `T4` Dormant: `stage=dormant` or `monitor=no`.
- `Alert Tier`:
  - `A1` Intraday: `T1` and monitor is not `no`.
  - `A2` Daily-only: `T2` or explicit `monitor=daily`.
  - `A3` Archive/no alert: `T3`, `T4`, `monitor=no`, or missing ticker.

Do not use `conviction` or free-text investment opinion to derive tier.

- [ ] **Step 3: Update coverage-tracker docs**

Rewrite its tier section to:

- State that `coverage-tracker` owns coverage state, not market monitoring.
- Remove wording that defines Tier as subjective weekly time allocation.
- Define `Research Tier` and `Alert Tier` using the rules above.
- State that `coverage-monitor` consumes the table for daily/intraday reporting.
- Keep boundary: not portfolio tracker, not P&L tracker.

Keep `SKILL.md` and `SKILL.en.md` content-density aligned.

- [ ] **Step 4: Update coverage-tracker metadata**

Set `description` in `SKILL.md` frontmatter and `skill.yaml` to the same concise English line:

```text
Maintain objective workspace coverage state with research tiers, alert tiers, review dates, and next triggers.
```

Update `skill.yaml` requirements to include `research_tier`, `alert_tier`, `last_review`, and `next_trigger`.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_coverage_table.py -q
```

Expected: PASS.

## Task 4: Add Coverage Monitor Skill Contract

**Files:**
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/SKILL.md`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/SKILL.en.md`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/skill.yaml`

- [ ] **Step 1: Add skill frontmatter and metadata**

Use this exact description in both frontmatter and `skill.yaml`:

```text
Generate daily coverage briefs and intraday material-event alerts from workspace coverage state.
```

Set `research_layer: operations`, tags including `coverage-monitor`, `daily-brief`, `intraday-alerts`, `email`, `wecom`, and trigger keywords including `coverage monitor`, `daily coverage brief`, `monitor my coverage`, `持仓监控`, `覆盖日报`, `盘中提醒`.

- [ ] **Step 2: Write the runtime contract**

`SKILL.md` must specify:

- Inputs: root `COVERAGE.md`, discovered `industry/<industry>/companies/<company>/` artifacts, optional quote/news provider, optional delivery env.
- Daily report sections, exactly:
  1. `Top Alerts`
  2. `Industry Coverage`
  3. `Upcoming Triggers`
  4. `Data & Monitor Gaps`
  5. `Appendix: Full Watchlist Snapshot`
- Intraday behavior: alert only `A1` by default, dedupe repeated events, degrade to report-only if delivery credentials are absent.
- Delivery: email via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `COVERAGE_EMAIL_TO`; WeChat-style delivery via `WECOM_WEBHOOK_URL`.
- Boundary: no portfolio P&L, no position sizing, no broker connection, no personal WeChat automation in v1, no paid FMP/EODHD dependency in v1.

- [ ] **Step 3: Write the English mirror**

`SKILL.en.md` must contain the same contract density and the same section list, env var names, and boundaries.

## Task 5: Implement Universe Builder And CLI Skeleton

**Files:**
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/__init__.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/cli.py`
- Modify: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/coverage.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/run_coverage_monitor.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_cli.py`

- [ ] **Step 1: Add CLI tests**

Create tests:

```python
from pathlib import Path
from coverage_monitor.cli import build_universe


def test_build_universe_from_coverage_and_artifacts(tmp_path: Path):
    (tmp_path / "COVERAGE.md").write_text(
        """## Coverage
| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MYCR.ST | Mycronic | optical-module-equipment |  |  | active | 2026-06-01 | Q2 results | yes |  |
""",
        encoding="utf-8",
    )
    company_dir = tmp_path / "industry" / "optical-module-equipment" / "companies" / "mycronic"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-05-30-stock-quickread-mycronic.md").write_text("# Mycronic", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].ticker == "MYCR.ST"
    assert universe.entries[0].research_tier == "T1"
    assert universe.entries[0].alert_tier == "A1"
    assert universe.entries[0].source_path.endswith("industry/optical-module-equipment/companies/mycronic")


def test_build_universe_discovers_company_without_coverage_row(tmp_path: Path):
    company_dir = tmp_path / "industry" / "semicap" / "companies" / "santec"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-06-01-stock-quickread-santec.md").write_text("# santec", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].company == "santec"
    assert universe.entries[0].research_tier == "T3"
    assert universe.entries[0].alert_tier == "A3"
```

- [ ] **Step 2: Implement universe builder**

Behavior:

- Read `COVERAGE.md` when present.
- Discover company directories under `industry/*/companies/*`.
- Merge by normalized company slug and ticker where possible.
- Count markdown artifacts in each company directory.
- Set `source_path` to the company directory when discovered.
- Derive missing `research_tier` and `alert_tier`.
- Do not mutate `COVERAGE.md` during `build_universe`.

- [ ] **Step 3: Implement CLI commands**

`run_coverage_monitor.py` should call `coverage_monitor.cli.main()`.

`cli.py` should support:

```text
python .scripts/coverage-monitor/run_coverage_monitor.py doctor
python .scripts/coverage-monitor/run_coverage_monitor.py normalize-coverage --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py daily --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py intraday --once --dry-run
```

Exit codes:

- `0`: command succeeded, even if optional delivery or market data degraded.
- `2`: workspace root not found or coverage parse failed.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_cli.py -q
```

Expected: PASS.

## Task 6: Implement Reports, State, Market Data, And Delivery

**Files:**
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/reports.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/state.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/market_data.py`
- Create: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/coverage_monitor/delivery.py`
- Add tests: `plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests/test_reports.py`

- [ ] **Step 1: Add report tests**

Create tests:

```python
from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.reports import render_daily_markdown, should_alert_intraday


def test_daily_report_has_fixed_five_sections():
    text = render_daily_markdown(
        entries=[CoverageEntry(ticker="MYCR.ST", company="Mycronic", industry="optical-module-equipment", research_tier="T1", alert_tier="A1")],
        snapshots={},
        today="2026-06-20",
        gaps=["WECOM_WEBHOOK_URL missing"],
    )
    for heading in [
        "## 1. Top Alerts",
        "## 2. Industry Coverage",
        "## 3. Upcoming Triggers",
        "## 4. Data & Monitor Gaps",
        "## 5. Appendix: Full Watchlist Snapshot",
    ]:
        assert heading in text


def test_intraday_alert_only_for_a1_material_events():
    entry = CoverageEntry(ticker="MYCR.ST", company="Mycronic", alert_tier="A1")
    assert should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
    entry.alert_tier = "A2"
    assert not should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
```

- [ ] **Step 2: Implement daily report renderer**

Rules:

- Group company rows by `industry`.
- `Top Alerts` includes material quote/news events and missing critical data for `A1`.
- `Industry Coverage` lists all `T1`/`T2` names grouped by industry.
- `Upcoming Triggers` sorts rows with non-empty `next_trigger`.
- `Data & Monitor Gaps` lists missing ticker, missing provider, missing delivery env, and parse warnings.
- `Appendix` includes all rows including `T3`/`T4`.

- [ ] **Step 3: Implement market data adapter**

Rules:

- Try importing `yfinance`; if unavailable, return gap `yfinance_unavailable` and continue.
- Quote snapshot fields: `last_price`, `price_move_pct`, `currency`, `market_time`, `provider`.
- News snapshot fields: `headline`, `url`, `published_at`, `provider`.
- Do not add FMP/EODHD in this release. Leave provider interface simple enough to add paid APIs later.

- [ ] **Step 4: Implement state and dedupe**

Use workspace path:

```text
.cache/coverage-monitor/state.json
```

State keys:

- `last_daily_report_date`
- `sent_event_ids`
- `last_intraday_run_at`

Event id:

```text
{ticker}|{event_type}|{event_date_or_headline_hash}
```

- [ ] **Step 5: Implement delivery**

Email:

- Send via `smtplib` only if `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, and `COVERAGE_EMAIL_TO` exist.
- Default `SMTP_PORT=587`.
- Return a delivery gap instead of raising for missing env.

WeCom:

- Send JSON text/card payload to `WECOM_WEBHOOK_URL` if present.
- If absent, return `WECOM_WEBHOOK_URL missing`.
- Do not implement personal WeChat automation.

- [ ] **Step 6: Wire CLI daily and intraday**

`daily --dry-run` prints report path and delivery gaps without sending.

`daily` writes:

```text
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.md
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.html
```

`intraday --once --dry-run` prints alert candidates without sending.

`intraday --interval-minutes 15` loops until interrupted and writes state each run.

- [ ] **Step 7: Run tests**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests -q
```

Expected: PASS.

## Task 7: Update Init Workspace And Research Workflow Docs

**Files:**
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/coverage.md.template`
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/env-setup.ps1.template`
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/SKILL.md`
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/SKILL.en.md`
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.md.template`
- Modify: `plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.en.md.template`
- Modify if present: core company-flow skills that mention coverage handoff, especially `research-journal`, `alpha-thesis`, `earnings-setup`, `post-earnings-quick`, and existing dirty `stock-quickread` only with hunk-preserving edits.

- [ ] **Step 1: Update coverage template**

Set the new default table:

```markdown
# Coverage Map

> 本文件是 workspace coverage source of truth。研究过的公司进入表；`coverage-monitor` 消费本表生成日报和盘中提醒。

| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |
|---|---|---|---|---|---|---|---|---|---|
```

- [ ] **Step 2: Add monitor env placeholders**

In `env-setup.ps1.template`, add comments only:

```powershell
# Coverage Monitor delivery (optional)
# $env:SMTP_HOST=""
# $env:SMTP_PORT="587"
# $env:SMTP_USER=""
# $env:SMTP_PASSWORD=""
# $env:COVERAGE_EMAIL_TO=""
# $env:WECOM_WEBHOOK_URL=""
```

Do not add automatic credential validation logic.

- [ ] **Step 3: Update init-workspace docs**

Add `coverage-monitor` to the workspace capability summary:

- `coverage-tracker` maintains objective coverage state.
- `coverage-monitor` consumes that state for daily/intraday monitoring.
- `update-agent-runtime` copies skill scripts into `.scripts/coverage-monitor/`.

Mirror the same content in `SKILL.en.md`.

- [ ] **Step 4: Update workflow handoffs**

Add short handoff language:

- `stock-quickread`: after saving a company artifact, ensure company exists in coverage with `T3` or better.
- `alpha-thesis`: completed thesis should update `last_review`, `stage`, and `next_trigger`; do not set tier from conviction.
- `earnings-setup`/`post-earnings-quick`: update `next_trigger` and last review after earnings.
- `research-journal`: record why coverage state changed.

Keep edits minimal. Preserve any existing dirty `stock-quickread` changes.

## Task 8: Public Docs, Manifests, And Version Bump

**Files:**
- Modify: `README.md`
- Modify: `docs/README.cn.md` if it mirrors the catalog/version sections
- Modify: `docs/release.md`
- Modify: `plugins/buy-side-research-skills/.claude-plugin/plugin.json`
- Modify: `plugins/buy-side-research-skills/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.agents/plugins/marketplace.json`

- [ ] **Step 1: Update README skill count and catalog**

Increment skill count from `39` to `40`.

Add `coverage-monitor` to the Memory or Operations area:

```markdown
| `coverage-monitor` | Daily coverage briefs and intraday material-event alerts | "Send today's coverage brief" |
```

Add version history row:

```markdown
| v5.37.0 | 2026-06-20 | coverage-monitor skill: objective coverage tiers, daily coverage brief, intraday alert runner, email/WeCom delivery, and normalized COVERAGE.md contract. |
```

- [ ] **Step 2: Update manifests**

Set all seven version surfaces to `5.37.0` unless the tag already exists:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `plugins/buy-side-research-skills/.claude-plugin/plugin.json`
- `plugins/buy-side-research-skills/.codex-plugin/plugin.json`
- `docs/release.md`
- `README.md`
- later git tag `v5.37.0`

Update plugin keywords/default prompts to include `coverage-monitor`, `daily-brief`, `intraday-alerts`, `coverage-monitoring`.

- [ ] **Step 3: Update release docs**

In `docs/release.md`, add `skills/coverage-monitor/...` to release package contents and set current version to `5.37.0`.

## Task 9: Full Validation

**Files:**
- All changed files

- [ ] **Step 1: Run unit tests**

Run:

```powershell
python -m pytest plugins/buy-side-research-skills/skills/coverage-monitor/scripts/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run Python syntax checks**

Run:

```powershell
python -m compileall -q plugins/buy-side-research-skills/skills/coverage-monitor/scripts
```

Expected: exit code `0`.

- [ ] **Step 3: Run CLI smoke tests**

Run from repo root:

```powershell
python plugins/buy-side-research-skills/skills/coverage-monitor/scripts/run_coverage_monitor.py doctor --workspace .
python plugins/buy-side-research-skills/skills/coverage-monitor/scripts/run_coverage_monitor.py daily --workspace . --dry-run
python plugins/buy-side-research-skills/skills/coverage-monitor/scripts/run_coverage_monitor.py intraday --workspace . --once --dry-run
```

Expected:

- `doctor` reports workspace detection and optional env gaps without crashing.
- `daily --dry-run` prints report preview or path without sending.
- `intraday --once --dry-run` reports candidates/gaps without sending.

- [ ] **Step 4: Validate skill metadata shape**

Run:

```powershell
rg -n '^description:' plugins/buy-side-research-skills/skills/coverage-monitor plugins/buy-side-research-skills/skills/coverage-tracker -g SKILL.md
rg -n '^summary:|^description:' plugins/buy-side-research-skills/skills/coverage-monitor plugins/buy-side-research-skills/skills/coverage-tracker -g skill.yaml
```

Expected: frontmatter `description` and `skill.yaml` description match for both changed skills.

- [ ] **Step 5: Validate no accidental runtime scope creep**

Run:

```powershell
git diff --name-only
```

Expected changed files are limited to new `coverage-monitor`, docs/templates/metadata, release docs/manifests, and explicitly reviewed adjacent skill docs. No financial-data provider, hook, requirements, or user workspace files should be modified.

## Task 10: Commit, Push, And Release

**Files:**
- Git state and GitHub release only

- [ ] **Step 1: Review final diff**

Run:

```powershell
git diff --stat
git diff -- plugins/buy-side-research-skills/skills/stock-quickread/SKILL.md
```

Expected: stock-quickread diff contains preserved pre-existing hunks plus only intentional coverage handoff wording, if any.

- [ ] **Step 2: Commit**

Run:

```powershell
git add README.md docs/README.cn.md docs/release.md .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/buy-side-research-skills/.claude-plugin/plugin.json plugins/buy-side-research-skills/.codex-plugin/plugin.json plugins/buy-side-research-skills/skills/coverage-monitor plugins/buy-side-research-skills/skills/coverage-tracker plugins/buy-side-research-skills/skills/init-workspace
git add plugins/buy-side-research-skills/skills/research-journal plugins/buy-side-research-skills/skills/alpha-thesis plugins/buy-side-research-skills/skills/earnings-setup plugins/buy-side-research-skills/skills/post-earnings-quick plugins/buy-side-research-skills/skills/stock-quickread
git commit -m "feat: add coverage monitor skill"
```

If a listed path is unchanged, Git ignores it. If `stock-quickread` contains unrelated user changes that should not be included, stop and ask before committing.

- [ ] **Step 3: Push**

Run:

```powershell
git push
```

Expected: push succeeds.

- [ ] **Step 4: Create GitHub release**

First confirm no existing tag:

```powershell
git tag --list v5.37.0
```

If empty:

```powershell
git tag v5.37.0
git push origin v5.37.0
gh release create v5.37.0 --title "v5.37.0" --notes "Adds coverage-monitor for objective coverage tiers, daily coverage briefs, intraday alerts, and email/WeCom delivery."
```

If `v5.37.0` exists, use `v5.37.1` and update all version surfaces before tagging.

## Assumptions And Defaults

- First release is script/plugin based, not an `.exe`. A packaged executable can be a later feature after the CLI proves stable.
- WeCom webhook is the supported WeChat-style delivery path. Personal WeChat automation is out of scope.
- Paid APIs such as FMP/EODHD are out of scope for this release. The provider interface should be easy to extend later.
- `coverage-monitor` is not a portfolio tracker: no positions, cost basis, exposure sizing, P&L, or brokerage integration.
- Objective tiering must not depend on analyst conviction text. It uses ticker presence, artifact count, review recency, stage, next trigger, and explicit monitor flags.
- Daily report is industry-grouped and always uses the fixed five-section structure.
- Intraday alerts default to `A1` only to avoid noise.
- Missing market data or delivery credentials must degrade with visible gaps, not block report generation.
