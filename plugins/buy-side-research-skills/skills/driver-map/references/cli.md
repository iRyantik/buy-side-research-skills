# CLI — 生成 Excel 模型

## 命令

```bash
python .scripts/driver-map/build-logic-model.py <path/to/driver-map.json> [-o output.xlsx]
```

## 参数

| 参数 | 说明 |
|---|---|
| `json_path` | 必填，driver-map.json 路径 |
| `-o, --output` | 可选，输出 Excel 路径。默认 `json_path.replace('.json', '.xlsx')` |

## 执行流程

1. `validate_json(cfg)` — 检查 depth/method/数组长度/必填字段
2. yfinance 拉 Market Data（mcap/price/shares/PE/52W），失败则用 `meta.mcap_m` fallback
3. §1 Reported Segments → §2 Logic Lines (module dispatch) → §2→§1 Fill → §3 P&L → §4-5 SOTP → §6 Market Data → §7 Scenario Summary
4. Post-format（字体/加粗/列宽/冻结）
5. 保存 Excel

## Output Naming

Agent 生成文件命名：`YYYY-MM-DD-driver-model-<ticker>.xlsx`，与 driver-map.json 同目录。
