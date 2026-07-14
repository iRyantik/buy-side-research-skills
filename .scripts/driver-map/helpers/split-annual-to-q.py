"""Split annual values into Q1-Q4 using seasonal weights.

Usage:
  python split-annual-to-q.py <annual_value> <weights.json>
  python split-annual-to-q.py 4752 '{"Q1":0.23,"Q2":0.25,"Q3":0.26,"Q4":0.26}'

Output: { "Q1": val, "Q2": val, "Q3": val, "Q4": val }
"""
import json, sys

def split(annual, weights):
    """Split annual value into 4 Qs by weights. Residual goes to Q4."""
    qs = {}
    residual = annual
    for qk in ['Q1', 'Q2', 'Q3']:
        v = round(annual * weights.get(qk, 0.25))
        qs[qk] = v
        residual -= v
    qs['Q4'] = residual
    return qs

if __name__ == '__main__':
    annual = float(sys.argv[1])
    w_str = sys.argv[2]
    try:
        weights = json.loads(w_str)
    except json.JSONDecodeError:
        with open(w_str) as f:
            weights = json.load(f)
    result = split(annual, weights)
    print(json.dumps(result, indent=2))
    print(f'\n  Sum: {sum(result.values())} (input: {annual}, diff: {sum(result.values()) - annual})')
