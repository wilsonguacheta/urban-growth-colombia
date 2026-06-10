-- DDL 04: Índices espaciales y columnas frecuentemente consultadas

-- ── Vectores raw ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ucdb_geom   ON raw.ucdb_colombia  USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_runap_geom  ON raw.runap           USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_flood_geom  ON raw.amenaza_flood   USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_limite_geom ON raw.limite_colombia USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_ucdb_uc_id  ON raw.ucdb_colombia(uc_id);
CREATE INDEX IF NOT EXISTS idx_runap_cat   ON raw.runap(categoria);

-- ── Catálogo de rasters ───────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_catalog_product ON catalog.raster_catalog(product);
CREATE INDEX IF NOT EXISTS idx_catalog_year    ON catalog.raster_catalog(year);

-- ── Tablas de análisis — índices individuales ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_m1_uc_id ON analysis.m1_urban_growth(uc_id);
CREATE INDEX IF NOT EXISTS idx_m1_year  ON analysis.m1_urban_growth(year);

CREATE INDEX IF NOT EXISTS idx_m2_uc_id ON analysis.m2_population_pressure(uc_id);
CREATE INDEX IF NOT EXISTS idx_m2_year  ON analysis.m2_population_pressure(year);

CREATE INDEX IF NOT EXISTS idx_m3_uc_id ON analysis.m3_deforestation(uc_id);

CREATE INDEX IF NOT EXISTS idx_m4_uc_id       ON analysis.m4_hazard_exposure(uc_id);
CREATE INDEX IF NOT EXISTS idx_m4_hazard_type ON analysis.m4_hazard_exposure(hazard_type);

CREATE INDEX IF NOT EXISTS idx_m5_runap_gid ON analysis.m5_protected_areas(runap_gid);
CREATE INDEX IF NOT EXISTS idx_m5_dist_uc   ON analysis.m5_city_ap_distances(uc_id);

CREATE INDEX IF NOT EXISTS idx_m6_uc_id ON analysis.m6_topography(uc_id);
CREATE INDEX IF NOT EXISTS idx_m6_year  ON analysis.m6_topography(year);

-- ── Índices compuestos para queries temporales frecuentes ─────────────────────
CREATE INDEX IF NOT EXISTS idx_m1_uc_id_year ON analysis.m1_urban_growth(uc_id, year);
CREATE INDEX IF NOT EXISTS idx_m2_uc_id_year ON analysis.m2_population_pressure(uc_id, year);
CREATE INDEX IF NOT EXISTS idx_m4_uc_year    ON analysis.m4_hazard_exposure(uc_id, year);
CREATE INDEX IF NOT EXISTS idx_m6_uc_id_year ON analysis.m6_topography(uc_id, year);
