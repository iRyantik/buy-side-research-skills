# Cache 文件树 + PDF 路径推导 设计

> 状态: draft
> 日期: 2026-06-05
> 关联: pdf_auto_cache.py, to-markdown.py, _cache/

---

## 1. 问题

当前 `_cache/` 平铺一层，文件一多不可维护。`pdf_auto_cache.py` 的 `_derive_ticker` 依赖文件名模糊匹配，不可靠。需要：
- 明确的分层缓存文件树
- 可靠的 ticker + industry + source_type 推导逻辑

## 2. 目标

`_cache/` 按来源类型分层，所有缓存文件为 markdown（PDF 转换后删除）。元数据自描述在 md 头部。

## 3. 文件树

```
_cache/
├── disclosure/                    # 公司一手披露
│   ├── annual/                    # 年报 / 10-K / 20-F / 有価証券報告書
│   ├── quarterly/                 # 季报 / 10-Q / IR presentation
│   ├── transcript/                # Earnings call / 説明会 / 決算説明会
│   ├── prospectus/                # 招股书 / S-1 / IPO
│   ├── filing/                    # 其他监管 filing（8-K / 6-K / HKEX公告）
│   └── press/                     # 公司新闻稿
├── sell-side/                     # 券商研究所，按 house 分
│   ├── <house>/                   # Morgan-Stanley / Goldman / 中金 ...
│   │   └── *.md
│   └── ...
├── institution/                   # 行业机构（TrendForce/IDC/协会/咨询）
│   ├── <source>/                  # TrendForce / IDC / Gartner / 行业协会
│   │   └── *.md
│   └── ...
├── primary/                       # 一手调研
│   ├── expert-call/               # 专家 call
│   ├── channel-check/             # 渠道调研
│   └── management-call/           # 管理层交流
├── financial-data/                # 结构化财务（已有，不动）
├── evidence/                      # evidence ledger（已有，不动）
├── images/                        # Logo / 产品图（已有，不动）
├── web/                           # 网页快照（web-extract.py 产出）
└── inbox/                         # 未分类临时文件（兜底）
```

## 4. 命名规则

### disclosure/

```
FY<year>-<type>.md              例: FY2025-ar.md
<year>-Q<n>-<type>.md           例: 2026-Q1-ir.md
<year>-Q<n>-earnings-call.md    例: 2026-Q1-earnings-call.md
<year>-IPO-prospectus.md        例: 2025-IPO-prospectus.md
<date>-<form-type>.md           例: 2026-06-05-8-K.md
```

### sell-side/

```
<house>-<date>-<ticker>-<note>.md
例: Morgan-Stanley-2026-03-Mycronic-initiation.md
```

### institution/

```
<source>-<date>-<topic>.md
例: TrendForce-2026-Q2-coupe-snapshot.md
```

### primary/

```
<date>-<company>-<type>.md
例: 2026-06-05-BESI-IR-call.md
```

### web/ + inbox/

```
<date>-<slug>.md                例: 2026-06-05-ir-mycronic-guidance.md
```

## 5. 元数据头部

每个缓存 markdown 文件头带 HTML comment 元数据块：

```markdown
<!--
  source_url: https://ir.company.com/annual/fy2025.pdf
  source_type: disclosure/annual
  downloaded: 2026-06-05
  converter: to-markdown.py
  ticker: MYCR.ST
  pages: 142
  sha256: a1b2c3...
-->
# FY2025 Annual Report — Mycronic
```

`source_type` 值 = `{top}/{sub}` 映射到文件树：
- `disclosure/annual`
- `disclosure/quarterly`
- `disclosure/transcript`
- `disclosure/prospectus`
- `disclosure/filing`
- `disclosure/press`
- `sell-side/<house>`
- `institution/<source>`
- `primary/expert-call`
- `primary/channel-check`
- `primary/management-call`
- `web`
- `inbox`

## 6. 路径推导逻辑

`pdf_auto_cache.py` 推导顺序：

### Layer 1: URL → source_type + ticker

从下载 URL 提取信息：

| URL 模式 | 提取 |
|---|---|
| `ir.<company>.com` / `investor.<company>.com` | host → ticker |
| `sec.gov/...?CIK=xxx` | CIK → ticker（需要 CIK→ticker mapping） |
| `dart.fss.or.kr/...` | corpCode → ticker |
| `hkexnews.hk/...?stock=xxx` | stock code → ticker |
| URL path contains `/annual/` / `/10-k/` / `/10-k/` | source_type = disclosure/annual |
| URL path contains `/quarterly/` / `/10-q/` | source_type = disclosure/quarterly |
| URL path contains `/transcript/` / `/earnings/` | source_type = disclosure/transcript |
| URL path contains `/prospectus/` / `/s-1/` / `/s1/` | source_type = disclosure/prospectus |
| URL host matches known sell-side domain | source_type = sell-side |
| URL host matches known institution domain | source_type = institution |

### Layer 2: 文件名 → 补充信息

```
文件名含 "annual" / "fy" / "10-k" / "20-f"     → disclosure/annual
文件名含 "q1" / "2q" / "quarterly" / "10-q"     → disclosure/quarterly
文件名含 "transcript" / "earnings" / "call"     → disclosure/transcript
文件名含 "prospectus" / "s-1" / "s1" / "ipo"   → disclosure/prospectus
文件名含 "8-k" / "6-k" / "filing"               → disclosure/filing
```

### Layer 3: ticker → industry slug

```python
def _find_industry(workspace: str, ticker: str) -> str | None:
    for ind in os.listdir(f"{workspace}/industry"):
        comp_dir = f"{workspace}/industry/{ind}/companies/{ticker}"
        if os.path.isdir(comp_dir):
            return ind
    return None
```

### Layer 4: 兜底

前三层失败 → `_cache/inbox/<date>-<slug>.md`，保留 PDF。

## 7. 去重

同目录下同名 `.md` 已存在 → 跳过转换，直接删重复 PDF（不重复缓存）。

## 8. 与现有系统关系

| 系统 | 关系 |
|---|---|
| evidence ledger | `source_url` 元数据可直接引用为 evidence source |
| RESEARCH.md §1 Source 地图 | 本地缓存列指向 `_cache/<type>/<file>.md` |
| generate-memory-cards.py | 不扫 `_cache/`——只扫 RESEARCH.md |
| `_cache/financial-data/` | 不抢 financial-data 的 `internal/` 目录 |
| `_cache/images/` | 不抢 download-image.py 的图片缓存 |

## 9. 实现依赖

| 文件 | 动作 |
|---|---|
| `pdf_auto_cache.py` | 重写 `_derive_ticker` + 新增 `_resolve_cache_path` + `_infer_source_type` |
| `_shared/research-runtime.md` | §2.1.1 更新缓存文件树说明 |
| CLAUDE.md | §5.5 更新缓存路径文档 |

## 10. 非目标

- 不做 CIK→ticker 映射表（第一版用 ticker 名称匹配兜底，后续补充）
- 不做 house/source 自动识别（sell-side 和 institution 第一版走 inbox 兜底，agent 手动整理）
- 不迁移已有 `_cache/` 文件（存量不管，增量按新树）
