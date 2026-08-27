# Changelog

## v8.x (2026-07)

| Version | Changes |
|---|---|
| v8.9.12 | **financial-data market_data 重跑补填 + FMP stable 客户端 + 写前纪律**：_route_api 早退曾跳过市场数据 closeout（actuals 已有三表时重跑 market_data 留空）→ 新增 _fill_market_data_fmp() 从 FMP /stable/ 自动回补且不覆盖已填；依赖缺失给可操作提示（pip install akshare）；新增 fmp.py（base 锁 /stable/，legacy /api/v3/ 2025-08-31 起 403）；research-runtime §4.4 写前纪律 |

| v8.9.9 | **email-intelligence 定时 3 次/天**：默认排程 09:30 → `05:00 / 13:00 / 21:00`（周一~六，Asia/Hong_Kong）；`install_windows.ps1` 单任务三触发器，SKILL.md / SKILL.en.md 调度说明同步；进程增量（每次只 review `state.seen` 未处理的新邮件），每天 3 封 brief（标题带 `覆盖窗口 上次→本次`） |

| v8.9.8 | **email-intelligence 生产级闭环**：identity 归一化（FMP 后缀别名 `.CH→.SZ/.SS` 等、`Semiconductor Equipment`/`Semiconductor-Equipment` 合并为一张卡）；state 原子写入+损坏备份+unstable 邮件扫描（body 缺失/太新不 review 不标 seen）；评审改本机 Codex/Claude agent（读图片/PDF 附件、正文超长截断保留尾部报名链接、outbox 重试未送达、dry-run 不写 state）；canonical report + 6-section 契约（Worth Your Time / Industry / Core Watch / Other Coverage / New Ideas / Meetings）+ 配色语义重构（各栏一色、公司状态独立、会议推荐绿/琥珀/灰、去棕色）；Industry 只收 Coverage 行业或可映射 read-through（## Focus 非覆盖不降级塞进 Industry）；公司卡事实 read-through 确定性 prun（韩华海洋卡不再带纽威下游 clause，只留主标的）；deep 抽取新增主标 scope（每条只写主标的，read-through 只留方向）；meeting 标题承载真实报名链接、所有外部链接开新标签(`target=_blank`)；Windows 计划任务 `install_windows.ps1`（ASCII-safe）+ Codex 应用定时自动化；48 项单元测试全绿 |

| v8.9.5 | **市场国家化 + 日报两级筛选 + 邮件两时点**：COVERAGE Market 列 → 国家/地区码（US/CA/GB/FR/DE/SE/NO/FI/IT/ES/NL/JP/KR/CN/HK/TW/MY，洲由码派生，§3.3/Contract 同步）；日报网页前端洲（美洲/亚洲/欧洲/全部）+ 国家芯片两级筛选（universe/mover/core/review 联动 + 清空国家）；邮件两封——`[欧美盘后]`（us=美+欧，07:45）/ `[亚盘盘后]`（asia，16:15），邮件 HTML 的 Universe/Review Queue 保持全市场、其余区块按报告口径，正文模板不动；邮件 HTML 补数据来源行（viz_delivery_contract）；`.US` 尾缀 → 裸码（COVERAGE + 目录 16 家 + estimates-resolved keys 迁移，estimates_store 归一化——DPC/KEYS/ESLT 等 PE_NTM 恢复）；`render_coverage_markdown` 修复（Status/Coverage 双列重复、Val Anchor 列丢失、Market 列渲染 country 优先防 normalize 回写降级）；workspace-validate-names 改 FMP 直通后缀白名单（弃 Bloomberg 旧后缀）；coverage 契约测试钉住（5/5）；Mac 定时三时点 → 两时点（install_launchd/install_cron：`am 07:45`→`us 07:45`、eu 23:45 废弃并入次早 us） |

| v8.9.4 | **日报作用域 + Market 上市地列 + 目录匹配**：日报前端（Candidates/Movers/Core Watch）只显刚收盘市场（us/asia/eu 各盘后），Universe / Review Queue 全量，顶部加可见作用域说明（不含技术词）；CoverageEntry 加 `market`（us/eu/asia 上市主要市场），COVERAGE 表加 Market 列（154 行回填）+ 注册时记录（§3.3）+ entry_market 显式优先否则 ticker 推断；大金重工多 ticker legacy（002487 CH / 1081 HK）市场误判修复——_market_of 先规范化（多 ticker 按首上市地）+ COVERAGE 改 canonical `002487.SZ / 1081.HK`；公司目录↔COVERAGE 匹配修复（_dir_links_row：中文名目录 + 缩写名 + é NFC/NFD 归一，unregistered gap 12→8）；CLAUDE.md §3.2 补 `.DE`(德国/XETRA) + 措辞校准"FMP 直通后缀" |
| v8.9.3 | **email 跨天事件追踪 + 增量标注**：merge_key 跨天稳定（不含日期），事件库记录 first/last_seen + brokers + 最新 what_changed；跟进事件（昨日 broker 提过）AI 判断 delta_vs_last（相对上次基线的实质新增），brief 标「此前已有 broker 提及」+「新增」 |
| v8.9.2 | **mover 归因 DeepSeek 化**：mover_review 从 claude CLI session 改为 DeepSeek 批量（无痕、Windows/Mac 通用，DeepSeek → claude fallback → 规则）；DeepSeek 关 reasoning（reasoning_effort:none——8 家 chunk 66s→11s 且 content 不空，translation/review 更快更稳） |
| v8.9.1 | **coverage-monitor 补齐**：手机 Universe 重构（7 列 / 估值两行 / th-td 列对齐 / 括号染色）；新闻 4 源 publish 日期（yfinance unix→ISO / DDG snippet 提取）；intraday 当天新闻触发（published_at==today，排除旧新闻误报）；email 模式 section→div + 注释小字；产物目录迁移 daily/market/ + daily/logs/ |
| v8.9.0 | **Email Intelligence + Focus 层**：新增 email-intelligence skill（轻量 5-section sell-side 邮件情报——Core Watch / Other Coverage / New Ideas / Industry & Sell-side Signals / Meetings + Worth Your Time，DeepSeek 结构化提取（多公司 items + 多会议 meetings）+ 确定性 routing（New Idea gate 非 initiation）+ 增量 state）；Focus 合并进 COVERAGE.md 顶部 `## Focus` 区（Current Lens / Theme Book / Theme→Industry→Company / Research Feedback / Maintenance Rule），candidate-screener 读作默认 lens、research-journal earned change 反馈；init-workspace / update-agent-runtime 部署（copy-if-missing 不覆盖用户 Focus）；workspace_guard 允许 macOS dev repo |

| v8.8.26 | **intraday 实时异动监控**：`intraday --market-aware` 只扫开市市场（复用日报时段表，全休市跳过）；告警邮件升级 HTML 卡片（涨跌红绿 + Price/Vol + 当天新闻佐证"为什么动"，正文无附件）；配合 Mac launchd 每 5 分钟轮询（com.cc.intraday，StartInterval 300） |
| v8.8.25 | **Research Candidates + 负估值修复**：日报新增"研究推荐"区块（Movers 前）——数据信号打分（重要异动 ±8% +2 / 普通异动 +1 / 深度低估（估值 vs 5y ≤-30%）+2 / 深度贵 +1 / 财报 7 天内 +1 / 重大新闻 +1 / 放量 ≥2x +1），总分 ≥3 入选 Top 5，评分规则注明；信号卡片（分数徽章 + 染色胶囊 + 新闻锚点）；负估值清 NA（亏损公司 PE/EV·EBITDA/PS/PB/PFCF ≤0 → None，vs 5y 不再出假对比）；邮件版红绿内联染色（Universe 涨跌/估值——邮件客户端 class 样式不可靠）；邮件 quote 行改 label/value 小格子（inline-block 3×2 涨跌红绿，不依赖 media query）；页面过滤库扩充 15 条（股价行情/实时行情/个股资料/Stock Quote 等个股页模板）；cli import sys 修复（v8.8.23 潜伏 NameError） |
| v8.8.24 | **手机 Universe 修复**：恢复 PE_NTM / EV·EBITDA_NTM 列（手机 6 列：Company/Today/1m/YTD/PE_NTM/EV·EBITDA_NTM，1y 隐藏，无横向溢出）；表格完整展开（邮件版 email-flat + 手机 media 去容器高度限制，页面滚动——邮件客户端容器滚动不可靠导致手机只能看到表格开头） |
| v8.8.23 | **DeepSeek 翻译 + 日报布局**：翻译链加 DeepSeek（OpenAI 兼容，Windows/Mac 通用——渲染前批量预翻 + 单条兜底，init-workspace 引导配置 DEEPSEEK_API_KEY/DEEPSEEK_API_BASE/DEEPSEEK_MODEL）；gtx 失败不再误缓存原文（清理 7 条污染条目，标题不再被"原文缓存"卡死）；hook：空 last-prompt 元数据行视为子集（副本只多这类行直接删，实测 skip → delete-copy）；HTML 布局：卡片等比缩小 + quote 3×2 + Core Watch 按行业分组（可折叠、公司数降序）+ 内容顺序调整（Movers→Core Watch→Review Queue→Valuation Universe）；邮件正文 = email 模式完整日报（无 hero/tab/Data Health，mover/core 单列卡片内联样式，手机邮件客户端兼容）；手机 Universe 只留 5 核心列（Company/Today/1m/YTD/1y）无横向溢出 |
| v8.8.22 | **session_conflict_clean hook 修复**：8-21 重写的 Syncthing 冲突自动解析版从未进入 release（plugin cache 全为 OneDrive 旧版 → 每次 update-agent-runtime 覆盖回退，Syncthing 冲突弹窗只能人工选）；本次打包进 init-workspace assets；移除 50MB 合并阈值（互有独有超大 transcript 也自动合并，tmp+os.replace 原子写，hook 超时不会损坏 base）；活跃会话：子集副本直接删除（不碰正在写的 base）、非子集留到会话结束；合并改 tuple 存储降内存；测试 25 项 |
| v8.8.21 | **调度调整（收盘逻辑）**：us（美股盘后）扩展周一~周六——周六早上发周五美股盘后（一周收官，最后一封），周一早上发周末后开盘前瞻；asia/eu 保持周一~周五；脚本层周末跳过只跳周日（launchd Weekday 参数化） |
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
