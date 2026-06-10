-- Módulo 5: Presión sobre Áreas Protegidas
-- EPSG:9377 → ST_Distance retorna metros directamente.

-- Distancia de cada ciudad a la AP más cercana
SELECT
    u.uc_nm,
    r.nombre                         AS runap_nombre,
    r.categoria,
    r.area_ha,
    ROUND(ST_Distance(u.geom, r.geom) / 1000.0, 2) AS dist_km
FROM raw.ucdb_colombia u
CROSS JOIN LATERAL (
    SELECT nombre, categoria, area_ha, geom
    FROM raw.runap
    ORDER BY u.geom <-> geom
    LIMIT 1
) r
ORDER BY dist_km;

-- Ciudades con crecimiento urbano dentro de áreas protegidas (cualquier año)
SELECT
    m5.nombre      AS runap_nombre,
    m5.categoria,
    m5.year,
    ROUND(m5.built_inside_ha, 2) AS built_inside_ha,
    ROUND(m5.built_inside_ha / NULLIF(m5.area_ha, 0) * 100, 2) AS pct_ap_construido
FROM analysis.m5_protected_areas m5
WHERE m5.built_inside_ha > 0
ORDER BY m5.built_inside_ha DESC, m5.year;

-- Buffer 5km: área construida en zona de influencia
SELECT
    buf.nombre,
    buf.categoria,
    -- built_inside se calcula con Python (rasterstats) y se une aquí
    m5.built_buffer_ha
FROM analysis.mv_runap_buffer_5km buf
LEFT JOIN (
    SELECT runap_gid, year, built_buffer_ha
    FROM analysis.m5_protected_areas
    WHERE year = 2025
) m5 ON buf.gid = m5.runap_gid
ORDER BY m5.built_buffer_ha DESC NULLS LAST;
