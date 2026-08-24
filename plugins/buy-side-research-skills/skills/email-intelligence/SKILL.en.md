---
name: email-intelligence
description: Review preserved sell-side emails and generate a lightweight buy-side brief of updates, ideas, signals, and meetings.
---

# Email Intelligence

## Philosophy

This skill is not an email-by-email summarizer. It turns preserved sell-side email into a lightweight attention-allocation brief: changes at core names, marginal changes elsewhere in coverage, uncovered companies worth investigating, industry signals, and meetings worth attending.

The preservation and review layers remain separate. Power Automate saves email reliably; this skill reads those files. A New Idea is not the same as a sell-side initiation: the company must be outside coverage, show a substantive change, and fit the current the `## Focus` section of COVERAGE.md lens.

## Responsibilities

It reads `meta.txt`, `body.txt`, `outlook.link.txt`, and attachment filenames; uses `COVERAGE.md` and the `## Focus` section of COVERAGE.md; extracts multiple company items and multiple meetings from roundup emails; deduplicates repeated events; writes the brief; and optionally sends it through the coverage-monitor mail runtime.

It does not configure Power Automate, download broker-gated reports, convert long attachments into research artifacts, change `COVERAGE.md` or the `## Focus` section of COVERAGE.md, or promote ordinary initiations and target-price changes into ideas.

## Triggers and Inputs

Use for “review sell-side email,” “generate an email brief,” “email intelligence,” or meeting-email triage. The default input directory is `EMAIL_INTELLIGENCE_BASE`, falling back to the OneDrive `/Email-AI/` folder. The workspace supplies coverage, focus, output, and state. DeepSeek review requires `DEEPSEEK_API_KEY`.

## Modes

```bash
python .scripts/email-intelligence/run_email_intel.py review
python .scripts/email-intelligence/run_email_intel.py review --dry-run
python .scripts/email-intelligence/run_email_intel.py review --all --no-send
```

The pipeline is `scan → unseen filter → structured review → deterministic routing → merge → HTML → delivery → state`. Only successfully reviewed email is marked seen.

## Report Contract

The brief has five lightweight sections:

1. **Core Watch** — substantive updates for Core names.
2. **Other Coverage** — marginal changes elsewhere in coverage, with a simple action.
3. **New Ideas** — uncovered companies with a substantive change and a clear the `## Focus` section of COVERAGE.md fit.
4. **Industry & Sell-side Signals** — peer read-through, theme facts, and differentiated sell-side views.
5. **Meetings** — each meeting’s identifying information, topic, recommendation, and one-line reason.

The header highlights at most three items. Filtering and failure counts stay in a one-line footer.

## Tools

- Entrypoint: `python .scripts/email-intelligence/run_email_intel.py review`
- AI: DeepSeek OpenAI-compatible API
- Delivery: coverage-monitor SMTP runtime
- State: `.cache/email-intelligence/state.json`
- Output: `daily/email/YYYYMMDD-email-brief-HHMM.html`

## File Safety

The preservation directory, `COVERAGE.md`, and the `## Focus` section of COVERAGE.md are read-only. The skill writes only `daily/email/` and `.cache/email-intelligence/`. It never logs API keys or full attachment contents. Dry-run and `--no-send` never send mail.

## Runtime Output Contract

Return a short result with processed email count, signal and meeting counts, output path, delivery status, and explicit gaps. HTML cards contain only the change, relevance, suggested action, and original-email link. Meeting cards remain informational and light.

## Failure Handling

Missing input or no email does not advance state. Missing API credentials or total review failure exits non-zero. Partial failures remain unseen for retry. Missing Outlook links degrade to sender text. Delivery failures preserve the generated HTML and report the gap.

## Workflow Links

Power Automate, `COVERAGE.md`, and the `## Focus` section of COVERAGE.md feed this skill. New Ideas can route to `stock-quickread` or `candidate-screener`; completed calls can route to `meeting-minutes`; long-file extraction belongs to the future knowledge layer.

## Safety Check

- Do not assume one item or one meeting per email.
- Do not equate initiation with New Idea.
- Do not discard same-industry companies merely because they are uncovered.
- Do not treat routine target changes as differentiated views.
- Do not make meeting cards analytical essays.
- Do not mark failed reviews seen.
- Do not mutate preserved email.
- Do not invent user preferences when the `## Focus` section of COVERAGE.md is absent.
