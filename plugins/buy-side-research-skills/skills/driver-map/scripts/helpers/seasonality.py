"""Calculate Q1-Q4 seasonal weights from historical Q data.

Usage:
  python seasonality.py <research-model.json> [--segment "Engine Products Segment"]

Reads actuals.gaap.segments[name].rev Q1-Q4 values and computes seasonal weights.
If no --segment specified, uses company-level gaap.is.rev.

Output: { "Q1": weight, "Q2": weight, "Q3": weight, "Q4": weight }
"""
import json, codecs, sys

def seasonality(json_path, segment=None):
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    a = cfg['actuals']
    if segment:
        gs = next((s for s in a['gaap']['segments'] if s['name'] == segment), None)
        if not gs:
            raise ValueError(f'Segment "{segment}" not found')
        rev = gs['rev']
    else:
        rev = a['gaap']['is']['rev']

    weights = {}
    for fy in rev:
        annual = rev[fy].get('annual', 0)
        if not annual:
            continue
        q_sum = sum(rev[fy].get(f'Q{i}', 0) for i in range(1, 5))
        if q_sum <= 0:
            continue
        # Normalize
        for qi in range(1, 5):
            qk = f'Q{qi}'
            w = rev[fy].get(qk, 0) / q_sum
            weights.setdefault(qk, []).append(w)

    # Average across years
    avg = {}
    for qk in ['Q1', 'Q2', 'Q3', 'Q4']:
        ws = weights.get(qk, [0.25])
        avg[qk] = round(sum(ws) / len(ws), 4)

    return avg

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('json_path')
    p.add_argument('--segment', default=None)
    args = p.parse_args()
    w = seasonality(args.json_path, args.segment)
    print(json.dumps(w, indent=2))
    print(f'\n  Sum: {sum(w.values()):.4f} (should be ~1.0)')
