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

import json, argparse, codecs, functools, os, time, datetime
import yfinance as yf
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Color
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
import win32com.client

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

VALID_DEPTH = {'gp', 'op', 'ebitda'}
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

    # actuals required fields (varies by depth)
    if depth == 'ebitda':
        req_fields = ['rev', 'ebitda', 'op', 'ni']
    elif depth == 'op':
        req_fields = ['rev', 'gp', 'op']
    else:
        req_fields = ['rev', 'gp']
    for fy_key in ['fy-2', 'fy-1', 'fy0']:
        fy = a.get(fy_key, {})
        for field in req_fields:
            if field not in fy:
                raise ValueError(f'actuals.{fy_key}.{field} is required')

    # global opm only required for GP/OP depth
    if depth != 'ebitda':
        opm_arr = cfg.get('global', {}).get('opm', [])
        if len(opm_arr) != 3 + proj_n:
            raise ValueError(f'global.opm length {len(opm_arr)} != {3 + proj_n} (3 actual + {proj_n} proj)')

    # segments: split sum sanity
    for seg in cfg.get('segments', []):
        sn = seg.get('name', '?')
        lls = seg.get('logic_lines', [])
        if lls:
            total_split = sum(l.get('split', 0) for l in lls)
            if abs(total_split - 1.0) > 0.05:
                print(f'  [warn] seg "{sn}" logic_lines split sum={total_split:.3f} (≠1.0 by {abs(total_split-1.0):.1%})')

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

def _adapt_new_to_old(cfg):
    """Convert research-model.json new structure to backward-compat old keys."""
    if 'assumptions' not in cfg:
        return cfg  # already old format
    a = cfg['actuals']
    asm = cfg['assumptions']
    fy_map = {'FY2023': 'fy-2', 'FY2024': 'fy-1', 'FY2025': 'fy0'}

    # actuals
    n_act = {}
    for new_fy, old_fy in fy_map.items():
        ann = a.get(new_fy, {}).get('annual', {})
        gaap = ann.get('gaap', {}).get('is', {})
        non_gaap = ann.get('non_gaap', {}).get('is', {})
        n_act[old_fy] = {
            'rev': gaap.get('rev', 0),
            'gp': gaap.get('gp', 0),
            'op': gaap.get('oi', 0),
            'ni': gaap.get('ni', 0),
            'tax': gaap.get('tax', 0),
            'da': gaap.get('da', 0),
            'ebitda': non_gaap.get('ebitda', 0),
            'details': ann.get('non_gaap', {}).get('adj', {}),
        }
    cfg['actuals'] = n_act

    # segments (from most recent FY gaap + non_gaap)
    def _match_seg(name, candidates):
        """Match segment name (handle 'Segment' suffix difference)."""
        for c in candidates:
            if c.startswith(name) or name.startswith(c):
                return c
        return None

    segs = []
    for s in a.get('FY2025', {}).get('annual', {}).get('gaap', {}).get('segments', []):
        s_name = s['name']
        # Find matching lines from assumptions
        matched_lines = [ll for ll in asm.get('lines', []) if ll.get('segment') and (ll['segment'] in s_name or s_name in ll['segment'])]
        if not matched_lines:
            continue
        seg_entry = {
            'name': s_name,
            'fy0': {'rev': s.get('rev', 0)},
            'logic_lines': [{'name': ll['name'], 'split': 1.0 if ll.get('one_to_one') else 0} for ll in matched_lines],
            'quarters': {},
        }
        # Non-GAAP ebitda + historical years
        for ns in a.get('FY2025', {}).get('annual', {}).get('non_gaap', {}).get('segments', []):
            if ns['name'] == s_name or s_name in ns['name']:
                seg_entry['fy0']['ebitda'] = ns.get('ebitda', 0)
        for new_fy, old_fy in fy_map.items():
            sg = {}
            for sg_g in a.get(new_fy, {}).get('annual', {}).get('gaap', {}).get('segments', []):
                if sg_g['name'] == s_name or s_name in sg_g['name']:
                    sg['rev'] = sg_g.get('rev', 0)
            for sg_n in a.get(new_fy, {}).get('annual', {}).get('non_gaap', {}).get('segments', []):
                if sg_n['name'] == s_name or s_name in sg_n['name']:
                    sg['ebitda'] = sg_n.get('ebitda', 0)
            if sg:
                seg_entry[old_fy] = sg
        # Quarters
        for qk in ['Q1','Q2','Q3','Q4']:
            seg_entry['quarters'][qk.lower()] = {'rev': 0, 'ebitda': 0}
            q_non = a.get('FY2025', {}).get(qk, {}).get('non_gaap', {}).get('segments', [])
            for sq in q_non:
                if sq['name'] == s_name or s_name in sq['name']:
                    seg_entry['quarters'][qk.lower()] = {'rev': a.get('FY2025',{}).get(qk,{}).get('gaap',{}).get('is',{}).get('rev',0), 'ebitda': sq.get('ebitda', 0)}
        if seg_entry['logic_lines']:
            segs.append(seg_entry)
    # Remaining logic lines (no segment) -> add as Non-core line at top level
    remaining = [ll for ll in asm.get('lines', []) if not any(ll['name'] in [l['name'] for s2 in segs for l in s2['logic_lines']] for _ in [1])]
    cfg['segments'] = segs

    # logic_lines from assumptions.lines
    cfg['logic_lines'] = []
    for ll in asm.get('lines', []):
        entry = {'name': ll['name'], 'module': ll['module']}
        # gm
        gm = ll.get('gm', {})
        if gm:
            entry['gm'] = {
                'fy-2': gm.get('FY2023', None),
                'fy-1': gm.get('FY2024', None),
                'fy0': gm.get('FY2025', 0),
                'proj': [gm.get(k, 0) for k in sorted([k for k in gm.keys() if 'E' in k])],
            }
        # yoy
        yoy = ll.get('yoy', {})
        if yoy:
            entry['yoy'] = {}
            for scenario in ['bull','base','bear']:
                if yoy.get(scenario):
                    items = sorted([(k,v) for k,v in yoy[scenario].items()])
                    entry['yoy'][scenario] = [v for _,v in items]
        # q_history
        qd = ll.get('q_data', {})
        if qd:
            entry['q_history'] = {}
            for fy, qs in qd.items():
                for qk, qv in qs.items():
                    if qv.get('rev') is not None:
                        entry['q_history'][qk.lower()] = {'rev': qv['rev']}
            if not entry['q_history']:
                del entry['q_history']
        # sotp
        if ll.get('sotp'):
            entry['sotp'] = ll['sotp']
        cfg['logic_lines'].append(entry)

    # quarters (company-level from actuals)
    cfg['quarters'] = {}
    for qk in ['Q1','Q2','Q3','Q4']:
        q_gaap = a.get('FY2025', {}).get(qk, {}).get('gaap', {}).get('is', {})
        q_non = a.get('FY2025', {}).get(qk, {}).get('non_gaap', {}).get('is', {})
        if q_gaap.get('rev') is not None:
            cfg['quarters'][qk.lower()] = {
                'rev': q_gaap.get('rev', 0),
                'gp': q_gaap.get('gp', 0),
                'op': q_gaap.get('oi', 0),
                'ni': q_gaap.get('ni', 0),
                'tax': q_gaap.get('tax', 0),
                'ebitda': q_non.get('ebitda', 0),
            }

    # global
    cfg['global'] = {'tax_rate': asm.get('global', {}).get('tax_rate', {}).get('FY2025', 0.22)}

    return cfg


def build(json_path, output_path=None):
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    cfg = _adapt_new_to_old(cfg)
    validate_json(cfg)

    is_ebitda_depth = cfg['meta'].get('p&l_depth') == 'ebitda'
    is_op_depth = cfg['meta'].get('p&l_depth') == 'op'
    is_gp_depth = cfg['meta'].get('p&l_depth') == 'gp'

    # ═══ Phase 1.1: Reconcile — scale Q→FY for M=4 complete actual FYs ═══
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
                        qh=ll.setdefault('q_history',{})
                        for j in range(4):
                            qk=f'q{qi+j+1}'; qd=qh.get(qk,{})
                            if 'rev' in qd: qh[qk]['rev']=round(qd['rev']*s)
                            if 'volume' in qd and 'asp' in qd and qd.get('asp',0)>0:
                                qh[qk]['volume']=round(qh[qk]['rev']*ll.get('unit_scale',100)/qd['asp'])
            qi += fyc; cur_yr += 1; cur_q = 1

        # ═══ Phase 1.2: Company Q → Segment Q split (A-share: seg Q from company Q) ═══
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
                qh = ll.setdefault('q_history', {})
                qd = qh.get(qk, {})
                if qd.get('rev'): continue  # already has data
                if qd.get('volume') and qd.get('asp'): continue  # vol_asp: use own Q data
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

        # ═══ Phase 1.3: Blend — actual Q profit rates → annual model assumptions ═══
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

                        # Blend per-line gm + opm for each logic line in this segment
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
                                line_opex = ll_obj.get('opm')
                                opm_arr = line_opex if line_opex else gl.get('opm', [])
                                idx_o = 3 + proj_i
                                om_model = opm_arr[idx_o] if idx_o < len(opm_arr) else 0.25
                                om_blend = w_act * om_actual + w_mod * om_model
                                if idx_o < len(opm_arr):
                                    if line_opex: ll_obj['opm'][idx_o] = round(om_blend, 4)
                                    else: gl.get('opm', [])[idx_o] = round(om_blend, 4)
                    # Blend global opm (company-level, from all segments' actual Qs)
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
                            co_om_mod = gl.get('opm', [])[3 + proj_i] if 3 + proj_i < len(gl.get('opm', [])) else 0.25
                            co_blend = (M_seg / 4) * co_om_act + (1 - M_seg / 4) * co_om_mod
                            idx_g = 3 + proj_i
                            if idx_g < len(gl.get('opm', [])):
                                gl.get('opm', [])[idx_g] = round(co_blend, 4)
            qi_b += fyc; cur_yr += 1; cur_q = 1

        # ═══ Phase 1.4: Q Driver Distribution — annual drivers → Q projections ═══
        # For each complete 4Q FY, distribute annual drivers to Qs using seasonal weights.
        # vol_asp: Q_Vol = Vol_Y × w_i, Q_ASP = ASP_Y × s_i (Σ(w×s)=1)
        # yoy: Newton solve r s.t. Σ Q_1×(1+r)^k = Annual
        # backlog_burn: Q_Burn = Burn_Y × w_i, Q_ASP = ASP_Y × s_i

        # Pre-compute total_residual (Non-core absorbs all segment residuals)
        total_residual = 0; gp_residual = 0
        for seg in cfg.get('segments', []):
            r = round(seg['fy0']['rev'] - sum(seg['fy0']['rev'] * l['split'] for l in seg.get('logic_lines', [])))
            if r > 0:
                total_residual += r
                gp_residual += round(r * seg.get('residual', {}).get('gm', 0))
        cur_yr, cur_q, qi = q_start_yr, q_start_q, 0
        while qi < total_q:
            rem = 4 - cur_q + 1; fyc = min(rem, total_q - qi)
            if fyc == 4:
                fy_idx = cur_yr - bfyr + 2; proj_i = fy_idx - 3
                for ll in cfg.get('logic_lines', []):
                    ln = ll['name']; qh = ll.setdefault('q_history', {})
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
                            vp = ll['volume']['proj']
                            t0 = ll['tiers'][0]
                            # BBE tiers: use asp_base (Base scenario) for Q distribution
                            if any(k in t0 for k in ('asp_bull', 'asp_base', 'asp_bear')):
                                ap = t0.get('asp_base', t0.get('asp', [0]))
                            else:
                                ap = t0.get('asp', t0.get('asp_base', [0]))
                            if proj_i < len(vp):
                                # ASP array: if tier has no explicit asp_fy0, ap[0]=FY0,
                                # proj values start at ap[1]. BBE arrays always FY0-first.
                                asp_offset = 0 if 'asp_fy0' in t0 else 1
                                ap_idx = min(proj_i + asp_offset, len(ap) - 1)
                                ann_asp = ap[ap_idx]
                                ann_vol = vp[proj_i]
                                ann = ann_vol * ann_asp / us  # display units, matches actual Q rev
                        elif module == 'backlog_burn':
                            bp = ll['backlog']['burn']['proj']; ap_arr = ll.get('asp', [])
                            # backlog_burn asp array: check if first element is FY0
                            bb_asp_offset = 0 if ll.get('asp_fy0') is not None else 1
                            bb_ap_idx = min(proj_i + bb_asp_offset, len(ap_arr) - 1)
                            ann_asp = ap_arr[bb_ap_idx] if ap_arr else 0
                            ann_vol = bp[proj_i]  # burn = "volume" in this context
                            ann = ann_vol * ann_asp / us if ann_asp else 0  # display units
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
                            # Non-core absorbs all segment residuals
                            if ln == 'Non-core':
                                ann += total_residual
                    if ann <= 0: continue

                    # ── Count M and read actual Q driver data ──
                    actual_q = []  # list of (offset, rev, vol, asp) for Qs with data
                    for j in range(4):
                        qk = f'q{qi+j+1}'; qd = qh.get(qk, {})
                        rv = qd.get('rev', 0)
                        # Fallback: segment quarters (skip for vol_asp/backlog with volume+asp)
                        if not rv and qd.get('volume') and qd.get('asp') and module in ('vol_asp', 'backlog_burn'):
                            rv = round(qd['volume'] * qd['asp'] / us, 2)  # compute from vol×asp
                        elif not rv:
                            for seg in cfg.get('segments', []):
                                for l in seg.get('logic_lines', []):
                                    if l['name'] == ln:
                                        sq_r = seg.get('quarters', {}).get(qk, {}).get('rev', 0)
                                        if sq_r:
                                            rv = sq_r * l['split']
                        if rv and rv > 0:
                            vv = qd.get('volume', 0) or (rv * us / ann_asp if ann_asp else 0)
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

                        # Non-core: write full Q revs + GP (base + residual) to q_history
                        if ln == 'Non-core' and total_residual > 0:
                            residual_per_q = round(total_residual / 4)
                            gp_residual_per_q = round(gp_residual / 4)
                            nc_gm = ll.get('gm', {}).get('proj', [ll.get('gm', {}).get('fy0', 0.22)])[0] if proj_i < len(ll.get('gm', {}).get('proj', [0.22])) else 0.22
                            if not isinstance(nc_gm, (int, float)): nc_gm = 0.22
                            for j in range(4):
                                qk = f'q{qi+j+1}'
                                qh[qk] = qh.get(qk, {})
                                if j in actual_set:
                                    for a in actual_q:
                                        if a[0] == j:
                                            qh[qk]['rev'] = a[1] + residual_per_q
                                            qh[qk]['gp'] = round(a[1] * nc_gm) + gp_residual_per_q
                                elif j < first_actual:
                                    base_rev = round(a_first / ((1 + r_q) ** (first_actual - j)))
                                    qh[qk]['rev'] = base_rev + residual_per_q
                                    qh[qk]['gp'] = round(base_rev * nc_gm) + gp_residual_per_q
                                else:
                                    base_rev = round(a_last * ((1 + r_q) ** (j - last_actual)))
                                    qh[qk]['rev'] = base_rev + residual_per_q
                                    qh[qk]['gp'] = round(base_rev * nc_gm) + gp_residual_per_q

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
                        remaining_asp = remaining_rev * us / remaining_vol  # natural ASP for formula Vol*ASP/us

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
                                            qh[qk]['asp'] = a[1] * us / a[2]  # natural ASP for Vol×ASP/us formula
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

    # ═══ Phase 1.5: Market Data — yfinance snapshot ═══
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
    LC = LC_ANNUAL  # always the last annual column (never polluted by Q)
    if has_q:
        Q_START = LC_ANNUAL + 3  # 2 blank columns between Y and Q
        Q_END = Q_START + q_actual_n + q_proj_n - 1
        ALL_END = Q_END  # last column including Q, for loops that span both
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
        ALL_END = LC_ANNUAL
        QL = []

    YR = [f'FY{bfyr - 2}A', f'FY{bfyr - 1}A', f'FY{bfyr}A'] + \
         [f'FY{bfyr + i}E' for i in range(1, proj_n + 1)]

    # ═══════════════ Phase 2: Render Excel ═══════════════
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

    # ═══ Phase 2.1: §1 Reported Segments ═══
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
        srev = fy0['rev']
        if is_ebitda_depth:
            sebitda = fy0.get('ebitda', 0)
        else:
            sgp = fy0['gp']; sgm = sgp / srev if srev else 0; scost = srev - sgp
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
        C(ws, R, 3, 'Revenue', font=bf)
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
        C(ws, R, 3, 'Rev YoY', font=nf)
        R += 1
        # QoQ row (collapsed, Q columns only)
        if has_q:
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  Rev QoQ', font=itf)
            R += 1

        if is_ebitda_depth:
            # ── EBITDA block (EBITDA first, margin formula after) ──
            for yr_key, col in hist_years:
                yr = seg.get(yr_key)
                if yr and yr.get('ebitda'): A(ws, R, col, sc(yr['ebitda']), fmt=NUM)
                else: C(ws, R, col, '', fmt=NUM)
            A(ws, R, FY0, sc(sebitda), fmt=NUM)
            if has_q:
                for qi in range(q_actual_n):
                    qk = f'q{qi+1}'
                    q_ebitda = seg.get('quarters', {}).get(qk, {}).get('ebitda', 0)
                    if q_ebitda: A(ws, R, Q_START + qi, sc(q_ebitda), fmt=NUM)
            ebitda_r_s1 = R
            C(ws, R, 3, 'EBITDA', font=bf)
            R += 1
            # EBITDA YoY
            C(ws, R, DS, '', fmt=PCT)
            _cle = get_column_letter(DS + 1); _cld = get_column_letter(DS)
            C(ws, R, DS + 1, f'=IFERROR({_cle}{ebitda_r_s1}/{_cld}{ebitda_r_s1}-1,"")', fmt=PCT)
            _f0 = get_column_letter(FY0); _f1 = get_column_letter(FY0 - 1)
            C(ws, R, FY0, f'=IFERROR({_f0}{ebitda_r_s1}/{_f1}{ebitda_r_s1}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{ebitda_r_s1}/{pl}{ebitda_r_s1}-1,"")', fmt=PCT)
            C(ws, R, 3, 'EBITDA YoY', font=nf)
            R += 1
            # EBITDA QoQ
            if has_q:
                for ci in range(DS, LC_ANNUAL + 1):
                    C(ws, R, ci, '', fmt=PCT)
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                    if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                    else: C(ws, R, qi, f'=IFERROR({cl}{ebitda_r_s1}/{pl}{ebitda_r_s1}-1,"")', fmt=PCT)
                C(ws, R, 3, '  EBITDA QoQ', font=itf)
                R += 1
            # EBITDA margin = EBITDA / Revenue (formula)
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{ebitda_r_s1}/{cl}{rev_r},"")', fmt=PCT)
            C(ws, R, 3, 'EBITDA margin', font=nf)
            gm_r = R; R += 1
            cost_r = 0
            gp_r = ebitda_r_s1  # alias for seg_info
        else:
            # ── GP block ──
            _gp_r = R + 2
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{rev_r}-{cl}{_gp_r},"")', fmt=NUM)
            cost_r = R
            C(ws, R, 3, 'Cost', font=bf)
            R += 1

            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                CF(ws, R, ci, f'=IFERROR({cl}{R + 1}/{cl}{rev_r},"")', fmt=PCT)
            gm_r = R
            C(ws, R, 3, 'GM', font=nf)
            R += 1

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
            C(ws, R, 3, 'GP', font=bf)
            R += 1
            # GP YoY
            C(ws, R, DS, '', fmt=PCT)
            _cle = get_column_letter(DS + 1); _cld = get_column_letter(DS)
            C(ws, R, DS + 1, f'=IFERROR({_cle}{gp_r}/{_cld}{gp_r}-1,"")', fmt=PCT)
            _f0 = get_column_letter(FY0); _f1 = get_column_letter(FY0 - 1)
            C(ws, R, FY0, f'=IFERROR({_f0}{gp_r}/{_f1}{gp_r}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
            C(ws, R, 3, 'GP YoY', font=nf)
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
        # Opex = GP - OI (OP depth only, OI = R + 1)
        op_r_est = R + 1
        if not is_ebitda_depth and fy0.get('op') is not None:
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{gp_r}-{cl}{op_r_est},"")', fmt=NUM)
            C(ws, R, 3, 'Opex', font=bf)
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
                    _op_rate = gl.get('opm', [0.25]*8)[2]  # FY0 rate
                    _op = round(qd['gp'] - qd['rev'] * _op_rate)
                if _op is not None: A(ws, R, Q_START + qi, sc(_op), fmt=NUM)
            for qi in range(q_proj_n):
                C(ws, R, Q_START + q_actual_n + qi, '', fmt=NUM)
            op_r = R
            C(ws, R, 3, 'OI', font=bf)
            R += 1
            # OI YoY
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
            C(ws, R, 3, 'OI YoY', font=nf)
            R += 1
            # OI QoQ (collapsed, Q columns only)
            if has_q:
                for ci in range(DS, LC_ANNUAL + 1):
                    C(ws, R, ci, '', fmt=PCT)
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                    if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                    else: C(ws, R, qi, f'=IFERROR({cl}{op_r}/{pl}{op_r}-1,"")', fmt=PCT)
                C(ws, R, 3, '  OI QoQ', font=itf)
                R += 1
            # OPM
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{op_r}/{cl}{rev_r},"")', fmt=PCT)
            C(ws, R, 3, 'OPM', font=nf)
            R += 1


        # Line Revenue Split
        R += 1
        C(ws, R, 3, 'Line Revenue Split', font=bf)
        R += 1

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

        # ── Segment Check rows (multi-line segments only, below residual) ──
        seg_check_gp_r = 0; seg_check_op_r = 0
        if len(lls) >= 2:
            for ci in range(DS, ALL_END + 1):
                C(ws, R, ci, '', fmt=PCT)
            C(ws, R, 3, '  Check Seg GP', font=itf)
            ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
            seg_check_gp_r = R; R += 1
            if op_r:
                for ci in range(DS, ALL_END + 1):
                    C(ws, R, ci, '', fmt=PCT)
                C(ws, R, 3, '  Check Seg OP', font=itf)
                ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
                seg_check_op_r = R; R += 1

        seg_info[sn] = {
            'rev': rev_r, 'cost': cost_r, 'gp': gp_r, 'gm': gm_r,
            'split_rows': srows, 'lrev_rows': lrevs, 'res_row': res_row,
            'seg_check_gp_r': seg_check_gp_r, 'seg_check_op_r': seg_check_op_r,
        }
        if op_r: seg_info[sn]['op'] = op_r
        # Blank row between segments
        R += 1
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

        # ── Common: GM + GP (all modules) ──
        gm = ll['gm']
        # Cost = Rev - GP (GP/OP depth only, GP = R + 2: Cost→GM→GP)
        if not is_ebitda_depth:
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{result["rev_r"]}-{cl}{R + 2},"")', fmt=NUM)
            C(ws, R, 3, 'Cost', font=bf)
            cost_s2_r = R; R += 1
        else:
            cost_s2_r = 0

        if ln in one_to_one:
            # 1:1 → reference S1 margin row directly
            for yr_key, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]:
                if col == FY0 or (seg_obj and seg_obj.get(yr_key)):
                    cl = get_column_letter(col)
                    C(ws, R, col, f'={cl}{si["gm"]}', fmt=PCT)
        else:
            # Non-1:1 or EBITDA depth → I() assumption
            for yr_key, col in [('fy-2', DS), ('fy-1', DS + 1)]:
                if gm.get(yr_key): I(ws, R, col, gm[yr_key], fmt=PCT)
                else: C(ws, R, col, '', fmt=PCT)
            if gm.get('fy0'): I(ws, R, FY0, gm['fy0'], fmt=PCT)
        for i, v in enumerate(gm['proj']):
            I(ws, R, FY0 + 1 + i, v, fmt=PCT)
        C(ws, R, 3, 'EBITDA margin' if is_ebitda_depth else 'GM')
        gm_r = R; R += 1

        for ci in range(DS, ALL_END + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'=IFERROR({cl}{result["rev_r"]}*{cl}{gm_r},"")', fmt=NUM)
        C(ws, R, 3, 'EBITDA' if is_ebitda_depth else 'GP')
        gp_r = R; R += 1
        # GP/EBITDA YoY
        C(ws, R, DS, '', fmt=PCT)
        _cl2e = get_column_letter(DS + 1); _cl2d = get_column_letter(DS)
        C(ws, R, DS + 1, f'=IFERROR({_cl2e}{gp_r}/{_cl2d}{gp_r}-1,"")', fmt=PCT)
        _cf2_0 = get_column_letter(FY0); _cf2_1 = get_column_letter(FY0 - 1)
        C(ws, R, FY0, f'=IFERROR({_cf2_0}{gp_r}/{_cf2_1}{gp_r}-1,"")', fmt=PCT)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
            C(ws, R, ci, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
        C(ws, R, 3, ('EBITDA' if is_ebitda_depth else 'GP') + ' YoY')
        R += 1
        # GP QoQ
        if has_q:
            for ci in range(DS, LC_ANNUAL + 1):
                C(ws, R, ci, '', fmt=PCT)
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                else: C(ws, R, qi, f'=IFERROR({cl}{gp_r}/{pl}{gp_r}-1,"")', fmt=PCT)
            C(ws, R, 3, '  ' + ('EBITDA' if is_ebitda_depth else 'GP') + ' QoQ', font=itf)
            R += 1

        # ── Check rows: anchor reference for agent-driven diagnosis ──
        # Each check cell = gap% between model and anchor, agent scans pattern.
        # Format: Check Rev = (ModelRev - AnchorRev) / ABS(AnchorRev) → PCT
        rev_module = ll.get('module', 'yoy')
        needs_rev_check = True  # all lines get Rev check
        needs_gp_check = ln not in one_to_one
        hist_rev_ok = lrev_row and s1_rev_row and split_r
        hist_gp_ok = lrev_row and s1_gp_row and split_r

        def _chk_gap(ws, r, col, model_r, anchor_r, fmt=PCT):
            """Write gap% formula: (Model - Anchor) / ABS(Anchor)"""
            cl = get_column_letter(col)
            CF(ws, r, col,
               f'=IFERROR(({cl}{model_r}-{cl}{anchor_r})/ABS({cl}{anchor_r}),"")', fmt=fmt)

        # Check GP/GM removed from Section 2 — validated in Section 1 via Segment Aggregation

        # ── Check Util: for vol_asp lines with capacity ──
        cap_r = result.get('cap_r', 0)
        if cap_r and result.get('util_r', 0):
            # Util % is already Vol/Cap at result['util_r']
            # Check: is Util > 100%? Flag pattern for agent.
            # Re-use util_r as the check — agent reads it directly.
            check_util_r = result['util_r']
        else:
            check_util_r = 0

        # ── Check Util: for vol_asp lines with capacity ──
        cap_r = result.get('cap_r', 0)
        if cap_r and result.get('util_r', 0):
            check_util_r = result['util_r']
        else:
            check_util_r = 0

        # ── Per-line profit chain (gated by segment disclosure depth) ──
        line_ni_r = 0
        if max_seg_depth >= DEPTH_RANK['op']:
            # Opex = GP - OI (formula, hidden), OI = R+2 (Opex→OPM→OI)
            _oi_r_expected = R + 2
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                C(ws, R, ci, f'=IFERROR({cl}{gp_r}-{cl}{_oi_r_expected},"")', fmt=NUM)
            C(ws, R, 3, 'Opex', font=bf)
            R += 1

            # OPM = OI/Rev (operating margin assumption)
            line_om_arr = ll.get('opm')
            om_rates = line_om_arr if line_om_arr else gl.get('opm', [])
            _om_r = R
            for yr_i, col in [(0, DS), (1, DS + 1), (2, FY0)]:
                cl = get_column_letter(col)
                if (ln in one_to_one) and s1_gp_row and s1_op_row and s1_rev_row:
                    CF(ws, R, col, f'=IFERROR(({cl}{s1_gp_row}-{cl}{s1_op_row})/{cl}{s1_rev_row},"")', fmt=PCT)
                elif yr_i < len(om_rates):
                    I(ws, R, col, om_rates[yr_i], fmt=PCT)
                else:
                    C(ws, R, col, '', fmt=PCT)
            for i in range(proj_n):
                ri = 3 + i
                if ri < len(om_rates):
                    I(ws, R, FY0 + 1 + i, om_rates[ri], fmt=PCT)
            C(ws, R, 3, 'OPM', font=nf)
            R += 1
            # OI = Rev × OPM (historical: S1 OP×split for actual years)
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                is_hist = ci <= FY0 or (has_q and Q_START <= ci < Q_START + q_actual_n)
                if is_hist and s1_op_row and split_r:
                    if ln in one_to_one:
                        CF(ws, R, ci, '=IFERROR(%s%d,"")' % (cl, s1_op_row), fmt=NUM)
                    else:
                        CF(ws, R, ci, '=IFERROR(%s%d*%s%d,"")' % (cl, s1_op_row, cl, split_r), fmt=NUM)
                else:
                    CF(ws, R, ci, '=IFERROR(%s%d*%s%d,"")' % (cl, result['rev_r'], cl, _om_r), fmt=NUM)
            C(ws, R, 3, 'OI', font=bf)
            line_op_r = R; R += 1
            if _om_r: protected_rows.add(_om_r)
            # OI YoY
            C(ws, R, DS, '', fmt=PCT)
            _cl3e = get_column_letter(DS + 1); _cl3d = get_column_letter(DS)
            C(ws, R, DS + 1, f'=IFERROR({_cl3e}{line_op_r}/{_cl3d}{line_op_r}-1,"")', fmt=PCT)
            _cf3_0 = get_column_letter(FY0); _cf3_1 = get_column_letter(FY0 - 1)
            C(ws, R, FY0, f'=IFERROR({_cf3_0}{line_op_r}/{_cf3_1}{line_op_r}-1,"")', fmt=PCT)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
                C(ws, R, ci, f'=IFERROR({cl}{line_op_r}/{pl}{line_op_r}-1,"")', fmt=PCT)
            C(ws, R, 3, 'OI YoY', font=nf)
            R += 1
            # OI QoQ
            if has_q:
                for ci in range(DS, LC_ANNUAL + 1):
                    C(ws, R, ci, '', fmt=PCT)
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
                    if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
                    else: C(ws, R, qi, f'=IFERROR({cl}{line_op_r}/{pl}{line_op_r}-1,"")', fmt=PCT)
                C(ws, R, 3, '  OI QoQ', font=itf)
                R += 1
        if max_seg_depth >= DEPTH_RANK['ni']:
            # NM assumed → NI = Rev × NM → Tax = OI - NI (derived)
            line_nm = ll.get('tax_rate')  # JSON field: NM array
            nm_rates = line_nm if (line_nm and isinstance(line_nm, list)) else gl.get('tax_rate', [])
            _nm_r = R
            for yr_i, col in [(0, DS), (1, DS + 1), (2, FY0)]:
                cl = get_column_letter(col)
                if yr_i < len(nm_rates):
                    I(ws, R, col, nm_rates[yr_i], fmt=PCT)
                else:
                    C(ws, R, col, '', fmt=PCT)
            for i in range(proj_n):
                ri = 3 + i
                if ri < len(nm_rates):
                    I(ws, R, FY0 + 1 + i, nm_rates[ri], fmt=PCT)
            C(ws, R, 3, '  NM', font=itf)
            R += 1
            # NI = Rev × NM (same pattern as GP = Rev × GM)
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                CF(ws, R, ci, f'=IFERROR({cl}{result["rev_r"]}*{cl}{_nm_r},"")', fmt=NUM)
            C(ws, R, 3, '  NI', font=bf)
            line_ni_r = R; R += 1

        # ── Check Rev: at end of line section, Q→Y + split verification ──
        check_rev_r = 0
        if lrev_row and s1_rev_row and split_r:
            for col in (DS, DS + 1, FY0):
                _chk_gap(ws, R, col, result['rev_r'], lrev_row)
            for ci in range(FY0 + 1, LC_ANNUAL + 1):
                _chk_gap(ws, R, ci, result['rev_r'], lrev_row)
            gm_fy0 = gm.get('fy0', 0)
            gm_label = f' ({gm_fy0:.0%} ' + ('EBITDA margin' if is_ebitda_depth else 'GM') + ')' if gm_fy0 else ''
            C(ws, R, 3, f'  Check Rev{gm_label}', font=itf)
            ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
            check_rev_r = R; R += 1

        result['gm_r'] = gm_r
        result['gp_r'] = gp_r
        result['op_r'] = line_op_r
        result['ni_r'] = 0  # NI depth removed
        result['next_R'] = R
        L[ln] = result
        # Protect Rev, GM, GP, OI, NI from D/E clear
        protected_rows.update([result['rev_r'], gm_r, gp_r])
        if line_op_r: protected_rows.add(line_op_r)
        # line_ni_r protection removed
        # Store check row refs for agent diagnosis (Section 2: Check Rev + Util only)
        result['check_rev_r'] = check_rev_r
        result['check_util_r'] = check_util_r
        if check_rev_r: protected_rows.add(check_rev_r)
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
                        # Fallback: use annual volume for this Q's FY (divided evenly across 4 Qs)
                        fy_year = q_start_yr + (q_start_q - 1 + qi) // 4
                        fy_ofs = fy_year - bfyr - 1  # 0=FY26, 1=FY27, ...
                        vp_arr = ll.get('q_volume', ll['volume']['proj'])
                        ann_vol = vp_arr[min(max(0, fy_ofs), len(vp_arr) - 1)]
                        I(ws, result['vol_r'], col, round(ann_vol / 4), fmt=INT)
                # Q ASP row (first tier, mirrors annual ASP) — pre-fill from annual or q_history
                asp_r = result.get('asp_rows', [0])[0] if result.get('asp_rows') else 0
                if asp_r:
                    t0 = ll['tiers'][0]
                    # BBE tiers: use asp_base for Q distribution (same as driver)
                    if any(k in t0 for k in ('asp_bull', 'asp_base', 'asp_bear')):
                        asp_arr = t0.get('asp_base', t0.get('asp', [0]))
                    else:
                        asp_arr = t0.get('asp', t0.get('asp_base', [0]))
                    # If tier has no explicit asp_fy0, asp_arr[0] is FY0, proj starts at [1]
                    asp_offset = 0 if 'asp_fy0' in t0 else 1
                    asp_fy0_val = t0.get('asp_fy0') or asp_arr[0]
                    for qi in range(q_actual_n + q_proj_n):
                        col = Q_START + qi
                        q_asp = q_hist.get(f'q{qi+1}', {}).get('asp')  # check all Qs
                        if q_asp is not None:
                            I(ws, asp_r, col, q_asp, fmt=DEC)
                        elif qi < q_actual_n:
                            I(ws, asp_r, col, asp_fy0_val, fmt=DEC)
                        else:
                            # Fallback: use annual ASP for the Q's fiscal year
                            fy_year = q_start_yr + (q_start_q - 1 + qi) // 4
                            fy_ofs = fy_year - bfyr  # 0=FY0, 1=FY26, ...
                            if asp_offset:
                                ap_idx = min(fy_ofs, len(asp_arr) - 1)  # arr[0]=FY0
                            else:
                                ap_idx = min(max(0, fy_ofs - 1), len(asp_arr) - 1)  # arr[0]=FY26
                            I(ws, asp_r, col, asp_arr[ap_idx], fmt=DEC)
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
                    # Non-core: use q_history hardcodes for all Qs (residual distribution avoids chain compounding)
                    if ln == 'Non-core' and qi < q_actual_n:
                        qv = q_hist.get(f'q{qi+1}', {}).get('rev')
                        if qv is not None:
                            I(ws, result['rev_r'], col, sc(qv), fmt=NUM)
                        elif anchor_row:
                            C(ws, result['rev_r'], col, f'={cl}{anchor_row}', fmt=NUM)
                    elif ln in one_to_one and anchor_row and is_q_actual:
                        C(ws, result['rev_r'], col, f'={cl}{anchor_row}', fmt=NUM)
                    elif is_q_actual:
                        # non-1:1 actual Q: q_history rev or S1 anchor
                        qv = q_hist.get(f'q{qi+1}', {}).get('rev')
                        if qv is not None:
                            I(ws, result['rev_r'], col, sc(qv), fmt=NUM)
                        elif anchor_row:
                            C(ws, result['rev_r'], col, f'={cl}{anchor_row}', fmt=NUM)
                    elif ln == 'Non-core':
                        # Non-core proj Q: use q_history hardcode (residual avoids chain compounding)
                        qv = q_hist.get(f'q{qi+1}', {}).get('rev')
                        if qv is not None:
                            I(ws, result['rev_r'], col, sc(qv), fmt=NUM)
                        else:
                            # fallback to chain formula
                            pl = get_column_letter(col - 1)
                            CF(ws, result['rev_r'], col,
                               f'={pl}{result["rev_r"]}*(1+{cl}{ya})', fmt=NUM)
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
                for qi in range(Q_START, Q_END + 1):
                    cl = get_column_letter(qi)
                    CF(ws, line_op_r, qi, f'=IFERROR({cl}{result["rev_r"]}*{cl}{_om_r},"")', fmt=NUM)
        # ── Check rows: extend Check Rev to Q columns ──
        if has_q:
            for scan_r in range(result['rev_r'], R):
                cv = str(ws.cell(row=scan_r, column=3).value or '')
                if 'Check Rev' in cv and lrev_row:
                    for qi in range(q_actual_n + q_proj_n):
                        col = Q_START + qi; cl = get_column_letter(col)
                        _chk_gap(ws, scan_r, col, result['rev_r'], lrev_row)

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
            if s1c:
                CF(ws, s1c, ci, f'=IFERROR({cl}{s1r}-{cl}{s1g},"")', fmt=NUM)
            CF(ws, s1g, ci, '=' + '+'.join(
                [f'{cl}{L[ln["name"]]["gp_r"]}' for ln in lls] +
                ([f'{sc(res_val)}*{res_gm}'] if res_val else [])), fmt=NUM)
            if s1gm:
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
                if s1c:
                    CF(ws, s1c, ci, f'=IFERROR({cl}{s1r}-{cl}{s1g},"")', fmt=NUM)
                CF(ws, s1g, ci, '=' + '+'.join(
                    [f'{cl}{L[ln["name"]]["gp_r"]}' for ln in lls] +
                    ([f'{sc(res_val)}*{res_gm}'] if res_val else [])), fmt=NUM)
                if s1gm:
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

        # Write Segment Check formulas (multi-line segments only)
        seg_check_gp_r = si.get('seg_check_gp_r', 0)
        seg_check_op_r = si.get('seg_check_op_r', 0)
        if seg_check_gp_r:
            for ci in range(DS, ALL_END + 1):
                cl = get_column_letter(ci)
                line_sum = '+'.join([f'{cl}{L[l["name"]]["gp_r"]}' for l in lls])
                if res_val:
                    line_sum += f'+{sc(round(res_val * res_gm))}'
                CF(ws, seg_check_gp_r, ci,
                   f'=IFERROR(({line_sum}-{cl}{s1g})/ABS({cl}{s1g}),"")', fmt=PCT)
        if seg_check_op_r:
            op_lls = [l for l in lls if L[l['name']].get('op_r')]
            if op_lls:
                for ci in range(DS, ALL_END + 1):
                    cl = get_column_letter(ci)
                    line_sum = '+'.join([f'{cl}{L[l["name"]]["op_r"]}' for l in op_lls])
                    CF(ws, seg_check_op_r, ci,
                       f'=IFERROR(({line_sum}-{cl}{s1_op})/ABS({cl}{s1_op}),"")', fmt=PCT)

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
        # Annual columns: add full annual residual
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            old_rev = ws.cell(row=nc_rev_r, column=ci).value or ''
            old_gp = ws.cell(row=nc_gp_r, column=ci).value or ''
            if isinstance(old_rev, str) and old_rev.startswith('='):
                CF(ws, nc_rev_r, ci, old_rev + f'+{sc(total_residual)}', fmt=NUM)
            if isinstance(old_gp, str) and old_gp.startswith('='):
                CF(ws, nc_gp_r, ci, old_gp + f'+{sc(gp_residual)}', fmt=NUM)
        # Q columns: add residual_per_q to chain formulas only (hardcoded values already include it)
        if has_q:
            residual_per_q = round(total_residual / 4)
            gp_residual_per_q = round(gp_residual / 4)
            for qi in range(q_actual_n + q_proj_n):
                col = Q_START + qi; cl = get_column_letter(col)
                old_rev = ws.cell(row=nc_rev_r, column=col).value or ''
                old_gp = ws.cell(row=nc_gp_r, column=col).value or ''
                if isinstance(old_rev, str) and old_rev.startswith('='):
                    CF(ws, nc_rev_r, col, old_rev + f'+{sc(residual_per_q)}', fmt=NUM)
                if isinstance(old_gp, str) and old_gp.startswith('='):
                    CF(ws, nc_gp_r, col, old_gp + f'+{sc(gp_residual_per_q)}', fmt=NUM)

    # EBITDA depth: Non-core Corporate - zero revenue + absorb company ebitda gap
    nc = None
    if is_ebitda_depth:
        _nc_key = next((k for k in L.keys() if 'Non-core' in k), None)
        nc = L[_nc_key] if _nc_key else None
    if nc is not None:
        nc_rev_r = nc.get('rev_r', 0)
        nc_gp_r = nc.get('gp_r', 0)
        # Zero out Revenue (Non-core has no revenue)
        if nc_rev_r:
            for ci in range(DS, ALL_END + 1):
                A(ws, nc_rev_r, ci, 0, fmt=NUM)
        # Write EBITDA = company gap
        if nc_gp_r:
            for fy_idx, fy_key, col in [(0,'fy-2',DS),(1,'fy-1',DS+1),(2,'fy0',FY0)]:
                seg_sum = sum(s.get(fy_key,{}).get('ebitda',0) for s in cfg.get('segments',[]))
                cv = cfg['actuals'][fy_key]['ebitda']
                gap_val = round(cv - seg_sum)
                if gap_val:
                    A(ws, nc_gp_r, col, sc(gap_val), fmt=NUM)
            # Q gap = company Q ebitda - Σ seg Q ebitda
            if has_q and 'quarters' in cfg:
                for i, qk in enumerate(['q1','q2','q3','q4']):
                    cq = cfg['quarters'].get(qk, {})
                    q_company = cq.get('ebitda', 0)
                    q_seg = sum(s.get('quarters',{}).get(qk,{}).get('ebitda',0) for s in cfg.get('segments',[]))
                    q_gap = round(q_company - q_seg)
                    if q_gap:
                        A(ws, nc_gp_r, Q_START + i, sc(q_gap), fmt=NUM)

    # ── Q Columns: post-Fill GM + opm extension ──
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
            # OPM → Q columns (1:1 actual Qs use S1 (GP−OP)/Rev)
            om_arr = ll.get('opm') or gl.get('opm', [])
            cur_yr, cur_q = q_start_yr, q_start_q
            for scan_r in range(rev_r, rows.get('op_r', rev_r + 6)):
                cv = str(ws.cell(row=scan_r, column=3).value or '')
                if 'OPM' in cv:
                    for qi in range(Q_START, Q_END + 1):
                        cl = get_column_letter(qi)
                        is_q_actual = qi < Q_START + q_actual_n
                        if (ln in one_to_one) and s1_gp_row and s1_op_row and s1_rev_row and is_q_actual:
                            CF(ws, scan_r, qi, f'=IFERROR(({cl}{s1_gp_row}-{cl}{s1_op_row})/{cl}{s1_rev_row},"")', fmt=PCT)
                        else:
                            _py = cur_yr - bfyr - 1
                            _idx = max(0, min(2 + _py + 1, len(om_arr) - 1))
                            I(ws, scan_r, qi, om_arr[_idx], fmt=PCT)
                        cur_q += 1
                        if cur_q > 4: cur_q = 1; cur_yr += 1
                    break

    # Collapse Section 1 (segment rows only)
    ws.row_dimensions.group(s1_start, s1_end, outline_level=1, hidden=True)

    # ═══════════════ Overall rates ═══════════════
    s2_end = R  # Section 2 ends before Global; D/E clear stops here
    R += 1  # blank row
    # Overall Opex/Rev (GP depth only — Opex is derived for OP/EBITDA depth)
    opex_r = 0
    if meta.get('p&l_depth') == 'gp':
        for ci in range(DS, ALL_END + 1):
            C(ws, R, ci, 0, fmt=PCT)
        C(ws, R, 2, 'Overall', font=bf)
        C(ws, R, 3, 'Opex/Rev', font=nf)
        opex_r = R; R += 1
    # Overall (OI-NI)/Rev (all depths)
    for ci in range(DS, ALL_END + 1):
        C(ws, R, ci, 0, fmt=PCT)
    C(ws, R, 2, 'Overall', font=bf)
    C(ws, R, 3, '(OI-NI)/Rev', font=nf)
    tax_r = R; R += 1

    # ═══ Hidden Bridge: actuals + gap formulas (all depths, collapsed) ═══
    R += 1
    _ds_col = get_column_letter(DS)
    _fy0_col = get_column_letter(FY0)
    gap_gp_ref = gap_oi_ref = gap_ni_ref = tax_rate_ref = '0'
    rev_act_r = gp_act_r = op_act_r = ebitda_act_r = ni_act_r = tax_act_r = da_act_r = 0
    rev_act_cells = gp_act_cells = op_act_cells = ebitda_act_cells = ni_act_cells = tax_act_cells = da_act_cells = {}
    q_act_cells = {}

    # Helper for Q actuals, reusable
    def _q_act(mkey, qkey):
        if not has_q: return
        q_act_cells[qkey] = {}
        for _qi, _qk in enumerate(['q1','q2','q3','q4'][:min(q_actual_n,4)]):
            _v = cfg.get('quarters',{}).get(_qk,{}).get(mkey,0)
            if not _v:
                _v = sum(_s.get('quarters',{}).get(_qk,{}).get(mkey,0) for _s in cfg.get('segments',[]))
            if _v: I(ws, R, Q_START+_qi, sc(_v), fmt=NUM)
            q_act_cells[qkey][_qk] = R

    # Rev actuals (all depths)
    for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
        I(ws, R, ci, sc(cfg['actuals'][fy]['rev']), fmt=NUM)
    C(ws, R, 3, '  actuals Rev', font=itf)
    _q_act('rev', 'Revenue')
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    rev_act_r = R
    rev_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
    R += 1

    # GP actuals (all depths)
    for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
        I(ws, R, ci, sc(cfg['actuals'][fy].get('gp', 0)), fmt=NUM)
    C(ws, R, 3, '  actuals GP', font=itf)
    _q_act('gp', 'GP')
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    gp_act_r = R
    gp_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
    R += 1

    # OI actuals (OP + EBITDA depth)
    if not is_gp_depth:
        for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
            I(ws, R, ci, sc(cfg['actuals'][fy].get('op', 0)), fmt=NUM)
        C(ws, R, 3, '  actuals OI', font=itf)
        _q_act('op', 'OI')
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        op_act_r = R
        op_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
        R += 1

    # EBITDA depth extras: ebitda, ni, tax actuals + gap formulas
    if is_ebitda_depth:
        for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
            I(ws, R, ci, sc(cfg['actuals'][fy].get('ebitda', 0)), fmt=NUM)
        C(ws, R, 3, '  actuals EBITDA', font=itf)
        _q_act('ebitda', 'EBITDA')
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        ebitda_act_r = R
        ebitda_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
        R += 1

        for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
            I(ws, R, ci, sc(cfg['actuals'][fy].get('ni', 0)), fmt=NUM)
        C(ws, R, 3, '  actuals NI', font=itf)
        _q_act('ni', 'NI')
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        ni_act_r = R
        ni_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
        R += 1

        for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
            I(ws, R, ci, sc(cfg['actuals'][fy].get('tax', 0)), fmt=NUM)
        C(ws, R, 3, '  actuals Tax', font=itf)
        _q_act('tax', 'Tax')
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        tax_act_r = R
        tax_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
        R += 1

        for ci, fy in [(DS, 'fy-2'), (DS + 1, 'fy-1'), (FY0, 'fy0')]:
            I(ws, R, ci, sc(cfg['actuals'][fy].get('da', 0)), fmt=NUM)
        C(ws, R, 3, '  actuals D&A', font=itf)
        _q_act('da', 'D&A')
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        da_act_r = R
        da_act_cells = {fy: f'{get_column_letter(col)}{R}' for fy, col in [('fy-2', DS), ('fy-1', DS + 1), ('fy0', FY0)]}
        R += 1

        # Gap formulas (Excel, FY0 single-year anchor — stable for modeling)
        C(ws, R, DS, f'=({ebitda_act_cells["fy0"]}-{gp_act_cells["fy0"]})/{rev_act_cells["fy0"]}', fmt=PCT)
        C(ws, R, 3, '  gap_gp (EBITDA→GP)', font=itf)
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        gap_gp_ref = f'${_ds_col}${R}'; R += 1

        C(ws, R, DS, f'=({ebitda_act_cells["fy0"]}-{op_act_cells["fy0"]})/{rev_act_cells["fy0"]}', fmt=PCT)
        C(ws, R, 3, '  gap_oi (EBITDA→OI)', font=itf)
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        gap_oi_ref = f'${_ds_col}${R}'; R += 1

        C(ws, R, DS, f'=({op_act_cells["fy0"]}-{ni_act_cells["fy0"]})/{rev_act_cells["fy0"]}', fmt=PCT)
        C(ws, R, 3, '  gap_ni (OI→NI)', font=itf)
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        gap_ni_ref = f'${_ds_col}${R}'; R += 1

        C(ws, R, DS, f'={tax_act_cells["fy0"]}/{op_act_cells["fy0"]}', fmt=PCT)
        C(ws, R, 3, '  tax_rate', font=itf)
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        tax_rate_ref = f'${_ds_col}${R}'; R += 1



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
    # Q columns: Non-core already absorbs residual_per_q, no extra term needed
    q_residual_term = ''
    q_gp_residual_term = ''

    # Total Revenue (all years Σ line rev)
    for ci in range(DS, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + residual_term,
          fmt=NUM)
    if has_q:
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi)
            C(ws, R, qi, '=' + '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + q_residual_term,
              fmt=NUM)
    C(ws, R, 3, 'Revenue', font=bf)
    trev = R; R += 1

    # Check Rev: (model sum - actual total rev) / actual total rev → gap%
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        term = q_residual_term if ci >= Q_START else residual_term
        model_sum = '+'.join([f'{cl}{L[ln]["rev_r"]}' for ln in LN]) + term
        CF(ws, R, ci,
           f'=IFERROR(({model_sum}-{cl}{trev})/ABS({cl}{trev}),"")', fmt=PCT)
    # Revenue YoY
    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{trev}/{cl_d}{trev}-1,"")', fmt=PCT)
    for ci in range(FY0, ALL_END + 1):
        cl = get_column_letter(ci)
        if has_q and ci >= Q_START:
            # Q columns: YoY (4Q back) if year-ago exists, else blank
            if ci - 4 >= Q_START:
                pl = get_column_letter(ci - 4)
            else:
                continue
        else:
            # Annual columns: YoY = current/prior year - 1
            pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{trev}/{pl}{trev}-1,"")', fmt=PCT)
    C(ws, R, 3, 'Rev YoY', font=nf)
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

    # ═══ P&L: Cost → GM → GP (GP row pre-computed for forward ref) ═══
    # GP will be at R+2 (after Cost, GM)
    _gp_future = R + 2

    # Cost = Rev - GP
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{trev}-{cl}{_gp_future},"")', fmt=NUM)
    C(ws, R, 3, 'Cost', font=bf)
    R += 1

    # GM = GP / Rev
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{_gp_future}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'GM', font=nf)
    R += 1

    # GP (all depths, all years formula)
    for ci in range(DS, LC_ANNUAL + 1):
        cl = get_column_letter(ci)
        if is_ebitda_depth:
            line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term
            C(ws, R, ci, f'={line_sum}-{cl}{trev}*{gap_gp_ref}', fmt=NUM)
        else:
            C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term, fmt=NUM)
    if has_q:
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi)
            if is_ebitda_depth:
                line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + q_gp_residual_term
                C(ws, R, qi, f'={line_sum}-{cl}{trev}*{gap_gp_ref}', fmt=NUM)
            else:
                C(ws, R, qi, '=' + '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + q_gp_residual_term, fmt=NUM)
    C(ws, R, 3, 'GP', font=bf)
    tgp = R; gp_row = R if is_ebitda_depth else 0
    R += 1

    # GP YoY
    _gp_yoy_ref = gp_row if is_ebitda_depth else tgp
    C(ws, R, DS, '', fmt=PCT)
    _gpe = get_column_letter(DS + 1); _gpd = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({_gpe}{_gp_yoy_ref}/{_gpd}{_gp_yoy_ref}-1,"")', fmt=PCT)
    _gf0 = get_column_letter(FY0); _gf1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({_gf0}{_gp_yoy_ref}/{_gf1}{_gp_yoy_ref}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{_gp_yoy_ref}/{pl}{_gp_yoy_ref}-1,"")', fmt=PCT)
    C(ws, R, 3, 'GP YoY', font=nf)
    R += 1
    # GP QoQ
    if has_q:
        for ci in range(DS, LC_ANNUAL + 1):
            C(ws, R, ci, '', fmt=PCT)
        for qi in range(Q_START, Q_END + 1):
            cl = get_column_letter(qi); pl = get_column_letter(qi - 1)
            if qi == Q_START: C(ws, R, qi, '', fmt=PCT)
            else: C(ws, R, qi, f'=IFERROR({cl}{_gp_yoy_ref}/{pl}{_gp_yoy_ref}-1,"")', fmt=PCT)
        C(ws, R, 3, '  GP QoQ', font=itf)
        R += 1

    _gp_ref = tgp  # GP row for Cost/GM/Opex formulas
    nci_rate = meta.get('nci_rate', 0)
    net_debt = meta.get('net_debt', 0)

    # Opex = GP - OI (OI = R + 1)
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{_gp_ref}-{cl}{R + 1},"")', fmt=NUM)
    C(ws, R, 3, 'Opex', font=bf)
    R += 1

    # OI (depth-aware: GP=A/F, OP=F/F, EBITDA=F/F)
    if is_gp_depth:
        # GP depth: OI not from lines — keep actuals for historical, global OPM for projected
        A(ws, R, DS, sc(a['fy-2']['op']), fmt=NUM)
        A(ws, R, DS + 1, sc(a['fy-1']['op']), fmt=NUM)
        A(ws, R, FY0, sc(a['fy0']['op']), fmt=NUM)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{tgp}-{cl}{trev}*{cl}{opex_r}', fmt=NUM)
        if has_q:
            for qi in range(q_actual_n):
                qk = f'q{qi+1}'
                qv = sum(seg.get('quarters', {}).get(qk, {}).get('op', 0) for seg in segments)
                if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('op', 0)
                if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
            for qi in range(Q_START + q_actual_n, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{tgp}-{cl}{trev}*{cl}{opex_r}', fmt=NUM)
    elif is_op_depth:
        # OP depth: OI = Σ line OI (all years formula, =ΣQ for complete 4Q years)
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, '=' + '+'.join([f'{cl}{L[ln]["op_r"]}' for ln in LN if L[ln].get('op_r')]), fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, '=' + '+'.join([f'{cl}{L[ln]["op_r"]}' for ln in LN if L[ln].get('op_r')]), fmt=NUM)
    else:
        # EBITDA depth: OI = Σ line EBITDA − Rev × gap_oi (=ΣQ for complete 4Q years)
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term
            C(ws, R, ci, f'={line_sum}-{cl}{trev}*{gap_oi_ref}', fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + q_gp_residual_term
                C(ws, R, qi, f'={line_sum}-{cl}{trev}*{gap_oi_ref}', fmt=NUM)
    C(ws, R, 3, 'OI', font=bf)
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
    C(ws, R, 3, 'OI YoY', font=nf)
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

    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{op}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'OPM', font=nf)
    _opex_end = R; R += 1

    # D&A (EBITDA depth: F/F = Rev×gap_oi; GP/OP depth: A/F = OI-ratio)
    _ebitda_start = R
    if is_ebitda_depth:
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{trev}*{gap_oi_ref}', fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{trev}*{gap_oi_ref}', fmt=NUM)
        da_actuals_r = 0
    else:
        da_fy2 = a['fy-2'].get('da', 0); da_fy1 = a['fy-1'].get('da', 0)
        da_fy0 = a['fy0'].get('da', 0)
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
    C(ws, R, 3, 'D&A', font=bf)
    da_r = R; R += 1

    ebitda_r = R
    if is_ebitda_depth:
        # EBITDA depth: = Σ line EBITDA (all years formula, =ΣQ for complete 4Q)
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + gp_residual_term
            C(ws, R, ci, f'={line_sum}', fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                line_sum = '+'.join([f'{cl}{L[ln]["gp_r"]}' for ln in LN]) + q_gp_residual_term
                C(ws, R, qi, f'={line_sum}', fmt=NUM)
    else:
        # GP/OP depth: EBITDA = OI + D&A
        for ci in range(DS, ALL_END + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{op}+{cl}{da_r}', fmt=NUM)
    C(ws, R, 3, 'EBITDA', font=bf)
    R += 1
    # EBITDA YoY (all depths)
    C(ws, R, DS, '', fmt=PCT)
    _ebe = get_column_letter(DS + 1); _ebd = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({_ebe}{ebitda_r}/{_ebd}{ebitda_r}-1,"")', fmt=PCT)
    _ebf0 = get_column_letter(FY0); _ebf1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({_ebf0}{ebitda_r}/{_ebf1}{ebitda_r}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{ebitda_r}/{pl}{ebitda_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'EBITDA YoY', font=nf)
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

    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ebitda_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'EBITDA margin', font=nf)
    _ebitda_end = R; R += 1

    # Tax + NI (EBITDA depth: F/F gap-derived; GP/OP depth: A/F)
    nm_val = gl.get('tax_rate', 0)  # global NM assumption
    _ni_start = R
    if is_ebitda_depth:
        # EBITDA depth: Tax = OI × tax_rate (all years formula)
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{op}*{tax_rate_ref}', fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{op}*{tax_rate_ref}', fmt=NUM)
    else:
        # GP/OP depth: Tax = OI − NI (historical actuals, projected formula)
        A(ws, R, DS, sc(a['fy-2'].get('tax', 0)), fmt=NUM)
        A(ws, R, DS + 1, sc(a['fy-1'].get('tax', 0)), fmt=NUM)
        A(ws, R, FY0, sc(a['fy0'].get('tax', 0)), fmt=NUM)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{op}-({cl}{trev}*{nm_val})', fmt=NUM)
        if has_q:
            for qi in range(q_actual_n):
                qk = f'q{qi+1}'
                qv = sum(seg.get('quarters', {}).get(qk, {}).get('tax', 0) for seg in segments)
                if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('tax', 0)
                cl = get_column_letter(Q_START + qi)
                if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
                else: C(ws, R, Q_START + qi, f'={cl}{op}-({cl}{trev}*{nm_val})', fmt=NUM)
            for qi in range(Q_START + q_actual_n, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{op}-({cl}{trev}*{nm_val})', fmt=NUM)
    C(ws, R, 3, 'Tax', font=bf)
    tv = R; R += 1

    if is_ebitda_depth:
        # EBITDA depth: NI = OI − Rev × gap_ni (all years formula)
        for ci in range(DS, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{op}-{cl}{trev}*{gap_ni_ref}', fmt=NUM)
        if has_q:
            for qi in range(Q_START, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{op}-{cl}{trev}*{gap_ni_ref}', fmt=NUM)
    else:
        # GP/OP depth: NI = Rev × NM (historical actuals, projected formula)
        A(ws, R, DS, sc(a['fy-2']['ni']), fmt=NUM)
        A(ws, R, DS + 1, sc(a['fy-1']['ni']), fmt=NUM)
        A(ws, R, FY0, sc(a['fy0']['ni']), fmt=NUM)
        for ci in range(FY0 + 1, LC_ANNUAL + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{trev}*{nm_val}', fmt=NUM)
        if has_q:
            for qi in range(q_actual_n):
                qk = f'q{qi+1}'
                qv = sum(seg.get('quarters', {}).get(qk, {}).get('ni', 0) for seg in segments)
                if not qv: qv = cfg.get('quarters', {}).get(qk, {}).get('ni', 0)
                cl = get_column_letter(Q_START + qi)
                if qv: A(ws, R, Q_START + qi, sc(qv), fmt=NUM)
                else: C(ws, R, Q_START + qi, f'={cl}{trev}*{nm_val}', fmt=NUM)
            for qi in range(Q_START + q_actual_n, Q_END + 1):
                cl = get_column_letter(qi)
                C(ws, R, qi, f'={cl}{trev}*{nm_val}', fmt=NUM)
    C(ws, R, 3, 'Net Income', font=bf)
    ni_r = R; R += 1

    if nci_rate > 0:
        for ci in range(DS, ALL_END + 1):
            cl = get_column_letter(ci)
            C(ws, R, ci, f'={cl}{ni_r}*(1-{nci_rate})', fmt=NUM)
        C(ws, R, 3, 'NI attributable')
        ni_r = R; R += 1

    C(ws, R, DS, '', fmt=PCT)
    cl_e = get_column_letter(DS + 1); cl_d = get_column_letter(DS)
    C(ws, R, DS + 1, f'=IFERROR({cl_e}{ni_r}/{cl_d}{ni_r}-1,"")', fmt=PCT)
    for ci in range(FY0, ALL_END + 1):
        cl = get_column_letter(ci)
        if has_q and ci >= Q_START and ci - 4 >= Q_START:
            pl = get_column_letter(ci - 4)
        elif has_q and ci >= Q_START:
            continue
        else:
            pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{pl}{ni_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'NI YoY', font=nf)
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
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        C(ws, R, ci, f'=IFERROR({cl}{ni_r}/{cl}{trev},"")', fmt=PCT)
    C(ws, R, 3, 'NPM', font=nf)
    R += 1
    _ni_end = R; R += 1

    # ═══ P&L Checks (consolidated at bottom, collapsed) ═══
    # Each Check: (P&L formula row - bridge actuals) / ABS(bridge actuals)
    # Historical years have actuals; projected years blank
    def _write_check(ref_r, act_cells, label):
        # FY checks (D/E/F columns)
        for ci in range(DS, ALL_END + 1):
            cl = get_column_letter(ci)
            if ci == DS: cell = act_cells.get('fy-2', '')
            elif ci == DS + 1: cell = act_cells.get('fy-1', '')
            elif ci == FY0: cell = act_cells.get('fy0', '')
            else: cell = ''
            if cell:
                C(ws, R, ci, f'=IFERROR(({cl}{ref_r}-{cell})/ABS({cell}),"")', fmt=PCT)
            else:
                C(ws, R, ci, '', fmt=PCT)
        # Q checks (N/Q_START... columns, when Q actuals exist)
        q_ok = has_q and label in q_act_cells and q_actual_n > 0
        if q_ok:
            for qi in range(min(q_actual_n, 4)):
                qk = f'q{qi+1}'; qc = Q_START + qi; cl = get_column_letter(qc)
                br = q_act_cells.get(label, {}).get(qk, 0)
                if br:
                    C(ws, R, qc, f'=IFERROR(({cl}{ref_r}-{cl}{br})/ABS({cl}{br}),"")', fmt=PCT)
                else:
                    C(ws, R, qc, '', fmt=PCT)
        C(ws, R, 3, f'  Check {label}', font=itf)
        ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
        return R + 1

    R = _write_check(trev, rev_act_cells, 'Revenue')
    R = _write_check(tgp, gp_act_cells, 'GP')
    if not is_gp_depth:
        R = _write_check(op, op_act_cells, 'OI')
    if is_ebitda_depth:
        R = _write_check(ebitda_r, ebitda_act_cells, 'EBITDA')
        R = _write_check(da_r, da_act_cells, 'D&A')
        R = _write_check(tv, tax_act_cells, 'Tax')
        R = _write_check(ni_r, ni_act_cells, 'NI')


    # ── Inline Check columns: per-row Annual−QSum at existing rows (S1-S3) ──
    if has_q:
        cur_yr, cur_q, qi = q_start_yr, q_start_q, 0
        total_q = q_actual_n + q_proj_n
        SKIP_KW = ('YoY', 'QoQ', 'GM', 'OPM', 'NPM', 'NM', 'margin', '/ Rev', '%', 'Check', 'Implied', 'Bull', 'Base', 'Bear', 'ASP', 'Shares', '(OI', 'NI)/', 'gap_', 'tax_rate', 'Line Revenue', 'actuals')
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
                        ws.cell(row=row, column=chk_col).value = f'=IFERROR(({ac}{row}-({q_sum_f.format(r=row)}))/ABS({ac}{row}),"")'
                        ws.cell(row=row, column=chk_col).number_format = PCT
                        ws.cell(row=row, column=chk_col).font = nf
                    ws.column_dimensions[cc].width = 12
                    ws.column_dimensions.group(cc, cc, outline_level=1, hidden=True)
            qi += fyc; cur_yr += 1; cur_q = 1

    # ── Fix Overall Opex/Rev formulas (GP depth only) ──
    if meta.get('p&l_depth') == 'gp':
        for ci in [DS, DS + 1, FY0]:
            cl = get_column_letter(ci)
            CF(ws, opex_r, ci, f'=IFERROR({cl}{op}/{cl}{trev},"")', fmt=PCT)
        for i, ov_val in enumerate(gl.get('opm', [0]*8)[3:], FY0 + 1):
            I(ws, opex_r, i, ov_val, fmt=PCT)
        if has_q:
            _opms = gl.get('opm', [0.25]*8)
            cur_yr, cur_q = q_start_yr, q_start_q
            for qi in range(q_actual_n + q_proj_n):
                _py = cur_yr - bfyr - 1
                if _py < 0: _py = 0
                _idx = min(3 + _py, len(_opms) - 1)
                I(ws, opex_r, Q_START + qi, _opms[_idx], fmt=PCT)
            cur_q += 1
            if cur_q > 4: cur_q = 1; cur_yr += 1
    # Overall (OI-NI)/Rev: historical = (OI-NI)/Rev, FY26+ from assumption
    for ci in [DS, DS + 1, FY0]:
        cl = get_column_letter(ci)
        CF(ws, tax_r, ci, f'=IFERROR(({cl}{op}-{cl}{ni_r})/{cl}{trev},"")', fmt=PCT)
    nm_val = gl.get('tax_rate', 0)
    for ci in range(FY0 + 1, LC_ANNUAL + 1):
        I(ws, tax_r, ci, nm_val, fmt=PCT)
    if has_q:
        for qi in range(q_actual_n + q_proj_n):
            I(ws, tax_r, Q_START + qi, nm_val, fmt=PCT)

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
        default_method = 'ev_ebitda' if is_ebitda_depth else 'pe'
        return s.get('method', default_method), s.get('multiple', 10)

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

    # Detect whether all lines use EV methods (for TOTAL directional logic)
    _all_methods = set()
    for ll in logic_lines:
        _m, _ = _sotp_info(ll)
        _all_methods.add(_m)
    is_ev_method = _all_methods and all(m.startswith('ev_') for m in _all_methods)

    for ll in logic_lines:
        ln = ll['name']
        method, mult = _sotp_info(ll)
        metric_r, metric_label = _sotp_metric_ref(method)
        gc = f'{sc_l}{L[ln]["gp_r"]}'        # line profit (allocation key)
        lr = f'{sc_l}{L[ln]["rev_r"]}'        # line revenue
        mc = f'{sc_l}{metric_r}'              # total metric
        tc_gp = f'{sc_l}{tgp}'                # total profit
        is_ev = method.startswith('ev_')
        is_ps = method in ('ev_sales', 'ps')

        # Revenue (all methods)
        C(ws, R, 2, ln, font=bf)
        C(ws, R, 3, 'Revenue', font=bf)
        C(ws, R, SC, f'={lr}', fmt=NUM)
        R += 1

        # Allocated metric
        if is_ps:
            alloc_formula = f'={lr}'
            alloc_ref = lr
        else:
            alloc_formula = f'=IFERROR({mc}*{gc}/{tc_gp},"")'
            alloc_ref = f'({mc}*{gc}/{tc_gp})'
        C(ws, R, 3, metric_label)
        C(ws, R, SC, alloc_formula, fmt=NUM)
        R += 1

        # Multiple
        if method == 'pe':      label_m = 'PE'
        elif method == 'ps':    label_m = 'P/S'
        else:                   label_m = method.replace('_', '/').upper()
        I(ws, R, SC, mult, fmt='0.0x')
        C(ws, R, 3, label_m, font=nf)
        mult_row = R; R += 1

        # EV or Mkt Cap (no per-line Net Debt)
        value_f = f'=IFERROR({alloc_ref}*{sc_l}{mult_row},"")'
        if is_ev:
            C(ws, R, 3, 'EV', font=bf)
        else:
            C(ws, R, 3, 'Mkt Cap', font=bf)
        C(ws, R, SC, value_f, fmt=DEC)
        mc_rows.append(R); R += 1

    # Blank row before Total section + Enterprise Value → Net Debt → Mkt Cap
    R += 1
    nd_total_r = R + 1  # Net Debt row (forward ref for PE/PS)
    if is_ev_method:
        ev_f = '=' + '+'.join([f'{sc_l}{mr}' for mr in mc_rows])
    else:
        ev_f = '=(' + '+'.join([f'{sc_l}{mr}' for mr in mc_rows]) + f')+{sc_l}{nd_total_r}'
    C(ws, R, 2, 'Total', font=bf)
    C(ws, R, SC, ev_f, fmt=DEC)
    C(ws, R, 3, 'Enterprise Value', font=bf)
    sotp_ev_r = R; R += 1

    # Net Debt
    I(ws, R, SC, net_debt, fmt=DEC)
    C(ws, R, 3, 'Net Debt', font=bf)
    nd_total_r = R; R += 1

    # Mkt Cap (EV method: EV − Net Debt; PE/PS: Σ Mkt Cap)
    if is_ev_method:
        mcap_f = f'=IFERROR({sc_l}{sotp_ev_r}-{sc_l}{nd_total_r},"")'
    else:
        mcap_f = '=' + '+'.join([f'{sc_l}{mr}' for mr in mc_rows])
    C(ws, R, SC, mcap_f, fmt=DEC)
    C(ws, R, 3, 'Mkt Cap', font=bf)
    sotp_mcap_r = R; R += 1

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
        lmethods = [LL_SOTP[l['name']][1] for l in lls]
        w_mult = sum(lmethods[i] * seg['fy0']['rev'] * lls[i]['split']
                     for i in range(len(lls))) / seg['fy0']['rev'] if seg['fy0']['rev'] > 0 else 10
        mult_s = round(w_mult)
        method_s = LL_SOTP[lls[0]['name']][0]
        metric_r_s, metric_label_s = _sotp_metric_ref(method_s)
        gc = f'{sc_l}{seg_info[sn]["gp"]}'
        sr = f'{sc_l}{seg_info[sn]["rev"]}'
        mc = f'{sc_l}{metric_r_s}'
        is_ev_s = method_s.startswith('ev_')
        is_ps_s = method_s in ('ev_sales', 'ps')

        # Revenue
        C(ws, R, 2, sn, font=bf)
        C(ws, R, 3, 'Revenue', font=bf)
        C(ws, R, SC, f'={sr}', fmt=NUM)
        R += 1

        # Allocated metric
        if is_ps_s:
            alloc_f_s = f'={sr}'
            alloc_ref_s = sr
        else:
            alloc_f_s = f'=IFERROR({mc}*{gc}/{sc_l}{tgp},"")'
            alloc_ref_s = f'({mc}*{gc}/{sc_l}{tgp})'
        C(ws, R, 3, metric_label_s)
        C(ws, R, SC, alloc_f_s, fmt=NUM)
        R += 1

        # Multiple
        if method_s == 'pe':      label_ms = 'PE'
        elif method_s == 'ps':    label_ms = 'P/S'
        else:                     label_ms = method_s.replace('_', '/').upper()
        I(ws, R, SC, mult_s, fmt='0.0x')
        C(ws, R, 3, label_ms, font=nf)
        pe_row = R; R += 1

        # EV or Mkt Cap
        value_f_s = f'=IFERROR({alloc_ref_s}*{sc_l}{pe_row},"")'
        if is_ev_s:
            C(ws, R, 3, 'EV', font=bf)
        else:
            C(ws, R, 3, 'Mkt Cap', font=bf)
        C(ws, R, SC, value_f_s, fmt=DEC)
        smc_rows.append(R); R += 1

    # Blank row before Total + Enterprise Value → Net Debt → Mkt Cap
    R += 1
    nd_seg_r = R + 1
    if is_ev_method:
        ev_f_s = '=' + '+'.join([f'{sc_l}{mr}' for mr in smc_rows])
    else:
        ev_f_s = '=(' + '+'.join([f'{sc_l}{mr}' for mr in smc_rows]) + f')+{sc_l}{nd_seg_r}'
    C(ws, R, 2, 'Total', font=bf)
    C(ws, R, SC, ev_f_s, fmt=DEC)
    C(ws, R, 3, 'Enterprise Value', font=bf)
    sotp_seg_ev_r = R; R += 1

    I(ws, R, SC, net_debt, fmt=DEC)
    C(ws, R, 3, 'Net Debt', font=bf)
    nd_seg_r = R; R += 1

    if is_ev_method:
        mcap_f_s = f'=IFERROR({sc_l}{sotp_seg_ev_r}-{sc_l}{nd_seg_r},"")'
    else:
        mcap_f_s = '=' + '+'.join([f'{sc_l}{mr}' for mr in smc_rows])
    C(ws, R, SC, mcap_f_s, fmt=DEC)
    C(ws, R, 3, 'Mkt Cap', font=bf)
    sotp_seg_mcap_r = R; R += 1
    ws.row_dimensions.group(sotp_seg_start, R - 1, outline_level=1, hidden=True)

    # ═══════════════ §6 Market Data ═══════════════
    R += 1
    C(ws, R, 1, 'Market Cap', font=bf12)
    R += 1
    # Key metrics — highlighted (actual market data)
    C(ws, R, 3, 'MCap (Actual)', font=hlfont, fill=hlfill)
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

    # Implied valuation (references SOTP-derived Mkt Cap, not EV)
    if shares:
        implied_logic = f'=IFERROR({sc_l}{sotp_mcap_r}*{div}/{sc_l}{shares_data_r},"")'
        implied_seg = f'=IFERROR({sc_l}{sotp_seg_mcap_r}*{div}/{sc_l}{shares_data_r},"")'
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
            methods.add(ll['sotp'].get('method', 'ev_ebitda' if is_ebitda_depth else 'pe'))
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
        # NI = Rev × NM (NM from global assumption)
        rev_total_sc = f'({rf[1:]})' if rf.startswith('=') else rf
        nf_s = f'={rev_total_sc}*{syc}{tax_r}'
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
        for c in range(DS, ALL_END + 1):
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
            'Revenue', 'Cost', 'GP', 'GM', 'OP', 'OPM', 'OI YoY',
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
    for ci in range(DS, ALL_END + 1):
        cl = get_column_letter(ci)
        ws.column_dimensions[cl].width = 5 if has_q and ci in (LC_ANNUAL + 1, LC_ANNUAL + 2) else 13

    ws.freeze_panes = 'D2'

    out_path = output_path or json_path.replace('.json', '.xlsx')
    wb.save(out_path)
    print(f'OK: {out_path}')

    # ── COM: compute + read Checks, write checks.json with flags ──
    THRESHOLDS = {
        'Check Rev': 0.02, 'Check GP': 0.05, 'Check OI': 0.05,
        'Check EBITDA': 0.05, 'Check D&A': 0.20, 'Check Tax': 0.10, 'Check NI': 0.15,
    }
    if is_ebitda_depth:
        THRESHOLDS['Check GP'] = 0.15; THRESHOLDS['Check OI'] = 0.15
    try:
        xl = win32com.client.Dispatch('Excel.Application')
        time.sleep(0.5)
        wb2 = xl.Workbooks.Open(os.path.abspath(out_path))
        ws2 = wb2.Sheets(1)
        check_data = {}
        q_check_data = {}
        flags_pnl = []; flags_q = []
        year_labels = [cfg['meta'].get('base_fy', 2025) - i for i in [2, 1, 0]]

        # Scan P&L checks (C column labels starting with '  Check ')
        for r in range(1, 3000):
            lab = str(ws2.Cells(r, 3).Value or '')
            if lab.startswith('  Check '):
                clean = lab.strip()
                vals = {}
                for ci, yr in zip([4, 5, 6], year_labels):
                    v = ws2.Cells(r, ci).Value
                    if isinstance(v, float):
                        pct = abs(v)
                        vals[str(yr)] = f'{v:.2%}' if pct < 100 else str(round(v, 1))
                        th = THRESHOLDS.get(clean, 0.10)
                        if pct > th:
                            flags_pnl.append(f'{clean} {yr}={v:.2%} (> {th:.0%})')
                    elif v is None:
                        vals[str(yr)] = '—'
                    else:
                        vals[str(yr)] = str(v)[:20]
                check_data[clean] = vals

        # Scan Q checks (U columns — FY{yr} Check headers, P&L F/F rows only)
        if has_q:
            if is_ebitda_depth:
                PNL_LABELS = {'Revenue', 'Cost', 'GP', 'Opex', 'OI', 'OPM', 'D&A', 'EBITDA', 'Tax', 'Net Income', 'NPM'}
            elif is_op_depth:
                PNL_LABELS = {'Revenue', 'Cost', 'GP', 'Opex', 'OI', 'OPM'}
            else:
                PNL_LABELS = {'Revenue', 'Cost', 'GP'}
            for chk_col in range(Q_END + 3, Q_END + 10):
                hdr = str(ws2.Cells(1, chk_col).Value or '')
                if not hdr.startswith('FY'): break
                fy_label = hdr.replace(' Check', '')
                q_check_data[fy_label] = {}
                for row in range(trev, _ni_end + 1):
                    cv = str(ws2.Cells(row, 3).Value or '').strip()
                    if cv not in PNL_LABELS: continue
                    v = ws2.Cells(row, chk_col).Value
                    if isinstance(v, float):
                        q_check_data[fy_label][cv] = f'{v:.2%}'
                        if abs(v) > 0.0001:
                            flags_q.append(f'{fy_label} {cv}={v:.2%} (ΣQ≠Annual)')
                    elif v is not None:
                        q_check_data[fy_label][cv] = str(v)[:20]

        # qq_checks: COM read P&L Q cells vs bridge Q actuals
        qq_check_data = {}
        if q_act_cells and q_actual_n > 0:
            xl.Calculation = -4105
            xl.CalculateFull()
            time.sleep(2)
            MAP = {'Revenue': trev, 'GP': tgp, 'OI': op, 'EBITDA': ebitda_r, 'NI': ni_r, 'Tax': tv}
            for qi in range(min(q_actual_n, 4)):
                qk = f'q{qi+1}'; qc = Q_START + qi
                qq_check_data[qk] = {}
                for lab, pnl_r in MAP.items():
                    if not pnl_r: continue
                    try:
                        cl = get_column_letter(qc)
                        v = ws2.Range(f'{cl}{pnl_r}').Value
                    except:
                        v = ws2.Cells(pnl_r, qc).Value
                    ar = q_act_cells.get(lab, {}).get(qk, 0)
                    try:
                        av = ws2.Range(f'{get_column_letter(DS)}{ar}').Value if ar else None
                    except:
                        av = ws2.Cells(ar, DS).Value if ar else None
                    if isinstance(v, float) and isinstance(av, float) and abs(av) > 0.01:
                        qq_check_data[qk][lab] = f'{(v - av) / abs(av):.2%}'

        # qq_checks: COM read P&L Q vs bridge actuals
        qq_check_data = {}
        if q_act_cells and q_actual_n > 0:
            xl.CalculateFull()
            time.sleep(2)
            MAP = {'Revenue':trev, 'GP':tgp, 'OI':op, 'EBITDA':ebitda_r, 'NI':ni_r, 'Tax':tv}
            for qi in range(min(q_actual_n, 4)):
                qk = f'q{qi+1}'; qc = Q_START + qi
                qq_check_data[qk] = {}
                for lab, pnl_r in MAP.items():
                    if not pnl_r: continue
                    v = ws2.Cells(pnl_r, qc).Value
                    ar = q_act_cells.get(lab, {}).get(qk, 0)
                    av = ws2.Cells(ar, DS).Value if ar else None
                    if isinstance(v, float) and isinstance(av, float) and abs(av) > 0.01:
                        qq_check_data[qk][lab] = f'{(v - av) / abs(av):.2%}'

        wb2.Close(False)
        xl.Quit()

        cj_path = json_path.replace('.json', '_checks.json')
        result = {
            'generated_at': datetime.datetime.now().isoformat(),
            'model': os.path.basename(out_path),
            'depth': cfg['meta'].get('p&l_depth', '?'),
            'checks': check_data,
            'flags': {'P&L': flags_pnl, 'Q': flags_q},
        }
        if has_q:
            result['q_checks'] = q_check_data
        if qq_check_data:
            result['qq_checks'] = qq_check_data
        with open(cj_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f'  Checks: {cj_path}')
        pl_checks = {k: v for k, v in check_data.items() if '%' not in k}
        for lab, vals in pl_checks.items():
            items = list(vals.items())[:3]
            print(f'    {lab:25s} {" | ".join(f"{k}={v}" for k,v in items)}')
        if flags_pnl:
            print(f'  [!] P&L flags ({len(flags_pnl)}):')
            for f in flags_pnl[:5]: print(f'    {f}')
        if flags_q:
            print(f'  [!] Q flags ({len(flags_q)}):')
            for f in flags_q[:3]: print(f'    {f}')
        if not flags_pnl and not flags_q:
            print(f'  [OK] All checks within threshold')
    except Exception as e:
        print(f'  [COM skip] {e}')


# ═══════════════════════════════════════════════════════════════
# CLI entry
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('json_path')
    p.add_argument('-o', '--output')
    a = p.parse_args()
    build(a.json_path, a.output)
