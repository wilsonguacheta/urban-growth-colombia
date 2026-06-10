-- Módulo 1: Consultas de análisis de crecimiento urbano

-- Expansión total 1975-2025 por ciudad
SELECT
    u.uc_nm,
    g75.built_area_ha  AS built_1975_ha,
    g25.built_area_ha  AS built_2025_ha,
    (g25.built_area_ha - g75.built_area_ha) AS expansion_total_ha,
    ROUND(
        (g25.built_area_ha / NULLIF(g75.built_area_ha, 0) - 1) * 100, 1
    )                  AS crecimiento_50anos_pct
FROM raw.ucdb_colombia u
LEFT JOIN analysis.m1_urban_growth g75 ON u.uc_id = g75.uc_id AND g75.year = 1975
LEFT JOIN analysis.m1_urban_growth g25 ON u.uc_id = g25.uc_id AND g25.year = 2025
WHERE g25.built_area_ha IS NOT NULL
ORDER BY expansion_total_ha DESC NULLS LAST;

-- Top 10 ciudades con mayor crecimiento en el último período (2020→2025)
SELECT
    uc_nm,
    year_prev,
    year,
    built_area_ha,
    delta_m2 / 10000.0  AS delta_ha,
    growth_rate_pct
FROM analysis.m1_urban_growth
WHERE year = 2025 AND year_prev = 2020
ORDER BY growth_rate_pct DESC NULLS LAST
LIMIT 10;

-- Serie temporal completa para las ciudades piloto
SELECT
    uc_nm,
    year,
    built_area_ha,
    growth_rate_pct
FROM analysis.m1_urban_growth
WHERE uc_nm IN ('Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga')
ORDER BY uc_nm, year;
