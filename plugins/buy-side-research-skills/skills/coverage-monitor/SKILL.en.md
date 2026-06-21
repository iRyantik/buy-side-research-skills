---
name: coverage-monitor
description: Generate daily coverage briefs and intraday material-event alerts from workspace coverage state.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Coverage Monitor

`coverage-monitor` turns workspace coverage state into a monitoring loop: normalize `COVERAGE.md`, build the watchlist from researched companies, generate a dashboard-style daily brief, and deliver an email summary with the full HTML attachment. It is an operations skill, not a research skill.

## Mindset

This skill does not create another research memo. It converts the coverage state already stored in the workspace into an actionable monitoring surface. It is designed for an Asia-timezone buy-side researcher who needs daytime monitoring for local/Europe names and fast post-print handling for US names at night.

Two failure modes matter most: turning it into a positions or P&L tracker, or making the alert threshold so loose that noise overwhelms signal. v1 stays inside `COVERAGE.md`, research priority, and material-event alerting only.

## Responsibilities

Responsible for:

- Reading the `## Coverage` table in workspace `COVERAGE.md` as the ticker/company/coverage-status source of truth.
- Using existing artifacts under `industry/*/companies/*` only to supplement artifact path, latest artifact, and artifact count.
- Running objective coverage-workflow checks after `stock-quickread` and deep-work artifacts land: quickread promotes to `Building Coverage`, while deep-work only triggers `Core Coverage` review instead of blind auto-upgrades.
- Normalizing the coverage table to canonical columns.
- Generating a dashboard-style daily coverage brief with fixed tabs: `Movers`, `Core Watch`, `Industry Tape`, and `Universe`.
- Running intraday material-event alerts for the `Core Watch` list only.
- Delivering output through email: summary body plus full HTML attachment.
- Failing honestly when quote/news or delivery credentials are unavailable.

Not responsible for:

- Position tracking, cost basis, P&L, exposure, or broker accounts.
- Rewriting research conclusions, generating theses, or replacing `coverage-tracker`.
- Depending on FMP, EODHD, or any paid API in v1.
- Personal WeChat automation.
- Installing OS-level scheduled tasks; daily mode is manually triggered in this version.

## Trigger And Input

Trigger phrases:

- "coverage monitor"
- "daily coverage brief"
- "monitor my coverage"
- "send today's coverage brief"
- "覆盖日报"
- "盘中提醒"

Inputs:

| Input | Purpose |
|---|---|
| `workspace` | Optional. Defaults to the current workspace root. |
| `mode` | `doctor` / `normalize-coverage` / `daily` / `intraday` |
| `today` | Optional override for the report date; `YYYY-MM-DD` |
| `dry_run` | Optional. Render and inspect without writing or sending |

Dependency inputs:

- `COVERAGE.md` is the coverage source of truth.
- `coverage-tracker` owns `Coverage`, `Monitor`, `Last Review`, and `Next Trigger`.
- `industry/*/companies/*` only supplements registered-company artifact metadata; when `COVERAGE.md` exists, unregistered directories are reported as gaps.
- Optional delivery env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `COVERAGE_EMAIL_TO`. The script reads workspace `.env` without overriding existing environment variables.

## Execution Modes

### Mode A: `doctor`

Check workspace visibility, coverage entry count, and delivery-env gaps. No files are written.

### Mode B: `normalize-coverage`

Rewrite legacy or inconsistent `COVERAGE.md` headers into the canonical table. `--dry-run` prints the normalized output only.

### Mode C: `daily`

Generate the dashboard-style daily brief. The HTML always uses 4 tabs:

1. `Movers`
2. `Core Watch`
3. `Industry Tape`
4. `Universe`

`Coverage Gaps` no longer owns its own tab; it lives inside the `Universe` tab alongside the coverage contract and registry table.

Normal mode writes:

```text
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.md
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.html
```

Normal mode also attempts email delivery: summary body plus full HTML dashboard attachment. `--dry-run` renders to stdout only; it does not write files or send email.

### Mode D: `intraday`

Scan only the `Core Watch` list for material events. Default behavior is one pass; `--interval-minutes` enables polling. Sent events are deduplicated.

## Tool Resources

- Workspace script entrypoint: `python .scripts/coverage-monitor/run_coverage_monitor.py`
- Provider path: optional `yfinance` quote/news snapshot
- Delivery path: Python stdlib `smtplib` email only

Example commands:

```bash
python .scripts/coverage-monitor/run_coverage_monitor.py doctor
python .scripts/coverage-monitor/run_coverage_monitor.py normalize-coverage --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py daily --dry-run
python .scripts/coverage-monitor/run_coverage_monitor.py intraday --once --dry-run
```

## File Safety

- Do not modify topic research artifacts directly.
- Only `normalize-coverage` may rewrite `COVERAGE.md`.
- `daily` writes only under `reports/coverage-monitor/` and `.cache/coverage-monitor/state.json`.
- Do not overwrite user `.env`; only read env values.
- Do not touch runtime config files outside this skill's owned surface.

## Output Contract

Default output stays short and actionable:

```markdown
## Coverage Monitor Result

**Bottom line**
[what this run did: doctor / normalization / daily brief / intraday alerts]

## Coverage
- [watchlist count]
- [Core Watch / Daily Watch distribution]

## Delivery
- [email sent / skipped]

## Gaps
- [...]
```

Daily HTML files always use the fixed 4-tab dashboard shell. The visual language references the `today` prototype, but the content is rebuilt around the coverage workflow. Markdown remains a short summary plus the universe table. `intraday` outputs only the triggered alert list and event explanation, not a long research memo.

Artifact policy:

- `save_policy`: `cache_artifact`
- `default_artifact`: `daily-coverage-brief.md`
- `canonical_location`: `reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.md`

## Failure Handling

- Missing `COVERAGE.md`: continue with company discovery from `industry/*/companies/*` and report the gap.
- Missing ticker / `IPO pending` / `private`: keep the row in coverage gaps and skip quote fetching.
- Multi-ticker rows such as `002487 CH / 1081 HK`: use the first ticker as quote primary and all tickers as search aliases.
- `yfinance` unavailable: continue report generation and record `yfinance_unavailable`.
- Missing email credentials: continue report generation and record delivery gaps instead of claiming success.
- Missing workspace path: exit with a non-zero code.

## Workflow Links

| Upstream | Role |
|---|---|
| `coverage-tracker` | Provides `Coverage`, `Monitor`, `Last Review`, and `Next Trigger` |
| `stock-quickread` | Registers or promotes names into `Building Coverage` + `Daily Watch` |
| `alpha-thesis` / `peer-deep-dive` / `earnings-setup` / `scenario-model` / `driver-map` / `catalyst-map` | Trigger `Core Coverage` review prompts without subjective auto-upgrades |
| `research-journal` | Explains why coverage state changed |

| Downstream | Role |
|---|---|
| Daily researcher workflow | Daily brief every day; intraday alerts for `Core Watch` only |
| `/update-agent-runtime` | Syncs this skill's scripts into workspace `.scripts/coverage-monitor/` |

## Safety Self-Check

- ❌ Turning this skill into a research report template.
- ❌ Tying `Coverage` or `Monitor` to subjective conviction.
- ❌ Introducing broker, P&L, or positions data.
- ❌ Reporting "sent" when delivery env is missing.
- ❌ Claiming scheduled delivery is implemented.
- ❌ Spamming intraday alerts for `Daily Watch` by default.
- ❌ Inventing a watchlist without workspace artifacts.
