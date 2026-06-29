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
3. **列映射 print**: `Cols: D=DS(4) FY0=F(6) LC=K(11) SC=H(8) proj_n=5 B_mode=False div=1`
4. §1 Reported Segments → §2 Logic Lines (module dispatch) → §2→§1 Fill → §3 P&L → §4-5 SOTP → §6 Market Data → §7 Scenario Summary
5. Post-format: zero cleanup + D/E clear + bold actuals + bold C-column labels
6. 保存 Excel

## 质量 Gate

```bash
python .scripts/driver-map/audit_style.py <output.xlsx>
```

检查: General format 单元格 / PCT 格式不匹配 / NUM 格式不匹配 / font 非 Calibri。Exit 0 = 通过。

## Output Naming

Agent 生成文件命名：`YYYY-MM-DD-driver-model-<ticker>.xlsx`，与 driver-map.json 同目录。

## Q Column Build

设置了 `q_actual_count > 0` 时自动生成 Q 列（1-4 actual + 4 proj）。Column mapping print 会显示 Q range。

## Quarterly Data Fetch

```bash
python .scripts/financial-data/financial_data.py --mode lite --market us --identifier LITE --quarters latest
```

yfinance 自动拉取最近 6Q IS 数据写入 `actuals-resolved.json`。
