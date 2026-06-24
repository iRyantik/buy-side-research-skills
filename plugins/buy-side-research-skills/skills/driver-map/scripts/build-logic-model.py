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
                                Depth switch (gp/ebitda/ebit/ni) controls row count
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

import json, argparse, codecs
import yfinance as yf
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# ── Format constants ──
PCT = '0.0%'; NUM = '#,##0'; DEC = '#,##0.0'; YEN = '¥#,##0.00'
DS = 4; COLS = 8

# ── Fonts / fills ──
nf   = Font(name='Calibri', size=11)
bf   = Font(name='Calibri', bold=True, size=11)
bf12 = Font(name='Calibri', bold=True, size=12)
itf  = Font(name='Calibri', size=10, italic=True, color='808080')
inpf = Font(name='Calibri', size=11, color='0000CC')
inpfill = PatternFill('solid', fgColor='FFFFCC')

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

# ── Context dict passed to modules ──
def make_ctx():
    return {
        'C': C, 'I': I,
        'nf': nf, 'bf': bf, 'itf': itf,
        'NUM': NUM, 'DEC': DEC, 'PCT': PCT,
        'DS': DS, 'FY0': DS + 2, 'LC': DS + COLS - 1,
        'proj_n': 0,
    }

# ═══════════════════════════════════════════════════════════════
# Built-in: base yoy template
# ═══════════════════════════════════════════════════════════════

def render_yoy(ws, R, ll, anchor_info, ctx):
    """Base yoy: Revenue = Section 1 ref, YoY Active (BBE group)."""
    C = ctx['C']; I = ctx['I']
    nf = ctx['nf']; bf = ctx['bf']; itf = ctx['itf']
    NUM = ctx['NUM']; PCT = ctx['PCT']
    DS = ctx['DS']; FY0 = ctx['FY0']; LC = ctx['LC']
    proj_n = ctx['proj_n']

    ln = ll['name']
    yoy = ll['yoy']
    bull = yoy['bull']; base = yoy['base']; bear = yoy['bear']
    s1r, _ = anchor_info.get(ln, (0, 0))

    # ── Revenue (FY25A = Section 1 ref) ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, FY0, f'={get_column_letter(FY0)}{s1r}', fmt=NUM)
    rev_r = R
    C(ws, R, 2, ln, font=bf)
    C(ws, R, 3, 'Revenue')
    R += 1

    # ── YoY Active (FY25A blank, FY26E+ formula) ──
    ya = R
    for ci in range(DS, FY0):
        C(ws, R, ci, '', fmt=PCT)
    C(ws, R, FY0, '', fmt=PCT)
    for i in range(proj_n):
        C(ws, R, FY0 + 1 + i, 0, fmt=PCT)
    C(ws, R, 3, 'YoY')
    R += 1

    # ── BBE YoY hidden rows ──
    yb = ys = ye = 0
    for arr, label in [(bull, 'Bull'), (base, 'Base'), (bear, 'Bear')]:
        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        C(ws, R, FY0, '', fmt=PCT)
        for i, v in enumerate(arr):
            I(ws, R, FY0 + 1 + i, v, fmt=PCT)
        C(ws, R, 3, f'  {label}', font=itf)
        ws.row_dimensions[R].hidden = True
        if label == 'Bull':   yb = R
        elif label == 'Base': ys = R
        elif label == 'Bear': ye = R
        R += 1

    ws.row_dimensions.group(yb, ye, outline_level=1, hidden=True)

    # ── YoY Active formulas + Revenue FY26+ formulas ──
    for i in range(proj_n):
        ci = FY0 + 1 + i
        cl = get_column_letter(ci)
        ws.cell(row=ya, column=ci).value = \
            f'=IF(B1="Bull",{cl}{yb},IF(B1="Bear",{cl}{ye},{cl}{ys}))'
        ws.cell(row=rev_r, column=FY0 + 1 + i).value = \
            f'={get_column_letter(FY0 + i)}{rev_r}*(1+{cl}{ya})'

    return {
        'next_R': R,
        'rev_r': rev_r,
        'gm_r': None,
        'gp_r': None,
        'yb': yb, 'ybs': ys, 'ybe': ye, 'ya': ya,
        'module': 'yoy',
    }


# ═══════════════════════════════════════════════════════════════
# Module registry
# ═══════════════════════════════════════════════════════════════

MODULES = {
    'yoy': render_yoy,
}

# Lazy imports for external modules
def _load_module(name):
    if name not in MODULES:
        if name == 'vol_asp':
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
        info = yf.Ticker(meta['ticker']).info
    except Exception:
        info = {}
    mcap_raw = info.get('marketCap', 0) or 0
    price = info.get('currentPrice', 0) or 0
    shares = int(info.get('sharesOutstanding', 0) / 1e6) or 0
    ttm_pe = info.get('trailingPE', 0) or 0
    fwd_pe = info.get('forwardPE', 0) or 0
    hi52 = info.get('fiftyTwoWeekHigh', 0) or 0
    lo52 = info.get('fiftyTwoWeekLow', 0) or 0
    mcap_M = int(mcap_raw / 1e6) if mcap_raw else 0
    use_B = meta.get('market', '') in ('jp', 'kr', 'tw') or mcap_M > 1_000_000
    div = 1000 if use_B else 1
    mcap_d = round(mcap_M / div, 1)

    def sc(v):
        return round(v / div, 2)

    bfyr = meta['base_fy']; proj_n = meta['proj_years']; s_off = meta['sotp_offset']
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
    ctx['bfyr'] = bfyr

    # ═══════════════ §1 Reported Segments ═══════════════
    R = 3
    C(ws, R, 1, 'Reported Segments', font=bf12)
    R = 5
    seg_info = {}
    anchor_info = {}  # logic_fy25 renamed: {ln: (Section1_Rev_row, value_in_M)}

    for seg in segments:
        sn = seg['name']; fy0 = seg['fy0']; lls = seg['logic_lines']
        srev = fy0['rev']; scost = fy0['cost']; sgp = fy0['gp']; sgm = fy0['gm']

        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=NUM)
        C(ws, R, FY0, sc(srev), fmt=NUM)
        rev_r = R
        C(ws, R, 2, sn, font=bf)
        C(ws, R, 3, 'Revenue')
        R += 1

        # Implied YoY
        f0 = get_column_letter(FY0); f_1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({f0}{rev_r}/{f_1}{rev_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        C(ws, R, 3, 'Implied YoY')
        R += 1

        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=NUM)
        C(ws, R, FY0, sc(scost), fmt=NUM)
        cost_r = R
        C(ws, R, 3, 'Cost')
        R += 1

        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=NUM)
        C(ws, R, FY0, sc(sgp), fmt=NUM)
        gp_r = R
        C(ws, R, 3, 'GP')
        R += 1

        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        C(ws, R, FY0, sgm, fmt=PCT)
        gm_r = R
        C(ws, R, 3, 'GM')
        R += 1

        srows = []; lrevs = {}
        for l in lls:
            ln = l['name']; sp = l['split']
            for ci in range(DS, DS + 2):
                C(ws, R, ci, '', fmt=PCT)
            I(ws, R, FY0, sp, fmt=PCT)
            C(ws, R, 3, f'  {ln} %', font=itf)
            srows.append(R); R += 1
            lr = round(srev * sp)
            anchor_info[ln] = (R, sc(lr))
            C(ws, R, 3, f'  {ln} FY25A Rev', font=itf)
            C(ws, R, FY0, sc(lr), fmt=NUM)
            lrevs[ln] = R; R += 1

        if srows:
            for ci in range(DS, DS + 2):
                C(ws, R, ci, '', fmt=PCT)
            refs = '+'.join([f'{get_column_letter(FY0)}{sr}' for sr in srows])
            C(ws, R, FY0, f'=1-({refs})', fmt=PCT)
            C(ws, R, 3, '  residual %', font=itf)
            res_row = R; R += 1
        else:
            res_row = 0

        seg_info[sn] = {
            'rev': rev_r, 'cost': cost_r, 'gp': gp_r, 'gm': gm_r,
            'split_rows': srows, 'lrev_rows': lrevs, 'res_row': res_row,
        }

    # ═══════════════ §2 Logic Lines ═══════════════
    R += 1
    C(ws, R, 1, 'Logic Lines', font=bf12)
    R += 1
    L = {}

    for ll in logic_lines:
        ln = ll['name']
        module_name = ll.get('module', 'yoy')

        # Dispatch to module
        _load_module(module_name)
        render_fn = MODULES[module_name]

        result = render_fn(ws, R, ll, anchor_info, ctx)
        R = result['next_R']

        # ── Common: GM + GP (all modules) ──
        gm = ll['gm']
        if gm.get('fy0'):
            C(ws, R, FY0, gm['fy0'], fmt=PCT)
        for i, v in enumerate(gm['proj']):
            I(ws, R, FY0 + 1 + i, v, fmt=PCT)
        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        C(ws, R, 3, 'GM')
        gm_r = R; R += 1

        for ci in range(DS, LC + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'=IFERROR({cl}{result["rev_r"]}*{cl}{gm_r},"")', fmt=NUM)
        C(ws, R, 3, 'GP')
        gp_r = R; R += 1

        result['gm_r'] = gm_r
        result['gp_r'] = gp_r
        result['next_R'] = R
        L[ln] = result

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
            ws.cell(row=s1r, column=ci).value = '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["rev_r"]}' for ln in lls] +
                ([str(sc(res_val))] if res_val else []))
            ws.cell(row=s1r, column=ci).number_format = NUM
            ws.cell(row=s1c, column=ci).value = '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["rev_r"]}*(1-{cl}{L[ln["name"]]["gm_r"]})' for ln in lls] +
                ([f'{sc(res_val)}*(1-{res_gm})'] if res_val else []))
            ws.cell(row=s1c, column=ci).number_format = NUM
            ws.cell(row=s1g, column=ci).value = '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["gp_r"]}' for ln in lls] +
                ([f'{sc(res_val)}*{res_gm}'] if res_val else []))
            ws.cell(row=s1g, column=ci).number_format = NUM
            ws.cell(row=s1gm, column=ci).value = f'=IFERROR({cl}{s1g}/{cl}{s1r},"")'
            ws.cell(row=s1gm, column=ci).number_format = PCT

        for ln_name in [l['name'] for l in lls]:
            for sr_row in srows:
                cell_val = ws.cell(row=sr_row, column=3).value
                if cell_val and ln_name in str(cell_val):
                    for ci in range(FY0 + 1, LC + 1):
                        cl = get_column_letter(ci)
                        ws.cell(row=sr_row, column=ci).value = \
                            f'=IFERROR({cl}{L[ln_name]["rev_r"]}/{cl}{s1r},"")'
                        ws.cell(row=sr_row, column=ci).number_format = PCT
            lr_row = lrevs.get(ln_name, 0)
            if lr_row:
                for ci in range(FY0 + 1, LC + 1):
                    cl = get_column_letter(ci)
                    ws.cell(row=lr_row, column=ci).value = \
                        f'={cl}{L[ln_name]["rev_r"]}'
                    ws.cell(row=lr_row, column=ci).number_format = NUM
        if res_row and srows:
            for ci in range(FY0 + 1, LC + 1):
                cl = get_column_letter(ci)
                refs = '+'.join([f'{cl}{r}' for r in srows])
                ws.cell(row=res_row, column=ci).value = f'=1-({refs})'
                ws.cell(row=res_row, column=ci).number_format = PCT

    # ═══════════════ Global Opex / Tax rate ═══════════════
    R += 1
    for i, ov in enumerate(gl['opex_rate']):
        ci = DS + i
        C(ws, R, ci, ov, fmt=PCT)
        if ci > FY0:
            I(ws, R, ci, ov, fmt=PCT)
    C(ws, R, 3, 'Opex / Rev', font=bf)
    opex_r = R; R += 1
    for ci in range(DS, LC + 1):
        C(ws, R, ci, gl['tax_rate'], fmt=PCT)
    C(ws, R, 3, 'Tax rate')
    tax_r = R; R += 1

    # ═══════════════ §3 P&L ═══════════════
    R += 1
    C(ws, R, 1, 'P&L', font=bf12)
    R += 1
    a = actuals
    LN = [ln['name'] for ln in logic_lines]

    # Total Revenue
    C(ws, R, DS, sc(a['fy-2']['rev']), fmt=NUM)
    C(ws, R, DS + 1, sc(a['fy-1']['rev']), fmt=NUM)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]),
          font=bf, fmt=NUM)
    C(ws, R, 3, 'Total Revenue')
    trev = R; R += 1

    # Check Rev
    fy0rev = a['fy0']['rev']
    for ci in range(DS, FY0):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, FY0, sc(fy0rev), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, '  Check (actual)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

    # Revenue YoY
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        if ci <= DS + 1:
            C(ws, R, ci, '', fmt=PCT)
        else:
            C(ws, R, ci, f'=IFERROR({cl}{trev}/{get_column_letter(ci-1)}{trev}-1,"")', fmt=PCT)
    C(ws, R, 3, 'Rev YoY')
    R += 1

    # Total GP
    C(ws, R, DS, sc(a['fy-2']['gp']), fmt=NUM)
    C(ws, R, DS + 1, sc(a['fy-1']['gp']), fmt=NUM)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]),
          font=bf, fmt=NUM)
    C(ws, R, 3, 'Total GP')
    tgp = R; R += 1

    fy0gp = a['fy0']['gp']
    for ci in range(DS, FY0):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, FY0, sc(fy0gp), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, '  Check (actual)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

    # Blended GM
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{tgp}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'Blended GM')
    R += 1

    # ── P&L depth (controls display, SOTP always has full chain) ──
    depth = meta.get('p&l_depth', 'ni')
    nci_rate = meta.get('nci_rate', 0)
    net_debt = meta.get('net_debt', 0)

    # Opex + OP (always computed)
    opex_fy2 = a['fy-2'].get('opex', a['fy-2']['gp'] - a['fy-2']['op'])
    opex_fy1 = a['fy-1'].get('opex', a['fy-1']['gp'] - a['fy-1']['op'])
    _opex_start = R
    C(ws, R, DS, sc(opex_fy2), fmt=NUM)
    C(ws, R, DS + 1, sc(opex_fy1), fmt=NUM)
    C(ws, R, FY0, sc(a['fy0']['opex']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{trev}*{cl}{opex_r}', fmt=NUM)
    C(ws, R, 3, 'Opex')
    ov = R; R += 1

    C(ws, R, DS, sc(a['fy-2']['op']), fmt=NUM)
    C(ws, R, DS + 1, sc(a['fy-1']['op']), fmt=NUM)
    C(ws, R, FY0, sc(a['fy0']['op']), fmt=NUM)
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
    C(ws, R, DS, sc(da_fy2), fmt=NUM)
    C(ws, R, DS + 1, sc(da_fy1), fmt=NUM)
    C(ws, R, FY0, sc(da_fy0), fmt=NUM)
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
    C(ws, R, DS, sc(a['fy-2']['tax']), fmt=NUM)
    C(ws, R, DS + 1, sc(a['fy-1']['tax']), fmt=NUM)
    C(ws, R, FY0, sc(a['fy0']['tax']), fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{ebit_r}*{cl}{tax_r}', fmt=NUM)
    C(ws, R, 3, 'Tax')
    tv = R; R += 1

    C(ws, R, DS, sc(a['fy-2']['ni']), fmt=NUM)
    C(ws, R, DS + 1, sc(a['fy-1']['ni']), fmt=NUM)
    C(ws, R, FY0, sc(a['fy0']['ni']), fmt=NUM)
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

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        if ci <= DS + 1:
            C(ws, R, ci, '', fmt=PCT)
        else:
            C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{get_column_letter(ci - 1)}{ni_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'NI YoY')
    _ni_end = R; R += 1

    # Hide rows above display depth (SOTP always has full chain)
    if depth == 'gp':
        ws.row_dimensions.group(_opex_start, _ni_end, outline_level=1, hidden=True)
    elif depth == 'ebitda':
        ws.row_dimensions.group(_ebit_start, _ni_end, outline_level=1, hidden=True)
    elif depth == 'ebit':
        ws.row_dimensions.group(_ni_start, _ni_end, outline_level=1, hidden=True)

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
        All metrics always exist (hidden rows if above P&L display depth)."""
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
        I(ws, R, SC, mult)
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
        I(ws, R, SC, mult_s)
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
    C(ws, R, 3, 'MCap', font=bf)
    C(ws, R, SC, mcap_d, fmt=NUM)
    mcap_data_r = R; R += 1
    if shares:
        C(ws, R, 3, 'Shares (M)', font=bf)
        C(ws, R, SC, sc(shares), fmt=NUM)
        shares_data_r = R; R += 1
    if price:
        C(ws, R, 3, 'Price', font=bf)
        C(ws, R, SC, price, fmt=YEN)
        price_data_r = R; R += 1
    R += 1
    mref = f'{sc_l}{mcap_data_r}'
    C(ws, R, 3, 'SOTP Logic / MCap')
    C(ws, R, SC, f'=IFERROR({sc_l}{sotp_r}/{mref},"")', fmt='0.0%')
    R += 1
    C(ws, R, 3, 'SOTP Seg / MCap')
    C(ws, R, SC, f'=IFERROR({sc_l}{sotp_seg_r}/{mref},"")', fmt='0.0%')
    R += 1
    if shares:
        C(ws, R, 3, 'SOTP Logic / Share')
        C(ws, R, SC, f'=IFERROR({sc_l}{sotp_r}*1000/{sc_l}{shares_data_r},"")', fmt=YEN)
        R += 1
        C(ws, R, 3, 'SOTP Seg / Share')
        C(ws, R, SC, f'=IFERROR({sc_l}{sotp_seg_r}*1000/{sc_l}{shares_data_r},"")', fmt=YEN)
        R += 1
    if price:
        C(ws, R, 3, 'Current Price')
        C(ws, R, SC, f'={sc_l}{price_data_r}', fmt=YEN)
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
        C(ws, R, 3, '52W Range')
        C(ws, R, SC, f'{lo52:.0f} - {hi52:.0f}')
        R += 1

    # ═══════════════ §7 Scenario Summary ═══════════════
    R += 2
    C(ws, R, 1, 'Scenario Summary', font=bf12)
    R += 1
    syl = YR[2 + s_off].replace('A', 'E')
    C(ws, R, DS, f'{syl} Rev', font=bf)
    C(ws, R, DS + 1, f'{syl} GP', font=bf)
    C(ws, R, DS + 2, f'{syl} NI', font=bf)
    C(ws, R, DS + 3, 'Implied PE', font=bf)
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
    # C-column labels that should be bold (key financial line items)
    BOLD_C = {
        'Revenue', 'Cost', 'GP', 'GM',
        'Total Revenue', 'Rev YoY', 'Total GP', 'Blended GM',
        'Opex', 'Operating Profit', 'OPM',
        'Tax', 'Net Income', 'NPM', 'NI YoY',
        'MCap', 'Shares (M)', 'Price',
        'SOTP Logic / MCap', 'SOTP Seg / MCap',
        'SOTP Logic / Share', 'SOTP Seg / Share',
        'Current Price', 'TTM PE', 'Fwd PE', '52W Range',
    }
    for row in range(1, R):
        for c in range(DS, LC + 1):
            cl = ws.cell(row=row, column=c)
            if cl.value and isinstance(cl.value, str) and cl.value.startswith('='):
                cl.font = nf
            # Ensure bare numeric cells have comma format
            if isinstance(cl.value, (int, float)) and cl.number_format == 'General':
                cl.number_format = CN1 if cl.value != int(cl.value) else NUM
        cv = ws.cell(row=row, column=3).value
        if cv and isinstance(cv, str) and cv in BOLD_C:
            ws.cell(row=row, column=3).font = bf
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
