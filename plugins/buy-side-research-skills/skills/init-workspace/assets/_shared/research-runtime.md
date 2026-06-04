# Research Runtime

所有研究 skill 的共享运行时基线。每个 research skill 的 `## Research Runtime Capsule` 引用本文件，不再各自重复声明。

Hook-enforced 规则（source boundary、structure floor、table render、mermaid syntax）由 workspace hooks 强制执行，不在本文重复。

---

## 1. 数据获取链

```
/financial-data --lite <TICKER>
  → _cache/financial-data/internal/actuals-resolved.json
```

- 默认 `--lite`：返回 `latest_fy` + `latest_quarter`
- 多期附录：`--lite --periods 3Y`（写入 `fy_y2/y1/y0` + `sub_0/1/2/3`）
- 所有 provider 路由、trust 排序、市场数据降级链均在 financial-data 内部执行
- 消费 skill 直接从 `actuals-resolved.json` 取数，不重复声明 provider/tier

---

## 2. 来源验证链

```
python _scripts/shared/verify-claim.py <url>
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
python _scripts/shared/verify-claim.py <url> --json

# 如果 Tier 1 失败 → 脚本输出 Playwright 指令 → agent 执行 → 回传
python _scripts/shared/verify-claim.py <url> --playwright-text "<snapshot>"
```

skill 的 artifact 中，每个 [I#] source 必须至少经过 Tier 1-2 验证（hook: `evidence_ledger_floor`）。

---

## 3. 证据协议

Subagent 产出的 evidence card 格式见 `references/policy/evidence-card-schema.json`。

主 agent 从每张 evidence card 取 1-3 个 evidence triplet，以三行格式嵌入 artifact：

```
claim: <key factual claim>
evidence: <supporting data>
source: [S#](url) or [I#](url)
```

至少 1 个 triplet（3 行）以满足 `subagent_protocol` hook。

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
python _scripts/financial-data/actuals-to-appendix.py --tickers <T1>,<T2>,...
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
2. `index.md` 注册公司/行业引用
3. `COVERAGE.md` 更新覆盖状态（如有）

详见 `references/policy/research-policy-baseline.md` §9-11。
