"""Compute base_rate from actuals segments for non-1:1 lines.

Usage:
  python derive-base-rate.py <research-model.json> [--depth ebitda]

Reads the flipped actuals structure (gaap.segments.rev + non_gaap.segments.ebitda)
and calculates base_rate per line per FY. Only for non-1:1 lines
(1:1 lines get their base_rate from build formula references to actuals).

Output: JSON dict { line_name: { "FY2023": {"annual": rate}, ... } }
"""
import json, codecs, sys

DEPTH_FIELD = {
    'gp': ('gp', 'rev'),     # base_rate = GP/Rev
    'op': ('gp', 'rev'),     # base_rate = GP/Rev
    'ebitda': ('ebitda', 'rev'),  # base_rate = EBITDA/Rev
}

def derive(json_path, depth='ebitda'):
    num_field, den_field = DEPTH_FIELD[depth]
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    a = cfg['actuals']
    lines = cfg['assumptions']['lines']
    gaap_segs = {s['name']: s for s in a['gaap']['segments']}
    non_segs = {s['name']: s for s in a['non_gaap']['segments']}

    result = {}
    for line in lines:
        name = line['name']
        if line.get('one_to_one'):
            continue  # 1:1: build references actuals directly
        seg = line.get('segment', '')
        if not seg:
            continue  # Non-core: always 0

        # Find GAAP segment by exact name
        gs = gaap_segs.get(seg)
        if not gs:
            print(f'  [warn] {name}: GAAP segment "{seg}" not found')
            continue

        # Find non-GAAP segment (strip " Segment" suffix if present)
        s_short = seg.replace(' Segment', '')
        ns = non_segs.get(s_short)
        if not ns:
            print(f'  [warn] {name}: non-GAAP segment "{s_short}" not found')
            continue

        rates = {}
        fys = list(gs['rev'].keys())
        for fy in fys:
            rev = gs['rev'][fy].get('annual', 0)
            if num_field == 'ebitda':
                num = ns['ebitda'][fy].get('annual', 0) if ns.get('ebitda') and fy in ns['ebitda'] else 0
            else:
                num = gs.get(num_field, {}).get(fy, {}).get('annual', 0)
            if rev and num:
                rates[fy] = {'annual': round(num / rev, 4)}

        if rates:
            result[name] = rates
            print(f'  {name}: {", ".join(f"{k}={v["annual"]:.3f}" for k,v in sorted(rates.items()))}')

    return result

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('json_path')
    p.add_argument('--depth', default='ebitda', choices=['gp','op','ebitda'])
    args = p.parse_args()
    rates = derive(args.json_path, args.depth)
    if rates:
        print('\n  Copy into assumptions.lines[].base_rate:')
        print(json.dumps(rates, indent=2, ensure_ascii=False))
