-- DDL 01: Creación de schemas y extensiones
-- CRS del proyecto: EPSG:9377 (MAGNA-SIRGAS 2018 / Colombia Origen Nacional)

CREATE EXTENSION IF NOT EXISTS postgis;

-- Schemas por dominio
CREATE SCHEMA IF NOT EXISTS raw;        -- Vectores cargados desde datos procesados
CREATE SCHEMA IF NOT EXISTS catalog;    -- Catálogo de metadatos de rasters
CREATE SCHEMA IF NOT EXISTS analysis;   -- Resultados de los 6 módulos analíticos
CREATE SCHEMA IF NOT EXISTS staging;    -- Tablas intermedias de cálculo
