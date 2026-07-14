# Merge Q actuals into FY Hidden Bridge - one row per metric
with open('.scripts/driver-map/build-logic-model.py', encoding='utf-8') as f:
    c = f.read()

# 1. Init q_act_cells near line 1794 (after rev/act vars)
c = c.replace(
    "rev_act_cells = gp_act_cells = op_act_cells = ebitda_act_cells = ni_act_cells = tax_act_cells = da_act_cells = {}",
    "rev_act_cells = gp_act_cells = op_act_cells = ebitda_act_cells = ni_act_cells = tax_act_cells = da_act_cells = {}\n    q_act_cells = {}"
)

# 2. Add Q write + q_act_cells to each actuals block
# Each block has: C(ws, R, 3, '  actuals XXXX', font=itf)
# Insert Q code BEFORE this label line

insertions = [
    ("C(ws, R, 3, '  actuals Rev', font=itf)", "Revenue", "rev"),
    ("C(ws, R, 3, '  actuals GP', font=itf)", "GP", "gp"),
    ("C(ws, R, 3, '  actuals OI', font=itf)", "OI", "op"),
]
for label, qkey, mkey in insertions:
    qcode = f"""
        if has_q:
            _qm = cfg.get('quarters', {{}})
            for _qi, _qk in enumerate(['q1','q2','q3','q4'][:min(q_actual_n,4)]):
                _qv = _qm.get(_qk, {{}}).get('{mkey}', 0)
                if not _qv:
                    _qv = sum(_s.get('quarters',{{}}).get(_qk,{{}}).get('{mkey}',0) for _s in cfg.get('segments',[]))
                if _qv:
                    I(ws, R, Q_START + _qi, sc(_qv), fmt=NUM)
                q_act_cells.setdefault('{qkey}', {{}})['{mkey.replace('rev','q1').replace('gp','q2').replace('op','q3')}'] = R
"""
    # Actually, the above is wrong. Let me use a simple insertion
    # Insert after label line
    old = label + "\n        ws.row_dimensions.group"
    new = label + "\n        if has_q:\n            for _qi, _qk in enumerate(['q1','q2','q3','q4'][:min(q_actual_n,4)]):\n                _qv = cfg.get('quarters',{}).get(_qk,{}).get('" + mkey + "',0)\n                if not _qv:\n                    _qv = sum(_s.get('quarters',{}).get(_qk,{}).get('" + mkey + "',0) for _s in cfg.get('segments',[]))\n                if _qv:\n                    I(ws, R, Q_START+_qi, sc(_qv), fmt=NUM)\n                q_act_cells.setdefault('" + qkey + "',{})[_qk] = R\n        ws.row_dimensions.group"
    c = c.replace(old, new, 1)

# 3. Delete Q bridge section
idx = c.find("# ── Q actuals bridge (one row per metric, Q1-Q4 in Q columns) ──")
if idx >= 0:
    end = c.find("\n\n    # ═══", idx)
    if end == -1: end = c.find("\n\n    # ──", idx)
    c = c[:idx] + c[end:]

with open('.scripts/driver-map/build-logic-model.py', 'w', encoding='utf-8') as f:
    f.write(c)
compile(c, 'x', 'exec')
print("Syntax OK")
