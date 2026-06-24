"""backlog_burn module — Beginning Backlog × Burn Rate revenue model.

Contract:
  render(ws, R, ll, anchor_info, ctx) -> dict

  Input:  logic_line JSON with module="backlog_burn"
          beg_backlog: {fy0, unit}     — FY25A hardcoded value
          order_rate: {fy0, proj}      — new orders as % of beg backlog (0.3-0.6)
          burn_rate: {fy0, proj}       — % of beg backlog recognized as revenue (0.2-0.5)

  Chain:  End_Backlog_t = Beg_Backlog_t × (1 + Order_Rate_t − Burn_Rate_t)
          Beg_Backlog_{t+1} = End_Backlog_t  (cross-column chain link)

  Output: {next_R, rev_r, gm_r:None, gp_r:None, beg_r, end_r, order_r, burn_r}
"""

from openpyxl.utils import get_column_letter


def render(ws, R, ll, anchor_info, ctx):
    C = ctx['C']; I = ctx['I']
    nf = ctx['nf']; bf = ctx['bf']; itf = ctx['itf']
    NUM = ctx['NUM']; DEC = ctx['DEC']; PCT = ctx['PCT']
    DS = ctx['DS']; FY0 = ctx['FY0']; LC = ctx['LC']
    proj_n = ctx['proj_n']

    ln = ll['name']
    beg = ll['beg_backlog']
    order = ll['order_rate']
    burn = ll['burn_rate']

    # ── Beginning Backlog ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    I(ws, R, FY0, beg['fy0'], fmt=NUM)
    C(ws, R, 2, ln, font=bf)
    C(ws, R, 3, f'Beg Backlog ({beg["unit"]})')
    beg_r = R; R += 1

    # ── Order Rate ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=PCT)
    I(ws, R, FY0, order['fy0'], fmt=PCT)
    for i, v in enumerate(order['proj']):
        I(ws, R, FY0 + 1 + i, v, fmt=PCT)
    C(ws, R, 3, 'Order Rate (% backlog)')
    order_r = R; R += 1

    # ── Burn Rate ──
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=PCT)
    I(ws, R, FY0, burn['fy0'], fmt=PCT)
    for i, v in enumerate(burn['proj']):
        I(ws, R, FY0 + 1 + i, v, fmt=PCT)
    C(ws, R, 3, 'Burn Rate (% backlog)')
    burn_r = R; R += 1

    # ── Revenue = Beg Backlog × Burn Rate ──
    rev_r = R
    for col_idx in [FY0] + [FY0 + 1 + i for i in range(proj_n)]:
        cl = get_column_letter(col_idx)
        C(ws, R, col_idx, f'={cl}{beg_r}*{cl}{burn_r}', fmt=NUM)
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, 'Revenue')
    R += 1

    # ── Check row (collapsible) ──
    s1r, s1v = anchor_info.get(ln, (0, 0))
    for ci in range(DS, DS + 2):
        C(ws, R, ci, '', fmt=NUM)
    if s1r:
        C(ws, R, FY0, f'={get_column_letter(FY0)}{s1r}', fmt=NUM)
    for ci in range(FY0 + 1, LC + 1):
        C(ws, R, ci, '', fmt=NUM)
    C(ws, R, 3, f'  Check (anchor {s1v}M)', font=itf)
    ws.row_dimensions.group(R, R, outline_level=1, hidden=True)
    R += 1

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
        ws.cell(row=beg_r, column=ci).value = f'={pl}{end_r}'
        ws.cell(row=beg_r, column=ci).font = nf
        ws.cell(row=beg_r, column=ci).number_format = NUM

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

    return {
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
