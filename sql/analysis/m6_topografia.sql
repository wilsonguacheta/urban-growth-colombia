-- Módulo 6: Influencia de la Topografía en el Crecimiento Urbano

-- Perfil topográfico del área construida por ciudad y año
SELECT
    uc_nm,
    year,
    ROUND(mean_elevation_m, 1)       AS elevacion_media_m,
    ROUND(mean_slope_deg, 2)         AS pendiente_media_deg,
    ROUND(pct_area_steep, 2)         AS pct_area_mayor_15deg
FROM analysis.m6_topography
WHERE year IN (2000, 2010, 2020, 2025)
ORDER BY year, mean_slope_deg DESC NULLS LAST;

-- Tendencia: ciudades que crecen hacia zonas más escarpadas
SELECT
    t25.uc_nm,
    ROUND(t00.mean_slope_deg, 2)     AS pendiente_2000,
    ROUND(t25.mean_slope_deg, 2)     AS pendiente_2025,
    ROUND(t25.mean_slope_deg - t00.mean_slope_deg, 2) AS delta_pendiente,
    ROUND(t25.slope_new_growth, 2)   AS pendiente_expansion_reciente
FROM analysis.m6_topography t25
JOIN analysis.m6_topography t00 ON t25.uc_id = t00.uc_id AND t00.year = 2000
WHERE t25.year = 2025
  AND t25.mean_slope_deg IS NOT NULL
ORDER BY delta_pendiente DESC NULLS LAST;

-- Ciudades con mayor % de área construida en pendiente > 15° (riesgo topográfico)
SELECT
    uc_nm,
    year,
    ROUND(pct_area_steep, 2)         AS pct_area_mayor_15deg,
    ROUND(mean_elevation_m, 1)       AS elevacion_media_m
FROM analysis.m6_topography
WHERE year = 2025
  AND pct_area_steep IS NOT NULL
ORDER BY pct_area_steep DESC NULLS LAST
LIMIT 15;
