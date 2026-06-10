-- DDL 03: Catálogo de rasters y tablas de resultados analíticos

-- ── Catálogo de rasters ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS catalog.raster_catalog (
    id            SERIAL PRIMARY KEY,
    product       VARCHAR(50)   NOT NULL,   -- 'built_s', 'pop', 'smod', 'hansen', 'dem', 'amenaza_mm', 'slope'
    year          INTEGER,                  -- NULL para datos estáticos (DEM, Hansen, AMENAZA)
    resolution_m  NUMERIC       NOT NULL,   -- Resolución en metros
    crs_epsg      INTEGER       NOT NULL,   -- EPSG del CRS
    file_path     TEXT          NOT NULL,   -- Ruta absoluta al TIF procesado
    bbox_xmin     NUMERIC,
    ymin          NUMERIC,
    bbox_xmax     NUMERIC,
    ymax          NUMERIC,
    width_px      INTEGER,
    height_px     INTEGER,
    nodata_value  NUMERIC,
    dtype         VARCHAR(20),
    file_size_mb  NUMERIC,
    processed_at  TIMESTAMP DEFAULT NOW()
);

-- ── Resultados Módulo 1: Crecimiento Urbano ──────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis.m1_urban_growth (
    id              SERIAL PRIMARY KEY,
    uc_id           INTEGER,
    uc_nm           VARCHAR(200),
    year            INTEGER NOT NULL,
    built_area_m2   NUMERIC,
    built_area_ha   NUMERIC GENERATED ALWAYS AS (built_area_m2 / 10000.0) STORED,
    year_prev       INTEGER,
    delta_m2        NUMERIC,
    growth_rate_pct NUMERIC,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, year)
);

-- ── Resultados Módulo 2: Presión Poblacional ─────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis.m2_population_pressure (
    id              SERIAL PRIMARY KEY,
    uc_id           INTEGER,
    uc_nm           VARCHAR(200),
    year            INTEGER NOT NULL,
    pop_total       NUMERIC,
    built_area_m2   NUMERIC,
    pop_density     NUMERIC,     -- hab/km²
    sprawl_index    NUMERIC,     -- ratio Δ%área / Δ%pop
    densification   BOOLEAN,     -- TRUE si pop crece más rápido que área
    year_prev       INTEGER,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, year)
);

-- ── Resultados Módulo 3: Deforestación ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis.m3_deforestation (
    id                        SERIAL PRIMARY KEY,
    uc_id                     INTEGER,
    uc_nm                     VARCHAR(200),
    buffer_km                 NUMERIC NOT NULL,
    forest_loss_ha            NUMERIC,
    expansion_ha              NUMERIC,
    overlap_ha                NUMERIC,
    pct_urban_on_deforested   NUMERIC,
    created_at                TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, buffer_km)
);

-- ── Resultados Módulo 4: Exposición a Amenazas ───────────────────────────────
CREATE TABLE IF NOT EXISTS analysis.m4_hazard_exposure (
    id                SERIAL PRIMARY KEY,
    uc_id             INTEGER,
    uc_nm             VARCHAR(200),
    year              INTEGER NOT NULL,
    hazard_type       VARCHAR(20) NOT NULL,  -- 'flood' | 'mass_movement'
    hazard_class      INTEGER,               -- 1-4 para MM; NULL para flood
    pop_exposed       NUMERIC,
    built_exposed_m2  NUMERIC,
    pct_pop_exposed   NUMERIC,
    pct_built_exposed NUMERIC,
    created_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, year, hazard_type, hazard_class)
);

-- ── Resultados Módulo 5: Superficie construida dentro de cada AP ──────────────
-- Granularidad: una fila por (runap_gid, year).
CREATE TABLE IF NOT EXISTS analysis.m5_protected_areas (
    id               SERIAL PRIMARY KEY,
    runap_gid        INTEGER NOT NULL,
    runap_nombre     VARCHAR(300),
    categoria        VARCHAR(200),
    area_ha          NUMERIC,
    year             INTEGER NOT NULL,
    built_inside_m2  NUMERIC,
    built_inside_ha  NUMERIC,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(runap_gid, year)
);

-- ── Resultados Módulo 5: Distancia ciudad → AP más cercana ───────────────────
-- Granularidad: una fila por (uc_id, runap_gid) — par ciudad↔AP más cercana.
CREATE TABLE IF NOT EXISTS analysis.m5_city_ap_distances (
    id           SERIAL PRIMARY KEY,
    uc_id        INTEGER,
    uc_nm        VARCHAR(200),
    runap_gid    INTEGER,
    runap_nombre VARCHAR(300),
    dist_m       NUMERIC,
    created_at   TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, runap_gid)
);

-- ── Resultados Módulo 6: Topografía ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis.m6_topography (
    id                   SERIAL PRIMARY KEY,
    uc_id                INTEGER,
    uc_nm                VARCHAR(200),
    year                 INTEGER NOT NULL,
    mean_elevation_m     NUMERIC,
    mean_slope_deg       NUMERIC,
    pct_area_steep       NUMERIC,   -- % área con pendiente > 15°
    elevation_new_growth NUMERIC,   -- Elevación media de la expansión respecto al período anterior
    slope_new_growth     NUMERIC,   -- Pendiente media de la expansión
    created_at           TIMESTAMP DEFAULT NOW(),
    UNIQUE(uc_id, year)
);
