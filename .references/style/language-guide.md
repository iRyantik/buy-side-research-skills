# Language & Style Guide

> CLAUDE.md §5 的详细版。Agent 需要更具体的规则时 Read 本文件。

## 保留英文（不翻译）

- **股票代码**：`2330 TT`、`AAPL US`、`9988.HK`、`005930 KS`、`7203.T`
- **财务比率 / 科目**：PE、P/B、EV/EBITDA、EV/Sales、FCF、ROIC、ROE、ROA、NRR、GRR、ARR、GMV、LTV、CAC、IRR、WACC、NPV、SOTP、DCF
- **会计 / 流程缩写**：GAAP、Non-GAAP、IFRS、M&A、IPO、SPAC、LBO、PIPE、ESOP、CapEx、OpEx、D&A
- **行业技术 jargon**：SaaS、IaaS、DTC、BNPL、Fab、EUV、ASIC、HBM、CoWoS、LLM、RAG
- **货币代码**：USD、JPY、KRW、CNY、EUR、SGD、HKD、TWD、INR、GBP
- **单位**：`x`（倍数）、`bps`、`pp`（百分点）、`bn`、`m`、`k`、`tn`
- **路径/系统**：source title、URL、文件路径、YAML/JSON key、skill name、产品代号
- **Buy-side jargon**：batting average、refi wall、underwater、guide-down、whisper number、tape、book、bid、ask、long、short、cover、squeeze、bagger、re-rate

## 公司名

| 类型 | 规则 | 示例 |
|---|---|---|
| 有公认中文名 | 用中文名 | 苹果、三星、丰田、台积电、宁德时代 |
| 圈内默认说英文 | 直接英文 | Salesforce、Shopify、Snowflake、Nvidia |
| 中国大陆/港/台 | 用原中文名 | 台积电、宁德时代、腾讯、阿里巴巴、比亚迪 |
| 日韩公司用汉字 | 用原汉字 | 任天堂、三菱商事、現代自動車、三星電子 |
| 日韩公司假名/谚文 | 首次：中文名（原文）；后续仅中文 | 迅销（ファーストリテイリング）→ "迅销"；起亚（기아）→ "起亚" |

**非中文公司披露项**：首次出现的 segment、KPI、订单分类、客户名保留源语言（中文译名）。后续用中文短名。

**管理层原话**：措辞影响判断时保留原文 + 贴 source；否则中文概述 + 贴 source。

## 语言切换

> `LANG-default = zh`

override：用户说 "用英文输出" / "use English" → 切英文，覆盖至本轮结束。用户明示日/韩/其他语言时仅该段切换。

## Agent 新闻搜索语言

| 市场后缀 | 搜索语言 |
|---|---|
| `.HK` `.SS` `.SZ` | 简体中文 |
| `.TW` | 繁体中文 |
| `.JP` | 日本語 |
| `.KS` `.KQ` | 한국어 |
| `.US` `.AS` `.DE` `.L` `.ST` `.KL` | English |
