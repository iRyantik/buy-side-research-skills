# Research Runtime

所有研究 skill 的共享运行时基线。每个 research skill 的 `## Research Runtime Capsule` 引用本文件，不再各自重复声明。

Hook-enforced 规则（source boundary、structure floor、table render、mermaid syntax）由 workspace hooks 强制执行，不在本文重复。

---

## 1. 数据获取链

```
/financial-data <TICKER>
  → .cache/financial-data/internal/actuals-resolved.json
```

- 默认 Lite：`/financial-data <ticker>` → latest FY + latest Q/H（~46 字段）
- Full 模式：`/financial-data <ticker> --mode full` → 5 FY + 4 Q/H（~72 字段）
- 灵活期间：`/financial-data <ticker> --periods FY2020-FY2025`
- 期间 key 从 provider values dict 动态读取（如 `"FY 2025"`），不硬编码 `fy_y2/y1/y0`
- 所有 provider 路由、trust 排序、市场数据降级链均在 financial-data 内部执行
- 消费 skill 直接从 `actuals-resolved.json` 取数，不重复声明 provider/tier
- **actuals 更新后必须同步 artifact**：任何字段被修改 → 找到所有引用该 ticker 的 artifact → 同步数字、结论、估值（详见 `CLAUDE.md` §3.5 做完就记）

---

## 2. 来源验证链

```
python .scripts/shared/verify-claim.py <url>
```

自动化 Tier 1→2→3 回退：

| Tier | 方法 | 说明 |
|---|---|---|
| 1 | HTTP GET | `urllib.request`，30s 超时，提取可见文本 |
| 2 | Playwright MCP | 脚本输出指令，agent 执行 `browser_navigate` + `browser_snapshot` |
| 3 | curl | 子进程 `curl -sL`，last resort |
| 4 | [UNVERIFIED] | 全部失败，标记 `[UNVERIFIED]` |

消费方式：
```
# 首次尝试
python .scripts/shared/verify-claim.py <url> --json

# 如果 Tier 1 失败 → 脚本输出 Playwright 指令 → agent 执行 → 回传
python .scripts/shared/verify-claim.py <url> --playwright-text "<snapshot>"
```

skill 的 artifact 中，每个 [I#] source 必须至少经过 Tier 1-2 验证（hook: `evidence_ledger_floor`）。

### 2.2 Source 纪律

**核心规则：WebSearch 摘要里的任何数字（市占率、增速、订单金额、客户数、精度）禁止直接写入 artifact。**

每个数字必须从原文页面亲眼验证——打开 URL 确认数字在原文中存在。摘要可能对、可能错。

**验证链路（强制）**：
```
1. WebSearch 返回摘要 → 找到候选 URL
2. WebFetch / Playwright browser_navigate 打开该 URL
3. 在原文中找到该数字 → 确认 URL 和数字匹配 ✅ → 写入 artifact
4. 原文中找不到 → 标 [需查证] 或找新 source
```

**Source 优先级（强制）**：

```
1. actuals-resolved.json    本地缓存，机器采集，零延迟，最高置信
   → 从 source_map 字段读取对应的 [S#](url) 标签。不在 artifact 中写裸 [actuals]。

2. [S#] 公司披露            IR PDF、年报、AGM presentation、earnings transcript
   → actuals 没有的字段：订单细节、管理层原话、产品路线图、产能计划
   → verify-claim.py 验证原文 → 标 [S1-S9]

3. [I#] 第三方              行业报告、新闻媒体、Yahoo Finance、卖方报告
   → actuals 和公司披露都覆盖不到：市占率、TAM、竞争格局、卖方 target、consensus
   → verify-claim.py 验证原文 → 标 [I1-I20]

同一 claim 只引用最高优先级的一个 source。
例：Revenue → actuals 已有 → 不标 [S1]。Q1 订单 → actuals 没 → [S1]。TSMC占60%+ → 公司不披露 → [I1]。
```

**禁止**：
- ❌ 摘要说「市占率超 50%」→ 挂一个"看起来相关"的 URL 就写进 artifact
- ❌ 同一 URL 下挂多个未经验证的 claim
- ❌ 个人博客当行业数据 source
- ❌ Source 标注与实际内容不符（张冠李戴——标称"产品页"但页面讲的是别的东西）

**自检——读完本节后确认**：
- [S#] 和 [I#] 的区别是什么？Revenue 数据从哪拿，标 [S1] 还是 [I1]？
- WebSearch 摘要说 TSMC 市占 60%，你能直接用吗？下一步应该做什么？

### 2.1 资料收集

**任何文件 → markdown 的统一入口：**

```
python .scripts/shared/to-markdown.py <file_or_url>                    # stdout markdown
python .scripts/shared/to-markdown.py <file> --cache <TICKER> <desc>   # stdout + .cache/ 归档
```

| 工具 | 用途 | 内部引擎 |
|---|---|---|
| `to-markdown.py` | **万能路由器**——检测格式→调提取器→输出 markdown | pdf-extract / extract-docx / extract-pptx / extract-xlsx / web-extract |
| `web-extract.py` | 网页正文提取（to-markdown 内部用，也可直接调） | `urllib` HTTP GET → HTML parser |
| `pdf-extract.py` | PDF 文本+表格（to-markdown 内部用） | pymupdf → pdfplumber → pypdf |

**智能路由**：
```
本地文件 → to-markdown.py（自动检测格式）
网页 URL → web-extract.py 或 to-markdown.py（效果相同）
PDF → to-markdown.py 调 pdf-extract --smart:
  ├─ 简单 PDF → fast 路径，直接返回 markdown ✅
  └─ 复杂 PDF（扫描件/tables-heavy）→ 输出 probe + 建议调 /ingest
```

#### 2.1.1 PDF 自动缓存（Hook 强制）

**规则**：任何 Bash / browser 下载的 PDF，满足以下任一条件自动触发缓存：

- **A 轨**：来源 URL 匹配官方 IR / 监管 filing 渠道（SEC/HKEX/TDNET/DART/巨潮/MOPS 等多市场）
- **B 轨**：文件名含一手资料关键词（annual/quarterly/earnings/transcript/prospectus/10-K/20-F/招股/年报/季报/決算 等）

**动作**：Hook 自动推断 source type → 推导缓存路径 → `to-markdown.py --output <path> --rm`：
1. 从 URL + 文件名推断 source type（disclosure/annual、disclosure/quarterly 等）
2. 计算缓存路径（按来源类型分层），见下方文件树
3. 转换为 markdown 并写入自描述元数据头部（`source_url / source_type / ticker / pages`）
4. 删除原始 PDF
5. 转换失败（扫描件 text < 200 chars / 超时 120s）→ 保留 PDF + warn

**缓存路径**（按来源类型分层）：

| 类型 | 路径 | 命名 |
|---|---|---|
| 年报/10-K/20-F | `.cache/disclosure/annual/` | `FY<year>-<desc>.md` |
| 季报/10-Q | `.cache/disclosure/quarterly/` | `<year>-Q<n>-<desc>.md` |
| Transcript | `.cache/disclosure/transcript/` | `<year>-Q<n>-earnings-call.md` |
| 招股书/S-1 | `.cache/disclosure/prospectus/` | `<year>-IPO-<desc>.md` |
| 其他 filing | `.cache/disclosure/filing/` | `<date>-<form-type>.md` |
| 卖方报告 | `.cache/sell-side/<house>/` | `<house>-<date>-<ticker>-<note>.md` |
| 行业机构 | `.cache/institution/<source>/` | `<source>-<date>-<topic>.md` |
| 一手调研 | `.cache/primary/<type>/` | `<date>-<company>-<type>.md` |
| 网页快照 | `.cache/web/` | `<date>-<slug>.md` |
| 未分类 | `.cache/inbox/` | 兜底 |

**不需满足** artifact 引用条件——一手资料本身就是缓存理由。

#### 2.1.2 缓存优先

**规则**：下载任何外部文件前，必须先检查本地缓存。

| 文件类型 | 缓存位置 | 检查方式 |
|---|---|---|
| 公司披露 | `industry/<slug>/companies/<ticker>/.cache/` | `ls` / `grep` 文件名关键词 |
| 行业报告 | `industry/<slug>/.cache/` | `ls` / `grep` |
| 跨行业通用 | `.cache/` | `ls` / `grep` |

- ✅ 命中 → 直接 Read 本地缓存，source 写 `[S#](./.cache/<path>)`
- ❌ 未命中 → 上网下载。下载后 §2.1.1 hook 自动缓存一手资料

---

## 3. 证据协议

Subagent 产出的 evidence card 格式见 `.references/policy/evidence-card-schema.json`。

主 agent 从每张 evidence card 取 1-3 个 evidence triplet，以三行格式嵌入 artifact：

```
claim: <key factual claim>
evidence: <supporting data>
source: [S#](url) or [I#](url)
```

至少 1 个 triplet（3 行）以满足 `subagent_protocol` hook。

---

## 2.5 图片获取链

```
python .scripts/shared/download-image.py <url> --output <slug>   # 产品/设备图
```

自动化 Tier 1→2 回退：

| Tier | 方法 | 说明 |
|---|---|---|
| 1 | HTTP | `urllib` 直接下载 |
| 2 | Playwright MCP | 脚本输出指令，agent 执行 `browser_navigate` + `browser_evaluate` 提取 base64 |
| 3 | `[缺图]` | 全部失败，标记 `[缺图]` |

缓存：`.cache/images/` + `.cache.json` 索引，workspace 级跨 skill 共享。

产品图命名：`<slug>.{ext}`（手动 `--output` 指定）。

**禁止** `browser_take_screenshot` 代替下载——hook `pre_write_gate` CHECK 6a 直接 block。

---

## 4. 产出合约

### 4.1 结构底限

- §0 任务定义 → §1 结论先行 → §2-§N 主体 → `## Resources` → `## Appendix`
- 表格必须有 separator row，header/separator/data 列数一致
- Mermaid 图必须用合法类型（`quadrantChart` 不是 `scatterchart`，`flowchart` 不是 `waterfall`）

### 4.2 Hook 防御

| Hook | 检查什么 |
|---|---|
| `pre_write_gate` | source anchor、paragraph density、image existence、mermaid type、table structure |
| `source_contract` | bare anchor、invalid source label、Resources section format |
| `table_render_integrity` | 列数一致性、separator row 存在 |
| `mermaid_syntax` | diagram type 合法性 |
| `skill_structure_contract` | 必填 section 存在 |
| `evidence_ledger_floor` | Tier 2 验证覆盖 ≥80% |

### 4.3 Appendix

```
python .scripts/financial-data/actuals-to-appendix.py --tickers <T1>,<T2>,...
```

**必须在写 artifact 正文之前执行**，输出嵌入 `## Appendix` 节。禁止留占位符。

---

## 5. 保存合约

### 5.1 路径

```
industry/<industry>/companies/<ticker>/YYYY-MM-DD-<artifact>.md     # 公司级
industry/<industry>/YYYY-MM-DD-<artifact>.md                        # 行业级
```

### 5.2 自动脚手架

Agent 保存 artifact 前完成：
1. `mkdir -p` 缺失目录
2. `RESEARCH.md` 注册公司/行业引用
3. `COVERAGE.md` 更新覆盖状态（如有）

详见 `.references/policy/research-policy-baseline.md` §9-11。

---

## 6. 写 Artifact 前逐条确认

**写完 artifact 正文后、保存前，逐条自检——任一条不通过 → 不要保存，先修复。**

```
□ 1. 每个数字来自 actuals（Tier 0）或 WebFetch/Playwright 打开的原文页面（Tier 1-2），不是 WebSearch 摘要
□ 2. 每个 [S#]/[I#] 在 evidence ledger 中有对应 entry（hook: evidence_ledger_floor Rule 0）
□ 3. 每个 [I#] 有 ≥1 条 Tier 1-2 验证记录（hook: evidence_ledger_floor Rule 4）
□ 4. 没有裸 [actuals]（§2.2：从 source_map 取 [S#] 标签）
□ 5. 没有 browser_take_screenshot（用 download-image.py）
□ 6. 图片已下载到 .cache/images/，缓存索引已更新
□ 7. [缺图] 仅在全部 tier 失败后使用，ledger 有 attempt 记录
□ 8. [需查证] 不超过 8 个（hook: pre_write_gate CHECK 8）
□ 9. 表格 header/separator/data 列数一致，≤12 列（hook: pre_write_gate CHECK 13）
□ 10. Mermaid 图用了合法类型（quadrantChart 不是 scatterchart）（hook: mermaid_syntax）
□ 11. `## Resources` 节格式正确，每个 label 是 [S#] 或 [I#]
□ 12. `## Appendix: Financial Data` 已嵌入（actuals-to-appendix.py 先跑，不留占位符）

---

## Standard Research Capsule

新 skill 的 `## Research Runtime Capsule` 统一写：

```markdown
## Research Runtime Capsule

**执行本 skill 前必须先读取以下文件：**
- workspace `CLAUDE.md` §3（Agent Rules）§4（Source Stance）§5（Output Style）§6（Pipeline Contract）
- `.references/runtime/research-runtime.md` §1（数据获取链）§2（来源验证链）§4（产出合约）§5（保存合约）
- `.references/style/language-guide.md`（语言规则）
- `.references/routing/data-routing.md`（数据路由，需要外部数据时）

**自动 Hook 防御：** `pre_write_gate` `source_contract` `table_render_integrity` `mermaid_syntax` `skill_structure_contract` `evidence_ledger_floor`

**GATE**: Read all referenced files BEFORE any action. Capsule only states what is unique to this skill.
```
```
