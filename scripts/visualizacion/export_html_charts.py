"""
Exporta fig1, fig4 y fig16 como HTML interactivo con Plotly desde los
resultados pre-calculados por los módulos analíticos.

No re-ejecuta el pipeline de rasters ni necesita conexión a PostGIS.

Uso:
    python scripts/visualizacion/export_html_charts.py

Salida:
    docs/charts/fig1_area_total.html
    docs/charts/fig4_scatter_sprawl.html
    docs/charts/fig16_radar_vulnerabilidad.html
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _composite_index import compute_composite_index

MODULOS      = PROJECT_ROOT / 'scripts' / 'modulos_analisis'
DOCS_CHARTS  = PROJECT_ROOT / 'docs' / 'charts'
DOCS_CHARTS.mkdir(parents=True, exist_ok=True)

PILOT_NMS = ['Bogota', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga']
PILOT_COLORS = {
    'Bogota':       '#e41a1c',
    'Medellín':     '#377eb8',
    'Cali':         '#4daf4a',
    'Barranquilla': '#ff7f00',
    'Cartagena':    '#984ea3',
    'Bucaramanga':  '#a65628',
}

# ── parquets (pre-calculados por run_modulos.py) ──────────────────────────────
m1    = pd.read_parquet(MODULOS / 'modulo1_crecimiento_urbano/m1_results.parquet')
m2    = pd.read_parquet(MODULOS / 'modulo2_presion_poblacional/m2_results.parquet')
m3    = pd.read_parquet(MODULOS / 'modulo3_deforestacion/m3_results.parquet')
m4_mm = pd.read_parquet(MODULOS / 'modulo4_amenazas/m4_mm_results.parquet')
m5    = pd.read_parquet(MODULOS / 'modulo5_runap/m5_results.parquet')
m6    = pd.read_parquet(MODULOS / 'modulo6_topografia/m6_results.parquet')


# ── Fig 1 — evolución área urbana total Colombia 1975–2030 ────────────────────
def fig1_area_total():
    total_yr = m1.groupby('year')['built_area_m2'].sum().reset_index()
    total_yr['built_km2'] = (total_yr['built_area_m2'] / 1e6).round(1)

    fig = px.line(
        total_yr, x='year', y='built_km2',
        markers=True,
        labels={'year': 'Año', 'built_km2': 'Área construida (km²)'},
        title='Evolución del área urbana construida en Colombia (1975–2030)',
        color_discrete_sequence=['steelblue'],
    )
    fig.update_traces(
        line_width=2.5,
        marker=dict(size=7),
        hovertemplate='%{x}: %{y:.1f} km²<extra></extra>',
    )
    fig.add_hline(y=0, line_width=0)  # fuerza eje y desde 0 visualmente
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=total_yr['year'].tolist(), tickangle=45),
        yaxis_title='Área construida (km²)',
        xaxis_title='Año',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=60, b=60, l=70, r=20),
    )
    fig.write_html(str(DOCS_CHARTS / 'fig1_area_total.html'), include_plotlyjs='cdn')
    print('  ✓ fig1_area_total.html')


# ── Fig 4 — scatter sprawl vs. densificación 2000–2025 ───────────────────────
def fig4_scatter_sprawl():
    b_pct = (
        (m1[m1['year'] == 2025].set_index('uc_nm')['built_area_m2'] /
         m1[m1['year'] == 2000].set_index('uc_nm')['built_area_m2'] - 1) * 100
    ).rename('area_pct')
    p_pct = (
        (m2[m2['year'] == 2025].set_index('uc_nm')['pop_total'] /
         m2[m2['year'] == 2000].set_index('uc_nm')['pop_total'] - 1) * 100
    ).rename('pop_pct')
    si_acum = m2[m2['year'] == 2025].set_index('uc_nm')['sprawl_index_acum'].rename('si_acum')
    sc_df = pd.concat([b_pct, p_pct, si_acum], axis=1).dropna().reset_index()
    sc_df['es_piloto'] = sc_df['uc_nm'].isin(PILOT_NMS)

    # Excluir ciudades con < 1 km² construido en 2000: GHSL subestima su población
    # en ese año → denominador casi 0 → pop_pct espuria de decenas de miles %.
    b2000 = m1[m1['year'] == 2000].set_index('uc_nm')['built_area_m2']
    sc_df = sc_df[sc_df['uc_nm'].isin(b2000[b2000 >= 1e6].index)]

    lim = max(sc_df['pop_pct'].max(), sc_df['area_pct'].max()) * 1.08
    lim = round(lim, -1)

    otras = sc_df[~sc_df['es_piloto']].copy()
    fig = px.scatter(
        otras, x='pop_pct', y='area_pct',
        color='si_acum',
        color_continuous_scale='RdYlGn_r',
        range_color=[0, 3],
        hover_name='uc_nm',
        hover_data={
            'pop_pct': ':.1f', 'area_pct': ':.1f',
            'si_acum': ':.2f', 'es_piloto': False,
        },
        labels={
            'pop_pct':  'Crecimiento poblacional 2000–2025 (%)',
            'area_pct': 'Crecimiento área construida 2000–2025 (%)',
            'si_acum':  'Índice sprawl acumulado',
        },
        title='Sprawl vs. densificación — ciudades colombianas 2000–2025',
    )

    # diagonal de equilibrio (área creció = población creció)
    fig.add_shape(type='line', x0=0, y0=0, x1=lim, y1=lim,
                  line=dict(color='black', dash='dash', width=1.2))
    # etiquetas en el triángulo correcto:
    # sprawl  → SOBRE la diagonal: y > x → esquina superior izquierda
    # densif  → BAJO la diagonal:  y < x → esquina inferior derecha
    fig.add_annotation(x=lim * 0.18, y=lim * 0.78, text='Zona sprawl',
                       showarrow=False, font=dict(color='#cc4444', size=10))
    fig.add_annotation(x=lim * 0.72, y=lim * 0.18, text='Densificación',
                       showarrow=False, font=dict(color='#228B22', size=10))

    # ciudades piloto: solo etiqueta de texto en negro, sin marcador ni leyenda
    for _, row in sc_df[sc_df['es_piloto']].iterrows():
        fig.add_trace(go.Scatter(
            x=[row['pop_pct']], y=[row['area_pct']],
            mode='text',
            text=[row['uc_nm']],
            textposition='top center',
            textfont=dict(size=9, color='black'),
            hovertemplate=(
                f"{row['uc_nm']}<br>"
                f"Pob: {row['pop_pct']:.1f}%<br>"
                f"Área: {row['area_pct']:.1f}%<br>"
                f"Sprawl acumulado: {row['si_acum']:.2f}<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        coloraxis_colorbar=dict(
            orientation='h',
            x=0.5, xanchor='center',
            y=-0.18, yanchor='top',
            len=0.55, thickness=12,
            title=dict(text='Índice sprawl', side='bottom'),
            tickfont=dict(size=10),
        ),
        showlegend=False,
        xaxis=dict(range=[-5, lim], title='Crecimiento poblacional 2000–2025 (%)'),
        yaxis=dict(range=[-5, lim], title='Crecimiento área construida 2000–2025 (%)'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=60, b=110, l=80, r=20),
    )
    fig.write_html(str(DOCS_CHARTS / 'fig4_scatter_sprawl.html'), include_plotlyjs='cdn')
    print('  ✓ fig4_scatter_sprawl.html')


# ── Fig 16 — radar vulnerabilidad compuesta — ciudades piloto ─────────────────
def fig16_radar_vulnerabilidad():
    idx_df   = compute_composite_index(m1, m2, m3, m4_mm, m5, m6)
    dim_cols = [c for c in idx_df.columns if c != 'Índice compuesto']

    fig = go.Figure()
    for city in PILOT_NMS:
        if city not in idx_df.index:
            continue
        vals = idx_df.loc[city, dim_cols].fillna(0).tolist()
        vals += vals[:1]
        cats  = dim_cols + [dim_cols[0]]
        color = PILOT_COLORS[city]
        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=cats,
            name=city,
            line_color=color,
            fillcolor=color,
            opacity=0.15,
            fill='toself',
            hovertemplate=city + '<br>%{theta}: %{r:.2f}<extra></extra>',
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=9)),
        ),
        title='Perfil de vulnerabilidad compuesta — ciudades piloto',
        showlegend=True,
        legend=dict(font=dict(size=10)),
        margin=dict(t=80, b=40, l=80, r=80),
        paper_bgcolor='white',
    )
    fig.write_html(str(DOCS_CHARTS / 'fig16_radar_vulnerabilidad.html'), include_plotlyjs='cdn')
    print('  ✓ fig16_radar_vulnerabilidad.html')


if __name__ == '__main__':
    print(f'Exportando gráficos → {DOCS_CHARTS}')
    fig1_area_total()
    fig4_scatter_sprawl()
    fig16_radar_vulnerabilidad()
    print('Listo. 3 gráficos HTML exportados.')
