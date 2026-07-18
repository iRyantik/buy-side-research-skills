"""Migrate old-format test-q-*.json to research-model.json."""
import json, codecs, sys

def migrate(old_path, out_path):
    with codecs.open(old_path, 'r', 'utf-8') as f:
        old = json.load(f)

    meta = old['meta']
    a = old['actuals']
    segs = old['segments']
    lines = old['logic_lines']
    gl = old.get('global', {})

    bfyr = int(meta.get('base_fy', 2025))
    proj_n = int(meta.get('proj_years', 5))
    fy_map_old = {'fy-2': f'FY{bfyr-2}', 'fy-1': f'FY{bfyr-1}', 'fy0': f'FY{bfyr}'}
    proj_fys = [f'FY{bfyr+1+i}E' for i in range(proj_n)]
    all_fys = [f'FY{bfyr-2}', f'FY{bfyr-1}', f'FY{bfyr}'] + proj_fys
    fy0_key = f'FY{bfyr}'  # dynamic, e.g. FY2025 or FY2026
    fy1_key = f'FY{bfyr-1}'
    fy2_key = f'FY{bfyr-2}'

    # Q mapping: q_actual_count=1, q_start_yr=2026, q_start_q=4 → Q4 only
    q_start = int(meta.get('q_start_q', 1))
    q_count = int(meta.get('q_actual_count', 0))
    q_labels = [f'Q{((q_start-1+i)%4)+1}' for i in range(q_count)]

    # ── actuals ──
    act = {'gaap': {'is': {}, 'segments': []}, 'non_gaap': {'is': {}, 'adj': {}, 'segments': []}}

    is_fields = ['rev', 'gp', 'oi', 'ni', 'tax', 'da']
    # Map old format field names to standardized keys
    field_remap = {'op': 'oi'}  # old → new
    for field in is_fields:
        old_field = field_remap.get(field, field)  # old format key
        std_field = field  # standardized key (oi)
        act['gaap']['is'][std_field] = {}
        for old_fy, new_fy in fy_map_old.items():
            v = a[old_fy].get(old_field)
            if v is not None:
                act['gaap']['is'][std_field][new_fy] = {'annual': float(v)}

    # Company non-gaap (OP depth: same as GAAP for Santec)
    act['non_gaap']['is'] = {'oi': {}}
    for old_fy, new_fy in fy_map_old.items():
        v = a[old_fy].get('op')
        if v is not None:
            act['non_gaap']['is']['oi'][new_fy] = {'annual': float(v)}

    # Segments
    for seg in segs:
        s_name = seg['name']
        gs = {'name': s_name, 'rev': {}, 'gp': {}, 'oi': {}}
        if 'name_cn' in seg:
            gs['name_cn'] = seg['name_cn']
        for old_fy, new_fy in fy_map_old.items():
            if old_fy in seg and isinstance(seg[old_fy], dict):
                gs['rev'][new_fy] = {'annual': float(seg[old_fy].get('rev', 0))}
                if 'gp' in seg[old_fy]:
                    gs['gp'][new_fy] = {'annual': float(seg[old_fy]['gp'])}
                if 'op' in seg[old_fy]:
                    gs['oi'][new_fy] = {'annual': float(seg[old_fy]['op'])}
        # Q data
        # Q data — rev, gp, op for OP depth
        for qi in range(q_count):
            qk = f'q{qi+1}'
            if qk in seg.get('quarters', {}):
                qd = seg['quarters'][qk]
                if qd.get('rev'):
                    gs['rev'][fy0_key][q_labels[qi]] = int(qd['rev'])
                if qd.get('gp'):
                    gs['gp'][fy0_key][q_labels[qi]] = int(qd['gp'])
                if qd.get('op'):
                    gs['oi'][fy0_key][q_labels[qi]] = int(qd['op'])
        act['gaap']['segments'].append(gs)

    print(f'  Segments: {[s["name"] for s in act["gaap"]["segments"]]}')

    # ── assumptions ──
    asm_lines = []
    for line in lines:
        entry = {
            'name': line['name'],
            'module': line['module'],
            'segment': '',
            'one_to_one': False,  # Santec: all non-1:1
            'is_segment_core': True,
        }
        # Find segment + split
        for seg in segs:
            for ll in seg.get('logic_lines', []):
                if ll['name'] == line['name']:
                    entry['segment'] = seg['name']
                    entry['split'] = ll.get('split', 0)

        # base_rate (gm -> base_rate)
        gm = line.get('gm', {})
        if gm:
            entry['base_rate'] = {}
            for old_fy, new_fy in fy_map_old.items():
                v = gm.get(old_fy)
                if v is not None:
                    entry['base_rate'][new_fy] = {'annual': round(float(v), 4)}
            for i, v in enumerate(gm.get('proj', [])):
                entry['base_rate'][proj_fys[i]] = {'annual': round(float(v), 4)}

        # yoy: {scenario: [array]} → {scenario: {FY: {annual: val}}}
        yoy = line.get('yoy', {})
        if yoy:
            entry['yoy'] = {}
            for sc in ['bull', 'base', 'bear']:
                arr = yoy.get(sc, [])
                if arr:
                    entry['yoy'][sc] = {}
                    for i, v in enumerate(arr):
                        if i < len(proj_fys):
                            entry['yoy'][sc][proj_fys[i]] = {'annual': round(float(v), 4)}

        # opex_rate: array of 8 → FY-keyed
        opm = line.get('opm', [])
        if opm:
            all_fy_opm = [fy2_key, fy1_key, fy0_key] + proj_fys
            entry['opex_rate'] = {}
            for i, v in enumerate(opm):
                if i < len(all_fy_opm):
                    entry['opex_rate'][all_fy_opm[i]] = {'annual': round(float(v), 4)}

        # module-specific
        if line['module'] == 'vol_asp':
            entry['unit_scale'] = int(line.get('unit_scale', 1000))
            # volume
            entry['volume'] = {}
            for old_fy, new_fy in fy_map_old.items():
                hist = line.get('history', {}).get(old_fy, {})
                v = hist.get('volume')
                if v is not None:
                    entry['volume'][new_fy] = {'annual': float(v)}
            entry['volume'][fy0_key] = {'annual': float(line['volume'].get('fy0', 0))}
            for i, v in enumerate(line['volume'].get('proj', [])):
                entry['volume'][proj_fys[i]] = {'annual': float(v)}
            # Q data
            for qi in range(q_count):
                qk = f'q{qi+1}'
                qh = line.get('q_history', {}).get(qk, {})
                if 'volume' in qh:
                    entry['volume'][fy0_key][q_labels[qi]] = float(qh['volume'])

            # tiers[] → new FY-keyed format
            old_tiers = line.get('tiers', [])
            if old_tiers:
                entry['tiers'] = []
                for ti, t in enumerate(old_tiers):
                    t_name = t.get('name', f'tier{ti}')
                    new_t = {'name': t_name}
                    # share (skip for last residual tier)
                    is_last = (ti == len(old_tiers) - 1)
                    if not is_last and ('share_fy0' in t or 'share_proj' in t):
                        new_t['share'] = {}
                        if 'share_fy0' in t:
                            new_t['share'][fy0_key] = {'annual': float(t['share_fy0'])}
                        for i, v in enumerate(t.get('share_proj', [])):
                            if i < len(proj_fys):
                                new_t['share'][proj_fys[i]] = {'annual': float(v)}
                    # asp (base or simple)
                    asp_key = 'asp_base' if 'asp_base' in t else ('asp_bull' if 'asp_bull' in t else 'asp')
                    new_t['asp'] = {}
                    for old_fy, new_fy in fy_map_old.items():
                        hist = line.get('history', {}).get(old_fy, {})
                        v = hist.get(f'{t_name}_asp', hist.get('asp'))
                        if v is not None:
                            new_t['asp'][new_fy] = {'annual': round(float(v), 1)}
                    asp_arr = t.get(asp_key, [])
                    if 'asp_fy0' in t:
                        new_t['asp'][fy0_key] = {'annual': float(t['asp_fy0'])}
                        for i, v in enumerate(asp_arr):
                            if i < len(proj_fys):
                                new_t['asp'][proj_fys[i]] = {'annual': float(v)}
                    elif asp_arr:
                        new_t['asp'][fy0_key] = {'annual': float(asp_arr[0])}
                        for i, v in enumerate(asp_arr[1:]):
                            if i < len(proj_fys):
                                new_t['asp'][proj_fys[i]] = {'annual': float(v)}
                    # Q asp
                    for qi in range(q_count):
                        qk = f'q{qi+1}'
                        qh = line.get('q_history', {}).get(qk, {})
                        if 'asp' in qh:
                            new_t['asp'][fy0_key][q_labels[qi]] = float(qh['asp'])
                    entry['tiers'].append(new_t)
            else:
                # Single tier fallback: use asp_base
                entry['tiers'] = [{'name': line['name'], 'asp': {}}]
                tier_asps = {}
                ln = line.get('name', '')
                for old_fy, new_fy in fy_map_old.items():
                    hist = line.get('history', {}).get(old_fy, {})
                    v = hist.get('asp', hist.get(ln + '_asp'))
                    if v is not None:
                        tier_asps[new_fy] = {'annual': round(float(v), 1)}
                tier_asps[fy0_key] = {'annual': 30}
                for i, v in enumerate([32, 34, 36, 37, 38]):
                    tier_asps[proj_fys[i]] = {'annual': float(v)}
                for qi in range(q_count):
                    qk = f'q{qi+1}'
                    qh = line.get('q_history', {}).get(qk, {})
                    if 'asp' in qh:
                        tier_asps[fy0_key][q_labels[qi]] = float(qh['asp'])
                entry['tiers'][0]['asp'] = tier_asps

        # sotp
        if line.get('sotp'):
            entry['sotp'] = line['sotp']
        else:
            entry['sotp'] = {'method': 'pe', 'multiple': 15}

        asm_lines.append(entry)

    print(f'  Lines: {[l["name"] for l in asm_lines]}')

    # ── global ──
    global_new = {}
    tax_r = gl.get('tax_rate', 0.3)
    global_new['tax_rate'] = {fy: {'annual': round(float(tax_r), 4)} for fy in all_fys}
    opm = gl.get('opm', [0.25]*8)
    global_new['opex_rev'] = {}
    for i, fy in enumerate(all_fys):
        global_new['opex_rev'][fy] = {'annual': round(float(opm[i]) if i < len(opm) else 0.25, 4)}
    global_new['nm'] = {fy: {'annual': 0.1} for fy in all_fys}

    # ── Build final ──
    unit = meta.get('unit', '')
    new_json = {
        'schema_version': '1.0',
        'generated_at': '2026-07-04T00:00:00Z',
        'identity': {
            'name': meta.get('company', ''),
            'ticker': meta.get('ticker', ''),
            'market': meta.get('market', 'us'),
            'currency': meta.get('currency', 'USD'),
            'accounting_standard': 'jp_gaap',
        },
        'meta': {
            'ticker': meta.get('ticker', ''),
            'company': meta.get('company', ''),
            'market': meta.get('market', 'us'),
            'base_fy': int(meta.get('base_fy', 2025)),
            'proj_years': int(meta.get('proj_years', 5)),
            'sotp_offset': int(meta.get('sotp_offset', 2)),
            'currency': meta.get('currency', 'USD'),
            'p&l_depth': meta.get('p&l_depth', 'gp'),
            'yf_ticker': meta.get('yf_ticker', ''),
            'price': float(meta.get('price', 0)),
            'shares_m': float(meta.get('shares_m', 0)),
            'mcap_m': float(meta.get('mcap_m', 0)),
            'net_debt': int(meta.get('net_debt', 0)),
            'q_actual_count': q_count,
            'q_proj_count': int(meta.get('q_proj_count', 4)),
            'q_start_yr': int(meta.get('q_start_yr', 2026)),
            'q_start_q': q_start,
        },
        'actuals': act,
        'assumptions': {
            'lines': asm_lines,
            'global': global_new
        },
        'market': {},
        'kpi': {}
    }
    # Add unit hint if present
    if unit:
        new_json['meta']['unit'] = unit

    with codecs.open(out_path, 'w', 'utf-8') as f:
        json.dump(new_json, f, indent=2, ensure_ascii=False)
    print(f'  Written: {out_path}')
    return new_json

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python migrate_old_to_new.py <old.json> <new.json>')
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])
