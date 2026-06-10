-- Módulo 2: Presión Poblacional y Densificación
-- EPSG:9377 → distancias y áreas en metros/m²

-- Densidad poblacional por ciudad en años clave
SELECT
    uc_nm,
    year,
    ROUND(pop_total::numeric, 0)             AS poblacion,
    ROUND(built_area_m2 / 1e6, 2)            AS area_construida_km2,
    ROUND(pop_density, 1)                    AS hab_por_km2,
    sprawl_index,
    CASE
        WHEN sprawl_index > 1.5  THEN 'Sprawl severo'
        WHEN sprawl_index > 1.0  THEN 'Sprawl moderado'
        WHEN sprawl_index BETWEEN 0.8 AND 1.0 THEN 'Equilibrado'
        WHEN sprawl_index < 0.8  THEN 'Densificación'
        ELSE 'Sin datos'
    END                                      AS tipo_crecimiento
FROM analysis.m2_population_pressure
WHERE year IN (2000, 2010, 2020, 2025)
ORDER BY year, sprawl_index DESC NULLS LAST;

-- Evolución del índice de sprawl en ciudades piloto
SELECT
    uc_nm,
    year,
    year_prev,
    ROUND(pop_total::numeric, 0)             AS poblacion,
    ROUND(pop_density, 1)                    AS densidad,
    ROUND(sprawl_index, 3)                   AS sprawl_index,
    densification
FROM analysis.m2_population_pressure
WHERE uc_nm IN ('Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga')
  AND year_prev IS NOT NULL
ORDER BY uc_nm, year;

-- Ciudades con peor sprawl (área crece 2× más rápido que la población)
SELECT
    uc_nm,
    year,
    ROUND(sprawl_index, 2) AS sprawl_index,
    ROUND(pop_density, 1)  AS densidad_hab_km2
FROM analysis.m2_population_pressure
WHERE sprawl_index > 2 AND year = 2025
ORDER BY sprawl_index DESC;
