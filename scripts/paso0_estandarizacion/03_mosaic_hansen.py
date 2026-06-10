"""
Paso 0 - Script 03: Mosaico de los 5 tiles Hansen GFC.
Salida en processed/mosaics/hansen_lossyear_mosaic_4326.tif (CRS original, sin clip aún).
method='max' preserva el año de pérdida sobre ceros en bordes de tile.
"""
import sys
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import SOURCES, MOSAICS_DIR, RASTER_WRITE_PROFILE, HANSEN_NODATA, COLOMBIA_BBOX_4326

# 100 m en grados decimales (≈ latitud media de Colombia ~5°N).
# Paso 05 reproyecta a EPSG:9377 exactamente a 100m; este valor es solo para
# reducir el mosaico a un tamaño manejable (~250 MB vs ~4 GB a 30m nativo).
HANSEN_RES_DEG = 100 / 111_320  # ≈ 0.000899°


HANSEN_TILE_PATTERN = "Hansen_GFC-*_lossyear_*.tif"


def main():
    MOSAICS_DIR.mkdir(parents=True, exist_ok=True)

    tiles = sorted(SOURCES["hansen"].glob(HANSEN_TILE_PATTERN))
    if not tiles:
        # Fallback: cualquier tif que contenga 'lossyear'
        tiles = [p for p in SOURCES["hansen"].glob("*.tif") if "lossyear" in p.name.lower()]

    if not tiles:
        print("✗ No se encontraron tiles Hansen. Verifica el directorio:")
        print(f"  {SOURCES['hansen']}")
        sys.exit(1)

    print(f"[HANSEN]  {len(tiles)} tiles encontrados:")
    for t in tiles:
        print(f"  - {t.name}")

    datasets = [rasterio.open(t) for t in tiles]
    try:
        # method="max" resuelve solapamientos entre tiles (preserva el año de pérdida).
        # Resampling.mode es la opción correcta para datos categóricos (valores 0-25);
        # Resampling.max no está soportado en operaciones de lectura de rasterio.
        mosaic, transform = merge(
            datasets,
            method="max",
            nodata=HANSEN_NODATA,
            bounds=COLOMBIA_BBOX_4326,
            res=(HANSEN_RES_DEG, HANSEN_RES_DEG),
            resampling=Resampling.mode,
        )
    finally:
        for ds in datasets:
            ds.close()

    meta = datasets[0].meta.copy()
    meta.update({
        **RASTER_WRITE_PROFILE,
        "height":    mosaic.shape[1],
        "width":     mosaic.shape[2],
        "transform": transform,
        "nodata":    HANSEN_NODATA,
    })

    out_path = MOSAICS_DIR / "hansen_lossyear_mosaic_4326.tif"
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(mosaic)

    size_mb = out_path.stat().st_size / 1e6
    print(f"\n✓ {out_path.name}  ({size_mb:.1f} MB)")
    print(f"  CRS:    {datasets[0].crs}")
    print(f"  Shape:  {mosaic.shape[1]} × {mosaic.shape[2]} px")
    print(f"  Valores: 0=sin pérdida, 1-25=año 2001-2025")


if __name__ == "__main__":
    main()
