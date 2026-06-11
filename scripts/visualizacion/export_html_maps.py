"""
Exporta los 4 mapas Folium como HTML interactivo desde los resultados
pre-calculados por los módulos analíticos.

No re-ejecuta el pipeline de rasters ni necesita conexión a PostGIS.

Uso:
    python scripts/visualizacion/export_html_maps.py

Salida:
    docs/maps/mapa1_crecimiento.html
    docs/maps/mapa2_sprawl.html
    docs/maps/mapa3_amenazas.html
    docs/maps/mapa4_vulnerabilidad.html
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import rankdata

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VECTORS   = PROJECT_ROOT / 'data' / 'processed' / 'vectors'
MODULOS   = PROJECT_ROOT / 'scripts' / 'modulos_analisis'
DOCS_MAPS = PROJECT_ROOT / 'docs' / 'maps'
DOCS_MAPS.mkdir(parents=True, exist_ok=True)

# ── geometrías ────────────────────────────────────────────────────────────────
gdf_ucdb     = gpd.read_file(VECTORS / 'ucdb_colombia.gpkg')
gdf_col_4326 = gpd.read_file(VECTORS / 'limite_colombia_9377.gpkg').to_crs(4326)

# ── parquets (pre-calculados por run_modulos.py) ──────────────────────────────
m1       = pd.read_parquet(MODULOS / 'modulo1_crecimiento_urbano/m1_results.parquet')
m2       = pd.read_parquet(MODULOS / 'modulo2_presion_poblacional/m2_results.parquet')
m3       = pd.read_parquet(MODULOS / 'modulo3_deforestacion/m3_results.parquet')
m4_mm    = pd.read_parquet(MODULOS / 'modulo4_amenazas/m4_mm_results.parquet')
m4_flood = pd.read_parquet(MODULOS / 'modulo4_amenazas/m4_flood_results.parquet')
m5       = pd.read_parquet(MODULOS / 'modulo5_runap/m5_results.parquet')
m6       = pd.read_parquet(MODULOS / 'modulo6_topografia/m6_results.parquet')


def _base_map():
    return gdf_col_4326.explore(
        color='#eef2e6',
        tiles='CartoDB positron',
        style_kwds={'fillOpacity': 0.35, 'weight': 0.8, 'color': '#b0b8a8'},
    )


# ── Mapa 1 — área construida y crecimiento 2000-2025 ─────────────────────────
def mapa1_crecimiento():
    b2025 = m1[m1['year'] == 2025].set_index('uc_nm')['built_area_m2']
    b2000 = m1[m1['year'] == 2000].set_index('uc_nm')['built_area_m2']

    built_km2 = (b2025 / 1e6).rename('built_km2').reset_index()
    delta_km2 = ((b2025 - b2000) / 1e6).rename('delta_km2').reset_index()

    gdf = (
        gdf_ucdb
        .merge(built_km2, on='uc_nm', how='left')
        .merge(delta_km2, on='uc_nm', how='left')
        [['uc_nm', 'built_km2', 'delta_km2', 'geometry']]
        .to_crs(4326)
        .copy()
    )
    gdf['built_km2'] = gdf['built_km2'].round(2)
    gdf['delta_km2'] = gdf['delta_km2'].round(2)

    fmap = _base_map()
    gdf.dropna(subset=['built_km2']).explore(
        m=fmap,
        column='built_km2',
        cmap='YlOrRd',
        vmin=0,
        vmax=gdf['built_km2'].quantile(0.97),
        tooltip=['uc_nm', 'built_km2', 'delta_km2'],
        style_kwds={'weight': 0.4},
    )
    fmap.save(str(DOCS_MAPS / 'mapa1_crecimiento.html'))
    print('  ✓ mapa1_crecimiento.html')


# ── Mapa 2 — patrón sprawl vs. densificación 2025 ────────────────────────────
def _sprawl_cat(si):
    if si > 1.5:
        return 'Sprawl severo'
    if si > 1.0:
        return 'Sprawl moderado'
    return 'Densificacion'


_CAT_COLORS = {
    'Sprawl severo':   '#d73027',
    'Sprawl moderado': '#fc8d59',
    'Densificacion':   '#4575b4',
}


def mapa2_sprawl():
    si_2025 = m2[m2['year'] == 2025][['uc_nm', 'sprawl_index', 'pop_density']].copy()
    si_2025['categoria'] = si_2025['sprawl_index'].apply(_sprawl_cat)

    gdf = (
        gdf_ucdb
        .merge(si_2025, on='uc_nm', how='left')
        [['uc_nm', 'categoria', 'sprawl_index', 'pop_density', 'geometry']]
        .to_crs(4326)
        .copy()
    )
    gdf['sprawl_index'] = gdf['sprawl_index'].round(2)

    fmap = _base_map()
    for cat, color in _CAT_COLORS.items():
        sub = gdf[gdf['categoria'] == cat]
        if sub.empty:
            continue
        sub.explore(
            m=fmap,
            color=color,
            tooltip=['uc_nm', 'categoria', 'sprawl_index'],
            style_kwds={'weight': 0.4, 'fillOpacity': 0.7},
        )
    fmap.save(str(DOCS_MAPS / 'mapa2_sprawl.html'))
    print('  ✓ mapa2_sprawl.html')


# ── Mapa 3 — exposición a amenazas (movimientos masa + inundación) ────────────
def mapa3_amenazas():
    exp_mm = (
        m4_mm[(m4_mm['year'] == 2025) & m4_mm['hazard_class'].isin([3, 4])]
        .groupby('uc_nm')['pop_exposed']
        .sum()
        .rename('pop_exp_mm')
        .reset_index()
    )
    pop_tot = m2[m2['year'] == 2025][['uc_nm', 'pop_total']]

    pct_exp = exp_mm.merge(pop_tot, on='uc_nm', how='left')
    pct_exp['pct_exp_mm'] = (
        (pct_exp['pop_exp_mm'] / pct_exp['pop_total'] * 100).clip(0, 100)
    )
    flood_pct = m4_flood[['uc_nm', 'pct_built_exposed']].rename(
        columns={'pct_built_exposed': 'pct_flood'}
    )

    gdf = (
        gdf_ucdb
        .merge(pct_exp[['uc_nm', 'pct_exp_mm', 'pop_exp_mm']], on='uc_nm', how='left')
        .merge(flood_pct, on='uc_nm', how='left')
        [['uc_nm', 'pct_exp_mm', 'pop_exp_mm', 'pct_flood', 'geometry']]
        .to_crs(4326)
        .copy()
    )
    gdf['pct_exp_mm'] = gdf['pct_exp_mm'].round(2)
    gdf['pop_exp_mm'] = gdf['pop_exp_mm'].round(0)
    gdf['pct_flood']  = gdf['pct_flood'].round(2)

    fmap = _base_map()
    gdf.dropna(subset=['pct_exp_mm']).explore(
        m=fmap,
        column='pct_exp_mm',
        cmap='RdYlGn_r',
        vmin=0,
        vmax=gdf['pct_exp_mm'].quantile(0.95),
        tooltip=['uc_nm', 'pct_exp_mm', 'pop_exp_mm', 'pct_flood'],
        style_kwds={'weight': 0.4},
    )
    fmap.save(str(DOCS_MAPS / 'mapa3_amenazas.html'))
    print('  ✓ mapa3_amenazas.html')


# ── Mapa 4 — índice compuesto de vulnerabilidad ───────────────────────────────
def _pct_rank(series):
    s = series.dropna()
    ranks = pd.Series(rankdata(s) / len(s), index=s.index)
    return ranks.reindex(series.index)


def mapa4_vulnerabilidad():
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
    vuln = idx_df[['Índice compuesto']].copy()

    gdf = (
        gdf_ucdb
        .merge(vuln, left_on='uc_nm', right_index=True, how='left')
        [['uc_nm', 'Índice compuesto', 'geometry']]
        .to_crs(4326)
        .copy()
    )
    gdf['Índice compuesto'] = gdf['Índice compuesto'].round(3)

    fmap = _base_map()
    gdf.dropna(subset=['Índice compuesto']).explore(
        m=fmap,
        column='Índice compuesto',
        cmap='RdYlGn_r',
        vmin=0.2,
        vmax=0.9,
        tooltip=['uc_nm', 'Índice compuesto'],
        style_kwds={'weight': 0.4},
    )
    fmap.save(str(DOCS_MAPS / 'mapa4_vulnerabilidad.html'))
    print('  ✓ mapa4_vulnerabilidad.html')


if __name__ == '__main__':
    print(f'Exportando mapas → {DOCS_MAPS}')
    mapa1_crecimiento()
    mapa2_sprawl()
    mapa3_amenazas()
    mapa4_vulnerabilidad()
    print('Listo. 4 mapas HTML exportados.')
