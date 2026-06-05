# PDF Auto-Cache Hook + 缓存优先 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hook 拦截 PDF 下载 → 判断一手资料 → 自动转 markdown 缓存 + 删 PDF + 缓存优先规则写入所有文档

**Architecture:** `get_candidate_paths()` 扩展 `.pdf` 检测 → `pdf_auto_cache.py` hook 在 Stop 时扫 PDF targets → `is_primary_source()` 判断 → `to-markdown.py --cache --rm` 转存删 → research-runtime.md + CLAUDE.md 缓存优先规则

**Tech Stack:** Python 3, regex, subprocess (to-markdown.py)

---

## File Structure

```
.claude/hooks/rules/pdf_auto_cache.py        # 🆕 Hook 主逻辑
.claude/hooks/common.py                      # ✏️ get_candidate_paths() 扩展 .pdf
.claude/hooks/hooks.registry.yaml            # ✏️ 注册 pdf_auto_cache
.claude/hooks/hook_entry.py                  # ✏️ STOP_RULES 加 pdf_auto_cache
_scripts/shared/to-markdown.py               # ✏️ 加 --rm + --auto flag
_shared/research-runtime.md                  # ✏️ 升级 §2.1.1 + 新增 §2.1.2
_shared/research-runtime.en.md               # ✏️ 英文同步
CLAUDE.md.template                           # ✏️ 加缓存优先规则 (plugin repo)
CLAUDE.en.md.template                        # ✏️ 英文同步 (plugin repo)
CLAUDE.md                                    # ✏️ workspace live copy
```

---

### Task 1: `get_candidate_paths()` 扩展 `.pdf` 检测

**Files:**
- Modify: `.claude/hooks/common.py:74-91`

- [ ] **Step 1: 扩展三个 regex 匹配新增 `.pdf` 扩展名**

Read `.claude/hooks/common.py` lines 74-91. The three regex patterns in `get_candidate_paths()` currently match `md|html|xlsx`. Add `|pdf` to each:

```python
# Line 78 — Bash redirections
# OLD: r'(?:>|>>)\s*["\']?([^"\'\s]+\.(?:md|html|xlsx))'
# NEW:
for m in re.finditer(r'(?:>|>>)\s*["\']?([^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):

# Line 83 — Windows absolute paths  
# OLD: r'["\']?([A-Z]:\\[^"\'\s]+\.(?:md|html|xlsx))'
# NEW:
for m in re.finditer(r'["\']?([A-Z]:\\[^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):

# Line 88 — Python/script write paths
# OLD: r'''(?:r)?["']([^"'\n]+?\.(?:md|html|xlsx))["']'''
# NEW:
for m in re.finditer(r'''(?:r)?["']([^"'\n]+?\.(?:md|html|xlsx|pdf))["']''', cmd):
```

Also add `download_path` / `suggestedFilename` extraction for Playwright MCP browser_download:

After the existing file path fields block (line 67-72), add:

```python
    # browser_download: Playwright MCP download path
    for key in ("download_path", "suggestedFilename", "downloadPath"):
        val = ti.get(key, "")
        if val and val.lower().endswith(".pdf"):
            r = resolve_path(str(val), root)
            if r:
                paths.append(r)
```

- [ ] **Step 2: 验证**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"
echo '{"cwd":"'$(pwd)'","tool_input":{"command":"curl -o test.pdf https://example.com/report.pdf"}}' | python -c "
import sys,json
sys.path.insert(0,'.claude/hooks')
from common import get_candidate_paths
payload = json.load(sys.stdin)
paths = get_candidate_paths(payload)
pdfs = [p for p in paths if p.endswith('.pdf')]
print(f'PDF paths detected: {len(pdfs)}')
assert len(pdfs) > 0, 'FAIL: no PDF paths found'
print('PASS')
"
```

Expected: `PDF paths detected: 1` + `PASS`

---

### Task 2: `to-markdown.py` 加 `--rm` + `--auto` flag

**Files:**
- Modify: `_scripts/shared/to-markdown.py:196-222` (main function)

- [ ] **Step 1: 在 argparse 中添加两个新参数**

In `main()`, after the existing `--format` argument, add:

```python
p.add_argument("--rm", action="store_true",
               help="Delete source file after successful cache")
p.add_argument("--auto", action="store_true",
               help="Silent mode: suppress stdout (for hook-driven calls)")
```

- [ ] **Step 2: 在 `--cache` 写入后加删除逻辑**

In `main()`, after the `if args.cache:` block (after `print(f"  Cached: {cp}", file=sys.stderr)`), add:

```python
    # Delete source PDF on success (hook-driven cache)
    if args.rm and args.cache:
        try:
            os.remove(args.file)
            print(f"  Deleted: {args.file}", file=sys.stderr)
        except OSError as e:
            print(f"  WARN: could not delete {args.file}: {e}", file=sys.stderr)
```

- [ ] **Step 3: 静默模式——抑制 stdout**

After `main()` converts and before printing, wrap the `print(md)` at the end:

```python
    if not args.auto:
        print(md)
```

- [ ] **Step 4: 测试**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"
# Test --rm flag with a sample PDF
cp "mycronic-fy2025-segment-ebit.png" /tmp/test-rm.pdf 2>/dev/null || python -c "open('/tmp/test-rm.pdf','w').write('test')"
python _scripts/shared/to-markdown.py /tmp/test-rm.pdf --cache TEST test-rm --rm --auto 2>&1
echo "Exit: $?"
ls /tmp/test-rm.pdf 2>/dev/null && echo "PDF still exists (expected for 0-page PDF)" || echo "PDF deleted"
```

Expected: runs without error, PDF deleted if conversion succeeded.

---

### Task 3: `pdf_auto_cache.py` Hook 主逻辑

**Files:**
- Create: `.claude/hooks/rules/pdf_auto_cache.py`

- [ ] **Step 1: 写 Hook 文件**

```python
"""Hook: intercept PDF downloads from primary sources and auto-cache as markdown.

Detects PDFs written by Bash/browser_download, checks if they are primary-source
documents (IR/filing URL patterns or filename keywords), converts via to-markdown.py,
caches to _cache/, and deletes the original PDF.

Non-blocking — failures log warnings and preserve the PDF.
"""
import os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import warn

# ── A track — multi-market regulatory filing / IR URL patterns ──
PRIMARY_SOURCE_URLS = [
    # Company IR
    r"ir\.[a-z0-9-]+\.(?:com|co\.\w{2,3})",
    r"investor[s]?\.[a-z0-9-]+\.(?:com|co\.\w{2,3})",
    r"/ir/", r"/investor[s]?/",
    # US (SEC/EDGAR)
    r"sec\.gov", r"data\.sec\.gov",
    # HK (HKEX)
    r"hkexnews\.hk", r"\.hkex\.com\.hk",
    # JP (TDNET/EDINET)
    r"tdnet\.", r"disclosure\.tdnet", r"disclosure2\.",
    r"edinet-fsa\.go\.jp", r"disclosure\.edinet",
    # KR (DART/KIND)
    r"dart\.fss\.or\.kr", r"kind\.krx\.co\.kr",
    # CN (巨潮/上交所/深交所)
    r"cninfo\.com\.cn", r"sse\.com\.cn", r"szse\.cn",
    # TW (MOPS)
    r"mops\.twse\.com\.tw", r"emops\.twse\.com\.tw",
    # EU / UK / CA
    r"companieshouse\.gov\.uk", r"bundesanzeiger\.de",
    r"sedar\.com", r"\.europa\.eu/",
    # Generic filing/disclosure paths
    r"/annual[-_]", r"/quarterly[-_]", r"/earnings[-_]",
    r"/transcript[s]?", r"/prospectus",
    r"/s-?1[/\.]", r"/10-?[kq][/\.]", r"/20-?f[/\.]",
    r"/8-?k[/\.]", r"/6-?k[/\.]",
]

# ── B track — filename keywords ──
PRIMARY_KEYWORDS = [
    "annual", "quarterly", "earnings", "transcript",
    "prospectus", "filing", "ir-", "fy", "1q", "2q", "3q", "4q",
    "10-k", "10-q", "20-f", "8-k", "6-k", "s-1", "s1",
    "招股", "年报", "季报", "半年报", "中期报告",
    "決算", "有価証券報告書", "四半期",
]

# Temporary paths we should not try to derive ticker from
SKIP_PREFIXES = ("/tmp/", "/temp/", "C:\\Windows\\Temp", "Downloads\\")

URL_RE = re.compile(r'https?://[^\s"\'<>]+', re.IGNORECASE)


def _is_primary_source(url_hint: str, filename: str) -> bool:
    """Return True if this PDF is a primary-source regulatory/IR document."""
    # A track: URL pattern
    if url_hint:
        for pattern in PRIMARY_SOURCE_URLS:
            if re.search(pattern, url_hint, re.IGNORECASE):
                return True
    # B track: filename keywords
    lower = filename.lower()
    for kw in PRIMARY_KEYWORDS:
        if kw in lower:
            return True
    return False


def _extract_url_from_bash(cmd: str) -> str:
    """Extract likely source URL from a Bash command."""
    urls = URL_RE.findall(cmd)
    return urls[0] if urls else ""


def _derive_ticker(workspace: str, pdf_path: str) -> str | None:
    """Derive ticker by searching industry/*/companies/<ticker>/ for a _cache/ dir."""
    industry_dir = os.path.join(workspace, "industry")
    if not os.path.isdir(industry_dir):
        return None
    # Try to match path components against ticker directories
    for ind in os.listdir(industry_dir):
        ind_path = os.path.join(industry_dir, ind)
        if not os.path.isdir(ind_path):
            continue
        comp_dir = os.path.join(ind_path, "companies")
        if not os.path.isdir(comp_dir):
            continue
        # Check if pdf_path contains the ticker name
        pdf_lower = pdf_path.lower()
        for ticker in os.listdir(comp_dir):
            ticker_lower = ticker.lower().replace(" ", "-").replace("_", "-")
            if ticker_lower in pdf_lower:
                return ticker
    return None


def _derive_desc(filename: str) -> str:
    """Derive a short cache description from PDF filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Clean: replace spaces, underscores, special chars with hyphens
    name = re.sub(r'[^a-zA-Z0-9一-鿿-]', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-').lower()
    # Truncate
    return name[:60] if len(name) > 60 else name


def check(ctx):
    # Find PDF files among targets by inspecting candidate_paths from raw payload
    payload = ctx.get("raw_payload", {})
    root = ctx.get("cwd", "")
    ti = payload.get("tool_input") or payload.get("toolInput") or {}

    # Collect source URL hints
    url_hint = ti.get("url", "") or ""
    if not url_hint:
        cmd = ti.get("command", "") or ""
        url_hint = _extract_url_from_bash(cmd)
    if not url_hint:
        # Check assistant message for URLs near the PDF mention
        msg = payload.get("assistant_text", "") or ""
        urls = URL_RE.findall(msg)
        url_hint = urls[0] if urls else ""

    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path", "")
        if not path.lower().endswith(".pdf"):
            continue

        filename = os.path.basename(path)

        # Skip temp/download paths
        if any(path.lower().replace("\\", "/").startswith(p.lower()) for p in SKIP_PREFIXES):
            continue

        # Gate: is this a primary-source document?
        if not _is_primary_source(url_hint, filename):
            continue

        # Derive ticker and desc
        ticker = _derive_ticker(root, path)
        if not ticker:
            warn(f"pdf_auto_cache: cannot derive ticker for {filename}, skipping")
            continue

        desc = _derive_desc(filename)

        # Check if already cached (same ticker + desc pattern)
        cache_glob = os.path.join(root, "industry", "*", "companies", ticker,
                                   "_cache", f"{ticker}-{desc}.md")
        existing = list(glob.glob(cache_glob)) if hasattr(os, 'glob') else []
        if not existing:
            import glob as _glob
            existing = _glob.glob(cache_glob)
        if existing:
            # Already cached — still delete the redundant PDF
            try:
                os.remove(path)
                print(f"pdf_auto_cache: {filename} already cached, deleted redundant PDF", file=sys.stderr)
            except OSError:
                pass
            continue

        # Convert + cache + delete
        to_md = os.path.join(root, "_scripts", "shared", "to-markdown.py")
        if not os.path.exists(to_md):
            warn(f"pdf_auto_cache: to-markdown.py not found, skipping {filename}")
            continue

        try:
            r = subprocess.run(
                [sys.executable, to_md, path, "--cache", ticker, desc, "--rm", "--auto"],
                capture_output=True, text=True, timeout=120,
                cwd=root,
            )
            if r.returncode != 0:
                warn(f"pdf_auto_cache: conversion failed for {filename}: {r.stderr[:200]}")
            else:
                print(f"pdf_auto_cache: {filename} → {ticker}-{desc}.md", file=sys.stderr)
        except subprocess.TimeoutExpired:
            warn(f"pdf_auto_cache: timeout converting {filename} (>120s), PDF preserved")
        except Exception as e:
            warn(f"pdf_auto_cache: error processing {filename}: {e}")

    sys.exit(0)
```

- [ ] **Step 2: 注册 hook**

In `.claude/hooks/hooks.registry.yaml`, add after the `research_memory_gate` entry:

```yaml
  - name: pdf_auto_cache
    file: rules/pdf_auto_cache.py
    layer: governance
    events: [Stop]
    scope: [workspace_mutation]
    severity: warn
```

In `.claude/hooks/hook_entry.py`, add to STOP_RULES (after research_memory_gate):

```python
    "research_memory_gate",
    "pdf_auto_cache",
]
```

- [ ] **Step 3: 测试**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"

# Create a mock PDF with a primary-source filename
echo "mock pdf" > /tmp/test-fy2025-annual-report.pdf

# Simulate a Stop event with a Bash curl download
echo '{"cwd":"'$(pwd)'","tool_input":{"command":"curl -o /tmp/test-fy2025-annual-report.pdf https://ir.company.com/annual/fy2025.pdf","url":"https://ir.company.com/annual/fy2025.pdf"},"targets":[{"kind":"file","path":"/tmp/test-fy2025-annual-report.pdf","display":"test"}]}' | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"
```

Expected: pdf_auto_cache runs, tries to derive ticker, either converts or warns about unknown ticker. Does NOT block.

---

### Task 4: 文档更新——缓存优先规则

**Files:**
- Modify: `_shared/research-runtime.md` (workspace)
- Modify: `_shared/research-runtime.en.md` (workspace)
- Modify: `CLAUDE.md` (workspace live copy)

- [ ] **Step 1: 升级 research-runtime.md §2.1.1**

Read `_shared/research-runtime.md` around line 116-122. Replace the old §2.1.1 auto-cache text with the new hook-enforced version:

Old text (~lines 116-122):
```
#### 2.1.1 自动缓存

**规则**：任何研究 workflow 中下载的重要 PDF（年报、季报、招股书、监管 filing、卖方报告、会议 transcript），必须自动转成 markdown 缓存，原始 PDF 删除。

- **触发**：PDF 来自公司 IR 页面或官方渠道，且将被 artifact 引用（≥1 个 [S#] 指向它）
- **动作**：`to-markdown.py --cache <TICKER> <desc>` → `industry/<industry>/companies/<ticker>/_cache/<TICKER>-<desc>.md`
- **例外**：扫描件无法提取文本 → 保留 PDF，标 `[扫描件]`；legal filing 需保留原始排版 → 保留 PDF
```

Replace with:

```markdown
#### 2.1.1 PDF 自动缓存（Hook 强制）

**规则**：任何 Bash / browser 下载的 PDF，满足以下任一条件自动触发缓存：

- **A 轨**：来源 URL 匹配官方 IR / 监管 filing 渠道（SEC/HKEX/TDNET/DART/巨潮/MOPS 等多市场）
- **B 轨**：文件名含一手资料关键词（annual/quarterly/earnings/transcript/prospectus/10-K/20-F/招股/年报/季报/決算 等）

**动作**：Hook 自动调用 `to-markdown.py --cache <TICKER> <desc> --rm`：
1. 提取 ticker → 推导缓存路径
2. 转换为 markdown 并缓存到 `industry/<slug>/companies/<ticker>/_cache/<TICKER>-<desc>.md`
3. 删除原始 PDF
4. 转换失败（扫描件 text < 200 chars / 超时 120s）→ 保留 PDF + warn

**不需满足** artifact 引用条件——一手资料本身就是缓存理由。
```

- [ ] **Step 2: 新增 §2.1.2 缓存优先**

After the updated §2.1.1 block, add:

```markdown
#### 2.1.2 缓存优先

**规则**：下载任何外部文件前，必须先检查本地缓存。

| 文件类型 | 缓存位置 | 检查方式 |
|---|---|---|
| 公司披露 | `industry/<slug>/companies/<ticker>/_cache/` | `ls` / `grep` 文件名关键词 |
| 行业报告 | `industry/<slug>/_cache/` | `ls` / `grep` |
| 跨行业通用 | `_cache/` | `ls` / `grep` |

- ✅ 命中 → 直接 Read 本地缓存，source 写 `[S#](./_cache/<path>)`
- ❌ 未命中 → 上网下载。下载后 §2.1.1 hook 自动缓存一手资料
```

- [ ] **Step 3: 同步英文版 `research-runtime.en.md`**

Same changes in English. Translate inline.

- [ ] **Step 4: 更新 CLAUDE.md 工作区实时版**

In workspace `CLAUDE.md`, find the "来源验证规则" section (~line 248). After the "Canvas 文件" section and before the Research Memory section, add:

```markdown
### 缓存优先

下载外部文件前先检查本地缓存：
- 公司披露 → `industry/<slug>/companies/<ticker>/_cache/`
- 行业报告 → `industry/<slug>/_cache/`
- 命中直接用，未命中再上网。下载后 hook 自动缓存一手资料 PDF。
```

- [ ] **Step 5: 同步到 plugin repo CLAUDE.md.template（zh+en）**

Apply the same cache-first rule addition to:
- `c:/Users/M/Desktop/buy-side-research-skills-1.1.0/plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.md.template`
- `c:/Users/M/Desktop/buy-side-research-skills-1.1.0/plugins/buy-side-research-skills/skills/init-workspace/assets/CLAUDE.en.md.template`

---

### Task 5: 回退 source_contract hook

**Files:**
- Modify: `.claude/hooks/hook_entry.py`

- [ ] **Step 1: 恢复 source_contract**

Remove the `# -- temporarily disabled` comments and uncomment `"source_contract"`:

POST_TOOL_USE_RULES:
```python
    "source_contract",
```

STOP_RULES:
```python
    "source_contract",
```

- [ ] **Step 2: 验证**

```bash
echo '{"targets":[]}' | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"
```

Expected: Exit 0, no errors.

---

### Task 6: 同步到 plugin repo + workspace

- [ ] **Step 1: 复制新文件和修改到 plugin repo assets**

```bash
PLUGIN="c:/Users/M/Desktop/buy-side-research-skills-1.1.0/plugins/buy-side-research-skills/skills/init-workspace/assets"
WS="c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"

cp "$WS/.claude/hooks/rules/pdf_auto_cache.py" "$PLUGIN/.claude/hooks/rules/"
cp "$WS/.claude/hooks/common.py" "$PLUGIN/.claude/hooks/common.py"
cp "$WS/.claude/hooks/hooks.registry.yaml" "$PLUGIN/.claude/hooks/hooks.registry.yaml"
cp "$WS/.claude/hooks/hook_entry.py" "$PLUGIN/.claude/hooks/hook_entry.py"
cp "$WS/_scripts/shared/to-markdown.py" "$PLUGIN/_scripts/shared/to-markdown.py"
cp "$WS/_shared/research-runtime.md" "$PLUGIN/_shared/research-runtime.md"
cp "$WS/_shared/research-runtime.en.md" "$PLUGIN/_shared/research-runtime.en.md"
```

- [ ] **Step 2: Smoke test**

```bash
echo '{"targets":[]}' | python "$WS/.claude/hooks/hook_entry.py" --runtime claude --event Stop 2>&1
echo "Exit: $?"
ls "$WS/.claude/hooks/rules/pdf_auto_cache.py"
```

Expected: Exit 0, file exists.

---

## Post-Implementation Verification

```bash
# 1. pdf_auto_cache hook loads
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from rules import pdf_auto_cache; print('imports OK')"

# 2. common.py detects PDF paths
python -c "
import sys,json
sys.path.insert(0,'.claude/hooks')
from common import get_candidate_paths
payload = json.loads('{\"cwd\":\".\",\"tool_input\":{\"command\":\"curl -o test.pdf https://ir.company.com/annual/fy2025.pdf\"}}')
paths = get_candidate_paths(payload)
pdfs = [p for p in paths if p.endswith('.pdf')]
assert pdfs, 'FAIL: pdf not detected'
print(f'PASS: {len(pdfs)} pdf(s) detected')
"

# 3. to-markdown.py --rm flag works
python _scripts/shared/to-markdown.py --help 2>&1 | grep -q -- '--rm' && echo 'PASS: --rm flag' || echo 'FAIL: --rm flag missing'
python _scripts/shared/to-markdown.py --help 2>&1 | grep -q -- '--auto' && echo 'PASS: --auto flag' || echo 'FAIL: --auto flag missing'

# 4. Full hook pipeline (Stop event)
echo '{"targets":[]}' | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"
```
