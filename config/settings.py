from pathlib import Path

# ── Raíz de datos originales ──────────────────────────────────────────────────
# Los datasets crudos viven en el directorio padre de urban-growth-colombia/
RAW_DATA_ROOT = Path(__file__).resolve().parents[2]

# ── Raíz del proyecto ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR     = PROJECT_ROOT / "data"

EXTRACTED_DIR = DATA_DIR / "extracted"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR      = DATA_DIR / "logs"

MOSAICS_DIR = PROCESSED_DIR / "mosaics"
CLIPPED_DIR = PROCESSED_DIR / "clipped"
SLOPE_DIR   = PROCESSED_DIR / "slope"
VECTORS_DIR = PROCESSED_DIR / "vectors"

# ── Fuentes de datos originales ───────────────────────────────────────────────
SOURCES = {
    "built_s":    RAW_DATA_ROOT / "GHS-BUILT-S",
    "pop":        RAW_DATA_ROOT / "GHS-POP",
    "smod":       RAW_DATA_ROOT / "GHS-SMOD",
    "ucdb":       RAW_DATA_ROOT / "GHS-UCDB",
    "runap":      RAW_DATA_ROOT / "RUNAP",
    "ghsl_grid":  RAW_DATA_ROOT / "GHS-POP" / "2025",
    "dem":        RAW_DATA_ROOT / "DEM-Col" / "dem-col.tif",
    "amenaza_mm": RAW_DATA_ROOT / "AMENAZA-MM" / "class_amen.tif",
    "amenaza_flood": RAW_DATA_ROOT / "AMENAZA-FLOOD",
    "hansen":     RAW_DATA_ROOT / "Hansen Global Forest Change",
    "limite":     RAW_DATA_ROOT / "LIMITE_COL" / "LIMITE_COLOMBIA.shp",
}

# ── CRS y resolución estándar ─────────────────────────────────────────────────
TARGET_CRS  = "EPSG:9377"   # MAGNA-SIRGAS 2018 / Colombia Origen Nacional
TARGET_RES  = 100           # metros

# ── Bounding box de Colombia en EPSG:9377 (xmin, ymin, xmax, ymax) ────────────
# Derivado de limite_colombia_9377.gpkg; EPSG:9377 usa False easting ~5_000_000 m.
COLOMBIA_BBOX_9377 = (4_047_000, 1_090_000, 5_685_000, 3_054_000)

# ── Años disponibles por producto GHSL ───────────────────────────────────────
GHSL_YEARS = {
    "built_s": [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2018, 2020, 2025, 2030],
    "pop":     [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030],
    "smod":    [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030],
}
# Años comunes para comparación temporal (excluye 2018 exclusivo de built_s)
COMMON_YEARS = [y for y in GHSL_YEARS["built_s"] if y != 2018]

# ── Bounding box de Colombia en EPSG:4326 (WGS84, grados decimales) ──────────
# xmin, ymin, xmax, ymax — márgenes amplios para no cortar datos en bordes.
COLOMBIA_BBOX_4326 = (-80.0, -5.0, -66.0, 14.0)

# ── Bounding box de Colombia en EPSG:54009 (Mollweide, metros) ────────────────
# Usado durante el merge para limitar la extensión y evitar mosaicos globales.
# Márgenes amplios para no cortar datos en los bordes del país.
COLOMBIA_BBOX_54009 = (-9_000_000, -600_000, -6_900_000, 1_600_000)

# ── Parámetros de mosaico GHSL ────────────────────────────────────────────────
GHSL_TILE_PATTERN = "*.tif"
GHSL_NODATA = {
    "built_s": 65535,   # uint16
    "pop":     65535,   # uint16 / float32
    "smod":    255,     # uint8 — 65535 desborda uint8 (máx 255)
}

# ── Parámetros Hansen ─────────────────────────────────────────────────────────
HANSEN_NODATA    = 255   # valor sin datos (verificar en auditoría)
HANSEN_VALID_MAX = 25    # valores 1-25 = año de pérdida 2001-2025

# ── Parámetros DEM ────────────────────────────────────────────────────────────
DEM_NODATA = -999.0

# ── Parámetros AMENAZA-MM ─────────────────────────────────────────────────────
MM_NODATA      = 0
MM_CLASS_RANGE = (1, 4)

# ── Conversión de unidades raster ─────────────────────────────────────────────
PIXEL_HA = (TARGET_RES ** 2) / 10_000   # hectáreas por píxel (0.01 ha @ 100m×100m)

# ── Compresión y tiling para archivos de salida ───────────────────────────────
RASTER_WRITE_PROFILE = {
    "compress":   "lzw",
    "tiled":      True,
    "blockxsize": 512,
    "blockysize": 512,
    "driver":     "GTiff",
}

# ── Fase piloto: ciudades de análisis prioritario ─────────────────────────────
PILOT_CITIES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga"]
