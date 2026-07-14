"""Validate Q SUM ≈ annual for all fields in research-model.json.

Usage:
  python validate-q-fy.py <research-model.json> [--tolerance 0.02]

Checks:
  - Company-level: actuals.gaap.is.{field}.FY{n}.Q1-Q4 vs annual
  - Segment-level: actuals.gaap.segments[name].rev.FY{n}.Q1-Q4 vs annual
  - Segment-level: actuals.non_gaap.segments[name].ebitda.FY{n}.Q1-Q4 vs annual

Output: list of discrepancies, exit code 1 if any exceed tolerance.
"""
import json, codecs, sys

FIELDS = ['rev', 'gp', 'oi', 'ni', 'tax', 'ebitda']

def validate(json_path, tolerance=0.02):
    with codecs.open(json_path, 'r', 'utf-8') as f:
        cfg = json.load(f)

    a = cfg['actuals']
    issues = []

    # Company-level fields
    for field in FIELDS:
        gaap = a['gaap']['is'].get(field, {})
        for fy in gaap:
            annual = gaap[fy].get('annual', 0)
            if not annual:
                continue
            q_sum = sum(gaap[fy].get(f'Q{i}', 0) for i in range(1, 5))
            if q_sum == 0:
                continue  # No Q data — OK
            diff = abs(q_sum / annual - 1) if annual else 1
            if diff > tolerance:
                issues.append(f'  {field}.{fy}: annual={annual} Q_sum={q_sum} diff={diff:.2%}')

    # Segment-level
    for seg in a['gaap']['segments']:
        rev = seg.get('rev', {})
        for fy in rev:
            annual = rev[fy].get('annual', 0)
            if not annual:
                continue
            q_sum = sum(rev[fy].get(f'Q{i}', 0) for i in range(1, 5))
            if q_sum == 0:
                continue
            diff = abs(q_sum / annual - 1) if annual else 1
            if diff > tolerance:
                issues.append(f'  {seg["name"]}.rev.{fy}: annual={annual} Q_sum={q_sum} diff={diff:.2%}')

    for seg in a['non_gaap']['segments']:
        ebitda = seg.get('ebitda', {})
        for fy in ebitda:
            annual = ebitda[fy].get('annual', 0)
            if not annual:
                continue
            q_sum = sum(ebitda[fy].get(f'Q{i}', 0) for i in range(1, 5))
            if q_sum == 0:
                continue
            diff = abs(q_sum / annual - 1) if annual else 1
            if diff > tolerance:
                issues.append(f'  {seg["name"]}.ebitda.{fy}: annual={annual} Q_sum={q_sum} diff={diff:.2%}')

    return issues

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('json_path')
    p.add_argument('--tolerance', type=float, default=0.02)
    args = p.parse_args()
    issues = validate(args.json_path, args.tolerance)
    if issues:
        print(f'{len(issues)} discrepancy(ies):')
        for i in issues:
            print(i)
        sys.exit(1)
    else:
        print('  All Q SUM ≈ annual OK')
