# PDF Auto-Cache Hook + 缓存优先 设计

> 状态: draft
> 日期: 2026-06-05
> 关联: research-runtime.md §2.1.1, to-markdown.py, hook infrastructure

---

## 1. 问题

当前 §2.1.1 定义的 PDF→markdown 缓存规则是 agent 自律执行的——需要 agent 手动调用 `to-markdown.py --cache`。重要一手资料（年报、季报、call transcript、招股书）的缓存率依赖 agent 是否记得这条规则。

而且规则有一个过度限制："将被 artifact 引用（≥1 个 [S#] 指向它）"——对于一手资料，就算暂时不引用也应该缓存，因为它是后续所有研究的基础。

另外，agent 经常跳过热身步骤直接上网搜，没有先检查本地 `_cache/` 是否已有相关文件。

## 2. 目标

### 2.1 PDF 自动缓存 Hook

- Hook 拦截所有 Bash / browser 下载的 PDF
- 判断是否"重要一手资料"——URL 模式（多市场监管 filing）OR 文件名关键词
- 自动调用 `to-markdown.py` 转 markdown 缓存到对应公司/行业 `_cache/`
- 转换成功 → 删除原始 PDF
- 转换失败（扫描件 text < 200 chars）→ 保留 PDF + warn
- **不需要** artifact 引用条件——一手资料本身就是缓存理由

### 2.2 缓存优先规则

- Agent 在下载/搜索外部文件前，必须先检查本地 `_cache/` 目录
- 命中 → 直接用本地缓存，source 写本地路径
- 未命中 → 上网，下载后自动触发 §2.1 hook 缓存

## 3. 设计原则

- **Hook 强制，不依赖 agent 自律**：PDF 下载事件在 Stop/PostToolUse 阶段被 hook 拦截
- **复用 to-markdown.py**：不重复造转换轮子，只加 `--rm` 参数
- **宽进严出**：URL 或文件名任一命中即触发，但转换失败时不删 PDF
- **不阻塞研究流程**：hook 只在 Stop 时做转换，转换失败只 warn

## 4. 检测面

### 4.1 Bash 命令

`get_candidate_paths()` 扩展 `.pdf` 检测：

```python
# Redirections: > file.pdf
for m in re.finditer(r'(?:>|>>)\s*["\']?([^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):
    ...

# Absolute paths
for m in re.finditer(r'["\']?([A-Z]:\\[^"\'\s]+\.(?:md|html|xlsx|pdf))', cmd):
    ...

# Python/script write paths
for m in re.finditer(r'''(?:r)?["']([^"'\n]+?\.(?:md|html|xlsx|pdf))["']''', cmd):
    ...
```

### 4.2 Playwright MCP browser_download

`get_candidate_paths()` 增加 `download_path` / `suggestedFilename` 字段检测。

## 5. 判断逻辑

### 5.1 A 轨——URL 模式匹配（多市场）

检测 PDF 的来源 URL（取自 tool input 的 `url` 字段、Bash 命令中的 URL、browser_download 的来源 URL）：

```python
PRIMARY_SOURCE_URLS = [
    # 公司 IR 通用
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

    # 通用 filing / disclosure 路径
    r"/annual[-_]", r"/quarterly[-_]", r"/earnings[-_]",
    r"/transcript[s]?", r"/prospectus",
    r"/s-?1[/\.]", r"/10-?[kq][/\.]", r"/20-?f[/\.]",
    r"/8-?k[/\.]", r"/6-?k[/\.]",
]
```

### 5.2 B 轨——文件名关键词

```python
PRIMARY_KEYWORDS = [
    "annual", "quarterly", "earnings", "transcript",
    "prospectus", "filing", "ir-", "fy", "1q", "2q", "3q", "4q",
    "10-k", "10-q", "20-f", "8-k", "6-k", "s-1", "s1",
    "招股", "年报", "季报", "半年报", "中期报告",
    "決算", "有価証券報告書", "四半期",
]
```

### 5.3 组合规则

```python
def is_primary_source(url: str | None, filename: str) -> bool:
    if url and any(re.search(p, url, re.IGNORECASE) for p in PRIMARY_SOURCE_URLS):
        return True
    if any(kw in filename.lower() for kw in PRIMARY_KEYWORDS):
        return True
    return False
```

## 6. 动作链

```
Stop hook → pdf_auto_cache.check(ctx)
  for each target in ctx.targets (that is a .pdf file):
    1. Extract source URL from tool_input / Bash command
    2. is_primary_source(url, filename) → False → skip
    3. derive ticker from PDF path (search industry/*/companies/<ticker>/)
       → fail: log warning, skip (can't determine ticker)
    4. derive desc from filename (e.g. "FY2025-annual-report" → "fy2025-ar")
    5. Check _cache/ for existing: same ticker-desc pattern → skip (already cached)
    6. Run: to-markdown.py <pdf> --cache <TICKER> <desc> --rm
       → success: pdf deleted, markdown cached, print to stderr
       → pdf-extract text < 200 chars: warn + keep PDF (scanned)
       → pdf-extract crash: warn + keep PDF
```

### to-markdown.py 新增参数

```python
p.add_argument("--rm", action="store_true",
               help="Delete source PDF after successful cache")
p.add_argument("--auto", action="store_true",
               help="Silent mode: suppress stdout, only stderr for logs")
```

`--rm` 逻辑（在 `main()` 中 `--cache` 块后）：
```python
if args.rm and args.cache:
    try:
        os.remove(args.file)
        print(f"  Deleted: {args.file}", file=sys.stderr)
    except OSError as e:
        print(f"  WARN: could not delete {args.file}: {e}", file=sys.stderr)
```

## 7. 不触发场景

| 场景 | 行为 |
|---|---|
| PDF 在 `/tmp/` 或 `~/Downloads/` | 跳过——无法确定 ticker |
| PDF 已在 `_cache/` 中（相同 ticker + desc） | 跳过——已缓存 |
| 非一手来源（第三方报告、新闻截图） | 跳过——不匹配 URL 也不匹配关键词 |
| 扫描件 text < 200 chars | warn + 保留 PDF，标 `[扫描件-未转换]` |
| pdf-extract 崩溃 | warn + 保留 PDF，标 `[转换失败]` |
| ticker 推导失败 | warn + 跳过 |

## 8. 边界与其他系统

| 系统 | 关系 |
|---|---|
| evidence ledger | 缓存后的 markdown 可作为 evidence source。不抢 evidence ledger 的验证职能 |
| pre_write_gate | 不影响——pre_write_gate 仍然检查 artifact 引用完整性 |
| to-markdown.py | 新增 `--rm` + `--auto` flag —— 向后兼容，现有调用不受影响 |
| pdf-extract.py | 复用——不修改。通过 exit code 判断扫描件 |
| research_memory_gate | 互补——PDF 缓存后自动进入 Source 地图的本地缓存列 |

## 9. 缓存优先规则

改三个文件：

### 9.1 `_shared/research-runtime.md` §2.1.2（新增）

```markdown
#### 2.1.2 缓存优先

**规则**：下载任何外部文件前，必须先检查本地缓存。

| 文件类型 | 缓存位置 | 检查方式 |
|---|---|---|
| 公司披露 | `industry/<slug>/companies/<ticker>/_cache/` | grep / ls 文件名关键词 |
| 行业报告 | `industry/<slug>/_cache/` | grep / ls 文件名关键词 |
| 跨行业 | `_cache/` | grep / ls |

- ✅ 命中 → 直接 Read 本地缓存，source 写 `[S#](./_cache/<path>)`
- ❌ 未命中 → 上网下载。下载后 §2.1.1 hook 自动缓存
```

### 9.2 `CLAUDE.md.template`（§5.5 追加）

```markdown
### 缓存优先

下载外部文件前先检查本地缓存：
- 公司披露 → `industry/<slug>/companies/<ticker>/_cache/`
- 行业报告 → `industry/<slug>/_cache/`
- 命中直接用，未命中再上网。下载后 hook 自动缓存一手资料 PDF。
```

### 9.3 `research-runtime.en.md` + `CLAUDE.en.md.template`（英文同步）

## 10. 实现依赖

| 文件 | 动作 | 类型 |
|---|---|---|
| `.claude/hooks/rules/pdf_auto_cache.py` | 🆕 Hook 主逻辑 | 核心 |
| `.claude/hooks/common.py` | ✏️ `get_candidate_paths()` 扩展 `.pdf` | 核心 |
| `.claude/hooks/hooks.registry.yaml` | ✏️ 注册 `pdf_auto_cache` hook | 配线 |
| `.claude/hooks/hook_entry.py` | ✏️ STOP_RULES 加 `pdf_auto_cache` | 配线 |
| `_scripts/shared/to-markdown.py` | ✏️ 加 `--rm` + `--auto` flag | 核心 |
| `_shared/research-runtime.md` | ✏️ 升级 §2.1.1 + 新增 §2.1.2 | 文档 |
| `_shared/research-runtime.en.md` | ✏️ 英文同步 | 文档 |
| `plugins/.../CLAUDE.md.template` | ✏️ 加缓存优先规则 | 文档 |
| `plugins/.../CLAUDE.en.md.template` | ✏️ 英文同步 | 文档 |

## 11. 非目标

- ❌ 不做异步队列——Stop hook 里同步执行，大 PDF 转换超时 120s（subprocess timeout 已有）
- ❌ 不做 PDF 质量审核——一手资料标记由 URL/文件名规则判断，不做内容 NLP
- ❌ 不拦截非 PDF 文件——docx/pptx/xlsx 不走这条 hook
- ❌ 不处理 agent 主动 curl 到 `/dev/null` 的场景——只检测写盘操作
