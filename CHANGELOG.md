# Changelog

## v8.x (2026-07)

| Version | Changes |
|---|---|
| v8.8.20 | **数据新鲜度 + universe 全量修复**：filter_entries us 视为全量（改 am→us 时漏改导致 universe/queue 只剩美股）；数据新鲜度（Universe 加行情时间列显示数据日期 + 早于今天标旧；hero 各市场时点摘要；FMP quote 无精确时间戳，fallback 采集日） |
| v8.8.19 | **邮件升级（HTML 正文）**：标题带市场（US Post-Market/Asia Close/Europe Close）；mover 附 claude 归因原因 + 证据链接（原用 enrichment 空数据导致无原因）；Upcoming Earnings（未来 7 天财报区块）；Core Watch 显示 1m/YTD/1y + PE/EV 估值 + lead 新闻；公司名中文优先（_display_name 与 html 一致）；正文改 HTML（<a> 链接文字，非裸 URL，支持邮件客户端）；mover/Core 每家空行分隔 |
| v8.8.18 | **日报产物整理 + 命名修正**：md 收进 daily/md/ 子目录（根目录只留 html，用户只看 html）；report_type am→us（07:45 日报实为美股盘后），文件名 YYYYMMDD-brief-us.html、launchd 与显示标签同步 |
| v8.8.17 | **HTML 日报响应式（手机 + 大屏兼顾）**：手机端 ≤640px 紧凑布局（字号/间距/卡片）+ Universe 表隐藏次要列保留核心列 + 卡片网格 auto-fill 自适应任意屏 + safe-area 适配；表格列距收紧 （company/ticker 贴紧，min-width 桌面 1250→1000 / 手机 640→420，列贴合内容不拉伸）；手机表头 sticky 冻结修复（容器滚动恢复 58vh）；Universe 列 class 修复（手机端公司名正确显示） |
| v8.8.16 | **定时调度 + 新闻归因质量**：launchd 定时跑 claude 检测修复（已知路径兜底，不再因 PATH 缺 ~/.local/bin 退化为规则 fallback 机械复刻）；周末跳过（脚本层 datetime 判断，launchd Weekday 数组 macOS 实测不可靠）；新闻页面过滤（标题黑名单：资金流/异动/行情/荐股/散户页面 + 来源分层：investing/benzinga/seekingalpha 等聚合站）；归因质量（事件方向映射 利好/利空 + 逆向标注 + claude 审查 prompt 归因分「公司特定/板块联动/宏观」）；时间窗对齐（新闻影响交易日映射：盘前/盘中→当日、盘后→下一交易日，窗口 ±2 天过滤上周新闻） |
| v8.8.15 | **估值数据修复 + init-workspace assets 同步**：NTM 年度选择修复（FMP analyst-estimates 倒序 → _pick_ntm_period 按 date 取最近未来财年；RHM PE_NTM 9.1x→21.1x 等 117 家受益）；CoverageEntry.val_anchor 字段缺失修复（非 skip-fetch 估值崩溃）；FMP .L 伦敦 pence/pound 单位归一化（BA.L 2218x→22.2x、RR.L 3004x→30.0x）；init-workspace assets 同步 coverage-monitor/financial-data/reddit-sentiment 最新脚本（含 _cache→.cache 路径修正） |
| v8.8.14 | **coverage-monitor AI 机制 + estimates 层 + 估值数据源统一**：公司名保护替换（protect_names，防音译错乱）；movers 审查分块（claude CLI ≤8家/块，块失败规则 fallback）；标题 agent 翻译闭环（--ai-review-input → translate_titles.py → --ai-review，agent 批量翻译，不用外部 API）；agent_session 固定会话（--session-id/--resume，修相对导入越界）；LIG D&A / AGC 改名。estimates 层：estimates-resolved.json 全局单文件（`.cache/estimates/`）+ L1 forward / L2 consensus 分级 + fill（FMP analyst-estimates 全 COVERAGE）/ scan 接入 + 日报 Data Health 缺 estimate 汇总 + 估值列 L1 优先（`L1 fwd` 标注）+ set-forward CLI；driver-map/model-update SKILL.md 加 Forward 回写步骤。估值数据源统一：估值层读本地 estimates-resolved.json（不再实时拉 analyst-estimates） |
| v8.8.13 | **financial-data FMP 集成 + 日报自动化**：fmp_provider（stable API 行情/三表/estimates/segments/历史价/涨跌/财报日/news + ticker 词典自修正）；mode 收敛 scan/lite/full + scan 批量；FMP 路由探路 + closeout FMP 优先；日报 5 区块（Review Queue/估值表/Movers/Core Watch/Data Health）+ 估值表 4 列（PE_TTM/NTM/EV-EBITDA_TTM/NTM vs 5y 中位）+ COVERAGE v3 Status 列（Screened/Quickread/Modeled/Thesis/Terminated）；launchd 三时点调度 |
| v8.8.11 | plugin.json (claude/codex) version synced to release tag: 8.8.9 → 8.8.11 — internal version always matches the release number (v8.8.10 shipped with stale 8.8.9 declaration) |
| v8.8.10 | version bump: plugin.json (claude/codex) → 8.8.9; workspace_guard ALLOWED_EXTERNAL_ROOTS (plugin dev repo) added to workspace + init-workspace assets |
| v8.8.9 | evidence_ledger_floor Rule 5 rewritten: coverage-quota (≥80%) replaced by disposition gate — every artifact-anchored claim must leave unverified AND carry an attempt record ([S#]: one WebFetch/actuals cross-check; [I#]: tier 1-2 via Rule 4); scoped to artifact codes (stale claims don't gate sibling writes); dead sources must be corroborated or removed, never faked plausible; fixed latent Rule 2 NameError (len(anchors) → anchor_map); hook tests rewritten as real check() invocations (7 cases) |
| v8.8.8 | evidence_ledger fixes + claim-quote verification: auto max-ID+1 (no collisions), full-content anchor scan via shared extract_anchors (code-block/Resources anchors no longer missed — S12 class; hook Rule 0 aligned), verify writes attempts (hook Rule 4 gate), add/batch merge preserve attempts + provenances union, new delete subcommand, tier validation; verify-claim --claim-text matched/reachable semantics + staging schema 2 (int tier) + --apply, schema 1 compat |
| v8.8.7 | image-path integrity: single root image pool (workspace .cache/images) — new image-path-check.py (scan + --fix migrate/rewrite refs, 122 refs fixed on real workspace), image_path_integrity hook (PostToolUse warn-only), download-image.py --artifact prints artifact-relative ref; skills aligned (quickread / mechanism-insight / teach-in), research-runtime §2.5 |
| v8.8.6 | disclosure_fact_source_boundary rewrite: 3-track logic (strict / information-impact / unregistered-token backstop), URL-stripped paragraph windows, per-row table split, line-numbered block messages, format warns (false-positive class fixed, rename dodge closed) |
| v8.8.5 | workspace-validate-names: TICKERS_WITHOUT_CN_NAME exemption (0522.HK ASMPT - English-only brand, no registered Chinese name); TW company dirs renamed to Chinese (1590.TW-亞德客, 2327.TW-國巨) |
| v8.8.4 | verify-claim --ledger staging + evidence_ledger apply-staging (two-layer fix, batch backfill gone); workspace-validate-names company dir check (CN/HK/TW must be Chinese); quickread SKILL Step 4/7 updated |

| v8.8.3 | market_snapshot_source_boundary rewrite: paragraph-window scan, URL-stripped keyword match, line-numbered block messages, PE/20x/市值 allowed terms, format checks demoted to warn (484->49 blocks on real artifacts) |


| v8.2.1 | Tool alias table, CLAUDE.md section 11 agent behavior rules |
| v8.2.0 | workspace-summary + workspace-validate-names scripts, remove dcf-model/comps-analysis/3-statement-model |
| v8.1.0 | workspace-locate.py, transcribe encoding fix, meeting-minutes workspace awareness + naming enforcement |
| v8.0.0 | Colleague-ready: Python auto-install, PreToolUse hooks, VS Code extension support, all hardcoded paths removed |

## v7.x (2026-07)

| Version | Changes |
| v8.8.8 | evidence_ledger fixes + claim-quote verification: auto max-ID+1 (no collisions), full-content anchor scan via shared extract_anchors (code-block/Resources anchors no longer missed — S12 class; hook Rule 0 aligned), verify writes attempts (hook Rule 4 gate), add/batch merge preserve attempts + provenances union, new delete subcommand, tier validation; verify-claim --claim-text matched/reachable semantics + staging schema 2 (int tier) + --apply, schema 1 compat |
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
| v8.8.8 | evidence_ledger fixes + claim-quote verification: auto max-ID+1 (no collisions), full-content anchor scan via shared extract_anchors (code-block/Resources anchors no longer missed — S12 class; hook Rule 0 aligned), verify writes attempts (hook Rule 4 gate), add/batch merge preserve attempts + provenances union, new delete subcommand, tier validation; verify-claim --claim-text matched/reachable semantics + staging schema 2 (int tier) + --apply, schema 1 compat |
|---|---|
| v6.7.0 | driver-map v1.4.0: CF/HL/BOLD helpers, yoy module |
| v6.5.14 | RAG 4-tier fallback, Evidence Ledger, sentence-end anchors |
| v6.5.9 | Removed verification badges from source anchors |

## v5.x (2026-05—06)

| Version | Changes |
| v8.8.8 | evidence_ledger fixes + claim-quote verification: auto max-ID+1 (no collisions), full-content anchor scan via shared extract_anchors (code-block/Resources anchors no longer missed — S12 class; hook Rule 0 aligned), verify writes attempts (hook Rule 4 gate), add/batch merge preserve attempts + provenances union, new delete subcommand, tier validation; verify-claim --claim-text matched/reachable semantics + staging schema 2 (int tier) + --apply, schema 1 compat |
|---|---|
| v5.4.0 | Source contract injection (27 skill output tables + Ev column) |
| v5.3.0 | Actuals-only ratio constraint |
| v5.2.1 | Directory auto-discovery |
| v5.1.0 | Python unified bootstrap, init-workspace rewrite |
| v5.0.0 | 7 new skills, regime-based candidate screener, full-chain hook governance |
