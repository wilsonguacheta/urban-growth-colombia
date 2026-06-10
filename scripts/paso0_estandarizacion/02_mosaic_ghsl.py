"""
Paso 0 - Script 02: Mosaico de tiles GHSL por producto y año.
Genera un TIF por producto×año en processed/mosaics/ (CRS 54009, sin clip aún).
Las 36 tareas (product×year) se procesan en paralelo con ProcessPoolExecutor.
PROJ_DATA se obtiene de pyproj via subprocess y se hereda por los workers spawn.
"""
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


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
from rasterio.merge import merge

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    EXTRACTED_DIR, MOSAICS_DIR, GHSL_YEARS, GHSL_NODATA,
    RASTER_WRITE_PROFILE, COLOMBIA_BBOX_54009,
)


def mosaic_year(product: str, year: int, extracted_base: Path, output_dir: Path) -> Path | None:
    _ensure_proj_data()   # workers heredan PROJ_DATA; esta llamada es inmediata
    tile_dir = extracted_base / "ghsl" / product / str(year)
    tiles = sorted(tile_dir.rglob("*.tif"))
    if not tiles:
        print(f"  ! Sin tiles para {product}/{year}", flush=True)
        return None

    datasets = [rasterio.open(t) for t in tiles]
    try:
        native_res = abs(datasets[0].transform.a)
        src_dtype  = datasets[0].dtypes[0]
        nodata     = GHSL_NODATA.get(product)
        dtype_info = np.iinfo(src_dtype) if np.issubdtype(np.dtype(src_dtype), np.integer) else None
        if dtype_info is not None and nodata > dtype_info.max:
            nodata = int(dtype_info.max)

        mosaic, transform = merge(
            datasets, method="last", nodata=nodata, bounds=COLOMBIA_BBOX_54009,
        )
    finally:
        for ds in datasets:
            ds.close()

    out_path = output_dir / f"{product}_{year}_mosaic_54009.tif"
    meta = datasets[0].meta.copy()
    meta.update({
        **RASTER_WRITE_PROFILE,
        "height": mosaic.shape[1], "width": mosaic.shape[2],
        "transform": transform, "nodata": nodata, "dtype": src_dtype,
    })
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(mosaic)

    size_mb = out_path.stat().st_size / 1e6
    print(f"  ✓ {out_path.name}  ({len(tiles)} tiles, @{native_res:.0f}m, {size_mb:.1f} MB)", flush=True)
    return out_path


def main():
    if _PROJ_DATA:
        print(f"  PROJ_DATA -> {_PROJ_DATA}", flush=True)
    else:
        print("  ! PROJ_DATA no resuelto -- puede haber conflicto con PostgreSQL PROJ", flush=True)

    MOSAICS_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [
        (product, year)
        for product, years in GHSL_YEARS.items()
        for year in years
        if not (product == "built_s" and year == 2018)
    ]

    n_workers = min(len(tasks), os.cpu_count() or 8)
    print(f"  {len(tasks)} mosaicos · {n_workers} workers\n", flush=True)

    total_ok = total_skip = 0
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(mosaic_year, p, y, EXTRACTED_DIR, MOSAICS_DIR): (p, y)
            for p, y in tasks
        }
        for f in as_completed(futures):
            product, year = futures[f]
            try:
                result = f.result()
                total_ok += 1 if result else 0
                total_skip += 0 if result else 1
            except Exception as e:
                print(f"  ✗ {product}/{year}: {e}", flush=True)
                total_skip += 1

    print(f"\n── Mosaicos generados: {total_ok} OK | {total_skip} sin datos")


if __name__ == "__main__":
    main()
