---
name: integrate
description: Use when merging a child topic into a parent topic (e.g. merging a company topic into its industry topic after research).
---

# Integrate

把已经研究的子 topic（如某家公司）合并到父 topic（如所属行业）下面，形成 `topics/<parent>/<child>/` 层级结构，并更新双向 index.md 引用。

它是 operations skill。不写研究结论，不做跨 topic 分析。

## 心法

研究容易"散"：先研究行业，再研究行业里的公司，两个 topic 独立但逻辑上是父子关系。`integrate` 把这个关系落到目录结构上，让后续研究自然发现父 topic 的行业 cache + 子 topic 的公司 cache。

## 职责边界

负责：
- 将 child topic 整个目录移入 parent topic 下
- 更新 parent `index.md` 的 Sub-topics / Related topics 段落
- 更新 child `index.md` 记录 parent 引用
- 报告 merge summary

不负责：
- 不写研究结论
- 不修改 child 内部的 session 内容
- 不删除或合并 index.md
- 不做跨 topic 分析或比较

## 触发与输入

触发短语：
- "merge ge-aerospace into aerospace"
- "把 GE 的研究合并到 aerospace 下面"
- "integrate these two topics"
- "合并这两个 topic"

输入要求：

| 输入 | 用途 |
|---|---|
| `parent_slug` | 父 topic slug（如 `aerospace`） |
| `child_slug` | 子 topic slug（如 `ge-aerospace`） |
| `workspace_path` | research workspace 根目录 |

## 执行模式

### Merge

1. 验证 parent 存在：`topics/<parent>/index.md`
2. 验证 child 存在：`topics/<child>/index.md`
3. 检查冲突：`topics/<parent>/<child>/` 是否已存在
4. 执行移动：`topics/<child>/` → `topics/<parent>/<child>/`
5. 更新 parent `index.md`：追加 `## Sub-topics` 段落，链接到 child
6. 更新 child `index.md`：追加 `**Parent topic**: [parent]` 引用
7. 输出 merge summary

## 运行输出契约

```markdown
## Integrate Result

**结论先行**
已将 `topics/<child>/` 合并至 `topics/<parent>/<child>/`

## Moved
- `topics/<child>/` → `topics/<parent>/<child>/`
  - _raw files: N
  - _cache files: N
  - sessions: N

## Index Updated
- parent: `topics/<parent>/index.md` (+sub-topic link)
- child: `topics/<parent>/<child>/index.md` (+parent reference)
```

## 工具资源

- 使用文件系统检查确认 parent / child topic 是否存在。
- 使用安全移动操作把 child topic 移入 parent topic 下。
- 使用文本编辑更新 parent 和 child 的 `index.md` 链接。
- 不依赖外部网络、模型、数据库或 research source。

## 文件安全

- 不删除 child 原路径（是移动，不是复制后删除）
- 冲突时（child 目录名已在 parent 下存在）→ block 并提示手动处理
- 不修改 child 内部的 session artifact 内容
- parent 或 child 不存在 → block 并提示先创建 topic

## 失败处理

- parent 不存在：block，提示先 `new-session` 创建父 topic
- child 不存在：block，提示确认 child slug
- 冲突：block，提示已有同名子目录，需手动处理
- 不同行业合并：提示用户确认（如 `aerospace` 下合并 `semiconductor` 公司）

## Workflow 联动

| 场景 | 处理 |
|---|---|
| 先研究行业，再研究公司，想把公司归入行业 | `integrate` |
| 两个独立 topic 有交叉但不想合并 | 在 `index.md` 互相加 Related topics 链接即可，不用 integrate |
| 三个以上 topic 合并 | 逐个 integrate（先合两个，再合第三个） |

Artifact policy：
- `save_policy`: `none`
- `default_artifact`: `conversation-only`（只做文件系统操作）
- `canonical_location`: `conversation-only`

## 安全自查

- ❌ 写研究结论
- ❌ 删除原 child 目录（只移动）
- ❌ 覆盖已有 `index.md`
- ❌ 合并不同行业的 topic 不提示确认
