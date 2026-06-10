-- DDL 02: Tablas vectoriales (todas en EPSG:9377)

-- Límite administrativo Colombia
CREATE TABLE IF NOT EXISTS raw.limite_colombia (
    gid     SERIAL PRIMARY KEY,
    nombre  VARCHAR(100),
    geom    GEOMETRY(MULTIPOLYGON, 9377)
);

-- Centros urbanos Colombia (GHS-UCDB filtrado)
CREATE TABLE IF NOT EXISTS raw.ucdb_colombia (
    gid         SERIAL PRIMARY KEY,
    uc_id       INTEGER,
    uc_nm       VARCHAR(200),
    ctr_mn_nm   VARCHAR(100),
    pop_2000    NUMERIC,
    pop_2015    NUMERIC,
    area_ha     NUMERIC,
    geom        GEOMETRY(MULTIPOLYGON, 9377)
);

-- Áreas protegidas (RUNAP)
CREATE TABLE IF NOT EXISTS raw.runap (
    gid         SERIAL PRIMARY KEY,
    nombre      VARCHAR(300),
    categoria   VARCHAR(150),
    fecha_decl  DATE,
    area_ha     NUMERIC,
    departamento VARCHAR(100),
    geom        GEOMETRY(MULTIPOLYGON, 9377)
);

-- Amenaza por inundación (vectorial)
CREATE TABLE IF NOT EXISTS raw.amenaza_flood (
    gid       SERIAL PRIMARY KEY,
    categoria VARCHAR(100),
    geom      GEOMETRY(MULTIPOLYGON, 9377)
);
