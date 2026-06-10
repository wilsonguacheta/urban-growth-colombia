# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Urban Growth Colombia** is an end-to-end geospatial analytics pipeline analyzing urban expansion, population dynamics, and environmental risks across Colombian cities (1975–2030). It integrates GHSL, Hansen forest loss, DEM, protected areas, and hazard datasets using PostgreSQL/PostGIS for spatial queries and Python for ETL and analysis.

Raw data lives in `C:\Users\GuachetaW\Documents\PROYECTO_2\` (parent of this repo). Processed outputs go into `data/processed/` inside this repo.

## Architecture & Data Flow

Three sequential phases, each orchestrated by its own runner script.

### Phase 0 — Standardization (`scripts/paso0_estandarizacion/`)

All raster and vector inputs are standardized to **EPSG:9377 @ 100m** GeoTIFF (LZW, 512×512 tiles).

`run_paso0.py` enforces this execution order (note: step 06 runs before 02–05):

| Step | Script | Purpose |
|------|--------|---------|
| 00 | `00_extract_zips.py` | Extract raw GHSL/UCDB/RUNAP ZIPs |
| 01 | `01_audit_crs.py` | CRS audit across all files → `data/logs/crs_audit.csv` |
| 06 | `06_reproject_vectors.py` | Reproject vectors to EPSG:9377 (**required before clip**) |
| 02 | `02_mosaic_ghsl.py` | Mosaic GHSL tiles (built_s, pop, smod) by year |
| 03 | `03_mosaic_hansen.py` | Mosaic Hansen forest loss tiles |
| 04 | `04_resample_built2018.py` | Resample BUILT-S 2018 to 100m (other years already standardized) |
| 05 | `05_clip_to_colombia.py` | Clip all rasters to Colombia boundary |
| 07 | `07_derive_slope.py` | Derive slope from DEM |
| 08 | `08_integrity_check.py` | Validate all outputs exist and have valid geometry |

### Phase 1 — Database Loading (`scripts/paso1_carga_postgis/`)

Loads reprojected vectors into PostgreSQL/PostGIS and applies DDL:

- `10_load_vectors_postgis.py` — applies `sql/ddl/*.sql` then loads vectors via `geopandas.to_postgis()`
- `11_load_rasters_postgis.py` — optionally loads rasters as PostGIS raster objects

**DB schemas:** `raw` (vectors), `catalog` (raster catalog), `analysis` (module results), `staging` (intermediate)

### Phase 2 — Analysis (`scripts/modulos_analisis/`)

Six analytical modules, each with two scripts:

- `m[N]_rasterstats.py` — extracts zonal statistics via `base_rasterstats.extract_zonal_stats()`
- `m[N]_indicadores.py` — computes derived indicators, saves to CSV

| Module | Focus |
|--------|-------|
| M1 | Urban area expansion, growth rates |
| M2 | Population growth vs. area expansion, sprawl index |
| M3 | Overlap of urban growth with Hansen forest loss (2001–2025) |
| M4 | Flood and landslide hazard exposure |
| M5 | Urban pressure on RUNAP protected areas |
| M6 | Slope/elevation influence on urban patterns |

`base_rasterstats.py` is the shared utility used by all six modules.

## Running the Pipeline

### Setup (one-time)

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Edit .env: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
```

### Paso 0 — Standardization

```bash
python scripts/paso0_estandarizacion/run_paso0.py             # all steps
python scripts/paso0_estandarizacion/run_paso0.py --from 05   # resume from step 05
python scripts/paso0_estandarizacion/run_paso0.py --only 08   # single step
```

### Paso 1 — Database Loading

```bash
python scripts/paso1_carga_postgis/10_load_vectors_postgis.py
python scripts/paso1_carga_postgis/11_load_rasters_postgis.py  # optional
```

### Módulos Analíticos

```bash
python scripts/modulos_analisis/run_modulos.py                 # all modules
python scripts/modulos_analisis/run_modulos.py --from m3       # resume from M3
python scripts/modulos_analisis/run_modulos.py --only m1       # single module
python scripts/modulos_analisis/run_modulos.py --step rs       # only rasterstats
python scripts/modulos_analisis/run_modulos.py --step ind      # only indicators
```

### Validation Notebook

```bash
jupyter notebook notebooks/00_exploracion_datos.ipynb
```

## Configuration (`config/settings.py`)

Single source of truth for all paths, CRS, years, and nodata values:

- `RAW_DATA_ROOT` — resuelve a `C:\Users\GuachetaW\Documents\PROYECTO_2\` (datasets crudos, directorio padre del repo)
- `TARGET_CRS = "EPSG:9377"` — MAGNA-SIRGAS 2018 / Colombia Origen Nacional
- `TARGET_RES = 100` — pixel resolution in meters
- `GHSL_YEARS` — per-product year lists; `built_s` includes 2018, others don't
- `COMMON_YEARS` — all GHSL years except 2018 (use this for cross-product comparisons)
- `GHSL_NODATA` — `built_s`/`pop`: 65535; `smod`: 255
- `HANSEN_NODATA = 255`; values 1–25 encode year of loss (2001–2025)
- `DEM_NODATA = -999`
- `PILOT_CITIES` — Bogotá, Medellín, Cali, Barranquilla, Cartagena, Bucaramanga

## Key Development Notes

**Step ordering matters when running scripts manually:** `06_reproject_vectors.py` must complete before `05_clip_to_colombia.py` because the clip uses the reprojected Colombia boundary. `run_paso0.py` enforces the correct order; manual invocation does not.

**COMMON_YEARS vs. GHSL_YEARS:** Always use `COMMON_YEARS` when joining or comparing across GHSL products. Using `GHSL_YEARS["built_s"]` would include 2018, which is absent from pop and smod.

**Hansen encoding:** The raster pixel value is the loss year offset (1 = 2001, 25 = 2025), not a binary mask. `0` = no loss, `255` = nodata.

**Adding a new module:**
1. Create `scripts/modulos_analisis/modulo[N]_<name>/`
2. Implement `m[N]_rasterstats.py` using `base_rasterstats.extract_zonal_stats()`
3. Implement `m[N]_indicadores.py`
4. Add a tuple to `MODULES` in `run_modulos.py`
5. Add SQL to `sql/analysis/m[N]_<name>.sql` if PostGIS integration is needed

**Logs:** Each phase writes to `data/logs/`: `extraction_log.csv`, `crs_audit.csv`, `integrity_report.csv`.
