# Financial-Data Cache 目录收口

> 状态: spec
> 日期: 2026-06-08
> 版本: v5.13.13

## 1. 目标

消灭 `_raw/`、`_cache/datasets/`、`_cache/financial-data/internal/` 三层之间的重复文件写入。统一为两层：`_raw/`（不可复现证据）+ `_cache/`（可复现衍生品 + 消费入口）。

## 2. 新文件树

```
<company>/
├── _raw/
│   └── financial-data/
│       └── <market>/<id>/<run_id>/
│           ├── provider_payload.json
│           ├── identity-source.json
│           └── filings/
│               └── <filing_id>/
│                   ├── source.html|pdf|xml
│                   ├── source-metadata.json
│                   └── source.sha256
│
└── _cache/
    └── financial-data/
        │
        ├── <market>/<id>/<run_id>/        ← 版本化 run 输出
        │   ├── manifest.json
        │   ├── identity.json
        │   ├── financials.normalized.json
        │   ├── financials.md
        │   ├── completeness.json
        │   ├── source-map.json
        │   ├── cross-check.json
        │   ├── filing-index.json
        │   ├── full-filing.chunks.jsonl
        │   └── full-filing.index.json
        │
        ├── actuals-resolved.json           ← 最新 run 的结构化数据
        ├── evidence-pack.json              ← 最新 run 聚合指针
        ├── full-filing.md                  ← 最新 run 全文
        └── summary.md                      ← 人类入口
```

## 3. 变化对照

| 现状 | 新 | 原因 |
|---|---|---|
| `_raw/datasets/financial-data/` | `_raw/financial-data/` | 去掉无意义的 `datasets/` 中间层 |
| `_cache/datasets/financial-data/` | `_cache/financial-data/<run_id>/` | 同上，run-id 目录平铺在 skill 名下 |
| `_cache/financial-data/internal/` (14文件) | `_cache/financial-data/` (4文件平铺) | 去掉 `internal/` 子目录，只有4个独有文件 |
| `internal/_raw/` copytree | 不存在 | copytree 是什么鬼 |
| `internal/manifest.json` 等12个副本 | 不存在 | 都在 run-id 目录里，不需要复制 |
| `internal/raw-evidence.json` | 不存在 | `evidence-pack.json` 里已有同样字段 |
| `internal/full-filing.md` | `_cache/financial-data/full-filing.md` | 提到顶层 |
| `financial-data-summary.md` | `summary.md` | 更短，在自家目录下不需要前缀 |

## 4. 代码改动

### 4.1 `write_canonical_pack()`（行 1096-1184）

```python
# 行 1101-1103: 路径变更
# 旧:
rel_tail = Path("datasets") / "financial-data" / args.market / canonical_id / rid
raw_dir = topic_path / "_raw" / rel_tail
cache_dir = topic_path / "_cache" / rel_tail
# → _raw/datasets/financial-data/... , _cache/datasets/financial-data/...

# 新:
rel_tail = Path("financial-data") / args.market / canonical_id / rid
raw_dir = topic_path / "_raw" / rel_tail
cache_dir = topic_path / "_cache" / rel_tail
# → _raw/financial-data/... , _cache/financial-data/...

# 行 1132-1143: full-filing.md 改为只在顶层写，run-id 目录只留 chunks+index
# 删掉 write_md(cache_dir / "full-filing.md", filing_md)
# 只保留 chunks.jsonl + index.json

# 行 1179-1184: 返回值
# 旧:
return {
    ...
    "financial_data_summary_path": str(topic_path / "_cache" / "financial-data" / "financial-data-summary.md"),
    "financial_data_internal_path": str(topic_path / "_cache" / "financial-data" / "internal"),
}
# 新:
return {
    ...
    "financial_data_summary_path": str(topic_path / "_cache" / "financial-data" / "summary.md"),
    "financial_data_internal_path": str(topic_path / "_cache" / "financial-data"),
}
```

### 4.2 `write_modeling_input_aliases()`（行 1187-1293）

重命名为 `write_consumer_outputs()`，逻辑简化为只写 4 个顶层文件：

```python
def write_consumer_outputs(topic_path, cache_dir, raw_dir, manifest, identity,
                           filing, filing_md, financials, completeness, 
                           source_map, cross_check):
    out_dir = topic_path / "_cache" / "financial-data"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. evidence-pack.json（聚合指针）
    write_json(out_dir / "evidence-pack.json", {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "latest_run_cache_path": str(cache_dir),
        "latest_raw_evidence_path": str(raw_dir),
        "manifest": manifest,
        "identity": identity,
        "filing": { ... },           # filing 摘要
        "completeness": completeness,
        "source_map": source_map,
        "cross_check": cross_check,
    })

    # 2. actuals-resolved.json（consumer 唯一读的）
    write_json(out_dir / "actuals-resolved.json", { ... })

    # 3. full-filing.md（全文，提到顶层）
    if filing_md:
        write_md(out_dir / "full-filing.md", filing_md)

    # 4. summary.md（人类入口）
    write_md(out_dir / "summary.md", 
             build_financial_data_summary(evidence_pack, actuals_resolved, out_dir))

    # 清理旧 internal/ 目录的 legacy 文件
    _clean_legacy_internal(out_dir)
```

**删掉的代码**：
- 行 1249-1256: 12 个重复文件写入
- 行 1260-1266: `shutil.copytree(raw_dir, alias_raw_dir)`
- 行 1268-1282: 重复的 filing 文件写入

### 4.3 `main()` yfinance auto-fill（行 1460-1500）

```python
# 行 1464: 路径适配
# 旧:
internal_dir = output.get("financial_data_internal_path", "")
# → .../_cache/financial-data/internal
actuals_path = Path(internal_dir) / "actuals-resolved.json"

# 新:
data_dir = output.get("financial_data_internal_path", "")
# → .../_cache/financial-data
actuals_path = Path(data_dir) / "actuals-resolved.json"
```

### 4.4 `build_financial_data_summary()`（行 857+）

```python
# 摘要里引用路径更新：
# "Internal machine data: `internal/`" → "Machine data: `_cache/financial-data/`"
# "Full filing retained internally: ..." → "Full filing: `full-filing.md`"
```

## 5. 文件变更清单

| 文件 | 改动 |
|---|---|
| `financial_data.py` | `write_canonical_pack()` 路径变更、`write_modeling_input_aliases()` → `write_consumer_outputs()` 精简、`main()` 路径适配、`build_financial_data_summary()` 文案更新 |
| `SKILL.md` | §1 输出结构表对齐新树、consumer contract 路径更新、`internal/` 引用全部改为 `_cache/financial-data/` |
| `SKILL.en.md` | 同上英文 |
| `stock-quickread/SKILL.md` | `actuals-resolved.json` 路径从 `_cache/financial-data/internal/` → `_cache/financial-data/` |
| `comps-analysis/SKILL.md` | 同上 |

## 6. 不做

- 不删除已有 workspace 里的旧目录（`internal/`、`_raw/datasets/`）——用户自己清理
- 不迁移旧 run 数据到新结构——新 run 用新结构即可
- 不改 `write_snapshot()` ——它路径独立且简单
- 不改 `_cache/images/` ——和本次无关
