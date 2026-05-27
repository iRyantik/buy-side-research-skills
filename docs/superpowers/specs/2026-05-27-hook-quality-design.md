# Hook 体系重构：提升实现质量，消除误报

## 问题

用户在 Codex 聊天时 30+ hook 在每次 PostToolUse/Stop 全跑，其中写作质量类 hook 用纯正则做语义判断（"有没有分析力"、"有没有陈述市场预期"），频繁误报阻断，严重影响正常使用。

## 设计原则

**Hook 只做机械检查，不做语义判断。** 正则擅长的（格式、关键词组合、是否存在）留在 hook；语义判断（写得好不好、有没有分析力）交给 SKILL.md + Claude 自己。

## 改动概要

- 删 10 个语义判断/太僵/重复 hook
- 留 7 个写作质量 hook（纯机械检查）
- 优化 6 个 hook 的实现质量（降低误报）
- 16 个 hook 不变（全局安全 + 建模层）
- 共 ~22 个 hook，PostToolUse ~20 个进程

---

## Section 1: 删除的 Hook（10 个）

| Hook | 文件路径 | 删除原因 |
|---|---|---|
| `no_filing_summary` | `narrative/no_filing_summary.ps1` | 正则判断"有没有分析力" — 语义，正则做不了 |
| `must_state_market_expectation` | `narrative/must_state_market_expectation.ps1` | 搜 `expectation` 匹配"高期望"但没提市场定价 — 语义 |
| `consensus_floor` | `narrative/consensus_floor.ps1` | 搜英文标题 `## Market Expectation` — 写成中文就拦 |
| `earnings_decision_contract` | `narrative/earnings_decision_contract.ps1` | 搜 `decision tree` — 中文输出永远不匹配 |
| `pair_structure_floor` | `narrative/pair_structure_floor.ps1` | 5 组关键词永远补不全同义词 |
| `thesis_catalyst_floor` | `narrative/thesis_catalyst_floor.ps1` | `catalyst` 匹配酶催化剂 — 正则无法消歧 |
| `peer_matrix_floor` | `narrative/peer_matrix_floor.ps1` | 只检查 2 个 section 名 — 每个 skill 都要一个 hook？ |
| `next_step_anchored_facts_only` | `narrative/next_step_anchored_facts_only.ps1` | source_contract 已覆盖 — 功能重复 |
| `earned_insight_only` | `journal/earned_insight_only.ps1` | "沉淀见解 vs 过程记录" — 语义 |
| `topic_index_map_only` | `journal/topic_index_map_only.ps1` | "研究地图 vs tracker" — 语义 |

还需同步删除 `hooks.registry.yaml` 和 `settings.json` 中对应条目。

---

## Section 2: 保留的写作质量 Hook（7 个，纯机械）

| Hook | 机械检查内容 | Severity |
|---|---|---|
| `claim_qualification` | 同一行：强声明词 + 弱证据词 + 无安全词 | block |
| `social_clue_only` | 同一行：社交来源词 + 强声明词 + 无安全词 | block |
| `disclosure_fact_source_boundary` | I/LBG 锚点 + 披露事实禁词 | block |
| `market_snapshot_source_boundary` | I/LBG 锚点 → 必须有 fallback 声明 + provider/as-of/原因 | block |
| `primary_research_compliance` | "专家说"无 "planned/假设" 标记；要 MNPI 无 "red-line" 标记 | block |
| `cross_market_parity` | 比较场景 → 必须有上市身份 + 货币 + 时间戳 | warning |
| `viz_delivery_contract` | HTML 自包含 + 日期命名 + 标题 + 来源行 | block |

---

## Section 3: 不需改实现的 Hook（17 个）

这些 hook 已足够机械、低误报，只改 _hook_common.ps1 基础和 registry 注册即可，不碰 .ps1 本体。

### 全局层（2 个）
`workspace_guard`、`subagent_protocol`

### 写作质量层（4 个）
`social_clue_only`、`disclosure_fact_source_boundary`、`market_snapshot_source_boundary`、`viz_delivery_contract`

### 建模层（11 个）
`model_statement_presence`、`model_balance_integrity`、`no_hardcoded_formula_assumption`、`missing_actuals_not_zero`、`historical_actuals_fill_floor`、`driver_breakdown_coverage_floor`、`valuation_basis_required`、`three_statement_structure_floor`、`three_statement_audit_floor`、`three_statement_driver_floor`、`three_statement_checks_result_floor`

---

## 最终统计

| 类别 | 数量 |
|---|---|
| 删除 | 10 |
| 保留且改实现 | 6（source_contract, table_render_integrity, claim_qualification, primary_research_compliance, cross_market_parity + _hook_common.ps1） |
| 保留不改本体 | 17（2 全局 + 4 写作质量 + 11 建模） |
| **总计保留** | **22** |

---

## Section 4: 需优化的 Hook 实现（6 个文件）

### 4.1 `_hook_common.ps1`（基础库）

- **Test-FactualLine**：排除年份、日期、版本号、页码、步骤编号、章节编号、序号开头
- **Test-IsArtifactLikeText**：不再 600 字符就判定为 artifact；必须同时有 `##` 标题 + 长度 > 1000 字符。管道符只在匹配 `^\|.+\|$` 时视为表格信号
- **新增 Test-HasCodeFence**：检测文本是否在三重反引号代码块内，跳过代码块内容
- **新增 Write-Warn**：打印到 stderr 后 `exit 0`，不阻断
- **新增 Test-IsCasualChat**：无 Write/Edit 到 `topics/` 路径 → 判定为聊天场景
- **Test-IsValidSourceTarget**：允许 `#` 片段锚点；接受无扩展名裸标签
- **Get-ResourcesEntries**：接受无 `= metadata` 后缀的条目
- **Get-MarkdownPipeTables**：跳过代码围栏内的管道符行

### 4.2 `source_contract.ps1`

- 入口调用 Test-IsCasualChat → 纯聊天 `exit 0`
- 重复资源条目同一目标 → 允许（不再 `Write-Block`）
- 表格行证据锚点格式扩展为 `[S|P|I|LBG|R|SRC]\d+`
- `## Resources` 计数 >1 → 遍历所有块，改为 `Write-Warn`

### 4.3 `table_render_integrity.ps1`

- 入口跳过代码围栏内的内容
- 分隔符破折号阈值从 3 降到 2（接受 `|--|`）

### 4.4 `claim_qualification.ps1`

- 强声明 + 弱证据匹配从同一行扩展到邻行（前后 2 行内）

### 4.5 `primary_research_compliance.ps1`

- `pricing` 从 MNPI 禁止词移除（太宽，正常定价讨论不涉 MNPI）

### 4.6 `cross_market_parity.ps1`

- `Write-Block` 改为 `Write-Warn`（不阻断，仅提示）

---

## Section 5: 注册表同步

**`hooks.registry.yaml`**：删 10 个 hook 条目，severity 栏更新

**`settings.json`**：
- PreToolUse、PostToolUse、Stop、SubagentStop 四个事件数组中删除对应 hook 命令
- `cross_market_parity` 的 timeout 保持 20s

---

## 涉及文件清单

| 文件 | 操作 |
|---|---|
| `hooks.registry.yaml` | 编辑（删 10 条目） |
| `settings.json` | 编辑（删 10 注册） |
| `_hook_common.ps1` | 编辑（新增函数 + 修复） |
| `source_contract.ps1` | 编辑（优化） |
| `table_render_integrity.ps1` | 编辑（优化） |
| `claim_qualification.ps1` | 编辑（邻行匹配） |
| `primary_research_compliance.ps1` | 编辑（移除 pricing） |
| `cross_market_parity.ps1` | 编辑（warning） |
| `no_filing_summary.ps1` | 删除 |
| `must_state_market_expectation.ps1` | 删除 |
| `consensus_floor.ps1` | 删除 |
| `earnings_decision_contract.ps1` | 删除 |
| `pair_structure_floor.ps1` | 删除 |
| `thesis_catalyst_floor.ps1` | 删除 |
| `peer_matrix_floor.ps1` | 删除 |
| `next_step_anchored_facts_only.ps1` | 删除 |
| `earned_insight_only.ps1` | 删除 |
| `topic_index_map_only.ps1` | 删除 |

---

## 验证

1. 纯聊天场景（无 Write/Edit 文件）→ 所有写作质量 hook 静默 `exit 0`
2. 数字行含年份/日期/版本号 → 不触发 source_contract
3. 代码块中的管道符 → 不触发 table_render_integrity
4. `## Resources` 无 `= metadata` → source_contract 仍正确解析
5. `pricing` 出现在调研计划中 → 不触发 primary_research_compliance
6. warning 级别 hook 阻断时 → 只打印提示，`exit 0`
7. `init-research-workspace.ps1` 部署后 hook 数量从 32 → 22
8. `settings.json` 解析无误（JSON valid, no BOM）
