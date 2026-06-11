import numpy as np
import pandas as pd
from scipy.stats import rankdata


def _pct_rank(series):
    s = series.dropna()
    ranks = pd.Series(rankdata(s) / len(s), index=s.index)
    return ranks.reindex(series.index)


def compute_composite_index(m1, m2, m3, m4_mm, m5, m6):
    """Calcula el índice compuesto de vulnerabilidad urbana (percentil-rank por dimensión).

    Retorna un DataFrame indexado por uc_nm con una columna por dimensión
    más 'Índice compuesto' (promedio de percentiles disponibles).
    """
    b2025  = m1[m1['year'] == 2025].set_index('uc_nm')['built_area_m2']
    b2000  = m1[m1['year'] == 2000].set_index('uc_nm')['built_area_m2']
    pop_25 = m2[m2['year'] == 2025].set_index('uc_nm')['pop_total']

    exp_mm_idx = (
        m4_mm[(m4_mm['year'] == 2025) & m4_mm['hazard_class'].isin([3, 4])]
        .groupby('uc_nm')['pop_exposed']
        .sum()
    )

    d1 = ((b2025 - b2000).dropna() / 1e6)
    d2 = m2[m2['year'] == 2025].set_index('uc_nm')['sprawl_index'].clip(lower=0)
    d3 = m3[m3['buffer_km'] == 10].set_index('uc_nm')['pct_urban_on_deforested']
    d4 = (exp_mm_idx / pop_25).replace([np.inf, -np.inf], np.nan)
    d6 = m6[m6['year'] == 2025].set_index('uc_nm')['pct_area_steep']

    dims = {
        'Crecimiento (M1)':   d1,
        'Sprawl (M2)':        d2,
        'Deforestación (M3)': d3,
        'Amenaza MM (M4)':    d4,
        'Topografía (M6)':    d6,
    }
    if 'uc_nm' in m5.columns:
        d5 = m5[m5['year'] == 2025].groupby('uc_nm')['built_inside_ha'].sum()
        if len(d5) > 0:
            dims['Presión RUNAP (M5)'] = d5

    idx_df = pd.DataFrame(
        {k: _pct_rank(v) for k, v in dims.items()}
    ).dropna(how='all')
    idx_df['Índice compuesto'] = idx_df.mean(axis=1)
    return idx_df
