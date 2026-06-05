# Cache 文件树 + 路径推导 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `_cache/` 从平铺升级为分层文件树（disclosure/sell-side/institution/primary/web/inbox），重写 `pdf_auto_cache.py` 的路径推导 + 元数据头部

**Architecture:** `_infer_source_type()` 从 URL+文件名推断类型 → `_resolve_cache_path()` 计算目标路径 → `to-markdown.py --metadata` 写入自描述头部 → `pdf_auto_cache.py` 三层推导 ticker/industry

**Tech Stack:** Python 3, regex, os.path

---

## File Structure

```
.claude/hooks/rules/pdf_auto_cache.py        # ✏️ 重写路径推导 (核心改动)
_scripts/shared/to-markdown.py                # ✏️ --metadata JSON 写入头部
_shared/research-runtime.md                   # ✏️ 更新缓存树说明
```

---

### Task 1: `_infer_source_type()` — URL + 文件名 → 类型+子目录

**Files:**
- Modify: `.claude/hooks/rules/pdf_auto_cache.py`

**Step 1: 新增 source type 推断逻辑**

在 `pdf_auto_cache.py` 的 `_PRIMARY_KEYWORDS` 之后添加：

```python
# ── Source type inference from URL patterns ──
_SOURCE_TYPE_URL = [
    (re.compile(r"/annual[-_]|/10-?[kK][/\.]|/20-?[fF][/\.]|annual.report|annual-report"), ("disclosure", "annual")),
    (re.compile(r"/quarterly[-_]|/10-?[qQ][/\.]|/earnings[-_]|q[1-4].*report|quarterly.report"), ("disclosure", "quarterly")),
    (re.compile(r"/transcript[s]?|/earnings.call|/決算説明会|/earnings-call"), ("disclosure", "transcript")),
    (re.compile(r"/prospectus|/s-?1[/\.]|/ipo|/招股"), ("disclosure", "prospectus")),
    (re.compile(r"/8-?k[/\.]|/6-?k[/\.]|/filing|/sec-filing"), ("disclosure", "filing")),
    (re.compile(r"ir\.|investor[s]?\.|/ir/|/investor[s]?/|/press|/newsroom|/pr/"), None),  # Generic IR — defer to filename
]

_SOURCE_TYPE_FILENAME = [
    (re.compile(r"annual|10-?[kK]|20-?[fF]|fy\d|fiscal.year|年報|有価証券報告書"), ("disclosure", "annual")),
    (re.compile(r"quarterly|10-?[qQ]|q[1-4]|interim|半年報|四半期|half.year"), ("disclosure", "quarterly")),
    (re.compile(r"transcript|earnings.call|earnings-call|決算説明|説明会|conference.call"), ("disclosure", "transcript")),
    (re.compile(r"prospectus|s-?1|ipo|招股|目論見書"), ("disclosure", "prospectus")),
    (re.compile(r"8-?k|6-?k|filing|sec.filing|form.8|form.6"), ("disclosure", "filing")),
    (re.compile(r"press.release|news|pr-|statement|発表"), ("disclosure", "press")),
]


def _infer_source_type(url: str, filename: str) -> tuple[str, str]:
    """Return (top_dir, sub_dir) for the cache file tree.
    
    Examples:
        ("disclosure", "annual")
        ("disclosure", "quarterly")
        ("inbox", "")
    """
    # 1. URL patterns first (more reliable)
    for pattern, result in _SOURCE_TYPE_URL:
        if pattern.search(url):
            if result is not None:
                return result
            else:
                break  # Generic IR — fall to filename

    # 2. Filename patterns
    for pattern, result in _SOURCE_TYPE_FILENAME:
        if pattern.search(filename, re.IGNORECASE):
            return result

    # 3. Default: inbox
    return ("inbox", "")
```

**Step 2: 验证**

```bash
cd "c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"
python -c "
import sys; sys.path.insert(0,'.claude/hooks')
from rules.pdf_auto_cache import _infer_source_type

# Test disclosure/annual
assert _infer_source_type('https://ir.company.com/annual/fy2025.pdf', 'fy2025-ar.pdf') == ('disclosure', 'annual')
# Test disclosure/quarterly
assert _infer_source_type('https://ir.company.com/quarterly/q1-2026.pdf', 'q1-2026-ir.pdf') == ('disclosure', 'quarterly')
# Test disclosure/transcript
assert _infer_source_type('https://ir.company.com/earnings/q4-call.pdf', 'earnings-call-transcript.pdf') == ('disclosure', 'transcript')
# Test fallback to inbox
assert _infer_source_type('https://random.com/doc.pdf', 'unknown-file.pdf') == ('inbox', '')
print('PASS: all assertions')
"
```

Expected: `PASS: all assertions`

---

### Task 2: `_resolve_cache_path()` — 计算完整缓存路径

**Files:**
- Modify: `.claude/hooks/rules/pdf_auto_cache.py`

**Step 1: 新增路径计算函数**

```python
def _find_industry(workspace: str, ticker: str) -> str | None:
    """Find industry slug for a ticker by scanning industry/*/companies/<ticker>/."""
    industry_dir = os.path.join(workspace, "industry")
    if not os.path.isdir(industry_dir):
        return None
    for ind in os.listdir(industry_dir):
        comp_dir = os.path.join(industry_dir, ind, "companies", ticker)
        if os.path.isdir(comp_dir):
            return ind
    return None


def _build_filename(source_type: tuple[str, str], url: str, filename: str) -> str:
    """Build a descriptive cache filename from source type and PDF metadata.
    
    Returns a clean .md filename (no extension — _resolve_cache_path adds .md).
    """
    top, sub = source_type
    name = os.path.splitext(os.path.basename(filename))[0]
    # Clean special chars
    name = re.sub(r'[^a-zA-Z0-9一-鿿_-]', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name[:80] if len(name) > 80 else name


def _resolve_cache_path(workspace: str, ticker: str | None, source_type: tuple[str, str],
                        url: str, pdf_path: str) -> str:
    """Compute the full cache path for a converted PDF.
    
    Returns the absolute path where the markdown should be cached.
    """
    top, sub = source_type
    base = os.path.join(workspace, "_cache")
    filename_stem = _build_filename(source_type, url, os.path.basename(pdf_path))
    filename = f"{filename_stem}.md"

    if top == "disclosure":
        # _cache/disclosure/<sub>/<filename>.md (under industry ticker dir)
        if ticker:
            ind = _find_industry(workspace, ticker)
            if ind:
                return os.path.join(workspace, "industry", ind, "companies", ticker,
                                    "_cache", top, sub, filename)
        # Fallback: workspace-level _cache
        os.makedirs(os.path.join(base, top, sub), exist_ok=True)
        return os.path.join(base, top, sub, filename)

    elif top in ("sell-side", "institution"):
        # _cache/<top>/<sub>/<filename>.md (workspace-level)
        os.makedirs(os.path.join(base, top, sub), exist_ok=True)
        return os.path.join(base, top, sub, filename)

    elif top == "primary":
        # _cache/primary/<sub>/<filename>.md
        os.makedirs(os.path.join(base, top, sub), exist_ok=True)
        return os.path.join(base, top, sub, filename)

    elif top == "web":
        # _cache/web/<filename>.md
        web_dir = os.path.join(workspace, "industry", _find_industry(workspace, ticker) or "",
                               "companies", ticker or "", "_cache", "web")
        if ticker and _find_industry(workspace, ticker):
            os.makedirs(web_dir, exist_ok=True)
            return os.path.join(web_dir, filename)
        os.makedirs(os.path.join(base, "web"), exist_ok=True)
        return os.path.join(base, "web", filename)

    else:  # inbox or unknown
        inbox_dir = os.path.join(base, "inbox")
        os.makedirs(inbox_dir, exist_ok=True)
        return os.path.join(inbox_dir, filename)
```

**Step 2: 验证**

```bash
python -c "
import os, sys; sys.path.insert(0,'.claude/hooks')
from rules.pdf_auto_cache import _resolve_cache_path, _infer_source_type

workspace = os.getcwd()
src = _infer_source_type('https://ir.company.com/annual/fy2025.pdf', 'fy2025-ar.pdf')
path = _resolve_cache_path(workspace, 'mycronic', src, 'https://ir.company.com/annual/fy2025.pdf', 'fy2025-ar.pdf')
print(f'Cache path: {path}')
assert 'industry' in path and 'mycronic' in path and 'disclosure' in path and 'annual' in path
assert path.endswith('.md')
print('PASS')
"
```

Expected: path includes `industry/.../companies/mycronic/_cache/disclosure/annual/fy2025-ar.md`

---

### Task 3: `to-markdown.py` — 元数据头部

**Files:**
- Modify: `_scripts/shared/to-markdown.py`

**Step 1: 替换 `_cache_header` 函数**

Replace the existing `_cache_header` function (line ~185):

```python
def _cache_header(source_url: str, source_type: str = "", pages: int = 0,
                  ticker: str = "", sha256: str = "") -> str:
    """Generate self-describing metadata header for cached markdown."""
    parts = [
        f"  source_url: {source_url}",
        f"  downloaded: {datetime.now().strftime('%Y-%m-%d')}",
        f"  converter: to-markdown.py",
    ]
    if source_type:
        parts.append(f"  source_type: {source_type}")
    if ticker:
        parts.append(f"  ticker: {ticker}")
    if pages:
        parts.append(f"  pages: {pages}")
    if sha256:
        parts.append(f"  sha256: {sha256}")
    return "<!--\n" + "\n".join(parts) + "\n-->\n\n"
```

**Step 2: 更新 `main()` 调用**

Find the `_cache_header(args.file, pages)` call in `main()` and update to pass new params:

```python
        source_type_str = f"{args.source_type_top}/{args.source_type_sub}" if hasattr(args, 'source_type_top') else ""
        header = _cache_header(
            source_url=args.file,
            source_type=source_type_str,
            pages=pages,
            ticker=ticker if args.cache else "",
        )
```

Add new CLI args for source_type:

```python
    p.add_argument("--source-type-top", help="Top-level cache dir (disclosure/sell-side/institution/primary/web/inbox)")
    p.add_argument("--source-type-sub", help="Sub-directory (annual/quarterly/transcript/etc or house/source name)")
```

**Step 3: 验证**

```bash
python -c "
from _scripts.shared.to_markdown import _cache_header
h = _cache_header('https://ir.company.com/annual/fy2025.pdf', source_type='disclosure/annual', pages=142, ticker='MYCR.ST')
print(h[:200])
assert 'source_url' in h and 'source_type' in h and 'ticker' in h and 'pages' in h
print('PASS')
"
```

---

### Task 4: 重连 `pdf_auto_cache.py` 的 `check()` 函数

**Files:**
- Modify: `.claude/hooks/rules/pdf_auto_cache.py` (check() function)

**Step 1: 替换 check() 中的路径构建逻辑**

Replace the `_derive_ticker` + `_derive_desc` + `_is_already_cached` calls with the new pipeline:

```python
def check(ctx):
    payload = ctx.get("raw_payload", {})
    root = ctx.get("cwd", "")
    ti = payload.get("tool_input") or payload.get("toolInput") or {}

    url_hint = ti.get("url", "") or ""
    if not url_hint:
        cmd = ti.get("command", "") or ""
        url_hint = _extract_url_from_bash(cmd)

    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path", "")
        if not path.lower().endswith(".pdf"):
            continue

        filename = os.path.basename(path)

        # Skip temp/download paths
        normalized_path = path.replace("\\", "/")
        if any(normalized_path.lower().startswith(p.lower().replace("\\", "/"))
               for p in _SKIP_PREFIXES):
            continue

        # Gate: is this a primary-source document?
        if not _is_primary_source(url_hint, filename):
            continue

        # ── New: source type inference ──
        source_type = _infer_source_type(url_hint, filename)
        top, sub = source_type

        # ── New: ticker derivation (layered) ──
        ticker = _derive_ticker(root, path)
        if not ticker and top == "disclosure":
            warn(f"pdf_auto_cache: cannot derive ticker for {filename}, caching to inbox")
            source_type = ("inbox", "")
            ticker = None

        # ── New: resolve cache path ──
        cache_path = _resolve_cache_path(root, ticker, source_type, url_hint, path)

        # Dedup check
        if os.path.exists(cache_path):
            try:
                os.remove(path)
                print(f"pdf_auto_cache: {filename} already cached at {cache_path}, deleted redundant PDF",
                      file=sys.stderr)
            except OSError:
                pass
            continue

        # Convert + cache + delete
        to_md = os.path.join(root, "_scripts", "shared", "to-markdown.py")
        if not os.path.exists(to_md):
            warn(f"pdf_auto_cache: to-markdown.py not found, skipping {filename}")
            continue

        # Build args with source type metadata
        cmd = [sys.executable, to_md, path, "--cache", ticker or "inbox",
               _build_filename(source_type, url_hint, filename),
               "--source-type-top", top, "--source-type-sub", sub,
               "--rm", "--auto"]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=root)
            if r.returncode != 0:
                warn(f"pdf_auto_cache: conversion failed for {filename}: {r.stderr[:200]}")
            elif r.stderr:
                for line in r.stderr.strip().split("\n"):
                    if line.strip():
                        print(f"pdf_auto_cache: {line.strip()}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            warn(f"pdf_auto_cache: timeout converting {filename} (>120s), PDF preserved")
        except Exception as e:
            warn(f"pdf_auto_cache: error processing {filename}: {e}")

    sys.exit(0)
```

**Step 2: 移除旧函数**

Delete the old `_derive_ticker`, `_derive_desc`, `_is_already_cached` functions (replaced by `_resolve_cache_path` + `_find_industry` + `_build_filename`).

**Step 3: 验证**

```bash
echo "mock pdf" > /tmp/test-fy2025-annual-report.pdf
echo "{\"cwd\":\"$(pwd)\",\"tool_input\":{\"command\":\"curl -o /tmp/test-fy2025-annual-report.pdf https://ir.company.com/annual/fy2025.pdf\",\"url\":\"https://ir.company.com/annual/fy2025.pdf\"},\"targets\":[{\"kind\":\"file\",\"path\":\"/tmp/test-fy2025-annual-report.pdf\",\"display\":\"test\"}]}" | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"
```

Expected: Exit 0, no errors. /tmp path skipped with warning.

---

### Task 5: 文档更新

**Files:**
- Modify: `_shared/research-runtime.md` §2.1.1

**Step 1: 更新缓存文件树说明**

Replace the §2.1.1 action block's cache path mention with the new tree structure:

```markdown
**缓存路径**（按来源类型分层）：

| 类型 | 路径 | 命名 |
|---|---|---|
| 年报/10-K | `_cache/disclosure/annual/` | `FY<year>-<desc>.md` |
| 季报/10-Q | `_cache/disclosure/quarterly/` | `<year>-Q<n>-<desc>.md` |
| Transcript | `_cache/disclosure/transcript/` | `<year>-Q<n>-earnings-call.md` |
| 招股书/S-1 | `_cache/disclosure/prospectus/` | `<year>-IPO-<desc>.md` |
| 其他 filing | `_cache/disclosure/filing/` | `<date>-<form-type>.md` |
| 卖方报告 | `_cache/sell-side/<house>/` | `<house>-<date>-<ticker>-<note>.md` |
| 行业机构 | `_cache/institution/<source>/` | `<source>-<date>-<topic>.md` |
| 一手调研 | `_cache/primary/<type>/` | `<date>-<company>-<type>.md` |
| 网页快照 | `_cache/web/` | `<date>-<slug>.md` |
| 未分类 | `_cache/inbox/` | 兜底 |

每个缓存文件头部包含自描述元数据（`<!-- source_url / source_type / ticker / pages / sha256 -->`）。
```

**Step 2: 同步 plugin repo**

```bash
cp _shared/research-runtime.md <plugin-assets>/_shared/research-runtime.md
```

---

### Task 6: 同步 plugin repo + 验证

**Step 1: 复制所有修改到 plugin repo**

```bash
PLUGIN="c:/Users/M/Desktop/buy-side-research-skills-1.1.0/plugins/buy-side-research-skills/skills/init-workspace/assets"
WS="c:/Users/M/Desktop/Hel Ved/Markdown/CC research workspace"

cp "$WS/.claude/hooks/rules/pdf_auto_cache.py" "$PLUGIN/.claude/hooks/rules/"
cp "$WS/_scripts/shared/to-markdown.py" "$PLUGIN/_scripts/shared/"
cp "$WS/_shared/research-runtime.md" "$PLUGIN/_shared/"
```

**Step 2: 完整管线烟雾测试**

```bash
echo '{"targets":[]}' | python .claude/hooks/hook_entry.py --runtime claude --event Stop 2>&1
echo "Exit: $?"
python -c "import sys; sys.path.insert(0,'.claude/hooks'); from rules.pdf_auto_cache import _infer_source_type, _resolve_cache_path, _find_industry; print('All functions import OK')"
```

Expected: Exit 0, all imports OK.
