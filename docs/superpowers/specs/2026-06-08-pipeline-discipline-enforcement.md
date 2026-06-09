# Pipeline Discipline Enforcement

> 状态: spec
> 日期: 2026-06-08
> 目标版本: v5.14.2

---

## 背景

Agent 有 15 种绕开 pipeline 的行为模式——主动偏离（失败记忆、假装已完成、提前产出、工具替换、选择性执行、顺序颠倒、降级当默认、提前路由）、被动偏离（上下文压缩丢失、子 Agent 不继承约束、大文件跳过、错误恢复过界、静默降级）、跨 Skill（规则混用、Capsule 不读）。

分四层防线加固。

---

## Layer 1: CLAUDE.md 全局宪法

### 插入位置：§6 Routing Stance 末尾，`## 7. UTF-8 文本纪律` 之前

```markdown
## 6. Routing Stance（续）

### Workflow 执行纪律

以下规则适用于所有 skill 的所有 pipeline 步骤。不可绕过，不可协商。

1. **Pipeline 步骤不可裁减**：Skill 定义的每一步都是强制步骤。Agent 没有权限判断某步骤"不需要"或"可以跳过"。全部执行，无一例外。

2. **步骤失败 → 报告 + STOP**：任何步骤报错，Agent 必须报告具体错误信息并停止流程。不得发明替代方案，不得静默降级，不得用"看起来类似"的工具替换。如果需要替代，必须显式向用户报告并等待批准。

3. **前置条件必须验证**：下一步开始前，必须确认上一步的产出物真实存在。不得假设"应该已经好了"。如 Step 2 需要 actuals-resolved.json，必须在 Step 1 完成后用 Read 确认文件存在且非空。

4. **工具不可替换**：Skill 明确指定的脚本/命令就是唯一执行路径。不得用 browser_take_screenshot 代替 download-image.py，不得用 WebSearch 代替 verify-claim.py，不得手写 markdown 代替 evidence_ledger.py。

5. **不得提前判断"不值得"**：正在执行的 skill 必须跑完。不得在中途判断"这个公司没意思"或"这个行业太小"而提前终止。完成后可以在结论里说不值得，但不能在执行中判断。

6. **子 Agent 继承父级约束**：使用 Agent tool 分派子任务时，prompt 中必须包含 "Follow all pipeline steps defined in the skill. No skipping, no tool substitution. If a step fails, report the error — do not work around it."

7. **Compact/Summary 后重新读 Skill**：对话被压缩后，Agent 不知道哪些步骤已完成。继续工作前必须重新 Read 当前 skill 的 SKILL.md 全文 + Capsule 引用的文件。

8. **Best-effort ≠ Optional**：标记为 best-effort 的步骤仍然必须尝试。只在尝试后确实失败（且已报告用户）时才能跳过。
```

### CLAUDE.en.md.template 同步翻译

---

## Layer 2: Capsule GATE 强化

### 现 GATE
```
**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action.
All pipeline steps below are MANDATORY. If any step fails, STOP and report the error.
Do NOT skip steps — past failures do not justify bypassing the workflow.
```

### 新 GATE
```
**GATE**: Read workspace `.references/runtime/research-runtime.md` BEFORE any action.
All pipeline steps below are MANDATORY. If any step fails, STOP and report the error.
Do NOT skip steps — past failures are not grounds for bypassing the workflow.
After conversation compaction, re-read this SKILL.md + Capsule before continuing.
```

改动：
- "past failures do not justify" → "past failures are not grounds for"
- 加 "After conversation compaction, re-read this SKILL.md + Capsule before continuing."

### 范围
所有 research skill 的 SKILL.md + SKILL.en.md（~25 个），以及 stock-quickread 的 HARD GATE。

---

## Layer 3: Pipeline 步骤硬化为命令

### 原则
每个 pipeline 步骤必须包含：
1. `★` 标记（MANDATORY step）
2. 可执行的命令（不是自然语言描述）
3. 验证条件（产出物必须存在）
4. 失败策略（STOP / ask user / retry）

### 示例：stock-quickread

```
Step 1: /financial-data <ticker>
        ★ Verify: Read actuals-resolved.json — must exist and contain "statements" key
        ★ Fail → STOP. Do not proceed without actuals.

Step 2: python .scripts/evidence_ledger.py init <artifact-path> -t <TICKER>
        ★ Verify: evidence ledger file exists at _cache/evidence/<TICKER>.evidence.json
        ★ Fail → STOP. Do not create ledger manually.

Step 3: Discovery — WebSearch 找候选 URL（至少 8 条）
        ★ Must produce ≥ 8 candidate source URLs before moving to Step 4
        ★ Fail → report how many found, continue with what you have

Step 4: python .scripts/shared/verify-claim.py <url> --json
        ★ Tier 1→2→3 逐条验证。全部 candidate URL 必须至少尝试 Tier 1
        ★ Fail per-URL → mark [UNVERIFIED]. Fail all → STOP and report.

Step 5: python .scripts/shared/download-image.py --logo <TICKER>
        + python .scripts/shared/download-image.py <url> --output <slug>
        ★ Logo MUST exist. Product images best-effort — [缺图] if all tiers fail.
        ★ Fail logo → STOP.

Step 6: Write artifact
        ★ MUST include Pipeline report header
        ★ pre_write_gate auto-validates

Step 7: python .scripts/evidence_ledger.py auto <artifact> -t <TICKER>
        ★ Fail → STOP. Do NOT manually edit the ledger.

Step 8: python .scripts/financial-data/actuals-to-appendix.py <artifact>
        ★ Best-effort. Fail → report and continue without appendix.
```

### 范围
- stock-quickread（最完整，作为模板）
- 其他 research skill 按需调整

---

## Layer 4: Pre-write gate CHECK 15

### 新增 CHECK：pipeline_report_header

```
CHECK 15: pipeline_report_header
  Artifact must contain a Pipeline report header block:
    > Pipeline: actuals ✅ | verify-claim X/N ✅ | images ✅ | ledger ✅
  任一 mandatory step (actuals/ledger/images) 标 ❌ → block
  任一 best-effort step 标 ❌ 且有 [跳过原因] → allow
```

### 实现
在 `pre_write_gate.py` 中加检查函数。

---

## 执行顺序

```
1. CLAUDE.md.template + CLAUDE.en.md.template — 加 §6 执行纪律
2. 批量更新 ~25 Capsule GATE
3. stock-quickread SKILL.md pipeline 步骤硬化（作为模板）
4. stock-quickread SKILL.en.md 同步
5. pre_write_gate CHECK 15
6. 其他 skill pipeline 步骤硬化（分批）
7. CPR v5.14.2
```

---

## 影响面

| 层 | 文件数 | 风险 |
|---|---|---|
| CLAUDE.md templates | 2 | 低 |
| Capsule GATE | ~50 | 低——文本替换 |
| stock-quickread pipeline | 2 | 低 |
| pre_write_gate | 1 | 中——新增 hook rule |
| 其他 skill | 分批 | 低 |
