-- Módulo 4: Exposición a Amenaza por Inundación (vectorial)
-- Todas las geometrías en EPSG:9377 → ST_Area() retorna m² directamente.

-- Superficie construida en zonas inundables por ciudad
SELECT
    u.uc_nm,
    COUNT(f.gid)                                          AS n_poligonos_flood,
    ST_Area(ST_Union(ST_Intersection(u.geom, f.geom))) / 1e4
                                                          AS area_inundable_ha,
    ST_Area(u.geom) / 1e4                                AS area_ciudad_ha,
    ROUND(
        (ST_Area(ST_Union(ST_Intersection(u.geom, f.geom))) /
        NULLIF(ST_Area(u.geom), 0) * 100)::NUMERIC, 2
    )                                                     AS pct_ciudad_inundable
FROM raw.ucdb_colombia u
JOIN raw.amenaza_flood f ON ST_Intersects(u.geom, f.geom)
WHERE ST_IsValid(u.geom) AND ST_IsValid(f.geom)
GROUP BY u.uc_nm, u.geom
ORDER BY pct_ciudad_inundable DESC NULLS LAST;

-- Insertar resultados flood en tabla de análisis.
-- La capa amenaza_flood es estática (año de referencia 2020).
-- pop_exposed y pct_pop_exposed son calculados en Python (m4_indicadores.py)
-- y actualizados via UPDATE tras este INSERT.
INSERT INTO analysis.m4_hazard_exposure
    (uc_id, uc_nm, year, hazard_type, hazard_class,
     pop_exposed, built_exposed_m2, pct_pop_exposed, pct_built_exposed)
SELECT
    u.uc_id,
    u.uc_nm,
    2020                                               AS year,
    'flood'                                            AS hazard_type,
    NULL                                               AS hazard_class,
    NULL                                               AS pop_exposed,
    ST_Area(ST_Union(ST_Intersection(u.geom, f.geom))) AS built_exposed_m2,
    NULL                                               AS pct_pop_exposed,
    ROUND(
        (ST_Area(ST_Union(ST_Intersection(u.geom, f.geom))) /
        NULLIF(ST_Area(u.geom), 0) * 100)::NUMERIC, 2
    )                                                  AS pct_built_exposed
FROM raw.ucdb_colombia u
JOIN raw.amenaza_flood f ON ST_Intersects(u.geom, f.geom)
WHERE ST_IsValid(u.geom) AND ST_IsValid(f.geom)
GROUP BY u.uc_id, u.uc_nm, u.geom
ON CONFLICT (uc_id, year, hazard_type, hazard_class) DO NOTHING;
