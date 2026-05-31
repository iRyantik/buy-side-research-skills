with open('plugins/buy-side-research-skills/skills/driver-map/SKILL.md', 'r', encoding='utf-8') as f:
    text = f.read()

changes = []

# 1. 心法加例子
old_xinfa = "`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。"
new_xinfa = """`driver-map` 的工作是把披露口径拆成业务实质，再把业务实质压缩成少数可验证、可跟踪、可建模的 driver。

举个例子：公司披露叫 "Industrial Solutions"，实际是燃气轮机设备+长期服务捆在一起。坏的分析写 "Industrial Solutions 收入 $3.2bn"——那是复读财报。好的分析拆出来：设备销售 $1.3bn 毛利率 22%、服务 $1.9bn 毛利率 45%，服务装机利用率是核心 driver。这才是 `driver-map` 的价值。"""
text = text.replace(old_xinfa, new_xinfa)
changes.append('1. 心法+例子')

# 2. §1 产品图 — add after Reported Bucket table header
old_fig = '| Reported bucket | Business reality | End-market / customer | Ev | Gap |\n|---|---|---|---|---|'
new_fig = '| Reported bucket | Business reality | End-market / customer | Ev | Gap |\n|---|---|---|---|---|\n| [segment] | [实际卖什么 / 做什么] | [客户或应用] | [S1](url) | [缺口] |\n\n> 每个核心 segment 配产品/设备图：下载到当前 topic 的 `_cache/images/<slug>-<product>.png`——① 公司 Media Kit → ② web search 产品图 → ③ 找不到用行业代表图 → ④ 标 [缺图]。'
text = text.replace(old_fig, new_fig)
changes.append('2. §1+产品图')

# 3. Driver Library 列表→表
old_lib = """常用 driver library：
- **Volume**：unit shipment、capacity、MTPA、MW、rig count、installed base、customer count。
- **Price**：ASP、contract escalation、commodity pass-through、pricing index。
- **Mix**：equipment vs services、newbuild vs aftermarket、large frame vs aero-derivative、project vs recurring。
- **Backlog / orders**：order intake、book-to-bill、backlog conversion、project timing。
- **Utilization**：fleet utilization、factory load、service hours、capacity factor。
- **Installed base / attach**：service attach rate、replacement cycle、parts intensity。
- **End-market proxy**：LNG FID、data center power demand、aerospace build rate、grid capex。"""
new_lib = """常用 driver 速查：

| 类型 | 指标 | 适用场景 |
|---|---|---|
| Volume | unit shipment、capacity、MW、MTPA、rig count、installed base | 制造/能源/设备 |
| Price | ASP、contract escalation、commodity pass-through | 定价权分析 |
| Mix | equipment vs services、newbuild vs aftermarket、project vs recurring | 利润率结构 |
| Backlog/orders | order intake、book-to-bill、backlog conversion | 项目制/长周期 |
| Utilization | fleet utilization、factory load、service hours、capacity factor | 服务/运维 |
| Installed base | service attach rate、replacement cycle、parts intensity | aftermarket |
| End-market proxy | LNG FID、data center power demand、aerospace build rate | 需求前瞻 |"""
text = text.replace(old_lib, new_lib)
changes.append('3. Driver Library 列表→表')

# 4. 删 Step 5 Implications
old_step5 = """### Step 5: Implications

说明这个 driver map 如何影响后续研究：
- 对 `3-statement-model / dcf-model / comps-analysis / model-update`：哪些 line item 应该按 driver 建模。
- 对 `alpha-thesis`：variant view 应该落在哪个 driver。
- 对 `primary-research-plan`：哪些 driver 假设需要 expert call、customer / supplier channel check、survey 或 fieldwork 验证。
- 对 `peer-deep-dive`：哪些 KPI 才可比，哪些不可比。
- 对 `pair-trade`：两腿是否受同一 driver 驱动，还是只是主题相似。
- 对 `research-journal`：哪些认知已经想清楚、值得沉淀。

## 输出结构"""
new_step5 = """## 输出结构"""
if old_step5 in text:
    text = text.replace(old_step5, new_step5)
    changes.append('4. 删 Step 5 Implications')
else:
    changes.append('4. Step 5 NOT FOUND')

# 5. Financial-Data 联动压缩
old_fd = """## Financial-Data 联动

`financial-data` 是本 skill 的 preferred upstream input，但不能替代 driver 判断。

读取顺序：

1. 先读 `topics/company/<company-slug>/_cache/financial-data/internal/actuals-resolved.json`。
2. 如果 `statements.revenue_split` 存在且非空，直接 review 其披露口径：`source_type = official-xbrl-dimension` 标为 `provider-structured`，`source_type = filing-table-extracted-review` 标为 `provider-table-review`，再转成 model bucket。
3. 如果 `revenue_split` 缺失或为空，读 `internal/evidence-pack.json` / `internal/completeness.json` 确认缺口，再读 `internal/full-filing.md`，用 LLM 从原文抽 disclosed revenue split，并标为 `llm-extracted-review`。
4. 如果原文也没有披露，标为 `not-disclosed`；不能编造 segment、product 或 geography split。

本 skill 可以改变收入 bucket 的建模处理方式，但不能覆盖 `financial-data` 的 completeness。`provider-structured`、`provider-table-review`、`provider-normalized-review`、`llm-extracted-review` 和 `not-disclosed` 必须在 `driver-map.md` 和 `internal/driver-map.json` 中分清。若 `revenue_split` row 标有 `review_required: true`，必须由 LLM 解释 axis/member 并映射 model bucket，不能直接当作最终建模口径。"""
new_fd = """## Financial-Data 联动

从 `actuals-resolved.json` 取数据，按 revenue_split 状态分类处理：

1. revenue_split 存在 → 按 source_type 归类：`official-xbrl-dimension` = provider-structured，`filing-table-extracted` = provider-table-review → 转 model bucket
2. revenue_split 缺失 → 读 `full-filing.md`，LLM 抽 disclosed split → 标 `llm-extracted-review`
3. 原文无披露 → 标 `not-disclosed`，不编造

`review_required: true` 的 row 需 LLM 解释 axis/member 映射，不能直接当最终口径。不覆盖 `financial-data` 的 completeness。"""
if old_fd in text:
    text = text.replace(old_fd, new_fd)
    changes.append('5. Financial-Data 联动压缩')
else:
    changes.append('5. FD NOT FOUND')

# 6. 保存对齐
old_save = '| **保存需求** | 写入 company driver-map cache + topic artifact | 默认对话；用户要求保存为建模输入时外显 `driver-map.md`，机器 JSON 写 `internal/driver-map.json` |'
new_save = '| **保存需求** | 写入 company topic cache + artifact | 默认保存：`driver-map.md` + `internal/driver-map.json` |'
text = text.replace(old_save, new_save)
changes.append('6. 保存对齐')

# 7. 篇幅合并
old_len = '- Quick driver check：400-700 字 + 1-2 张表。\n- Full company / segment driver-map：900-1600 字 + 3-4 张表。\n- 超过 1800 字通常说明范围过大，应拆给 `peer-deep-dive`、`3-statement-model / dcf-model / comps-analysis / model-update` 或多个 segment。'
# This was already changed earlier. Let me check what's there now.
idx = text.find('## 篇幅基准')
if idx >= 0:
    chunk = text[idx:]
    # find the lines
    lines = chunk.split('\n')
    # The current 篇幅 section should be 2 lines after the heading
    print('Current 篇幅 section:')
    for i in range(min(6, len(lines))):
        print(f'  {lines[i]}')

# Actually let me just check what the current 篇幅 looks like
old_len2 = '- 标准 driver-map：900-1600 字 + 3-4 张表。\n- 低于 700 字通常 driver 拆解不深或遗漏 proxy strategy；超过 1800 字通常说明范围过大，应收窄到核心 segment 或确认已覆盖所有关键 driver 后停止。'
new_len2 = '- 标准：900-1600 字 + 3-4 张表。低于 700 字通常 driver 拆解不深或漏 proxy strategy；超过 1800 字应收窄到核心 segment。'
if old_len2 in text:
    text = text.replace(old_len2, new_len2)
    changes.append('7. 篇幅合并')
else:
    changes.append('7. 篇幅 NOT FOUND')

# Check if old_len exists
if '- Quick driver check' in text:
    text = text.replace(old_len, new_len2)
    changes.append('7. 篇幅合并 (old format)')

with open('plugins/buy-side-research-skills/skills/driver-map/SKILL.md', 'w', encoding='utf-8') as f:
    f.write(text)

for c in changes:
    print(c)
print(f'Lines: {text.count(chr(10))+1}')
