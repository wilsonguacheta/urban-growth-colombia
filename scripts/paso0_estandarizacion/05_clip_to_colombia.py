"""
Paso 0 - Script 05: Reproyecta, remuestrea a 100m y recorta todos los rasters
al polígono real de Colombia (LIMITE_COLOMBIA.shp) en EPSG:9377.

Operación en un solo paso por dataset para minimizar pérdida de precisión.
Todos los rasters de salida: EPSG:9377, 100m × 100m, máscara del límite Colombia
con buffer de 500m para no perder píxeles de borde.
Los ~40 datasets se procesan en paralelo con ProcessPoolExecutor.
PROJ_DATA se obtiene de pyproj via subprocess y se hereda por los workers spawn.
"""
import math
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Literal


def _ensure_proj_data() -> str:
    """
    Fija PROJ_DATA al proj.db correcto para rasterio/GDAL 3.12 (schema >= 6).
    Prioridad: rasterio/proj_data (schema 6) > pyproj (schema 4, demasiado viejo).
    """
    existing = os.environ.get("PROJ_DATA", "")
    if existing and (Path(existing) / "proj.db").exists():
        return existing

    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util; from pathlib import Path; "
             "spec = importlib.util.find_spec('rasterio'); "
             "p = Path(spec.origin).parent / 'proj_data'; "
             "print(p if (p / 'proj.db').exists() else '')"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            p = r.stdout.strip()
            if p and (Path(p) / "proj.db").exists():
                os.environ["PROJ_DATA"] = p
                os.environ["PROJ_LIB"]  = p
                return p
    except Exception:
        pass

    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "import pyproj; print(pyproj.datadir.get_data_dir())"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            p = r.stdout.strip()
            if p and (Path(p) / "proj.db").exists():
                os.environ["PROJ_DATA"] = p
                os.environ["PROJ_LIB"]  = p
                return p
    except Exception:
        pass
    return ""


# Ejecuta en el proceso padre → el resultado se hereda por los workers spawn
_PROJ_DATA = _ensure_proj_data()

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.mask import mask as rio_mask
from rasterio.warp import calculate_default_transform, reproject
import geopandas as gpd
from shapely.geometry import mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    SOURCES, MOSAICS_DIR, CLIPPED_DIR, VECTORS_DIR,
    TARGET_CRS, TARGET_RES, GHSL_YEARS, RASTER_WRITE_PROFILE,
    DEM_NODATA, MM_NODATA, HANSEN_NODATA, GHSL_NODATA,
)

ResamplingType = Literal["bilinear", "nearest"]

TARGET = CRS.from_string(TARGET_CRS)

# Buffer al límite Colombia para no perder píxeles de borde (5 px @ 100m)
CLIP_BUFFER_M = 500.0


def load_colombia_mask() -> list:
    """Carga el límite de Colombia en EPSG:9377 con buffer y retorna geometrías para mask."""
    limite_path = VECTORS_DIR / "limite_colombia_9377.gpkg"
    if not limite_path.exists():
        print("  ! limite_colombia_9377.gpkg no encontrado en vectors/")
        print("    Ejecuta primero 06_reproject_vectors.py")
        sys.exit(1)
    gdf = gpd.read_file(limite_path)
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(CLIP_BUFFER_M)
    return [mapping(geom) for geom in gdf.geometry]


def warp_and_clip(
    src_path: Path,
    dst_path: Path,
    colombia_geoms: list,
    src_nodata,
    dst_nodata,
    resampling_method: ResamplingType,
) -> None:
    """
    Reproyecta src_path a EPSG:9377 y 100m, luego recorta con la máscara Colombia.
    """
    if dst_path.exists():
        print(f"  → {dst_path.name}  (ya existe, omitido)", flush=True)
        return
    _ensure_proj_data()   # workers heredan PROJ_DATA; esta llamada es inmediata
    resamp  = Resampling.bilinear if resampling_method == "bilinear" else Resampling.nearest
    _target = CRS.from_string(TARGET_CRS)   # re-crear en el worker

    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, _target, src.width, src.height, *src.bounds,
            resolution=TARGET_RES,
        )

        meta = src.meta.copy()
        meta.update({
            **RASTER_WRITE_PROFILE,
            "crs":       _target,
            "transform": transform,
            "width":     width,
            "height":    height,
            "nodata":    dst_nodata if dst_nodata is not None else src_nodata,
        })

        data_reproj = np.full(
            (src.count, height, width),
            fill_value=dst_nodata if dst_nodata is not None else (src_nodata or 0),
            dtype=meta["dtype"],
        )

        reproject(
            source=rasterio.band(src, list(range(1, src.count + 1))),
            destination=data_reproj,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=_target,
            resampling=resamp,
            src_nodata=src_nodata,
            dst_nodata=dst_nodata,
        )

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with rasterio.open(tmp_path, "w", **meta) as tmp_dst:
            tmp_dst.write(data_reproj)

        with rasterio.open(tmp_path) as tmp_src:
            clipped, clip_transform = rio_mask(
                tmp_src, colombia_geoms,
                crop=True, filled=True,
                nodata=dst_nodata if dst_nodata is not None else (src_nodata or 0),
            )

        meta.update({
            "height":    clipped.shape[1],
            "width":     clipped.shape[2],
            "transform": clip_transform,
        })

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dst_path, "w", **meta) as dst:
            dst.write(clipped)

    finally:
        os.unlink(tmp_path)

    size_mb = dst_path.stat().st_size / 1e6
    print(f"  ✓ {dst_path.name}  ({size_mb:.1f} MB)", flush=True)


def main():
    if _PROJ_DATA:
        print(f"  PROJ_DATA -> {_PROJ_DATA}", flush=True)
    else:
        print("  ! PROJ_DATA no resuelto -- puede haber conflicto con PostgreSQL PROJ", flush=True)

    CLIPPED_DIR.mkdir(parents=True, exist_ok=True)
    colombia_geoms = load_colombia_mask()

    tasks = []

    for year in GHSL_YEARS["built_s"]:
        src = (MOSAICS_DIR / "built_s_2018_mosaic_54009_100m.tif" if year == 2018
               else MOSAICS_DIR / f"built_s_{year}_mosaic_54009.tif")
        tasks.append((src, CLIPPED_DIR / f"built_s_{year}_col.tif",
                      colombia_geoms, GHSL_NODATA["built_s"], GHSL_NODATA["built_s"], "bilinear"))

    for year in GHSL_YEARS["pop"]:
        src = MOSAICS_DIR / f"pop_{year}_mosaic_54009.tif"
        tasks.append((src, CLIPPED_DIR / f"pop_{year}_col.tif",
                      colombia_geoms, GHSL_NODATA["pop"], GHSL_NODATA["pop"], "bilinear"))

    for year in GHSL_YEARS["smod"]:
        src = MOSAICS_DIR / f"smod_{year}_mosaic_54009.tif"
        tasks.append((src, CLIPPED_DIR / f"smod_{year}_col.tif",
                      colombia_geoms, GHSL_NODATA["smod"], GHSL_NODATA["smod"], "nearest"))

    tasks += [
        (MOSAICS_DIR / "hansen_lossyear_mosaic_4326.tif", CLIPPED_DIR / "hansen_col.tif",
         colombia_geoms, HANSEN_NODATA, HANSEN_NODATA, "nearest"),
        (SOURCES["dem"], CLIPPED_DIR / "dem_col.tif",
         colombia_geoms, DEM_NODATA, DEM_NODATA, "bilinear"),
        (SOURCES["amenaza_mm"], CLIPPED_DIR / "amenaza_mm_col.tif",
         colombia_geoms, MM_NODATA, MM_NODATA, "nearest"),
    ]

    tasks = [(s, d, g, sn, dn, rm) for s, d, g, sn, dn, rm in tasks if s.exists()]

    n_workers = min(len(tasks), 4)   # cap: pop/DEM ocupan ~2 GB cada worker
    print(f"\n  {len(tasks)} rasters · {n_workers} workers", flush=True)

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(warp_and_clip, s, d, g, sn, dn, rm): d.name
            for s, d, g, sn, dn, rm in tasks
        }
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ✗ {futures[f]}: {e}", flush=True)

    print("\n── Clip completo. Todos los rasters en EPSG:9377 @ 100m")


if __name__ == "__main__":
    main()
