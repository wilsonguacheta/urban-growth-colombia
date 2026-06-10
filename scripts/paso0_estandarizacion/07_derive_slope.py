"""
Paso 0 - Script 07: Deriva la pendiente (grados) desde el DEM recortado.
Entrada:  processed/clipped/dem_col.tif  (EPSG:9377, 100m)
Salida:   processed/slope/slope_col.tif  (EPSG:9377, 100m, valores en grados)

El DEM ya está en EPSG:9377 (metros), por lo que el gradiente se calcula
directamente en metros usando la resolución de pixel de 100m.
"""
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import CLIPPED_DIR, SLOPE_DIR, DEM_NODATA, RASTER_WRITE_PROFILE, TARGET_RES


def main():
    SLOPE_DIR.mkdir(parents=True, exist_ok=True)

    dem_path   = CLIPPED_DIR / "dem_col.tif"
    slope_path = SLOPE_DIR   / "slope_col.tif"

    if not dem_path.exists():
        print(f"✗ No encontrado: {dem_path}")
        print("  Ejecuta primero 05_clip_to_colombia.py")
        sys.exit(1)

    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float64)
        meta = src.meta.copy()
        res_x = abs(src.transform.a)  # metros (EPSG:9377)
        res_y = abs(src.transform.e)

    # Enmascarar nodata
    dem[dem == DEM_NODATA] = np.nan

    # Gradiente en x e y (en metros/metro → adimensional)
    gy, gx = np.gradient(dem, res_y, res_x)

    # Pendiente en grados
    slope = np.degrees(np.arctan(np.sqrt(gx**2 + gy**2)))

    # Restaurar nodata donde el DEM era nodata
    slope_out = slope.astype(np.float32)
    slope_out[np.isnan(dem)] = DEM_NODATA

    meta.update({
        **RASTER_WRITE_PROFILE,
        "dtype":  "float32",
        "nodata": DEM_NODATA,
        "count":  1,
    })

    with rasterio.open(slope_path, "w", **meta) as dst:
        dst.write(slope_out, 1)

    valid_pixels = np.sum(~np.isnan(dem))
    size_mb = slope_path.stat().st_size / 1e6
    print(f"✓ {slope_path.name}  ({size_mb:.1f} MB)")
    print(f"  Resolución: {res_x:.0f}m × {res_y:.0f}m  (EPSG:9377)")
    print(f"  Pendiente: min={np.nanmin(slope):.2f}° | max={np.nanmax(slope):.2f}° | "
          f"media={np.nanmean(slope):.2f}°")
    print(f"  Píxeles válidos: {valid_pixels:,}")


if __name__ == "__main__":
    main()
