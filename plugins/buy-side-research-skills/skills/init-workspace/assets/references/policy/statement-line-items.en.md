# Cross-Market Financial Statement Line Items

> This is the English translation of [statement-line-items.md](./statement-line-items.md). The Chinese version is the source of truth.

## Data Source Classification

| Tag | Meaning | Source Track |
|---|---|---|
| `FS` | Financial statement data (annual/quarterly filing disclosures) | disclosure-fact: topic-local cache > primary public > trusted third-party > web |
| `MKT` | Market data (price/valuation/FX/rates) | market-snapshot: financial-data > trusted third-party > web, must note as-of |
| `CON` | Consensus estimates (sell-side consensus/Bloomberg/Visible Alpha) | trusted third-party, must note date+source |
| `DER` | Derived value (computed from FS/MKT/CON) | no separate source required, but input sources must be traceable |

## Income Statement (IS)

| Line Item | Source | US GAAP / IFRS | A-Share | Hong Kong | Japan | Korea |
|---|---|---|---|---|---|---|
| Revenue | FS | Revenue / Sales | 营业收入 | 收益 | 売上高 | 매출 |
| COGS | FS | Cost of Revenue | 营业成本 | 銷售成本 | 売上原価 | 매출원가 |
| Gross Profit | DER | Revenue - COGS | Not separately listed | 毛利 | 売上総利益 | 매출총이익 |
| SG&A | FS | SG&A | 销售+管理费用 | 銷售及行政開支 | 販売費+一般管理費 | 판매비+관리비 |
| R&D | FS | R&D Expense | 研发费用 | 研發開支 | 研究開発費 | 연구개발비 |
| EBIT | DER | Operating Income | 营业利润 | 經營溢利 | 営業利益 | 영업이익 |
| Interest Expense | FS | Interest Expense | 财务费用/利息费用 | 融資成本 | 支払利息 | 이자비용 |
| Pre-Tax Income | FS | Pre-Tax Income | 利润总额 | 除稅前溢利 | 税引前純利益 | 법인세차감전순이익 |
| Net Income | FS | Net Income | 归母净利润 | 年內溢利 | 当期純利益 | 당기순이익 |
| SBC | FS | Stock-Based Comp (notes) | 股份支付 (notes) | 以股份為基礎的付款 | ストックオプション費用 | 주식기준보상 |

## Balance Sheet (BS)

| Line Item | Source | US GAAP / IFRS | A-Share | Hong Kong | Japan | Korea |
|---|---|---|---|---|---|---|
| Cash | FS | Cash & Equivalents | 货币资金 | 現金及現金等價物 | 現金及び預金 | 현금및현금성자산 |
| Accounts Receivable | FS | Accounts Receivable | 应收+应收票据 | 應收賬款及票據 | 売掛金+受取手形 | 매출채권 |
| Inventory | FS | Inventory | 存货 | 存貨 | 棚卸資産 | 재고자산 |
| Goodwill | FS | Goodwill | 商誉 | 商譽 | のれん | 영업권 |
| Short-Term Debt | FS | Short-Term Debt | 短期借款 | 短期借款 | 短期借入金 | 단기차입금 |
| Long-Term Debt | FS | Long-Term Debt | 长期借款 | 長期借款 | 長期借入金 | 장기차입금 |
| Bonds Payable | FS | Bonds Payable | 应付债券 | 應付債券 | 社債 | 사채 |
| Total Equity (Parent) | FS | Total Equity (Parent) | 归母股东权益 | 本公司擁有人應佔權益 | 親会社株主に帰属する純資産 | 지배기업소유주지분 |
| Market Cap | MKT | Shares × Price | 总市值 | 總市值 | 時価総額 | 시가총액 |

## Cash Flow Statement (CF)

| Line Item | Source | US GAAP / IFRS | A-Share | Hong Kong | Japan | Korea |
|---|---|---|---|---|---|---|
| Operating CF | FS | Operating Cash Flow | 经营活动现金流量净额 | 經營活動現金淨額 | 営業活動CF | 영업활동현금흐름 |
| CapEx | FS | Purchase of PP&E (Investing) | 购建固定资产无形资产支付的现金 | 購置物業廠房設備 | 有形固定資産の取得による支出 | 유형자산취득 |
| D&A | FS | Depreciation & Amortization (Supplemental) | 折旧+摊销+长期待摊 (supplemental) | 折舊及攤銷 | 減価償却費 | 감가상각비 |
| Dividends | FS | Dividends Paid (Financing) | 分配股利利润或偿付利息支付的现金 | 已付股息 | 配当金の支払額 | 배당금지급 |
| Buybacks | FS | Share Repurchase (Financing) | 股份回购 (financing activity/notes) | 股份回購 | 自己株式の取得 | 자기주식취득 |

## Market Data (MKT)

| Data Point | Notes |
|---|---|
| Share Price | Stock price — must note exchange + as-of date |
| FX Rate | Exchange rate — must note source + as-of date |
| Shares Outstanding | Total shares — basic vs diluted, must distinguish |
| Short Interest | Short interest / margin balance — A-share data center opaque; HK/US available |
| Implied Volatility | Option-implied volatility — when A-share underlyings are scarce, substitute with historical earnings move |

## Data Quality Markers

| Symbol | Meaning |
|---|---|
| `[S<n>](url)` | primary public source — disclosure original |
| `[I<n>](url)` | internet source — market snapshot/valuation/liquidity downgrade, must note as-of + fallback reason |
| `[ND]` | not disclosed — company has not disclosed |
| `[UNVERIFIED]` | number exists but source yet to be verified |
| `[note derivation basis]` | has derivation logic, note the derivation method |

> Full source policy: see `references/policy/research-policy-baseline.md` and workspace `CLAUDE.md`.
