#!/usr/bin/env python3
"""Fetch deterministic, source-tracked financial evidence packs.

Only structured, verifiable data is extracted by code. Narrative analysis,
segment interpretation, and business insights are left for LLM/research skills
at query time.

Output contract:
  .raw/.../provider_payload.json
  .raw/.../identity-source.json
  .raw/.../filings/<filing-id>/source.*
  .raw/.../filings/<filing-id>/source-metadata.json
  .raw/.../filings/<filing-id>/source.sha256

  .cache/.../manifest.json
  .cache/.../identity.json
  .cache/.../filing-index.json
  .cache/.../financials.normalized.json
  .cache/.../financials.md
  .cache/.../full-filing.md
  .cache/.../full-filing.chunks.jsonl
  .cache/.../full-filing.index.json
  .cache/.../completeness.json
  .cache/.../source-map.json
  .cache/.../cross-check.json

Modeling input aliases:
  industry/<industry>/companies/<ticker>/.cache/financial-data/financial-data-summary.md
  industry/<industry>/companies/<ticker>/.cache/financial-data/internal/evidence-pack.json
  industry/<industry>/companies/<ticker>/.cache/financial-data/internal/actuals-resolved.json
  industry/<industry>/companies/<ticker>/.cache/financial-data/internal/full-filing.md
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any


DEFAULT_ITEMS = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]
FINANCIAL_OUTPUT_KEYS = (
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "revenue_split",
    "income_statement_quarterly_derived",
    "cash_flow_quarterly_derived",
)

SUPPORTED_MODES = ("latest_core", "five_years", "filing_only", "cross_check", "snapshot", "lite", "full")

# Third-party normalized-data providers: their output is never model-ready
THIRD_PARTY_PROVIDERS = {"akshare", "finmind"}
OFFICIAL_EVIDENCE_PROVIDERS = {"edgartools", "dart-fss", "edinet-tools", "openesef"}

# Field schema is now in .references/policy/statement-line-items.md.
# No more LITE/FULL field caps — extract everything the filing has.
# Mode difference: lite = latest period only, full = 5Y periods.

# ---------------------------------------------------------------------------
# Concept mapping: parse statement-line-items.md → {concept_alias: standard_field}
# ---------------------------------------------------------------------------
_concept_map_cache = None

# Standard field name aliases: canonical name / variant → LITE_FIELDS-compatible key
_FIELD_ALIASES = {
    "revenue": "revenue", "sales": "revenue", "cogs": "cogs",
    "cost_of_revenue": "cogs", "cost_of_goods_sold": "cogs",
    "gross_profit": "gross_profit", "sg&a": "sg_and_a", "r&d": "r_and_d",
    "operating_income": "operating_income", "ebit": "ebit", "ebitda": "ebitda",
    "interest_expense": "interest_expense", "income_tax": "income_tax",
    "pre_tax_income": "pre_tax_income", "pre-tax_income": "pre_tax_income",
    "net_income": "net_income", "eps": "eps", "sbc": "sbc",
    "d&a": "d_and_a", "d_and_a": "d_and_a", "amortization": "amortization",
    "cash": "cash", "accounts_receivable": "accounts_receivable",
    "inventory": "inventory", "total_current_assets": "total_current_assets",
    "goodwill": "goodwill", "intangible_assets": "intangible_assets",
    "total_assets": "total_assets", "short_term_debt": "short_term_debt",
    "short-term_debt": "short_term_debt", "long_term_debt": "long_term_debt",
    "long-term_debt": "long_term_debt", "total_debt": "total_debt",
    "total_liabilities": "total_liabilities", "total_equity": "total_equity",
    "market_cap": "market_cap", "bonds_payable": "bonds_payable",
    "total_current_liabilities": "total_current_liabilities",
    "operating_cf": "operating_cf", "capex": "capex",
    "dividends": "dividends_paid", "dividends_paid": "dividends_paid",
    "buybacks": "buybacks", "free_cash_flow": "free_cash_flow",
    "order_backlog": "order_backlog", "orders": "orders",
    "book_to_bill": "book_to_bill", "installed_base": "installed_base",
    "employees": "employees", "customer_count": "customer_count",
    "arr": "arr", "nrr": "nrr", "grr": "grr", "churn": "churn",
    "production_volume": "production_volume", "utilization_pct": "utilization_pct",
    # AKShare / Eastmoney provider codes (CN)
    "total_operate_income": "revenue", "operate_income": "operating_income",
    "total_operate_cost": "cogs", "operate_cost": "cogs",
    "sale_expense": "sg_and_a", "admin_expense": "sg_and_a",
    "research_expense": "r_and_d", "develop_expense": "r_and_d",
    "finance_expense": "interest_expense",
    "income_tax_expense": "income_tax",
    "netprofit_atsopc": "net_income", "net_profit": "net_income",
    "gross_profit_is": "gross_profit",
    "accounts_rece": "accounts_receivable", "inventories": "inventory",
    "monetary_cap": "cash",
    "goodwill_bs": "goodwill",
    "shortterm_borrow": "short_term_debt", "longterm_borrow": "long_term_debt",
    "bond_payable": "bonds_payable",
    "total_current_liability": "total_current_liabilities",
    "total_equity_atsopc": "total_equity",
    "net_cash_flows_oper": "operating_cf", "net_cash_flows_oper_act": "operating_cf",
    "purchase_assets": "capex",
    "dividend_paid": "dividends_paid",
    "eps_basic": "eps", "diluted_eps": "eps",
    # EDINET JP provider codes
    "net_sales": "revenue",
    "ordinary_income": "pre_tax_income", "ordinary_profit": "pre_tax_income",
    "profit_loss": "net_income",
    "total_assets_bs": "total_assets", "net_assets": "total_equity",
    "net_cash_provided_by_used_in_operating_activities": "operating_cf",
    "purchase_of_property_plant_and_equipment": "capex",
    # DART KR provider codes
    "ifrs_revenue": "revenue", "ifrs_operating_profit_loss": "operating_income",
    "ifrs_profit_loss": "net_income", "ifrs_total_assets": "total_assets",
    # Chinese CN concept names (AKShare / Eastmoney)
    "营业总收入": "revenue", "营业收入": "revenue", "营业总成本": "cogs", "营业成本": "cogs",
    "营业利润": "operating_income", "利润总额": "pre_tax_income", "净利润": "net_income",
    "归属于母公司股东的净利润": "net_income", "归母净利润": "net_income",
    "研发费用": "r_and_d", "销售费用": "sg_and_a", "管理费用": "sg_and_a",
    "财务费用": "interest_expense", "利息费用": "interest_expense",
    "资产总计": "total_assets", "总资产": "total_assets",
    "负债合计": "total_liabilities", "总负债": "total_liabilities",
    "股东权益合计": "total_equity", "总权益": "total_equity",
    "经营活动产生的现金流量净额": "operating_cf", "经营现金流": "operating_cf",
    "购建固定资产、无形资产和其他长期资产支付的现金": "capex",
    "基本每股收益": "eps", "稀释每股收益": "eps",
    "货币资金": "cash", "应收账款": "accounts_receivable", "存货": "inventory",
    "商誉": "goodwill", "短期借款": "short_term_debt", "长期借款": "long_term_debt",
    # Japanese JP concept names (EDINET)
    "売上高": "revenue", "営業利益": "operating_income", "経常利益": "pre_tax_income",
    "当期純利益": "net_income", "親会社株主に帰属する当期純利益": "net_income",
    "総資産": "total_assets", "純資産": "total_equity", "負債": "total_liabilities",
    "営業活動によるキャッシュ・フロー": "operating_cf",
    # HK concept names (AKShare — auto-generated from API, 97 items)
    "保留溢利(累计亏损)": "retained_earnings",
    "储备": "other_equity",
    "全面收益总额": "total_comprehensive_income",
    "其他储备": "other_equity",
    "其他全面收益": "other_comprehensive_income",
    "其他全面收益其他项目": "other_comprehensive_income",
    "其他支出": "other_operating_expenses",
    "其他收入": "other_operating_income",
    "其他收益": "other_operating_income",
    "其他营业收入": "other_operating_income",
    "其他非流动资产": "other_non_current_assets",
    "净资产": "total_equity",
    "减:出售资产之溢利": "gain_loss_on_disposal",
    "减:利息收入": "interest_income",
    "减:汇兑收益": "fx_gain_loss",
    "出售附属公司": "sale_of_subsidiaries",
    "利息收入": "interest_income",
    "加:利息支出": "interest_expense",
    "加:折旧及摊销": "depreciation",
    "发行债券": "bond_issuance",
    "发行股份": "share_issuance",
    "合营公司权益": "equity_method_investments",
    "回购股份": "buybacks",
    "固定资产": "ppe",
    "土地使用权": "right_of_use_assets",
    "在建工程": "construction_in_progress",
    "存货": "inventories",
    "存货(增加)减少": "change_in_inventory",
    "少数股东损益": "net_income_non_controlling",
    "少数股东权益": "non_controlling_interests",
    "已付利息(经营)": "interest_paid",
    "已付税项": "income_tax_paid",
    "已付股息(融资)": "dividends_paid",
    "库存股": "treasury_shares",
    "应付帐款": "payables",
    "应付票据": "notes_payable",
    "应付税项": "income_tax_payable",
    "应占合营公司溢利": "equity_method_income",
    "应占联营公司溢利": "equity_method_income",
    "应收帐款": "receivables",
    "应收帐款减少": "change_in_receivables",
    "总权益": "total_equity",
    "总负债": "total_liabilities",
    "总资产": "total_assets",
    "投资业务现金净额": "investing_cf",
    "投资物业": "investment_properties",
    "持续经营业务税后利润": "net_income",
    "收购附属公司": "acquisition_of_subsidiaries",
    "无形资产": "intangible_assets",
    "期初现金": "cash_beginning",
    "期末现金": "cash_ending",
    "本公司拥有人应占全面收益总额": "total_comprehensive_income_parent",
    "每股基本盈利": "eps_basic",
    "每股摊薄盈利": "eps_diluted",
    "每股股息": "dps",
    "毛利": "gross_profit",
    "流动负债合计": "current_liabilities",
    "流动资产合计": "current_assets",
    "溢利其他项目": "other_profit_items",
    "物业厂房及设备": "ppe",
    "现金净额": "change_in_cash",
    "现金及等价物": "cash",
    "短期贷款": "short_term_debt",
    "税项": "income_tax",
    "经营业务现金净额": "operating_cf",
    "经营产生现金": "cash_generated_from_operations",
    "经营溢利": "operating_income",
    "联营公司权益": "equity_method_investments",
    "股东应占溢利": "net_income",
    "股东权益": "total_equity_parent",
    "股息": "dps",
    "股本": "share_capital",
    "股本溢价": "capital_surplus",
    "营业额": "revenue",
    "营运支出": "cogs",
    "营运收入": "revenue",
    "融资业务现金净额": "financing_cf",
    "融资成本": "interest_expense",
    "融资租赁负债(流动)": "lease_liabilities_current",
    "融资租赁负债(非流动)": "lease_liabilities_non_current",
    "行政开支": "admin_expenses",
    "购建固定资产": "capex",
    "赎回债券": "bond_redemption",
    "递延收入(流动)": "contract_liabilities",
    "递延税项负债": "deferred_tax_liabilities",
    "递延税项资产": "deferred_tax_assets",
    "销售及分销费用": "sg_and_a",
    "长期贷款": "long_term_debt",
    "除税前溢利": "pretax_income",
    "除税前溢利(业务利润)": "profit_before_tax_cf",
    "除税后溢利": "net_income_total",
    "非控股权益应占全面收益总额": "total_comprehensive_income_nci",
    "非流动负债合计": "non_current_liabilities",
    "非流动资产合计": "non_current_assets",
    "非运算项目": "elimination_items",
    "预付款按金及其他应收款": "other_receivables",
    "预付款项": "prepayments",

# AKShare HK label count:97 AKShare HK label mappings added above

    # HK concept names (AKShare — auto-generated from API, 130 items)
    "中长期存款": "short_term_investments",
    "保留溢利(累计亏损)": "retained_earnings",
    "偿还借款": "repayment_of_borrowings",
    "储备": "other_equity",
    "全面收益总额": "total_comprehensive_income",
    "其他储备": "other_equity",
    "其他全面收益": "other_comprehensive_income",
    "其他全面收益其他项目": "other_comprehensive_income",
    "其他投资": "long_term_investments",
    "其他支出": "other_operating_expenses",
    "其他收入": "other_operating_income",
    "其他收益": "other_operating_income",
    "其他营业收入": "other_operating_income",
    "其他金融资产(流动)": "other_current_assets",
    "其他金融资产(非流动)": "other_non_current_assets",
    "其他非流动资产": "other_non_current_assets",
    "净流动资产": "net_current_assets",
    "净资产": "total_equity",
    "减:出售资产之溢利": "gain_loss_on_disposal",
    "减:利息收入": "interest_income",
    "减:汇兑收益": "fx_gain_loss",
    "出售附属公司": "sale_of_subsidiaries",
    "利息收入": "interest_income",
    "加:利息支出": "interest_expense",
    "加:折旧及摊销": "depreciation",
    "发行债券": "bond_issuance",
    "发行股份": "share_issuance",
    "受限制存款及现金": "cash",
    "可转换可赎回优先股": "other_equity",
    "合营公司权益": "equity_method_investments",
    "回购股份": "buybacks",
    "固定资产": "ppe",
    "土地使用权": "right_of_use_assets",
    "在建工程": "construction_in_progress",
    "存货": "inventories",
    "存货(增加)减少": "change_in_inventory",
    "少数股东损益": "net_income_non_controlling",
    "少数股东权益": "non_controlling_interests",
    "已付利息(经营)": "interest_paid",
    "已付税项": "income_tax_paid",
    "已付股息(融资)": "dividends_paid",
    "已收利息(投资)": "interest_received",
    "已收股息(投资)": "dividend_received",
    "库存股": "treasury_shares",
    "应付关联方款项(流动)": "other_payables",
    "应付帐款": "payables",
    "应付票据": "notes_payable",
    "应付税项": "income_tax_payable",
    "应占合营公司溢利": "equity_method_income",
    "应占联营公司溢利": "equity_method_income",
    "应收关联方款项": "other_receivables",
    "应收帐款": "receivables",
    "应收帐款减少": "change_in_receivables",
    "总权益": "total_equity",
    "总权益及总负债": "total_assets",
    "总权益及非流动负债": "total_equity_and_ncl",
    "总负债": "total_liabilities",
    "总资产": "total_assets",
    "总资产减流动负债": "net_assets",
    "投资业务现金净额": "investing_cf",
    "投资物业": "investment_properties",
    "拟派股息": "dps",
    "拨备(流动)": "provisions",
    "持作出售的负债(流动)": "other_current_liabilities",
    "持作出售的资产(流动)": "short_term_investments",
    "持续经营业务税后利润": "net_income",
    "收购附属公司": "acquisition_of_subsidiaries",
    "新增借款": "new_borrowings",
    "无形资产": "intangible_assets",
    "期初现金": "cash_beginning",
    "期末现金": "cash_ending",
    "本公司拥有人应占全面收益总额": "total_comprehensive_income_parent",
    "每股基本盈利": "eps_basic",
    "每股摊薄盈利": "eps_diluted",
    "每股股息": "dps",
    "毛利": "gross_profit",
    "流动负债合计": "current_liabilities",
    "流动资产合计": "current_assets",
    "溢利其他项目": "other_profit_items",
    "物业厂房及设备": "ppe",
    "现金净额": "change_in_cash",
    "现金及等价物": "cash",
    "短期存款": "short_term_investments",
    "短期贷款": "short_term_debt",
    "税项": "income_tax",
    "经营业务现金净额": "operating_cf",
    "经营产生现金": "cash_generated_from_operations",
    "经营溢利": "operating_income",
    "职工薪酬及福利(非流动)": "retirement_benefit_liabilities",
    "联营公司权益": "equity_method_investments",
    "股东应占溢利": "net_income",
    "股东权益": "total_equity_parent",
    "股息": "dps",
    "股本": "share_capital",
    "股本溢价": "capital_surplus",
    "营业额": "revenue",
    "营运支出": "cogs",
    "营运收入": "revenue",
    "融资业务现金净额": "financing_cf",
    "融资前现金净额": "net_cash_before_financing",
    "融资成本": "interest_expense",
    "融资租赁负债(流动)": "lease_liabilities_current",
    "融资租赁负债(非流动)": "lease_liabilities_non_current",
    "行政开支": "admin_expenses",
    "衍生金融工具-负债": "other_non_current_liabilities",
    "衍生金融工具-负债(流动)": "other_current_liabilities",
    "衍生金融工具-资产": "other_non_current_assets",
    "衍生金融工具-资产(流动)": "short_term_investments",
    "购建固定资产": "capex",
    "赎回债券": "bond_redemption",
    "递延收入(流动)": "contract_liabilities",
    "递延税项负债": "deferred_tax_liabilities",
    "递延税项资产": "deferred_tax_assets",
    "销售及分销费用": "sg_and_a",
    "长期应付款": "other_non_current_liabilities",
    "长期应收款": "other_non_current_assets",
    "长期贷款": "long_term_debt",
    "除税前溢利": "pretax_income",
    "除税前溢利(业务利润)": "profit_before_tax_cf",
    "除税后溢利": "net_income_total",
    "非控股权益应占全面收益总额": "total_comprehensive_income_nci",
    "非流动负债合计": "non_current_liabilities",
    "非流动资产其他项目": "other_non_current_assets",
    "非流动资产合计": "non_current_assets",
    "非运算项目": "elimination_items",
    "预付款按金及其他应收款": "other_receivables",
    "预付款项": "prepayments",
    "预收款项": "advance_payments",
    "预缴及应收税项": "other_current_assets",

# AKShare HK label count:129 AKShare HK label mappings added above

    # HK concept names (AKShare, auto-generated from API)
    "中长期存款": "short_term_investments",
    "保留溢利(累计亏损)": "retained_earnings",
    "偿还借款": "repayment_of_borrowings",
    "偿还融资租赁": "lease_repayments",
    "储备": "other_equity",
    "全面收益总额": "total_comprehensive_income",
    "其他储备": "other_equity",
    "其他全面收益": "other_comprehensive_income",
    "其他全面收益其他项目": "other_comprehensive_income",
    "其他投资": "long_term_investments",
    "其他支出": "other_operating_expenses",
    "其他收入": "other_operating_income",
    "其他收益": "other_operating_income",
    "其他营业收入": "other_operating_income",
    "其他金融资产(流动)": "other_current_assets",
    "其他金融资产(非流动)": "other_non_current_assets",
    "其他非流动资产": "other_non_current_assets",
    "净流动资产": "net_current_assets",
    "净资产": "total_equity",
    "减:出售资产之溢利": "gain_loss_on_disposal",
    "减:利息收入": "interest_income",
    "减:应占附属公司溢利": "equity_method_income",
    "减:汇兑收益": "fx_gain_loss",
    "减:重估盈余": "revaluation_surplus",
    "出售附属公司": "sale_of_subsidiaries",
    "利息收入": "interest_income",
    "加:减值及拨备": "impairment_cf",
    "加:利息支出": "interest_expense",
    "加:折旧及摊销": "depreciation",
    "加:经营调整其他项目": "other_cf_adjustments",
    "加:购股权开支": "sbc",
    "发行债券": "bond_issuance",
    "发行股份": "share_issuance",
    "受限制存款及现金": "cash",
    "可转换可赎回优先股": "other_equity",
    "合营公司权益": "equity_method_investments",
    "吸收投资所得": "proceeds_from_equity",
    "回购股份": "buybacks",
    "固定资产": "ppe",
    "土地使用权": "right_of_use_assets",
    "在建工程": "construction_in_progress",
    "处置固定资产": "sale_of_ppe",
    "存款(增加)减少": "change_in_deposits",
    "存款减少(增加)": "change_in_deposits",
    "存货": "inventories",
    "存货(增加)减少": "change_in_inventory",
    "少数股东损益": "net_income_non_controlling",
    "少数股东权益": "non_controlling_interests",
    "已付利息(经营)": "interest_paid",
    "已付利息(融资)": "interest_paid_fin",
    "已付税项": "income_tax_paid",
    "已付股息(融资)": "dividends_paid",
    "已收利息(投资)": "interest_received",
    "已收股息(投资)": "dividend_received",
    "库存股": "treasury_shares",
    "应付关联方款项(流动)": "other_payables",
    "应付帐款": "payables",
    "应付帐款及应计费用增加(减少)": "change_in_payables",
    "应付票据": "notes_payable",
    "应付税项": "income_tax_payable",
    "应占合营公司溢利": "equity_method_income",
    "应占联营公司溢利": "equity_method_income",
    "应收关联方款项": "other_receivables",
    "应收关联方款项(增加)减少": "change_in_related_party",
    "应收帐款": "receivables",
    "应收帐款减少": "change_in_receivables",
    "总权益": "total_equity",
    "总权益及总负债": "total_assets",
    "总权益及非流动负债": "total_equity_and_ncl",
    "总负债": "total_liabilities",
    "总资产": "total_assets",
    "总资产减流动负债": "net_assets",
    "投资业务其他项目": "other_investing_items",
    "投资业务现金净额": "investing_cf",
    "投资支付现金": "payments_for_investments",
    "投资物业": "investment_properties",
    "拟派股息": "dps",
    "拨备(流动)": "provisions",
    "持作出售的负债(流动)": "other_current_liabilities",
    "持作出售的资产(流动)": "short_term_investments",
    "持续经营业务税后利润": "net_income",
    "收购附属公司": "acquisition_of_subsidiaries",
    "新增借款": "new_borrowings",
    "无形资产": "intangible_assets",
    "期初现金": "cash_beginning",
    "期末现金": "cash_ending",
    "期间变动其他项目": "other_cash_changes",
    "本公司拥有人应占全面收益总额": "total_comprehensive_income_parent",
    "每股基本盈利": "eps_basic",
    "每股摊薄盈利": "eps_diluted",
    "每股股息": "dps",
    "毛利": "gross_profit",
    "流动负债合计": "current_liabilities",
    "流动资产合计": "current_assets",
    "溢利其他项目": "other_profit_items",
    "物业厂房及设备": "ppe",
    "现金净额": "change_in_cash",
    "现金及等价物": "cash",
    "短期存款": "short_term_investments",
    "短期贷款": "short_term_debt",
    "税项": "income_tax",
    "经营业务现金净额": "operating_cf",
    "经营产生现金": "cash_generated_from_operations",
    "经营溢利": "operating_income",
    "职工薪酬及福利(非流动)": "retirement_benefit_liabilities",
    "联营公司权益": "equity_method_investments",
    "股东应占溢利": "net_income",
    "股东权益": "total_equity_parent",
    "股息": "dps",
    "股本": "share_capital",
    "股本溢价": "capital_surplus",
    "营业额": "revenue",
    "营运支出": "cogs",
    "营运收入": "revenue",
    "营运资本变动其他项目": "change_in_working_capital_other",
    "营运资金变动前经营溢利": "operating_profit_before_wc",
    "融资业务其他项目": "other_financing_items",
    "融资业务现金净额": "financing_cf",
    "融资前现金净额": "net_cash_before_financing",
    "融资成本": "interest_expense",
    "融资租赁负债(流动)": "lease_liabilities_current",
    "融资租赁负债(非流动)": "lease_liabilities_non_current",
    "行政开支": "admin_expenses",
    "衍生金融工具-负债": "other_non_current_liabilities",
    "衍生金融工具-负债(流动)": "other_current_liabilities",
    "衍生金融工具-资产": "other_non_current_assets",
    "衍生金融工具-资产(流动)": "short_term_investments",
    "购买子公司少数股权而支付的现金": "acquisition_of_nci",
    "购建固定资产": "capex",
    "购建无形资产及其他资产": "purchase_of_intangibles",
    "赎回债券": "bond_redemption",
    "递延收入(流动)": "contract_liabilities",
    "递延税项负债": "deferred_tax_liabilities",
    "递延税项资产": "deferred_tax_assets",
    "销售及分销费用": "sg_and_a",
    "长期应付款": "other_non_current_liabilities",
    "长期应收款": "other_non_current_assets",
    "长期贷款": "long_term_debt",
    "除税前溢利": "pretax_income",
    "除税前溢利(业务利润)": "profit_before_tax_cf",
    "除税后溢利": "net_income_total",
    "非控股权益应占全面收益总额": "total_comprehensive_income_nci",
    "非流动负债合计": "non_current_liabilities",
    "非流动资产其他项目": "other_non_current_assets",
    "非流动资产合计": "non_current_assets",
    "非运算项目": "elimination_items",
    "预付款按金及其他应收款": "other_receivables",
    "预付款项": "prepayments",
    "预付款项、按金及其他应收款项减少(增加)": "change_in_prepayments",
    "预收款项": "advance_payments",
    "预缴及应收税项": "other_current_assets",

# AKShare HK label count:151 AKShare HK label mappings

    # Korean KR concept names (DART)
    "매출액": "revenue", "영업이익": "operating_income", "당기순이익": "net_income",
    "자산총계": "total_assets", "부채총계": "total_liabilities", "자본총계": "total_equity",
    # HK concept names (AKShare — Traditional Chinese)
    "營業額": "revenue", "营业额": "revenue", "收益": "revenue",
    "營運收入": "revenue", "营运收入": "revenue", "營業收入": "revenue",
    "銷售成本": "cogs", "销售成本": "cogs",
    "毛利": "gross_profit",
    "其他收入": "other_operating_income", "其他收益": "other_operating_income",
    "銷售及分銷費用": "sg_and_a", "销售及分销费用": "sg_and_a",
    "行政開支": "admin_expenses", "行政开支": "admin_expenses",
    "研發費用": "r_and_d", "研发费用": "r_and_d", "研究及開發費用": "r_and_d",
    "出售資產之溢利": "gain_loss_on_disposal",
    "經營溢利": "operating_income", "经营溢利": "operating_income", "經營利潤": "operating_income",
    "其他支出": "other_operating_expenses",
    "應佔合營公司溢利": "equity_method_income", "应佔合营公司溢利": "equity_method_income",
    "持續經營業務稅後利潤": "net_income", "持续经营业务税后利润": "net_income",
    "終止或非持續業務溢利": "net_income_discontinued",
    "除稅後溢利": "net_income_total", "除税后溢利": "net_income_total",
    "少數股東損益": "net_income_non_controlling", "少数股东损益": "net_income_non_controlling",
    "其他全面收益": "other_comprehensive_income",
    "其他全面收益其他項目": "other_comprehensive_income",
    "全面收益總額": "total_comprehensive_income", "全面收益总额": "total_comprehensive_income",
    "非控股權益應佔全面收益總額": "total_comprehensive_income_nci",
    "本公司擁有人應佔全面收益總額": "total_comprehensive_income_parent",
    "非運算項目": "elimination_items", "非运算项目": "elimination_items",
    "溢利其他項目": "other_profit_items",
    "融資成本": "interest_expense", "融资成本": "interest_expense",
    "融資收入": "finance_income", "融资收入": "finance_income",
    "利息收入": "interest_income",
    "利息支出": "interest_expense",
    "應佔聯營公司溢利": "equity_method_income", "应佔联营公司溢利": "equity_method_income",
    "除稅前溢利": "pretax_income", "除税前溢利": "pretax_income", "除稅前利潤": "pretax_income",
    "稅項": "income_tax", "税项": "income_tax", "所得稅開支": "income_tax",
    "股東應佔溢利": "net_income", "股东应佔溢利": "net_income", "股東應佔利潤": "net_income",
    "本公司擁有人應佔溢利": "net_income_parent",
    "非控股權益應佔溢利": "net_income_non_controlling",
    "每股基本盈利": "eps_basic", "每股基本收益": "eps_basic",
    "每股攤薄盈利": "eps_diluted", "每股攤薄收益": "eps_diluted",
    "股息": "dps", "每股股息": "dps",
    "現金及現金等價物": "cash", "现金及现金等价物": "cash", "現金及銀行存款": "cash",
    "存貨": "inventories", "存货": "inventories",
    "應收賬款": "receivables", "应收账款": "receivables", "應收賬款及票據": "receivables",
    "流動資產": "current_assets", "流动资产": "current_assets",
    "物業廠房及設備": "ppe", "物业厂房及设备": "ppe", "固定資產": "ppe",
    "商譽": "goodwill", "商誉": "goodwill",
    "無形資產": "intangible_assets", "无形资产": "intangible_assets",
    "資產總額": "total_assets", "资产总额": "total_assets", "總資產": "total_assets",
    "應付賬款": "payables", "应付账款": "payables", "應付賬": "payables",
    "短期借款": "short_term_debt",
    "長期借款": "long_term_debt",
    "流動負債": "current_liabilities", "流动负债": "current_liabilities",
    "負債總額": "total_liabilities", "负债总额": "total_liabilities", "總負債": "total_liabilities",
    "本公司擁有人應佔權益": "total_equity_parent",
    "非控股權益": "non_controlling_interests", "非控股权益": "non_controlling_interests",
    "權益總額": "total_equity", "权益总额": "total_equity", "總權益": "total_equity",
    "經營活動現金流量": "operating_cf", "经营活动现金流量": "operating_cf",
    "投資活動現金流量": "investing_cf",
    "融資活動現金流量": "financing_cf",
    "資本開支": "capex", "资本开支": "capex", "購置物業廠房設備": "capex",
    "折舊": "depreciation", "折旧": "depreciation", "折舊及攤銷": "depreciation",
    "攤銷": "amortization", "摊销": "amortization",
    "已付股息": "dividends_paid", "已付股利": "dividends_paid",
    "股份回購": "buybacks", "股份回购": "buybacks",
}

# Common SEC US GAAP XBRL concept → standard field mappings
# Complements statement-line-items.md label-based mappings with CamelCase XBRL concepts
_SEC_CONCEPT_MAP = {
    # Income Statement
    "revenues": "revenue",
    "revenuefromcontractwithcustomerincludingassessedtax": "revenue",
    "revenuefromcontractwithcustomerexcludingassessedtax": "revenue",
    "costofgoodsandservicessold": "cogs",
    "costofrevenue": "cogs",
    "costofsales": "cogs",
    "grossprofit": "gross_profit",
    "grossprofit_calculated": "gross_profit",
    "sellinggeneralandadministrativeexpense": "sg_and_a",
    "researchanddevelopmentexpense": "r_and_d",
    "operatingincomeloss": "operating_income",
    "interestexpense": "interest_expense",
    "interestexpensenonoperating": "interest_expense",
    "incometaxexpensebenefit": "income_tax",
    "incomelossfromcontinuingoperationsbeforeincometaxesextraordinaryitemsnoncontrollinginterest": "pre_tax_income",
    "netincomeloss": "net_income",
    "profitloss": "net_income",
    "incomelossfromcontinuingoperations": "net_income",
    "earningspersharebasic": "eps",
    "earningspersharediluted": "eps",
    "incomelossfromcontinuingoperationsperbasicshare": "eps",
    "incomelossfromcontinuingoperationsperdilutedshare": "eps",
    "weightedaveragenumberofsharesoutstandingbasic": "shares_outstanding",
    "weightedaveragenumberofdilutedsharesoutstanding": "shares_outstanding",
    "sharebasedcompensation": "sbc",
# EDINET/DART provider concept mappings (snake_case English → standard)
"net_sales": "revenue",
"total_revenue": "revenue",
"operating_income": "ebit",
"ordinary_income": "ebt",
"net_income": "net_income",
"income_before_taxes": "pre_tax_income",
"non_operating_income": "non_operating_income",
"non_operating_expenses": "non_operating_expenses",
"income_taxes": "income_tax",
"total_assets": "total_assets",
"current_assets": "current_assets",
"noncurrent_assets": "noncurrent_assets",
"cash_and_deposits": "cash",
"property_plant_equipment": "ppe",
"deferred_tax_assets": "deferred_tax_assets",
"total_liabilities": "total_liabilities",
"current_liabilities": "current_liabilities",
"net_assets": "equity",
"retained_earnings": "retained_earnings",
"short_term_loans_payable": "short_term_debt",
"long_term_loans_payable": "long_term_debt",
"bonds_payable": "bonds_payable",
"commercial_paper": "commercial_paper",
"operating_cash_flow": "operating_cf",
"investing_cash_flow": "investing_cf",
"financing_cash_flow": "financing_cf",
"depreciation_amortization": "depreciation",
    "allocatedsharebasedcompensationexpense": "sbc",
    "depreciation": "d_and_a",
    "amortizationofintangibleassets": "amortization",
    "adjustmentforamortization": "d_and_a",
    # Balance Sheet
    "cashandcashequivalentsatcarryingvalue": "cash",
    "accountsreceivablenetcurrent": "accounts_receivable",
    "inventorynet": "inventory",
    "assets": "total_assets",
    "goodwill": "goodwill",
    "intangibleassetsnetexcludinggoodwill": "intangible_assets",
    "propertyplantandequipmentnet": "ppe_net",
    "stockholdersequity": "total_equity",
    "assetscurrent": "total_current_assets",
    "liabilitiescurrent": "total_current_liabilities",
    "liabilities": "total_liabilities",
    "liabilitiesandstockholdersequity": "total_assets",
    "longtermdebt": "long_term_debt",
    "longtermdebtcurrent": "short_term_debt",
    "longtermdebtnoncurrent": "long_term_debt",
    "accountspayablecurrent": "accounts_payable",
    "operatingleaseliabilitycurrent": "short_term_debt",
    "operatingleaseliabilitynoncurrent": "long_term_debt",
    "retainedearningsaccumulateddeficit": "retained_earnings",
    "additionalpaidincapital": "additional_paid_in_capital",
    "commonstockvalue": "common_stock",
    "preferredstockvalue": "preferred_stock",
    # Cash Flow
    "netcashprovidedbyusedinoperatingactivities": "operating_cf",
    "paymentstoacquirepropertyplantandequipment": "capex",
    "paymentsforrepurchaseofcommonstock": "buybacks",
    "paymentsrelatedtotaxwithholdingforsharebasedcompensation": "buybacks",
    "netcashprovidedbyusedininvestingactivities": "investing_cf",
    "netcashprovidedbyusedinfinancingactivities": "financing_cf",
    "paymentstoacquirebusinessesnetofcashacquired": "acquisitions",
    "interestpaidnet": "interest_expense",
    "incometaxespaidnet": "income_tax_paid",
    "cashcashequivalentsrestrictedcashandrestrictedcashequivalentsperiodincreasedecreaseincludingexchangerateeffect": "change_in_cash",
    "cashcashequivalentsrestrictedcashandrestrictedcashequivalents": "cash",
    # Supplementary
    "increasedecreaseinaccountsreceivable": "accounts_receivable",
    "increasedecreaseininventories": "inventory",
    "increasedecreaseinaccountspayable": "accounts_payable",
}


def _load_concept_map(workspace: Path = None) -> dict[str, str]:
    """Parse statement-line-items.md → {concept_alias: standard_field}.

    Dynamically builds a mapping from XBRL concepts, local-language labels,
    and variant names to standard LITE_FIELDS-compatible field names.
    Cached globally after first call.
    """
    global _concept_map_cache
    if _concept_map_cache is not None:
        return _concept_map_cache

    if workspace is None:
        try:
            workspace = discover_workspace()
        except RuntimeError:
            _concept_map_cache = {}
            return {}

    template = workspace / ".references" / "policy" / "statement-line-items.md"
    if not template.exists():
        template = workspace / "references" / "policy" / "statement-line-items.md"
    if not template.exists():
        _concept_map_cache = {}
        return {}

    text = template.read_text(encoding="utf-8")
    mapping = {}

    # Parse each table row. Column indices: 1=标准科目, 3=US, 4=CN, 5=HK, 6=JP, 7=KR
    for line in text.split("\n"):
        if not line.startswith("|") or "---" in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 5:
            continue

        # Derive standard field name from column 1
        col1 = cols[1].strip()
        raw_name = col1.lower()
        raw_name = raw_name.replace(" ", "_").replace("/", "_")
        raw_name = raw_name.replace("(", "").replace(")", "").replace(".", "")
        if not raw_name or raw_name in ("?", "—", "数据点", "符号", "标记", "科目"):
            continue

        std_name = _FIELD_ALIASES.get(raw_name)
        if std_name is None:
            # Try stripping parenthetical (e.g. "Total Equity (Parent)" → "Total Equity")
            base = re.sub(r'\([^)]*\)', '', col1).strip().lower()
            base = base.replace(" ", "_").replace("/", "_").replace(".", "")
            std_name = _FIELD_ALIASES.get(base, raw_name)

        # Extract all language-specific labels and map them to std_name
        for col_idx in (3, 4, 5, 6, 7):
            if col_idx >= len(cols):
                continue
            cell = cols[col_idx].strip()
            if not cell or cell == "—":
                continue
            # Split on "/" and "or" for multiple label variants in one cell
            parts = re.split(r'\s*/\s*|\s+or\s+', cell)
            for part in parts:
                key = part.strip().lower()
                # Normalize: remove spaces, special chars; keep alphanumeric + CJK
                key = re.sub(r'[^a-z0-9一-鿿぀-ゟ゠-ヿ가-힯]', '', key)
                if key and len(key) >= 2:
                    mapping.setdefault(key, std_name)

    # Add FIELD_ALIASES keys as direct mappings (covers fields not in statement-line-items.md)
    for alias, std_name in _FIELD_ALIASES.items():
        mapping.setdefault(alias, std_name)

    # Add SEC/EDINET/DART concept mappings (override FIELD_ALIASES identity mappings)
    for concept, std_name in _SEC_CONCEPT_MAP.items():
        mapping[concept] = std_name

    _concept_map_cache = mapping
    return mapping


def _map_concept(concept: str, concept_map: dict = None) -> str:
    """Map a provider concept/label to standard field name.

    Examples:
        'Revenues' → 'revenue'
        'SellingGeneralAndAdministrativeExpense' → 'sg_and_a'
        '売上高' → 'revenue' (JP label)
        '매출' → 'revenue' (KR label)
    """
    if concept_map is None:
        concept_map = _concept_map_cache or {}

    if not concept or not isinstance(concept, str):
        return concept.lower().replace(" ", "_") if concept else ""

    # _FIELD_ALIASES first — direct label→standard mapping wins over concept_map
    lower_concept = concept.lower()
    if lower_concept in _FIELD_ALIASES:
        return _FIELD_ALIASES[lower_concept]

    # Try raw concept first (provider concepts like net_sales, operating_income)
    raw_key = concept.lower()
    if raw_key in concept_map:
        return concept_map[raw_key]

    # Normalize: lowercase, remove spaces and underscores
    key = concept.lower().replace(" ", "").replace("_", "")

    # Direct lookup
    if key in concept_map:
        return concept_map[key]

    # Try stripping trailing 's' (plural → singular: Revenues → Revenue)
    if key.endswith('s') and len(key) > 3:
        key_singular = key[:-1]
        if key_singular in concept_map:
            return concept_map[key_singular]

    # Fuzzy lookup: strip common XBRL concept suffixes
    key_clean = re.sub(
        r'(calculated|usd|atcarryingvalue|net|current|noncurrent|'
        r'afterallowance|forcreditloss|parent|attributableto|'
        r'fromcontractwithcustomer|abstract|member|'
        r'total|segment)$', '', key
    )
    if key_clean and key_clean != key:
        if key_clean in concept_map:
            return concept_map[key_clean]
        # Try again with trailing 's' stripped from cleaned key
        if key_clean.endswith('s') and len(key_clean) > 3:
            if key_clean[:-1] in concept_map:
                return concept_map[key_clean[:-1]]

    # Last resort: return normalized concept name
    return concept.lower().replace(" ", "_").replace("/", "_")


# ---------------------------------------------------------------------------
# Consumer helper: filter statements to lite/full field sets
# ---------------------------------------------------------------------------
def get_fields(statements: dict, mode: str = "lite") -> dict:
    """Pass-through: all fields are kept regardless of mode.

    Previously filtered to LITE_FIELDS / FULL_EXTRA_FIELDS sets.
    Now: extract everything. Mode only affects period depth (lite=latest, full=5Y).
    Field schema is in .references/policy/statement-line-items.md.
    """
    return statements


PROVIDER_MODULES = {
    "us": "sec_provider",
    "cn": "akshare_provider",
    "hk": "akshare_provider",
    "jp": "edinet_provider",
    "kr": "dart_provider",
    "tw": "finmind_provider",
    "eu": "openesef_provider",
}

IR_MARKETS = {"jp", "kr", "tw", "eu", "se", "fr", "de", "uk", "sg", "my", "in", "au"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return value.strip("-") or "unknown"


# Map internal market codes to yfinance ticker suffixes
_YF_SUFFIX = {
    "hk": "HK", "sh": "SS", "sz": "SZ",
    "jp": "T", "kr": "KS", "tw": "TW", "sg": "SI",
    "se": "ST", "fr": "PA", "de": "DE", "uk": "L",
    "my": "KL", "in": "NS", "au": "AX",
}


def _yf_ticker(identifier: str, market: str) -> str:
    suffix = _YF_SUFFIX.get(market.lower(), "")
    if suffix and not identifier.upper().endswith(f".{suffix}"):
        return f"{identifier}.{suffix}"
    return identifier


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def dependency_matrix() -> dict[str, Any]:
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "packages": {
            "edgartools": {"available": module_available("edgar"), "install_hint": "pip install edgartools"},
            "akshare": {"available": module_available("akshare"), "install_hint": "pip install akshare"},
            "finmind": {"available": True, "install_hint": "uses FinMind public HTTP API; no package required"},
            "edinet-tools": {"available": module_available("edinet_tools"), "install_hint": "pip install edinet-tools"},
            "dart-fss": {"available": module_available("dart_fss"), "install_hint": "pip install dart-fss"},
            "openesef": {"available": module_available("openesef"), "install_hint": "pip install openesef"},
        },
        "env": {
            "EDGAR_IDENTITY": {"configured": bool(os.getenv("EDGAR_IDENTITY"))},
            "DART_API_KEY": {"configured": bool(os.getenv("DART_API_KEY"))},
            "EDINET_API_KEY": {"configured": bool(os.getenv("EDINET_API_KEY"))},
            "FINMIND_TOKEN": {"configured": bool(os.getenv("FINMIND_TOKEN")), "required": False},
        },
    }


def discover_workspace(source: Path | None = None) -> Path:
    candidates = [source or Path.cwd(), Path.cwd()]
    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in [current, *current.parents]:
            if (parent / "industry").is_dir():
                return parent
    raise RuntimeError("Could not discover workspace. Pass --workspace or run init-workspace first.")


def ensure_company_topic(workspace: Path, company_slug: str, industry_slug: str = "",
                         ticker: str = "", market: str = "") -> Path:
    """Find or create company directory under industry/*/companies/.

    Uses <TICKER.MARKET>-<Company-Name> format when ticker+market provided.
    Falls back to company_slug for backward compat.
    """
    industry_dir = workspace / "industry"

    # Determine company directory name
    if ticker and market:
        suffix = _YF_SUFFIX.get(market.lower(), market.upper())
        dir_name = f"{ticker.split('.')[0]}.{suffix}-{company_slug}"
    else:
        dir_name = company_slug

    # Search existing dirs first
    if industry_dir.is_dir():
        for ind in industry_dir.iterdir():
            if not ind.is_dir():
                continue
            tp = ind / "companies" / dir_name
            if tp.is_dir():
                return tp
            # Also search by company_slug for existing dirs
            tp2 = ind / "companies" / company_slug
            if tp2.is_dir():
                return tp2

    # Auto-create under specified industry (match case of existing dir)
    if not industry_slug:
        raise RuntimeError(
            f"Company directory not found for {company_slug}. "
            f"Pass --industry <slug> to auto-create under that industry."
        )
    # Find existing industry dir with matching name (case-insensitive)
    target_ind = industry_dir / industry_slug
    if industry_dir.is_dir():
        for ind in industry_dir.iterdir():
            if ind.is_dir() and ind.name.lower() == industry_slug.lower():
                target_ind = ind
                break
    company_dir = target_ind / "companies" / dir_name
    company_dir.mkdir(parents=True, exist_ok=True)
    return company_dir


def load_provider(market: str):
    pdir = Path(__file__).resolve().parent / "providers"
    if str(pdir) not in sys.path:
        sys.path.insert(0, str(pdir))
    mn = PROVIDER_MODULES.get(market)
    if not mn:
        raise RuntimeError(f"Unsupported market: {market}")
    return importlib.import_module(mn)


# ---------------------------------------------------------------------------
# Central normalizer
# ---------------------------------------------------------------------------
CONFIDENCE_ORDER = {"model-ready": 0, "evidence-ready": 1, "provider-normalized-review": 2, "partial": 3, "provider-gap": 4, "unavailable": 5, "failed": 5}


def _safe_json_dump(data, path: Path):
    """Write JSON with Unicode minus → ASCII hyphen normalization (#13)."""
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    text = text.replace("−", "-")  # Unicode minus sign
    path.write_text(text + "\n", encoding="utf-8")

# Policy: providers must fail honestly (provider_gap) when dependencies, credentials,
# or market coverage are missing rather than returning empty partial results.

DEFAULT_ITEMS_REQUIRE = (
    "identity",
    "filing_index",
    "latest_full_filing",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "revenue_split",
)


def normalize_result(provider_result: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Central normalizer: standardize provider output into the canonical pack format."""
    provider = provider_result.get("provider", "unknown")
    provider_status = provider_result.get("status", "provider-gap")

    company = provider_result.get("company", {})
    financials_raw = {}
    for key in FINANCIAL_OUTPUT_KEYS:
        val = provider_result.get(key)
        if val:
            financials_raw[key] = val
    financials_raw = filter_financials_by_period(financials_raw, request.get("periods", "latest"))

    filing_info = provider_result.get("filing", {}) or {}
    errors = list(provider_result.get("errors", []))
    data_gaps = list(provider_result.get("data_gaps", []))
    provider_timing = provider_result.get("provider_timing", {}) or {}
    gap_by_item = {
        str(gap).split(":", 1)[0].strip(): str(gap).split(":", 1)[1].strip()
        for gap in data_gaps
        if ":" in str(gap)
    }
    provider_error = provider_result.get("error")
    if provider_error:
        errors.append(str(provider_error))

    # Build completeness from what was actually extracted
    declared_extracted = provider_result.get("items_extracted", request.get("items", []))
    extracted = [item for item in declared_extracted if item_materialized(item, provider_result, financials_raw)]
    requested_items = request.get("items", [])
    completeness_items = []
    for item in DEFAULT_ITEMS_REQUIRE:
        if item in extracted:
            status_c = confidence_determine(item, provider_result)
        elif item in requested_items:
            status_c = "provider-gap"
        else:
            status_c = "unavailable"
        completeness_items.append({
            "data_item": item, "status": status_c,
            "source_provider": provider, "period_coverage": request.get("periods", "latest"),
            "model_usable": status_c,
            "caveat": gap_by_item.get(item, ""),
        })

    status = derive_pack_status(provider_status, requested_items, extracted, errors)

    return {
        "provider": provider,
        "status": status,
        "provider_status": provider_status,
        "company": company,
        "financials_raw": financials_raw,
        "filing": filing_info,
        "completeness": completeness_items,
        "errors": errors,
        "data_gaps": data_gaps,
        "provider_timing": provider_timing,
        "items_extracted": extracted,
        "provider_payload": provider_result,
    }


def filter_financials_by_period(financials: dict[str, Any], periods: str | None) -> dict[str, Any]:
    if not financials or not periods or periods in ("latest", "5Y"):
        # latest: keep all periods (agent picks last FY+Q)
        # 5Y: keep all periods (agent picks 5FY+4Q for modeling)
        return financials

    if is_latest4q_period_filter(str(periods)):
        return filter_financials_latest_periods(financials, max_periods=4)

    allowed_years = parse_fiscal_year_filter(str(periods))
    if not allowed_years:
        return financials

    filtered: dict[str, Any] = {}
    for statement, rows in financials.items():
        kept_rows = []
        for row in rows:
            values = row.get("values", {}) if isinstance(row, dict) else {}
            kept_values = {
                period: value
                for period, value in values.items()
                if fiscal_year_from_label(period) in allowed_years
            }
            if kept_values:
                kept = dict(row)
                kept["values"] = kept_values
                if isinstance(row.get("metrics"), dict):
                    kept["metrics"] = {
                        period: metrics
                        for period, metrics in row.get("metrics", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("source_periods"), dict):
                    kept["source_periods"] = {
                        period: sources
                        for period, sources in row.get("source_periods", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("cumulative_values"), dict):
                    kept["cumulative_values"] = {
                        period: value
                        for period, value in row.get("cumulative_values", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("period_basis_by_period"), dict):
                    kept["period_basis_by_period"] = {
                        period: basis
                        for period, basis in row.get("period_basis_by_period", {}).items()
                        if period in kept_values
                    }
                kept_rows.append(kept)
        filtered[statement] = kept_rows
    return filtered


def is_latest4q_period_filter(periods: str | None) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


def filter_financials_latest_periods(financials: dict[str, Any], max_periods: int = 4) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for statement, rows in financials.items():
        periods = sorted(
            {
                str(period)
                for row in rows
                if isinstance(row, dict)
                for period in (row.get("values", {}) or {}).keys()
            },
            key=period_sort_key,
            reverse=True,
        )[:max_periods]
        allowed = set(periods)
        kept_rows = []
        for row in rows:
            values = row.get("values", {}) if isinstance(row, dict) else {}
            kept_values = {
                period: value
                for period, value in values.items()
                if str(period) in allowed
            }
            if kept_values:
                kept = dict(row)
                kept["values"] = kept_values
                if isinstance(row.get("metrics"), dict):
                    kept["metrics"] = {
                        period: metrics
                        for period, metrics in row.get("metrics", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("source_periods"), dict):
                    kept["source_periods"] = {
                        period: sources
                        for period, sources in row.get("source_periods", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("cumulative_values"), dict):
                    kept["cumulative_values"] = {
                        period: value
                        for period, value in row.get("cumulative_values", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("period_basis_by_period"), dict):
                    kept["period_basis_by_period"] = {
                        period: basis
                        for period, basis in row.get("period_basis_by_period", {}).items()
                        if str(period) in allowed
                    }
                kept_rows.append(kept)
        filtered[statement] = kept_rows
    return filtered


def period_sort_key(label: Any) -> tuple[int, int, int, int, str]:
    """Sort period labels from multiple providers without inventing periods."""
    text = str(label or "").strip()
    date_match = re.search(r"(20\d{2}|19\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if date_match:
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        quarter = max(1, min(4, (month - 1) // 3 + 1))
        return (year, quarter, month, day, text)

    year_match = re.search(r"(20\d{2}|19\d{2})", text)
    year = int(year_match.group(1)) if year_match else 0
    quarter = 4
    month = 12
    day = 31

    q_match = re.search(r"[Qq]([1-4])", text)
    if q_match:
        quarter = int(q_match.group(1))
        month = quarter * 3
        day = 31 if quarter in {1, 4} else 30
    elif re.search(r"[Hh]1|中报|半年|半期|二季|第二季", text):
        quarter, month, day = 2, 6, 30
    elif re.search(r"[Hh]2", text):
        quarter, month, day = 4, 12, 31
    elif re.search(r"一季|第一季", text):
        quarter, month, day = 1, 3, 31
    elif re.search(r"三季|第三季", text):
        quarter, month, day = 3, 9, 30
    elif re.search(r"年报|年度|annual|FY", text, flags=re.IGNORECASE):
        quarter, month, day = 4, 12, 31

    return (year, quarter, month, day, text)


def parse_fiscal_year_filter(periods: str) -> set[int]:
    years = [int(year) for year in re.findall(r"FY\s*(20\d{2}|19\d{2})", periods, flags=re.IGNORECASE)]
    if not years:
        years = [int(year) for year in re.findall(r"\b(20\d{2}|19\d{2})\b", periods)]
    if not years:
        return set()
    if len(years) >= 2:
        start, end = min(years[0], years[-1]), max(years[0], years[-1])
        return set(range(start, end + 1))
    return {years[0]}


def fiscal_year_from_label(label: str) -> int | None:
    match = re.search(r"(20\d{2}|19\d{2})", str(label))
    if not match:
        return None
    return int(match.group(1))


def item_materialized(item: str, provider_result: dict[str, Any],
                      financials_raw: dict[str, Any] | None = None) -> bool:
    """Return true only when a declared extracted item has real payload behind it."""
    if item == "identity":
        return bool(provider_result.get("company"))
    if item == "filing_index":
        filing = provider_result.get("filing", {}) or {}
        filing_documents = provider_result.get("filing_documents") or []
        return (bool(filing) and filing.get("status") != "error") or bool(filing_documents)
    if item == "latest_full_filing":
        filing = provider_result.get("filing", {}) or {}
        return bool(filing.get("markdown"))
    if item in ("income_statement", "balance_sheet", "cash_flow", "revenue_split"):
        if financials_raw is not None:
            return bool(financials_raw.get(item))
        return bool(provider_result.get(item))
    return False


def confidence_determine(item: str, provider_result: dict[str, Any]) -> str:
    """Return the canonical confidence/status tier for a materialized item."""
    provider = provider_result.get("provider", "")
    if provider in THIRD_PARTY_PROVIDERS:
        return "provider-normalized-review"
    if provider in OFFICIAL_EVIDENCE_PROVIDERS and item in ("identity", "filing_index", "latest_full_filing"):
        return "evidence-ready"
    if item == "revenue_split":
        return provider_result.get("revenue_split_completeness_status", "available-review") if provider_result.get(item) else "provider-gap"
    if item in ("income_statement", "balance_sheet", "cash_flow"):
        return "model-ready" if provider_result.get(item) else "provider-gap"
    return "provider-gap"


def derive_pack_status(provider_status: str, requested_items: list[str],
                       extracted_items: list[str], errors: list[str]) -> str:
    """Derive truthful top-level pack status from materialized outputs, not provider optimism."""
    if provider_status in {"dependency-gap", "credential-gap", "failed"}:
        return provider_status

    extracted = set(extracted_items)
    if not extracted:
        return "provider-gap"

    requested = set(requested_items)
    non_identity_requested = requested - {"identity"}
    non_identity_extracted = extracted - {"identity"}

    if provider_status == "partial":
        return "partial"
    if errors:
        return "partial"
    if non_identity_requested and not non_identity_extracted:
        return "partial"
    return "success"


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def build_financials_markdown(financials: dict[str, Any]) -> str:
    lines = ["# Financial Data Evidence Pack", "", "## Income Statement", ""]
    for row in financials.get("income_statement", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    lines.extend(["", "## Balance Sheet", ""])
    for row in financials.get("balance_sheet", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    lines.extend(["", "## Cash Flow", ""])
    for row in financials.get("cash_flow", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    lines.extend(["", "## Revenue Split", ""])
    split_rows = financials.get("revenue_split", [])
    if split_rows:
        for row in split_rows:
            lbl = row.get("label", "")
            split_type = row.get("split_type", "")
            vals = row.get("values", {})
            if vals:
                periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
                prefix = f"{split_type} / " if split_type else ""
                lines.append(f"- {prefix}{lbl}: {periods_str}")
    else:
        lines.append("- No structured revenue split extracted.")
    derived_sections = [
        ("income_statement_quarterly_derived", "Income Statement - Quarter-Only Derived"),
        ("cash_flow_quarterly_derived", "Cash Flow - Quarter-Only Derived"),
    ]
    for key, title in derived_sections:
        rows = financials.get(key, [])
        if not rows:
            continue
        lines.extend(["", f"## {title}", "", "_Derived from cumulative OpenDART reporting periods; original cumulative statements are retained._", ""])
        for row in rows:
            lbl = row.get("label", "")
            vals = row.get("values", {})
            if vals:
                periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
                lines.append(f"- {lbl}: {periods_str}")
    return "\n".join(lines)


def period_basis_summary(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        basis_by_period = row.get("period_basis_by_period", {}) if isinstance(row, dict) else {}
        if not isinstance(basis_by_period, dict):
            continue
        for basis in basis_by_period.values():
            key = str(basis or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return ", ".join(f"{basis}={count}" for basis, count in sorted(counts.items()))


def build_financial_data_summary(evidence_pack: dict[str, Any],
                                 actuals_resolved: dict[str, Any],
                                 out_dir: Path) -> str:
    """Build the single public Markdown entry for financial-data outputs."""
    manifest = evidence_pack.get("manifest", {})
    identity = evidence_pack.get("identity", {})
    filing = evidence_pack.get("filing", {})
    completeness = evidence_pack.get("completeness", [])
    cross_check = evidence_pack.get("cross_check", {})
    statements = actuals_resolved.get("statements", {}) or {}
    company_name = identity.get("name") or identity.get("company_name") or manifest.get("company_slug", "unknown")
    ticker = identity.get("ticker") or manifest.get("identifier", "")
    status = cross_check.get("status") or manifest.get("status", "unknown")

    lines = [
        f"# {company_name} Financial Data Summary",
        "",
        "**Conclusion**",
        "",
        f"- Status: `{status}`",
        f"- Market / identifier: `{manifest.get('market', 'unknown')}` / `{manifest.get('identifier', ticker)}`",
        f"- Provider: `{manifest.get('provider', evidence_pack.get('source_provider', 'unknown'))}`",
        f"- Period filter: `{manifest.get('periods', 'latest')}`",
        f"- Latest run cache: `{evidence_pack.get('latest_run_cache_path', '')}`",
        f"- Machine data: `.cache/financial-data/`",
        "",
        "## Filing",
        "",
        f"- Filing status: `{filing.get('status', 'unavailable')}`",
        f"- Filing date: `{filing.get('filing_date') or ''}`",
        f"- Accession / document id: `{filing.get('accession_number') or filing.get('document_id') or ''}`",
        f"- Full filing: `full-filing.md` ({'available' if filing.get('has_full_filing_markdown') else 'unavailable'})",
        "",
        "## Completeness Matrix",
        "",
        "| Data item | Status | Provider | Period coverage | Model usable | Caveat |",
        "|---|---|---|---|---|---|",
    ]
    for item in completeness:
        lines.append(
            "| {data_item} | {status} | {source_provider} | {period_coverage} | {model_usable} | {caveat} |".format(
                data_item=item.get("data_item", ""),
                status=item.get("status", ""),
                source_provider=item.get("source_provider", ""),
                period_coverage=item.get("period_coverage", ""),
                model_usable=item.get("model_usable", ""),
                caveat=item.get("caveat", ""),
            )
        )

    lines.extend(["", "## Structured Actuals", ""])
    if statements:
        for statement in FINANCIAL_OUTPUT_KEYS:
            rows = statements.get(statement, [])
            periods = sorted({
                period
                for row in rows
                for period in (row.get("values", {}) if isinstance(row, dict) else {}).keys()
            })
            basis = period_basis_summary(rows)
            basis_text = f"; period basis: {basis}" if basis else ""
            lines.append(f"- `{statement}`: {len(rows)} rows; periods: {', '.join(periods) if periods else 'none'}{basis_text}")
        derived_rows = {
            key: statements.get(key, [])
            for key in ("income_statement_quarterly_derived", "cash_flow_quarterly_derived")
            if statements.get(key)
        }
        if derived_rows:
            lines.extend(["", "## Derived Quarter-Only KR Flow Statements", ""])
            lines.append("- OpenDART Q1/H1/Q3/FY flow statements can be cumulative; original cumulative rows are retained.")
            lines.append("- Derived rows are calculated as `Q1 = Q1`, `Q2 = H1 - Q1`, `Q3 = Q3_YTD - H1`, `Q4 = FY - Q3_YTD`.")
            lines.append("- Balance sheet is not derived because it is a point-in-time statement.")
            for statement, rows in derived_rows.items():
                periods = sorted({
                    period
                    for row in rows
                    for period in (row.get("values", {}) if isinstance(row, dict) else {}).keys()
                })
                lines.append(f"- `{statement}`: {len(rows)} rows; derived periods: {', '.join(periods) if periods else 'none'}")
    else:
        lines.append("- No structured statement rows were materialized.")

    unmapped = actuals_resolved.get("unmapped_items", [])
    lines.extend(["", "## Model Input Policy", ""])
    lines.append("- Public surface is Markdown-only: this summary is the default file for humans and LLMs.")
    lines.append("- Machine inputs are under `.cache/financial-data/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.")
    lines.append("- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.")
    if unmapped:
        lines.append("- Unmapped / unavailable items:")
        for item in unmapped:
            lines.append(f"  - `{item.get('data_item')}`: `{item.get('status')}`")
    else:
        lines.append("- No unavailable default core items were reported.")

    if cross_check.get("errors"):
        lines.extend(["", "## Errors / Caveats", ""])
        for err in cross_check.get("errors", []):
            lines.append(f"- {err}")
    if cross_check.get("data_gaps"):
        if not cross_check.get("errors"):
            lines.extend(["", "## Errors / Caveats", ""])
        for gap in cross_check.get("data_gaps", []):
            lines.append(f"- {gap}")

    return "\n".join(lines) + "\n"


def chunk_full_filing(text: str, max_chars: int = 12000) -> list[dict[str, Any]]:
    """Split full filing text into overlapping chunks for retrieval."""
    chunks = []
    for i, start in enumerate(range(0, len(text), max_chars)):
        chunk_text = text[start:start + max_chars]
        chunks.append({
            "chunk_id": f"chunk_{i:04d}",
            "start_char": start,
            "end_char": start + len(chunk_text),
            "length": len(chunk_text),
            "content": chunk_text,
        })
    return chunks


# ---------------------------------------------------------------------------
# Source-map builder
# ---------------------------------------------------------------------------
def _build_source_map(provider: str, filing: dict, financials: dict,
                      completeness: list[dict[str, Any]]) -> dict:
    """Build source-map.json tracing each data dimension to its source."""
    entries = []
    completeness_by_item = {item["data_item"]: item for item in completeness}
    filing_source_id = _source_id_from_filing(filing)
    filing_url = filing.get("filing_url") or filing.get("source_url") if filing else ""

    # Filing-level source
    if filing and filing.get("status") != "error":
        entries.append({
            "data_item": "filing_index",
            "provider": provider,
            "source_id": filing_source_id,
            "filing_date": filing.get("filing_date", ""),
            "filing_url": filing_url,
            "confidence": completeness_by_item.get("filing_index", {}).get("status", "provider-gap"),
        })
        if filing.get("markdown"):
            entries.append({
                "data_item": "latest_full_filing",
                "provider": provider,
                "source_id": filing_source_id,
                "sha256": filing.get("markdown_sha256", ""),
                "source_package_type": filing.get("source_package_type", ""),
                "source_url": filing_url,
                "confidence": completeness_by_item.get("latest_full_filing", {}).get("status", "provider-gap"),
            })

    # Statement-level source
    for stmt_type in FINANCIAL_OUTPUT_KEYS:
        rows = financials.get(stmt_type, [])
        first_row = rows[0] if rows else {}
        entry = {
            "data_item": stmt_type,
            "provider": provider,
            "record_count": len(rows),
            "confidence": completeness_by_item.get(stmt_type, {}).get("status", first_row.get("confidence", "provider-gap")),
        }
        if rows:
            entry["source_id"] = filing_source_id
            if first_row.get("source_type"):
                entry["source_type"] = first_row.get("source_type")
            if first_row.get("derivation"):
                entry["derivation"] = first_row.get("derivation")
            if stmt_type == "revenue_split":
                entry["concepts"] = sorted({
                    str(row.get("concept"))
                    for row in rows
                    if isinstance(row, dict) and row.get("concept")
                })
                entry["axes"] = sorted({
                    str(row.get("axis"))
                    for row in rows
                    if isinstance(row, dict) and row.get("axis")
                })
                entry["members_sample"] = sorted({
                    str(row.get("member") or row.get("label"))
                    for row in rows[:25]
                    if isinstance(row, dict) and (row.get("member") or row.get("label"))
                })
                entry["split_types"] = sorted({
                    str(row.get("split_type"))
                    for row in rows
                    if isinstance(row, dict) and row.get("split_type")
                })
                entry["axis_count"] = len(entry["axes"])
                entry["extraction_methods"] = sorted({
                    str(row.get("extraction_method"))
                    for row in rows
                    if isinstance(row, dict) and row.get("extraction_method")
                })
                entry["model_bucket_hints"] = sorted({
                    str(row.get("model_bucket_hint"))
                    for row in rows
                    if isinstance(row, dict) and row.get("model_bucket_hint")
                })
                entry["review_required"] = any(
                    bool(row.get("review_required"))
                    for row in rows
                    if isinstance(row, dict)
                )
                reconciliation_statuses = sorted({
                    str(row.get("reconciliation_status") or row.get("axis_completeness_status"))
                    for row in rows
                    if isinstance(row, dict) and (row.get("reconciliation_status") or row.get("axis_completeness_status"))
                })
                if reconciliation_statuses:
                    entry["reconciliation_statuses"] = reconciliation_statuses
                    entry["reconciliation_status"] = (
                        "partial-review" if "partial-review" in reconciliation_statuses
                        else "unreconciled-review" if "unreconciled-review" in reconciliation_statuses
                        else reconciliation_statuses[0]
                    )
                if first_row.get("completeness_status"):
                    entry["revenue_split_completeness_status"] = first_row.get("completeness_status")
        entries.append(entry)

    return {"entries": entries, "source_provider": provider}


def _source_id_from_filing(filing: dict | None) -> str:
    if not filing:
        return ""
    for key in ("accession_number", "document_id", "doc_id", "rcept_no", "edinet_code", "corp_code", "source_sha256", "markdown_sha256"):
        value = filing.get(key)
        if value:
            return str(value)
    return ""


# ---------------------------------------------------------------------------
# Canonical pack writer
# ---------------------------------------------------------------------------
def write_canonical_pack(args: argparse.Namespace, normalized: dict[str, Any],
                         workspace: Path, rid: str) -> dict[str, Any]:
    company_slug = slugify(args.company_slug)
    canonical_id = slugify(args.canonical_id or args.identifier)
    topic_path = ensure_company_topic(workspace, company_slug, getattr(args, 'industry', '') or '',
                                      ticker=args.identifier, market=args.market)
    rel_tail = Path("financial-data") / args.market / canonical_id / rid
    raw_dir = topic_path / ".raw" / rel_tail
    cache_dir = topic_path / ".cache" / rel_tail
    raw_dir.mkdir(parents=True, exist_ok=False)
    cache_dir.mkdir(parents=True, exist_ok=False)

    provider = normalized["provider"]
    status = normalized["status"]
    company = normalized["company"]
    financials = normalized["financials_raw"]
    filing = normalized["filing"]

    # _raw output
    write_json(raw_dir / "provider_payload.json", normalized["provider_payload"])
    write_raw_evidence_pack(raw_dir, provider, company, filing)

    # _cache output
    manifest = {
        "schema_version": 2, "generated_at_utc": utc_now(), "run_id": rid,
        "output_scope": args.output_scope, "market": args.market,
        "identifier": args.identifier, "identifier_type": args.identifier_type,
        "company_slug": args.company_slug, "canonical_id": canonical_id,
        "periods": args.periods, "mode": getattr(args, "mode", "latest_core"),
        "provider": provider, "provider_status": normalized["provider_status"], "status": status,
    }
    identity_payload = company if company else {"identifier": args.identifier, "ticker": args.identifier}
    write_json(cache_dir / "manifest.json", manifest)
    write_json(cache_dir / "identity.json", identity_payload)

    filing_md = ""
    if filing and filing.get("status") != "error":
        write_json(cache_dir / "filing-index.json", filing)
        filing_md = filing.get("markdown", "")
        if filing_md:
            chunks = chunk_full_filing(filing_md)
            write_jsonl(cache_dir / "full-filing.chunks.jsonl", chunks)
            write_json(cache_dir / "full-filing.index.json", {
                "source": filing.get("source_url"),
                "total_chars": len(filing_md),
                "num_chunks": len(chunks),
                "chunk_size": 12000,
            })

    if financials:
        write_json(cache_dir / "financials.normalized.json", financials)
        write_md(cache_dir / "financials.md", build_financials_markdown(financials))
    else:
        write_json(cache_dir / "financials.normalized.json", [])
        write_md(cache_dir / "financials.md", "# No structured financials extracted.\n")

    write_json(cache_dir / "completeness.json", {"items": normalized["completeness"], "status": status})
    cross_check = {
        "status": status,
        "provider_status": normalized["provider_status"],
        "errors": normalized["errors"],
        "data_gaps": normalized.get("data_gaps", []),
        "provider_timing": normalized.get("provider_timing", {}),
        "items_extracted": normalized["items_extracted"],
    }
    write_json(cache_dir / "cross-check.json", cross_check)
    source_map = _build_source_map(provider, filing, financials, normalized["completeness"])
    write_json(cache_dir / "source-map.json", source_map)

    write_consumer_outputs(
        topic_path=topic_path,
        raw_dir=raw_dir,
        cache_dir=cache_dir,
        manifest=manifest,
        identity=identity_payload,
        filing=filing,
        filing_md=filing_md,
        financials=financials,
        completeness=normalized["completeness"],
        source_map=source_map,
        cross_check=cross_check,
    )

    # Cleanup: raw financial-data no longer needed after cache is written
    raw_fin = topic_path / ".raw" / "financial-data"
    if raw_fin.is_dir():
        try:
            import shutil
            shutil.rmtree(raw_fin)
        except OSError:
            pass

    return {
        "raw": str(raw_dir), "cache": str(cache_dir),
        "financial_data_pack_path": str(cache_dir),
        "financial_data_summary_path": str(topic_path / ".cache" / "financial-data" / "summary.md"),
        "financial_data_dir": str(topic_path / ".cache" / "financial-data"),
    }


def write_consumer_outputs(topic_path: Path, cache_dir: Path, manifest: dict[str, Any],
                           raw_dir: Path,
                           identity: dict[str, Any], filing: dict[str, Any],
                           filing_md: str, financials: dict[str, Any],
                           completeness: list[dict[str, Any]] | None = None,
                           source_map: dict[str, Any] | None = None,
                           cross_check: dict[str, Any] | None = None) -> None:
    """Write consumer-facing files to .cache/financial-data/.

    Only 4 files: evidence-pack.json (audit pointer), actuals-resolved.json
    (what all consumer skills read), full-filing.md (latest filing full text),
    and summary.md (human entry point).

    Versioned run outputs live under .cache/financial-data/<market>/<id>/<run_id>/.
    Raw evidence lives under .raw/financial-data/<market>/<id>/<run_id>/.
    """
    out_dir = topic_path / ".cache" / "financial-data"
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_pack = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "latest_run_cache_path": str(cache_dir),
        "latest_raw_evidence_path": str(raw_dir),
        "manifest": manifest,
        "identity": identity,
        "filing": {
            "status": filing.get("status", "unavailable") if filing else "unavailable",
            "accession_number": filing.get("accession_number") if filing else None,
            "document_id": filing.get("document_id") if filing else None,
            "rcept_no": filing.get("rcept_no") if filing else None,
            "report_name": filing.get("report_name") if filing else None,
            "source_package_type": filing.get("source_package_type") if filing else None,
            "filing_date": filing.get("filing_date") if filing else None,
            "source_url": filing.get("filing_url", filing.get("source_url")) if filing else None,
            "has_full_filing_markdown": bool(filing_md),
        },
        "completeness": completeness,
        "source_map": source_map,
        "cross_check": cross_check,
        "provider_timing": cross_check.get("provider_timing", {}),
        "statements": financials or {},
    }
    write_json(out_dir / "evidence-pack.json", evidence_pack)

    actuals_resolved = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "latest_run_cache_path": str(cache_dir),
        "status": cross_check.get("status", "unknown"),
        "resolution_policy": {
            "missing_or_unmapped": "leave_blank_and_flag_review",
            "never_fill_missing_with_zero": True,
            "model_input_gate": "use completeness/source_map before workbook population",
        },
        "identity": identity or {},
        "statements": financials or {},
        "completeness": completeness,
        "source_map": source_map,
        "unmapped_items": [
            item for item in completeness
            if item.get("status") in {"provider-gap", "unavailable", "failed"}
        ],
    }
    write_json(out_dir / "actuals-resolved.json", actuals_resolved)

    if filing_md:
        write_md(out_dir / "full-filing.md", filing_md)
    else:
        write_md(out_dir / "full-filing.md",
                 "# Full filing unavailable\n\nNo full filing markdown was materialized for the latest financial-data run.\n")

    write_md(
        out_dir / "summary.md",
        build_financial_data_summary(evidence_pack, actuals_resolved, out_dir),
    )

    # Clean up legacy internal/ directory from older plugin versions
    legacy_internal = out_dir / "internal"
    if legacy_internal.exists() and legacy_internal.is_dir():
        shutil.rmtree(legacy_internal)
    for legacy_name in ("financial-data-summary.md",):
        legacy_path = out_dir / legacy_name
        if legacy_path.exists() and legacy_path.is_file():
            legacy_path.unlink()


def write_raw_evidence_pack(raw_dir: Path, provider: str, company: dict[str, Any],
                            filing: dict[str, Any]) -> None:
    """Persist deterministic raw evidence files when real source material exists."""
    write_json(raw_dir / "identity-source.json", {
        "provider": provider,
        "company": company,
        "captured_at_utc": utc_now(),
        "status": "available" if company else "unavailable",
    })

    if not filing or filing.get("status") == "error":
        return

    filing_id = _filing_id(provider, filing)
    filing_dir = raw_dir / "filings" / filing_id
    filing_dir.mkdir(parents=True, exist_ok=True)

    source_path = _materialize_raw_source(filing_dir, filing)
    if not source_path:
        return

    write_json(filing_dir / "source-metadata.json", {
        "provider": provider,
        "filing_id": filing_id,
        "status": filing.get("status", "fetched"),
        "filing_url": filing.get("filing_url", filing.get("source_url")),
        "local_path": filing.get("local_path"),
        "accession_number": filing.get("accession_number"),
        "rcept_no": filing.get("rcept_no"),
        "report_name": filing.get("report_name"),
        "report_code": filing.get("report_code"),
        "edinet_code": filing.get("edinet_code"),
        "doc_type": filing.get("doc_type"),
        "source_file": source_path.name,
    })
    (filing_dir / "source.sha256").write_text(sha256_file(source_path) + "\n", encoding="utf-8")


def _filing_id(provider: str, filing: dict[str, Any]) -> str:
    candidates = [
        filing.get("accession_number"),
        filing.get("document_id"),
        filing.get("rcept_no"),
        filing.get("edinet_code"),
        filing.get("corp_code"),
        filing.get("source_sha256"),
        filing.get("markdown_sha256"),
        provider,
    ]
    for candidate in candidates:
        if candidate:
            return slugify(str(candidate))
    return "unknown-filing"


def _materialize_raw_source(filing_dir: Path, filing: dict[str, Any]) -> Path | None:
    local_path = filing.get("local_path")
    if local_path:
        candidate = Path(str(local_path)).expanduser()
        if candidate.exists() and candidate.is_file():
            target = filing_dir / f"source{candidate.suffix or '.bin'}"
            shutil.copyfile(candidate, target)
            return target

    markdown = filing.get("markdown")
    if markdown:
        target = filing_dir / "source.md"
        write_md(target, markdown)
        return target

    source_url = filing.get("filing_url") or filing.get("source_url")
    if source_url:
        target = filing_dir / "source.url.txt"
        write_md(target, str(source_url) + "\n")
        return target
    return None


def write_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Snapshot writer
# ---------------------------------------------------------------------------
def write_snapshot(args: argparse.Namespace, normalized: dict[str, Any],
                  workspace: Path, rid: str) -> dict[str, Any]:
    if not args.topic:
        raise RuntimeError("--topic required for snapshot")
    topic = args.topic.replace("\\", "/").strip().strip("/")
    if topic.startswith("topics/"):
        topic = topic[len("topics/"):]
    if "/" not in topic:
        topic = f"industry/{topic}"
    tp = workspace / topic
    if not tp.is_dir():
        raise RuntimeError(f"Topic does not exist: {tp}")
    sd = tp / ".cache" / "financial-data-snapshot" / rid
    sd.mkdir(parents=True, exist_ok=False)
    summary = {
        "run_id": rid, "generated_at_utc": utc_now(),
        "market": args.market, "identifier": args.identifier,
        "status": normalized["status"],
    }
    write_json(sd / "peer-completeness.json", summary)
    write_md(sd / "snapshot-index.md", f"# Financial Data Snapshot\n\nmarket: {args.market}\nidentifier: {args.identifier}\n")
    return {"cache": str(sd)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch financial data evidence packs.")
    p.add_argument("--check-deps", action="store_true")
    p.add_argument("--workspace")
    p.add_argument("--output-scope", choices=("canonical_company", "current_topic_snapshot"), default="canonical_company")
    p.add_argument("--company-slug")
    p.add_argument("--industry", help="Industry slug (e.g. 'optical-module-equipment') — auto-creates directory if new")
    p.add_argument("--topic")
    p.add_argument("--market", choices=("us", "cn", "hk", "jp", "kr", "tw", "eu", "se", "fr", "de", "uk", "sg", "my", "in", "au"), help="Market route")
    p.add_argument("--identifier", help="Ticker, CIK, filing URL, or market-specific identifier")
    p.add_argument("--identifier-type", default="ticker", choices=("ticker", "isin", "lei", "cik", "edinet_code", "dart_corp_code", "filing_url", "local_esef_package"))
    p.add_argument("--canonical-id")
    p.add_argument("--periods", default="latest")
    p.add_argument("--items", default=",".join(DEFAULT_ITEMS), help=f"Comma-separated. Default: {','.join(DEFAULT_ITEMS)}")
    p.add_argument("--mode", choices=SUPPORTED_MODES, default="latest_core")
    p.add_argument("--source-mode", choices=("auto", "filing_only", "provider_normalized"), default="auto")
    p.add_argument("--financial-data-pack-path")
    return p.parse_args()


def _route_ir(args) -> int:
    """IR market route: WebSearch → Playwright → download → convert → extract → validate.

    Prints actionable step-by-step instructions. Agent executes each step.
    Checks for existing intermediate files to avoid re-work.
    """
    import subprocess
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else discover_workspace()
    ticker = args.identifier
    market = args.market.lower()
    mode = getattr(args, 'mode', 'lite')
    company_slug = args.company_slug
    industry = getattr(args, 'industry', '') or ''

    # Resolve company directory and paths
    try:
        company_dir = ensure_company_topic(workspace, company_slug, industry,
                                           ticker=ticker, market=market)
    except RuntimeError:
        company_dir = workspace / "industry" / industry / "companies" / f"{ticker}-{company_slug}"
        company_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = company_dir / ".cache" / "raw"
    filings_md_dir = company_dir / ".cache" / "financial-data" / "filings"
    actuals_path = company_dir / ".cache" / "financial-data" / "actuals-resolved.json"
    raw_dir.mkdir(parents=True, exist_ok=True)
    filings_md_dir.mkdir(parents=True, exist_ok=True)

    # Determine filing template
    template_map = {"jp": "jp_kessan_tanshin", "kr": "kr_saup_bogoseo",
                    "tw": "tw_financial_report", "eu": "eu_annual_report",
                    "se": "eu_annual_report", "fr": "eu_annual_report",
                    "de": "eu_annual_report", "uk": "eu_annual_report",
                    "sg": "eu_annual_report", "my": "eu_annual_report",
                    "in": "eu_annual_report", "au": "eu_annual_report"}
    filing_type = template_map.get(market, "eu_annual_report")

    ticker_num = ticker.split(".")[0]

    # Check existing progress
    existing_pdfs = sorted(raw_dir.glob("*.pdf")) if raw_dir.is_dir() else []
    existing_mds = sorted(filings_md_dir.glob("*.md")) if filings_md_dir.is_dir() else []
    has_actuals = actuals_path.exists()

    print(f"=== IR Download Chain: {ticker} ({market.upper()}, {mode}) ===")
    print(f"  Company dir: {company_dir}")
    print(f"  Raw PDFs:    {raw_dir} ({len(existing_pdfs)} existing)")
    print(f"  Filing MDs:  {filings_md_dir} ({len(existing_mds)} existing)")
    print(f"  Actuals:     {actuals_path} {'✓ exists' if has_actuals else '✗ missing'}")
    print()

    # ── Step 0: Check if actuals already exist ──
    if has_actuals and actuals_path.stat().st_size > 100:
        try:
            actuals = json.loads(actuals_path.read_text(encoding="utf-8"))
            stmts = actuals.get("statements", {})
            has_is = bool(stmts.get("income_statement"))
            has_seg = bool(stmts.get("revenue_split"))
            if has_is:
                print(f"✅ actuals-resolved.json exists (IS: {len(stmts.get('income_statement',[]))} rows, "
                      f"segments: {len(stmts.get('revenue_split',[]))} segments)")
                md = actuals.get("market_data", {})
                if not md or not md.get("price"):
                    print("▶ Market data missing — filling from yfinance:")
                    yf_id = _yf_ticker(ticker, market)
                    print(f"   python -c \"import yfinance as yf; t=yf.Ticker('{yf_id}'); info=t.info; ...\"")
                else:
                    print(f"   Market data: price={md.get('price')}, mcap={md.get('market_cap')}")
                print()
                print("✅ IR chain complete. actuals-resolved.json ready for stock-quickread.")
                return 0
        except Exception:
            pass  # corrupt file, fall through to normal chain

    # ── Step 1: Download PDFs ──
    if existing_pdfs:
        print(f"✅ Step 1 SKIP — {len(existing_pdfs)} PDF(s) already downloaded:")
        for p in existing_pdfs:
            print(f"     {p.name} ({p.stat().st_size/1024:.0f}KB)")
    else:
        print("▶ Step 1: Download IR filing PDFs")
        print()
        # Print market-specific download plan from ir_download.py
        ir_script = workspace / ".scripts" / "ingest" / "ir_download.py"
        subprocess.run([sys.executable, str(ir_script),
                        "--ticker", ticker, "--market", market, "--mode", mode,
                        "--dest-dir", str(raw_dir)])
        print()
        print("   Agent actions:")
        print(f"   a. WebSearch → find IR page / filing page for {ticker}")
        print(f"   b. Playwright navigate → locate PDF links (annual report / 決算短信 / 사업보고서)")
        print(f"   c. Download PDF → {raw_dir}")
        print(f"   d. Re-run this command to continue to Step 2")
        return 0

    # ── Step 2: Convert PDFs to MD ──
    unprocessed = [p for p in existing_pdfs
                   if not (filings_md_dir / f"{p.stem}.md").exists()]
    if not unprocessed and existing_mds:
        print(f"✅ Step 2 SKIP — {len(existing_mds)} MD(s) already converted:")
        for m in existing_mds:
            print(f"     {m.name} ({m.stat().st_size/1024:.0f} chars)")
    elif unprocessed:
        print(f"▶ Step 2: Convert {len(unprocessed)} PDF(s) to markdown")
        pdf_to_md = workspace / ".scripts" / "ingest" / "pdf-to-md.py"
        for pdf in unprocessed:
            print(f"   python {pdf_to_md} \"{pdf}\" --output \"{filings_md_dir / (pdf.stem + '.md')}\"")
        print()
        print("   Agent: run the pdf-to-md.py command(s) above, then re-run this command.")
        return 0

    # ── Step 3: Extract actuals (guided) ──
    if has_actuals:
        print(f"✅ Step 3-4 SKIP — actuals-resolved.json exists")
    else:
        print(f"▶ Step 3: Extract structured actuals (table-dump mode)")
        print(f"   Filing type: {filing_type}")
        print()
        extract_script = workspace / ".scripts" / "financial-data" / "extract-actuals.py"
        cmd = (f'python "{extract_script}" --filings-dir "{filings_md_dir}" '
               f'--filing-type {filing_type} --table-dump')
        print(f"   {cmd}")
        print()
        print("   Agent: run the above command. IS/BS/CF tables will be dumped in full.")
        print("   Read each table region, extract every line item with value + period,")
        print(f"   write actuals-resolved.json to: {actuals_path}")
        print()
        print("   Template for actuals-resolved.json:")
        print(f"   python \"{extract_script}\" --ticker {ticker} --template")
        return 0

    # ── Step 4: Validate ──
    print(f"▶ Step 4: Validate actuals against source filings")
    extract_script = workspace / ".scripts" / "financial-data" / "extract-actuals.py"
    print(f"   python \"{extract_script}\" --validate \"{actuals_path}\" --filings-dir \"{filings_md_dir}\"")
    print()

    # ── Step 5: Market data fill ──
    print(f"▶ Step 5: Market data (yfinance)")
    yf_id = _yf_ticker(ticker, market)
    print(f"   python -c \"import yfinance as yf; t=yf.Ticker('{yf_id}');")
    print(f"   info=t.info; print('price:', info.get('currentPrice'), 'mcap:', info.get('marketCap'))\"")
    print()
    print("───")
    print("Agent: execute Steps 4-5 above. When done, actuals-resolved.json is ready for stock-quickread.")
    return 0


# ── API market filing types ─────────────────────────────────

_API_FILING_TYPES = {
    "us": {
        "name": "United States (SEC EDGAR)",
        "provider": "edgartools",
        "lite": ["10-K (annual) + latest 10-Q (quarterly) — ~30 fields IS/BS/CF from XBRL"],
        "full": ["10-K + 10-Q × 3 — 5Y annual + 4Q quarterly data"],
        "simpler_filing": "8-K Exhibit 99.1 (Earnings Release) — 20-30 page PDF with IS/BS + segment + commentary",
        "simpler_use": "API XBRL covers IS/BS/CF. Download Earnings Release PDF only if segment detail or management commentary is needed.",
    },
    "cn": {
        "name": "China A-Share",
        "provider": "akshare / eastmoney",
        "lite": ["年报 + 最新季报 — ~20 fields from standardized financial tables"],
        "full": ["年报 + 季报×3 + 半年报 — 5Y annual + 4Q + H1 data"],
        "simpler_filing": "业绩快报 (Earnings Flash) — 1-2 page summary with key metrics",
        "simpler_use": "API already provides structured IS/BS/CF with segment data. PDF only for verification.",
    },
    "hk": {
        "name": "Hong Kong",
        "provider": "akshare / finmind",
        "lite": ["Annual Report + latest Interim Report — ~20 fields IS/BS/CF from API", "PLUS: 全年業績公告 PDF from HKEXnews → segment data (API lacks this)"],
        "full": ["Annual + Interim×2 — 5Y annual + H1 data via API", "PLUS: Results Announcement PDFs for segment + commentary"],
        "simpler_filing": "全年業績公告 / 中期業績公告 (Results Announcement) — 30-40 page PDF on HKEXnews with full IS/BS/CF + segment + commentary",
        "simpler_use": "API (AKShare) does NOT return segment data for HK stocks. Download Results Announcement PDF from HKEXnews → pymupdf4llm → table-dump to fill segment/commentary.",
    },
}

_API_MARKETS = {"us", "cn", "hk"}


def _route_api(args) -> int:
    """API market route: provider → normalize → actuals-resolved.json.

    US/CN/HK markets use structured API data (XBRL/standardized tables).
    No PDF→MD chain needed unless segment/commentary supplement is required.
    """
    import subprocess
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else discover_workspace()
    ticker = args.identifier
    market = args.market.lower()
    mode = getattr(args, 'mode', 'lite')
    filing_info = _API_FILING_TYPES.get(market, {})

    # Check if actuals already exist
    try:
        company_dir = ensure_company_topic(workspace, args.company_slug,
                                           getattr(args, 'industry', '') or '',
                                           ticker=ticker, market=market)
    except RuntimeError:
        company_dir = workspace / "industry" / (getattr(args, 'industry', '') or 'unknown')
    actuals_path = company_dir / ".cache" / "financial-data" / "actuals-resolved.json"

    print(f"=== API Data Route: {ticker} ({filing_info.get('name', market.upper())}, {mode}) ===")
    print(f"  Provider: {filing_info.get('provider', 'unknown')}")
    print(f"  Company dir: {company_dir}")
    print()

    # Show plan
    print(f"## Filing types ({mode} mode)")
    for f in filing_info.get(mode, filing_info.get("lite", [])):
        print(f"  - {f}")
    print()

    # Check existing actuals
    if actuals_path.exists():
        try:
            actuals = json.loads(actuals_path.read_text(encoding="utf-8"))
            stmts = actuals.get("statements", {})
            has_is = bool(stmts.get("income_statement"))
            if has_is:
                print(f"✅ actuals-resolved.json exists (IS: {len(stmts.get('income_statement',[]))} rows)")
                md = actuals.get("market_data", {})
                if md.get("price"):
                    print(f"   Market data: price={md.get('price')}, mcap={md.get('market_cap')}")
                print()
                print("✅ API chain complete.")
                return 0
        except Exception:
            pass

    # Step 1: API fetch
    print("▶ Step 1: API provider fetch")
    print(f"   Provider: {filing_info.get('provider')}")
    print(f"   Periods: {args.periods}")
    print()

    # Step 2: Normalize + write
    print("▶ Step 2: Normalize provider output → actuals-resolved.json")
    print("   (IS/BS/CF rows extracted from structured API data)")
    print()

    # Step 3: Market data
    print("▶ Step 3: Market data (yfinance)")
    yf_id = _yf_ticker(ticker, market)
    print(f"   Ticker: {yf_id}")
    print()

    # Step 4: Optional PDF supplement
    simpler = filing_info.get("simpler_filing", "")
    if market == "hk":
        print(f"▶ Step 4: HK segment PDF (REQUIRED — AKShare API returns SEG=0)")
        print(f"   Downloading company IR annual results PDF for segment data.")
        ir_script = workspace / ".scripts" / "ingest" / "ir_download.py"
        subprocess.run([sys.executable, str(ir_script), "--ticker", ticker, "--market", "hk", "--mode", mode])
        print(f"   After PDF downloaded:")
        print(f"   python .scripts/ingest/pdf-to-md.py <pdf> --output <md>")
        print(f"   python .scripts/financial-data/extract-actuals.py --filings-dir <md_dir> --filing-type eu_annual_report --table-dump")
        print()
    elif simpler:
        print(f"▶ Step 4 (optional): Segment/Commentary supplement")
        print(f"   {simpler}")
        print(f"   {filing_info.get('simpler_use', '')}")
        print()

    print("───")
    print("Agent: Steps 1-3 run automatically via provider API.")
    print("Step 4 only needed if segment data or management commentary is missing from API output.")
    print()

    # Actually run the provider
    return 2  # signal to main() to continue with provider path


def main() -> int:
    args = parse_args()
    if args.check_deps:
        print(json.dumps(dependency_matrix(), ensure_ascii=True, indent=2))
        return 0

    if not args.market or not args.identifier:
        print(json.dumps({"status": "failed", "error": "--market and --identifier required"}, ensure_ascii=True, indent=2))
        return 1
    if args.output_scope == "canonical_company" and not args.company_slug:
        print(json.dumps({"status": "failed", "error": "--company-slug required for canonical_company"}, ensure_ascii=True, indent=2))
        return 1

    # Period defaults based on mode: lite=latest, full=5Y
    mode = getattr(args, 'mode', 'lite')
    if args.periods == 'latest' and mode == 'full':
        args.periods = '5Y'

    if args.market.lower() in IR_MARKETS:
        return _route_ir(args)

    if args.market.lower() in _API_MARKETS:
        api_signal = _route_api(args)
        if api_signal == 0:
            return 0
        # api_signal == 2 means: continue with provider path below

    try:
        workspace = Path(args.workspace).expanduser().resolve() if args.workspace else discover_workspace()
        provider = load_provider(args.market)
        items = [i.strip() for i in str(args.items).split(",") if i.strip()]
        request = {k: getattr(args, k) for k in ("identifier", "identifier_type", "periods", "source_mode", "market")}
        request["items"] = items
        provider_result = provider.fetch(request)
        normalized = normalize_result(provider_result, request)
        rid = run_id()
        if args.output_scope == "canonical_company":
            output = write_canonical_pack(args, normalized, workspace, rid)
        else:
            output = write_snapshot(args, normalized, workspace, rid)

        # Lite mode: unified closeout (market_data fill + revenue_split persist + FY supplement)
        if getattr(args, "mode", "latest_core") == "lite":
            actuals_path = None
            try:
                data_dir = output.get("financial_data_dir", "")
                if not data_dir:
                    tp = ensure_company_topic(workspace, args.company_slug, getattr(args, 'industry', '') or '',
                                              ticker=args.identifier, market=args.market)
                    data_dir = str(tp / ".cache" / "financial-data")
                actuals_path = Path(data_dir) / "actuals-resolved.json"
                if actuals_path.exists():
                    with open(actuals_path, encoding="utf-8") as f:
                        actuals = json.load(f)
                else:
                    actuals = {}
            except Exception:
                actuals = {}

            # 1. market_data fill: yfinance → Bridge fields
            md = actuals.get("market_data") or {}
            if not md or not md.get("pe_ttm") or not md.get("market_cap"):
                try:
                    import yfinance as yf
                    yf_id = _yf_ticker(args.identifier, args.market)
                    t = yf.Ticker(yf_id)
                    info = t.info
                    md.update({k: v for k, v in {
                        "price": info.get("currentPrice"),
                        "market_cap": info.get("marketCap"),
                        "pe_ttm": info.get("trailingPE"),
                        "pe_ntm": info.get("forwardPE"),
                        "pb": info.get("priceToBook"),
                        "ps_ttm": info.get("priceToSalesTrailing12Months"),
                        "ev_ebitda": info.get("enterpriseToEbitda"),
                        "ev_sales": info.get("enterpriseToRevenue"),
                        "dividend_yield_pct": info.get("dividendYield"),
                        "beta": info.get("beta"),
                        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                    }.items() if v is not None})
                    actuals["market_data"] = md
                except Exception:
                    if not md:
                        actuals["market_data"] = {}

            # 2. revenue_split persist: if lite result has revenue_split, write it back
            has_split = "revenue_split" in normalized.get("items_extracted", [])
            existing_split = actuals.get("statements", {}).get("revenue_split") if "statements" in actuals else None
            if has_split and not existing_split:
                actuals.setdefault("statements", {})
                actuals["statements"]["revenue_split"] = provider_result.get("revenue_split") or []

            # 3. supplement missing FY (e.g. EDINET only returns 2FY)
            periods_fetched = len(normalized.get("periods_fetched", []))
            has_is = "income_statement" in normalized.get("items_extracted", [])
            if has_is and periods_fetched < 3 and args.market in ("jp", "kr", "tw"):
                try:
                    import yfinance as yf
                    yf_id = _yf_ticker(args.identifier, args.market)
                    t = yf.Ticker(yf_id)
                    fin = t.financials
                    if fin is not None and not fin.empty:
                        supplement = {col.year: {"revenue": fin.loc["Total Revenue", col] if "Total Revenue" in fin.index else None} for col in fin.columns[:4]}
                        actuals.setdefault("_supplement", {})
                        actuals["_supplement"]["yfinance_income_annual"] = {
                            str(yr): val for yr, val in supplement.items() if val
                        }
                except Exception:
                    pass

            # 4. write back
            try:
                actuals_path.parent.mkdir(parents=True, exist_ok=True)
                _safe_json_dump(actuals, actuals_path)
            except Exception:
                pass

        print(json.dumps({
            "status": normalized["status"],
            "provider": normalized["provider"],
            "extracted": normalized["items_extracted"],
            "errors": normalized["errors"],
            "provider_timing": normalized.get("provider_timing", {}),
            "completeness": normalized["completeness"],
            "output": output,
        }, ensure_ascii=True, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
