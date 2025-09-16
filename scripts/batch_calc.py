
import sys, math, pandas as pd
from lumen_method import room_index, uf_estimate, required_fixtures, suggest_grid

if len(sys.argv) < 3:
    print("Usage: python scripts/batch_calc.py input.csv output.csv")
    sys.exit(1)

inp, outp = sys.argv[1], sys.argv[2]
df = pd.read_csv(inp)

rows_out = []
for i, r in df.iterrows():
    L, W, H = r['length'], r['width'], r['height']
    wp, susp = r.get('workplane', 0.8), r.get('suspension', 0.0)
    lux, lumens = r['target_lux'], r['lumens']
    mf = r.get('mf', 0.8)
    uf = r.get('uf', 'auto')
    rho_c = r.get('rho_c', 0.7); rho_w = r.get('rho_w', 0.5); rho_f = r.get('rho_f', 0.2)
    shr_max = r.get('shr_max', None)
    p_fix = r.get('p_fixture', None); hours = r.get('hours_year', 2000); tariff = r.get('tariff', None); gf = r.get('grid_factor', None)

    area = L*W; hm = max(0.0, H - wp - susp); K = room_index(L, W, hm)
    if isinstance(uf, str) and uf == 'auto':
        uf_val = uf_estimate(K, rho_c, rho_w, rho_f)
    else:
        uf_val = float(uf)

    n = required_fixtures(lux, area, lumens, uf_val, mf)
    rws, cls, sx, sy, ok = suggest_grid(n, L, W, hm, shr_max)

    result = dict(r)
    result.update({
        'area': area, 'Hm': hm, 'room_index': K, 'UF_used': uf_val, 'required_fixtures': n,
        'rows': rws, 'cols': cls, 'step_x': sx, 'step_y': sy, 'spacing_ok': ok
    })

    if pd.notnull(p_fix):
        P_total = n * p_fix
        E_year = P_total * hours / 1000.0
        result['kWh_year'] = E_year
        if pd.notnull(tariff):
            result['cost_year'] = E_year * tariff
        if pd.notnull(gf):
            result['co2_year'] = E_year * gf

    rows_out.append(result)

pd.DataFrame(rows_out).to_csv(outp, index=False)
print(f"Saved: {outp}")
