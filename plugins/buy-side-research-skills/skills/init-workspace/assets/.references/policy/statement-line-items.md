# 跨市场报表科目对照 — Field Registry

> **这是唯一的 field schema。** extract、validate、provider filter、Excel model 都从这里查。
> 原则：**有啥拿啥**——不在本章的表里也照存，concept 用原生 label。

## 数据来源分类

| 标记 | 含义 | Source Track |
|---|---|---|
| `FS` | 财务报表数据（年报/季报披露） | disclosure-fact: topic-local cache > primary public > trusted third-party > web |
| `MKT` | 市场数据（股价/估值/汇率/利率） | market-snapshot: financial-data > trusted third-party > web，须标 as-of |
| `CON` | 共识预期（sell-side consensus/Bloomberg/Visible Alpha） | trusted third-party，须标日期+来源 |
| `DER` | 推导值（由 FS/MKT/CON 计算得出） | 不需单独 source，但输入来源需可追溯 |

---

## 利润表 (Income Statement) — 30 科目

| # | concept | 来源 | US GAAP / IFRS | A 股 | 香港 | 日本 | 韩国 |
|---|---|---|---|---|---|---|---|
| IS-01 | revenue | FS | Revenue / Sales / Net Sales | 营业收入 / 营业总收入 | 收益 / 收入 | 売上収益 / 売上高 | 매출 / 매출액 |
| IS-02 | cogs | FS | Cost of Revenue / Cost of Sales / Cost of Goods Sold | 营业成本 / 营业总成本 | 銷售成本 | 売上原価 | 매출원가 |
| IS-03 | gross_profit | DER | Gross Profit / Gross Margin | —（可推导） | 毛利 | 売上総利益 | 매출총이익 |
| IS-04 | sg_and_a | FS | SG&A / Selling, General & Administrative | 销售费用+管理费用 | 銷售及行政開支 / 銷售及分銷成本 | 販売費及び一般管理費 | 판매비와관리비 |
| IS-05 | selling_expenses | FS | Selling Expenses / Sales & Marketing | 销售费用 | 銷售費用 | 販売費 | 판매비 |
| IS-06 | admin_expenses | FS | General & Administrative Expenses | 管理费用 | 行政開支 | 一般管理費 | 관리비 |
| IS-07 | r_and_d | FS | R&D Expense / Research & Development | 研发费用 | 研發開支 / 研究及開發費用 | 研究開発費 | 연구개발비 |
| IS-08 | operating_income | FS | Operating Income / Operating Profit / EBIT | 营业利润 | 經營溢利 | 営業利益 | 영업이익 |
| IS-09 | core_operating_income | FS | Core Operating Income (non-GAAP) | 扣非净利润（非 GAAP） | — | コア営業利益 | — |
| IS-10 | ebitda | DER | EBITDA | EBITDA（可推导） | EBITDA（可推导） | EBITDA（可推导） | EBITDA（可推导） |
| IS-11 | other_operating_income | FS | Other Operating Income | 其他收益 | 其他經營收入 | その他の営業収益 | 기타영업수익 |
| IS-12 | other_operating_expenses | FS | Other Operating Expenses | — | 其他經營開支 | その他の営業費用 | 기타영업비용 |
| IS-13 | finance_income | FS | Finance Income / Financial Income | 财务收入 / 利息收入 | 財務收入 | 金融収益 | 금융수익 |
| IS-14 | interest_income | FS | Interest Income | 利息收入 | 利息收入 | 受取利息 / 利息収入 | 이자수익 |
| IS-15 | dividend_income | FS | Dividend Income | 投资收益（股利） | 股息收入 | 受取配当金 | 배당금수익 |
| IS-16 | finance_costs | FS | Finance Costs / Financial Expenses | 财务费用 | 融資成本 / 財務費用 | 金融費用 | 금융비용 |
| IS-17 | interest_expense | FS | Interest Expense | 利息费用 / 利息支出 | 利息開支 | 支払利息 | 이자비용 |
| IS-18 | fx_gain_loss | FS | Foreign Exchange Gain/Loss | 汇兑损益 | 匯兌損益 | 為替差損益 | 외환차손익 |
| IS-19 | equity_method_income | FS | Equity Method Investment Income / Share of Profit of Associates | 对联营合营企业投资收益 | 應佔聯營及合營公司溢利 | 持分法による投資損益 | 관계기업투자손익 |
| IS-20 | impairment_loss | FS | Impairment Loss | 资产减值损失 | 減值虧損 | 減損損失 | 손상차손 |
| IS-21 | gain_loss_on_disposal | FS | Gain/Loss on Disposal of Assets | 资产处置收益 | 出售資產收益 | 固定資産売却損益 | 유형자산처분손익 |
| IS-22 | pretax_income | FS | Pre-Tax Income / Income Before Tax | 利润总额 | 除稅前溢利 | 税引前利益 | 법인세차감전순이익 |
| IS-23 | income_tax | FS | Income Tax Expense / Provision for Income Taxes | 所得税费用 | 所得稅開支 | 法人所得税費用 | 법인세비용 |
| IS-24 | net_income | FS | Net Income / Net Profit / Profit for the Year | 净利润 / 归母净利润 | 年內溢利 / 本公司擁有人應佔溢利 | 当期利益 / 親会社株主に帰属する当期利益 | 당기순이익 / 지배기업지분순이익 |
| IS-25 | net_income_parent | FS | Net Income Attributable to Parent | 归属于母公司股东的净利润 | 本公司擁有人應佔溢利 | 親会社の所有者に帰属する当期利益 | 지배기업소유주지분순이익 |
| IS-26 | net_income_non_controlling | FS | Net Income Attributable to Non-Controlling Interests | 少数股东损益 | 非控股權益應佔溢利 | 非支配持分帰属当期利益 | 비지배지분순이익 |
| IS-27 | eps_basic | FS | Basic Earnings Per Share | 基本每股收益 | 每股基本盈利 | 基本的１株当たり当期利益 | 기본주당순이익 |
| IS-28 | eps_diluted | FS | Diluted Earnings Per Share | 稀释每股收益 | 每股攤薄盈利 | 希薄化後１株当たり当期利益 | 희석주당순이익 |
| IS-29 | sbc | FS | Stock-Based Compensation | 股份支付 | 以股份為基礎的付款 | ストックオプション費用 | 주식기준보상 |
| IS-30 | d_and_a_in_is | FS | D&A within COGS/OPEX (if disclosed) | 折旧摊销（计入成本费用部分） | 折舊攤銷 | 減価償却費及び償却額（内訳） | 감가상각비（영업비용내） |

---

## 资产负债表 (Balance Sheet) — 38 科目

| # | concept | 来源 | US GAAP / IFRS | A 股 | 香港 | 日本 | 韩国 |
|---|---|---|---|---|---|---|---|
| **ASSETS** |
| BS-01 | cash | FS | Cash & Cash Equivalents | 货币资金 | 現金及現金等價物 / 現金及銀行存款 | 現金及び現金同等物 | 현금및현금성자산 |
| BS-02 | short_term_investments | FS | Short-Term Investments / Marketable Securities | 交易性金融资产 | 短期投資 | 短期投資 / 有価証券 | 단기금융상품 / 단기투자자산 |
| BS-03 | notes_receivable | FS | Notes Receivable | 应收票据 | 應收票據 | 受取手形 | 받을어음 |
| BS-04 | trade_receivables | FS | Trade Receivables / Accounts Receivable | 应收账款 | 應收賬款 | 営業債権 / 売掛金 | 매출채권 |
| BS-05 | other_receivables | FS | Other Receivables | 其他应收款 | 其他應收款 | その他の債権 | 기타채권 |
| BS-06 | contract_assets | FS | Contract Assets | 合同资产 | 合約資產 | 契約資産 | 계약자산 |
| BS-07 | inventories | FS | Inventories / Inventory | 存货 | 存貨 | 棚卸資産 | 재고자산 |
| BS-08 | prepayments | FS | Prepayments / Prepaid Expenses | 预付款项 | 預付款項 | 前払費用 | 선급금 / 선급비용 |
| BS-09 | other_current_assets | FS | Other Current Assets | 其他流动资产 | 其他流動資產 | その他の流動資産 | 기타유동자산 |
| BS-10 | current_assets | FS | Total Current Assets | 流动资产合计 | 流動資產總額 | 流動資産合計 | 유동자산계 |
| BS-11 | long_term_investments | FS | Long-Term Investments | 长期股权投资 / 其他权益工具投资 | 長期投資 | 投資有価証券 / 関係会社株式 | 장기투자자산 / 관계기업투자 |
| BS-12 | equity_method_investments | FS | Investments Accounted for Using Equity Method | 长期股权投资（权益法） | 於聯營及合營公司之權益 | 持分法で会計処理されている投資 | 관계기업및공동기업투자 |
| BS-13 | ppe | FS | Property, Plant & Equipment (Net) | 固定资产 | 物業、廠房及設備 | 有形固定資産 | 유형자산 |
| BS-14 | right_of_use_assets | FS | Right-of-Use Assets | 使用权资产 | 使用權資產 | 使用権資産 | 사용권자산 |
| BS-15 | investment_properties | FS | Investment Properties | 投资性房地产 | 投資物業 | 投資不動産 | 투자부동산 |
| BS-16 | goodwill | FS | Goodwill | 商誉 | 商譽 | のれん | 영업권 |
| BS-17 | intangible_assets | FS | Intangible Assets (excl. Goodwill) | 无形资产 | 無形資產 | 無形資産 | 무형자산（영업권제외） |
| BS-18 | deferred_tax_assets | FS | Deferred Tax Assets | 递延所得税资产 | 遞延稅項資產 | 繰延税金資産 | 이연법인세자산 |
| BS-19 | other_non_current_assets | FS | Other Non-Current Assets | 其他非流动资产 | 其他非流動資產 | その他の非流動資産 | 기타비유동자산 |
| BS-20 | non_current_assets | FS | Total Non-Current Assets | 非流动资产合计 | 非流動資產總額 | 非流動資産合計 | 비유동자산계 |
| BS-21 | total_assets | FS | Total Assets | 资产总计 | 資產總額 | 資産合計 | 자산총계 |
| **LIABILITIES** |
| BS-22 | short_term_debt | FS | Short-Term Debt / Current Portion of LT Debt | 短期借款 | 短期借款 | 短期借入金（1年内返済） | 단기차입금 / 유동성장기부채 |
| BS-23 | notes_payable | FS | Notes Payable | 应付票据 | 應付票據 | 支払手形 | 지급어음 |
| BS-24 | trade_payables | FS | Trade Payables / Accounts Payable | 应付账款 | 應付賬款 | 営業債務 / 買掛金 | 매입채무 |
| BS-25 | other_payables | FS | Other Payables | 其他应付款 | 其他應付款 | その他の債務 | 기타채무 |
| BS-26 | contract_liabilities | FS | Contract Liabilities / Deferred Revenue | 合同负债 | 合約負債 | 契約負債 | 계약부채 |
| BS-27 | advance_payments | FS | Advance Payments from Customers | 预收款项 | 預收款項 | 前受金 | 선수금 |
| BS-28 | income_tax_payable | FS | Income Tax Payable | 应交税费 | 應付稅項 | 未払法人所得税 | 미지급법인세 |
| BS-29 | lease_liabilities_current | FS | Lease Liabilities (Current) | 一年内到期的租赁负债 | 租賃負債（流動） | リース負債（流動） | 리스부채（유동） |
| BS-30 | other_current_liabilities | FS | Other Current Liabilities | 其他流动负债 | 其他流動負債 | その他の流動負債 | 기타유동부채 |
| BS-31 | current_liabilities | FS | Total Current Liabilities | 流动负债合计 | 流動負債總額 | 流動負債合計 | 유동부채계 |
| BS-32 | long_term_debt | FS | Long-Term Debt | 长期借款 | 長期借款 | 長期借入金 | 장기차입금 |
| BS-33 | bonds_payable | FS | Bonds Payable | 应付债券 | 應付債券 | 社債 | 사채 |
| BS-34 | lease_liabilities_non_current | FS | Lease Liabilities (Non-Current) | 租赁负债（非流动） | 租賃負債（非流動） | リース負債（非流動） | 리스부채（비유동） |
| BS-35 | deferred_tax_liabilities | FS | Deferred Tax Liabilities | 递延所得税负债 | 遞延稅項負債 | 繰延税金負債 | 이연법인세부채 |
| BS-36 | retirement_benefit_liabilities | FS | Retirement Benefit Obligations / Pension Liabilities | 应付职工薪酬（长期） | 退休福利責任 | 退職給付に係る負債 | 퇴직급여부채 / 확정급여부채 |
| BS-37 | provisions | FS | Provisions | 预计负债 / 准备金 | 撥備 | 引当金 | 충당부채 |
| BS-38 | other_non_current_liabilities | FS | Other Non-Current Liabilities | 其他非流动负债 | 其他非流動負債 | その他の非流動負債 | 기타비유동부채 |
| BS-39 | non_current_liabilities | FS | Total Non-Current Liabilities | 非流动负债合计 | 非流動負債總額 | 非流動負債合計 | 비유동부채계 |
| BS-40 | total_liabilities | FS | Total Liabilities | 负债合计 | 負債總額 | 負債合計 | 부채총계 |
| **EQUITY** |
| BS-41 | share_capital | FS | Share Capital / Common Stock | 股本 / 实收资本 | 股本 | 資本金 | 자본금 |
| BS-42 | capital_surplus | FS | Additional Paid-In Capital / Share Premium | 资本公积 | 股份溢價 | 資本剰余金 | 자본잉여금 |
| BS-43 | treasury_shares | FS | Treasury Shares | 库存股 | 庫存股 | 自己株式 | 자기주식 / 자본조정 |
| BS-44 | retained_earnings | FS | Retained Earnings | 盈余公积+未分配利润 | 保留溢利 | 利益剰余金 | 이익잉여금 |
| BS-45 | other_equity | FS | Other Comprehensive Income / Other Reserves | 其他综合收益 | 其他儲備 | その他の資本の構成要素 | 기타포괄손익누계액 |
| BS-46 | total_equity_parent | FS | Total Equity Attributable to Parent | 归属于母公司股东权益合计 | 本公司擁有人應佔權益 | 親会社の所有者に帰属する持分 | 지배기업소유주지분 |
| BS-47 | non_controlling_interests | FS | Non-Controlling Interests / Minority Interest | 少数股东权益 | 非控股權益 | 非支配持分 | 비지배지분 |
| BS-48 | total_equity | FS | Total Equity | 股东权益合计 | 權益總額 | 資本合計 | 자본총계 |

---

## 现金流量表 (Cash Flow) — 16 科目

| # | concept | 来源 | US GAAP / IFRS | A 股 | 香港 | 日本 | 韩国 |
|---|---|---|---|---|---|---|---|
| CF-01 | operating_cf | FS | Net Cash from Operating Activities | 经营活动产生的现金流量净额 | 經營活動所得現金淨額 | 営業活動によるキャッシュ・フロー | 영업활동현금흐름 |
| CF-02 | profit_before_tax_cf | FS | Profit Before Tax (CF starting point) | 利润总额（间接法起点） | — | 税引前利益（CF起点） | — |
| CF-03 | depreciation | FS | Depreciation & Amortization (CF adjustment) | 折旧 | 折舊 | 減価償却費 | 감가상각비 |
| CF-04 | amortization | FS | Amortization of Intangibles | 摊销 | 攤銷 | 償却費 | 무형자산상각비 |
| CF-05 | impairment_cf | FS | Impairment Losses (CF adjustment) | 资产减值准备 | 減值 | 減損損失（CF調整） | 손상차손（CF조정） |
| CF-06 | finance_costs_cf | FS | Finance Costs (CF adjustment) | 财务费用（CF调整） | 財務成本（CF調整） | 金融費用（CF調整） | 금융비용（CF조정） |
| CF-07 | interest_received | FS | Interest Received | 收到利息 | 已收利息 | 利息の受取額 | 이자수취 |
| CF-08 | interest_paid | FS | Interest Paid | 支付利息 | 已付利息 | 利息の支払額 | 이자지급 |
| CF-09 | dividend_received | FS | Dividends Received | 收到股利 | 已收股息 | 配当金の受取額 | 배당금수취 |
| CF-10 | income_tax_paid | FS | Income Tax Paid | 支付所得税 | 已付所得稅 | 法人所得税の支払額 | 법인세납부 |
| CF-11 | change_in_working_capital | DER | Change in Working Capital | 营运资本变动 | 營運資金變動 | 運転資本増減 | 운전자본변동 |
| CF-12 | investing_cf | FS | Net Cash from Investing Activities | 投资活动产生的现金流量净额 | 投資活動所得現金淨額 | 投資活動によるキャッシュ・フロー | 투자활동현금흐름 |
| CF-13 | capex | FS | Purchase of PP&E / Capital Expenditure | 购建固定资产无形资产支付的现金 | 購置物業廠房設備 | 有形固定資産の取得による支出 | 유형자산취득 |
| CF-14 | financing_cf | FS | Net Cash from Financing Activities | 筹资活动产生的现金流量净额 | 融資活動所得現金淨額 | 財務活動によるキャッシュ・フロー | 재무활동현금흐름 |
| CF-15 | dividends_paid | FS | Dividends Paid | 分配股利利润或偿付利息支付的现金 | 已付股息 | 配当金の支払額 | 배당금지급 |
| CF-16 | buybacks | FS | Share Repurchases / Treasury Stock Acquired | 股份回购 | 股份回購 | 自己株式の取得による支出 | 자기주식취득 |

---

## 分部与补充数据 (Segment & Supplementary)

| # | concept | 来源 | 说明 |
|---|---|---|---|
| SG-01 | revenue_split | FS | 分部收入拆分 — segment × period × value |
| SG-02 | segment_profit | FS | 分部利润 — segment × period × value（口径标注：EBIT/GP/CoreOP） |
| SG-03 | order_backlog | FS/MKT | 订单积压 / Order Backlog |
| SG-04 | orders | FS/MKT | 新签订单 / Orders Received / Bookings |
| SG-05 | book_to_bill | DER | Book-to-Bill ratio |
| SG-06 | employees | FS | 员工总数 |
| SG-07 | production_volume | FS | 产量 / Production Volume |
| SG-08 | utilization_pct | FS/MKT | 产能利用率 |
| SG-09 | installed_base | FS/MKT | 装机量 / Installed Base |
| SG-10 | arr | FS | Annual Recurring Revenue（SaaS） |
| SG-11 | nrr | FS | Net Revenue Retention（SaaS） |

---

## 市场数据 (Market Data) — 12 项

| # | concept | 来源 | 说明 |
|---|---|---|---|
| MK-01 | price | MKT | 股价 — 须标 exchange + as-of date |
| MK-02 | market_cap | MKT | 总市值 |
| MK-03 | shares_outstanding | MKT | 总股本（basic / diluted 须区分） |
| MK-04 | pe_ttm | MKT | P/E (Trailing Twelve Months) |
| MK-05 | pe_ntm | MKT | P/E (Forward / NTM) |
| MK-06 | pb | MKT | Price to Book |
| MK-07 | ps_ttm | MKT | Price to Sales (TTM) |
| MK-08 | ev_ebitda | MKT | EV/EBITDA |
| MK-09 | ev_sales | MKT | EV/Sales |
| MK-10 | dividend_yield_pct | MKT | 股息率 |
| MK-11 | beta | MKT | Beta |
| MK-12 | fifty_two_week_high_low | MKT | 52周高低 |

---

## 数据质量标记

| 符号 | 含义 |
|---|---|
| `[S<n>](url)` | primary public source — 披露原文 |
| `[I<n>](url)` | internet source — 市场快照/估值/流动性降级，须标 as-of + fallback reason |
| `[ND]` | not disclosed — 公司未披露 |
| `[需查证]` | 数字存在但 source 待验证 |
| `[推算]` | 有推算逻辑，标推算方法 |

> 完整 source policy 见 `.references/policy/research-policy-baseline.md` 和 workspace `CLAUDE.md`。

---

## actuals-resolved.json schema

```json
{
  "ticker": "string",
  "market": "string (us/cn/hk/jp/kr/tw/eu/se/fr/de/uk/sg/my/in/au)",
  "source": "string (ir_tdnet/ir_dart/ir_mops/ir_company/edgar_api/akshare_api/...)",
  "identity": { "ticker": "", "name_en": "", "name_native": "", "fiscal_year_end": "" },
  "statements": {
    "income_statement": [
      {
        "label": "native label (e.g. 売上収益)",
        "concept": "standard concept (e.g. revenue) — from this registry",
        "values": { "FY2024": 100, "FY2025": 110 },
        "unit": "JPY_M",
        "source": "S1",
        "note": "optional"
      }
    ],
    "balance_sheet": [ /* same structure */ ],
    "cash_flow": [ /* same structure */ ],
    "revenue_split": [
      {
        "segment": "segment name",
        "type": "business / geography / product",
        "revenue": { "FY2025": 100 },
        "operating_profit": { "FY2025": 20 },
        "unit": "JPY_M",
        "source": "S1"
      }
    ]
  },
  "commentary": "string — management discussion summary",
  "outlook": { /* structured guidance if available */ },
  "market_data": { /* MK fields from above */ },
  "source_map": {
    "S1": { "source_layer": "", "url": "", "detail": "" }
  }
}
```

### 规则

1. **concept 必填**：每个 item 必须有 concept——优先从本 registry 取标准名，registry 没有就用原生 label 做 concept
2. **不裁减**：filing 有什么存什么。不在 registry 里的照存，concept 用 `label` 的 snake_case
3. **缺了不报错**：没披露的字段不存，不标 `[ND]` 也不留空行
4. **unit 必填**：每个 item 必须标单位（JPY_M / KRW_M / TWD_M / USD / SEK_M 等）
5. **source 必填**：每个 item 指向 `source_map` 里的 key
