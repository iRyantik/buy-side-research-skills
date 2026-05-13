## Financial Data Result

**结论先行：可用。** IONQ 三表（IS/BS/CF）全部 `model-ready`，覆盖 FY2022-FY2025 共 4 个财年，来自最新 10-K。可直接给 `3-statement-model / dcf-model / comps-analysis / model-update` 消费。

| Data item | Status | Source/provider | Period coverage | Model usable? | Caveat |
|---|---|---|---|---|---|
| Identity | provider-normalized-review | edgartools | latest | review | 公司识别信息完整；shares outstanding 需与最新 diluted count 核对 |
| Filing index | provider-normalized-review | edgartools | 10-K latest | review | 仅获取了最新一份 10-K |
| Income statement | model-ready | edgartools/XBRL | FY2022-FY2025 | yes | 含 Revenue、R&D、SG&A、OpEx、OI、Tax、EPS |
| Balance sheet | model-ready | edgartools/XBRL | FY2022-FY2025 | yes | 含 Assets、Liabilities、Equity、Goodwill、Cash、Debt |
| Cash flow | model-ready | edgartools/XBRL | FY2022-FY2025 | yes | 含 OCF、ICF、FCF components、SBC、D&A |

### 关键缺陷提示

- **无 segment revenue 拆分**：IONQ 目前为单业务线，SEC XBRL 无 segment tag，不适用。
- **无 geography split**：XBRL 未提供地域收入拆分。
- **FY2025 含重大并购影响**：Goodwill 从 $9.9M → $1,963M，反映 Acquisition of Cubane Limited；建模时应注意 pro-forma vs. actual 的区别。
- **SBC 占比极高**：FY2025 SBC $317M vs. Revenue $130M；model 需明确处理 SBC 加回和控制。
- **Noncontrolling interest 仅出现在 FY2025**：并购导致的结构变化，需要注意股权结构。
- **FY2025 有大额 equity raise**：Common stock issuance $3.3B，dilution 已体现在 share count 中。
- **Net operating loss / deferred tax assets**：FY2025 出现 $44.6M 的 income tax benefit（主要来自 deferred tax），需确认 NOL 利用情况。

### Output

- cache: `examples/financial-data-pull/us/ionq/`
- manifest: `examples/financial-data-pull/us/ionq/manifest.json`
- financial_data_pack_path: `examples/financial-data-pull/us/ionq/`

### Provider / Credential

- market: us
- identifier_type: ticker
- provider: edgartools (SEC XBRL)
- credential_status: EDGAR_IDENTITY configured
- latest 10-K used: FY2025 (period ending 2025-12-31)

### Caveats

- 数据来自 edgartools 对 SEC XBRL 的标签解析，属于 provider-normalized 数据，非原始 filing 文字。三表数值已交叉验证，在 filing 范围内可靠。
- 缺少 `filing-index.json`（因复制遗漏），但不影响建模；如需 filing 级 metadata 可从 full-filing.md 头部获取。
- 不包含 consensus、price、EV、FX 或 market data。
