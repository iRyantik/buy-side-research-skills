---
name: coverage-monitor
description: Generate daily coverage briefs and intraday material-event alerts from workspace coverage state.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Coverage Monitor

`coverage-monitor` turns workspace coverage state into a monitoring loop: normalize `COVERAGE.md`, build the watchlist from researched companies, generate a daily brief, and send intraday alerts for material events on the highest-priority names. It is an operations skill, not a research skill.

## Mindset

This skill does not create another research memo. It converts the coverage state already stored in the workspace into an actionable monitoring surface. It is designed for an Asia-timezone buy-side researcher who needs daytime monitoring for local/Europe names and fast post-print handling for US names at night.

Two failure modes matter most: turning it into a positions or P&L tracker, or making the alert threshold so loose that noise overwhelms signal. v1 stays inside `COVERAGE.md`, research priority, and material-event alerting only.

## Responsibilities

Responsible for:

- Reading workspace `COVERAGE.md` and existing artifacts under `industry/*/companies/*`.
- Normalizing the coverage table to canonical columns.
- Generating the fixed five-section daily coverage brief.
- Running intraday material-event alerts for the `A1` watchlist only.
- Delivering output through email and WeCom webhook.
- Failing honestly when quote/news or delivery credentials are unavailable.

Not responsible for:

- Position tracking, cost basis, P&L, exposure, or broker accounts.
- Rewriting research conclusions, generating theses, or replacing `coverage-tracker`.
- Depending on FMP, EODHD, or any paid API in v1.
- Personal WeChat automation.

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
- `coverage-tracker` owns `Research Tier`, `Alert Tier`, `Last Review`, and `Next Trigger`.
- `industry/*/companies/*` is used to discover researched companies that were never registered.
- Optional delivery env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `COVERAGE_EMAIL_TO`, `WECOM_WEBHOOK_URL`.

## Execution Modes

### Mode A: `doctor`

Check workspace visibility, coverage entry count, and delivery-env gaps. No files are written.

### Mode B: `normalize-coverage`

Rewrite legacy or inconsistent `COVERAGE.md` headers into the canonical table. `--dry-run` prints the normalized output only.

### Mode C: `daily`

Generate the fixed five-section daily brief:

1. `Top Alerts`
2. `Industry Coverage`
3. `Upcoming Triggers`
4. `Data & Monitor Gaps`
5. `Appendix: Full Watchlist Snapshot`

Normal mode writes:

```text
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.md
reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.html
```

### Mode D: `intraday`

Scan only the `A1` watchlist for material events. Default behavior is one pass; `--interval-minutes` enables polling. Sent events are deduplicated.

## Tool Resources

- Workspace script entrypoint: `python .scripts/coverage-monitor/run_coverage_monitor.py`
- Provider path: optional `yfinance` quote/news snapshot
- Delivery path: Python stdlib `smtplib` + WeCom webhook

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
- [A1 / A2 / A3 distribution]

## Delivery
- [email sent / skipped]
- [wecom sent / skipped]

## Gaps
- [...]
```

Daily brief files always use the fixed five-section structure. `intraday` outputs only the triggered alert list and event explanation, not a long research memo.

Artifact policy:

- `save_policy`: `cache_artifact`
- `default_artifact`: `daily-coverage-brief.md`
- `canonical_location`: `reports/coverage-monitor/YYYY-MM-DD-daily-coverage-brief.md`

## Failure Handling

- Missing `COVERAGE.md`: continue with company discovery from `industry/*/companies/*` and report the gap.
- Missing ticker: keep the row in the appendix, downgrade to `A3`, and skip intraday alerts.
- `yfinance` unavailable: continue report generation and record `yfinance_unavailable`.
- Missing email or WeCom credentials: continue report generation and record delivery gaps instead of claiming success.
- Missing workspace path: exit with a non-zero code.

## Workflow Links

| Upstream | Role |
|---|---|
| `coverage-tracker` | Provides `Research Tier`, `Alert Tier`, `Last Review`, and `Next Trigger` |
| `stock-quickread` / `alpha-thesis` / `earnings-setup` / `post-earnings-quick` | Their outputs should push coverage state and trigger updates |
| `research-journal` | Explains why coverage state changed |

| Downstream | Role |
|---|---|
| Daily researcher workflow | Daily brief every day; intraday alerts for `A1` only |
| `/update-agent-runtime` | Syncs this skill's scripts into workspace `.scripts/coverage-monitor/` |

## Safety Self-Check

- ❌ Turning this skill into a research report template.
- ❌ Tying `Research Tier` or `Alert Tier` to subjective conviction.
- ❌ Introducing broker, P&L, or positions data.
- ❌ Reporting "sent" when delivery env is missing.
- ❌ Spamming intraday alerts for `A2` or `A3` by default.
- ❌ Inventing a watchlist without workspace artifacts.
