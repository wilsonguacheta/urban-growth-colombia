-- DDL 05: Vistas analíticas y vistas materializadas de uso frecuente

-- ── M1: Ranking de ciudades por superficie construida ─────────────────────────
CREATE OR REPLACE VIEW analysis.v_m1_ranking_built AS
SELECT
    uc_nm,
    year,
    built_area_ha,
    RANK() OVER (PARTITION BY year ORDER BY built_area_ha DESC) AS ranking
FROM analysis.m1_urban_growth
ORDER BY year, ranking;

-- ── M1: Tasa de crecimiento por periodo ──────────────────────────────────────
CREATE OR REPLACE VIEW analysis.v_m1_growth_rate AS
SELECT
    uc_nm,
    year,
    year_prev,
    built_area_ha,
    delta_m2 / 10000.0                               AS delta_ha,
    growth_rate_pct,
    CASE
        WHEN growth_rate_pct > 50  THEN 'Muy alto'
        WHEN growth_rate_pct > 25  THEN 'Alto'
        WHEN growth_rate_pct > 10  THEN 'Moderado'
        WHEN growth_rate_pct >= 0  THEN 'Bajo'
        ELSE 'Negativo'
    END                                              AS categoria_crecimiento
FROM analysis.m1_urban_growth
WHERE year_prev IS NOT NULL
ORDER BY uc_nm, year;

-- ── M2: Clasificación de tendencia urbana ────────────────────────────────────
CREATE OR REPLACE VIEW analysis.v_m2_tendencia AS
SELECT
    uc_nm,
    year,
    pop_total,
    built_area_m2 / 1e6                              AS built_km2,
    pop_density,
    sprawl_index,
    CASE
        WHEN sprawl_index > 1.5  THEN 'Sprawl severo'
        WHEN sprawl_index > 1.0  THEN 'Sprawl moderado'
        WHEN sprawl_index BETWEEN 0.8 AND 1.0 THEN 'Equilibrado'
        WHEN sprawl_index < 0.8  THEN 'Densificación'
        ELSE 'Sin datos'
    END                                              AS tipo_crecimiento
FROM analysis.m2_population_pressure
WHERE sprawl_index IS NOT NULL
ORDER BY year, sprawl_index DESC;

-- ── M4: Resumen de exposición a amenazas ─────────────────────────────────────
CREATE OR REPLACE VIEW analysis.v_m4_exposure_summary AS
SELECT
    uc_nm,
    year,
    SUM(CASE WHEN hazard_type = 'flood'         THEN pop_exposed END) AS pop_flood,
    SUM(CASE WHEN hazard_type = 'mass_movement' THEN pop_exposed END) AS pop_mm,
    SUM(CASE WHEN hazard_type = 'flood'         THEN built_exposed_m2 / 10000 END) AS built_ha_flood,
    SUM(CASE WHEN hazard_type = 'mass_movement' THEN built_exposed_m2 / 10000 END) AS built_ha_mm
FROM analysis.m4_hazard_exposure
GROUP BY uc_nm, year
ORDER BY year, pop_flood DESC NULLS LAST;

-- ── M5: Buffer 5km alrededor de áreas protegidas (vista materializada) ────────
-- Requiere ejecución manual: REFRESH MATERIALIZED VIEW analysis.mv_runap_buffer_5km;
CREATE MATERIALIZED VIEW IF NOT EXISTS analysis.mv_runap_buffer_5km AS
SELECT
    gid,
    nombre,
    categoria,
    area_ha,
    ST_Buffer(geom, 5000)            AS buffer_5km_geom
FROM raw.runap;

CREATE INDEX IF NOT EXISTS idx_mv_runap_buffer ON analysis.mv_runap_buffer_5km USING GIST(buffer_5km_geom);

-- ── M6: Topografía del crecimiento urbano ────────────────────────────────────
CREATE OR REPLACE VIEW analysis.v_m6_topografia AS
SELECT
    uc_nm,
    year,
    mean_elevation_m,
    mean_slope_deg,
    pct_area_steep,
    slope_new_growth,
    elevation_new_growth
FROM analysis.m6_topography
ORDER BY year, mean_slope_deg DESC NULLS LAST;

-- ── M5: Distancia de cada ciudad al AP más cercana ───────────────────────────
CREATE OR REPLACE VIEW analysis.v_m5_dist_ap_cercana AS
SELECT
    u.uc_nm,
    r.nombre                         AS runap_nombre,
    r.categoria,
    ST_Distance(u.geom, r.geom) / 1000.0 AS dist_km
FROM raw.ucdb_colombia u
CROSS JOIN LATERAL (
    SELECT nombre, categoria, geom
    FROM raw.runap
    ORDER BY u.geom <-> geom
    LIMIT 1
) r
ORDER BY dist_km;
