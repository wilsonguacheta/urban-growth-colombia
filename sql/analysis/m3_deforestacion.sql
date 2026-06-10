-- Módulo 3: Urbanización y Deforestación (2000–2025)

-- Ciudades con mayor superposición entre expansión urbana y deforestación (buffer 10 km)
SELECT
    uc_nm,
    buffer_km,
    ROUND(forest_loss_ha, 1)              AS perdida_bosque_ha,
    ROUND(expansion_ha, 1)                AS expansion_urbana_ha,
    ROUND(overlap_ha, 1)                  AS solapamiento_ha,
    ROUND(pct_urban_on_deforested, 2)     AS pct_expansion_sobre_bosque
FROM analysis.m3_deforestation
WHERE buffer_km = 10
ORDER BY pct_urban_on_deforested DESC NULLS LAST;

-- Comparación entre buffers (5, 10, 20 km) para ciudades piloto
SELECT
    uc_nm,
    buffer_km,
    ROUND(forest_loss_ha, 1)              AS perdida_bosque_ha,
    ROUND(overlap_ha, 1)                  AS solapamiento_ha,
    ROUND(pct_urban_on_deforested, 2)     AS pct
FROM analysis.m3_deforestation
WHERE uc_nm IN ('Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga')
ORDER BY uc_nm, buffer_km;

-- Ranking de pérdida de bosque total en radio de 20 km
SELECT
    uc_nm,
    ROUND(forest_loss_ha, 1)              AS perdida_bosque_ha,
    ROUND(expansion_ha, 1)                AS expansion_urbana_ha,
    ROUND(pct_urban_on_deforested, 2)     AS pct_expansion_sobre_bosque
FROM analysis.m3_deforestation
WHERE buffer_km = 20
ORDER BY forest_loss_ha DESC NULLS LAST
LIMIT 20;
