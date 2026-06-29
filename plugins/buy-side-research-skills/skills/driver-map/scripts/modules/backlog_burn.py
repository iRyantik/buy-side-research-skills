"""backlog_burn module — Beginning Backlog × Burn Rate revenue model.

Contract:
  render(ws, R, ll, anchor_info, ctx) -> dict

  Input:  logic_line JSON with module="backlog_burn"
          beg_backlog: {fy0, unit}
          order_rate: {fy0, proj} | {bull, base, bear} (BBE optional)
          burn_rate:  {fy0, proj} | {bull, base, bear}

  Chain:  End_Backlog_t = Beg_Backlog_t × (1 + Order_Rate_t − Burn_Rate_t)
          Beg_Backlog_{t+1} = End_Backlog_t  (cross-column chain link)

  Output: {next_R, rev_r, gm_r:None, gp_r:None, beg_r, end_r, order_r, burn_r, [yb,ybs,ybe]}
"""

from openpyxl.utils import get_column_letter


def _write_bb_rate(ws, R, rate_data, label, ctx, is_order):
    """Write Order Rate or Burn Rate rows. Returns (active_row, next_R, yb, ys, ye)."""
    C = ctx['C']; I = ctx['I']; CF = ctx.get('CF', C)
    nf = ctx['nf']; bf = ctx['bf']; itf = ctx['itf']
    PCT = ctx['PCT']; NUM = ctx['NUM']; DS = ctx['DS']; FY0 = ctx['FY0']; LC = ctx['LC']
    proj_n = ctx['proj_n']

    is_bbe = isinstance(rate_data, dict) and 'bull' in rate_data
    yb = ys = ye = 0

    if is_bbe:
        bull = rate_data['bull']; base = rate_data['base']; bear = rate_data['bear']

        # Active row
        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        C(ws, R, FY0, '', fmt=PCT)
        for i in range(proj_n):
            C(ws, R, FY0 + 1 + i, 0, fmt=PCT)
        C(ws, R, 3, label)
        active_r = R; R += 1

        # Hidden BBE rows
        for arr, lbl in [(bull, 'Bull'), (base, 'Base'), (bear, 'Bear')]:
            for ci in range(DS, DS + 2):
                C(ws, R, ci, '', fmt=PCT)
            C(ws, R, FY0, '', fmt=PCT)
            for i, v in enumerate(arr):
                I(ws, R, FY0 + 1 + i, v, fmt=PCT)
            C(ws, R, 3, f'    {lbl}', font=itf)
            ws.row_dimensions[R].hidden = True
            if lbl == 'Bull':   yb = R
            elif lbl == 'Base': ys = R
            elif lbl == 'Bear': ye = R
            R += 1

        ws.row_dimensions.group(yb, ye, outline_level=1, hidden=True)

        # Active formula
        for i in range(proj_n):
            ci = FY0 + 1 + i
            cl = get_column_letter(ci)
            CF(ws, active_r, ci,
               f'=IF(B1="Bull",{cl}{yb},IF(B1="Bear",{cl}{ye},{cl}{ys}))', fmt=PCT)
    else:
        # Simple rate — no BBE
        for ci in range(DS, DS + 2):
            C(ws, R, ci, '', fmt=PCT)
        I(ws, R, FY0, rate_data.get('fy0', rate_data.get('proj', [0])[0] if rate_data.get('proj') else 0), fmt=PCT)
        for i, v in enumerate(rate_data.get('proj', [])):
            I(ws, R, FY0 + 1 + i, v, fmt=PCT)
        C(ws, R, 3, label)
        active_r = R; R += 1

    return active_r, R, yb, ys, ye


def render(ws, R, ll, anchor_info, ctx):
    C = ctx['C']; I = ctx['I']; CF = ctx.get('CF', C)
    nf = ctx['nf']; bf = ctx['bf']; itf = ctx['itf']
    NUM = ctx['NUM']; DEC = ctx['DEC']; PCT = ctx['PCT']
    DS = ctx['DS']; FY0 = ctx['FY0']; LC = ctx['LC']; SC = ctx['SC']
    proj_n = ctx['proj_n']

    ln = ll['name']
    beg = ll['beg_backlog']
    order = ll['order_rate']
    burn = ll['burn_rate']
    has_bbe = isinstance(order, dict) and 'bull' in order

    # ── Beginning Backlog ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    I(ws, R, FY0, beg['fy0'], fmt=NUM)
    C(ws, R, 2, ln, font=bf)
    C(ws, R, 3, f'Beg Backlog ({beg["unit"]})')
    beg_r = R; R += 1

    # ── Order Rate (BBE or simple) ──
    order_r, R, ob, os, oe = _write_bb_rate(ws, R, order, 'Order Rate (% backlog)', ctx, True)

    # ── Burn Rate (BBE or simple) ──
    burn_r, R, bb, bs, be = _write_bb_rate(ws, R, burn, 'Burn Rate (% backlog)', ctx, False)

    yb = ob if ob else bb  # use order's yb as primary, fallback to burn
    ys = os if os else bs
    ye = oe if oe else be

    # ── Revenue = Beg Backlog × Burn Rate ──
    rev_r = R
    for col_idx in [FY0] + [FY0 + 1 + i for i in range(proj_n)]:
        cl = get_column_letter(col_idx)
        C(ws, R, col_idx, f'={cl}{beg_r}*{cl}{burn_r}', fmt=NUM)
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, 'Revenue')
    R += 1

    # ── Scenario Revenue cache (if BBE) ──
    if has_bbe:
        sc_cl = get_column_letter(SC)
        for arr_key, arr_idx, label in [('bull', 2, 'Bull'), ('base', 3, 'Base'), ('bear', 4, 'Bear')]:
            # Rate arrays: bull=[0], base=[1], bear=[2] in BBE tuple
            # Use burn rate BBE rows for revenue scenario
            burn_bb = [yb, ys, ye]  # [bull_row, base_row, bear_row]
            # Actually need to reference the correct BBE row
            # Revenue = Beg × Burn_Rate_Scenario
            # Build SC formula: =SC_beg * SC_burn_fy(row)
            if arr_key == 'bull':
                burn_sc_row = ys  # fall back
                if bb: burn_sc_row = bb
            elif arr_key == 'base':
                burn_sc_row = ys
            else:
                burn_sc_row = ye

            if burn_sc_row:
                for ci in range(DS, DS + 2):
                    C(ws, R, ci, '', fmt=NUM)
                C(ws, R, 3, f'    {label} Rev @ SOTP', font=itf)
                C(ws, R, SC, f'={sc_cl}{beg_r}*{sc_cl}{burn_sc_row}', fmt=NUM)
                ws.row_dimensions[R].hidden = True
                if label == 'Bull':    yb = R
                elif label == 'Base':  ys = R
                elif label == 'Bear':  ye = R
                R += 1
        ws.row_dimensions.group(yb, ye, outline_level=1, hidden=True)

    # ── End Backlog = Beg × (1 + Order_Rate − Burn_Rate) ──
    end_r = R
    for col_idx in [FY0] + [FY0 + 1 + i for i in range(proj_n)]:
        cl = get_column_letter(col_idx)
        C(ws, R, col_idx,
          f'={cl}{beg_r}*(1+{cl}{order_r}-{cl}{burn_r})', fmt=NUM)
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, 'End Backlog')
    R += 1

    # ── Chain link: Beg Backlog FY26E+ = prior End Backlog ──
    for i in range(proj_n):
        ci = FY0 + 1 + i
        cl = get_column_letter(ci)
        pl = get_column_letter(ci - 1)
        CF(ws, beg_r, ci, f'={pl}{end_r}', fmt=NUM)

    # ── Implied YoY ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=PCT)
    f0 = get_column_letter(FY0); f_1 = get_column_letter(FY0 - 1)
    C(ws, R, FY0, f'=IFERROR({f0}{rev_r}/{f_1}{rev_r}-1,"")', fmt=PCT)
    for ci in range(FY0 + 1, LC + 1):
        cl = get_column_letter(ci); pl = get_column_letter(ci - 1)
        C(ws, R, ci, f'=IFERROR({cl}{rev_r}/{pl}{rev_r}-1,"")', fmt=PCT)
    C(ws, R, 3, 'Implied YoY')
    R += 1

    result = {
        'next_R': R,
        'rev_r': rev_r,
        'gm_r': None,
        'gp_r': None,
        'beg_r': beg_r,
        'end_r': end_r,
        'order_r': order_r,
        'burn_r': burn_r,
        'module': 'backlog_burn',
    }
    if yb:
        result['yb'] = yb
        result['ybs'] = ys
        result['ybe'] = ye
    return result
