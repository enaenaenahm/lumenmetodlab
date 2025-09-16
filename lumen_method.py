
import math
import click

def room_index(length, width, hm):
    # K = (L*W)/(Hm*(L+W))
    if hm <= 0 or (length+width) == 0:
        return 0.0
    return (length * width) / (hm * (length + width))

def uf_estimate(K, rho_c=0.7, rho_w=0.5, rho_f=0.2):
    """Грубая оценка UF.
    Идея: базовая кривая по индексу помещения + поправки за отражения.
    Диапазоны типичные для офисов: UF ~ 0.4..0.8
    НЕ для проектирования — только для прикидки.
    """
    # базовая кривая по K: растёт логарифмически и насыщается
    base = 0.35 + 0.22 * math.log(1 + K, 2)  # log2(1+K)
    base = max(0.30, min(base, 0.78))
    # поправки за отражения (около ±0.05)
    refl = (rho_c - 0.7) * 0.10 + (rho_w - 0.5) * 0.08 + (rho_f - 0.2) * 0.02
    uf = base + refl
    return max(0.30, min(uf, 0.80))

def suggest_grid(n, length, width, hm, shr_max=None):
    """Подбор сетки ряды×столбцы с примерно квадратичной раскладкой.
    Проверяем шаг против SHR_max * Hm, если задано.
    Возвращаем (rows, cols, sx, sy, ok_spacing).
    """
    if n <= 0:
        return 0, 0, 0.0, 0.0, True
    # пытаемся сделать решётку близкую к квадрату
    cols = math.ceil(math.sqrt(n * length / width))
    rows = math.ceil(n / cols)
    # шаги (грубая оценка: равномерное поле, отступы ~ полшага)
    sx = length / (cols + 1)
    sy = width / (rows + 1)
    ok = True
    if shr_max is not None and hm > 0:
        smax = shr_max * hm
        ok = (sx <= smax) and (sy <= smax)
    return rows, cols, sx, sy, ok

def required_fixtures(target_lux, area, lumens, uf, mf):
    if lumens <= 0 or uf <= 0 or mf <= 0:
        return 0
    return math.ceil(target_lux * area / (uf * mf * lumens))

@click.command()
@click.option('--length', type=float, required=True, help='Длина помещения, м')
@click.option('--width', type=float, required=True, help='Ширина помещения, м')
@click.option('--height', type=float, required=True, help='Высота потолка, м')
@click.option('--workplane', type=float, default=0.8, show_default=True, help='Высота рабочей плоскости, м')
@click.option('--suspension', type=float, default=0.0, show_default=True, help='Подвес/заглубление светильника над РП, м')
@click.option('--target_lux', type=float, required=True, help='Требуемая освещённость на РП, лк')
@click.option('--lumens', type=float, required=True, help='Световой поток одного светильника, лм')
@click.option('--mf', type=float, default=0.8, show_default=True, help='Коэффициент запаса (0..1)')
@click.option('--uf', type=str, default='auto', show_default=True, help='UF либо число, либо "auto"')
@click.option('--rho_c', type=float, default=0.7, show_default=True, help='Отражение потолка (0..1)')
@click.option('--rho_w', type=float, default=0.5, show_default=True, help='Отражение стен (0..1)')
@click.option('--rho_f', type=float, default=0.2, show_default=True, help='Отражение пола (0..1)')
@click.option('--shr_max', type=float, default=None, help='Макс. отношение шага к высоте (SHRmax)')
@click.option('--p_fixture', type=float, default=None, help='Мощность одного светильника, Вт (для энергоблока)')
@click.option('--hours_year', type=float, default=2000, show_default=True, help='Часы работы в год')
@click.option('--tariff', type=float, default=None, help='Тариф, у.е./кВт⋅ч')
@click.option('--grid_factor', type=float, default=None, help='Сетевой фактор CO2, кг/кВт⋅ч')
def cli(length, width, height, workplane, suspension, target_lux, lumens, mf, uf, rho_c, rho_w, rho_f, shr_max, p_fixture, hours_year, tariff, grid_factor):
    area = length * width
    hm = max(0.0, height - workplane - suspension)
    K = room_index(length, width, hm)
    if uf == 'auto':
        uf_val = uf_estimate(K, rho_c, rho_w, rho_f)
    else:
        uf_val = float(uf)

    n = required_fixtures(target_lux, area, lumens, uf_val, mf)
    rows, cols, sx, sy, ok = suggest_grid(n, length, width, hm, shr_max)

    print(f"Area: {area:.2f} m^2, Hm: {hm:.2f} m, Room Index K: {K:.2f}")
    print(f"UF: {uf_val:.2f} (mode: {'auto' if uf=='auto' else 'manual'}), MF: {mf:.2f}")
    print(f"Required fixtures: {n}")
    print(f"Suggested grid: {rows} rows × {cols} cols; step ≈ {sx:.2f} m (X), {sy:.2f} m (Y); spacing ok: {ok}")

    if p_fixture is not None and n > 0:
        P_total = n * p_fixture  # W
        E_year = P_total * hours_year / 1000.0  # kWh
        msg = f"Energy/year: {E_year:.1f} kWh"
        if tariff is not None:
            cost = E_year * tariff
            msg += f", Cost/year: {cost:.2f}"
        if grid_factor is not None:
            co2 = E_year * grid_factor
            msg += f", CO2/year: {co2:.1f} kg"
        print(msg)

if __name__ == '__main__':
    cli()
