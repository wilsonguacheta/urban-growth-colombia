"""
Paso 0 - Script 04: Normaliza GHS-BUILT-S 2018 de 10m a 100m.

Downsampling en el MISMO CRS (ESRI:54009) → no hay reproyeccion real.
Estrategia: numpy reshape + sum por bloques.
  - src.read(window=chunk) → uint8 chunk (~300 MB por franja)
  - reshape(dst_h, 10, dst_w, 10).sum(axis=(1,3)) → suma 10×10 bloques
  - ~5-10 seg por franja vs horas con rasterio.warp.reproject
  - Nodata (255) excluido de la suma; pixels de salida con todos nodata → 65535
MAX_WORKERS=2 (pico ~600 MB por worker = 1.2 GB total).
"""
import gc
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np


def _ensure_proj_data() -> str:
    """
    Fija PROJ_DATA al proj.db correcto para rasterio/GDAL 3.12 (schema >= 6).
    Prioridad: rasterio/proj_data (schema 6) > pyproj (schema 4, demasiado viejo).
    """
    existing = os.environ.get("PROJ_DATA", "")
    if existing and (Path(existing) / "proj.db").exists():
        return existing

    # 1. rasterio/proj_data — schema 6, compatible con GDAL 3.12. Se usa
    #    importlib.util.find_spec para no importar rasterio antes de fijar PROJ_DATA.
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

    # 2. pyproj fallback (schema 4 — puede fallar con GDAL 3.12)
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


_PROJ_DATA = _ensure_proj_data()

import rasterio
from rasterio.merge import merge
from rasterio.windows import Window
from rasterio.windows import from_bounds as window_from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    EXTRACTED_DIR, MOSAICS_DIR, RASTER_WRITE_PROFILE,
    COLOMBIA_BBOX_54009, TARGET_RES,
)

SCALE_FACTOR    = 10        # 10m → 100m
SRC_NODATA      = 255
DST_NODATA      = 65535
MAX_WORKERS     = 2
CHUNK_DST_ROWS  = 300       # = 3000 src rows (~300 MB por franja, pico ~600 MB)


def _block_sum(src_data: np.ndarray, dst_h: int, dst_w: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Downsample src_data (uint8, shape dst_h*10 x dst_w*10) via reshape+sum.
    Retorna (dst_sum uint16, all_nodata bool).
    Nodata pixels (SRC_NODATA=255) se excluyen de la suma.
    """
    # Marcar y anular nodata antes de sumar
    nodata_mask = (src_data == SRC_NODATA)            # bool, misma forma
    src_data[nodata_mask] = 0                          # in-place, no copia

    reshaped   = src_data.reshape(dst_h, SCALE_FACTOR, dst_w, SCALE_FACTOR)
    dst_sum    = reshaped.sum(axis=(1, 3), dtype=np.uint32).astype(np.uint16)

    mask_rs    = nodata_mask.reshape(dst_h, SCALE_FACTOR, dst_w, SCALE_FACTOR)
    all_nodata = mask_rs.all(axis=(1, 3))              # True donde todos 100 px son nodata

    return dst_sum, all_nodata


def reproject_tile(src_path: Path, dst_path: Path) -> None:
    """
    Clip + downsample 10m→100m con numpy block-sum en franjas de CHUNK_DST_ROWS filas.
    No usa rasterio.warp.reproject (lento para same-CRS downsampling).
    """
    _ensure_proj_data()

    with rasterio.open(src_path) as src:
        tb = src.bounds

        xmin = max(tb.left,   COLOMBIA_BBOX_54009[0])
        ymin = max(tb.bottom, COLOMBIA_BBOX_54009[1])
        xmax = min(tb.right,  COLOMBIA_BBOX_54009[2])
        ymax = min(tb.top,    COLOMBIA_BBOX_54009[3])

        if xmin >= xmax or ymin >= ymax:
            print(f"  ~ {src_path.name}: sin interseccion con Colombia -- omitido",
                  flush=True)
            return

        _w      = window_from_bounds(xmin, ymin, xmax, ymax, src.transform)
        col_off = int(math.floor(_w.col_off))
        row_off = int(math.floor(_w.row_off))

        total_src_w = (int(math.ceil(_w.width))  // SCALE_FACTOR) * SCALE_FACTOR
        total_src_h = (int(math.ceil(_w.height)) // SCALE_FACTOR) * SCALE_FACTOR
        total_dst_w = total_src_w // SCALE_FACTOR
        total_dst_h = total_src_h // SCALE_FACTOR

        if total_src_w <= 0 or total_src_h <= 0:
            print(f"  ~ {src_path.name}: interseccion trivial -- omitido", flush=True)
            return

        full_win      = Window(col_off, row_off, total_src_w, total_src_h)
        src_transform = src.window_transform(full_win)
        dst_transform = src_transform * src_transform.scale(SCALE_FACTOR, SCALE_FACTOR)
        src_meta      = src.meta.copy()

    src_meta.update({
        **RASTER_WRITE_PROFILE,
        "count": 1, "width": total_dst_w, "height": total_dst_h,
        "transform": dst_transform, "dtype": "uint16", "nodata": DST_NODATA,
    })

    n_chunks = math.ceil(total_dst_h / CHUNK_DST_ROWS)

    with rasterio.open(src_path) as src, rasterio.open(dst_path, "w", **src_meta) as dst:
        for ci in range(n_chunks):
            dst_row   = ci * CHUNK_DST_ROWS
            adh       = min(CHUNK_DST_ROWS, total_dst_h - dst_row)   # dst rows in chunk
            ash       = adh * SCALE_FACTOR                            # src rows in chunk
            src_row   = row_off + dst_row * SCALE_FACTOR

            src_win   = Window(col_off, src_row, total_src_w, ash)
            src_data  = src.read(1, window=src_win)   # uint8, adh*10 × dst_w*10

            dst_chunk, all_nodata = _block_sum(src_data, adh, total_dst_w)
            dst_chunk[all_nodata] = DST_NODATA

            dst.write(dst_chunk, 1,
                      window=Window(0, dst_row, total_dst_w, adh))

            del src_data, dst_chunk, all_nodata
            gc.collect()

    size_mb = dst_path.stat().st_size / 1e6
    print(f"  ok {dst_path.name}  ({total_dst_w}x{total_dst_h} px, "
          f"{n_chunks} franjas, {size_mb:.1f} MB)", flush=True)


def main():
    if _PROJ_DATA:
        print(f"  PROJ_DATA -> {_PROJ_DATA}", flush=True)
    else:
        print("  ! PROJ_DATA no resuelto -- puede haber conflicto con PostgreSQL PROJ",
              flush=True)

    tile_dir = EXTRACTED_DIR / "ghsl" / "built_s" / "2018"
    tiles    = sorted(tile_dir.rglob("*.tif"))
    if not tiles:
        print(f"! Sin tiles en {tile_dir}")
        sys.exit(1)

    tmp_dir = MOSAICS_DIR / "_tmp_built2018_100m"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for f in tmp_dir.glob("*.tif"):
        f.unlink()

    n_workers = min(MAX_WORKERS, len(tiles))
    chunk_src_mb = CHUNK_DST_ROWS * SCALE_FACTOR * 100_000 / 1e6  # estimado
    print(f"  {len(tiles)} tiles, {n_workers} workers, "
          f"numpy block-sum, ~{chunk_src_mb:.0f} MB/chunk...", flush=True)

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        tasks   = [(tile, tmp_dir / tile.name) for tile in tiles]
        futures = {executor.submit(reproject_tile, src, dst): src.name
                   for src, dst in tasks}
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ! {futures[f]}: {e}", flush=True)

    tmp_tiles = sorted(tmp_dir.glob("*.tif"))
    if not tmp_tiles:
        print("! Sin tiles procesados -- revisa los mensajes anteriores")
        sys.exit(1)

    print(f"  Mergeando {len(tmp_tiles)} tiles...", flush=True)
    dst_path   = MOSAICS_DIR / "built_s_2018_mosaic_54009_100m.tif"
    datasets   = [rasterio.open(t) for t in tmp_tiles]
    first_meta = None
    try:
        mosaic, transform = merge(datasets, method="last", nodata=DST_NODATA)
        first_meta = datasets[0].meta.copy()
    finally:
        for ds in datasets:
            ds.close()
    del datasets
    gc.collect()

    first_meta.update({
        **RASTER_WRITE_PROFILE,
        "count": 1, "height": mosaic.shape[1], "width": mosaic.shape[2],
        "transform": transform, "dtype": "uint16", "nodata": DST_NODATA,
    })
    with rasterio.open(dst_path, "w", **first_meta) as dst:
        dst.write(mosaic)
    del mosaic
    gc.collect()

    import shutil
    shutil.rmtree(tmp_dir)

    size_mb = dst_path.stat().st_size / 1e6
    print(f"\n  {dst_path.name}  ({len(tmp_tiles)} tiles, @{TARGET_RES}m, {size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
