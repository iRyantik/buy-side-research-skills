# RESEARCH.md 研究轨迹自动追加 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stop hook 自动在 RESEARCH.md §4 追加 artifact 记录

**Architecture:** 升级 `research_memory_gate.py` —— Stop 时检测新 artifact → 提取标题摘要 → 在 RESEARCH.md `### 已完成` 表追加行 → 更新 frontmatter `updated`。原 warn 逻辑保留。

**Tech Stack:** Python 3, regex

---

### Task 1: 升级 research_memory_gate.py

**Files:**
- Modify: `.claude/hooks/rules/research_memory_gate.py`

**Step 1: 重写 hook**

Replace the entire file content:

```python
"""Hook: after writing a research artifact, auto-append to RESEARCH.md trail + warn if stale.

Trail append (§4 已完成): automatic, no user intervention.
Stale check (other sections): warn only, agent must update manually.
"""
import os
import re
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import warn

ARTIFACT_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})-[\w-]+\.md$')
FRONTMATTER_UPDATED_RE = re.compile(r'^updated:\s*(\S+)', re.MULTILINE)

# Patterns to extract summary from artifact
TITLE_RE = re.compile(r'^#\s+(.+)', re.MULTILINE)


def _find_research_md(artifact_path: str) -> str | None:
    """Map artifact path -> corresponding RESEARCH.md (company preferred)."""
    artifact_dir = os.path.dirname(os.path.abspath(artifact_path))
    company_rm = os.path.join(artifact_dir, "RESEARCH.md")
    if os.path.exists(company_rm):
        return company_rm
    up = os.path.dirname(os.path.dirname(artifact_dir))
    industry_rm = os.path.join(up, "RESEARCH.md")
    if os.path.exists(industry_rm):
        return industry_rm
    return None


def _extract_summary(artifact_path: str) -> str:
    """Extract one-line summary from artifact: first # title or first paragraph."""
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            head = f.read(3000)
    except Exception:
        return os.path.basename(artifact_path)
    
    m = TITLE_RE.search(head)
    if m:
        title = m.group(1).strip()
        # Strip Research Memory suffix
        title = re.sub(r'\s*[-—]\s*Research Memory.*$', '', title)
        return title[:120]
    
    # Fallback: first non-empty, non-metadata line
    for line in head.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("---") and not stripped.startswith(">"):
            return stripped[:120]
    
    return os.path.basename(artifact_path)


def _make_trail_row(date_str: str, filename: str, summary: str) -> str:
    """Build a markdown table row for the trail."""
    # Relative link from RESEARCH.md to artifact
    link = f"[{filename}](./{filename})"
    return f"| {date_str} | {link} | {summary} |"


def _append_trail(research_md_path: str, row: str, artifact_filename: str) -> bool:
    """Append a row to the ### 已完成 table in RESEARCH.md. Returns True if written."""
    with open(research_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if this artifact already has a row
    if artifact_filename in content:
        # Already recorded — skip
        return False
    
    # Find ### 已完成 section
    done_marker = "### 已完成"
    done_idx = content.find(done_marker)
    
    if done_idx == -1:
        # Create the section under ## 4. 研究轨迹
        trail_marker = "## 4. 研究轨迹"
        trail_idx = content.find(trail_marker)
        if trail_idx == -1:
            return False
        # Find end of ## 4 section (next ## or end of file)
        next_section = re.search(r'\n## ', content[trail_idx + len(trail_marker):])
        insert_at = trail_idx + len(trail_marker) + next_section.start() if next_section else len(content)
        block = f"\n\n{done_marker}\n| 日期 | Artifact | 一句话产出 |\n|---|---|---|\n{row}\n"
        new_content = content[:insert_at] + block + content[insert_at:]
    else:
        # Find the table header row after ### 已完成
        rest = content[done_idx + len(done_marker):]
        table_header = re.search(r'\|[-\s|]+\|', rest)
        if not table_header:
            return False
        insert_at = done_idx + len(done_marker) + table_header.end() + 1
        new_content = content[:insert_at] + row + "\n" + content[insert_at:]
    
    with open(research_md_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def _update_frontmatter_updated(research_md_path: str, today_str: str):
    """Update the updated: field in frontmatter."""
    with open(research_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = FRONTMATTER_UPDATED_RE.sub(f"updated: {today_str}", content)
    
    if new_content != content:
        with open(research_md_path, "w", encoding="utf-8") as f:
            f.write(new_content)


def check(ctx):
    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path") or ""
        display = t.get("display", "unknown")
        leaf = os.path.basename(path)

        if not ARTIFACT_RE.match(leaf):
            continue

        rm_path = _find_research_md(path)
        if not rm_path:
            continue

        # ── Auto: append trail row ──
        date_str = leaf[:10]  # YYYY-MM-DD
        summary = _extract_summary(path)
        row = _make_trail_row(date_str, leaf, summary)
        written = _append_trail(rm_path, row, leaf)
        if written:
            today = datetime.date.today().isoformat()
            _update_frontmatter_updated(rm_path, today)
            print(f"research_memory_gate: appended trail -> {os.path.basename(os.path.dirname(rm_path))}/RESEARCH.md",
                  file=sys.stderr)

        # ── Warn: stale check (other sections still manual) ──
        try:
            mtime = os.path.getmtime(rm_path)
            mdate = datetime.date.fromtimestamp(mtime)
            today_date = datetime.date.today()
            if mdate < today_date:
                warn(f"research_memory_gate: {display} written, "
                     f"but RESEARCH.md other sections (Source/Thesis/事实基线) "
                     f"last updated {mdate}. Consider updating manually.")
        except OSError:
            pass

    sys.exit(0)
```

**Step 2: 测试——写入 mock artifact 到 Mycronic 目录**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"

# Backup current RESEARCH.md
cp industry/optical-module-equipment/companies/mycronic/RESEARCH.md /tmp/RESEARCH.md.bak

# Create a test artifact
echo "# Mycronic — 测试 artifact
这是测试内容。" > "industry/optical-module-equipment/companies/mycronic/2026-06-05-test-skill-mycronic.md"

# Trigger hook
echo "{\"cwd\":\"$(pwd)\",\"targets\":[{\"kind\":\"file\",\"path\":\"industry/optical-module-equipment/companies/mycronic/2026-06-05-test-skill-mycronic.md\",\"display\":\"test\"}]}" | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"

# Check RESEARCH.md
echo "=== Trail section ===" && grep -A5 "### 已完成" industry/optical-module-equipment/companies/mycronic/RESEARCH.md
echo "=== Updated date ===" && grep "updated:" industry/optical-module-equipment/companies/mycronic/RESEARCH.md
```

Expected: RESEARCH.md has a new row in 已完成 table with `2026-06-05 | [2026-06-05-test-skill-mycronic.md] | Mycronic — 测试 artifact |`. `updated:` date changed to 2026-06-05.

**Step 3: 再次触发——验证去重**

Run the same Stop event again. Expected: no duplicate row appended.

**Step 4: 清理测试文件并恢复**

```bash
rm "industry/optical-module-equipment/companies/mycronic/2026-06-05-test-skill-mycronic.md"
cp /tmp/RESEARCH.md.bak industry/optical-module-equipment/companies/mycronic/RESEARCH.md
```

**Step 5: 同步到 plugin repo + 全管线测试**

```bash
cp .claude/hooks/rules/research_memory_gate.py <plugin-assets>/.claude/hooks/rules/
echo '{"targets":[]}' | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1; echo "Exit: $?"
```
