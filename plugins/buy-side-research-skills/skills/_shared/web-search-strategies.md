# Web Search 策略：市场 × 数据类型

> 通用规则：先用 site: 限定首选域名 → 不加 site 用关键词搜 → 还搜不到标 `[ND]`。
> 每个 query 同时用**本地语言 + 英文**各搜一次。英文结果用于交叉验证，不以英文结果覆盖本地语言披露。

---

## A 股

### 三表 (IS/BS/CF)
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:eastmoney.com <ticker> <科目>` | `site:eastmoney.com <ticker> income statement` |
| ② | `site:10jqka.com.cn <公司名> 利润表` | — |
| ③ | `<ticker> 2025年报 利润表 资产负债表 现金流量表` | `<ticker> annual report financial statements` |

### 收入拆分
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:cninfo.com.cn <ticker> 营业收入构成` | — |
| ② | `<公司名> 2025年报 收入构成 分部` | `<ticker> revenue by segment` |

### 估值/股价
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:eastmoney.com <ticker> PE PB 市值` | `site:yahoo.com <ticker>.SZ statistics` |
| ② | `<ticker> 市盈率 市净率 总市值` | `<ticker>.SZ PE PB market cap` |

### Consensus
| 层 | 本地语言 |
|---|---|
| ① | `site:eastmoney.com <ticker> 盈利预测` |
| ② | `<ticker> 2026 EPS consensus 券商预测` |

---

## 港股

### 三表 (IS/BS/CF)
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:aastocks.com <code> 利润表` | `site:aastocks.com <code> income statement` |
| ② | `site:xueqiu.com <code> 财务` | `site:stockanalysis.com <code> financials` |
| ③ | `<code>.HK 2025年报 利润表 资产负债表` | `<code>.HK annual report IS BS CF` |

### 收入拆分
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:hkexnews.hk <code> 分部收入` | `site:hkexnews.hk <code> segment revenue` |
| ② | `<公司名> 2025年报 收入构成` | `<ticker>.HK revenue by segment` |

### 估值/股价
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:aastocks.com <code>` | `site:yahoo.com <code>.HK statistics` |
| ② | `<code>.HK PE PB 市值` | `<code>.HK PE PB market cap` |

### Consensus
| 层 | 英文 |
|---|---|
| ① | `site:marketscreener.com <ticker>.HK consensus` |
| ② | `<ticker>.HK analyst consensus EPS 2026` |

---

## 日本

### 三表
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:finance.yahoo.co.jp <code> 決算` | `site:yahoo.com <code>.T financials` |
| ② | `site:kabutan.jp <code> 業績` | `site:stockanalysis.com <code> financials` |
| ③ | `<code> 有価証券報告書 損益計算書 貸借対照表` | `<code>.T annual report income statement balance sheet` |

### 收入拆分
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `<code> セグメント別売上高` | `<ticker>.T revenue by segment` |
| ② | `<code> 決算説明会 セグメント` | `<ticker>.T segment breakdown` |

### 估值/股价
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:finance.yahoo.co.jp <code>` | `site:yahoo.com <code>.T statistics` |
| ② | `site:kabutan.jp <code>` | — |

### Consensus
| 层 | 英文 |
|---|---|
| ① | `site:marketscreener.com <code>.T consensus` |
| ② | `<code>.T analyst forecast EPS` |

---

## 韩国

### 三表
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:comp.fnguide.com <gicode>` | `site:yahoo.com <code>.KS financials` |
| ② | `site:finance.naver.com <code> 재무제표` | `site:stockanalysis.com <code> financials` |
| ③ | `<code> 감사보고서 재무상태표 손익계산서` | `<code>.KS annual report IS BS CF` |

### 收入拆分
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:dart.fss.or.kr <code> 사업부문별` | `<ticker>.KS revenue by segment` |
| ② | `<회사명> 사업보고서 매출구성` | `<ticker>.KS segment breakdown` |

### 估值/股价
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:comp.fnguide.com <gicode>` | `site:yahoo.com <code>.KS statistics` |
| ② | `site:markets.hankyung.com <code> consensus` | — |

### Consensus
| 层 | 本地语言 |
|---|---|
| ① | `site:comp.fnguide.com <gicode>` |
| ② | `site:markets.hankyung.com <code> consensus` |
| ③ | `site:marketscreener.com <ticker>.KS consensus` |

---

## 台湾

### 三表
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:goodinfo.tw <code>` | `site:yahoo.com <code>.TW financials` |
| ② | `site:mops.twse.com.tw <code> 财务报告` | — |
| ③ | `<code> 2025年報 損益表 資產負債表 現金流量表` | `<code>.TW annual report IS BS CF` |

### 收入拆分
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `<code> 營收 產品別 部門別` | `<ticker>.TW revenue by segment` |

### 估值/股价
| 层 | 本地语言 | 英文 |
|---|---|---|
| ① | `site:goodinfo.tw <code>` | `site:yahoo.com <code>.TW statistics` |

### Consensus
| 层 | 英文 |
|---|---|
| ① | `site:marketscreener.com <code>.TW consensus` |

---

## 欧洲

### 三表
| 层 | 英文 |
|---|---|
| ① | `site:yahoo.com <ticker> financials` |
| ② | `<ticker> annual report income statement balance sheet cash flow` |

### 收入拆分
| 层 | 英文 |
|---|---|
| ① | `<ticker> revenue by segment` |
| ② | `<ticker> annual report segment breakdown` |

### 估值/股价
| 层 | 英文 |
|---|---|
| ① | `site:yahoo.com <ticker> statistics` |

### Consensus
| 层 | 英文 |
|---|---|
| ① | `site:marketscreener.com <ticker> consensus` |

## US

### 三表
| 层 | 英文 |
|---|---|
| ① | `site:sec.gov <ticker> 10-K` |
| ② | `site:stockanalysis.com <ticker> financials` |
| ③ | `<ticker> 10-K annual report income statement balance sheet` |

### 收入拆分
| 层 | 英文 |
|---|---|
| ① | `site:sec.gov <ticker> segment revenue` |
| ② | `<ticker> 10-K revenue by segment` |

### 估值/股价
| 层 | 英文 |
|---|---|
| ① | `site:yahoo.com <ticker> statistics` |

### Consensus
| 层 | 英文 |
|---|---|
| ① | `site:marketscreener.com <ticker> consensus` |

## 跨市场通用

| 数据类型 | 首选 |
|---|---|
| Consensus | MarketScreener > 本地源（FnGuide/东方财富） |
| SI | 交易所官方 (FINRA/HKEX/JPX/KRX) |
| FX | `site:ecb.europa.eu` EUR / `site:pbc.gov.cn` CNY / `site:boj.or.jp` JPY |

## 网站速查

| 网站 | 市场 | site: 限定符 | URL 模式 |
|---|---|---|---|
| SEC EDGAR | US | `site:sec.gov` | — |
| 东方财富 | A+H | `site:eastmoney.com` | `quote.eastmoney.com/sz<code>.html` |
| 雪球 | A+H+US | `site:xueqiu.com` | `xueqiu.com/S/<code>` |
| 同花顺 | A+H | `site:10jqka.com.cn` | `basic.10jqka.com.cn/HK<code>/` |
| 新浪财经 | A+H | `site:finance.sina.com.cn` | — |
| 富途牛牛 | H+US | `site:futunn.com` | `futunn.com/stock/<code>-HK/earnings` |
| AAStocks | HK | `site:aastocks.com` | — |
| ET Net | HK | `site:etnet.com.hk` | — |
| Kabutan | JP | `site:kabutan.jp` | `kabutan.jp/stock/<code>` |
| Yahoo JP | JP | `site:finance.yahoo.co.jp` | — |
| FnGuide | KR | `site:comp.fnguide.com` | `comp.fnguide.com/SVO2/ASP/SVD_Main.asp?gicode=A<code>` |
| Naver Finance | KR | `site:finance.naver.com` | — |
| Hankyung | KR | `site:markets.hankyung.com` | `markets.hankyung.com/stock/<code>/consensus` |
| Goodinfo! | TW | `site:goodinfo.tw` | — |
| FinMind | TW | `site:finmindtrade.com` | — |
| MarketScreener | 全市场 | `site:marketscreener.com` | — |
| StockAnalysis | US/HK/EU | `site:stockanalysis.com` | — |
| Yahoo Finance | 全市场 | `site:yahoo.com` | `finance.yahoo.com/quote/<ticker>/key-statistics/` |
