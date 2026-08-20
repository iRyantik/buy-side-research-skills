# Changelog

## v8.x (2026-07)

| Version | Changes |
|---|---|
| v8.8.5 | workspace-validate-names: TICKERS_WITHOUT_CN_NAME exemption (0522.HK ASMPT - English-only brand, no registered Chinese name); TW company dirs renamed to Chinese (1590.TW-亞德客, 2327.TW-國巨) |
| v8.8.4 | verify-claim --ledger staging + evidence_ledger apply-staging (two-layer fix, batch backfill gone); workspace-validate-names company dir check (CN/HK/TW must be Chinese); quickread SKILL Step 4/7 updated |

| v8.8.3 | market_snapshot_source_boundary rewrite: paragraph-window scan, URL-stripped keyword match, line-numbered block messages, PE/20x/市值 allowed terms, format checks demoted to warn (484->49 blocks on real artifacts) |


| v8.2.1 | Tool alias table, CLAUDE.md section 11 agent behavior rules |
| v8.2.0 | workspace-summary + workspace-validate-names scripts, remove dcf-model/comps-analysis/3-statement-model |
| v8.1.0 | workspace-locate.py, transcribe encoding fix, meeting-minutes workspace awareness + naming enforcement |
| v8.0.0 | Colleague-ready: Python auto-install, PreToolUse hooks, VS Code extension support, all hardcoded paths removed |

## v7.x (2026-07)

| Version | Changes |
|---|---|
| v7.6.35 | P0-P2 bug fixes: pdf_auto_cache typo, subagent_protocol dispatch, merge conflicts, pip --user, tempfile |
| v7.6.30 | Version bump + install.md rewrite |
| v7.6.27 | delete-session.py interactive mode |
| v7.6.25 | Orphan session cleanup (zero-delay, manifest-synced) |
| v7.6.22 | Instant orphan cleanup |
| v7.6.20 | Auto-clean orphan session transcripts on CC Stop |
| v7.6.18 | question-sharpener: flip from router to question sharpener |
| v7.6.16 | Artifact date rules — auto current date, update-on-substance-change |
| v7.6.14 | Artifact naming v5 — bracket format |
| v7.6.12 | Artifact naming v4 — YYYYMMDD format |
| v7.6.10 | Industry directory rename — native case with spaces |
| v7.6.8 | Naming convention: dot ticker, single dash, CN-only Chinese names |
| v7.6.5 | Cross-machine sync docs (CLAUDE.md §9) |
| v7.6.2 | Init-workspace assets sync — 9 script dirs, §9 cross-machine, coverage schema |
| v7.6.1 | §9 cross-machine sync — new machine setup, dual repo discipline, switch workflow |
| v7.5.2 | pip show fallback for cross-machine Python path detection |
| v7.5.1 | browser-cdp recipes + sync subdirectory support |
| v7.5.0 | browser-harness CDP tier |

## v6.x (2026-06)

| Version | Changes |
|---|---|
| v6.7.0 | driver-map v1.4.0: CF/HL/BOLD helpers, yoy module |
| v6.5.14 | RAG 4-tier fallback, Evidence Ledger, sentence-end anchors |
| v6.5.9 | Removed verification badges from source anchors |

## v5.x (2026-05—06)

| Version | Changes |
|---|---|
| v5.4.0 | Source contract injection (27 skill output tables + Ev column) |
| v5.3.0 | Actuals-only ratio constraint |
| v5.2.1 | Directory auto-discovery |
| v5.1.0 | Python unified bootstrap, init-workspace rewrite |
| v5.0.0 | 7 new skills, regime-based candidate screener, full-chain hook governance |
