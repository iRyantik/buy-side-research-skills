"""fill-gaps v2.5 — three-layer actuals completion.

Layer 1: yfinance (already done by financial-data --lite)
Layer 2: provider API — official data, authoritative, value validation vs L1
Layer 3: web search — agent-executed, per-market site priority chain

Providers: EDINET(JP)/SEC(US)/DART(KR)/FinMind(TW)/AKShare(CN)/Longbridge(HK/US/CN)
"""
import json, os, sys, importlib, shutil, re, copy, math

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HOOKS_DIR, 'config', 'actuals_schema.json')


def _load_schema_runtime_contract():
    defaults = {
        'near_required_supplementary': ["revenue_by_geography", "shares_outstanding"],
        'sector_conditional_supplementary': ["order_backlog"],
        'best_effort_supplementary': ["sbc"],
        'best_effort_skippable': [
            "cash_flow.latest_fy.dividends_paid",
            "cash_flow.latest_fy.share_buybacks",
            "cash_flow.latest_quarter.dividends_paid",
            "cash_flow.latest_quarter.share_buybacks",
            "supplementary.sbc",
        ],
    }
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        supplementary = schema.get('supplementary', {})
        taxonomy = schema.get('_growth_first_taxonomy', {})
        defaults['near_required_supplementary'] = list(supplementary.get('_near_required_fields', defaults['near_required_supplementary']))
        defaults['sector_conditional_supplementary'] = list(supplementary.get('_sector_conditional_fields', defaults['sector_conditional_supplementary']))
        defaults['best_effort_supplementary'] = list(supplementary.get('_best_effort_fields', defaults['best_effort_supplementary']))
        defaults['best_effort_skippable'] = list(taxonomy.get('best_effort_skippable', defaults['best_effort_skippable']))
    except Exception:
        pass
    return defaults


SCHEMA_RUNTIME_CONTRACT = _load_schema_runtime_contract()

PERIOD_SECTIONS = ['income_statement', 'balance_sheet', 'cash_flow']
FLAT_SECTIONS = ['market_data', 'consensus', 'supplementary']
SOURCE_LAYER_ALIAS = {
    'web_search': 'broad_web',
    'local_web': 'trusted_web',
}
SOURCE_TRUST_RANK = {
    'provider_api': 3,
    'official_web': 3,
    'yfinance': 2,
    'trusted_web': 1,
    'broad_web': 1,
    'derived': 0,
    '': -1,
    None: -1,
}
YFINANCE_STATEMENT_MAP = {
    'income_statement': {
        'revenue': ['Total Revenue', 'Operating Revenue'],
        'cost_of_revenue': ['Cost Of Revenue', 'Reconciled Cost Of Revenue'],
        'gross_profit': ['Gross Profit'],
        'r_and_d': ['Research And Development'],
        'sg_and_a': ['Selling General And Administration'],
        'operating_income': ['Operating Income', 'Total Operating Income As Reported'],
        'ebit': ['EBIT'],
        'interest_expense': ['Interest Expense', 'Interest Expense Non Operating'],
        'income_tax': ['Tax Provision'],
        'net_income': [
            'Net Income Common Stockholders',
            'Net Income',
            'Net Income From Continuing Operation Net Minority Interest',
            'Net Income From Continuing And Discontinued Operation',
        ],
    },
    'balance_sheet': {
        'cash': ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments'],
        'accounts_receivable': ['Accounts Receivable', 'Gross Accounts Receivable'],
        'inventory': ['Inventory'],
        'total_assets': ['Total Assets'],
        'current_liabilities': ['Current Liabilities'],
        'goodwill': ['Goodwill', 'Goodwill And Other Intangible Assets'],
        'short_term_debt': ['Current Debt', 'Current Debt And Capital Lease Obligation'],
        'long_term_debt': ['Long Term Debt', 'Long Term Debt And Capital Lease Obligation'],
        'total_equity_parent': ['Stockholders Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'],
    },
    'cash_flow': {
        'operating_cf': ['Operating Cash Flow'],
        'capex': ['Capital Expenditure', 'Capital Expenditure Reported'],
        'd_and_a': ['Depreciation And Amortization', 'Depreciation'],
        'dividends_paid': ['Cash Dividends Paid', 'Common Stock Dividend Paid'],
        'share_buybacks': ['Repurchase Of Capital Stock', 'Common Stock Payments'],
    },
}
CONSUMER_REQUIRED_FIELDS = {
    "period_metadata": [
        "latest_fy_period",
        "latest_quarter_period",
        "latest_quarter_period_label",
        "latest_quarter_period_basis",
    ],
    "income_statement": [
        "revenue", "gross_profit", "cost_of_revenue", "operating_income",
        "ebit", "net_income", "r_and_d", "sg_and_a", "interest_expense", "income_tax",
    ],
    "balance_sheet": [
        "total_assets", "cash", "accounts_receivable", "inventory",
        "goodwill", "current_liabilities", "short_term_debt", "long_term_debt", "total_equity_parent",
    ],
    "cash_flow": ["operating_cf", "capex"],
    "market_data": ["market_cap", "trailing_pe", "price_to_book", "price_to_sales", "beta"],
    "consensus": ["current_year_eps", "current_year_revenue"],
}
CORE_FIELDS = {
    "income_statement": ["revenue", "gross_profit", "operating_income", "ebit", "net_income"],
    "balance_sheet": ["total_assets", "cash", "current_liabilities", "short_term_debt", "long_term_debt", "total_equity_parent"],
    "cash_flow": ["operating_cf", "capex"],
}
NEAR_REQUIRED_SUPPLEMENTARY_FIELDS = SCHEMA_RUNTIME_CONTRACT['near_required_supplementary']
SECTOR_CONDITIONAL_SUPPLEMENTARY_FIELDS = SCHEMA_RUNTIME_CONTRACT['sector_conditional_supplementary']
BEST_EFFORT_SUPPLEMENTARY_FIELDS = SCHEMA_RUNTIME_CONTRACT['best_effort_supplementary']
SKIPPABLE_COVERAGE_FIELDS = set(SCHEMA_RUNTIME_CONTRACT['best_effort_skippable']) | {
    'supplementary.' + field_name for field_name in SECTOR_CONDITIONAL_SUPPLEMENTARY_FIELDS
}
SEGMENT_STATUS_VALUES = {
    "extracted",
    "pending_official_extraction",
    "provider_unavailable",
    "not_disclosed",
}
SEGMENT_TYPE_VALUES = {
    "business_line",
    "geography",
    "end_market",
    "other",
}
SEGMENT_OPTIONAL_NUMERIC_KEYS = (
    "pct_of_total",
    "yoy_pct",
    "sequential_pct",
    "margin_pct",
    "ratio",
)
SEGMENT_NUMERIC_KEY_ALIASES = {
    "qoq_pct": "sequential_pct",
}
SEGMENT_REFERENCE_NUMERIC_KEYS = (
    "prior_year_value",
    "prior_period_value",
    "denominator_value",
)
SEGMENT_OPTIONAL_TEXT_KEYS = (
    "denominator_metric",
)
PROVIDER_GAP_REASONS = {
    "provider_unavailable",
    "official_source_available_not_extracted",
    "not_disclosed",
}

PROVIDER_MAP = {
    'us': 'sec_provider', 'cn': 'akshare_provider',
    'jp': 'edinet_provider', 'kr': 'dart_provider', 'tw': 'finmind_provider',
    'hk': 'akshare_provider', 'eu': 'openesef_provider',
}

PROVIDER_CONCEPT_MAP = {
    "edinet_provider": {
        "income_statement": {"net_sales": "revenue", "cost_of_sales": "cost_of_revenue", "gross_profit": "gross_profit", "operating_income": ["operating_income", "ebit"], "ordinary_income": "ebit", "net_income": "net_income", "profit_loss": "net_income", "income_before_taxes": "ebit", "income_taxes": "income_tax", "selling_general_admin": "sg_and_a"},
        "balance_sheet": {"total_assets": "total_assets", "cash_and_deposits": "cash", "current_liabilities": "current_liabilities", "short_term_loans_payable": "short_term_debt", "commercial_paper": "short_term_debt", "long_term_loans_payable": "long_term_debt", "bonds_payable": "long_term_debt", "net_assets": "total_equity_parent", "accounts_receivable": "accounts_receivable", "inventories": "inventory", "goodwill": "goodwill"},
        "cash_flow": {"operating_cash_flow": "operating_cf", "depreciation_amortization": "d_and_a"},
    },
    "sec_provider": {
        "income_statement": {"RevenueFromContractWithCustomerExcludingAssessedTax": "revenue", "Revenues": "revenue", "Revenue": "revenue", "CostOfGoodsAndServicesSold": "cost_of_revenue", "CostOfRevenue": "cost_of_revenue", "GrossProfit": "gross_profit", "ResearchAndDevelopmentExpense": "r_and_d", "SellingGeneralAndAdministrativeExpense": "sg_and_a", "OperatingIncomeLoss": ["operating_income", "ebit"], "NetIncomeLoss": "net_income", "InterestExpense": "interest_expense", "IncomeTaxExpenseBenefit": "income_tax"},
        "balance_sheet": {"Assets": "total_assets", "CashAndCashEquivalentsAtCarryingValue": "cash", "Cash": "cash", "AccountsReceivableNetCurrent": "accounts_receivable", "InventoryNet": "inventory", "Goodwill": "goodwill", "LiabilitiesCurrent": "current_liabilities", "LongTermDebtNoncurrent": "long_term_debt", "LongTermDebt": "long_term_debt", "LongTermDebtCurrent": "short_term_debt", "StockholdersEquity": "total_equity_parent"},
        "cash_flow": {"NetCashProvidedByUsedInOperatingActivities": "operating_cf", "DepreciationDepletionAndAmortization": "d_and_a", "PaymentsToAcquirePropertyPlantAndEquipment": "capex"},
    },
    "akshare_provider": {
        "income_statement": {"TOTAL_OPERATE_INCOME": "revenue", "OPERATE_INCOME": "revenue", "OPERATE_COST": "cost_of_revenue", "OPERATE_PROFIT": "operating_income", "TOTAL_PROFIT": "ebit", "NET_PROFIT": "net_income", "NET_PROFIT_ATSOPC": "net_income", "NETPROFIT": "net_income", "RESEARCH_EXPENSE": "r_and_d", "SALE_EXPENSE": "sg_and_a", "MANAGE_EXPENSE": "sg_and_a", "INTEREST_EXPENSE": "interest_expense", "INCOME_TAX": "income_tax"},
        "balance_sheet": {"TOTAL_ASSETS": "total_assets", "ASSET_BALANCE": "total_assets", "TOTAL_LIAB_EQUITY": "total_assets", "CASH": "cash", "MONETARYFUNDS": "cash", "ACCOUNTS_RECE": "accounts_receivable", "INVENTORY": "inventory", "GOODWILL": "goodwill", "SHORT_TERM_LOANS": "short_term_debt", "SHORT_LOAN": "short_term_debt", "LONG_TERM_LOANS": "long_term_debt", "LONG_LOAN": "long_term_debt", "CURRENT_LIABILITIES": "current_liabilities", "CURRENT_LIAB_BALANCE": "current_liabilities", "TOTAL_CURRENT_LIAB": "current_liabilities", "TOTAL_EQUITY": "total_equity_parent", "TOTAL_PARENT_EQUITY": "total_equity_parent", "PARENT_EQUITY_BALANCE": "total_equity_parent", "EQUITY_BALANCE": "total_equity_parent"},
        "cash_flow": {"NET_OPERATE_CASH_FLOW": "operating_cf", "OPERATE_NETCASH_BALANCE": "operating_cf", "NETCASH_OPERATE": "operating_cf", "CONSTRUCT_LONG_ASSET": "capex", "DEPRECIATION": "d_and_a", "IA_AMORTIZE": "d_and_a", "LPE_AMORTIZE": "d_and_a", "USERIGHT_ASSET_AMORTIZE": "d_and_a"},
    },
    "akshare_hk": {
        "income_statement": {"004001001": "revenue", "004005002": "cost_of_revenue", "004007999": "gross_profit", "004010003": "sg_and_a", "004010004": "sg_and_a", "004010010": "r_and_d", "004010999": "operating_income", "004011999": "ebit", "004010002": "interest_expense", "004012001": "income_tax", "004012999": "net_income", "004025002": "net_income"},
        "balance_sheet": {"004009999": "total_assets", "004002010": "cash", "004002003": "accounts_receivable", "004002001": "inventory", "004001005": "goodwill", "004011999": "current_liabilities", "004011010": "short_term_debt", "004020001": "long_term_debt", "004028999": "total_equity_parent"},
        "cash_flow": {"003999": "operating_cf", "000002999": "operating_cf", "005005": "capex", "000005005": "capex", "001009": "d_and_a", "000001009": "d_and_a"},
    },
    "dart_provider": {
        "income_statement": {"ifrs-full_Revenue": "revenue", "ifrs-full_GrossProfit": "gross_profit", "dart_OperatingIncomeLoss": "operating_income", "ifrs-full_ProfitLossBeforeTax": "ebit", "ifrs-full_IncomeTaxExpenseContinuingOperations": "income_tax", "ifrs-full_ProfitLoss": "net_income", "ifrs-full_CostOfSales": "cost_of_revenue", "ifrs-full_FinanceCosts": "interest_expense", "dart_TotalSellingGeneralAdministrativeExpenses": "sg_and_a"},
        "balance_sheet": {"ifrs-full_Assets": "total_assets", "ifrs-full_CashAndCashEquivalents": "cash", "ifrs-full_CurrentTradeReceivables": "accounts_receivable", "dart_ShortTermTradeReceivable": "accounts_receivable", "dart_CurrentNontradeReceivables": "accounts_receivable", "ifrs-full_Inventories": "inventory", "ifrs-full_IntangibleAssetsAndGoodwill": "goodwill", "ifrs-full_CurrentLiabilities": "current_liabilities", "ifrs-full_CurrentPortionOfLongtermBorrowings": "short_term_debt", "ifrs-full_ShorttermBorrowings": "short_term_debt", "ifrs-full_LongtermBorrowings": "long_term_debt", "dart_LongTermBorrowingsGross": "long_term_debt", "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued": "long_term_debt", "ifrs-full_NoncurrentPortionOfNoncurrentSecuredBankLoansReceived": "long_term_debt", "ifrs-full_EquityAttributableToOwnersOfParent": "total_equity_parent", "ifrs-full_Equity": "total_equity_parent"},
        "cash_flow": {"ifrs-full_CashFlowsFromUsedInOperatingActivities": "operating_cf", "ifrs-full_CashFlowsFromUsedInOperations": "operating_cf", "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": "capex", "ifrs-full_DividendsPaidClassifiedAsFinancingActivities": "dividends_paid"},
    },
    "finmind_provider": {
        "income_statement": {"Revenue": "revenue", "GrossProfit": "gross_profit", "OperatingIncome": "operating_income", "PreTaxIncome": "ebit", "IncomeAfterTaxes": "net_income", "CostOfGoodsSold": "cost_of_revenue", "OperatingExpenses": "sg_and_a", "TAX": "income_tax"},
        "balance_sheet": {"TotalAssets": "total_assets", "CashAndCashEquivalents": "cash", "AccountsReceivableNet": "accounts_receivable", "AccountsReceivableDuefromRelatedPartiesNet": "accounts_receivable", "Inventories": "inventory", "IntangibleAssets": "goodwill", "CurrentLiabilities": "current_liabilities", "ShorttermBorrowings": "short_term_debt", "BondsPayable": "long_term_debt", "LongtermBorrowings": "long_term_debt", "EquityAttributableToOwnersOfParent": "total_equity_parent", "Equity": "total_equity_parent"},
        "cash_flow": {"operating_cash_flow": "operating_cf", "CashFlowsFromOperatingActivities": "operating_cf", "NetCashInflowFromOperatingActivities": "operating_cf", "depreciation_amortization": "d_and_a", "Depreciation": "d_and_a", "AmortizationExpense": "d_and_a", "purchase_of_ppe": "capex", "PropertyAndPlantAndEquipment": "capex"},
    },
}


# ── I/O ──────────────────────────────────────────────
def _schema_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'actuals_schema.json')


def _company_root(industry, ticker):
    return os.path.join('industry', industry, 'companies', ticker)


def _load_actuals_template():
    with open(_schema_path(), 'r', encoding='utf-8') as f:
        return json.load(f)


def _is_legacy_actuals(data):
    for section in PERIOD_SECTIONS:
        for period_key in ['latest_fy', 'latest_quarter']:
            period_obj = data.get(section, {}).get(period_key, {})
            if isinstance(period_obj, dict) and any(key != 'period' for key in period_obj.keys()):
                return False
    return True


def _merge_template(template_obj, existing_obj):
    if isinstance(template_obj, dict):
        merged = copy.deepcopy(template_obj)
        existing_obj = existing_obj if isinstance(existing_obj, dict) else {}
        for key, value in existing_obj.items():
            if key in merged:
                merged[key] = _merge_template(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    if existing_obj not in (None, '', [], {}):
        return copy.deepcopy(existing_obj)
    return copy.deepcopy(template_obj)


def _ticker_from_market_code(market, code):
    text = str(code or '').strip()
    if not text:
        return None
    if '.' in text:
        return text
    market = (market or '').lower()
    if market == 'kr' and re.fullmatch(r'\d{6}', text):
        return text + '.KS'
    if market == 'jp' and re.fullmatch(r'\d{4}', text):
        return text + '.T'
    if market == 'tw' and re.fullmatch(r'\d{4}', text):
        return text + '.TW'
    if market == 'hk' and re.fullmatch(r'\d{4,5}', text):
        return text.zfill(5) + '.HK'
    return text


def _hydrate_identity_from_raw(industry, ticker, data):
    base = os.path.join(_company_root(industry, ticker), '_cache', 'financial-data', 'internal', '_raw')
    provider_payload_path = os.path.join(base, 'provider_payload.json')
    identity_source_path = os.path.join(base, 'identity-source.json')
    provider_payload = {}
    identity_source = {}
    if os.path.exists(provider_payload_path):
        with open(provider_payload_path, 'r', encoding='utf-8') as f:
            provider_payload = json.load(f)
    if os.path.exists(identity_source_path):
        with open(identity_source_path, 'r', encoding='utf-8') as f:
            identity_source = json.load(f)

    market = data.get('market') or provider_payload.get('market')
    company_block = provider_payload.get('company', {}) if isinstance(provider_payload.get('company'), dict) else {}
    identity_company = identity_source.get('company', {}) if isinstance(identity_source.get('company'), dict) else {}
    company_name = data.get('company') or company_block.get('name') or identity_company.get('name')
    code = (
        company_block.get('stock_code')
        or identity_company.get('stock_code')
        or provider_payload.get('identifier')
        or data.get('ticker')
    )
    ticker_value = data.get('ticker') or _ticker_from_market_code(market, code)

    if market and not data.get('market'):
        data['market'] = market
    if company_name and not data.get('company'):
        data['company'] = company_name
    if ticker_value and not data.get('ticker'):
        data['ticker'] = ticker_value
    return data


def _prepare_actuals(industry, ticker, data):
    prepared = data
    if _is_legacy_actuals(prepared):
        prepared = _merge_template(_load_actuals_template(), prepared)
    official_markers = (
        'earnings release',
        'annual results announcement',
        'results announcement',
        'annual report',
        'interim report',
        'investor relations',
        'press release',
        'buyback program',
        '10-k',
        '10-q',
        '20-f',
        '6-k',
        'edinet',
        'dart',
        'mops',
        'cninfo',
    )
    trusted_markers = (
        'marketscreener',
        'stockanalysis',
        'stock analysis',
        'naver',
        'goodinfo',
        'kabutan',
        'eastmoney',
        'fnguide',
    )
    def _normalize_source_layers(obj):
        if isinstance(obj, dict):
            layer = obj.get('source_layer')
            detail = str(obj.get('source_detail') or '').lower()
            if layer == 'web_search':
                obj['source_layer'] = 'trusted_web'
            elif layer in {'local_web', 'trusted_web'}:
                if any(marker in detail for marker in official_markers):
                    obj['source_layer'] = 'official_web'
                elif layer == 'local_web' and any(marker in detail for marker in trusted_markers):
                    obj['source_layer'] = 'trusted_web'
                elif layer == 'local_web':
                    obj['source_layer'] = 'trusted_web'
            for value in obj.values():
                _normalize_source_layers(value)
        elif isinstance(obj, list):
            for item in obj:
                _normalize_source_layers(item)
    _normalize_source_layers(prepared)
    _sanitize_nonfinite_values(prepared)
    _normalize_cash_flow_signs(prepared)
    prepared = _hydrate_identity_from_raw(industry, ticker, prepared)
    _finalize_segments_status(prepared, tried_web=False)
    return prepared


def _provider_identifier(market, ticker_value, fallback):
    text = str(ticker_value or fallback or '').strip()
    if not text:
        return text
    if market in {'jp', 'kr', 'tw', 'hk'} and '.' in text:
        text = text.split('.', 1)[0]
    return text


def _official_web_cache_path(industry, ticker):
    return os.path.join(
        _company_root(industry, ticker),
        '_cache', 'financial-data', 'internal', '_raw', 'official_web_cache.json'
    )


def _path_target(root, path):
    current = root
    for part in str(path or '').split('.'):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current.get(part)
    return current


def _apply_official_web_cache(industry, ticker, data):
    cache_path = _official_web_cache_path(industry, ticker)
    if not os.path.exists(cache_path):
        return 0
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as exc:
        print('  official_web cache load failed: ' + str(exc))
        return 0

    filled = 0
    for entry in payload.get('entries', []):
        entry_layer = _normalized_source_layer(entry.get('source_layer')) or 'official_web'
        source_title = _normalize_query_text(entry.get('source_title'))
        source_locator = _normalize_query_text(entry.get('source_locator'))
        source_url = _normalize_query_text(entry.get('source_url'))
        detail_bits = []
        if source_title:
            detail_bits.append(source_title)
        if source_locator:
            detail_bits.append(source_locator)
        if source_url:
            detail_bits.append(source_url)
        detail = entry_layer + ': ' + ' | '.join(detail_bits) if detail_bits else (entry_layer + ' cache')
        path = str(entry.get('path') or '')
        target = _path_target(data, path)
        if isinstance(target, dict) and set(target.keys()) >= {'value', 'source_layer', 'source_detail'}:
            filled += _set_sourced_value(target, entry.get('value'), entry_layer, detail)
            continue
        if path == 'segments.status':
            if entry.get('value') in SEGMENT_STATUS_VALUES:
                data.setdefault('segments', {})['status'] = entry.get('value')
            continue
        if path == 'segments.segments' and isinstance(entry.get('value'), list):
            segments_obj = data.setdefault('segments', {})
            existing = segments_obj.get('segments')
            if not isinstance(existing, list):
                existing = []
            existing.extend(_normalize_segment_entries(entry.get('value'), data, entry_layer, detail))
            segments_obj['segments'] = _dedupe_segments(existing)
            if segments_obj['segments']:
                segments_obj['status'] = 'extracted'

    metadata = payload.get('metadata', {})
    for key in ['latest_fy_period', 'latest_quarter_period', 'latest_quarter_period_label', 'latest_quarter_period_basis']:
        if metadata.get(key):
            data[key] = metadata[key]
    return filled


COMPANY_SUFFIX_RE = re.compile(
    r'(?:,\s*|\s+)(?:AB|AG|ASA|B\.?V\.?|CO|CO\.|COMPANY|CORP|CORPORATION|GROUP|HOLDINGS?|INC|INC\.|LIMITED|LTD|LTD\.|N\.?V\.?|OYJ|PLC|S\.?A\.?|SE|SPA|S\.?P\.?A\.?)$',
    re.IGNORECASE,
)


def _normalize_query_text(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def _company_query_names(company_name):
    name = _normalize_query_text(company_name)
    if not name:
        return []
    names = [name]
    stripped = COMPANY_SUFFIX_RE.sub('', name).strip(' ,')
    if stripped and stripped not in names:
        names.append(stripped)
    return names


def _query_context(data, market):
    ticker_value = _normalize_query_text(data.get('ticker'))
    provider_code = _normalize_query_text(_provider_identifier(market, ticker_value, ticker_value))
    if market == 'eu' and '.' in ticker_value:
        provider_code = ticker_value.split('.', 1)[0]
    company_names = _company_query_names(data.get('company'))
    return {
        'company_names': company_names,
        'company': company_names[0] if company_names else '',
        'ticker': ticker_value,
        'code': provider_code,
        'identifier': provider_code or ticker_value,
    }


def _render_query_template(template, context, company_override=None, code_override=None, ticker_override=None):
    rendered = str(template or '')
    replacements = {
        'company': company_override if company_override is not None else context.get('company', ''),
        'name': company_override if company_override is not None else context.get('company', ''),
        'ticker': ticker_override if ticker_override is not None else context.get('ticker', ''),
        'code': code_override if code_override is not None else context.get('code', ''),
        'identifier': code_override if code_override is not None else context.get('identifier', ''),
    }
    for key, value in replacements.items():
        rendered = rendered.replace(f'<{key}>', str(value or ''))
    return _normalize_query_text(rendered)


def _append_unique_query(bucket, seen, layer_name, query):
    normalized = _normalize_query_text(query)
    if not normalized:
        return
    dedupe_key = (layer_name, normalized.lower())
    if dedupe_key in seen:
        return
    seen.add(dedupe_key)
    bucket.append({'layer_name': layer_name, 'query': normalized})


def _expand_layer3_queries(layer_name, query, context):
    variants = []
    seen = set()
    company_names = context.get('company_names', [])
    code_value = context.get('code', '')
    has_company_placeholder = '<company>' in str(query or '') or '<name>' in str(query or '')

    def _add(query_text):
        normalized = _normalize_query_text(query_text)
        if not normalized:
            return
        lower = normalized.lower()
        if lower in seen:
            return
        seen.add(lower)
        variants.append(normalized)

    if layer_name == 'official_web':
        if has_company_placeholder:
            for company_name in company_names:
                rendered = _render_query_template(query, context, company_override=company_name)
                _add(rendered)
                if code_value and code_value.lower() not in rendered.lower():
                    _add(rendered + ' ' + code_value)
        else:
            for company_name in company_names:
                rendered = _render_query_template(
                    query,
                    context,
                    company_override=company_name,
                    code_override=company_name,
                    ticker_override=company_name,
                )
                _add(rendered)
                if code_value and code_value.lower() not in rendered.lower():
                    _add(rendered + ' ' + code_value)

    _add(_render_query_template(query, context))
    return variants


def _longbridge_identifier(market, ticker_value):
    text = str(ticker_value or '').strip()
    if not text:
        return text
    market = str(market or '').lower()
    upper = text.upper()
    if market == 'us':
        return upper if '.' in upper else upper + '.US'
    if market == 'cn':
        if upper.endswith('.SS'):
            return upper[:-3] + '.SH'
        if upper.endswith('.SZ'):
            return upper
        if re.fullmatch(r'\d{6}', upper):
            return upper + '.SH'
    return text


def _bootstrap_yfinance_layer1(data):
    ticker = str(data.get('ticker') or '').strip()
    if not ticker:
        return 0
    try:
        import yfinance as yf
        import yfinance.cache as yfc
        cache_dir = os.path.join('C:\\tmp', 'py-yfinance')
        yfc.set_cache_location(cache_dir)
        t = yf.Ticker(ticker)
    except Exception:
        return 0

    info = {}
    fast_info = {}
    earnings_estimate = None
    revenue_estimate = None
    try:
        info = t.info or {}
    except Exception:
        info = {}
    try:
        fast_info = dict(t.fast_info or {})
    except Exception:
        fast_info = {}
    try:
        earnings_estimate = getattr(t, 'earnings_estimate', None)
    except Exception:
        earnings_estimate = None
    try:
        revenue_estimate = getattr(t, 'revenue_estimate', None)
    except Exception:
        revenue_estimate = None

    filled = 0
    market_data = data.get('market_data', {})
    snapshot_map = {
        'market_cap': info.get('marketCap') or fast_info.get('marketCap') or fast_info.get('market_cap'),
        'trailing_pe': info.get('trailingPE'),
        'price_to_book': info.get('priceToBook'),
        'price_to_sales': info.get('priceToSalesTrailing12Months'),
        'ev_ebitda': info.get('enterpriseToEbitda'),
        'beta': info.get('beta'),
        'dividend_yield': info.get('dividendYield'),
        'shares_outstanding': info.get('sharesOutstanding') or fast_info.get('shares'),
    }
    for field, value in snapshot_map.items():
        target = market_data.get(field)
        if not isinstance(target, dict):
            continue
        if not _value_present(target.get('value')) and _value_present(value):
            target['value'] = value
            target['source_layer'] = 'yfinance'
            target['source_detail'] = ticker + ' yfinance'
            filled += 1

    shares_value = snapshot_map.get('shares_outstanding')
    supp_target = data.get('supplementary', {}).get('shares_outstanding')
    if isinstance(supp_target, dict) and not _value_present(supp_target.get('value')) and _value_present(shares_value):
        supp_target['value'] = shares_value
        supp_target['source_layer'] = 'yfinance'
        supp_target['source_detail'] = ticker + ' yfinance'
        filled += 1

    estimate_fields = {
        'current_year_eps': _extract_yfinance_estimate_value(earnings_estimate, '0y'),
        'next_year_eps': _extract_yfinance_estimate_value(earnings_estimate, '+1y'),
        'current_year_revenue': _extract_yfinance_estimate_value(revenue_estimate, '0y'),
    }
    consensus = data.get('consensus', {})
    for field, value in estimate_fields.items():
        target = consensus.get(field)
        if not isinstance(target, dict):
            continue
        if not _value_present(target.get('value')) and _value_present(value):
            target['value'] = value
            target['source_layer'] = 'yfinance'
            target['source_detail'] = ticker + ' yfinance estimates'
            filled += 1

    if not data.get('currency'):
        currency = info.get('currency') or fast_info.get('currency')
        if currency:
            data['currency'] = currency
    if filled and not data.get('source'):
        data['source'] = 'yfinance'
    filled += _fill_yfinance_statement_layer1(data, t)
    return filled


def _extract_yfinance_estimate_value(frame, period_key):
    if frame is None:
        return None
    try:
        if hasattr(frame, 'empty') and frame.empty:
            return None
        if period_key not in getattr(frame, 'index', []):
            return None
        value = frame.loc[period_key, 'avg']
        return _to_float(value)
    except Exception:
        return None


def _yfinance_period_str(period):
    if period is None:
        return None
    text = str(period)
    match = re.match(r'^(\d{4}-\d{2}-\d{2})', text)
    return match.group(1) if match else text


def _yfinance_pick_latest_period(frames):
    periods = []
    for frame in frames:
        try:
            cols_obj = getattr(frame, 'columns', None)
            cols = list(cols_obj) if cols_obj is not None else []
        except Exception:
            cols = []
        for col in cols:
            period = _yfinance_period_str(col)
            if period:
                periods.append(period)
    if not periods:
        return None
    return sorted(set(periods))[-1]


def _yfinance_lookup_value(frame, candidates, period):
    if frame is None or period is None:
        return None
    try:
        cols_obj = getattr(frame, 'columns', None)
        cols = list(cols_obj) if cols_obj is not None else []
    except Exception:
        cols = []
    column = None
    for candidate_col in cols:
        if _yfinance_period_str(candidate_col) == period:
            column = candidate_col
            break
    if column is None:
        return None
    for row_name in candidates:
        try:
            if row_name not in frame.index:
                continue
            value = frame.loc[row_name, column]
        except Exception:
            continue
        num = _to_float(value)
        if num is not None:
            return num
    return None


def _fill_yfinance_statement_period(data, target_period_key, source_period, frames, detail_prefix):
    if not source_period:
        return 0
    filled = 0
    for section_key, field_candidates in YFINANCE_STATEMENT_MAP.items():
        target_section = data.get(section_key, {}).get(target_period_key, {})
        frame = frames.get(section_key)
        if not isinstance(target_section, dict) or frame is None:
            continue
        for field_name, candidates in field_candidates.items():
            target = target_section.get(field_name)
            if not isinstance(target, dict) or target.get('value') is not None:
                continue
            value = _yfinance_lookup_value(frame, candidates, source_period)
            if value is None:
                continue
            if field_name in {'interest_expense', 'income_tax', 'capex', 'dividends_paid', 'share_buybacks'}:
                value = abs(value)
            target['value'] = value
            target['source_layer'] = 'yfinance'
            target['source_detail'] = detail_prefix + ': ' + candidates[0] + ' (' + str(source_period) + ')'
            filled += 1
    return filled


def _fill_yfinance_statement_layer1(data, ticker_obj):
    try:
        frames = {
            'annual': {
                'income_statement': getattr(ticker_obj, 'income_stmt', None),
                'balance_sheet': getattr(ticker_obj, 'balance_sheet', None),
                'cash_flow': getattr(ticker_obj, 'cashflow', None),
            },
            'quarterly': {
                'income_statement': getattr(ticker_obj, 'quarterly_income_stmt', None),
                'balance_sheet': getattr(ticker_obj, 'quarterly_balance_sheet', None),
                'cash_flow': getattr(ticker_obj, 'quarterly_cashflow', None),
            },
        }
    except Exception:
        return 0

    annual_period = _yfinance_pick_latest_period(frames['annual'].values())
    quarterly_period = _yfinance_pick_latest_period(frames['quarterly'].values())
    filled = 0

    if annual_period:
        if not data.get('latest_fy_period'):
            _apply_latest_period_metadata(data, 'latest_fy', annual_period, 'annual')
        filled += _fill_yfinance_statement_period(
            data,
            'latest_fy',
            annual_period,
            frames['annual'],
            'yfinance annual statement',
        )

    if quarterly_period:
        if not data.get('latest_quarter_period'):
            _apply_latest_period_metadata(data, 'latest_quarter', quarterly_period, _normalize_period_basis(quarterly_period))
        filled += _fill_yfinance_statement_period(
            data,
            'latest_quarter',
            quarterly_period,
            frames['quarterly'],
            'yfinance quarterly statement',
        )

    return filled


def _fetch_finmind_dataset(dataset, identifier, start_date='2024-01-01'):
    try:
        from urllib.parse import urlencode
        from urllib.request import urlopen
    except Exception:
        return []
    params = {
        'dataset': dataset,
        'data_id': identifier,
        'start_date': start_date,
    }
    try:
        with urlopen('https://api.finmindtrade.com/api/v4/data?' + urlencode(params), timeout=30) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception:
        return []
    if payload.get('status') != 200:
        return []
    return payload.get('data') or []


def _set_provider_value(target, value, detail):
    return _set_sourced_value(target, value, 'provider_api', detail)


def _set_sourced_value(target, value, layer_name, detail):
    if not isinstance(target, dict) or not _value_present(value):
        return 0
    existing_layer = _normalized_source_layer(target.get('source_layer'))
    if _value_present(target.get('value')) and not _can_overwrite_source(existing_layer, layer_name, allow_same_tier=False):
        return 0
    changed = (
        target.get('value') != value
        or target.get('source_layer') != layer_name
        or target.get('source_detail') != detail
    )
    if not changed:
        return 0
    target['value'] = value
    target['source_layer'] = layer_name
    target['source_detail'] = detail
    return 1


def _latest_finmind_row(rows):
    if not rows:
        return None
    return sorted(rows, key=lambda row: str(row.get('date') or ''))[-1]


def _fill_tw_finmind_aux(data, identifier, annual_result=None, q_result=None):
    if str(data.get('market') or '').lower() != 'tw' or not identifier:
        return 0

    filled = 0
    share_rows = _fetch_finmind_dataset('TaiwanStockShareholding', identifier, '2024-01-01')
    price_rows = _fetch_finmind_dataset('TaiwanStockPrice', identifier, '2026-01-01')
    per_rows = _fetch_finmind_dataset('TaiwanStockPER', identifier, '2026-01-01')

    latest_share = _latest_finmind_row(share_rows)
    latest_price = _latest_finmind_row(price_rows)
    latest_per = _latest_finmind_row(per_rows)

    shares_issued = _to_float((latest_share or {}).get('NumberOfSharesIssued'))
    share_date = str((latest_share or {}).get('date') or '')
    if shares_issued is not None:
        detail = 'FinMind TaiwanStockShareholding: NumberOfSharesIssued (' + share_date + ')'
        filled += _set_provider_value(data.get('market_data', {}).get('shares_outstanding'), shares_issued, detail)
        filled += _set_provider_value(data.get('supplementary', {}).get('shares_outstanding'), shares_issued, detail)

    if latest_per:
        per_date = str(latest_per.get('date') or '')
        per_map = {
            'trailing_pe': _to_float(latest_per.get('PER')),
            'price_to_book': _to_float(latest_per.get('PBR')),
            'dividend_yield': _to_float(latest_per.get('dividend_yield')),
        }
        for field_name, value in per_map.items():
            if value is None:
                continue
            detail = 'FinMind TaiwanStockPER: ' + field_name + ' (' + per_date + ')'
            filled += _set_provider_value(data.get('market_data', {}).get(field_name), value, detail)

    close_price = _to_float((latest_price or {}).get('close'))
    price_date = str((latest_price or {}).get('date') or '')
    market_cap = close_price * shares_issued if close_price is not None and shares_issued is not None else None
    if market_cap is not None:
        detail = 'FinMind TaiwanStockPrice close x TaiwanStockShareholding shares (' + price_date + ' / ' + share_date + ')'
        filled += _set_provider_value(data.get('market_data', {}).get('market_cap'), market_cap, detail)
        revenue = _to_float(data.get('income_statement', {}).get('latest_fy', {}).get('revenue', {}).get('value'))
        if revenue and revenue > 0:
            filled += _set_provider_value(
                data.get('market_data', {}).get('price_to_sales'),
                market_cap / revenue,
                'computed from FinMind provider route: market_cap / latest_fy.revenue',
            )

    def _all_zero_since_provider_gap(rows, target_period):
        series = []
        for row in rows:
            values = row.get('values', {}) if isinstance(row, dict) else {}
            for period, raw_value in values.items():
                value = _to_float(raw_value)
                if value is None:
                    continue
                series.append((str(period), value))
        series.sort()
        if len(series) < 4:
            return False, None
        tail = series[-4:]
        if any(value != 0 for _, value in tail):
            return False, None
        last_period = tail[-1][0]
        if target_period and last_period >= str(target_period):
            return False, None
        return True, last_period

    balance_rows = []
    for result in (annual_result, q_result):
        if isinstance(result, dict):
            balance_rows.extend(result.get('balance_sheet', []) or [])
    short_term_rows = [row for row in balance_rows if str(row.get('concept') or '') == 'ShorttermBorrowings']
    can_infer_zero, last_zero_period = _all_zero_since_provider_gap(short_term_rows, data.get('latest_quarter_period'))
    if can_infer_zero:
        detail = 'FinMind ShorttermBorrowings: last 4 disclosed periods were zero through ' + str(last_zero_period)
        filled += _set_provider_value(data.get('balance_sheet', {}).get('latest_fy', {}).get('short_term_debt'), 0.0, detail + ' (carry-forward to latest_fy)')
        filled += _set_provider_value(data.get('balance_sheet', {}).get('latest_quarter', {}).get('short_term_debt'), 0.0, detail + ' (carry-forward to latest_quarter)')

    return filled


def load_actuals(industry, ticker):
    path = os.path.join('industry', industry, 'companies', ticker, '_cache', 'financial-data', 'internal', 'actuals-resolved.json')
    if not os.path.exists(path):
        print('ERROR: no actuals for ' + ticker + ' in ' + industry)
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return _prepare_actuals(industry, ticker, json.load(f))

def save_actuals(industry, ticker, data):
    path = os.path.join('industry', industry, 'companies', ticker, '_cache', 'financial-data', 'internal', 'actuals-resolved.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _sanitize_nonfinite_values(data)
    _normalize_cash_flow_signs(data)
    _finalize_segments_status(data, tried_web='official_web' in str(data.get('source') or ''))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)

def get_null_fields(data):
    nulls = []
    for section in PERIOD_SECTIONS:
        for period_key in ['latest_fy', 'latest_quarter']:
            period_obj = data.get(section, {}).get(period_key, {})
            if not isinstance(period_obj, dict): continue
            for fname, fobj in period_obj.items():
                if fname == 'period': continue
                if isinstance(fobj, dict) and not _value_present(fobj.get('value')):
                    nulls.append({'path': section + '.' + period_key + '.' + fname, 'section': section, 'period': period_key, 'field': fname, 'obj': fobj})
    for section in FLAT_SECTIONS:
        for fname, fobj in data.get(section, {}).items():
            if isinstance(fobj, dict) and not _value_present(fobj.get('value')):
                nulls.append({'path': section + '.' + fname, 'section': section, 'field': fname, 'obj': fobj})
    return nulls

def _count_total_fields(data):
    total = 0
    for path, _ in _iter_field_objects(data):
        if not _is_skippable_coverage_field(path):
            total += 1
    return total


def _mark_provider_gap_fields(data, remaining, provider_label, scope_label, include_sections=None, include_periods=None, reason='official_source_available_not_extracted'):
    include_sections = set(include_sections or PERIOD_SECTIONS)
    include_periods = set(include_periods or ['latest_fy', 'latest_quarter'])
    marked = 0
    note = 'provider-gap: reason=' + str(reason) + ' provider=' + str(provider_label) + ' scope=' + str(scope_label)
    for item in remaining:
        if item.get('section') not in include_sections:
            continue
        if item.get('period') not in include_periods:
            continue
        field_obj = item.get('obj')
        if not isinstance(field_obj, dict) or field_obj.get('value') is not None:
            continue
        detail = str(field_obj.get('source_detail') or '')
        if 'provider-gap' not in detail.lower():
            field_obj['source_detail'] = note
            if field_obj.get('source_layer') is None:
                field_obj['source_layer'] = 'provider_api'
            marked += 1
    return marked


def _clear_provider_gap_fields(remaining, provider_label, include_sections=None, include_periods=None):
    include_sections = set(include_sections or PERIOD_SECTIONS)
    include_periods = set(include_periods or ['latest_fy', 'latest_quarter'])
    provider_token = 'provider=' + str(provider_label)
    for item in remaining:
        if item.get('section') not in include_sections:
            continue
        if item.get('period') not in include_periods:
            continue
        field_obj = item.get('obj')
        if not isinstance(field_obj, dict) or field_obj.get('value') is not None:
            continue
        detail = str(field_obj.get('source_detail') or '')
        if 'provider-gap:' not in detail or provider_token not in detail:
            continue
        segments = [segment.strip() for segment in detail.split('|') if segment.strip()]
        kept = [segment for segment in segments if provider_token not in segment]
        field_obj['source_detail'] = ' | '.join(kept) if kept else None
        if field_obj.get('source_layer') == 'provider_api':
            field_obj['source_layer'] = None


def _is_openesef_local_gap(market, provider_label, payload):
    if market != 'eu' or provider_label != 'openesef' or not isinstance(payload, dict):
        return False
    if payload.get('status') != 'provider-gap':
        return False
    text_parts = []
    error_text = payload.get('error')
    if error_text:
        text_parts.append(str(error_text))
    for item in payload.get('errors', []) or []:
        text_parts.append(str(item))
    detail = ' '.join(text_parts).lower()
    return 'local_esef_package' in detail or 'ticker-only filing discovery is experimental' in detail


# ── Layer 2: provider API ────────────────────────────
def _find_provider_path():
    for p in [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'buy-side-research-skills-1.1.0', 'plugins', 'buy-side-research-skills', 'skills', 'financial-data', 'scripts', 'providers'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '_scripts', 'financial-data', 'providers'),
        os.path.join(os.path.expanduser('~'), 'Desktop', 'buy-side-research-skills-1.1.0', 'plugins', 'buy-side-research-skills', 'skills', 'financial-data', 'scripts', 'providers'),
        os.path.join(os.path.expanduser('~'), '.codex', 'plugins', 'cache', 'buy-side-research-skills', 'buy-side-research-skills', '4.6.0', 'skills', 'financial-data', 'scripts', 'providers'),
        os.path.join(os.path.expanduser('~'), '.claude', 'plugins', 'cache', 'buy-side-research-skills', 'buy-side-research-skills', '4.5.6', 'skills', 'financial-data', 'scripts', 'providers'),
    ]:
        if os.path.isdir(p): return p
    return None

PROVIDER_PATH = _find_provider_path()
if PROVIDER_PATH and PROVIDER_PATH not in sys.path:
    sys.path.insert(0, PROVIDER_PATH)

def _normalize_period_basis(period, basis=None):
    token = str(basis or '').strip().lower()
    if token in {'quarter', 'half_year', 'annual', 'report_period', 'cumulative_report_period'}:
        return token
    text = str(period or '').strip()
    compact = re.sub(r'\s+', '', text.upper())
    if text.endswith('-03-31') or text.endswith('-09-30'):
        return 'quarter'
    if text.endswith('-06-30'):
        return 'half_year'
    if text.endswith('-12-31'):
        return 'annual'
    if re.fullmatch(r'(19\d{2}|20\d{2})一季报', text):
        return 'quarter'
    if re.fullmatch(r'(19\d{2}|20\d{2})(中报|半年报)', text):
        return 'half_year'
    if re.fullmatch(r'(19\d{2}|20\d{2})三季报', text):
        return 'quarter'
    if re.fullmatch(r'(19\d{2}|20\d{2})年报', text):
        return 'annual'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})Q[1-4]', compact, flags=re.IGNORECASE):
        return 'quarter'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})H1', compact, flags=re.IGNORECASE):
        return 'half_year'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', compact, flags=re.IGNORECASE):
        return 'annual'
    if re.fullmatch(r'Q[1-4] (19\d{2}|20\d{2})', text, flags=re.IGNORECASE):
        return 'quarter'
    if re.fullmatch(r'H1 (19\d{2}|20\d{2})', text, flags=re.IGNORECASE):
        return 'half_year'
    return 'unknown'


def _collect_periods_and_basis(result):
    periods = set()
    basis_by_period = {}
    for section_key in PERIOD_SECTIONS:
        section_list = result.get(section_key, [])
        if not isinstance(section_list, list):
            continue
        for item in section_list:
            if not isinstance(item, dict):
                continue
            values = item.get('values', {})
            if isinstance(values, dict):
                for period in values:
                    sp = str(period)
                    periods.add(sp)
            row_basis = item.get('period_basis_by_period', {})
            if isinstance(row_basis, dict):
                for period, basis in row_basis.items():
                    sp = str(period)
                    periods.add(sp)
                    basis_by_period[sp] = _normalize_period_basis(sp, basis)
    for period in list(periods):
        basis_by_period.setdefault(period, _normalize_period_basis(period))
    return sorted(periods), basis_by_period


def _period_sort_key(period):
    text = str(period or '')
    compact = re.sub(r'\s+', '', text.upper())
    if re.fullmatch(r'FY(19\d{2}|20\d{2})Q([1-4])', compact, flags=re.IGNORECASE):
        year = int(compact[2:6])
        quarter = int(compact[-1])
        month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
        return f'{year}-{month_day}'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})H1', compact, flags=re.IGNORECASE):
        return f'{compact[2:6]}-06-30'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', compact, flags=re.IGNORECASE):
        return f'{compact[2:6]}-12-31'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})Q([1-4])', text, flags=re.IGNORECASE):
        year = int(text[2:6])
        quarter = int(text[-1])
        month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
        return f'{year}-{month_day}'
    match = re.fullmatch(r'Q([1-4]) ((?:19|20)\d{2})', text, flags=re.IGNORECASE)
    if match:
        quarter = int(match.group(1))
        year = match.group(2)
        month_day = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[quarter]
        return f'{year}-{month_day}'
    match = re.fullmatch(r'H1 ((?:19|20)\d{2})', text, flags=re.IGNORECASE)
    if match:
        return f'{match.group(1)}-06-30'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})H1', text, flags=re.IGNORECASE):
        return f'{text[2:6]}-06-30'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', text, flags=re.IGNORECASE):
        return f'{text[2:6]}-12-31'
    match = re.fullmatch(r'((?:19|20)\d{2})(一季报|中报|半年报|三季报|年报)', text)
    if match:
        year = match.group(1)
        suffix = match.group(2)
        month_day = {
            '一季报': '03-31',
            '中报': '06-30',
            '半年报': '06-30',
            '三季报': '09-30',
            '年报': '12-31',
        }.get(suffix, '12-31')
        return f'{year}-{month_day}'
    return text


def _selection_basis(period, basis=None):
    text = str(period or '').strip()
    compact = re.sub(r'\s+', '', text.upper())
    normalized = _normalize_period_basis(text, basis)
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', compact, flags=re.IGNORECASE):
        return 'annual'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})H1', compact, flags=re.IGNORECASE):
        return 'half_year'
    if re.fullmatch(r'FY(19\d{2}|20\d{2})Q[1-4]', compact, flags=re.IGNORECASE):
        return 'quarter'
    if re.fullmatch(r'H1 ((?:19|20)\d{2})', text, flags=re.IGNORECASE):
        return 'half_year'
    if re.fullmatch(r'Q[1-4] ((?:19|20)\d{2})', text, flags=re.IGNORECASE):
        return 'quarter'
    return normalized


def _select_latest_periods(periods, basis_by_period):
    annual = sorted([p for p in periods if _selection_basis(p, basis_by_period.get(p)) == 'annual'], key=_period_sort_key)
    interim = sorted([
        p for p in periods
        if _selection_basis(p, basis_by_period.get(p)) in {'quarter', 'half_year', 'report_period', 'cumulative_report_period'}
    ], key=_period_sort_key)
    return (annual[-1] if annual else None, interim[-1] if interim else None)

def _validate_and_fill(field_name, new_val, existing_val_obj, provider_name, concept, tolerance_warn=0.2, tolerance_override=0.5, promote_source_when_close=False):
    """Validate provider value vs existing value using source-trust ranking, then numeric diff heuristics."""
    old_val = existing_val_obj.get('value') if isinstance(existing_val_obj, dict) else existing_val_obj
    if not _value_present(old_val):
        old_val = None
    if new_val is None: return False
    existing_layer = _normalized_source_layer(existing_val_obj.get('source_layer')) if isinstance(existing_val_obj, dict) else None
    existing_rank = _source_trust_rank(existing_layer)
    provider_rank = _source_trust_rank('provider_api')

    if old_val is not None and existing_rank < provider_rank:
        existing_val_obj['value'] = new_val
        existing_val_obj['source_layer'] = 'provider_api'
        existing_val_obj['source_detail'] = provider_name + ': higher-trust override of ' + str(existing_layer or 'unknown') + ' (' + concept + ')'
        return True
    if old_val is not None and existing_rank > provider_rank:
        return False
    if old_val is not None and existing_rank == provider_rank and existing_layer == 'official_web':
        return False

    if old_val is not None and isinstance(old_val, (int, float)) and old_val != 0:
        diff = abs(new_val - old_val) / abs(old_val)
        if diff > tolerance_override:
            existing_val_obj['value'] = new_val
            existing_val_obj['source_layer'] = 'provider_api'
            existing_val_obj['source_detail'] = provider_name + ': OVERRIDE L1 (diff=' + str(round(diff*100)) + '%, concept: ' + concept + ')'
            return True
        elif diff > tolerance_warn:
            print('  WARN ' + field_name + ': provider=' + str(new_val) + ' vs L1=' + str(old_val) + ' (diff=' + str(round(diff*100)) + '%) - keeping L1')
            return False
        if promote_source_when_close:
            current_layer = str(existing_val_obj.get('source_layer') or '')
            current_detail = str(existing_val_obj.get('source_detail') or '')
            new_detail = provider_name + ': validated existing value (diff=' + str(round(diff*100, 1)) + '%, concept: ' + concept + ')'
            if current_layer != 'provider_api' or current_detail != new_detail:
                existing_val_obj['source_layer'] = 'provider_api'
                existing_val_obj['source_detail'] = new_detail
                return True
        return False
    elif old_val is None:
        existing_val_obj['value'] = new_val
        existing_val_obj['source_layer'] = 'provider_api'
        existing_val_obj['source_detail'] = provider_name + ': ' + concept
        return True
    return False

def _fill_from_provider(result, remaining, concept_map, provider_name, target_period, source_period, data):
    filled = 0
    if not source_period:
        return 0
    for section_key in ('income_statement', 'balance_sheet', 'cash_flow'):
        section_list = result.get(section_key, [])
        if not isinstance(section_list, list): continue
        section_map = concept_map.get(section_key, {})
        if not section_map: continue
        for item in section_list:
            concept = item.get('concept', '')
            field_name = section_map.get(concept)
            if not field_name:
                cl = concept.lower().replace(' ', '_')
                field_name = next((f for c, f in section_map.items() if c.lower() == cl), None)
            if not field_name: continue

            target_fields = field_name if isinstance(field_name, list) else [field_name]
            values = item.get('values', {})
            if not values:
                val = item.get('value') or item.get('amount')
                if val is None: continue
            else:
                val = values.get(source_period)
            if val is None: continue

            for target_field in target_fields:
                if target_field in {'capex', 'dividends_paid', 'share_buybacks'}:
                    val_num = _to_float(val)
                    if val_num is not None:
                        val = abs(val_num)
                # Find in actuals (may already be filled by L1)
                actuals_field = None
                for sec in PERIOD_SECTIONS:
                    pobj = data.get(sec, {}).get(target_period, {})
                    if target_field in pobj:
                        actuals_field = pobj[target_field]
                        break
                if actuals_field is None:
                    # Try remaining nulls
                    for n in remaining:
                        if n['section'] == section_key and n['field'] == target_field and n.get('period') == target_period:
                            n['obj']['value'] = val
                            n['obj']['source_layer'] = 'provider_api'
                            n['obj']['source_detail'] = provider_name + ': ' + concept + ' (' + str(source_period) + ')'
                            filled += 1
                            break
                else:
                    if _validate_and_fill(section_key + '.' + target_field, val, actuals_field, provider_name, concept, promote_source_when_close=True):
                        filled += 1
    return filled


def _get_statement_rows(result, section_key):
    payload = result.get(section_key, [])
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get('rows', [])
    return []


def _extract_concept_period_value(result, section_key, concept, source_period):
    if not source_period:
        return None
    for row in _get_statement_rows(result, section_key):
        if str(row.get('concept')) != str(concept):
            continue
        values = row.get('values', {})
        if not isinstance(values, dict):
            continue
        value = values.get(source_period)
        if value is None:
            continue
        return _to_float(value)
    return None


def _fill_cross_statement_fallbacks(data, provider_name, result, target_period_key, source_period):
    if str(provider_name).strip().lower() != 'finmind':
        return 0
    filled = 0
    target_section = data.get('income_statement', {}).get(target_period_key, {})
    if not isinstance(target_section, dict):
        return 0
    target_field = target_section.get('interest_expense')
    if isinstance(target_field, dict) and target_field.get('value') is None:
        val = _extract_concept_period_value(result, 'cash_flow', 'InterestExpense', source_period)
        if val is not None:
            target_field['value'] = abs(val)
            target_field['source_layer'] = 'provider_api'
            target_field['source_detail'] = provider_name + ': cash_flow InterestExpense (' + str(source_period) + ')'
            filled += 1
    return filled


def _parse_kr_local_filing_value(industry, ticker):
    filing_path = os.path.join(_company_root(industry, ticker), '_cache', 'financial-data', 'internal', 'full-filing.md')
    if not os.path.exists(filing_path):
        return None, None
    try:
        text = open(filing_path, 'r', encoding='utf-8', errors='ignore').read()
    except Exception:
        return None, None
    return filing_path, text


def _fill_kr_local_filing_fallbacks(industry, ticker, data):
    market = str(data.get('market') or '').lower()
    if market != 'kr':
        return 0
    filing_path, filing_text = _parse_kr_local_filing_value(industry, ticker)
    if not filing_text:
        return 0

    filled = 0

    def _write_if_empty(section, period_key, field_name, value, detail):
        nonlocal filled
        target = data.get(section, {}).get(period_key, {}).get(field_name)
        if not isinstance(target, dict) or target.get('value') is not None or value is None:
            return
        target['value'] = value
        target['source_layer'] = 'provider_api'
        target['source_detail'] = detail
        filled += 1

    def _write_flat_if_empty(section, field_name, value, detail):
        nonlocal filled
        target = data.get(section, {}).get(field_name)
        if not isinstance(target, dict) or target.get('value') is not None or value is None:
            return
        target['value'] = value
        target['source_layer'] = 'provider_api'
        target['source_detail'] = detail
        filled += 1

    lines = filing_text.splitlines()

    d_and_a_components = []
    for pattern in [
        r'감가상각비에 대한 조정\s+([\d,]+)',
        r'사용권자산감가상각비 조정\s+([\d,]+)',
        r'무형자산상각비에 대한 조정\s+([\d,]+)',
        r'운휴자산감가상각비에대한 조정\s+([\d,]+)',
    ]:
        match = re.search(pattern, filing_text)
        if match:
            value = _to_float(match.group(1).replace(',', ''))
            if value is not None:
                d_and_a_components.append(value)
    if d_and_a_components:
        _write_if_empty(
            'cash_flow',
            'latest_fy',
            'd_and_a',
            sum(d_and_a_components),
            'Local KR filing cache: annual D&A adjustment sum (' + os.path.basename(filing_path) + ')',
        )

    for idx, line in enumerate(lines):
        if '(4) 당기와 전기 중 연구개발활동과 관련하여 지출된 내역은 다음과 같습니다.' not in line:
            continue
        for sub_idx in range(idx, min(idx + 20, len(lines) - 1)):
            if lines[sub_idx].strip() == '합 계':
                value = _to_float(lines[sub_idx + 1].replace(',', '').strip())
                _write_if_empty(
                    'income_statement',
                    'latest_fy',
                    'r_and_d',
                    value,
                    'Local KR filing cache: annual R&D spend total (' + os.path.basename(filing_path) + ')',
                )
                break
        break

    backlog_match = re.search(r"수주잔고는\s*([\d,]+)억원", filing_text)
    if backlog_match:
        backlog_eok = _to_float(backlog_match.group(1).replace(',', ''))
        if backlog_eok is not None:
            _write_flat_if_empty(
                'supplementary',
                'order_backlog',
                backlog_eok * 100000000,
                'Local KR filing cache: disclosed order backlog (' + os.path.basename(filing_path) + ')',
            )

    geo_match = re.search(
        r"당기 \(단위 : 천원\)\s*내수\s*수출\s*지역 합계\s*고객과의 계약에서 생기는 수익\s*([\d,]+)\s*([\d,]+)\s*([\d,]+)",
        filing_text,
        flags=re.MULTILINE,
    )
    if geo_match:
        domestic = _to_float(geo_match.group(1).replace(',', ''))
        export = _to_float(geo_match.group(2).replace(',', ''))
        total = _to_float(geo_match.group(3).replace(',', ''))
        _write_flat_if_empty(
            'supplementary',
            'revenue_by_geography',
            {
                'period': data.get('latest_fy_period'),
                'domestic': domestic,
                'export': export,
                'total': total,
                'unit': 'KRW',
            },
            'Local KR filing cache: domestic/export revenue split (' + os.path.basename(filing_path) + ')',
        )

    if '나. 자기주식 취득 및 처분 현황 해당사항 없음' in filing_text:
        _write_if_empty(
            'cash_flow',
            'latest_fy',
            'share_buybacks',
            0.0,
            'Local KR filing cache: no treasury-share acquisition/disposal disclosed (' + os.path.basename(filing_path) + ')',
        )

    if (
        '영업권 이외의 무형자산 합계' in filing_text
        and not re.search(r'(?<!이외의 무형자산 합계\s)영업권\s+[()\d,\-]', filing_text)
    ):
        _write_if_empty(
            'balance_sheet',
            'latest_fy',
            'goodwill',
            0.0,
            'Local KR filing cache: no standalone goodwill line disclosed in annual intangible note (' + os.path.basename(filing_path) + ')',
        )

    return filled


def _fill_kr_quarterly_filing_fallbacks(data, q_result, source_period):
    market = str(data.get('market') or '').lower()
    if market != 'kr' or not source_period:
        return 0
    filing = (q_result or {}).get('filing') or {}
    filing_text = filing.get('markdown') if isinstance(filing, dict) else None
    if not filing_text:
        return 0

    filled = 0

    def _write_if_empty(field_name, value, detail):
        nonlocal filled
        target = data.get('cash_flow', {}).get('latest_quarter', {}).get(field_name) if field_name in {'d_and_a', 'dividends_paid', 'share_buybacks'} else \
                 data.get('income_statement', {}).get('latest_quarter', {}).get(field_name) if field_name in {'r_and_d'} else \
                 data.get('balance_sheet', {}).get('latest_quarter', {}).get(field_name)
        existing_detail = str(target.get('source_detail') or '') if isinstance(target, dict) else ''
        can_overwrite = existing_detail.startswith('KR quarterly filing cache:')
        if not isinstance(target, dict) or (target.get('value') is not None and not can_overwrite) or value is None:
            return
        target['value'] = value
        target['source_layer'] = 'provider_api'
        target['source_detail'] = detail
        filled += 1

    if _selection_basis(source_period) == 'quarter':
        rd_match = re.search(r'연구개발비용 계\s*\n\s*([\d,]+)', filing_text)
        if rd_match:
            rd_val = _to_float(rd_match.group(1).replace(',', ''))
            if rd_val is not None:
                unit_multiplier = 1000000 if '(단위 : 백만원)' in filing_text[max(0, rd_match.start() - 200): rd_match.start() + 200] else 1
                _write_if_empty(
                    'r_and_d',
                    rd_val * unit_multiplier,
                    'KR quarterly filing cache: disclosed R&D spend total (' + str(source_period) + ')',
                )

        d_and_a_parts = []
        for pattern in [
            r'감가상각비, 유형자산[^\n]*\(([\d,]+)\)\s*$',
            r'기타 상각비, 영업권 이외의 무형자산[^\n]*\(([\d,]+)\)\s*$',
            r'사용권자산감가상각비[^\n]*\(([\d,]+)\)\s*$',
        ]:
            match = re.search(pattern, filing_text, flags=re.M)
            if not match:
                continue
            values = [_to_float(g.replace(',', '')) for g in match.groups()]
            values = [abs(v) for v in values if v is not None]
            if not values:
                continue
            d_and_a_parts.append(values[-1])
        if d_and_a_parts:
            _write_if_empty(
                'd_and_a',
                sum(d_and_a_parts),
                'KR quarterly filing cache: disclosed depreciation/amortization total (' + str(source_period) + ')',
            )

        dividend_matches = re.findall(r'소유주에 대한 배분으로 인식된 배당금[^\n]*', filing_text)
        nums = []
        for line in dividend_matches:
            nums.extend([
                _to_float(token.replace(',', '').replace('(', '').replace(')', ''))
                for token in re.findall(r'\(?[\d,]+\)?', line)
            ])
        nums = [abs(v) for v in nums if v is not None]
        if nums:
            _write_if_empty(
                'dividends_paid',
                max(nums),
                'KR quarterly filing cache: owner distribution dividend recognized in quarter (' + str(source_period) + ')',
            )

    if (
        '영업권 이외의 무형자산 합계' in filing_text
        and not re.search(r'(?<!이외의 무형자산 합계\s)영업권\s+[()\d,\-]', filing_text)
    ):
        _write_if_empty(
            'goodwill',
            0.0,
            'KR quarterly filing cache: no standalone goodwill line disclosed (' + str(source_period) + ')',
        )

    return filled


def _jp_parse_signed_number(text):
    token = str(text or '').strip().replace(',', '')
    negative = token.startswith(('△', '-', '−'))
    token = token.lstrip('△-−').strip()
    if not token.isdigit():
        return None
    value = int(token)
    return -value if negative else value


def _jp_extract_current_value(section_text, label, occurrence='first'):
    if not section_text:
        return None
    idx = section_text.find(label) if occurrence != 'last' else section_text.rfind(label)
    if idx < 0:
        return None
    values = []
    for raw_line in section_text[idx + len(label):].splitlines()[:12]:
        line = raw_line.strip()
        if not line:
            continue
        if line in {'－', '-', '−', '—'}:
            continue
        if re.fullmatch(r'[△\-−]?\s*(?:\d{1,3}(?:,\d{3})+|\d+)', line):
            parsed = _jp_parse_signed_number(line)
            if parsed is not None:
                values.append(parsed)
            continue
        if values:
            break
    while len(values) >= 2 and abs(values[0]) < 100 and any(abs(v) >= 100 for v in values[1:]):
        values.pop(0)
    if not values:
        return None
    if len(values) == 1:
        return abs(values[0])
    return abs(values[-1])


def _jp_extract_summary_triplet_current(text, label):
    if not text:
        return None
    idx = text.find(label)
    if idx < 0:
        return None
    values = []
    for raw_line in text[idx + len(label):].splitlines()[:10]:
        line = raw_line.strip()
        if not line or line in {'－', '-', '−', '—'}:
            continue
        if re.fullmatch(r'[△\-−]?\s*(?:\d{1,3}(?:,\d{3})+|\d+)', line):
            parsed = _jp_parse_signed_number(line)
            if parsed is not None:
                values.append(parsed)
            continue
        if values:
            break
    while len(values) >= 2 and abs(values[0]) < 100 and any(abs(v) >= 100 for v in values[1:]):
        values.pop(0)
    if len(values) >= 3:
        return abs(values[1])
    if len(values) == 2:
        return abs(values[-1])
    if len(values) == 1:
        return abs(values[0])
    return None


def _fill_jp_quarterly_filing_fallbacks(data, q_result, source_period):
    if not source_period or 'H1' not in str(source_period).upper():
        return 0
    filing = (q_result or {}).get('filing') or {}
    filing_text = filing.get('markdown') if isinstance(filing, dict) else None
    if not filing_text:
        return 0

    income_anchor = '【要約中間連結包括利益計算書】'
    cash_anchor = '【要約中間連結キャッシュ・フロー計算書】'
    balance_anchor = '【要約中間連結財政状態計算書】'
    income_start = filing_text.find(income_anchor)
    cash_start = filing_text.find(cash_anchor)
    balance_start = filing_text.find(balance_anchor)
    income_section = filing_text[income_start:cash_start] if income_start >= 0 and cash_start > income_start else ''
    cash_section = filing_text[cash_start:] if cash_start >= 0 else ''
    balance_section = filing_text[balance_start:income_start] if balance_start >= 0 and income_start > balance_start else ''
    if not income_section and not cash_section and not balance_section:
        return 0

    def _set_period_field(section_name, field_name, value, detail):
        if value is None:
            return 0
        period_obj = data.get(section_name, {}).get('latest_quarter', {})
        target = period_obj.get(field_name)
        if not isinstance(target, dict):
            return 0
        existing_value = target.get('value')
        existing_detail = str(target.get('source_detail') or '')
        existing_layer = _normalized_source_layer(target.get('source_layer'))
        can_overwrite = (
            existing_value is None
            or _can_overwrite_source(existing_layer, 'provider_api', allow_same_tier=False)
            or existing_detail.startswith('edinet-tools:')
            or existing_detail.startswith('JP quarterly filing cache:')
        )
        if not can_overwrite:
            return 0
        if existing_value == float(value) and existing_detail == detail and existing_layer == 'provider_api':
            return 0
        target['value'] = float(value)
        target['source_layer'] = 'provider_api'
        target['source_detail'] = detail
        return 1

    filled = 0
    income_map = {
        'revenue': '売上収益',
        'cost_of_revenue': '売上原価',
        'gross_profit': '売上総利益',
        'sg_and_a': '販売費及び一般管理費',
        'r_and_d': '研究開発費',
        'operating_income': '営業利益',
        'interest_expense': '金融費用',
        'income_tax': '法人所得税費用',
    }
    for field_name, label in income_map.items():
        value = _jp_extract_current_value(income_section, label)
        if value is None and field_name == 'income_tax':
            value = _jp_extract_current_value(income_section, '法人所得税費用')
        if value is not None:
            detail = 'JP quarterly filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('income_statement', field_name, value * 1000000, detail)
    net_income_value = _jp_extract_current_value(income_section, '親会社の所有者に帰属する中間利益')
    if net_income_value is None:
        net_income_value = _jp_extract_current_value(income_section, '中間利益')
    if net_income_value is not None:
        detail = 'JP quarterly filing cache: disclosed net_income (' + str(source_period) + ')'
        filled += _set_period_field('income_statement', 'net_income', net_income_value * 1000000, detail)

    # EBIT is not always explicitly disclosed in Japanese H1 filings; use disclosed operating profit as the closest
    # structured fallback only when the current value is still provider-gap/web fallback.
    operating_income_value = data.get('income_statement', {}).get('latest_quarter', {}).get('operating_income', {}).get('value')
    if operating_income_value is not None:
        filled += _set_period_field(
            'income_statement',
            'ebit',
            operating_income_value,
            'JP quarterly filing cache: proxied ebit from disclosed operating_income (' + str(source_period) + ')'
        )

    balance_map = {
        'cash': ('現金及び現金同等物', 'first'),
        'accounts_receivable': ('営業債権及びその他の債権', 'first'),
        'inventory': ('棚卸資産', 'first'),
        'current_liabilities': ('流動負債合計', 'first'),
        'short_term_debt': ('社債及び借入金', 'first'),
        'long_term_debt': ('社債及び借入金', 'last'),
    }
    for field_name, (label, occurrence) in balance_map.items():
        value = _jp_extract_current_value(balance_section, label, occurrence=occurrence)
        if value is not None:
            detail = 'JP quarterly filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('balance_sheet', field_name, value * 1000000, detail)

    cash_map = {
        'd_and_a': ('減価償却費及び償却費', 'first'),
        'dividends_paid': ('配当金の支払額', 'first'),
        'share_buybacks': ('自己株式の取得による支出', 'first'),
    }
    for field_name, (label, occurrence) in cash_map.items():
        value = _jp_extract_current_value(cash_section, label, occurrence=occurrence)
        if value is not None:
            detail = 'JP quarterly filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('cash_flow', field_name, value * 1000000, detail)
    operating_cf_summary = _jp_extract_summary_triplet_current(filing_text, '営業活動によるキャッシュ・フロー')
    if operating_cf_summary is not None:
        detail = 'JP quarterly filing cache: disclosed operating_cf from summary metrics (' + str(source_period) + ')'
        filled += _set_period_field('cash_flow', 'operating_cf', operating_cf_summary * 1000000, detail)

    capex_value = _jp_extract_current_value(cash_section, '有形固定資産の取得による支出')
    if capex_value is not None:
        detail = 'JP quarterly filing cache: disclosed capex from PPE acquisitions (' + str(source_period) + ')'
        filled += _set_period_field('cash_flow', 'capex', capex_value * 1000000, detail)

    return filled


def _fill_jp_annual_filing_fallbacks(data, annual_result, source_period):
    if not source_period or 'FY' not in str(source_period).upper():
        return 0
    filing = (annual_result or {}).get('filing') or {}
    filing_text = filing.get('markdown') if isinstance(filing, dict) else None
    if not filing_text:
        return 0

    income_anchor = '【連結包括利益計算書】'
    cash_anchor = '【連結キャッシュ・フロー計算書】'
    balance_anchor = '【連結財政状態計算書】'
    income_start = filing_text.find(income_anchor)
    cash_start = filing_text.find(cash_anchor)
    balance_start = filing_text.find(balance_anchor)
    income_section = filing_text[income_start:cash_start] if income_start >= 0 and cash_start > income_start else ''
    cash_section = filing_text[cash_start:] if cash_start >= 0 else ''
    balance_section = filing_text[balance_start:income_start] if balance_start >= 0 and income_start > balance_start else ''
    if not income_section and not cash_section and not balance_section:
        return 0

    def _set_period_field(section_name, field_name, value, detail):
        if value is None:
            return 0
        period_obj = data.get(section_name, {}).get('latest_fy', {})
        target = period_obj.get(field_name)
        if not isinstance(target, dict):
            return 0
        existing_detail = str(target.get('source_detail') or '')
        existing_layer = _normalized_source_layer(target.get('source_layer'))
        can_overwrite = (
            target.get('value') is None
            or _can_overwrite_source(existing_layer, 'provider_api', allow_same_tier=False)
            or existing_detail.startswith('JP annual filing cache:')
        )
        if not can_overwrite:
            return 0
        target['value'] = float(value)
        target['source_layer'] = 'provider_api'
        target['source_detail'] = detail
        return 1

    filled = 0
    income_map = {
        'revenue': '売上収益',
        'cost_of_revenue': '売上原価',
        'gross_profit': '売上総利益',
        'sg_and_a': '販売費及び一般管理費',
        'r_and_d': '研究開発費',
        'operating_income': '営業利益',
        'interest_expense': '金融費用',
        'income_tax': '法人所得税費用',
        'net_income': '当期利益',
    }
    for field_name, label in income_map.items():
        value = _jp_extract_current_value(income_section, label)
        if value is not None:
            detail = 'JP annual filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('income_statement', field_name, value * 1000000, detail)

    annual_operating_income = data.get('income_statement', {}).get('latest_fy', {}).get('operating_income', {}).get('value')
    if annual_operating_income is not None:
        filled += _set_period_field(
            'income_statement',
            'ebit',
            annual_operating_income,
            'JP annual filing cache: proxied ebit from disclosed operating_income (' + str(source_period) + ')'
        )

    balance_map = {
        'cash': ('現金及び現金同等物', 'first'),
        'accounts_receivable': ('営業債権及びその他の債権', 'first'),
        'inventory': ('棚卸資産', 'first'),
        'total_assets': ('資産合計', 'first'),
        'current_liabilities': ('流動負債合計', 'first'),
        'short_term_debt': ('社債及び借入金', 'first'),
        'long_term_debt': ('社債及び借入金', 'last'),
        'total_equity_parent': ('親会社の所有者に帰属する持分合計', 'first'),
    }
    for field_name, (label, occurrence) in balance_map.items():
        value = _jp_extract_current_value(balance_section, label, occurrence=occurrence)
        if value is not None:
            detail = 'JP annual filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('balance_sheet', field_name, value * 1000000, detail)

    cash_map = {
        'd_and_a': ('減価償却費及び償却費', 'first'),
        'dividends_paid': ('配当金の支払額', 'first'),
        'share_buybacks': ('自己株式の取得による支出', 'first'),
    }
    for field_name, (label, occurrence) in cash_map.items():
        value = _jp_extract_current_value(cash_section, label, occurrence=occurrence)
        if value is not None:
            detail = 'JP annual filing cache: disclosed ' + field_name + ' (' + str(source_period) + ')'
            filled += _set_period_field('cash_flow', field_name, value * 1000000, detail)

    capex_value = _jp_extract_current_value(cash_section, '有形固定資産の取得による支出')
    if capex_value is not None:
        detail = 'JP annual filing cache: disclosed capex from PPE acquisitions (' + str(source_period) + ')'
        filled += _set_period_field('cash_flow', 'capex', capex_value * 1000000, detail)

    return filled

def _period_label(period, basis=None):
    text = str(period or '').strip()
    compact = re.sub(r'\s+', '', text.upper())
    normalized_basis = _normalize_period_basis(text, basis)
    match = re.fullmatch(r'FY((?:19|20)\d{2})Q([1-4])', compact, flags=re.IGNORECASE)
    if match:
        return 'Q' + match.group(2) + ' FY' + match.group(1)
    match = re.fullmatch(r'FY((?:19|20)\d{2})H1', compact, flags=re.IGNORECASE)
    if match:
        return 'H1 FY' + match.group(1)
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', compact, flags=re.IGNORECASE):
        return compact.upper()
    match = re.fullmatch(r'FY((?:19|20)\d{2})Q([1-4])', text, flags=re.IGNORECASE)
    if match:
        return 'Q' + match.group(2) + ' FY' + match.group(1)
    match = re.fullmatch(r'FY((?:19|20)\d{2})H1', text, flags=re.IGNORECASE)
    if match:
        return 'H1 FY' + match.group(1)
    if re.fullmatch(r'FY(19\d{2}|20\d{2})', text, flags=re.IGNORECASE):
        return text.upper()
    match = re.fullmatch(r'Q([1-4]) ((?:19|20)\d{2})', text, flags=re.IGNORECASE)
    if match:
        return 'Q' + match.group(1) + ' FY' + match.group(2)
    match = re.fullmatch(r'H1 ((?:19|20)\d{2})', text, flags=re.IGNORECASE)
    if match:
        return 'H1 FY' + match.group(1)
    match = re.fullmatch(r'((?:19|20)\d{2})(一季报|中报|半年报|三季报|年报)', text)
    if match:
        year, suffix = match.groups()
        if suffix == '一季报':
            return 'Q1 FY' + year
        if suffix in {'中报', '半年报'}:
            return 'H1 FY' + year
        if suffix == '三季报':
            return 'Q3 FY' + year
        if suffix == '年报':
            return 'FY' + year
    year = text[:4] if len(text) >= 4 else ''
    if normalized_basis == 'half_year':
        return 'H1 FY' + year
    if normalized_basis == 'annual':
        return 'FY' + year
    if text.endswith('-03-31'):
        return 'Q1 FY' + year
    if text.endswith('-09-30'):
        return 'Q3 FY' + year
    if text.endswith('-12-31') and normalized_basis == 'quarter':
        return 'Q4 FY' + year
    return text


def _period_basis_from_date(period):
    return _normalize_period_basis(period)


def _to_float(value):
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


def _value_present(value):
    if value is None:
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return True


def _sanitize_nonfinite_values(obj):
    if isinstance(obj, dict):
        if 'value' in obj and not _value_present(obj.get('value')):
            obj['value'] = None
        for value in obj.values():
            _sanitize_nonfinite_values(value)
    elif isinstance(obj, list):
        for item in obj:
            _sanitize_nonfinite_values(item)


def _normalize_cash_flow_signs(data):
    for period_key in ('latest_fy', 'latest_quarter'):
        period_obj = data.get('cash_flow', {}).get(period_key, {})
        if not isinstance(period_obj, dict):
            continue
        for field_name in ('capex', 'dividends_paid', 'share_buybacks'):
            field_obj = period_obj.get(field_name)
            if not isinstance(field_obj, dict):
                continue
            value = field_obj.get('value')
            if isinstance(value, (int, float)) and math.isfinite(float(value)) and value < 0:
                field_obj['value'] = abs(value)


def _normalized_source_layer(layer):
    return SOURCE_LAYER_ALIAS.get(layer, layer)


def _source_trust_rank(layer):
    return SOURCE_TRUST_RANK.get(_normalized_source_layer(layer), -1)


def _can_overwrite_source(existing_layer, incoming_layer, allow_same_tier=False):
    existing_rank = _source_trust_rank(existing_layer)
    incoming_rank = _source_trust_rank(incoming_layer)
    if existing_rank < 0:
        return True
    if incoming_rank > existing_rank:
        return True
    if incoming_rank < existing_rank:
        return False
    return allow_same_tier


def _derived_source_layer(*field_objs):
    layers = []
    for obj in field_objs:
        if not isinstance(obj, dict):
            continue
        if not _value_present(obj.get('value')):
            continue
        layer = obj.get('source_layer')
        if layer in ('provider_api', 'official_web'):
            layers.append(layer)
    if not layers:
        return 'derived'
    if 'official_web' in layers:
        return 'official_web'
    return 'provider_api'


def _safe_console_text(text):
    if text is None:
        return ''
    rendered = str(text)
    try:
        rendered.encode(sys.stdout.encoding or 'utf-8')
        return rendered
    except UnicodeEncodeError:
        return rendered.encode('ascii', errors='backslashreplace').decode('ascii')


def _apply_latest_period_metadata(data, field_prefix, source_period, basis):
    if not source_period:
        return
    normalized_basis = _normalize_period_basis(source_period, basis)
    if field_prefix == 'latest_fy':
        data['latest_fy_period'] = source_period
    else:
        data['latest_quarter_period'] = source_period
        data['latest_quarter_period_basis'] = normalized_basis
        data['latest_quarter_period_label'] = _period_label(source_period, normalized_basis)
    for section in PERIOD_SECTIONS:
        period_obj = data.get(section, {}).get(field_prefix, {})
        if isinstance(period_obj, dict):
            period_obj['period'] = source_period if field_prefix == 'latest_fy' else data.get('latest_quarter_period_label')


def _segment_default_period(data):
    return data.get('latest_fy_period') or data.get('latest_quarter_period') or ''


def _segment_default_unit(data):
    return data.get('currency') or None


def _segment_base_total(data, metric, period):
    metric_map = {
        'revenue': ('income_statement', 'revenue'),
        'operating_income': ('income_statement', 'operating_income'),
        'ebit': ('income_statement', 'ebit'),
        'gross_profit': ('income_statement', 'gross_profit'),
    }
    target = metric_map.get(str(metric or ''))
    if not target:
        return None
    section_name, field_name = target
    period_candidates = [
        ('latest_fy', data.get('latest_fy_period')),
        ('latest_quarter', data.get('latest_quarter_period')),
        ('latest_quarter', data.get('latest_quarter_period_label')),
    ]
    for period_key, candidate in period_candidates:
        if not candidate or str(candidate) != str(period):
            continue
        field_obj = data.get(section_name, {}).get(period_key, {}).get(field_name)
        if isinstance(field_obj, dict) and _value_present(field_obj.get('value')):
            return _to_float(field_obj.get('value'))
    return None


def _segment_type_from_name(name):
    text = str(name or '').lower()
    if any(token in text for token in ['america', 'emea', 'asia', 'china', 'europe', 'japan', 'korea', 'domestic', 'export', 'other']):
        return 'geography'
    return 'business_line'


def _segment_period_info(period, basis=None):
    sort_key = _period_sort_key(period)
    match = re.fullmatch(r"((?:19|20)\d{2})-(\d{2}-\d{2})", str(sort_key))
    if not match:
        return None
    return {
        "sort_key": str(sort_key),
        "year": int(match.group(1)),
        "month_day": match.group(2),
        "basis": _selection_basis(period, basis),
    }


def _segment_entry_key(entry):
    return (
        str(entry.get("name") or ""),
        str(entry.get("type") or ""),
        str(entry.get("metric") or ""),
        str(entry.get("period") or ""),
    )


def _segment_group_key(entry):
    return (
        str(entry.get("name") or ""),
        str(entry.get("type") or ""),
        str(entry.get("metric") or ""),
    )


def _segment_default_denominator_metric(metric):
    token = str(metric or "")
    if token in {"gross_profit", "operating_income", "ebit", "net_income"}:
        return "revenue"
    return None


def _segment_counterpart(entries_by_key, entry, metric):
    target_key = (
        str(entry.get("name") or ""),
        str(entry.get("type") or ""),
        str(metric or ""),
        str(entry.get("period") or ""),
    )
    counterpart = entries_by_key.get(target_key)
    if isinstance(counterpart, dict):
        return counterpart
    return None


def _segment_denominator_total(entry, data, entries_by_key):
    direct_value = _to_float(entry.get("denominator_value"))
    if _value_present(direct_value):
        return float(direct_value)
    denominator_metric = str(entry.get("denominator_metric") or "").strip()
    if not denominator_metric:
        denominator_metric = _segment_default_denominator_metric(entry.get("metric"))
    if not denominator_metric:
        return None
    counterpart = _segment_counterpart(entries_by_key, entry, denominator_metric)
    if counterpart and _value_present(counterpart.get("value")):
        return float(counterpart.get("value"))
    return _segment_base_total(data, denominator_metric, entry.get("period"))


def _segment_comparable_entries(entry, entries_by_group):
    group_entries = list(entries_by_group.get(_segment_group_key(entry), []))
    current_info = _segment_period_info(entry.get("period"))
    if not current_info:
        return (None, None)
    prior_year = None
    prior_period = None
    same_basis_prior = None
    for candidate in group_entries:
        if candidate is entry:
            continue
        candidate_info = _segment_period_info(candidate.get("period"))
        if not candidate_info:
            continue
        if (
            candidate_info["month_day"] == current_info["month_day"]
            and candidate_info["year"] == current_info["year"] - 1
        ):
            if prior_year is None or candidate_info["sort_key"] > _segment_period_info(prior_year.get("period"))["sort_key"]:
                prior_year = candidate
        if candidate_info["sort_key"] < current_info["sort_key"]:
            if prior_period is None or candidate_info["sort_key"] > _segment_period_info(prior_period.get("period"))["sort_key"]:
                prior_period = candidate
            if candidate_info["basis"] == current_info["basis"]:
                if same_basis_prior is None or candidate_info["sort_key"] > _segment_period_info(same_basis_prior.get("period"))["sort_key"]:
                    same_basis_prior = candidate
    return (prior_year, same_basis_prior or prior_period)


def _derive_segment_numeric_fields(entries, data):
    entries_by_key = {
        _segment_entry_key(entry): entry
        for entry in entries
        if isinstance(entry, dict)
    }
    entries_by_group = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entries_by_group.setdefault(_segment_group_key(entry), []).append(entry)

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        for numeric_key in SEGMENT_OPTIONAL_NUMERIC_KEYS + SEGMENT_REFERENCE_NUMERIC_KEYS:
            numeric_value = _to_float(entry.get(numeric_key))
            if _value_present(numeric_value):
                entry[numeric_key] = float(numeric_value)
            elif numeric_key in entry and not _value_present(entry.get(numeric_key)):
                entry.pop(numeric_key, None)
        for legacy_key, canonical_key in SEGMENT_NUMERIC_KEY_ALIASES.items():
            legacy_value = _to_float(entry.get(legacy_key))
            canonical_value = _to_float(entry.get(canonical_key))
            if _value_present(legacy_value) and not _value_present(canonical_value):
                entry[canonical_key] = float(legacy_value)
            entry.pop(legacy_key, None)

        denominator_metric = str(entry.get("denominator_metric") or "").strip()
        if denominator_metric:
            entry["denominator_metric"] = denominator_metric

        base_total = _segment_base_total(data, entry.get("metric"), entry.get("period"))
        denominator_total = _segment_denominator_total(entry, data, entries_by_key)
        value = _to_float(entry.get("value"))
        pct_of_total = _to_float(entry.get("pct_of_total"))
        ratio = _to_float(entry.get("ratio"))
        margin_pct = _to_float(entry.get("margin_pct"))

        ratio_implies_total_share = not _value_present(denominator_total)
        if _value_present(pct_of_total) and not _value_present(ratio) and ratio_implies_total_share:
            ratio = float(pct_of_total) / 100.0
            entry["ratio"] = round(ratio, 6)
        elif _value_present(ratio) and not _value_present(pct_of_total) and ratio_implies_total_share:
            pct_of_total = float(ratio) * 100.0
            entry["pct_of_total"] = round(pct_of_total, 4)

        if not _value_present(value):
            if _value_present(ratio) and _value_present(denominator_total):
                value = float(denominator_total) * float(ratio)
                entry["value"] = value
            elif _value_present(ratio) and _value_present(base_total):
                value = float(base_total) * float(ratio)
                entry["value"] = value
            elif _value_present(pct_of_total) and _value_present(base_total):
                value = float(base_total) * float(pct_of_total) / 100.0
                entry["value"] = value
            elif _value_present(margin_pct) and _value_present(denominator_total):
                value = float(denominator_total) * float(margin_pct) / 100.0
                entry["value"] = value
        else:
            entry["value"] = float(value)
            value = float(entry["value"])

        if _value_present(entry.get("value")):
            value = float(entry["value"])
            if not _value_present(pct_of_total) and _value_present(base_total) and float(base_total) != 0.0:
                pct_of_total = float(value) / float(base_total) * 100.0
                entry["pct_of_total"] = round(pct_of_total, 4)
            if not _value_present(ratio) and _value_present(denominator_total) and float(denominator_total) != 0.0:
                ratio = float(value) / float(denominator_total)
                entry["ratio"] = round(ratio, 6)
            elif not _value_present(ratio) and _value_present(base_total) and float(base_total) != 0.0:
                ratio = float(value) / float(base_total)
                entry["ratio"] = round(ratio, 6)
            if not _value_present(margin_pct) and _value_present(denominator_total) and float(denominator_total) != 0.0:
                margin_pct = float(value) / float(denominator_total) * 100.0
                entry["margin_pct"] = round(margin_pct, 4)

        prior_year_entry, prior_period_entry = _segment_comparable_entries(entry, entries_by_group)
        prior_year_value = _to_float(entry.get("prior_year_value"))
        if not _value_present(prior_year_value) and isinstance(prior_year_entry, dict) and _value_present(prior_year_entry.get("value")):
            prior_year_value = float(prior_year_entry.get("value"))
            entry["prior_year_value"] = prior_year_value
        if not _value_present(entry.get("value")) and _value_present(prior_year_value) and _value_present(entry.get("yoy_pct")):
            entry["value"] = float(prior_year_value) * (1.0 + float(entry["yoy_pct"]) / 100.0)
        if _value_present(entry.get("value")) and _value_present(prior_year_value) and float(prior_year_value) != 0.0 and not _value_present(entry.get("yoy_pct")):
            entry["yoy_pct"] = round((float(entry["value"]) / float(prior_year_value) - 1.0) * 100.0, 4)

        prior_period_value = _to_float(entry.get("prior_period_value"))
        if not _value_present(prior_period_value) and isinstance(prior_period_entry, dict) and _value_present(prior_period_entry.get("value")):
            prior_period_value = float(prior_period_entry.get("value"))
            entry["prior_period_value"] = prior_period_value
        if not _value_present(entry.get("value")) and _value_present(prior_period_value) and _value_present(entry.get("sequential_pct")):
            entry["value"] = float(prior_period_value) * (1.0 + float(entry["sequential_pct"]) / 100.0)
        if _value_present(entry.get("value")) and _value_present(prior_period_value) and float(prior_period_value) != 0.0 and not _value_present(entry.get("sequential_pct")):
            entry["sequential_pct"] = round((float(entry["value"]) / float(prior_period_value) - 1.0) * 100.0, 4)

    return entries


def _normalize_segment_entry(entry, data, default_layer=None, default_detail=None):
    if not isinstance(entry, dict):
        return None
    normalized = dict(entry)
    normalized['name'] = str(normalized.get('name') or '').strip()
    if not normalized['name']:
        return None
    segment_type = normalized.get('type')
    if segment_type not in SEGMENT_TYPE_VALUES:
        segment_type = _segment_type_from_name(normalized['name'])
    normalized['type'] = segment_type
    normalized['period'] = str(normalized.get('period') or _segment_default_period(data) or '')
    metric = normalized.get('metric')
    if not metric:
        if _value_present(normalized.get('revenue')):
            metric = 'revenue'
        elif _value_present(normalized.get('operating_income')):
            metric = 'operating_income'
        else:
            metric = 'revenue'
    normalized['metric'] = str(metric)
    for numeric_key in SEGMENT_OPTIONAL_NUMERIC_KEYS:
        numeric_value = _to_float(normalized.get(numeric_key))
        if _value_present(numeric_value):
            normalized[numeric_key] = numeric_value
    for numeric_key in SEGMENT_REFERENCE_NUMERIC_KEYS:
        numeric_value = _to_float(normalized.get(numeric_key))
        if _value_present(numeric_value):
            normalized[numeric_key] = numeric_value
    for text_key in SEGMENT_OPTIONAL_TEXT_KEYS:
        text_value = str(normalized.get(text_key) or '').strip()
        if text_value:
            normalized[text_key] = text_value
    pct_of_total = _to_float(normalized.get('pct_of_total'))
    if _value_present(pct_of_total):
        normalized['pct_of_total'] = pct_of_total
    if not _value_present(normalized.get('value')):
        if normalized['metric'] == 'revenue' and _value_present(normalized.get('revenue')):
            normalized['value'] = _to_float(normalized.get('revenue'))
        elif normalized['metric'] == 'operating_income' and _value_present(normalized.get('operating_income')):
            normalized['value'] = _to_float(normalized.get('operating_income'))
        elif _value_present(pct_of_total):
            base_total = _segment_base_total(data, normalized['metric'], normalized['period'])
            if _value_present(base_total):
                normalized['value'] = float(base_total) * float(pct_of_total) / 100.0
    else:
        normalized['value'] = _to_float(normalized.get('value'))
    if 'pct_of_total' not in normalized and _value_present(normalized.get('value')):
        base_total = _segment_base_total(data, normalized['metric'], normalized['period'])
        if _value_present(base_total) and float(base_total) != 0.0:
            normalized['pct_of_total'] = round(float(normalized['value']) / float(base_total) * 100.0, 4)
    normalized['unit'] = normalized.get('unit') or _segment_default_unit(data)
    if not normalized.get('source_layer'):
        normalized['source_layer'] = default_layer
    if not normalized.get('source_detail'):
        normalized['source_detail'] = default_detail
    return normalized


def _normalize_segment_entries(entries, data, default_layer=None, default_detail=None):
    normalized = []
    for entry in entries or []:
        segment = _normalize_segment_entry(entry, data, default_layer, default_detail)
        if segment:
            normalized.append(segment)
    return _derive_segment_numeric_fields(normalized, data)


def _dedupe_segments(entries):
    seen = set()
    deduped = []
    for entry in entries:
        key = (
            str(entry.get('name') or ''),
            str(entry.get('type') or ''),
            str(entry.get('period') or ''),
            str(entry.get('metric') or ''),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _sync_segments_from_supplementary(data):
    segments_obj = data.setdefault('segments', {})
    existing = segments_obj.get('segments')
    if not isinstance(existing, list):
        existing = []
    existing = _normalize_segment_entries(existing, data)

    geo_obj = data.get('supplementary', {}).get('revenue_by_geography')
    if isinstance(geo_obj, dict):
        geo_value = geo_obj.get('value')
        if isinstance(geo_value, dict):
            period = str(geo_value.get('period') or _segment_default_period(data) or '')
            unit = geo_value.get('unit') or _segment_default_unit(data)
            for name, raw_value in geo_value.items():
                if name in {'period', 'unit', 'total'}:
                    continue
                value = _to_float(raw_value)
                if not _value_present(value):
                    continue
                existing.append({
                    'name': str(name),
                    'type': 'geography',
                    'period': period,
                    'metric': 'revenue',
                    'value': value,
                    'unit': unit,
                    'source_layer': geo_obj.get('source_layer'),
                    'source_detail': geo_obj.get('source_detail'),
                })

    segments_obj['segments'] = _dedupe_segments(existing)
    status = segments_obj.get('status')
    if segments_obj['segments']:
        segments_obj['status'] = 'extracted'
    elif status not in SEGMENT_STATUS_VALUES:
        segments_obj['status'] = None


def _provider_gap_reason(detail):
    text = str(detail or '')
    match = re.search(r'reason=([a-z_]+)', text)
    if match:
        token = match.group(1)
        if token in PROVIDER_GAP_REASONS:
            return token
    lowered = text.lower()
    if 'not_disclosed' in lowered:
        return 'not_disclosed'
    if 'provider_unavailable' in lowered:
        return 'provider_unavailable'
    if 'provider-gap' in lowered:
        return 'official_source_available_not_extracted'
    return None


def _finalize_segments_status(data, tried_web=False):
    _sync_segments_from_supplementary(data)
    segments_obj = data.setdefault('segments', {})
    if segments_obj.get('segments'):
        segments_obj['status'] = 'extracted'
        return
    status = segments_obj.get('status')
    if status in {'provider_unavailable', 'not_disclosed'}:
        return
    if tried_web:
        segments_obj['status'] = 'pending_official_extraction'
    elif status not in SEGMENT_STATUS_VALUES:
        segments_obj['status'] = None


def _sync_supplementary_from_segments(data):
    supplementary = data.setdefault('supplementary', {})
    existing = supplementary.get('revenue_by_geography')
    if isinstance(existing, dict) and isinstance(existing.get('value'), dict):
        return

    segment_entries = data.get('segments', {}).get('segments')
    if not isinstance(segment_entries, list):
        return

    geography_segments = []
    for entry in segment_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get('type') != 'geography' or entry.get('metric') != 'revenue':
            continue
        value = _to_float(entry.get('value'))
        if not _value_present(value):
            continue
        geography_segments.append(entry)
    if not geography_segments:
        return

    preferred_periods = [
        data.get('latest_fy_period'),
        data.get('latest_quarter_period'),
        data.get('latest_quarter_period_label'),
    ]
    selected = []
    period = None
    for candidate in preferred_periods:
        if not candidate:
            continue
        selected = [entry for entry in geography_segments if str(entry.get('period') or '') == str(candidate)]
        if selected:
            period = str(candidate)
            break
    if not selected:
        selected = geography_segments
        period = str(selected[0].get('period') or '')

    unit = next((entry.get('unit') for entry in selected if entry.get('unit')), _segment_default_unit(data))
    value_map = {'period': period}
    if unit:
        value_map['unit'] = unit
    for entry in selected:
        value_map[str(entry.get('name'))] = _to_float(entry.get('value'))

    source_layer = next((entry.get('source_layer') for entry in selected if entry.get('source_layer')), None)
    source_detail = next((entry.get('source_detail') for entry in selected if entry.get('source_detail')), None)
    supplementary['revenue_by_geography'] = {
        'value': value_map,
        'source_layer': source_layer or 'derived',
        'source_detail': source_detail or 'derived from segments.geography',
    }


def _sync_supplementary_convenience_fields(data):
    supplementary = data.setdefault('supplementary', {})
    market_shares = data.get('market_data', {}).get('shares_outstanding')
    target = supplementary.get('shares_outstanding')
    if isinstance(market_shares, dict) and _value_present(market_shares.get('value')):
        target_value = target.get('value') if isinstance(target, dict) else None
        if not _value_present(target_value):
            supplementary['shares_outstanding'] = {
                'value': market_shares.get('value'),
                'source_layer': market_shares.get('source_layer'),
                'source_detail': market_shares.get('source_detail'),
            }


def _iter_field_objects(data):
    for section in PERIOD_SECTIONS:
        for period_key in ('latest_fy', 'latest_quarter'):
            period_obj = data.get(section, {}).get(period_key, {})
            if not isinstance(period_obj, dict):
                continue
            for field_name, field_obj in period_obj.items():
                if field_name == 'period' or not isinstance(field_obj, dict):
                    continue
                yield f'{section}.{period_key}.{field_name}', field_obj
    for section in FLAT_SECTIONS:
        for field_name, field_obj in data.get(section, {}).items():
            if isinstance(field_obj, dict):
                yield f'{section}.{field_name}', field_obj


def _is_skippable_coverage_field(path):
    return path in SKIPPABLE_COVERAGE_FIELDS


def build_coverage_report(data):
    _finalize_segments_status(data, tried_web='official_web' in str(data.get('source') or ''))
    _sync_supplementary_from_segments(data)
    _sync_supplementary_convenience_fields(data)
    total = 0
    filled = 0
    layer2_filled = 0
    source_counts = {
        'yfinance': 0,
        'provider_api': 0,
        'official_web': 0,
        'trusted_web': 0,
        'broad_web': 0,
        'derived': 0,
    }
    provider_gap = []
    provider_gap_reasons = {reason: 0 for reason in PROVIDER_GAP_REASONS}
    missing_paths = []
    skippable_missing_paths = []
    for path, field_obj in _iter_field_objects(data):
        skippable = _is_skippable_coverage_field(path)
        if not skippable:
            total += 1
        value = field_obj.get('value')
        if _value_present(value):
            if not skippable:
                filled += 1
                source_layer = str(field_obj.get('source_layer') or '')
                if source_layer in source_counts:
                    source_counts[source_layer] += 1
                if source_layer == 'provider_api':
                    layer2_filled += 1
        else:
            if skippable:
                skippable_missing_paths.append(path)
            else:
                missing_paths.append(path)
            detail = str(field_obj.get('source_detail') or '')
            if (not skippable) and 'provider-gap' in detail.lower():
                provider_gap.append(path)
                reason = _provider_gap_reason(detail)
                if reason in provider_gap_reasons:
                    provider_gap_reasons[reason] += 1

    consumer_total = 0
    consumer_filled = 0
    core_total = 0
    core_filled = 0
    for meta_key in CONSUMER_REQUIRED_FIELDS['period_metadata']:
        consumer_total += 1
        if _value_present(data.get(meta_key)):
            consumer_filled += 1
    for section in ('income_statement', 'balance_sheet', 'cash_flow'):
        for period_key in ('latest_fy', 'latest_quarter'):
            period_obj = data.get(section, {}).get(period_key, {})
            if not isinstance(period_obj, dict):
                continue
            for field_name in CONSUMER_REQUIRED_FIELDS.get(section, []):
                field_obj = period_obj.get(field_name)
                if isinstance(field_obj, dict):
                    consumer_total += 1
                    if _value_present(field_obj.get('value')):
                        consumer_filled += 1
                if field_name in CORE_FIELDS.get(section, []) and isinstance(field_obj, dict):
                    core_total += 1
                    if _value_present(field_obj.get('value')):
                        core_filled += 1
    for section in ('market_data', 'consensus'):
        section_obj = data.get(section, {})
        if not isinstance(section_obj, dict):
            continue
        for field_name in CONSUMER_REQUIRED_FIELDS.get(section, []):
            field_obj = section_obj.get(field_name)
            if isinstance(field_obj, dict):
                consumer_total += 1
                if _value_present(field_obj.get('value')):
                    consumer_filled += 1

    supplementary_total = 0
    supplementary_filled = 0
    supplementary_missing = []
    supplementary_sector_total = 0
    supplementary_sector_filled = 0
    supplementary_sector_missing = []
    supplementary_obj = data.get('supplementary', {})
    if isinstance(supplementary_obj, dict):
        for field_name in NEAR_REQUIRED_SUPPLEMENTARY_FIELDS:
            supplementary_total += 1
            field_obj = supplementary_obj.get(field_name)
            if isinstance(field_obj, dict) and _value_present(field_obj.get('value')):
                supplementary_filled += 1
            else:
                supplementary_missing.append('supplementary.' + field_name)
        for field_name in SECTOR_CONDITIONAL_SUPPLEMENTARY_FIELDS:
            supplementary_sector_total += 1
            field_obj = supplementary_obj.get(field_name)
            if isinstance(field_obj, dict) and _value_present(field_obj.get('value')):
                supplementary_sector_filled += 1
            else:
                supplementary_sector_missing.append('supplementary.' + field_name)

    segments_obj = data.get('segments', {})
    segments_list = segments_obj.get('segments') if isinstance(segments_obj, dict) else []
    segments_status = segments_obj.get('status') if isinstance(segments_obj, dict) else None
    segments_count = len(segments_list) if isinstance(segments_list, list) else 0

    return {
        'total_fields': total,
        'filled_fields': filled,
        'fill_rate': round((filled / total) * 100, 1) if total else 0.0,
        'layer2_filled_fields': layer2_filled,
        'layer2_fill_share': round((layer2_filled / filled) * 100, 1) if filled else 0.0,
        'layer2_plus_official_filled_fields': layer2_filled + source_counts['official_web'],
        'layer2_plus_official_fill_share': round(((layer2_filled + source_counts['official_web']) / filled) * 100, 1) if filled else 0.0,
        'official_web_filled_fields': source_counts['official_web'],
        'official_web_fill_share': round((source_counts['official_web'] / filled) * 100, 1) if filled else 0.0,
        'trusted_web_filled_fields': source_counts['trusted_web'],
        'trusted_web_fill_share': round((source_counts['trusted_web'] / filled) * 100, 1) if filled else 0.0,
        'broad_web_filled_fields': source_counts['broad_web'],
        'broad_web_fill_share': round((source_counts['broad_web'] / filled) * 100, 1) if filled else 0.0,
        'source_layer_counts': source_counts,
        'consumer_required_total': consumer_total,
        'consumer_required_filled': consumer_filled,
        'consumer_required_fill_rate': round((consumer_filled / consumer_total) * 100, 1) if consumer_total else 0.0,
        'core_fields_total': core_total,
        'core_fields_filled': core_filled,
        'core_fields_fill_rate': round((core_filled / core_total) * 100, 1) if core_total else 0.0,
        'provider_gap_list': sorted(set(provider_gap)),
        'provider_gap_reason_counts': provider_gap_reasons,
        'missing_fields': sorted(missing_paths),
        'skippable_missing_fields': sorted(skippable_missing_paths),
        'supplementary_high_value_total': supplementary_total,
        'supplementary_high_value_filled': supplementary_filled,
        'supplementary_high_value_fill_rate': round((supplementary_filled / supplementary_total) * 100, 1) if supplementary_total else 0.0,
        'supplementary_high_value_missing': sorted(supplementary_missing),
        'supplementary_sector_conditional_total': supplementary_sector_total,
        'supplementary_sector_conditional_filled': supplementary_sector_filled,
        'supplementary_sector_conditional_fill_rate': round((supplementary_sector_filled / supplementary_sector_total) * 100, 1) if supplementary_sector_total else 0.0,
        'supplementary_sector_conditional_missing': sorted(supplementary_sector_missing),
        'segments_status': segments_status,
        'segments_count': segments_count,
    }


def _try_akshare_hk(data, nulls):
    """AKShare HK: Eastmoney HKF10 direct route, with FY + latest Q/H mapping."""
    if not PROVIDER_PATH:
        print('  AKShare HK provider path unavailable')
        return 0

    try:
        akshare_provider = importlib.import_module('akshare_provider')
    except Exception as e:
        print('  AKShare HK provider import error: ' + str(e)[:80])
        return 0

    if not akshare_provider.dependency_available():
        print('  akshare not installed')
        return 0

    identifier = data.get('ticker', '')
    try:
        result = akshare_provider.fetch({
            'identifier': identifier,
            'market': 'hk',
            'items': ['income_statement', 'balance_sheet', 'cash_flow'],
            'periods': 'latest',
        })
    except Exception as e:
        print('  AKShare HK fetch error: ' + str(e)[:80])
        return 0

    if result.get('status') != 'success':
        print('  AKShare HK status: ' + str(result.get('status')))
        return 0

    periods = sorted({
        str(period)
        for section in ('income_statement', 'balance_sheet', 'cash_flow')
        for row in result.get(section, [])
        for period in (row.get('values', {}) if isinstance(row, dict) else {}).keys()
    })
    annual_periods = [p for p in periods if p.endswith('-12-31')]
    interim_periods = [p for p in periods if not p.endswith('-12-31')]
    latest_annual = annual_periods[-1] if annual_periods else None
    latest_interim = interim_periods[-1] if interim_periods else None

    if latest_annual:
        data['latest_fy_period'] = latest_annual
        for section in PERIOD_SECTIONS:
            period_obj = data.get(section, {}).get('latest_fy', {})
            if isinstance(period_obj, dict):
                period_obj['period'] = latest_annual
    if latest_interim:
        data['latest_quarter_period'] = latest_interim
        data['latest_quarter_period_label'] = _period_label(latest_interim, 'half_year')
        data['latest_quarter_period_basis'] = _period_basis_from_date(latest_interim)
        for section in PERIOD_SECTIONS:
            period_obj = data.get(section, {}).get('latest_quarter', {})
            if isinstance(period_obj, dict):
                period_obj['period'] = data['latest_quarter_period_label']

    concept_map = PROVIDER_CONCEPT_MAP.get('akshare_hk', {})
    fill_targets = [('latest_fy', latest_annual), ('latest_quarter', latest_interim)]
    filled = 0

    for stmt in ('income_statement', 'balance_sheet', 'cash_flow'):
        sec_map = concept_map.get(stmt, {})
        for item in result.get(stmt, []):
            concept = str(item.get('concept', ''))
            field_name = sec_map.get(concept)
            if not field_name:
                continue
            values = item.get('values', {}) or {}
            label = item.get('label') or concept
            for target_period, source_period in fill_targets:
                if not source_period or source_period not in values:
                    continue
                val = _to_float(values.get(source_period))
                if val is None:
                    continue
                target = data.get(stmt, {}).get(target_period, {}).get(field_name)
                if not isinstance(target, dict):
                    continue
                old_val = target.get('value')
                target['value'] = val
                target['source_layer'] = 'provider_api'
                target['source_detail'] = 'AKShare HKF10: ' + str(label) + ' / ' + concept + ' (' + source_period + ')'
                if old_val != val:
                    filled += 1

    if filled:
        print('  AKShare HKF10: ' + str(filled) + ' FY/QH statement fields filled or overwritten')
    return filled


def _try_longbridge(data, nulls, fill_statements=True):
    """Longbridge for market data/consensus; statement fill is opt-in."""
    identifier = _longbridge_identifier(data.get('market', ''), data.get('ticker', ''))
    market = data.get('market', '')
    lb_available = bool(shutil.which('longbridge'))

    print('  Remaining: ' + str(len(nulls)) + ' null fields')
    if lb_available:
        print('  Longbridge CLI: available (quote/market data)')
    else:
        print('  Longbridge CLI: not installed')

    # Use CLI for market data, optional statements, and consensus.
    if lb_available:
        import subprocess, json as _json
        # 1. calc-index: PE, PB, market_cap
        try:
            cp = subprocess.run(['longbridge', 'calc-index', '--format', 'json', identifier],
                              capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            if cp.returncode == 0 and cp.stdout:
                lb_data = _json.loads(cp.stdout)
                items = lb_data if isinstance(lb_data, list) else [lb_data]
                LB_FIELD_MAP = {'mktcap': 'market_cap', 'pe': 'trailing_pe', 'pb': 'price_to_book'}
                for item in items:
                    for lb_key, actuals_key in LB_FIELD_MAP.items():
                        if lb_key in item and item[lb_key] is not None:
                            new_val = float(item[lb_key])
                            target = data.get('market_data', {}).get(actuals_key)
                            if isinstance(target, dict):
                                _validate_and_fill('market_data.' + actuals_key, new_val, target, 'Longbridge CLI', 'calc-index:' + lb_key, promote_source_when_close=True)
                print('  calc-index: market_cap/PE/PB from Longbridge')
        except Exception as e:
            print('  calc-index: ' + str(e)[:80])

        # 2. financial-report: IS/BS/CF (annual + quarterly)
        if fill_statements:
            try:
                cp = subprocess.run(['longbridge', 'financial-report', '--kind', 'ALL', '--format', 'json', identifier],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
                if cp.returncode == 0 and cp.stdout:
                    fr = _json.loads(cp.stdout)
                    LB_Q_MAP = {
                        'OperatingRevenue': ('income_statement', 'revenue'),
                        'OperatingIncome': ('income_statement', 'operating_income'),
                        'NetProfit': ('income_statement', 'net_income'),
                        'TotalAssets': ('balance_sheet', 'total_assets'),
                        'TotalLiability': ('balance_sheet', None),
                        'CashSTInvest': ('balance_sheet', 'cash'),
                    }
                    q_filled = 0
                    for stmt in ['IS', 'BS']:
                        indicators = fr.get('list', {}).get(stmt, {}).get('indicators', [])
                        for ind in indicators:
                            for acc in ind.get('accounts', []):
                                field = acc.get('field', '')
                                if field not in LB_Q_MAP: continue
                                sec, actuals_key = LB_Q_MAP[field]
                                if actuals_key is None: continue
                                values = acc.get('values', [])
                                latest_val = None
                                latest_period = None
                                for v in values:
                                    val = v.get('value', '')
                                    period = v.get('period', '')
                                    if val and period:
                                        latest_val = float(val)
                                        latest_period = period
                                        break
                                if latest_val is None: continue
                                target = data.get(sec, {}).get('latest_quarter', {}).get(actuals_key)
                                if isinstance(target, dict) and target.get('value') is None:
                                    target['value'] = latest_val
                                    target['source_layer'] = 'provider_api'
                                    target['source_detail'] = f'Longbridge CLI: financial-report ({latest_period})'
                                    q_filled += 1
                    if q_filled:
                        print(f'  financial-report: {q_filled} quarterly fields filled')
            except Exception as e:
                print('  financial-report: ' + str(e)[:80])
        else:
            print('  financial-report: skipped for HK statements (AKShare HKF10 is primary)')

        # 3. forecast-eps: consensus
        try:
            cp = subprocess.run(['longbridge', 'forecast-eps', '--format', 'json', identifier],
                              capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            if cp.returncode == 0 and cp.stdout:
                lb_data = _json.loads(cp.stdout)
                items = lb_data.get('items', lb_data) if isinstance(lb_data, dict) else lb_data
                items = items if isinstance(items, list) else [items]
                latest = max(
                    [item for item in items if isinstance(item, dict)],
                    key=lambda item: int(item.get('forecast_start_date') or 0),
                    default={}
                )
                eps_val = latest.get('forecast_eps_mean') if isinstance(latest, dict) else None
                if eps_val is not None:
                    target = data.get('consensus', {}).get('current_year_eps')
                    if isinstance(target, dict) and (target.get('value') is None or str(target.get('source_detail', '')).startswith('Longbridge CLI: forecast-eps')):
                        target['value'] = float(eps_val)
                        target['source_layer'] = 'provider_api'
                        target['source_detail'] = 'Longbridge CLI: forecast-eps mean (start=' + str(latest.get('forecast_start_date') or '') + ')'
                print('  forecast-eps: consensus filled')
        except Exception as e:
            print('  forecast-eps: ' + str(e)[:80])

    return 0

def fill_layer_2(data, nulls, industry, ticker):
    """Layer 2: provider API — authoritative data source."""
    remaining = [n for n in nulls if n['obj']['value'] is None]
    if not remaining: return remaining

    market = (data.get('market') or '').lower()
    module_name = PROVIDER_MAP.get(market)

    # Longbridge is a special case (CLI/SDK, not a Python provider module)
    if module_name == 'longbridge':
        print('\n=== Layer 2: Longbridge provider ===')
        _try_longbridge(data, remaining)
        return [n for n in nulls if n['obj']['value'] is None]

    # HK statements use AKShare/Eastmoney HKF10 direct; Longbridge only supplements market/consensus.
    if market == 'hk':
        print('\n=== Layer 2: AKShare HK provider ===')
        _try_akshare_hk(data, remaining)
        print('\n=== Layer 2: Longbridge HK market/consensus supplement ===')
        _try_longbridge(data, [n for n in nulls if n['obj']['value'] is None], fill_statements=False)
        data['source'] = 'yfinance + provider_api'
        return [n for n in nulls if n['obj']['value'] is None]

    if not module_name or not PROVIDER_PATH: return remaining

    try: mod = importlib.import_module(module_name)
    except ImportError: return remaining
    if not mod.dependency_available():
        print('  Layer 2: ' + module_name + ' dependency not installed — skipping')
        return remaining

    concept_map = PROVIDER_CONCEPT_MAP.get(module_name, {})
    identifier = _provider_identifier(market, data.get('ticker'), ticker)
    total_filled = 0

    print('\n=== Layer 2: ' + mod.PROVIDER + ' provider ===')

    # Annual fetch
    annual_status = 'error'
    q_status = 'skipped'
    try:
        result = mod.fetch({'identifier': identifier, 'market': market, 'items': mod.EXTRACTABLE, 'periods': 'latest'})
        annual_status = result.get('status', 'success')
    except Exception as e:
        print('  Annual fetch error: ' + str(e))
        result = {'status': 'error', 'errors': [str(e)]}
    if _is_openesef_local_gap(market, mod.PROVIDER, result):
        annual_status = 'skipped-no-local-esef'
    if annual_status == 'success':
        annual_periods, annual_basis = _collect_periods_and_basis(result)
        annual_source_period, _ = _select_latest_periods(annual_periods, annual_basis)
        if annual_source_period:
            _apply_latest_period_metadata(data, 'latest_fy', annual_source_period, annual_basis.get(annual_source_period))
        print('  Annual: ' + ', '.join(result.get('items_extracted', [])))
        fy_filled = _fill_from_provider(result, remaining, concept_map, mod.PROVIDER, 'latest_fy', annual_source_period, data)
        fy_filled += _fill_cross_statement_fallbacks(data, mod.PROVIDER, result, 'latest_fy', annual_source_period)
        fy_filled += _fill_jp_annual_filing_fallbacks(data, result, annual_source_period)
        total_filled += fy_filled
        _mark_provider_gap_fields(data, remaining, mod.PROVIDER, 'annual-unfilled', include_periods=['latest_fy'], reason='official_source_available_not_extracted')
    elif annual_status == 'skipped-no-local-esef':
        print('  Annual status: skipped-no-local-esef (prefer official_web until a local ESEF package is available)')
        _clear_provider_gap_fields(remaining, mod.PROVIDER, include_periods=['latest_fy'])
    else:
        print('  Annual status: ' + str(annual_status))
        _mark_provider_gap_fields(data, remaining, mod.PROVIDER, 'annual', include_periods=['latest_fy'], reason='provider_unavailable')

    # Quarterly fetch
    try:
        q_result = mod.fetch({'identifier': identifier, 'market': market, 'items': mod.EXTRACTABLE, 'periods': 'quarterly'})
        q_status = q_result.get('status', 'success')
        if _is_openesef_local_gap(market, mod.PROVIDER, q_result):
            q_status = 'skipped-no-local-esef'
        if q_status == 'success':
            q_periods, q_basis = _collect_periods_and_basis(q_result)
            _, q_source_period = _select_latest_periods(q_periods, q_basis)
            if q_source_period:
                _apply_latest_period_metadata(data, 'latest_quarter', q_source_period, q_basis.get(q_source_period))
            q_filled = _fill_from_provider(q_result, remaining, concept_map, mod.PROVIDER, 'latest_quarter', q_source_period, data)
            q_filled += _fill_cross_statement_fallbacks(data, mod.PROVIDER, q_result, 'latest_quarter', q_source_period)
            q_filled += _fill_kr_quarterly_filing_fallbacks(data, q_result, q_source_period)
            q_filled += _fill_jp_quarterly_filing_fallbacks(data, q_result, q_source_period)
            total_filled += q_filled
            _mark_provider_gap_fields(data, remaining, mod.PROVIDER, 'quarterly-unfilled', include_periods=['latest_quarter'], reason='official_source_available_not_extracted')
            print('  Quarterly: ' + ', '.join(q_result.get('items_extracted', [])) + ' - ' + str(q_filled) + ' Q/H fields')
        elif q_status == 'skipped-no-local-esef':
            print('  Quarterly status: skipped-no-local-esef (prefer official_web until a local ESEF package is available)')
            _clear_provider_gap_fields(remaining, mod.PROVIDER, include_periods=['latest_quarter'])
        else:
            print('  Quarterly status: ' + str(q_status))
            _mark_provider_gap_fields(data, remaining, mod.PROVIDER, 'quarterly', include_periods=['latest_quarter'], reason='provider_unavailable')
    except Exception as e:
        print('  Quarterly fetch error: ' + str(e))
        _mark_provider_gap_fields(data, remaining, mod.PROVIDER, 'quarterly', include_periods=['latest_quarter'], reason='provider_unavailable')

    provider_runs = data.setdefault('_provider_runs', {})
    provider_runs[mod.PROVIDER] = {'annual_status': annual_status, 'quarterly_status': q_status}

    if market == 'tw':
        tw_aux_filled = _fill_tw_finmind_aux(data, identifier, result if annual_status == 'success' else None, q_result if q_status == 'success' else None)
        total_filled += tw_aux_filled
        if tw_aux_filled:
            print('  TW FinMind aux: ' + str(tw_aux_filled) + ' market/structure fields')
    elif market in {'us', 'cn'}:
        print('\n=== Layer 2: Longbridge market/consensus supplement ===')
        _try_longbridge(data, [n for n in nulls if n['obj']['value'] is None], fill_statements=False)

    total_filled += _fill_kr_local_filing_fallbacks(industry, ticker, data)
    print('  Filled/overridden: ' + str(total_filled) + ' fields')
    data['source'] = 'yfinance + provider_api'
    return [n for n in nulls if n['obj']['value'] is None]


# ── Layer 3: web search ──────────────────────────────
def get_layer3_sources(data, market):
    sources_config = {}
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'actuals_schema.json')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        sources_config = schema.get('layer3_sources', {})
        if not sources_config:
            legacy = schema.get('layer2_sources', {})
            for mkt, sources in legacy.items():
                sources_config[mkt] = {'trusted_web': list(sources)}
    data_sources = data.get('layer3_sources', {})
    if data_sources:
        for mkt, sources in data_sources.items():
            sources_config[mkt] = sources
    elif data.get('layer2_sources', {}):
        for mkt, sources in data.get('layer2_sources', {}).items():
            existing = sources_config.get(mkt, {})
            if isinstance(existing, list):
                existing = {'trusted_web': list(existing)}
            merged = dict(existing)
            merged['trusted_web'] = list(sources)
            sources_config[mkt] = merged

    market_sources = sources_config.get(market, sources_config.get('*', {}))
    if isinstance(market_sources, list):
        market_sources = {'trusted_web': list(market_sources)}
    if not market_sources:
        market_sources = {'official_web': ['<company> investor relations annual report financial statements']}

    context = _query_context(data, market)
    ordered = []
    seen = set()
    for layer_name in ['official_web', 'trusted_web', 'broad_web']:
        for query in market_sources.get(layer_name, []):
            for expanded_query in _expand_layer3_queries(layer_name, query, context):
                _append_unique_query(ordered, seen, layer_name, expanded_query)
    if not ordered:
        _append_unique_query(ordered, seen, 'broad_web', _render_query_template('<company> annual report financial statements', context))
    if not any(item['layer_name'] == 'broad_web' for item in ordered):
        fallback = _render_query_template('<company> annual report financial statements', context)
        if not fallback:
            fallback = _render_query_template('<ticker> annual report financial statements', context)
        _append_unique_query(ordered, seen, 'broad_web', fallback)
    return ordered

def fill_layer_3(data, nulls, market):
    """Layer 3: web search — agent-executed site chain."""
    sources = get_layer3_sources(data, market)
    remaining = [n for n in nulls if not _is_skippable_coverage_field(n.get('path', ''))]
    web_layers = {'official_web', 'trusted_web', 'broad_web'}
    for n in remaining:
        field_obj = n.get('obj')
        if not isinstance(field_obj, dict) or field_obj.get('value') is not None:
            continue
        detail = str(field_obj.get('source_detail') or '')
        if _provider_gap_reason(detail) == 'not_disclosed':
            continue
        if field_obj.get('source_layer') in web_layers:
            field_obj['source_layer'] = None
            field_obj['source_detail'] = None
    for step_idx, source in enumerate(sources):
        if not remaining: break
        layer_name = source.get('layer_name', 'broad_web')
        source_query = source.get('query', '')
        label = ('site:' + source_query[5:].split()[0]) if source_query.startswith('site:') else 'unlimited web'
        print('\n--- Step 3' + chr(97 + step_idx) + ': ' + layer_name + ' / ' + label + ' ---')
        print('  Query: ' + _safe_console_text(source_query))
        print('  Remaining: ' + str(len(remaining)) + ' null fields')
        fields = ', '.join(sorted({n['field'] for n in remaining})[:15])
        print('  Target: ' + fields)
        for n in remaining:
            detail = str(n['obj'].get('source_detail') or '')
            reason = _provider_gap_reason(detail)
            if reason == 'not_disclosed':
                continue
            if reason == 'official_source_available_not_extracted':
                pending = 'pending: ' + source_query
                if pending not in detail:
                    n['obj']['source_detail'] = detail + ' | ' + pending
                if n['obj'].get('source_layer') not in web_layers:
                    n['obj']['source_layer'] = layer_name
                continue
            if n['obj'].get('source_layer') not in web_layers:
                n['obj']['source_layer'] = layer_name
                n['obj']['source_detail'] = 'pending: ' + source_query
                continue
            pending = 'pending: ' + source_query
            if pending not in detail:
                n['obj']['source_detail'] = (detail + ' | ' + pending).strip(' |')
    _finalize_segments_status(data, tried_web=bool(sources))
    return [n for n in nulls if n['obj']['value'] is None]


# ── Derived fields ────────────────────────────────────
def _derive_gross_profit(data):
    for period in ['latest_fy', 'latest_quarter']:
        isec = data.get('income_statement', {}).get(period, {})
        revenue_obj = isec.get('revenue', {})
        cost_obj = isec.get('cost_of_revenue', {})
        gross_obj = isec.get('gross_profit', {})
        rev = revenue_obj.get('value')
        cogs = cost_obj.get('value')
        gp = gross_obj.get('value')
        if rev is not None and cogs is not None and gp is None:
            gross_obj['value'] = rev - cogs
            gross_obj['source_layer'] = _derived_source_layer(revenue_obj, cost_obj)
            gross_obj['source_detail'] = 'computed: revenue - cost_of_revenue'
        elif rev is not None and cogs is not None and gp is not None:
            expected = rev - cogs
            if abs(expected - gp) <= max(1.0, abs(expected) * 0.001):
                derived_layer = _derived_source_layer(revenue_obj, cost_obj)
                if derived_layer in ('provider_api', 'official_web') and gross_obj.get('source_layer') not in ('provider_api', 'official_web'):
                    gross_obj['source_layer'] = derived_layer
                    gross_obj['source_detail'] = 'validated existing gross_profit against revenue - cost_of_revenue'


def _derive_market_multiples(data):
    market_data = data.get('market_data', {})
    if not isinstance(market_data, dict):
        return
    market_cap_obj = market_data.get('market_cap', {})
    market_cap = _to_float(market_cap_obj.get('value'))
    if market_cap is None or market_cap <= 0:
        return

    revenue_obj = data.get('income_statement', {}).get('latest_fy', {}).get('revenue', {})
    net_income_obj = data.get('income_statement', {}).get('latest_fy', {}).get('net_income', {})
    equity_obj = data.get('balance_sheet', {}).get('latest_fy', {}).get('total_equity_parent', {})
    revenue = _to_float(revenue_obj.get('value'))
    net_income = _to_float(net_income_obj.get('value'))
    equity = _to_float(equity_obj.get('value'))
    derived_map = {
        'trailing_pe': (net_income, net_income_obj, 'computed: market_cap / latest_fy.net_income'),
        'price_to_book': (equity, equity_obj, 'computed: market_cap / latest_fy.total_equity_parent'),
        'price_to_sales': (revenue, revenue_obj, 'computed: market_cap / latest_fy.revenue'),
    }
    for field_name, (denominator, denominator_obj, detail) in derived_map.items():
        target = market_data.get(field_name)
        if not isinstance(target, dict):
            continue
        if denominator is None or denominator <= 0:
            continue
        derived_layer = _derived_source_layer(market_cap_obj, denominator_obj)
        derived_value = market_cap / denominator
        if target.get('value') is None:
            target['value'] = derived_value
            target['source_layer'] = derived_layer
            target['source_detail'] = detail
            continue
        existing = _to_float(target.get('value'))
        if existing is None:
            continue
        if abs(existing - derived_value) <= max(1e-6, abs(derived_value) * 0.01):
            if derived_layer in ('provider_api', 'official_web') and target.get('source_layer') not in ('provider_api', 'official_web'):
                target['source_layer'] = derived_layer
                target['source_detail'] = 'validated existing value against ' + detail.replace('computed: ', '')


# ── Main ──────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print('Usage: python fill_gaps.py <industry> <ticker>')
        sys.exit(1)
    industry, ticker = sys.argv[1], sys.argv[2]
    data = load_actuals(industry, ticker)
    market = (data.get('market') or '').lower()
    _bootstrap_yfinance_layer1(data)
    nulls = get_null_fields(data)
    if not nulls:
        print('All fields filled.')
        return

    print(str(len(nulls)) + ' null fields for ' + ticker + ' (' + market + ')')

    # Layer 2: provider API
    nulls = fill_layer_2(data, nulls, industry, ticker)
    official_filled = _apply_official_web_cache(industry, ticker, data)
    if official_filled:
        print('  official_web cache applied: ' + str(official_filled) + ' fields')
    _finalize_segments_status(data, tried_web=False)
    _derive_gross_profit(data)
    _derive_market_multiples(data)
    save_actuals(industry, ticker, data)

    # Layer 3: web search
    still_null = [n for n in nulls if n['obj']['value'] is None]
    if still_null:
        print('\n=== Layer 3: web search chain ===')
        fill_layer_3(data, still_null, market)
        data['source'] = 'yfinance + provider_api + official_web + trusted_web + broad_web'
        save_actuals(industry, ticker, data)

    # Derived
    _finalize_segments_status(data, tried_web=bool(still_null))
    _derive_market_multiples(data)
    save_actuals(industry, ticker, data)

    # Summary
    nulls_after = get_null_fields(data)
    coverage = build_coverage_report(data)
    data['_coverage'] = coverage
    save_actuals(industry, ticker, data)
    print('\n=== Result: ' + str(coverage['filled_fields']) + '/' + str(coverage['total_fields']) + ' filled (' + str(coverage['fill_rate']) + '%) ===')
    print('Consumer-required: ' + str(coverage['consumer_required_filled']) + '/' + str(coverage['consumer_required_total']) + ' (' + str(coverage['consumer_required_fill_rate']) + '%)')
    print('Core fields: ' + str(coverage['core_fields_filled']) + '/' + str(coverage['core_fields_total']) + ' (' + str(coverage['core_fields_fill_rate']) + '%)')
    print('Layer 2 share of filled fields: ' + str(coverage['layer2_filled_fields']) + '/' + str(coverage['filled_fields']) + ' (' + str(coverage['layer2_fill_share']) + '%)')
    print('Official web share of filled fields: ' + str(coverage['official_web_filled_fields']) + '/' + str(coverage['filled_fields']) + ' (' + str(coverage['official_web_fill_share']) + '%)')
    print('Layer 2 + official web share: ' + str(coverage['layer2_plus_official_filled_fields']) + '/' + str(coverage['filled_fields']) + ' (' + str(coverage['layer2_plus_official_fill_share']) + '%)')
    print('Segments: status=' + str(coverage['segments_status']) + ', count=' + str(coverage['segments_count']))
    print('Supplementary high-value: ' + str(coverage['supplementary_high_value_filled']) + '/' + str(coverage['supplementary_high_value_total']) + ' (' + str(coverage['supplementary_high_value_fill_rate']) + '%)')
    print('Supplementary sector-conditional: ' + str(coverage['supplementary_sector_conditional_filled']) + '/' + str(coverage['supplementary_sector_conditional_total']) + ' (' + str(coverage['supplementary_sector_conditional_fill_rate']) + '%)')
    if coverage['skippable_missing_fields']:
        print('Skippable missing: ' + ', '.join(coverage['skippable_missing_fields'][:6]))
    if nulls_after:
        print('Remaining nulls:')
        for n in sorted(nulls_after, key=lambda x: x['path']):
            print('  ' + n['path'])


if __name__ == '__main__':
    main()
