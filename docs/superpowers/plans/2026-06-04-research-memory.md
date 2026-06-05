# Research Memory 系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为每个行业和公司创建 RESEARCH.md 记忆文件 + CC 自动加载卡片生成脚本 + hook 更新提醒

**Architecture:** 两个 markdown 模板（行业/公司）→ agent 手动维护 RESEARCH.md → `generate-memory-cards.py` 扫描提取生成 `memory/research/*.md` 薄卡片 → CC session 启动自动加载 → hook 在写 artifact 后提示更新

**Tech Stack:** Python 3, markdown (frontmatter + tables), bash

---

## File Structure

```
_shared/templates/research-memory-industry.md  # 行业模板 (NEW)
_shared/templates/research-memory-company.md   # 公司模板 (NEW)
_scripts/shared/generate-memory-cards.py        # 卡片生成脚本 (NEW)
.claude/hooks/rules/research_memory_gate.py     # Hook: 写 artifact 后提示更新 (NEW)
.claude/hooks/hook_entry.py                     # 注册新 hook (MODIFY)
memory/research/                                # CC 自动加载卡片目录 (NEW)
CLAUDE.md                                       # §5.5 加入读取指令 (MODIFY)
industry/*/RESEARCH.md                          # 从各 index.md 迁移 (MIGRATE)
```

---

### Task 1: 行业 RESEARCH.md 模板

**Files:**
- Create: `_shared/templates/research-memory-industry.md`

- [ ] **Step 1: 写行业模板文件**

```markdown
---
industry: <industry-slug>
updated: YYYY-MM-DD
stage: new | active | deep-dive | dormant
---

# <行业中文名> (<Industry English>) — Research Memory

## 1. 覆盖公司
| 公司 | Ticker | 路径 | Thesis 阶段 | 优先级 |
|---|---|---|---|---|
| ... | ... | [companies/<slug>/](./companies/<slug>/) | new/tracking/sizing/conviction/exited | 🔥高/中/低 |

## 2. 研究产出
| 日期 | Artifact | 一句话要点 |
|---|---|---|
| YYYY-MM-DD | [filename.md](./filename.md) | ... |

## 3. Source 地图
### 行业报告 / 协会 / 政策
| 来源 | URL | 本地缓存 | 覆盖 |
|---|---|---|---|
### 跨公司共用
| 来源 | URL | 本地缓存 | 覆盖 |
### 缺的 source
- [ ] ...
### 联系过的人 / 渠道
| 谁 | 渠道 | 聊了什么 | 日期 |
|---|---|---|---|
| ... | IR call / expert / channel check | ... | ... |

## 4. 行业 Thesis
### 周期判断
<1-2 句：当前周期阶段 + 方向>

### 结构性观点
| # | 观点 | 状态 | 最新确认 | 风险 |
|---|---|---|---|---|
| 1 | ... | ✅/🔥/❓/❌ | ... | ... |

### 核心争论
<多空分歧>

### 待验证
- [ ] ...

## 5. 事实基线
| 事实 | 值 | 适用范围 | 来源 | as-of |
|---|---|---|---|---|
| ... | ... | 行业整体 / 某子领域 | ... | ... |

## 6. 研究轨迹
### 下一步（跨公司）
1. ...
### 上个 session 读到哪
- YYYY-MM-DD: ...

### 关联行业
| 行业 | 说明 |
|---|---|
| [<slug>](../<slug>/RESEARCH.md) | ... |
```

- [ ] **Step 2: Commit**

```bash
git add _shared/templates/research-memory-industry.md
git commit -m "feat: add industry RESEARCH.md template"
```

---

### Task 2: 公司 RESEARCH.md 模板

**Files:**
- Create: `_shared/templates/research-memory-company.md`

- [ ] **Step 1: 写公司模板文件**

```markdown
---
ticker: <TICKER>
industry: <industry-slug>
updated: YYYY-MM-DD
stage: new | tracking | sizing | conviction | exited
conviction: 1-10
---

> 关联行业：[<行业名>](../RESEARCH.md)

# <公司名> (<TICKER>) — Research Memory

## 1. Source 地图
| 类型 | 文件 | URL | 本地缓存 | 覆盖内容 | 周期 |
|---|---|---|---|---|---|
| 年报 | ... | ... | _cache/... | ... | 年 |
| 季报/IR | ... | ... | _cache/... | ... | 季 |
| 第三方 | ... | ... | _cache/... | ... | — |

### 缺的 source
- [ ] ...

### 联系过的人 / 渠道
| 谁 | 渠道 | 聊了什么 | 日期 |
|---|---|---|---|
| ... | IR call / expert / channel check | ... | ... |

## 2. Thesis 状态
### 当前倾向
<一句话>

### 核心假设
| # | 假设 | 状态 | 最新确认 | 风险点 |
|---|---|---|---|---|
| 1 | ... | ✅/🔥/❓/❌ | ... | ... |

### 空头需要相信什么
- ...

### 多头需要相信什么（如果当前偏空）
- ...

## 3. 事实基线

### 速查卡
| 指标 | 值 | 同比/趋势 | 来源 |
|---|---|---|---|
| <thesis 盯的 5-8 个数> | ... | ... | ... |

### 完整事实表
| 事实 | 值 | 来源 | as-of |
|---|---|---|---|
| ... | ... | ... | ... |

### 已推翻
| 旧认知 | 推翻原因 | 新认知 | 日期 |
|---|---|---|---|
| ... | ... | ... | ... |

## 4. 研究轨迹
### 已完成
| 日期 | Artifact | 一句话产出 |
|---|---|---|

### 下一步 5 个问题
1. ...

### 已排除的方向
- ❌ <方向>——<为什么死胡同>

### 上次读到哪
- YYYY-MM-DD: <具体位置 + 待完成>
```

- [ ] **Step 2: Commit**

```bash
git add _shared/templates/research-memory-company.md
git commit -m "feat: add company RESEARCH.md template"
```

---

### Task 3: 卡片生成脚本

**Files:**
- Create: `_scripts/shared/generate-memory-cards.py`

- [ ] **Step 1: 写生成脚本**

```python
#!/usr/bin/env python3
"""Generate thin CC memory cards from RESEARCH.md files.

Scans industry/*/RESEARCH.md and industry/*/companies/*/RESEARCH.md,
extracts key fields, writes memory/research/<entity>.md (≤500 words each).
"""
import os
import re
import sys
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDUSTRY_DIR = os.path.join(WORKSPACE, "industry")
MEMORY_DIR = os.path.join(WORKSPACE, "memory", "research")

# ── helpers ──────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    """Extract YAML-like frontmatter from markdown."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).strip().split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            fm[k.strip()] = v.strip()
    return fm


def _extract_section(text: str, heading: str, stop_headings: list[str] | None = None) -> str:
    """Extract content between a heading and the next heading of same or higher level."""
    stops = stop_headings or []
    # match the heading (## N. Title format)
    pattern = rf'(?:^|\n)## {re.escape(heading)}\s*\n(.*?)(?=\n## |\n# |\Z)'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def _count_words(text: str) -> int:
    return len(text.split())


def _trim_to_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return ' '.join(words[:limit]) + '...'


# ── card generators ──────────────────────────────────────

def _generate_industry_card(text: str, slug: str) -> str:
    """Generate thin card for an industry RESEARCH.md."""
    fm = _parse_frontmatter(text)
    # §1 company table (keep compact)
    companies = _extract_section(text, "1. 覆盖公司")
    # §4 cycle judgment
    cycle = _extract_section(text, "4. 行业 Thesis")
    # §6 last read
    trail = _extract_section(text, "6. 研究轨迹")

    # Extract just the table rows from companies, not the header
    rows = [l for l in companies.split('\n') if l.startswith('|') and not l.startswith('| 公司')]

    card = f"""---
industry: {slug}
stage: {fm.get('stage', '?')}
updated: {fm.get('updated', '?')}
---

# {slug} — 行业速览

## 覆盖公司
{'| 公司 | Ticker | Thesis 阶段 | 优先级 |'}
{'|---|---|---|---|'}
{chr(10).join(rows[:15])}

## 周期判断
{_trim_to_words(cycle.split('\n')[0] if cycle else '?', 100)}

## 上次读到哪
{_trim_to_words(trail, 150) if trail else '?'}
"""
    return _trim_to_words(card, 500)


def _generate_company_card(text: str, ticker: str) -> str:
    """Generate thin card for a company RESEARCH.md."""
    fm = _parse_frontmatter(text)
    # §2 current lean + core assumptions
    thesis = _extract_section(text, "2. Thesis 状态")
    # §3 speed card
    speed = _extract_section(text, "3. 事实基线")
    # §4 last read
    trail = _extract_section(text, "4. 研究轨迹")

    card = f"""---
ticker: {ticker}
industry: {fm.get('industry', '?')}
stage: {fm.get('stage', '?')}
conviction: {fm.get('conviction', '?')}
updated: {fm.get('updated', '?')}
---

# {ticker} — 研究速览

## Thesis
{_trim_to_words(thesis.split('\n')[0] if thesis else '?', 150)}

## 速查卡
{_trim_to_words(speed, 200) if speed else '?'}

## 上次读到哪
{_trim_to_words(trail, 200) if trail else '?'}
"""
    return _trim_to_words(card, 500)


# ── main ─────────────────────────────────────────────────

def main():
    os.makedirs(MEMORY_DIR, exist_ok=True)

    count = 0

    # Industry cards
    if os.path.isdir(INDUSTRY_DIR):
        for slug in sorted(os.listdir(INDUSTRY_DIR)):
            indir = os.path.join(INDUSTRY_DIR, slug)
            if not os.path.isdir(indir):
                continue
            rm_path = os.path.join(indir, "RESEARCH.md")
            if not os.path.exists(rm_path):
                continue
            with open(rm_path, "r", encoding="utf-8") as f:
                text = f.read()
            card = _generate_industry_card(text, slug)
            out = os.path.join(MEMORY_DIR, f"{slug}.md")
            with open(out, "w", encoding="utf-8") as f:
                f.write(card)
            count += 1

            # Company cards within this industry
            comp_dir = os.path.join(indir, "companies")
            if not os.path.isdir(comp_dir):
                continue
            for ticker in sorted(os.listdir(comp_dir)):
                crm = os.path.join(comp_dir, ticker, "RESEARCH.md")
                if not os.path.exists(crm):
                    continue
                with open(crm, "r", encoding="utf-8") as f:
                    text = f.read()
                card = _generate_company_card(text, ticker)
                out = os.path.join(MEMORY_DIR, f"{ticker}.md")
                with open(out, "w", encoding="utf-8") as f:
                    f.write(card)
                count += 1

    print(f"Generated {count} memory cards → {MEMORY_DIR}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试——创建临时 RESEARCH.md 验证生成**

```bash
# Create a quick test
mkdir -p /tmp/test-research/industry/test-industry/companies/TEST
cp _shared/templates/research-memory-industry.md /tmp/test-research/industry/test-industry/RESEARCH.md
cp _shared/templates/research-memory-company.md /tmp/test-research/industry/test-industry/companies/TEST/RESEARCH.md
# Modify paths for test
python _scripts/shared/generate-memory-cards.py
# Should print: Generated 2 memory cards → .../memory/research/
```

Expected: script runs without error, produces 2 `.md` cards in `memory/research/` with ≤500 words each.

- [ ] **Step 3: Clean up test and commit**

```bash
rm -rf /tmp/test-research
git add _scripts/shared/generate-memory-cards.py
git commit -m "feat: add generate-memory-cards.py for RESEARCH.md → CC memory cards"
```

---

### Task 4: Hook — artifact 写完后提示更新 RESEARCH.md

**Files:**
- Create: `.claude/hooks/rules/research_memory_gate.py`
- Modify: `.claude/hooks/hook_entry.py`

- [ ] **Step 1: 写 hook 文件**

```python
"""Hook: after writing a research artifact, remind agent to update RESEARCH.md.

This is a WARN-level hook — it never blocks, only suggests.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import warn

ARTIFACT_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})-[\w-]+\.md$')
TICKER_FROM_PATH_RE = re.compile(r'companies[/\\]([a-zA-Z0-9_-]+)')


def _find_research_md(artifact_path: str) -> str | None:
    """Map artifact path → corresponding RESEARCH.md."""
    artifact_dir = os.path.dirname(artifact_path)
    # Try company level first
    company_rm = os.path.join(artifact_dir, "RESEARCH.md")
    if os.path.exists(company_rm):
        return company_rm
    # Try industry level (go up from companies/<ticker>/ to industry/)
    up = os.path.dirname(os.path.dirname(artifact_dir))
    industry_rm = os.path.join(up, "RESEARCH.md")
    if os.path.exists(industry_rm):
        return industry_rm
    return None


def check(ctx):
    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path") or ""
        display = t.get("display", "unknown")
        leaf = os.path.basename(path)

        # Only match YYYY-MM-DD-skill-*.md artifacts
        if not ARTIFACT_RE.match(leaf):
            continue

        rm_path = _find_research_md(path)
        if not rm_path:
            continue

        # Check if RESEARCH.md was updated today
        try:
            import datetime
            mtime = os.path.getmtime(rm_path)
            mdate = datetime.date.fromtimestamp(mtime)
            today = datetime.date.today()
            if mdate < today:
                warn(f"research_memory_gate: {display} 已写入，"
                     f"但对应 RESEARCH.md ({os.path.basename(os.path.dirname(rm_path))}) "
                     f"上次更新是 {mdate}。建议更新 RESEARCH.md 的相关 section。")
        except OSError:
            pass

    sys.exit(0)
```

- [ ] **Step 2: 注册 hook 到 STOP_RULES**

Edit `.claude/hooks/hook_entry.py` line 40-45:

```python
STOP_RULES = [
    "source_contract",
    "table_render_integrity",
    "mermaid_syntax",
    "evidence_ledger_floor",
    "research_memory_gate",
]
```

- [ ] **Step 3: 测试 hook 触发**

```bash
# Create a fake artifact write to trigger the hook
# Simulate a Stop event with a target that's a research artifact
python .claude/hooks/hook_entry.py --runtime claude --event Stop << 'EOF'
{"targets": [{"kind": "file", "path": "industry/optical-module-equipment/companies/mycronic/2026-06-04-test.md", "display": "test artifact"}]}
EOF
```

Expected: If RESEARCH.md exists and its mtime < today, prints a warn message. Does NOT exit with non-zero (warn only, no block).

- [ ] **Step 4: Commit**

```bash
git add .claude/hooks/rules/research_memory_gate.py .claude/hooks/hook_entry.py
git commit -m "feat: add research_memory_gate hook — warn on stale RESEARCH.md after artifact write"
```

---

### Task 5: CLAUDE.md §5.5 加入 RESEARCH.md 读取指令

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 在 CLAUDE.md §5.5 末尾追加 RESEARCH.md 指令块**

Read CLAUDE.md, locate the end of §5.5 (before §6 or end of file), and append:

```markdown
### Research Memory 系统

每个行业和公司目录下有一个 `RESEARCH.md`（命名固定大写），记录四层信息：
1. **Source 地图** — 所有关键披露/第三方文件的 URL 和本地缓存路径
2. **Thesis 状态** — 当前多空倾向、核心假设及验证状态
3. **事实基线** — 速查卡（thesis 盯的 5-8 个数）+ 完整表 + 已推翻认知
4. **研究轨迹** — 已完成 artifact、下一步 5 问、已排除方向、上次读到哪

**自动加载**：`memory/research/` 下的薄卡片由 `generate-memory-cards.py` 从 RESEARCH.md 自动生成，CC session 启动时自动注入。

**Agent 行为**：
- 新 session 提到公司/ticker → 先 `Read` 对应公司 RESEARCH.md + 行业 RESEARCH.md
- 每次产出 artifact 后 → 更新对应 RESEARCH.md 的相关 section（≤5 分钟，增量维护）
- Hook 会在写 artifact 后提醒更新，但最终由 agent 负责
- RESEARCH.md 是覆盖更新（非 append），只保留最新状态
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add RESEARCH.md reading instructions to CLAUDE.md §5.5"
```

---

### Task 6: 迁移现有 index.md → RESEARCH.md

**Files:**
- Create: 7 个行业 `RESEARCH.md`（从现有 `index.md` 迁移）
- Delete: 7 个 `index.md`（迁移后）

现有的行业目录：
```
industry/aerospace/index.md
industry/foundry/index.md
industry/korea-defense/index.md
industry/optical-module-equipment/index.md
industry/pcb-equipment/index.md
industry/quantum/index.md
industry/ship-building/index.md
```

- [ ] **Step 1: 逐个行业迁移 index.md → RESEARCH.md**

对每个行业：
1. `Read` 现有 `index.md`
2. 将其内容映射到 RESEARCH.md 模板：
   - 公司列表 → §1 覆盖公司
   - 研究产出列表 → §2 研究产出
   - "待解决问题" → §4 Thesis "待验证"
   - "来源" → §3 Source 地图
   - "当前问题" → §4 周期判断
   - "相关 Topics" → §6 关联行业
3. 用 `Write` 创建 RESEARCH.md
4. `Bash rm` 删除 index.md

具体映射示例（以 optical-module-equipment 为例）：

markdown 内容从 index.md 提取并按模板重组。frontmatter 中 `industry` 取目录 slug，`stage` 从最新 artifact 密度判断（有 artifact → active，只有 index → new）。

- [ ] **Step 2: 运行卡片生成脚本**

```bash
python _scripts/shared/generate-memory-cards.py
```

Expected: `Generated 7 memory cards → .../memory/research/`

- [ ] **Step 3: 验证 memory/research/ 输出**

```bash
ls memory/research/
# Should see: aerospace.md, foundry.md, korea-defense.md, optical-module-equipment.md, pcb-equipment.md, quantum.md, ship-building.md
wc -w memory/research/*.md
# Each should be ≤500 words
```

- [ ] **Step 4: Commit**

```bash
git add industry/*/RESEARCH.md memory/research/
git rm industry/*/index.md
git commit -m "migrate: index.md → RESEARCH.md for all 7 industries"
```

---

### Task 7: 为已有公司创建 RESEARCH.md 骨架

**Files:**
- Create: 每个公司目录下 `RESEARCH.md`（从模板 + 已有 artifact 提取）

已有公司目录（从 COVERAGE.md 和实际目录扫描）：
```
aerospace: spacex
korea-defense: hanwha-aerospace, hanwha-systems, hyundai-rotem, kai, lig-nex1
optical-module-equipment: anritsu, asmpt, besi, bozhong, keysight, mycronic, robo-technik, semight
pcb-equipment: mycronic (symlink or shared)
```

- [ ] **Step 1: 批量为已有公司创建 RESEARCH.md 骨架**

对每个公司目录：
1. 检查是否已有 RESEARCH.md（跳过）
2. 从模板 `_shared/templates/research-memory-company.md` 复制骨架
3. 填入 ticker、industry、stage（默认 new）、conviction（默认 3）
4. 如存在 actuals-resolved.json → 从 supplementary 字段提取公司全名
5. 如存在 evidence ledger → 统计 verified claims 数量填入
6. `Write` 创建

```bash
# Script to batch-create company RESEARCH.md stubs
python -c "
import os, json

workspace = 'industry'
template_path = '_shared/templates/research-memory-company.md'
with open(template_path, 'r', encoding='utf-8') as f:
    template = f.read()

for industry_dir in os.listdir(workspace):
    comp_dir = os.path.join(workspace, industry_dir, 'companies')
    if not os.path.isdir(comp_dir):
        continue
    for ticker in os.listdir(comp_dir):
        rm_path = os.path.join(comp_dir, ticker, 'RESEARCH.md')
        if os.path.exists(rm_path):
            continue
        content = template.replace('<TICKER>', ticker)
        content = content.replace('<industry-slug>', industry_dir)
        content = content.replace('<公司名>', ticker)
        content = content.replace('<行业名>', industry_dir)
        with open(rm_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Created {rm_path}')
"
```

Expected: Creates RESEARCH.md for ~15 companies with bare skeleton.

- [ ] **Step 2: 运行卡片生成 + 验证**

```bash
python _scripts/shared/generate-memory-cards.py
ls memory/research/ | wc -l
# Should be 7 industries + ~15 companies = ~22 cards
```

- [ ] **Step 3: 更新 COVERAGE.md**

在 COVERAGE.md 末尾加一行注释：
```
<!-- 详细研究状态见各行业 RESEARCH.md。本文件仅保留全局跨行业注册。—— 2026-06-04 research-memory migration -->
```

- [ ] **Step 4: Commit**

```bash
git add industry/*/companies/*/RESEARCH.md memory/research/ COVERAGE.md
git commit -m "feat: create RESEARCH.md skeletons for all companies, generate CC memory cards"
```

---

## Post-Implementation Verification

全部完成后验证：

```bash
# 1. 所有行业有 RESEARCH.md
find industry/ -maxdepth 2 -name "RESEARCH.md" | wc -l  # ≥7

# 2. 所有公司有 RESEARCH.md
find industry/ -maxdepth 4 -name "RESEARCH.md" | wc -l  # ≥15

# 3. index.md 全部删除
find industry/ -name "index.md"  # 无输出

# 4. 卡片生成成功
python _scripts/shared/generate-memory-cards.py
# Output: Generated N memory cards

# 5. Hook 可加载
python .claude/hooks/hook_entry.py --runtime claude --event Stop < /dev/null 2>&1
# No import errors
```
