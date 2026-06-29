"""build-logic-model.py v4 — JSON-driven formula-linked Excel model.

Usage: python .scripts/driver-map/build-logic-model.py <driver-map.json> [-o output.xlsx]

Generates single-sheet Excel with 7 sections from JSON config. Zero hardcodes —
all company data, assumptions, and module choices from JSON.

Sections:
  §1 Reported Segments        Rev/Cost/GP/GM hardcode FY25A, FY26+ = Σ logic lines
  §2 Logic Lines              Module dispatch (yoy/vol_asp/capacity_util/backlog_burn)
                                → inputs + Revenue formula + Check + GM/GP
  §2→§1 Fill                  Back-link Section 1 from logic line results
  §3 P&L                      Total Rev/GP = Σ formulas + Check rows (collapsible)
                                Opex/Tax/NI hardcode FY23-25, formula FY26+
                                Full P&L always shown (SOTP needs all metrics)
                                D&A/EBITDA/EBIT per actuals.da + Rev YoY row
  §4 SOTP Logic               Per line: GP → metric alloc → multiple → MCap → SUM
  §5 SOTP Segments            Segment weighted multiple
  §6 Market Data              yfinance (mcap/price/shares/PE/52W) + implied ratios
  §7 Scenario Summary         3-scenario projection (yoy chain / vol_asp cache / single)

Revenue modules (modules/):
  yoy (built-in)              Rev = Prior × (1 + YoY Active), BBE group
  vol_asp                     Rev = Σ(Vol × Share% × ASP) / 100, multi-tier BBE
  capacity_util               Rev = Capacity × Util% × ASP
  backlog_burn                Rev = Beg_Backlog × Burn%, chain-linked

SOTP valuation methods: pe / ev_ebitda / ev_ebit / ev_sales (per line)
Backward compat: old ``sotp_pe: 40`` auto-converts to ``{method: pe, multiple: 40}``

Format: no gridlines, Calibri 11, yellow+blue inputs, selective C-column bold,
        ASP #,##0.0, Revenue #,##0, C1 (CUR millions), freeze D2.

validate_json() runs before build — checks depth, method, array lengths, required fields.
"""

import json, argparse, codecs, functools
import yfinance as yf
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Color
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# ── Row reference: wraps int row number for safety + traceability ──
class Ref:
    __slots__ = ('_r', '_label')
    def __init__(self, row, label=''):
        self._r = row; self._label = label
    def __int__(self): return self._r
    def __index__(self): return self._r
    def __str__(self): return str(self._r)
    def __repr__(self): return f'Ref({self._r}, {self._label!r})'

# ── Format constants ──
PCT = '0.0%'; NUM = '#,##0.0'; DEC = '#,##0.00'; INT = '#,##0'
PRICE_FMT = {'cn': '¥#,##0.00', 'jp': '¥#,##0', 'kr': '₩#,##0', 'tw': 'NT$#,##0.00',
             'us': '$#,##0.00', 'hk': 'HK$#,##0.00', 'sg': 'S$#,##0.00'}
DS = 4

# ── Fonts / fills ──
nf   = Font(name='Calibri', size=11)
bf   = Font(name='Calibri', bold=True, size=11)
bf12 = Font(name='Calibri', bold=True, size=12)
itf  = Font(name='Calibri', size=10, italic=True, color='808080')
inpf = Font(name='Calibri', size=11, color='0000CC')
inpfill = PatternFill('solid', fgColor='FFFFCC')
actfill = PatternFill('solid', fgColor='F0F0F0')
hlfill = PatternFill('solid', fgColor='963634')
hlfont = Font(name='Calibri', bold=True, size=11, color=Color(rgb='FFFFFF'))

# ── Shared cell helpers ──
def C(ws, r, c, v=None, font=None, fill=None, fmt=None):
    cl = ws.cell(row=r, column=c, value=v)
    cl.font = font or nf
    if fill: cl.fill = fill
    if fmt: cl.number_format = fmt
    cl.alignment = Alignment(
        horizontal='right' if c >= DS else 'left',
        vertical='center', wrap_text=False)

def I(ws, r, c, v, fmt=None):
    C(ws, r, c, v, font=inpf, fill=inpfill, fmt=fmt)

def A(ws, r, c, v, fmt=None):
    C(ws, r, c, v, fill=actfill, fmt=fmt)

def CF(ws, r, c, formula, fmt=None):
    """Write a formula cell — black font, no fill, guaranteed number_format."""
    C(ws, r, c, formula, fmt=fmt)

def HL(ws, r, c, v=None, fmt=None):
    """Highlight cell — deep red bg + white bold font."""
    C(ws, r, c, v, font=hlfont, fill=hlfill, fmt=fmt)

def BOLD(ws, r, c, v=None, fmt=None):
    """Bold key metric — black bold font."""
    C(ws, r, c, v, font=bf, fmt=fmt)

# ── Module contract decorator ──
RENDER_CONTRACT = {'next_R', 'rev_r', 'gm_r', 'gp_r', 'module'}

def validate_contract(fn):
    @functools.wraps(fn)
    def wrapper(ws, R, ll, anchor_info, ctx):
        result = fn(ws, R, ll, anchor_info, ctx)
        missing = RENDER_CONTRACT - set(result.keys())
        if missing:
            raise ValueError(f'{fn.__name__}: missing contract keys {missing}')
        return result
    return wrapper

# ── Context dict passed to modules ──
def make_ctx():
    return {
        'C': C, 'I': I, 'A': A, 'CF': CF, 'HL': HL,
        'nf': nf, 'bf': bf, 'itf': itf,
        'NUM': NUM, 'DEC': DEC, 'PCT': PCT, 'INT': INT,
        'DS': DS, 'FY0': 0, 'LC': 0,
        'proj_n': 0,
    }

# ═══════════════════════════════════════════════════════════════
# Module registry
# ═══════════════════════════════════════════════════════════════

MODULES = {}

# Lazy imports for external modules
def _load_module(name):
    if name not in MODULES:
        if name == 'yoy':
            from modules.yoy import render as fn
        elif name == 'vol_asp':
            from modules.vol_asp import render as fn
        elif name == 'backlog_burn':
            from modules.backlog_burn import render as fn
        else:
            raise ValueError(f'Unknown module: {name}')
        MODULES[name] = fn


# ═══════════════════════════════════════════════════════════════
# JSON validation
# ═══════════════════════════════════════════════════════════════

VALID_DEPTH = {'gp', 'ebitda', 'ebit', 'ni'}
VALID_METHOD = {'pe', 'ps', 'ev_ebitda', 'ev_ebit', 'ev_sales'}

def validate_json(cfg):
    """Check JSON structure before build. Raises ValueError on issues."""
    meta = cfg.get('meta', {})
    a = cfg.get('actuals', {})
    proj_n = meta.get('proj_years', 5)

    # depth
    depth = meta.get('p&l_depth', 'ni')
    if depth not in VALID_DEPTH:
        raise ValueError(f'p&l_depth must be one of {VALID_DEPTH}, got {depth}')

    # actuals required fields
    for fy_key in ['fy-2', 'fy-1', 'fy0']:
        fy = a.get(fy_key, {})
        for field in ['rev', 'gp', 'op', 'tax', 'ni']:
            if field not in fy:
                raise ValueError(f'actuals.{fy_key}.{field} is required')

    # da required for ebitda/ebit depth
    if depth in ('ebitda', 'ebit', 'ni'):
        for fy_key in ['fy-2', 'fy-1', 'fy0']:
            if 'da' not in a.get(fy_key, {}):
                print(f'  [warn] actuals.{fy_key}.da missing, assuming 0')

    # global opex_rate length
    opex_arr = cfg.get('global', {}).get('opex_rate', [])
    if len(opex_arr) != 3 + proj_n:
        raise ValueError(f'global.opex_rate length {len(opex_arr)} != {3 + proj_n} (3 actual + {proj_n} proj)')

    # logic_lines
    for ll in cfg.get('logic_lines', []):
        ln = ll.get('name', '?')
        # sotp method
        sotp = ll.get('sotp', {})
        if sotp:
            m = sotp.get('method', 'pe')
            if m not in VALID_METHOD:
                raise ValueError(f'{ln}: sotp.method {m} not in {VALID_METHOD}')
            if 'multiple' not in sotp:
                raise ValueError(f'{ln}: sotp.multiple required')
        # module volume/asp arrays
        if ll.get('module') == 'vol_asp':
            vol = ll.get('volume', {})
            proj = vol.get('proj', [])
            if len(proj) != proj_n:
                raise ValueError(f'{ln}: volume.proj length {len(proj)} != proj_years {proj_n}')
            for t in ll.get('tiers', []):
                for k in ('asp', 'asp_bull', 'asp_base', 'asp_bear'):
                    arr = t.get(k, [])
                    if arr and len(arr) < 1 + proj_n:
                        print(f'  [warn] {ln} {t.get("name","?")} {k}: {len(arr)} values, need >={1+proj_n}')

    print(f'  Validated: depth={depth}, {len(cfg.get("logic_lines",[]))} logic lines, {len(cfg.get("segments",[]))} segments')


# ═══════════════════════════════════════════════════════════════
# Main build function
# ═══════════════════════════════════════════════════════════════

def build(json_path, output_path=None):
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    validate_json(cfg)

    meta = cfg['meta']; actuals = cfg['actuals']; segments = cfg['segments']
    logic_lines = cfg['logic_lines']; gl = cfg['global']

    # ── yfinance market data ──
    try:
        yf_ticker = meta.get('yf_ticker', meta['ticker'])
        info = yf.Ticker(yf_ticker).info
    except Exception:
        info = {}
    mcap_raw = info.get('marketCap', 0) or 0
    price = info.get('currentPrice', 0) or 0
    shares = int(info.get('sharesOutstanding', 0) / 1e6) or 0
    ttm_pe = info.get('trailingPE', 0) or 0
    fwd_pe = info.get('forwardPE', 0) or 0
    hi52 = info.get('fiftyTwoWeekHigh', 0) or 0
    lo52 = info.get('fiftyTwoWeekLow', 0) or 0
    # Manual overrides from meta take priority over yfinance
    if meta.get('mcap_m'): mcap_M = meta['mcap_m']
    else: mcap_M = int(mcap_raw / 1e6) if mcap_raw else 0
    if meta.get('price'): price = meta['price']
    if meta.get('shares_m'): shares = meta['shares_m']
    # Unit: explicit override > market heuristic > auto
    if 'unit' in meta:
        use_B = meta['unit'] == 'B'
    else:
        use_B = meta.get('market', '') in ('jp', 'kr', 'tw') or mcap_M > 1_000_000
    div = 1000 if use_B else 1
    mcap_d = round(mcap_M / div, 1)
    price_fmt = PRICE_FMT.get(meta.get('market', 'cn'), '¥#,##0.00')

    def sc(v):
        return round(v / div, 2)

    bfyr = meta['base_fy']; proj_n = meta['proj_years']; s_off = meta['sotp_offset']
    COLS = 3 + proj_n
    FY0 = DS + 2; SC = FY0 + s_off; LC = DS + COLS - 1
    YR = [f'FY{bfyr - 2}A', f'FY{bfyr - 1}A', f'FY{bfyr}A'] + \
         [f'FY{bfyr + i}E' for i in range(1, proj_n + 1)]

    # ── Workbook setup ──
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = meta['company'][:31]
    ws.sheet_view.showGridLines = False
    C(ws, 1, 1, 'Scenario:', font=bf)
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"')
    ws.add_data_validation(dv)
    C(ws, 1, 2, 'Base', font=Font(name='Calibri', bold=True, size=12, color='2F5496'))
    dv.add('B1')
    for ci, y in enumerate(YR, DS):
        C(ws, 1, ci, y, font=bf)
    unit_label = 'bn' if use_B else 'millions'
    C(ws, 1, 3, f'({meta.get("currency","CNY")} {unit_label})', font=itf)

    # module context
    ctx = make_ctx()
    ctx['FY0'] = FY0; ctx['LC'] = LC; ctx['SC'] = SC; ctx['proj_n'] = proj_n
    ctx['COLS'] = COLS; ctx['bfyr'] = bfyr

    print(f'  Cols: D=DS({DS}) FY0={get_column_letter(FY0)}({FY0}) '
          f'LC={get_column_letter(LC)}({LC}) SC={get_column_letter(SC)}({SC}) '
          f'proj_n={proj_n} B_mode={use_B} div={div}')

    # ═══════════════ §1 Reported Segments ═══════════════
    R = 3
    C(ws, R, 1, 'Reported Segments', font=bf12)
    s1_start = R  # include header row
    R = 5
    seg_info = {}
    anchor_info = {}  # {ln: (Section1_Rev_row, value_in_M)}
    one_to_one = set()  # logic lines where segment=line (split=1.0, no residual)
    line_to_seg = {}    # {ln: seg_name}
    line_to_split = {}  # {ln: split_row}

    for seg in segments:
        sn = seg['name']; fy0 = seg['fy0']; lls = seg['logic_lines']
        srev = fy0['rev']; scost = fy0['cost']; sgp = fy0['gp']; sgm = fy0['gm']
        # History layer: fy-2 (FY23) and fy-1 (FY24). Optional — leave empty if segment didn't exist.
        hist_years = [('fy-2', DS), ('fy-1', DS + 1)]

        # Revenue
        for yr_key, col in hist_years:
            yr = seg.get(yr_key)
            if yr: A(ws, R, col, sc(yr['rev']), fmt=NUM)
            else: C(ws, R, col, '', fmt=NUM)
        A(ws, R, FY0, sc(srev), fmt=NUM)
        rev_r = R
        C(ws, R, 2, sn, font=bf)
        C(ws, R, 3, 'Revenue')
        R += 1

        # Chinese translation sub-row (if provided)
        sn_cn = seg.get('name_cn', '')
        if sn_cn:
            C(ws, R, 2, sn_cn, font=itf)
            for ci in range(DS, LC + 1):
                C(ws, R, ci, '', fmt=NUM)
            R += 1

        # Implied YoY
        for yr_key, col in hist_years:
            C(ws, R, col, '', fmt=PCT)
        # E column: FY2025 vs FY2024
        cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
        C(ws, R, DS + 1, f'=IFERROR({cl_e}{rev_r}/{cl_d}{rev_r}-1,"")', fmt=PCT)
        f0 = get_column_letter(FY0); f_1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({f0}{rev_r}/{f_1}{rev_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
        C(ws, R, 3, 'Implied YoY')
        R += 1

        # Cost
        for yr_key, col in hist_years:
            yr = seg.get(yr_key)
            if yr: A(ws, R, col, sc(yr['cost']), fmt=NUM)
            else: C(ws, R, col, '', fmt=NUM)
        A(ws, R, FY0, sc(scost), fmt=NUM)
        cost_r = R
        C(ws, R, 3, 'Cost')
        R += 1

        # GM (before GP — placeholder, fixed below)
        for yr_key, col in hist_years:
            C(ws, R, col, '', fmt=PCT)  # placeholder
        C(ws, R, FY0, 0, fmt=PCT)
        gm_r = R
        C(ws, R, 3, 'GM')
        R += 1

        # GP
        for yr_key, col in hist_years:
            yr = seg.get(yr_key)
            if yr: A(ws, R, col, sc(yr['gp']), fmt=NUM)
            else: C(ws, R, col, '', fmt=NUM)
        A(ws, R, FY0, sc(sgp), fmt=NUM)
        gp_r = R
        C(ws, R, 3, 'GP')
        R += 1

        # OP row (if segment discloses operating profit)
        fy0_op = fy0.get('op')
        op_r = 0
        if fy0_op is not None:
            for yr_key, col in hist_years:
                yr = seg.get(yr_key)
                if yr and yr.get('op') is not None: A(ws, R, col, sc(yr['op']), fmt=NUM)
                else: C(ws, R, col, '', fmt=NUM)
            A(ws, R, FY0, sc(fy0_op), fmt=NUM)
            op_r = R
            C(ws, R, 3, 'OP')
            R += 1
            # OP YoY
            for yr_key, col in hist_years:
                C(ws, R, col, '', fmt=PCT)
            CF(ws, R, DS + 1, f'=IFERROR({get_column_letter(DS+1)}{op_r}/{get_column_letter(DS)}{op_r}-1,"")', fmt=PCT)
            CF(ws, R, FY0, f'=IFERROR({get_column_letter(FY0)}{op_r}/{get_column_letter(FY0-1)}{op_r}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{op_r}/{pl}{op_r}-1,"")', fmt=PCT)
            C(ws, R, 3, 'OP YoY')
            R += 1
            # OPM
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{op_r}/{cl}{rev_r},"")', fmt=PCT)
            C(ws, R, 3, 'OPM')
            R += 1

        # Fix GM formulas for all years: =GP/Rev
        cl_f0 = get_column_letter(FY0)
        CF(ws, gm_r, FY0, f'=IFERROR({cl_f0}{gp_r}/{cl_f0}{rev_r},"")', fmt=PCT)
        for yr_key, col in hist_years:
            cl = get_column_letter(col)
            if seg.get(yr_key):
                CF(ws, gm_r, col, f'=IFERROR({cl}{gp_r}/{cl}{rev_r},"")', fmt=PCT)

        srows = []; lrevs = {}
        for l in lls:
            ln = l['name']; sp = l['split']
            # Split% — same value across all historical years + FY0
            for col in (DS, DS + 1, FY0):
                I(ws, R, col, sp, fmt=PCT)
            C(ws, R, 3, f'  {ln} %', font=itf)
            srows.append(R); R += 1
            lr = round(srev * sp)
            anchor_info[ln] = (R, sc(lr))
            C(ws, R, 3, f'  {ln} FY{bfyr}A Rev', font=itf)
            split_row = srows[-1]
            line_to_seg[ln] = sn
            line_to_split[ln] = split_row
            for col in (DS, DS + 1, FY0):
                cl = get_column_letter(col)
                CF(ws, R, col, f'={cl}{rev_r}*{cl}{split_row}', fmt=NUM)
            lrevs[ln] = R; R += 1

        if srows:
            for col in (DS, DS + 1, FY0):
                cl = get_column_letter(col)
                refs = '+'.join([f'{cl}{sr}' for sr in srows])
                CF(ws, R, col, f'=1-({refs})', fmt=PCT)
            C(ws, R, 3, '  residual %', font=itf)
            res_row = R; R += 1
        else:
            res_row = 0

        seg_info[sn] = {
            'rev': rev_r, 'cost': cost_r, 'gp': gp_r, 'gm': gm_r,
            'split_rows': srows, 'lrev_rows': lrevs, 'res_row': res_row,
        }
        if op_r: seg_info[sn]['op'] = op_r
        # Mark yoy 1:1 lines (segment=line, no residual, no vol_asp fit)
        if len(lls) == 1 and lls[0]['split'] == 1.0:
            one_to_one.add(lls[0]['name'])

    # Detect deepest profit level disclosed across all segments (numeric ordering)
    DEPTH_RANK = {'gp': 0, 'op': 1, 'ni': 2}
    max_seg_depth = 0
    for seg in segments:
        fy0 = seg.get('fy0', {})
        if fy0.get('op') is not None and DEPTH_RANK['op'] > max_seg_depth: max_seg_depth = DEPTH_RANK['op']
        if fy0.get('ni') is not None and DEPTH_RANK['ni'] > max_seg_depth: max_seg_depth = DEPTH_RANK['ni']

    # ═══════════════ §2 Logic Lines ═══════════════
    s1_end = R  # Section 1 rows end here
    R += 1
    C(ws, R, 1, 'Logic Lines', font=bf12)
    R += 1
    L = {}
    protected_rows = set()
    for ll in logic_lines:
        ln = ll['name']
        module_name = ll.get('module', 'yoy')

        # Dispatch to module
        _load_module(module_name)
        render_fn = MODULES[module_name]

        result = render_fn(ws, R, ll, anchor_info, ctx)
        R = result['next_R']
        line_op_r = 0  # may be set by per-line profit chain below

        # ── Resolve line→segment (O(1) via dict) ──
        seg_name = line_to_seg.get(ln, '')
        si = seg_info.get(seg_name, {})
        s1_gp_row = si.get('gp', 0)
        s1_rev_row = si.get('rev', 0)
        split_r = line_to_split.get(ln, 0)
        lrev_row = si.get('lrev_rows', {}).get(ln, 0)
        seg_obj = None
        for s in segments:
            if s['name'] == seg_name:
                seg_obj = s
                break

        # ── Common: GM + GP (all modules) ──
        gm = ll['gm']
        if ln in one_to_one:
            # 1:1 → S1 formula for history + FY0
            for yr_key, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]:
                if col == FY0 or (seg_obj and seg_obj.get(yr_key)):
                    cl = get_column_letter(col)
                    C(ws, R, col, f'=IFERROR({cl}{si["gp"]}/{cl}{si["rev"]},"")', fmt=PCT)
        else:
            # Non-1:1 → I() assumption: all years from gm
            for yr_key, col in [('fy-2', DS), ('fy-1', DS + 1)]:
                if gm.get(yr_key): I(ws, R, col, gm[yr_key], fmt=PCT)
                else: C(ws, R, col, '', fmt=PCT)
            if gm.get('fy0'): I(ws, R, FY0, gm['fy0'], fmt=PCT)
        for i, v in enumerate(gm['proj']):
            I(ws, R, FY0 + 1 + i, v, fmt=PCT)
        C(ws, R, 3, 'GM')
        gm_r = R; R += 1

        for ci in range(DS, LC + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'=IFERROR({cl}{result["rev_r"]}*{cl}{gm_r},"")', fmt=NUM)
        C(ws, R, 3, 'GP')
        gp_r = R; R += 1

        # ── Check rows: anchor reference for reconciliation ──
        rev_module = ll.get('module', 'yoy')
        needs_rev_check = rev_module in ('vol_asp', 'backlog_burn', 'capacity_util')
        needs_gp_check = ln not in one_to_one
        hist_rev_ok = lrev_row and s1_rev_row and split_r
        hist_gp_ok = lrev_row and s1_gp_row and split_r

        if needs_rev_check:
            for col in (DS, DS + 1):
                cl = get_column_letter(col)
                if hist_rev_ok:
                    C(ws, R, col, f'={cl}{lrev_row}', fmt=NUM)
                else:
                    C(ws, R, col, '', fmt=NUM)
            if hist_rev_ok:
                C(ws, R, FY0, f'={get_column_letter(FY0)}{lrev_row}', fmt=NUM)
            for ci in range(FY0 + 1, LC + 1):
                C(ws, R, ci, '', fmt=NUM)
            gm_fy0 = gm.get('fy0', 0)
            gm_label = f' ({gm_fy0:.0%} GM)' if gm_fy0 else ''
            C(ws, R, 3, f'  Check Rev{gm_label}', font=itf)
            ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
            R += 1

        if needs_gp_check:
            for col in (DS, DS + 1):
                cl = get_column_letter(col)
                if hist_gp_ok:
                    C(ws, R, col, f'={cl}{s1_gp_row}*{cl}{split_r}', fmt=NUM)
                else:
                    C(ws, R, col, '', fmt=NUM)
            if hist_gp_ok:
                C(ws, R, FY0, f'={get_column_letter(FY0)}{s1_gp_row}*{get_column_letter(FY0)}{split_r}', fmt=NUM)
            for ci in range(FY0 + 1, LC + 1):
                C(ws, R, ci, '', fmt=NUM)
            seg_gm = seg_obj['fy0']['gm'] if seg_obj and seg_obj.get('fy0', {}).get('gm') else 0
            seg_gm_label = f' ({seg_gm:.0%} seg GM)' if seg_gm else ''
            C(ws, R, 3, f'  Check GP{seg_gm_label}', font=itf)
            ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
            R += 1

        # ── Per-line profit chain (gated by segment disclosure depth) ──
        if max_seg_depth >= DEPTH_RANK['op']:
            # Opex rate (per-line fallback to global)
            line_opex = ll.get('opex_rate')
            opex_rates = line_opex if line_opex else gl.get('opex_rate', [])
            _ope_r = R
            for yr_i, col in [(0, DS), (1, DS + 1), (2, FY0)]:
                if yr_i < len(opex_rates):
                    I(ws, R, col, opex_rates[yr_i], fmt=PCT)
                else:
                    C(ws, R, col, '', fmt=PCT)
            for i in range(proj_n):
                ri = 3 + i
                if ri < len(opex_rates):
                    I(ws, R, FY0 + 1 + i, opex_rates[ri], fmt=PCT)
            C(ws, R, 3, '  Opex / Rev', font=itf)
            R += 1
            # Opex
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'={cl}{result["rev_r"]}*{cl}{_ope_r}', fmt=NUM)
            C(ws, R, 3, '  Opex', font=itf)
            R += 1
            # OP
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'={cl}{gp_r}-{cl}{R - 1}', fmt=NUM)
            C(ws, R, 3, '  OP', font=bf)
            line_op_r = R; R += 1
            # OPM
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{line_op_r}/{cl}{result["rev_r"]},"")', fmt=PCT)
            C(ws, R, 3, '  OPM', font=itf)
            R += 1

            # Check OP (if segment discloses OP)
            seg_op_row = si.get('op', 0)
            if seg_op_row and split_r:
                for col in (DS, DS + 1):
                    cl = get_column_letter(col)
                    if hist_gp_ok:
                        C(ws, R, col, f'={cl}{seg_op_row}*{cl}{split_r}', fmt=NUM)
                    else:
                        C(ws, R, col, '', fmt=NUM)
                if hist_gp_ok:
                    C(ws, R, FY0, f'={get_column_letter(FY0)}{seg_op_row}*{get_column_letter(FY0)}{split_r}', fmt=NUM)
                for ci in range(FY0 + 1, LC + 1):
                    C(ws, R, ci, '', fmt=NUM)
                C(ws, R, 3, '  Check OP', font=itf)
                ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
                R += 1

        if max_seg_depth >= DEPTH_RANK['ni']:
            # Tax rate (per-line optional override, fallback to global scalar)
            line_tax = ll.get('tax_rate')
            if line_tax and isinstance(line_tax, list):
                _tax_r = R
                for yr_i, col in [(0, DS), (1, DS + 1), (2, FY0)]:
                    if yr_i < len(line_tax):
                        C(ws, R, col, line_tax[yr_i], fmt=PCT)
                    else:
                        C(ws, R, col, '', fmt=PCT)
                for i in range(proj_n):
                    ri = 3 + i
                    if ri < len(line_tax):
                        I(ws, R, FY0 + 1 + i, line_tax[ri], fmt=PCT)
                C(ws, R, 3, '  Tax rate', font=itf)
                R += 1
            else:
                _tax_r = 0
            tax_val = _tax_r if _tax_r else gl.get('tax_rate', 0)
            # Tax
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                if _tax_r:
                    C(ws, R, ci, f'={cl}{line_op_r}*{cl}{_tax_r}', fmt=NUM)
                else:
                    C(ws, R, ci, f'={cl}{line_op_r}*{tax_val}', fmt=NUM)
            C(ws, R, 3, '  Tax', font=itf)
            R += 1
            # NI
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'={cl}{line_op_r}-{cl}{R - 1}', fmt=NUM)
            C(ws, R, 3, '  NI', font=bf)
            R += 1

        result['gm_r'] = gm_r
        result['gp_r'] = gp_r
        result['op_r'] = line_op_r
        result['next_R'] = R
        L[ln] = result
        # Protect Rev, GM, GP, Check and per-line profit from D/E clear
        protected_rows.update([result['rev_r'], gm_r, gp_r])
        for scan_r in range(result['rev_r'], R):
            cv = str(ws.cell(row=scan_r, column=3).value or '')
            if any(kw in cv for kw in ('Check', 'YoY', 'Opex', 'OP', 'Tax', 'NI')):
                protected_rows.add(scan_r)

    # ═══════════════ §2→§1 Fill ─ Section 1 FY26E+ ═══════════════
    for seg in segments:
        sn = seg['name']; lls = seg['logic_lines']
        res_val = round(seg['fy0']['rev'] -
                        sum(seg['fy0']['rev'] * l['split'] for l in lls))
        res_val = res_val if res_val > 0 else 0
        res_gm = seg.get('residual', {}).get('gm', 0)
        si = seg_info.get(sn, {})
        s1r = si.get('rev', 0); s1c = si.get('cost', 0)
        s1g = si.get('gp', 0); s1gm = si.get('gm', 0)
        if not s1r or not s1g:
            continue
        srows = si.get('split_rows', [])
        lrevs = si.get('lrev_rows', {})
        res_row = si.get('res_row', 0)

        for ci in range(FY0 + 1, LC + 1):
            cl = get_column_letter(ci)
            CF(ws, s1r, ci, '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["rev_r"]}' for ln in lls] +
                ([str(sc(res_val))] if res_val else [])), fmt=NUM)
            CF(ws, s1c, ci, '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["rev_r"]}*(1-{cl}{L[ln["name"]]["gm_r"]})' for ln in lls] +
                ([f'{sc(res_val)}*(1-{res_gm})'] if res_val else [])), fmt=NUM)
            CF(ws, s1g, ci, '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["gp_r"]}' for ln in lls] +
                ([f'{sc(res_val)}*{res_gm}'] if res_val else [])), fmt=NUM)
            CF(ws, s1gm, ci, f'=IFERROR({cl}{s1g}/{cl}{s1r},"")', fmt=PCT)
            # OP fill (if segment discloses OP)
            s1_op = si.get('op', 0)
            if s1_op and max_seg_depth >= DEPTH_RANK['op']:
                op_terms = [f'{cl}{L[ln["name"]]["op_r"]}' for ln in lls if L[ln["name"]].get('op_r')]
                if op_terms:
                    CF(ws, s1_op, ci, '=' + '+'.join(op_terms), fmt=NUM)

        for ln_name in [l['name'] for l in lls]:
            for sr_row in srows:
                cell_val = ws.cell(row=sr_row, column=3).value
                if cell_val and ln_name in str(cell_val):
                    for ci in range(FY0 + 1, LC + 1):
                        cl = get_column_letter(ci)
                        CF(ws, sr_row, ci, f'=IFERROR({cl}{L[ln_name]["rev_r"]}/{cl}{s1r},"")', fmt=PCT)
            lr_row = lrevs.get(ln_name, 0)
            if lr_row:
                for ci in range(FY0 + 1, LC + 1):
                    cl = get_column_letter(ci)
                    CF(ws, lr_row, ci, f'={cl}{L[ln_name]["rev_r"]}', fmt=NUM)
        if res_row and srows:
            for ci in range(FY0 + 1, LC + 1):
                cl = get_column_letter(ci)
                refs = '+'.join([f'{cl}{r}' for r in srows])
                CF(ws, res_row, ci, f'=1-({refs})', fmt=PCT)

    # ── Non-core absorbs all segment residuals ──
    total_residual = 0; gp_residual = 0
    for seg in segments:
        r = round(seg['fy0']['rev'] - sum(seg['fy0']['rev'] * l['split'] for l in seg.get('logic_lines', [])))
        if r > 0:
            total_residual += r
            gp_residual += round(r * seg.get('residual', {}).get('gm', 0))
    # Patch Non-core Revenue + GP to include residuals
    if 'Non-core' in L:
        nc = L['Non-core']
        nc_rev_r = nc['rev_r']
        nc_gp_r = nc['gp_r']
        for ci in range(FY0, LC + 1):
            cl = get_column_letter(ci)
            old_rev = ws.cell(row=nc_rev_r, column=ci).value or ''
            old_gp = ws.cell(row=nc_gp_r, column=ci).value or ''
            if isinstance(old_rev, str) and old_rev.startswith('='):
                CF(ws, nc_rev_r, ci, old_rev + f'+{sc(total_residual)}', fmt=NUM)
            if isinstance(old_gp, str) and old_gp.startswith('='):
                CF(ws, nc_gp_r, ci, old_gp + f'+{sc(gp_residual)}', fmt=NUM)

    # Collapse Section 1 (segment rows only)
    ws.row_dimensions.group(s1_start, s1_end, outline_level=1, hidden=True)

    # ═══════════════ Global Opex / Tax rate ═══════════════
    s2_end = R  # Section 2 ends before Global; D/E clear stops here
    R += 1
    # Placeholder — formulas filled after P&L builds trev/ov rows
    for ci in range(DS, LC + 1):
        C(ws, R, ci, 0, fmt=PCT)
    C(ws, R, 3, 'Opex / Rev', font=bf)
    opex_r = R; R += 1
    for ci in range(DS, LC + 1):
        C(ws, R, ci, 0, fmt=PCT)
    C(ws, R, 3, 'Tax rate')
    tax_r = R; R += 1

    # ═══════════════ §3 P&L ═══════════════
    R += 1
    C(ws, R, 1, 'P&L', font=bf12)
    R += 1
    a = actuals
    LN = [ln['name'] for ln in logic_lines]

    residual_term = f'+{sc(total_residual)}' if total_residual else ''
    gp_residual_term = f'+{sc(gp_residual)}' if gp_residual else ''

    # Total Revenue (FY23-25 actuals, FY26+ formula)
    A(ws, R, DS, sc(a['fy-2']['rev']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['rev']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['rev']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term,
          font=bf, fmt=NUM)
    C(ws, R, 3, 'Total Revenue')
    trev = R; R += 1

    # Check Rev (model formula for validation)
    for ci in range(DS, FY0):
        C(ws, R, ci, '', fmt=NUM)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term, fmt=NUM)
    C(ws, R, 3, '  Check (model)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

    # Revenue YoY
    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{trev}/{cl_d}{trev}-1,"")', fmt=PCT)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{trev}/{get_column_letter(ci-1)}{trev}-1,"")', fmt=PCT)
    C(ws, R, 3, 'Rev YoY')
    R += 1

    # Total GP (FY23-25 actuals, FY26+ formula)
    A(ws, R, DS, sc(a['fy-2']['gp']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['gp']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['gp']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term,
          font=bf, fmt=NUM)
    C(ws, R, 3, 'Total GP')
    tgp = R; R += 1

    # Check GP (model formula for validation)
    for ci in range(DS, FY0):
        C(ws, R, ci, '', fmt=NUM)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term, fmt=NUM)
    C(ws, R, 3, '  Check (model)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

    # Blended GM
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{tgp}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'Blended GM')
    R += 1

    # ── P&L depth (controls display, SOTP always has full chain) ──
    nci_rate = meta.get('nci_rate', 0)
    net_debt = meta.get('net_debt', 0)

    # Opex + OP (always computed)
    opex_fy2 = a['fy-2'].get('opex', a['fy-2']['gp'] - a['fy-2']['op'])
    opex_fy1 = a['fy-1'].get('opex', a['fy-1']['gp'] - a['fy-1']['op'])
    _opex_start = R
    A(ws, R, DS, sc(opex_fy2), fmt=NUM)
    A(ws, R, DS + 1, sc(opex_fy1), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['opex']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{trev}*{cl}{opex_r}', fmt=NUM)
    C(ws, R, 3, 'Opex')
    ov = R; R += 1

    A(ws, R, DS, sc(a['fy-2']['op']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['op']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['op']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{tgp}-{cl}{ov}', font=bf, fmt=NUM)
    C(ws, R, 3, 'Operating Profit')
    op = R; R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{op}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'OPM')
    _opex_end = R; R += 1

    # D&A + EBITDA (always computed)
    da_fy2 = a['fy-2'].get('da', 0); da_fy1 = a['fy-1'].get('da', 0)
    da_fy0 = a['fy0'].get('da', 0)
    _ebitda_start = R
    A(ws, R, DS, sc(da_fy2), fmt=NUM)
    A(ws, R, DS + 1, sc(da_fy1), fmt=NUM)
    A(ws, R, FY0, sc(da_fy0), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}*{get_column_letter(FY0)}{da_fy0}/{get_column_letter(FY0)}{trev}', fmt=NUM)
    C(ws, R, 3, 'D&A')
    da_r = R; R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}+{cl}{da_r}', font=bf, fmt=NUM)
    C(ws, R, 3, 'EBITDA')
    ebitda_r = R; R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ebitda_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'EBITDA margin')
    _ebitda_end = R; R += 1

    # EBIT (always computed)
    _ebit_start = R
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{ebitda_r}-{cl}{da_r}', font=bf, fmt=NUM)
    C(ws, R, 3, 'EBIT')
    ebit_r = R; R += 1
    _ebit_end = ebit_r

    # Tax + NI (always computed)
    _ni_start = R
    A(ws, R, DS, sc(a['fy-2']['tax']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['tax']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['tax']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{ebit_r}*{cl}{tax_r}', fmt=NUM)
    C(ws, R, 3, 'Tax')
    tv = R; R += 1

    A(ws, R, DS, sc(a['fy-2']['ni']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['ni']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['ni']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{ebit_r}-{cl}{tv}', font=bf, fmt=NUM)
    C(ws, R, 3, 'Net Income')
    ni_r = R; R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'NPM')
    R += 1

    if nci_rate > 0:
        for ci in range(DS, LC + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{ni_r}*(1-{nci_rate})', font=bf, fmt=NUM)
        C(ws, R, 3, 'NI attributable')
        ni_r = R; R += 1

    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{ni_r}/{cl_d}{ni_r}-1,"")', fmt=PCT)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{get_column_letter(ci - 1)}{ni_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'NI YoY')
    _ni_end = R; R += 1

    # ── Fix Global Opex rate / Tax rate formulas ──
    # FY23-25: =Opex/Rev, =Tax/OP (formulas, no fill — computed not raw actuals)
    for ci in [DS, DS + 1, FY0]:
        cl = get_column_letter(ci)
        CF(ws, opex_r, ci, f'=IFERROR({cl}{ov}/{cl}{trev},"")', fmt=PCT)
    for i, ov_val in enumerate(gl['opex_rate'][3:], FY0 + 1):
        I(ws, opex_r, i, ov_val, fmt=PCT)
    for ci in [DS, DS + 1, FY0]:
        cl = get_column_letter(ci)
        CF(ws, tax_r, ci, f'=IFERROR({cl}{tv}/{cl}{op},"")', fmt=PCT)
    for ci in range(FY0 + 1, LC + 1):
        I(ws, tax_r, ci, gl['tax_rate'], fmt=PCT)

    # ═══════════════ §4 SOTP - Logic ═══════════════
    R += 1
    C(ws, R, 1, 'SOTP - Logic', font=bf12)
    R += 1
    sc_l = get_column_letter(SC)
    mc_rows = []

    def _sotp_info(ll):
        """Resolve sotp method + multiple, backward-compat with sotp_pe."""
        s = ll.get('sotp', {})
        if not s and 'sotp_pe' in ll:
            s = {'method': 'pe', 'multiple': ll['sotp_pe']}
        return s.get('method', 'pe'), s.get('multiple', 10)

    def _sotp_metric_ref(method):
        """Return (metric_row, metric_label) for a given valuation method.
        All metrics always exist. P&L depth set by segment disclosure (max_seg_depth)."""
        if method == 'pe':
            return ni_r, 'NI'
        if method == 'ev_ebitda':
            return ebitda_r, 'EBITDA'
        if method == 'ev_ebit':
            return ebit_r, 'EBIT'
        if method in ('ev_sales', 'ps'):
            return trev, 'Revenue'
        return tgp, 'GP'

    for ll in logic_lines:
        ln = ll['name']
        method, mult = _sotp_info(ll)
        metric_r, metric_label = _sotp_metric_ref(method)
        gc = f'{sc_l}{L[ln]["gp_r"]}'
        mc = f'{sc_l}{metric_r}'
        tc_gp = f'{sc_l}{tgp}'
        tc_rev = f'{sc_l}{trev}'

        # GP (allocation base)
        C(ws, R, 2, ln, font=bf)
        C(ws, R, 3, 'GP')
        C(ws, R, SC, f'={gc}', fmt=NUM)
        R += 1

        # Allocated metric
        if method in ('ev_sales', 'ps'):
            alloc_ref = f'{sc_l}{L[ln]["rev_r"]}'
            alloc_formula = f'={alloc_ref}'
        else:
            alloc_formula = f'=IFERROR({mc}*{gc}/{tc_gp},"")'
            alloc_ref = f'({mc}*{gc}/{tc_gp})'
        C(ws, R, 3, metric_label)
        C(ws, R, SC, alloc_formula, fmt=NUM)
        R += 1

        # Multiple input
        if method == 'pe':      label_m = 'PE'
        elif method == 'ps':    label_m = 'P/S'
        else:                   label_m = method.replace('_', '/').upper()
        I(ws, R, SC, mult, fmt='0.0x')
        C(ws, R, 3, label_m)
        mult_row = R; R += 1

        # MCap
        if method.startswith('ev_'):
            nd_share = f'({gc}/{tc_gp}*{net_debt})' if net_debt else '0'
            mcap_f = f'=IFERROR({alloc_ref}*{sc_l}{mult_row}-{nd_share},"")'
        else:
            mcap_f = f'=IFERROR({alloc_ref}*{sc_l}{mult_row},"")'
        C(ws, R, 3, 'Mkt Cap')
        C(ws, R, SC, mcap_f, font=bf, fmt=DEC)
        mc_rows.append(R); R += 1

    C(ws, R, 2, 'TOTAL', font=bf)
    C(ws, R, SC, '=' + '+'.join([f'{sc_l}{mr}' for mr in mc_rows]),
      font=bf, fmt=DEC)
    sotp_r = R; R += 1

    # ═══════════════ §5 SOTP - Segments ═══════════════
    R += 1
    C(ws, R, 1, 'SOTP - Segments', font=bf12)
    R += 1
    smc_rows = []
    LL_SOTP = {}
    for ll in logic_lines:
        method, mult = _sotp_info(ll)
        LL_SOTP[ll['name']] = (method, mult)

    for seg in segments:
        sn = seg['name']; lls = seg['logic_lines']
        # Weighted multiple across logic lines in segment
        lmethods = [LL_SOTP[l['name']][1] for l in lls]  # multiples only
        w_mult = sum(lmethods[i] * seg['fy0']['rev'] * lls[i]['split']
                     for i in range(len(lls))) / seg['fy0']['rev'] if seg['fy0']['rev'] > 0 else 10
        mult_s = round(w_mult)
        method_s = LL_SOTP[lls[0]['name']][0]  # use first line's method for segment
        metric_r_s, metric_label_s = _sotp_metric_ref(method_s)
        gc = f'{sc_l}{seg_info[sn]["gp"]}'
        mc = f'{sc_l}{metric_r_s}'

        C(ws, R, 2, sn, font=bf)
        C(ws, R, 3, 'GP')
        C(ws, R, SC, f'={gc}', fmt=NUM)
        R += 1

        if method_s in ('ev_sales', 'ps'):
            alloc_ref_s = f'{sc_l}{seg_info[sn]["rev"]}'
            alloc_f_s = f'={alloc_ref_s}'
        else:
            alloc_f_s = f'=IFERROR({mc}*{gc}/{sc_l}{tgp},"")'
            alloc_ref_s = f'({mc}*{gc}/{sc_l}{tgp})'
        C(ws, R, 3, metric_label_s)
        C(ws, R, SC, alloc_f_s, fmt=NUM)
        R += 1

        if method_s == 'pe':      label_ms = 'PE'
        elif method_s == 'ps':    label_ms = 'P/S'
        else:                     label_ms = method_s.replace('_', '/').upper()
        I(ws, R, SC, mult_s, fmt='0.0x')
        C(ws, R, 3, label_ms)
        pe_row = R; R += 1

        if method_s.startswith('ev_'):
            nd_s = f'({gc}/{sc_l}{tgp}*{net_debt})' if net_debt else '0'
            mcap_f_s = f'=IFERROR({alloc_ref_s}*{sc_l}{pe_row}-{nd_s},"")'
        else:
            mcap_f_s = f'=IFERROR({alloc_ref_s}*{sc_l}{pe_row},"")'
        C(ws, R, 3, 'Mkt Cap')
        C(ws, R, SC, mcap_f_s, font=bf, fmt=DEC)
        smc_rows.append(R); R += 1

    C(ws, R, 2, 'TOTAL', font=bf)
    C(ws, R, SC, '=' + '+'.join([f'{sc_l}{mr}' for mr in smc_rows]),
      font=bf, fmt=DEC)
    sotp_seg_r = R; R += 1

    # ═══════════════ §6 Market Data ═══════════════
    R += 1
    # Key metrics — highlighted
    C(ws, R, 3, 'MCap', font=hlfont, fill=hlfill)
    C(ws, R, SC, mcap_d, fmt=NUM)
    mcap_data_r = R; R += 1
    if shares:
        C(ws, R, 3, 'Shares (M)', font=hlfont, fill=hlfill)
        C(ws, R, SC, shares, fmt='#,##0.0')
        shares_data_r = R; R += 1
    if price:
        C(ws, R, 3, 'Price', font=hlfont, fill=hlfill)
        C(ws, R, SC, price, fmt=price_fmt)
        price_data_r = R; R += 1
    R += 1
    mref = f'{sc_l}{mcap_data_r}'

    # Implied valuation
    if shares:
        implied_logic = f'=IFERROR({sc_l}{sotp_r}*{div}/{sc_l}{shares_data_r},"")'
        implied_seg = f'=IFERROR({sc_l}{sotp_seg_r}*{div}/{sc_l}{shares_data_r},"")'
        C(ws, R, 3, 'Implied Price')
        C(ws, R, SC, implied_logic, fmt=price_fmt)
        imp_row = R; R += 1
        C(ws, R, 3, 'Implied Price (Seg)')
        C(ws, R, SC, implied_seg, fmt=price_fmt)
        R += 1
        C(ws, R, 3, 'Upside / Downside')
        C(ws, R, SC, f'=IFERROR({sc_l}{imp_row}/{sc_l}{price_data_r}-1,"")', fmt='0.0%')
        R += 1
    if ttm_pe:
        C(ws, R, 3, 'TTM PE')
        C(ws, R, SC, round(ttm_pe, 1), fmt='0.0x')
        R += 1
    if fwd_pe:
        C(ws, R, 3, 'Fwd PE')
        C(ws, R, SC, round(fwd_pe, 1), fmt='0.0x')
        R += 1
    if hi52:
        currency_prefix = PRICE_FMT.get(meta.get('market', 'cn'), '¥#,##0.00').replace('#,##0.00','').replace('#,##0','').rstrip()
        C(ws, R, 3, '52W Range')
        C(ws, R, SC, f'{currency_prefix}{lo52:.0f} - {currency_prefix}{hi52:.0f}')
        R += 1

    # ═══════════════ §7 Scenario Summary ═══════════════
    R += 2
    C(ws, R, 1, 'Scenario Summary', font=bf12)
    R += 1
    syl = YR[2 + s_off].replace('A', 'E')
    C(ws, R, DS, f'{syl} Rev', font=bf)
    C(ws, R, DS + 1, f'{syl} GP', font=bf)
    # Determine dominant metric/multiple labels from SOTP methods in use
    methods = set()
    for ll in logic_lines:
        if ll.get('sotp'):
            methods.add(ll['sotp'].get('method', 'pe'))
        elif 'sotp_pe' in ll:
            methods.add('pe')
    if not methods: methods = {'pe'}
    ev_only = all(m.startswith('ev_') for m in methods)
    metric_label = 'EBITDA' if ev_only else ('Revenue' if methods == {'ps'} else 'NI')
    mult_label = 'Implied EV/EBITDA' if ev_only else ('Implied P/S' if methods == {'ps'} else 'Implied PE')
    C(ws, R, DS + 2, f'{syl} {metric_label}', font=bf)
    C(ws, R, DS + 3, mult_label, font=bf)
    R += 1
    syc = get_column_letter(FY0 + s_off)

    for label, yk in [('Bull', 'yb'), ('Base', 'ybs'), ('Bear', 'ybe')]:
        rp = []; gp = []
        for ll in logic_lines:
            ln = ll['name']
            rows = L.get(ln)
            if not rows:
                continue
            is_yoy = rows.get('module') == 'yoy'
            if is_yoy and yk in rows:
                # yoy: chain projection FY0 → FY0+s_off
                yr = rows[yk]
                comp = f'{get_column_letter(FY0)}{rows["rev_r"]}'
                for off in range(1, s_off + 1):
                    comp = f'{comp}*(1+{get_column_letter(FY0 + off)}{yr})'
            elif yk in rows:
                # non-yoy with BBE cache: direct SC read
                comp = f'{sc_l}{rows[yk]}'
            else:
                # non-yoy no BBE: use Revenue SC (scenario-independent)
                comp = f'{sc_l}{rows["rev_r"]}'
            rp.append(comp)
            gp.append(f'({comp}*{sc_l}{rows["gm_r"]})')
        if not rp:
            continue
        rf = '=' + '+'.join(rp)
        gf = '=' + '+'.join(gp)
        # NI = (GP - Rev×opex_rate) × (1-tax_rate) — correct P&L path
        rev_total_sc = f'({rf[1:]})' if rf.startswith('=') else rf
        gp_total_sc = f'({gf[1:]})' if gf.startswith('=') else gf
        nf_s = f'=({gp_total_sc}-{rev_total_sc}*{syc}{opex_r})*(1-{syc}{tax_r})'
        pf = f'=IFERROR({mref}/({nf_s[1:]}),"")'
        C(ws, R, 2, label, font=bf)
        C(ws, R, DS, rf, fmt=NUM)
        C(ws, R, DS + 1, gf, fmt=NUM)
        C(ws, R, DS + 2, nf_s, fmt=NUM)
        C(ws, R, DS + 3, pf, font=bf, fmt='0.0x')
        R += 1

    # ═══════════════ Post-format ═══════════════
    for row in range(1, R):
        # Clear placeholder zeros
        for c in range(DS, LC + 1):
            cl = ws.cell(row=row, column=c)
            if cl.value == 0:
                cl.value = None
        # Clear D/E formula-only cells (Section 2 only, skip protected rows)
        if s1_end < row <= s2_end and row not in protected_rows:
            for c in (DS, DS + 1):
                cl = ws.cell(row=row, column=c)
                if cl.value and isinstance(cl.value, str) and cl.value.startswith('='):
                    cl.value = None
        # Bold actuals in data columns (gray fill → bold font)
        for c in range(DS, LC + 1):
            cl = ws.cell(row=row, column=c)
            if cl.fill and cl.fill.start_color and cl.fill.start_color.rgb == '00F0F0F0':
                cl.font = bf
        # Bold key C-column labels
        cv = ws.cell(row=row, column=3).value
        if cv and isinstance(cv, str) and cv.strip() in {
            'Revenue', 'Cost', 'GP', 'GM', 'OP', 'OPM', 'OP YoY',
            'Total Revenue', 'Rev YoY', 'Total GP', 'Blended GM',
            'Opex', 'Operating Profit', 'EBITDA', 'EBIT',
            'Tax', 'Net Income', 'NPM', 'NI YoY',
        }:
            cell = ws.cell(row=row, column=3)
            if not (cell.fill and cell.fill.start_color and cell.fill.start_color.rgb == '00963634'):
                cell.font = bf
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 24
    ws.column_dimensions['C'].width = 36
    for ci in range(DS, LC + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 13

    ws.freeze_panes = 'D2'

    out_path = output_path or json_path.replace('.json', '.xlsx')
    wb.save(out_path)
    print(f'OK: {out_path}')


# ═══════════════════════════════════════════════════════════════
# CLI entry
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('json_path')
    p.add_argument('-o', '--output')
    a = p.parse_args()
    build(a.json_path, a.output)
