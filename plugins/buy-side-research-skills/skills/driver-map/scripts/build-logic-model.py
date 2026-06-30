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
            # ── Unit scale check: Vol×ASP/scale must ≈ anchor revenue ──
            vol_fy0 = ll['volume']['fy0']
            scale = ll.get('unit_scale', 100)
            asp_fy0 = ll['tiers'][0].get('asp_fy0', ll['tiers'][0].get('asp', [0])[0] if ll['tiers'][0].get('asp') else 0)
            computed = vol_fy0 * asp_fy0 / scale  # in display units
            # Compute div for anchor conversion (same logic as main build)
            _meta = cfg.get('meta', {})
            _use_B = _meta.get('unit') == 'B' or _meta.get('market', '') in ('jp', 'kr', 'tw')
            _div = 1000 if _use_B else 1
            # Find anchor revenue (seg rev × split), also in display units
            anchor = 0
            for seg in cfg.get('segments', []):
                for l in seg.get('logic_lines', []):
                    if l['name'] == ln:
                        anchor = seg['fy0']['rev'] * l['split'] / _div
                        break
            if anchor > 0:
                gap = abs(computed - anchor) / anchor
                if gap > 0.10:
                    print(f'  [!!] UNIT SCALE: {ln} Vol({vol_fy0})xASP({asp_fy0})/scale({scale})={computed:.0f} vs anchor={anchor:.0f} gap={gap:.1%} -- fix unit_scale or Vol/ASP!')

    # ── Provenance: warn on fields without source tracking ──
    _PROVENANCE_OK = {'edgartools:', 'edinet:', 'yfinance:', 'calculated:', 'disclosed:',
                      'akshare:', 'dart-fss:', 'openesef:', 'finmind:', 'eastmoney:',
                      'longbridge:', 'websearch:', 'webfetch:', 'curl:', 'manual:'}
    _CRITICAL_FIELDS = ['rev', 'gp', 'op', 'ni', 'tax', 'da', 'opex', 'cost',
                        'ebit', 'ebitda', 'pretax', 'nci', 'sbc', 'eps',
                        'gaap_op', 'nongaap_op', 'gaap_ni', 'nongaap_ni']
    est_count = 0
    for fy_key in ['fy-2', 'fy-1', 'fy0']:
        fy = a.get(fy_key, {})
        for field in _CRITICAL_FIELDS:
            src = fy.get('_src', '')
            is_ok = any(src.startswith(p) for p in _PROVENANCE_OK)
            if not is_ok and field in fy:
                print(f'  [provenance] actuals.{fy_key}.{field}: no _src')
                est_count += 1
    for field in ['da', 'opex', 'tax']:
        vals = [a.get(fk, {}).get(field) for fk in ['fy-2', 'fy-1', 'fy0']]
        if vals[0] == vals[1] == vals[2] and vals[0] is not None and vals[0] > 0:
            print(f'  [warn] actuals.{field}: identical 3y ({vals[0]}) — verify not copy-paste')
    if est_count:
        print(f'  [provenance] {est_count} fields without source — review needed')

    print(f'  Validated: depth={depth}, {len(cfg.get("logic_lines",[]))} logic lines, {len(cfg.get("segments",[]))} segments')


# ═══════════════════════════════════════════════════════════════
# Main build function
# ═══════════════════════════════════════════════════════════════

def build(json_path, output_path=None):
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    validate_json(cfg)

    # ── Pre-process: auto-scale Q actuals to match FY annual (complete 4Q FYs) ──
    meta_tmp = cfg['meta']
    q_actual_n = meta_tmp.get('q_actual_count', 0)
    if q_actual_n > 0:
        a = cfg['actuals']; bfyr = meta_tmp['base_fy']; proj_n = meta_tmp['proj_years']
        q_start_yr = meta_tmp.get('q_start_yr', bfyr)
        q_start_q = meta_tmp.get('q_start_q', 1)
        cur_yr, cur_q, qi = q_start_yr, q_start_q, 0
        total_q = q_actual_n + meta_tmp.get('q_proj_count', 0)
        while qi < total_q:
            rem = 4 - cur_q + 1; fyc = min(rem, total_q - qi)
            if fyc == 4:  # complete 4Q FY
                fy_idx = cur_yr - bfyr + 2
                fy_rev = 0
                if fy_idx < 3:
                    fy_rev = a[['fy-2','fy-1','fy0'][fy_idx]]['rev']
                elif fy_idx < 3 + proj_n:
                    proj_i = fy_idx - 3
                    for ll in cfg.get('logic_lines', []):
                        if ll.get('module') == 'vol_asp':
                            vp = ll['volume']['proj']; ap = ll['tiers'][0].get('asp', ll['tiers'][0].get('asp_base',[0]))
                            if proj_i < len(vp):
                                asp = ap[min(proj_i,len(ap)-1)]
                                fy_rev += vp[proj_i] * asp / ll.get('unit_scale',100)
                        else:
                            base = ll['yoy']['base']
                            for seg in cfg.get('segments',[]):
                                for l in seg.get('logic_lines',[]):
                                    if l['name'] == ll['name']:
                                        f0 = seg['fy0']['rev'] * l['split']
                                        cum = 1.0
                                        for bi in range(proj_i+1):
                                            if bi < len(base): cum *= (1+base[bi])
                                        fy_rev += round(f0*cum)
                if fy_rev == 0: qi += fyc; cur_yr += 1; cur_q = 1; continue
                qdata = cfg.get('quarters',{})
                # Guard: only reconcile if ALL 4 Qs have actual data (skip mixed actual+proj FYs)
                all_q_present = all(qdata.get(f'q{qi+j+1}',{}).get('rev',0) > 0 for j in range(4))
                if not all_q_present: qi += fyc; cur_yr += 1; cur_q = 1; continue
                q_rev_sum = sum(qdata.get(f'q{qi+j+1}',{}).get('rev',0) for j in range(4))
                if q_rev_sum > 0 and abs(q_rev_sum/fy_rev-1) > 0.005:
                    s = fy_rev / q_rev_sum
                    print(f'  [reconcile] FY{cur_yr}: Q sum={q_rev_sum:.0f} FY={fy_rev:.0f} scale={s:.3f}')
                    for field in ['rev','gp','op','ni','opex','tax','da']:
                        for j in range(4):
                            qk=f'q{qi+j+1}'; qd=qdata.get(qk,{})
                            if field in qd: qdata[qk][field]=round(qd[field]*s)
                    for seg in cfg.get('segments',[]):
                        sq=seg.get('quarters',{})
                        for field in ['rev','gp','op','ni','opex','tax','da']:
                            for j in range(4):
                                qk=f'q{qi+j+1}'; qd=sq.get(qk,{})
                                if field in qd: sq[qk][field]=round(qd[field]*s)
                    for ll in cfg.get('logic_lines',[]):
                        qh=ll.get('q_history',{})
                        for j in range(4):
                            qk=f'q{qi+j+1}'; qd=qh.get(qk,{})
                            if 'rev' in qd: qh[qk]['rev']=round(qd['rev']*s)
                            if 'volume' in qd and 'asp' in qd and qd.get('asp',0)>0:
                                qh[qk]['volume']=round(qh[qk]['rev']*ll.get('unit_scale',100)/qd['asp'])
            qi += fyc; cur_yr += 1; cur_q = 1

        # ── Company Q → Segment Q split (when company has Q data but seg doesn't) ──
        cq = cfg.get('quarters', {})
        segs = cfg.get('segments', [])
        for qk, qd in cq.items():
            if not qd.get('rev'): continue
            q_rev = qd['rev']; q_gp = qd.get('gp', 0); q_op = qd.get('op')
            # Check if ANY segment has Q data for this qk
            any_seg_has = any(s.get('quarters', {}).get(qk, {}).get('rev', 0) > 0 for s in segs)
            if any_seg_has: continue
            # Split by FY0 proportions
            fy0_tot_rev = sum(s['fy0']['rev'] for s in segs)
            fy0_tot_gp = sum(s['fy0']['gp'] for s in segs)
            if fy0_tot_rev <= 0: continue
            for s in segs:
                sq = s.get('quarters', {})
                w_rev = s['fy0']['rev'] / fy0_tot_rev
                w_gp = s['fy0']['gp'] / fy0_tot_gp if fy0_tot_gp else w_rev
                sq[qk] = sq.get(qk, {})
                sq[qk]['rev'] = round(q_rev * w_rev)
                if q_gp: sq[qk]['gp'] = round(q_gp * w_gp)
                if q_op is not None:
                    tot_op = sum(s2['fy0'].get('op', 0) for s2 in segs)
                    if tot_op: sq[qk]['op'] = round(q_op * s['fy0'].get('op', 0) / tot_op)
                q_opex = qd.get('opex', 0)
                if q_opex:
                    # Derive seg FY0 opex = gp - op
                    fy0_seg_opex = {s2['name']: s2['fy0'].get('gp',0) - s2['fy0'].get('op',0) for s2 in segs}
                    tot_seg_opex = sum(v for v in fy0_seg_opex.values())
                    if tot_seg_opex > 0:
                        sq[qk]['opex'] = round(q_opex * fy0_seg_opex.get(s['name'], 0) / tot_seg_opex)
                s['quarters'] = sq
            # Also write to per-line q_history for 1:1 lines
            for ll in cfg.get('logic_lines', []):
                qh = ll.get('q_history', {})
                if qh.get(qk, {}).get('rev'): continue  # already has data
                for s in segs:
                    for l in s.get('logic_lines', []):
                        if l['name'] == ll['name']:
                            sq = s['quarters']
                            if qk in sq:
                                qh[qk] = qh.get(qk, {})
                                qh[qk]['rev'] = round(sq[qk]['rev'] * l['split'])
                                if sq[qk].get('gp'):
                                    qh[qk]['gp'] = round(sq[qk]['gp'] * l['split'])
                            break

        # ── Blend: actual Q profit rates → update annual model assumptions ──
        # For projection FYs with M∈{1,2,3}, blend actual Q margins with model
        gl = cfg.get('global', {})
        cur_yr, cur_q, qi_b = q_start_yr, q_start_q, 0
        while qi_b < total_q:
            rem = 4 - cur_q + 1; fyc = min(rem, total_q - qi_b)
            if fyc == 4:
                fy_idx = cur_yr - bfyr + 2; proj_i = fy_idx - 3
                if 0 <= proj_i < proj_n:
                    for seg in cfg.get('segments', []):
                        sq = seg.get('quarters', {})
                        # Count actual Qs for this segment in this FY
                        seg_q_revs = []; seg_q_gps = []; seg_q_ops = []
                        for j in range(4):
                            qk = f'q{qi_b+j+1}'; qd = sq.get(qk, {})
                            rv = qd.get('rev', 0); gv = qd.get('gp', 0)
                            if rv and rv > 0:
                                seg_q_revs.append(rv)
                                if gv: seg_q_gps.append(gv)
                                ov = qd.get('op')
                                if ov is not None: seg_q_ops.append(ov)
                        M_seg = len(seg_q_revs)
                        if M_seg not in (1, 2, 3): continue
                        w_act = M_seg / 4; w_mod = 1 - w_act

                        # Blend per-line gm + opex_rate for each logic line in this segment
                        for ll_cfg in seg.get('logic_lines', []):
                            ln_name = ll_cfg['name']
                            ll_obj = None
                            for ll in cfg.get('logic_lines', []):
                                if ll['name'] == ln_name: ll_obj = ll; break
                            if not ll_obj: continue

                            # GM blend
                            if seg_q_gps and sum(seg_q_revs) > 0:
                                gm_actual = sum(seg_q_gps) / sum(seg_q_revs)
                                gm_model = ll_obj['gm']['proj'][proj_i] if proj_i < len(ll_obj['gm']['proj']) else 0
                                gm_blend = w_act * gm_actual + w_mod * gm_model
                                ll_obj['gm']['proj'][proj_i] = round(gm_blend, 4)

                            # Opex/Rev blend (requires OP data)
                            if seg_q_ops and seg_q_gps and sum(seg_q_revs) > 0:
                                opex_actual = sum(seg_q_gps) - sum(seg_q_ops)
                                om_actual = opex_actual / sum(seg_q_revs) if sum(seg_q_revs) > 0 else 0
                                line_opex = ll_obj.get('opex_rate')
                                opex_arr = line_opex if line_opex else gl.get('opex_rate', [])
                                idx_o = 3 + proj_i
                                om_model = opex_arr[idx_o] if idx_o < len(opex_arr) else 0.25
                                om_blend = w_act * om_actual + w_mod * om_model
                                if idx_o < len(opex_arr):
                                    if line_opex: ll_obj['opex_rate'][idx_o] = round(om_blend, 4)
                                    else: gl['opex_rate'][idx_o] = round(om_blend, 4)
                    # Blend global opex_rate (company-level, from all segments' actual Qs)
                    if M_seg > 0:
                        all_act_rev = 0; all_act_gp = 0; all_act_op = 0
                        for seg in cfg.get('segments', []):
                            sq = seg.get('quarters', {})
                            for j in range(4):
                                qk = f'q{qi_b+j+1}'; qd = sq.get(qk, {})
                                rv = qd.get('rev', 0)
                                if rv and rv > 0:
                                    all_act_rev += rv
                                    gv = qd.get('gp', 0)
                                    if gv: all_act_gp += gv
                                    ov = qd.get('op')
                                    if ov is not None: all_act_op += ov
                        if all_act_rev > 0 and all_act_gp > 0 and all_act_op > 0:
                            co_om_act = (all_act_gp - all_act_op) / all_act_rev
                            co_om_mod = gl['opex_rate'][3 + proj_i] if 3 + proj_i < len(gl['opex_rate']) else 0.25
                            co_blend = (M_seg / 4) * co_om_act + (1 - M_seg / 4) * co_om_mod
                            idx_g = 3 + proj_i
                            if idx_g < len(gl['opex_rate']):
                                gl['opex_rate'][idx_g] = round(co_blend, 4)
            qi_b += fyc; cur_yr += 1; cur_q = 1

        # ── Q Driver Distribution ──
        # For each complete 4Q FY, distribute annual drivers to Qs using seasonal weights.
        # vol_asp: Q_Vol = Vol_Y × w_i, Q_ASP = ASP_Y × s_i (Σ(w×s)=1)
        # yoy: Newton solve r s.t. Σ Q_1×(1+r)^k = Annual
        # backlog_burn: Q_Burn = Burn_Y × w_i, Q_ASP = ASP_Y × s_i
        cur_yr, cur_q, qi = q_start_yr, q_start_q, 0
        while qi < total_q:
            rem = 4 - cur_q + 1; fyc = min(rem, total_q - qi)
            if fyc == 4:
                fy_idx = cur_yr - bfyr + 2; proj_i = fy_idx - 3
                for ll in cfg.get('logic_lines', []):
                    ln = ll['name']; qh = ll.get('q_history', {})
                    module = ll.get('module', 'yoy')
                    us = ll.get('unit_scale', 100)

                    # ── Compute annual revenue & drivers ──
                    ann = 0; ann_vol = 0; ann_asp = 0
                    if fy_idx < 3:
                        for seg in cfg.get('segments', []):
                            for l in seg.get('logic_lines', []):
                                if l['name'] == ln:
                                    seg_fy_key = ['fy-2', 'fy-1', 'fy0'][fy_idx]
                                    yr_data = seg.get(seg_fy_key, {})
                                    if yr_data and yr_data.get('rev'):
                                        ann += yr_data['rev'] * l['split']
                    elif 0 <= proj_i < proj_n:
                        if module == 'vol_asp':
                            vp = ll['volume']['proj']; ap = ll['tiers'][0].get('asp', ll['tiers'][0].get('asp_base', [0]))
                            if proj_i < len(vp):
                                ann_asp = ap[min(proj_i, len(ap) - 1)]
                                ann_vol = vp[proj_i]
                                ann = ann_vol * ann_asp  # raw product, unit_scale applied at formula level
                        elif module == 'backlog_burn':
                            bp = ll['backlog']['burn']['proj']; ap_arr = ll.get('asp', [])
                            ann_asp = ap_arr[min(proj_i, len(ap_arr) - 1)] if ap_arr else 0
                            ann_vol = bp[proj_i]  # burn = "volume" in this context
                            ann = ann_vol * ann_asp if ann_asp else 0  # raw product
                        else:  # yoy
                            base = ll['yoy']['base']
                            for seg in cfg.get('segments', []):
                                for l in seg.get('logic_lines', []):
                                    if l['name'] == ln:
                                        f0 = seg['fy0']['rev'] * l['split']
                                        cum = 1.0
                                        for bi in range(proj_i + 1):
                                            if bi < len(base): cum *= (1 + base[bi])
                                        ann += round(f0 * cum)
                    if ann <= 0: continue

                    # ── Count M and read actual Q driver data ──
                    actual_q = []  # list of (offset, rev, vol, asp) for Qs with data
                    for j in range(4):
                        qk = f'q{qi+j+1}'; qd = qh.get(qk, {})
                        rv = qd.get('rev', 0)
                        # Fallback: segment quarters
                        if not rv:
                            for seg in cfg.get('segments', []):
                                for l in seg.get('logic_lines', []):
                                    if l['name'] == ln:
                                        sq_r = seg.get('quarters', {}).get(qk, {}).get('rev', 0)
                                        if sq_r:
                                            rv = sq_r * l['split']
                        if rv and rv > 0:
                            vv = qd.get('volume', 0) or (rv / ann_asp if ann_asp else 0)
                            av = qd.get('asp', 0) or ann_asp
                            actual_q.append((j, rv, vv, av))
                    M = len(actual_q)
                    if M == 4: continue  # all-actual FY, reconcile handled

                    # ── Compute QoQ rate r ──
                    if M >= 2:
                        qoq_rates = []
                        for mi in range(1, len(actual_q)):
                            r_prev = actual_q[mi - 1][1]; r_curr = actual_q[mi][1]
                            if r_prev > 0: qoq_rates.append(r_curr / r_prev - 1)
                        _r = sum(qoq_rates) / len(qoq_rates) if qoq_rates else 0.02
                    else:
                        _yoy = 0
                        if fy_idx < 3:
                            fy_a = ['fy-2', 'fy-1', 'fy0']
                            if fy_idx > 0:
                                _yoy = a[fy_a[fy_idx]]['rev'] / a[fy_a[fy_idx - 1]]['rev'] - 1
                        elif module == 'yoy':
                            _yoy = ll['yoy']['base'][proj_i] if proj_i < len(ll['yoy']['base']) else 0
                        elif module in ('vol_asp', 'backlog_burn'):
                            _src = ll.get('volume', ll.get('backlog', {}).get('burn', {}))
                            vp = _src.get('proj', [])
                            if proj_i > 0 and proj_i - 1 < len(vp) and vp[proj_i - 1] > 0:
                                _yoy = vp[proj_i] / vp[proj_i - 1] - 1
                        _r = (1 + _yoy) ** (1 / 4) - 1 if _yoy > -0.99 else 0.02
                    _r = max(-0.2, min(0.2, _r))  # cap for vol_asp/backlog weights only

                    # ── Compute seasonal weights ──
                    actual_set = set(a[0] for a in actual_q)
                    first_actual = actual_q[0][0] if actual_q else 0
                    last_actual = actual_q[-1][0] if actual_q else -1

                    if module == 'yoy':
                        # ── yoy: binary search for r such that Σ Q_i = ann ──
                        a_first = actual_q[0][1] if actual_q else ann / 4
                        a_last = actual_q[-1][1] if actual_q else ann / 4
                        def yoy_sum(_r):
                            s = 0
                            for j in range(4):
                                if j in actual_set:
                                    for a in actual_q:
                                        if a[0] == j: s += a[1]
                                elif j < first_actual:
                                    s += a_first / ((1 + _r) ** (first_actual - j))
                                else:  # j > last_actual
                                    s += a_last * ((1 + _r) ** (j - last_actual))
                            return s
                        lo, hi = -0.5, 1.0
                        for _ in range(30):
                            mid = (lo + hi) / 2
                            s = yoy_sum(mid)
                            if abs(s - ann) < 0.5:
                                r_q = mid; break
                            if s > ann: hi = mid
                            else: lo = mid
                        else:
                            r_q = mid
                        r_q = max(-0.5, min(1.0, r_q))

                        # Write YoY_Q rates to q_history
                        for j in range(4):
                            qk = f'q{qi+j+1}'
                            if j in actual_set: continue
                            qh[qk] = qh.get(qk, {})
                            qh[qk]['yoy_q'] = round(r_q, 6)

                        # Compute Q Rev targets for debug
                        q_revs = []
                        for j in range(4):
                            if j in actual_set:
                                for a in actual_q:
                                    if a[0] == j: q_revs.append(a[1])
                            elif j < first_actual:
                                q_revs.append(a_first / ((1 + r_q) ** (first_actual - j)))
                            else:
                                q_revs.append(a_last * ((1 + r_q) ** (j - last_actual)))
                        print(f'  [Q driver] {ln} FY{cur_yr} M={M} (yoy): r={r_q:.4f} Q revs={[round(x) for x in q_revs]} sum={round(sum(q_revs))} ann={round(ann)}')

                    elif module in ('vol_asp', 'backlog_burn'):
                        # ── vol_asp / backlog_burn: Vol/Burn + ASP weights ──
                        # Locked actual Qs consume part of annual Vol and Rev budget
                        locked_vol = sum(a[2] for a in actual_q)
                        locked_rev = sum(a[1] for a in actual_q)
                        remaining_vol = max(0.01, ann_vol - locked_vol)
                        remaining_rev = max(0.01, ann - locked_rev)
                        remaining_asp = remaining_rev / remaining_vol  # target ASP for proj Qs

                        # Compute Vol/Burn weights from actual Q data
                        if M >= 2 and len([a for a in actual_q if a[2] > 0]) >= 2:
                            vol_actuals = [a for a in actual_q if a[2] > 0]
                            vol_sum = sum(a[2] for a in vol_actuals)
                            w_actual = {a[0]: a[2] / vol_sum for a in vol_actuals}
                        else:
                            w_actual = {}

                        # Compute ASP seasonal s_i_raw from actual Q data
                        if M >= 2 and len([a for a in actual_q if a[3] > 0]) >= 2:
                            asp_actuals = [a for a in actual_q if a[3] > 0]
                            s_raw_vals = {a[0]: a[3] / ann_asp for a in asp_actuals} if ann_asp else {}
                        else:
                            s_raw_vals = {}

                        # Build w and s for projection Qs only
                        n_proj = 4 - M
                        w = [0.0] * 4; s = [1.0] * 4
                        proj_indices = [j for j in range(4) if j not in actual_set]
                        for j in proj_indices:
                            if j in w_actual:
                                w[j] = w_actual[j]
                                s[j] = s_raw_vals.get(j, 1.0)
                            elif j < first_actual:
                                steps = first_actual - j
                                w[j] = w_actual.get(first_actual, 1.0/n_proj) / ((1 + _r) ** steps)
                                s[j] = s_raw_vals.get(first_actual, 1.0)
                            elif j > last_actual:
                                steps = j - last_actual
                                w[j] = w_actual.get(last_actual, 1.0/n_proj) * ((1 + _r) ** steps)
                                s[j] = s_raw_vals.get(last_actual, 1.0)
                            else:
                                # M=0: uniform with r growth
                                w[j] = (1.0 / n_proj) * ((1 + _r) ** (j + 1))
                                s[j] = 1.0

                        # Normalize w for projection Qs to sum to 1
                        w_proj_sum = sum(w[j] for j in proj_indices)
                        if w_proj_sum > 0:
                            for j in proj_indices:
                                w[j] /= w_proj_sum

                        # Normalize s for projection Qs so Σ(w × s) = 1
                        inner = sum(w[j] * s[j] for j in proj_indices)
                        if inner > 0:
                            for j in proj_indices:
                                s[j] /= inner

                        # Write q_history
                        for j in range(4):
                            qk = f'q{qi+j+1}'
                            qh[qk] = qh.get(qk, {})
                            if j in actual_set:
                                # Lock actual Qs: preserve Vol, set ASP so Vol×ASP=actual Rev
                                for a in actual_q:
                                    if a[0] == j:
                                        qh[qk]['rev'] = a[1]
                                        if a[2] > 0 and a[1] > 0 and module == 'vol_asp':
                                            qh[qk]['volume'] = a[2]
                                            qh[qk]['asp'] = a[1] / a[2]  # raw ASP, formula divides by unit_scale
                                continue
                            if module == 'vol_asp':
                                qh[qk]['volume'] = remaining_vol * w[j]
                                qh[qk]['asp'] = remaining_asp * s[j]
                            else:  # backlog_burn
                                qh[qk]['burn'] = remaining_vol * w[j]  # remaining_vol = Burn_budget
                                qh[qk]['asp'] = remaining_asp * s[j]
                                order_yr = ll['backlog']['order']['proj'][proj_i] if proj_i < len(ll['backlog']['order']['proj']) else 0
                                qh[qk]['order'] = order_yr * w[j]

                        # Debug output
                        _revs = []
                        for j in range(4):
                            if j in actual_set:
                                for a in actual_q:
                                    if a[0] == j: _revs.append(a[1])
                            else:
                                _revs.append(remaining_vol * w[j] * remaining_asp * s[j] / us)
                        print(f'  [Q driver] {ln} FY{cur_yr} M={M} ({module}): '
                              f'w={[round(w[j],3) if j in proj_indices else 0 for j in range(4)]} '
                              f's={[round(s[j],3) if j in proj_indices else 0 for j in range(4)]} '
                              f'revs={[round(x) for x in _revs]} sum={round(sum(_revs))} ann={round(ann)}')

            qi += fyc; cur_yr += 1; cur_q = 1

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
    q_actual_n = meta.get('q_actual_count', 0)
    q_proj_n = meta.get('q_proj_count', 0)
    has_q = q_actual_n + q_proj_n > 0
    COLS = 3 + proj_n
    FY0 = DS + 2; SC = FY0 + s_off; LC_ANNUAL = DS + COLS - 1
    if has_q:
        Q_START = LC_ANNUAL + 3  # 2 blank columns between Y and Q
        Q_END = Q_START + q_actual_n + q_proj_n - 1
        LC = Q_END
        # Q labels: 4Q25A, 1Q26A, 2Q26E, 3Q26E, ...
        q_start_yr = meta.get('q_start_yr', bfyr)
        q_start_q = meta.get('q_start_q', 1)
        yr, q = q_start_yr, q_start_q
        QL = []
        for i in range(q_actual_n):
            QL.append(f'{q}Q{str(yr)[-2:]}A')
            q += 1
            if q > 4: q = 1; yr += 1
        for i in range(q_proj_n):
            QL.append(f'{q}Q{str(yr)[-2:]}E')
            q += 1
            if q > 4: q = 1; yr += 1
    else:
        Q_START = Q_END = 0
        LC = LC_ANNUAL
        QL = []
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
    for ci, ql in enumerate(QL, Q_START):
        C(ws, 1, ci, ql, font=bf)
    unit_label = 'bn' if use_B else 'millions'
    C(ws, 1, 3, f'({meta.get("currency","CNY")} {unit_label})', font=itf)

    # module context (modules see annual range only)
    ctx = make_ctx()
    ctx['FY0'] = FY0; ctx['LC'] = LC_ANNUAL; ctx['SC'] = SC; ctx['proj_n'] = proj_n
    ctx['COLS'] = COLS; ctx['bfyr'] = bfyr
    ctx['Q_START'] = Q_START; ctx['Q_END'] = Q_END
    ctx['q_actual_n'] = q_actual_n; ctx['q_proj_n'] = q_proj_n

    print(f'  Cols: D=DS({DS}) FY0={get_column_letter(FY0)}({FY0}) '
          f'LC={get_column_letter(LC_ANNUAL)}({LC_ANNUAL}) SC={get_column_letter(SC)}({SC}) '
          f'proj_n={proj_n} B_mode={use_B} div={div}'
          + (f' Q={get_column_letter(Q_START)}({Q_START})-{get_column_letter(Q_END)}({Q_END})' if has_q else ''))

    # ═══════════════ §1 Reported Segments ═══════════════
    R = 3
    C(ws, R, 1, 'Reported Segments', font=bf12)
    s1_start = R
    R += 1
    C(ws, R, 1, '(Segments)', font=itf)
    # Basis label (below Reported Segments, same as Logic Lines)
    basis = meta.get('basis', 'gaap')
    basis_note = meta.get('basis_note', '')
    basis_label = f'Basis: {basis.upper()}'
    if basis_note:
        basis_label += f' — {basis_note[:120]}'
    C(ws, R, 1, basis_label, font=itf)
    R = 6
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
        # Q columns: segment Q actuals
        seg_quarters = seg.get('quarters', {})
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'; qd = seg_quarters.get(qk, {})
            if qd.get('rev'): A(ws, R, Q_START + qi, sc(qd['rev']), fmt=NUM)
        for qi in range(q_proj_n):
            C(ws, R, Q_START + q_actual_n + qi, '', fmt=NUM)
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

        # Implied YoY (annual) + QoQ (quarterly)
        for yr_key, col in hist_years:
            C(ws, R, col, '', fmt=PCT)
        cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
        C(ws, R, DS + 1, f'=IFERROR({cl_e}{rev_r}/{cl_d}{rev_r}-1,"")', fmt=PCT)
        f0 = get_column_letter(FY0); f_1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({f0}{rev_r}/{f_1}{rev_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
        # Q columns: YoY (vs same Q 4 quarters ago)
        if has_q:
            for qi in range(Q_START, Q_START + q_actual_n + q_proj_n):
                cl = get_column_letter(qi)
                if qi - 4 >= Q_START:
                    pl = get_column_letter(qi - 4)
                    C(ws, R, qi, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
                else:
                    C(ws, R, qi, '', fmt=PCT)
        C(ws, R, 3, 'Implied YoY')
        R += 1
        # QoQ row (collapsed, Q columns only)
        if has_q:
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  QoQ', font=itf)
            R += 1

        # Cost
        for yr_key, col in hist_years:
            yr = seg.get(yr_key)
            if yr: A(ws, R, col, sc(yr['cost']), fmt=NUM)
            else: C(ws, R, col, '', fmt=NUM)
        A(ws, R, FY0, sc(scost), fmt=NUM)
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'; qd = seg_quarters.get(qk, {})
            _cost = qd.get('cost')
            if not _cost and qd.get('rev') and qd.get('gp'):
                _cost = qd['rev'] - qd['gp']
            if _cost: A(ws, R, Q_START + qi, sc(_cost), fmt=NUM)
        for qi in range(q_proj_n):
            C(ws, R, Q_START + q_actual_n + qi, '', fmt=NUM)
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
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'; qd = seg_quarters.get(qk, {})
            if qd.get('gp'): A(ws, R, Q_START + qi, sc(qd['gp']), fmt=NUM)
        for qi in range(q_proj_n):
            C(ws, R, Q_START + q_actual_n + qi, '', fmt=NUM)
        gp_r = R
        C(ws, R, 3, 'GP')
        R += 1
        # GP YoY
        C(ws, R, DS, '', fmt=PCT)
        _cle = get_column_letter(DS + 1); _cld = get_column_letter(DS)
        C(ws, R, DS + 1, f'=IFERROR({_cle}{gp_r}/{_cld}{gp_r}-1,"")', fmt=PCT)
        _cf0 = get_column_letter(FY0); _cf1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({_cf0}{gp_r}/{_cf1}{gp_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
        C(ws, R, 3, 'GP YoY')
        R += 1
        # GP QoQ
        if has_q:
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  GP QoQ', font=itf)
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
            for qi in range(q_actual_n):
                qk = f'q{qi+1}'; qd = seg_quarters.get(qk, {})
                _op = qd.get('op')
                if not _op and qd.get('gp') and qd.get('rev'):
                    _op_rate = gl.get('opex_rate', [0.25]*8)[2]  # FY0 rate
                    _op = round(qd['gp'] - qd['rev'] * _op_rate)
                if _op is not None: A(ws, R, Q_START + qi, sc(_op), fmt=NUM)
            for qi in range(q_proj_n):
                C(ws, R, Q_START + q_actual_n + qi, '', fmt=NUM)
            op_r = R
            C(ws, R, 3, 'OP')
            R += 1
            # OP YoY
            for yr_key, col in hist_years:
                C(ws, R, col, '', fmt=PCT)
            CF(ws, R, DS + 1, f'=IFERROR({get_column_letter(DS+1)}{op_r}/{get_column_letter(DS)}{op_r}-1,"")', fmt=PCT)
            CF(ws, R, FY0, f'=IFERROR({get_column_letter(FY0)}{op_r}/{get_column_letter(FY0-1)}{op_r}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{op_r}/{pl}{op_r}-1,"")', fmt=PCT)
            # Q YoY (vs 4Q back)
            if has_q:
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi)
                    if qi - 4 >= Q_START:
                        pl = get_column_letter(qi - 4)
                        C(ws, R, qi, f'=IFERROR({cl}{op_r}/{pl}{op_r}-1,"")', fmt=PCT)
                    else:
                        C(ws, R, qi, '', fmt=PCT)
            C(ws, R, 3, 'OP YoY')
            R += 1
            # OP QoQ (collapsed, Q columns only)
            if has_q:
                for ci in range(DS, LC_ANNUAL + 1):
                    C(ws, R, ci, '', fmt=PCT)
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                    if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                    else: C(ws, R, qi, f'=IFERROR({cl}{op_r}/{pl}{op_r}-1,"")', fmt=PCT)
                C(ws, R, 3, '  OP QoQ', font=itf)
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
        # Q GM formula
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                CF(ws, gm_r, qi, f'=IFERROR({cl}{gp_r}/{cl}{rev_r},"")', fmt=PCT)

        srows = []; lrevs = {}
        for l in lls:
            ln = l['name']; sp = l['split']
            # Split% — same value across all historical years + FY0 + Q
            for col in (DS, DS + 1, FY0):
                I(ws, R, col, sp, fmt=PCT)
            if has_q:
                for qi in range(Q_START, Q_END + 1):
                    I(ws, R, qi, sp, fmt=PCT)
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
            if has_q:
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi)
                    CF(ws, R, qi, f'={cl}{rev_r}*{cl}{split_row}', fmt=NUM)
            lrevs[ln] = R; R += 1

        if srows:
            for col in (DS, DS + 1, FY0):
                cl = get_column_letter(col)
                refs = '+'.join([f'{cl}{sr}' for sr in srows])
                CF(ws, R, col, f'=1-({refs})', fmt=PCT)
            if has_q:
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi)
                    refs = '+'.join([f'{cl}{sr}' for sr in srows])
                    CF(ws, R, qi, f'=1-({refs})', fmt=PCT)
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
    # Basis label (below Logic Lines header)
    basis = meta.get('basis', 'gaap')
    basis_note = meta.get('basis_note', '')
    basis_label = f'Basis: {basis.upper()}'
    if basis_note:
        basis_label += f' — {basis_note[:120]}'
    C(ws, R, 1, basis_label, font=itf)
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
        s1_op_row = si.get('op', 0)
        split_r = line_to_split.get(ln, 0)
        lrev_row = si.get('lrev_rows', {}).get(ln, 0)
        seg_obj = None
        for s in segments:
            if s['name'] == seg_name:
                seg_obj = s
                break

        # ── yoy module: QoQ below YoY row ──
        if has_q and module_name == 'yoy' and result.get('ya'):
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{result["rev_r"]}/{pl}{result["rev_r"]}-1,"")', fmt=PCT)
            C(ws, R, 3, '  QoQ', font=itf)
            R += 1

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
        # GP YoY
        C(ws, R, DS, '', fmt=PCT)
        _cl2e = get_column_letter(DS + 1); _cl2d = get_column_letter(DS)
        C(ws, R, DS + 1, f'=IFERROR({_cl2e}{gp_r}/{_cl2d}{gp_r}-1,"")', fmt=PCT)
        _cf2_0 = get_column_letter(FY0); _cf2_1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({_cf2_0}{gp_r}/{_cf2_1}{gp_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
        C(ws, R, 3, 'GP YoY')
        R += 1
        # GP QoQ
        if has_q:
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  GP QoQ', font=itf)
            R += 1

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
            # Opex rate (per-line fallback to global; 1:1 historical uses S1 formula)
            line_opex = ll.get('opex_rate')
            opex_rates = line_opex if line_opex else gl.get('opex_rate', [])
            _ope_r = R
            for yr_i, col in [(0, DS), (1, DS + 1), (2, FY0)]:
                cl = get_column_letter(col)
                # 1:1 actual years: use S1 (GP−OP)/Rev like GM
                if (ln in one_to_one) and s1_gp_row and s1_op_row and s1_rev_row:
                    CF(ws, R, col, f'=IFERROR(({cl}{s1_gp_row}-{cl}{s1_op_row})/{cl}{s1_rev_row},"")', fmt=PCT)
                elif yr_i < len(opex_rates):
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
            # OP YoY
            C(ws, R, DS, '', fmt=PCT)
            _cl3e = get_column_letter(DS + 1); _cl3d = get_column_letter(DS)
            C(ws, R, DS + 1, f'=IFERROR({_cl3e}{line_op_r}/{_cl3d}{line_op_r}-1,"")', fmt=PCT)
            _cf3_0 = get_column_letter(FY0); _cf3_1 = get_column_letter(FY0 - 1)
            C(ws, R, FY0, f'=IFERROR({_cf3_0}{line_op_r}/{_cf3_1}{line_op_r}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{line_op_r}/{pl}{line_op_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  OP YoY')
            R += 1
            # OP QoQ
            if has_q:
                for ci in range(DS, LC_ANNUAL + 1):
                    C(ws, R, ci, '', fmt=PCT)
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                    if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                    else: C(ws, R, qi, f'=IFERROR({cl}{line_op_r}/{pl}{line_op_r}-1,"")', fmt=PCT)
                C(ws, R, 3, '    OP QoQ', font=itf)
                R += 1
            # OPM (1:1 actual years & actual Qs use S1 OP/Rev)
            for ci in range(DS, LC + 1):
                cl = get_column_letter(ci)
                is_actual_q = has_q and Q_START <= ci < Q_START + q_actual_n
                if (ln in one_to_one) and s1_op_row and s1_rev_row and (ci <= FY0 or is_actual_q):
                    C(ws, R, ci, f'=IFERROR({cl}{s1_op_row}/{cl}{s1_rev_row},"")', fmt=PCT)
                else:
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

        # ── Q Columns: mirror Y logic for actual + projection ──
        if has_q:
            q_hist = ll.get('q_history', {})
            rev_module = ll.get('module', 'yoy')
            is_vol_asp = rev_module == 'vol_asp'

            if is_vol_asp:
                # Q Volume row (mirrors annual Volume) — pre-fill from annual or q_history
                vol_fy0 = ll['volume']['fy0']
                for qi in range(q_actual_n + q_proj_n):
                    col = Q_START + qi
                    qv = q_hist.get(f'q{qi+1}', {}).get('volume')  # check all Qs
                    if qv is not None:
                        I(ws, result['vol_r'], col, qv, fmt=INT)
                    elif qi < q_actual_n:
                        I(ws, result['vol_r'], col, round(vol_fy0 / 4), fmt=INT)
                    else:
                        I(ws, result['vol_r'], col,
                          ll.get('q_volume', ll['volume']['proj'])[min(qi - q_actual_n, len(ll['volume']['proj']) - 1)],
                          fmt=INT)
                # Q ASP row (first tier, mirrors annual ASP) — pre-fill from annual or q_history
                asp_r = result.get('asp_rows', [0])[0] if result.get('asp_rows') else 0
                if asp_r:
                    asp_fy0 = ll['tiers'][0].get('asp_fy0') or ll['tiers'][0].get('asp', ll['tiers'][0].get('asp_base', [0]))[0]
                    for qi in range(q_actual_n + q_proj_n):
                        col = Q_START + qi
                        q_asp = q_hist.get(f'q{qi+1}', {}).get('asp')  # check all Qs
                        if q_asp is not None:
                            I(ws, asp_r, col, q_asp, fmt=DEC)
                        elif qi < q_actual_n:
                            I(ws, asp_r, col, asp_fy0, fmt=DEC)
                        else:
                            I(ws, asp_r, col,
                              ll['tiers'][0].get('asp', ll['tiers'][0].get('asp_base', [0]))[min(qi - q_actual_n,
                                len(ll['tiers'][0].get('asp', ll['tiers'][0].get('asp_base', [0]))) - 1)],
                              fmt=DEC)
                # Q Revenue: =Q_Vol × Q_ASP / scale (mirrors annual formula)
                for qi in range(q_actual_n + q_proj_n):
                    col = Q_START + qi; cl = get_column_letter(col)
                    scale = ll.get('unit_scale', 100)
                    if asp_r:
                        CF(ws, result['rev_r'], col, f'=({cl}{result["vol_r"]}*{cl}{asp_r})/{scale}', fmt=NUM)
                    else:
                        CF(ws, result['rev_r'], col, '', fmt=NUM)
            else:
                # yoy: Q Revenue = prior_Q × (1+YoY_Active) for proj, I() for actual
                # Extend YoY Active row to Q columns (scenario-driven)
                ya = result.get('ya', 0)
                if ya and result.get('yb'):
                    for qi in range(q_actual_n + q_proj_n):
                        col = Q_START + qi; cl = get_column_letter(col)
                        CF(ws, ya, col,
                           f'=IF(B1="Bull",{cl}{result["yb"]},IF(B1="Bear",{cl}{result["ybe"]},{cl}{result["ybs"]}))',
                           fmt=PCT)
                for qi in range(q_actual_n + q_proj_n):
                    col = Q_START + qi; cl = get_column_letter(col)
                    is_q_actual = qi < q_actual_n
                    s1r = anchor_info.get(ln, (0, 0))[0]
                    anchor_row = s1r if ln in one_to_one else lrev_row
                    # 1:1 actual Q: use S1 reference like GM/OpexRev (real data)
                    if ln in one_to_one and anchor_row and is_q_actual:
                        C(ws, result['rev_r'], col, f'={cl}{anchor_row}', fmt=NUM)
                    elif is_q_actual:
                        # non-1:1 actual Q: q_history rev or S1 anchor
                        qv = q_hist.get(f'q{qi+1}', {}).get('rev')
                        if qv is not None:
                            I(ws, result['rev_r'], col, sc(qv), fmt=NUM)
                        elif anchor_row:
                            C(ws, result['rev_r'], col, f'={cl}{anchor_row}', fmt=NUM)
                    else:
                        # proj Q: chain formula (never use stale q_history rev)
                        pl = get_column_letter(col - 1)
                        CF(ws, result['rev_r'], col,
                           f'={pl}{result["rev_r"]}*(1+{cl}{ya})', fmt=NUM)
                # Extend BBE rows to Q columns (q_history yoy_q if available, else annual rate → QoQ)
                if result.get('yb'):
                    yoy_keys = [('bull', 'yb'), ('base', 'ybs'), ('bear', 'ybe')]
                    cur_yr, cur_q = q_start_yr, q_start_q
                    for qi in range(q_actual_n + q_proj_n):
                        proj_idx = cur_yr - bfyr - 1
                        qk = f'q{qi+1}'
                        # q_history yoy_q takes priority (per-Q rate from driver distribution)
                        q_yoy = q_hist.get(qk, {}).get('yoy_q')
                        if q_yoy is not None:
                            for arr_key, rk in yoy_keys:
                                I(ws, result[rk], Q_START + qi, q_yoy, fmt=PCT)
                        elif 0 <= proj_idx < proj_n:
                            # Fallback: convert annual rate to QoQ
                            _ann_rate = ll['yoy']['base'][proj_idx] if proj_idx < len(ll['yoy']['base']) else 0
                            _q_rate = (1 + _ann_rate) ** (1 / 4) - 1 if _ann_rate > -0.99 else 0.02
                            for arr_key, rk in yoy_keys:
                                I(ws, result[rk], Q_START + qi, _q_rate, fmt=PCT)
                        cur_q += 1
                        if cur_q > 4: cur_q = 1; cur_yr += 1
            # Q GP/OP cascade (same as annual)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                CF(ws, gp_r, qi, f'=IFERROR({cl}{result["rev_r"]}*{cl}{gm_r},"")', fmt=NUM)
            if line_op_r:
                q_opex_r = line_op_r - 1
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi)
                    CF(ws, line_op_r, qi, f'={cl}{gp_r}-{cl}{q_opex_r}', fmt=NUM)
            # QoQ row (collapsed, Q columns only)
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{result["rev_r"]}/{pl}{result["rev_r"]}-1,"")', fmt=PCT)
            C(ws, R, 3, '  QoQ', font=itf)
            R += 1

        # ── Check rows: extend to Q actual columns (scan C column for positions) ──
        if has_q and q_actual_n > 0:
            for scan_r in range(result['rev_r'], R):
                cv = str(ws.cell(row=scan_r, column=3).value or '')
                if 'Check Rev' in cv and needs_rev_check and lrev_row:
                    for qi in range(q_actual_n):
                        cl = get_column_letter(Q_START + qi)
                        C(ws, scan_r, Q_START + qi, f'={cl}{lrev_row}', fmt=NUM)
                if 'Check GP' in cv and needs_gp_check and hist_gp_ok:
                    for qi in range(q_actual_n):
                        cl = get_column_letter(Q_START + qi)
                        C(ws, scan_r, Q_START + qi, f'={cl}{s1_gp_row}*{cl}{split_r}', fmt=NUM)
                if 'Check OP' in cv and si.get("op", 0) and split_r:
                    for qi in range(q_actual_n):
                        cl = get_column_letter(Q_START + qi)
                        C(ws, scan_r, Q_START + qi, f'={cl}{si["op"]}*{cl}{split_r}', fmt=NUM)

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

        for ci in range(FY0 + 1, LC_ANNUAL + 1):
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

        # Q proj fill (same logic as annual, for Q projection columns)
        if has_q:
            for ci in range(Q_START + q_actual_n, Q_END + 1):
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
                s1_op = si.get('op', 0)
                if s1_op and max_seg_depth >= DEPTH_RANK['op']:
                    op_terms = [f'{cl}{L[ln["name"]]["op_r"]}' for ln in lls if L[ln["name"]].get('op_r')]
                    if op_terms:
                        CF(ws, s1_op, ci, '=' + '+'.join(op_terms), fmt=NUM)

        for ln_name in [l['name'] for l in lls]:
            for sr_row in srows:
                cell_val = ws.cell(row=sr_row, column=3).value
                if cell_val and ln_name in str(cell_val):
                    for ci in range(FY0 + 1, LC_ANNUAL + 1):
                        cl = get_column_letter(ci)
                        CF(ws, sr_row, ci, f'=IFERROR({cl}{L[ln_name]["rev_r"]}/{cl}{s1r},"")', fmt=PCT)
            lr_row = lrevs.get(ln_name, 0)
            if lr_row:
                for ci in range(FY0 + 1, LC_ANNUAL + 1):
                    cl = get_column_letter(ci)
                    CF(ws, lr_row, ci, f'={cl}{L[ln_name]["rev_r"]}', fmt=NUM)
        if res_row and srows:
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
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

    # ── Q Columns: post-Fill GM + opex_rate extension ──
    if has_q:
        for ll in logic_lines:
            ln = ll['name']; rows = L.get(ln)
            if not rows: continue
            gm = ll['gm']; rev_r = rows['rev_r']; gm_r = rows['gm_r']
            seg_name = line_to_seg.get(ln, ''); si = seg_info.get(seg_name, {})
            s1_gp_row = si.get('gp', 0); s1_rev_row = si.get('rev', 0)
            is_1to1 = ln in one_to_one
            cur_yr, cur_q = q_start_yr, q_start_q
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                proj_idx = cur_yr - bfyr - 1
                is_q_actual = qi < Q_START + q_actual_n
                # GM: 1:1 actual Qs use S1 GP/Rev (real quarterly margin)
                if is_1to1 and s1_gp_row and s1_rev_row and is_q_actual:
                    CF(ws, gm_r, qi, f'=IFERROR({cl}{s1_gp_row}/{cl}{s1_rev_row},"")', fmt=PCT)
                elif is_1to1 and not is_q_actual and 0 <= proj_idx < len(gm.get('proj', [])):
                    I(ws, gm_r, qi, gm['proj'][proj_idx], fmt=PCT)
                else:
                    I(ws, gm_r, qi, gm.get('fy0', 0), fmt=PCT)
                cur_q += 1
                if cur_q > 4: cur_q = 1; cur_yr += 1
            # Opex/Rev rate → Q columns (1:1 actual Qs use S1 (GP−OP)/Rev)
            line_opex = ll.get('opex_rate')
            opex_rates = line_opex if line_opex else gl.get('opex_rate', [])
            s1_op_row = si.get('op', 0)
            cur_yr, cur_q = q_start_yr, q_start_q
            for scan_r in range(rev_r, rows.get('op_r', rev_r + 6)):
                cv = str(ws.cell(row=scan_r, column=3).value or '')
                if 'Opex / Rev' in cv:
                    for qi in range(Q_START, Q_END + 1):
                        cl = get_column_letter(qi)
                        is_q_actual = qi < Q_START + q_actual_n
                        # 1:1 actual Q: use segment (GP−OP)/Rev like GM
                        if (ln in one_to_one) and s1_gp_row and s1_op_row and s1_rev_row and is_q_actual:
                            CF(ws, scan_r, qi, f'=IFERROR(({cl}{s1_gp_row}-{cl}{s1_op_row})/{cl}{s1_rev_row},"")', fmt=PCT)
                        else:
                            _py = cur_yr - bfyr - 1
                            _idx = 2 + _py + 1
                            _idx = max(0, min(_idx, len(opex_rates) - 1))
                            I(ws, scan_r, qi, opex_rates[_idx], fmt=PCT)
                        cur_q += 1
                        if cur_q > 4: cur_q = 1; cur_yr += 1
                    break

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
    C(ws, R, 3, 'Tax rate', font=bf)
    tax_r = R; R += 1

    # ═══════════════ §3 P&L ═══════════════
    R += 1
    C(ws, R, 1, 'P&L', font=bf12)
    R += 1
    # Basis label (below P&L, same as Sections 1+2)
    _basis = meta.get('basis', 'gaap')
    _bnote = meta.get('basis_note', '')
    _blabel = f'Basis: {_basis.upper()}'
    if _bnote:
        _blabel += f' — {_bnote[:120]}'
    C(ws, R, 1, _blabel, font=itf)
    R += 1
    a = actuals
    LN = [ln['name'] for ln in logic_lines]

    residual_term = f'+{sc(total_residual)}' if total_residual else ''
    gp_residual_term = f'+{sc(gp_residual)}' if gp_residual else ''

    # Total Revenue (FY23-25 actuals, FY26+ formula)
    A(ws, R, DS, sc(a['fy-2']['rev']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['rev']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['rev']), fmt=NUM)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term,
          font=bf, fmt=NUM)
    # Q actuals A() (synthesized from segment Q data) + Q proj Σ
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('rev', 0) for seg in segments)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term,
              font=bf, fmt=NUM)
    C(ws, R, 3, 'Total Revenue')
    trev = R; R += 1

    # Check Rev (model formula for all columns)
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term, fmt=NUM)
    C(ws, R, 3, '  Check (model)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    check_rev_r = R; R += 1

    # Revenue YoY
    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{trev}/{cl_d}{trev}-1,"")', fmt=PCT)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        if ci >= Q_START:
            # Q columns: YoY (4Q back) if year-ago exists, else blank
            if ci - 4 >= Q_START:
                pl = get_column_letter(ci - 4)
            else:
                continue
        else:
            # Annual columns: YoY = current/prior year - 1
            pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{trev}/{pl}{trev}-1,"")', fmt=PCT)
    C(ws, R, 3, 'Rev YoY')
    R += 1
    # QoQ (collapsed, Q columns only)
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{trev}/{pl}{trev}-1,"")', fmt=PCT)
        C(ws, R, 3, '  Rev QoQ', font=itf)
        R += 1

    # Total GP (FY23-25 actuals, FY26+ formula)
    A(ws, R, DS, sc(a['fy-2']['gp']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['gp']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['gp']), fmt=NUM)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term,
          font=bf, fmt=NUM)
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('gp', 0) for seg in segments)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term,
              font=bf, fmt=NUM)
    C(ws, R, 3, 'Total GP')
    tgp = R; R += 1
    # GP YoY
    C(ws, R, DS, '', fmt=PCT)
    _gpe = get_column_letter(DS + 1); _gpd = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({_gpe}{tgp}/{_gpd}{tgp}-1,"")', fmt=PCT)
    _gf0 = get_column_letter(FY0); _gf1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({_gf0}{tgp}/{_gf1}{tgp}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{tgp}/{pl}{tgp}-1,"")', fmt=PCT)
    C(ws, R, 3, 'GP YoY')
    R += 1
    # GP QoQ
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{tgp}/{pl}{tgp}-1,"")', fmt=PCT)
        C(ws, R, 3, '  GP QoQ', font=itf)
        R += 1

    # Check GP (model formula for all columns)
    for ci in range(DS, LC + 1):
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
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{trev}*{cl}{opex_r}', fmt=NUM)
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('opex', 0) for seg in segments)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, f'={cl}{trev}*{cl}{opex_r}', fmt=NUM)
    C(ws, R, 3, 'Opex')
    ov = R; R += 1

    A(ws, R, DS, sc(a['fy-2']['op']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['op']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['op']), fmt=NUM)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{tgp}-{cl}{ov}', fmt=NUM)
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('op', 0) for seg in segments)
            # Fallback to company quarters
            if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('op', 0)
            cl = get_column_letter(Q_START + qi)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
            else: C(ws, R, Q_START + qi, f'={cl}{tgp}-{cl}{ov}', fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, f'={cl}{tgp}-{cl}{ov}', fmt=NUM)
    C(ws, R, 3, 'OI')
    op = R; R += 1

    # OI YoY
    C(ws, R, DS, '', fmt=PCT)
    _cl_e = get_column_letter(DS + 1); _cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({_cl_e}{op}/{_cl_d}{op}-1,"")', fmt=PCT)
    _f0 = get_column_letter(FY0); _f_1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({_f0}{op}/{_f_1}{op}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{op}/{pl}{op}-1,"")', fmt=PCT)
    C(ws, R, 3, 'OI YoY')
    R += 1
    # OI QoQ
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{op}/{pl}{op}-1,"")', fmt=PCT)
        C(ws, R, 3, '  OI QoQ', font=itf)
        R += 1

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
    da_actuals_r = R
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}*{get_column_letter(FY0)}{da_actuals_r}/{get_column_letter(FY0)}{trev}', fmt=NUM)
    if has_q:
        da_fy0_col = get_column_letter(FY0)
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('da', 0) for seg in segments)
            if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('da', 0)
            cl = get_column_letter(Q_START + qi)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
            else: C(ws, R, Q_START + qi, f'=({da_fy0_col}{op}*{da_fy0_col}{da_actuals_r}/{da_fy0_col}{trev})/4', fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, f'=({da_fy0_col}{op}*{da_fy0_col}{da_actuals_r}/{da_fy0_col}{trev})/4', fmt=NUM)
    C(ws, R, 3, 'D&A')
    da_r = R; R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}+{cl}{da_r}', fmt=NUM)
    C(ws, R, 3, 'EBITDA')
    ebitda_r = R; R += 1
    # EBITDA YoY
    C(ws, R, DS, '', fmt=PCT)
    _ebe = get_column_letter(DS + 1); _ebd = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({_ebe}{ebitda_r}/{_ebd}{ebitda_r}-1,"")', fmt=PCT)
    _ebf0 = get_column_letter(FY0); _ebf1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({_ebf0}{ebitda_r}/{_ebf1}{ebitda_r}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{ebitda_r}/{pl}{ebitda_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'EBITDA YoY')
    R += 1
    # EBITDA QoQ
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{ebitda_r}/{pl}{ebitda_r}-1,"")', fmt=PCT)
        C(ws, R, 3, '  EBITDA QoQ', font=itf)
        R += 1

    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ebitda_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'EBITDA margin')
    _ebitda_end = R; R += 1

    # Check EBIT (model formula for all columns)
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["op_r"]}' for ln in LN if L[ln].get('op_r')]), fmt=NUM)
    C(ws, R, 3, '  Check (model)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

    # Tax + NI (always computed)
    _ni_start = R
    A(ws, R, DS, sc(a['fy-2']['tax']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['tax']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['tax']), fmt=NUM)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}*{cl}{tax_r}', fmt=NUM)
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('tax', 0) for seg in segments)
            if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('tax', 0)
            cl = get_column_letter(Q_START + qi)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
            else: C(ws, R, Q_START + qi, f'={cl}{op}*{cl}{tax_r}', fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, f'={cl}{op}*{cl}{tax_r}', fmt=NUM)
    C(ws, R, 3, 'Tax')
    tv = R; R += 1

    A(ws, R, DS, sc(a['fy-2']['ni']), fmt=NUM)
    A(ws, R, DS + 1, sc(a['fy-1']['ni']), fmt=NUM)
    A(ws, R, FY0, sc(a['fy0']['ni']), fmt=NUM)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'={cl}{op}-{cl}{tv}', fmt=NUM)
    if has_q:
        for qi in range(q_actual_n):
            qk = f'q{qi+1}'
            qv = sum(seg.get('quarters', {}).get(qk, {}).get('ni', 0) for seg in segments)
            if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('ni', 0)
            cl = get_column_letter(Q_START + qi)
            if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
            else: C(ws, R, Q_START + qi, f'={cl}{op}-{cl}{tv}', fmt=NUM)
        for qi in range(Q_START + q_actual_n, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, f'={cl}{op}-{cl}{tv}', fmt=NUM)
    C(ws, R, 3, 'Net Income')
    ni_r = R; R += 1

    if nci_rate > 0:
        for ci in range(DS, LC + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{ni_r}*(1-{nci_rate})', fmt=NUM)
        C(ws, R, 3, 'NI attributable')
        ni_r = R; R += 1

    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{ni_r}/{cl_d}{ni_r}-1,"")', fmt=PCT)
    for ci in range(FY0, LC + 1):
        cl = get_column_letter(ci)
        if ci >= Q_START and ci - 4 >= Q_START:
            pl = get_column_letter(ci - 4)
        elif ci >= Q_START:
            continue
        else:
            pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{pl}{ni_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'NI YoY')
    R += 1
    # QoQ (collapsed, Q columns only)
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{ni_r}/{pl}{ni_r}-1,"")', fmt=PCT)
        C(ws, R, 3, '  NI QoQ', font=itf)
        R += 1
    # NPM (after NI YoY+QoQ, consistent with OPM placement)
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'NPM')
    R += 1
    _ni_end = R; R += 1


    # ── Inline Check columns: per-row Annual−QSum at existing rows (S1-S3) ──
    if has_q:
        cur_yr, cur_q, qi = q_start_yr, q_start_q, 0
        total_q = q_actual_n + q_proj_n
        SKIP_KW = ('YoY', 'QoQ', 'GM', 'OPM', 'NPM', 'margin', '/ Rev', '%', 'Check', 'Implied', 'Bull', 'Base', 'Bear', 'Tax rate', 'ASP', 'Shares')
        while qi < total_q:
            rem_in_fy = 4 - cur_q + 1; fyc = min(rem_in_fy, total_q - qi)
            if fyc == 4:
                ann_col = DS + (cur_yr - bfyr + 2)
                chk_col = Q_END + 3  # after Q + 2 gap
                if ann_col <= LC_ANNUAL:
                    ac = get_column_letter(ann_col); cc = get_column_letter(chk_col)
                    q_letters = [get_column_letter(Q_START + qi + j) for j in range(4)]
                    q_sum_f = '+'.join(f'{ql}{{r}}' for ql in q_letters)
                    ws.cell(row=1, column=chk_col).value = f'FY{cur_yr} Check'
                    ws.cell(row=1, column=chk_col).font = bf
                    for row in range(s1_start, _ni_end + 1):
                        cv = str(ws.cell(row=row, column=3).value or '').strip()
                        if not cv or any(kw in cv for kw in SKIP_KW): continue
                        ws.cell(row=row, column=chk_col).value = f'=({ac}{row}-({q_sum_f.format(r=row)}))/{ac}{row}'
                        ws.cell(row=row, column=chk_col).number_format = PCT
                        ws.cell(row=row, column=chk_col).font = nf
                    ws.column_dimensions[cc].width = 12
                    ws.column_dimensions.group(cc, cc, outline_level=1, hidden=True)
            qi += fyc; cur_yr += 1; cur_q = 1

    # ── Fix Global Opex rate / Tax rate formulas ──
    # FY23-25: =Opex/Rev, =Tax/OP
    for ci in [DS, DS + 1, FY0]:
        cl = get_column_letter(ci)
        CF(ws, opex_r, ci, f'=IFERROR({cl}{ov}/{cl}{trev},"")', fmt=PCT)
    for i, ov_val in enumerate(gl['opex_rate'][3:], FY0 + 1):
        I(ws, opex_r, i, ov_val, fmt=PCT)
    if has_q:
        _opex_rates = gl.get('opex_rate', [0.25]*8)
        cur_yr, cur_q = q_start_yr, q_start_q
        for qi in range(q_actual_n + q_proj_n):
            _py = cur_yr - bfyr - 1
            if _py < 0: _py = 0  # actual Q in base year → use FY0 rate
            _idx = min(3 + _py, len(_opex_rates) - 1)
            I(ws, opex_r, Q_START + qi, _opex_rates[_idx], fmt=PCT)
            cur_q += 1
            if cur_q > 4: cur_q = 1; cur_yr += 1
    for ci in [DS, DS + 1, FY0]:
        cl = get_column_letter(ci)
        CF(ws, tax_r, ci, f'=IFERROR({cl}{tv}/{cl}{op},"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        I(ws, tax_r, ci, gl['tax_rate'], fmt=PCT)
    if has_q:
        for qi in range(q_actual_n + q_proj_n):
            I(ws, tax_r, Q_START + qi, gl['tax_rate'], fmt=PCT)

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
            return op, 'EBIT'
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

        # MCap (with EV bridge for EV methods)
        if method.startswith('ev_'):
            nd_share = f'({gc}/{tc_gp}*{net_debt})' if net_debt else '0'
            # Enterprise Value
            C(ws, R, 3, '  EV', font=itf)
            C(ws, R, SC, f'={alloc_ref}*{sc_l}{mult_row}', fmt=DEC)
            ev_line_r = R; R += 1
            # Net Debt (allocated)
            C(ws, R, 3, '  Net Debt', font=itf)
            C(ws, R, SC, f'={nd_share}' if net_debt else '0', fmt=DEC)
            R += 1
            # Mkt Cap
            mcap_f = f'=IFERROR({sc_l}{ev_line_r}-{sc_l}{R - 1},"")'
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
    sotp_seg_start = R
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
            # Enterprise Value
            C(ws, R, 3, '  EV', font=itf)
            C(ws, R, SC, f'={alloc_ref_s}*{sc_l}{pe_row}', fmt=DEC)
            ev_line_s = R; R += 1
            # Net Debt (allocated)
            C(ws, R, 3, '  Net Debt', font=itf)
            C(ws, R, SC, f'={nd_s}' if net_debt else '0', fmt=DEC)
            R += 1
            mcap_f_s = f'=IFERROR({sc_l}{ev_line_s}-{sc_l}{R - 1},"")'
        else:
            mcap_f_s = f'=IFERROR({alloc_ref_s}*{sc_l}{pe_row},"")'
        C(ws, R, 3, 'Mkt Cap')
        C(ws, R, SC, mcap_f_s, font=bf, fmt=DEC)
        smc_rows.append(R); R += 1

    C(ws, R, 2, 'TOTAL', font=bf)
    C(ws, R, SC, '=' + '+'.join([f'{sc_l}{mr}' for mr in smc_rows]),
      font=bf, fmt=DEC)
    sotp_seg_r = R; R += 1
    ws.row_dimensions.group(sotp_seg_start, sotp_seg_r, outline_level=1, hidden=True)

    # ═══════════════ §6 Market Data ═══════════════
    R += 1
    C(ws, R, 1, 'Market Cap', font=bf12)
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

    # Bridge: Net Debt + Enterprise Value (collapsed)
    if net_debt:
        nd_start = R
        C(ws, R, 3, '  Net Debt', font=itf)
        C(ws, R, SC, sc(net_debt), fmt=NUM)
        nd_r = R; R += 1
        C(ws, R, 3, '  Enterprise Value', font=itf)
        C(ws, R, SC, f'={sc_l}{sotp_r}+{sc_l}{nd_r}', fmt=NUM)
        ev_r = R; R += 1
        ws.row_dimensions.group(nd_start, ev_r, outline_level=1, hidden=True)

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
        # Clear placeholder zeros (only cells without explicit format)
        for c in range(DS, LC + 1):
            cl = ws.cell(row=row, column=c)
            if cl.value == 0 and cl.number_format == 'General':
                cl.value = None
        # Clear D/E formula-only cells (Section 2 only, skip protected rows)
        if s1_end < row <= s2_end and row not in protected_rows:
            for c in (DS, DS + 1):
                cl = ws.cell(row=row, column=c)
                if cl.value and isinstance(cl.value, str) and cl.value.startswith('='):
                    cl.value = None
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
    # Clear gap columns between annual and Q (value + fill)
    if has_q:
        for row in range(1, R):
            for gc in (LC_ANNUAL + 1, LC_ANNUAL + 2):
                c = ws.cell(row=row, column=gc)
                c.value = None; c.fill = PatternFill()
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 24
    ws.column_dimensions['C'].width = 36
    for ci in range(DS, LC + 1):
        cl = get_column_letter(ci)
        ws.column_dimensions[cl].width = 5 if has_q and ci in (LC_ANNUAL + 1, LC_ANNUAL + 2) else 13

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
