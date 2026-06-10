"""
Módulo 3: Urbanización y Deforestación.
Cuantifica la superposición entre expansión urbana y pérdida de bosque (2000-2025).
Todos los rasters en EPSG:9377 @ 100m → no se requiere remuestreo.
"""
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import CLIPPED_DIR, VECTORS_DIR, GHSL_NODATA, HANSEN_NODATA

# Píxel de 100m × 100m = 10,000 m² = 0.01 ha
PIXEL_HA = 0.01
BUFFERS_KM = [5, 10, 20]


def _read_masked(raster_path: Path, geom, nodata) -> np.ndarray:
    """Extrae ventana del raster para una geometría y retorna array 2D.
    Retorna array vacío si la geometría no solapa el raster."""
    try:
        with rasterio.open(raster_path) as src:
            arr, _ = rio_mask(src, [mapping(geom)], crop=True, filled=True, nodata=nodata)
        return arr[0]  # banda única
    except (ValueError, rasterio.errors.WindowError):
        return np.array([[]], dtype=np.uint16)


def compute_m3(buffers_km: Iterable[int] = BUFFERS_KM) -> pd.DataFrame:
    gdf_ucdb = gpd.read_file(VECTORS_DIR / "ucdb_colombia.gpkg")

    built_2000 = CLIPPED_DIR / "built_s_2000_col.tif"
    built_2025 = CLIPPED_DIR / "built_s_2025_col.tif"
    hansen     = CLIPPED_DIR / "hansen_col.tif"

    for p in [built_2000, built_2025, hansen]:
        if not p.exists():
            raise FileNotFoundError(f"Raster requerido no encontrado: {p}")

    records = []
    for _, row in gdf_ucdb.iterrows():
        for buf_km in buffers_km:
            # Buffer en metros (EPSG:9377 está en metros)
            geom_buf = row.geometry.buffer(buf_km * 1000)

            b00 = _read_masked(built_2000, geom_buf, GHSL_NODATA["built_s"])
            b25 = _read_masked(built_2025, geom_buf, GHSL_NODATA["built_s"])
            hns = _read_masked(hansen,     geom_buf, HANSEN_NODATA)

            # Si algún array quedó vacío (geometría fuera del raster) todos los valores son 0
            if b00.size == 0 or b25.size == 0 or hns.size == 0:
                expansion_ha = overlap_ha = loss_ha = 0.0
            else:
                # Máscaras binarias (asegurar misma forma con mínimo shape)
                min_shape = (
                    min(b00.shape[0], b25.shape[0], hns.shape[0]),
                    min(b00.shape[1], b25.shape[1], hns.shape[1]),
                )
                b00 = b00[:min_shape[0], :min_shape[1]]
                b25 = b25[:min_shape[0], :min_shape[1]]
                hns = hns[:min_shape[0], :min_shape[1]]

                built_2000_mask = b00 > 0
                built_2025_mask = b25 > 0
                forest_loss     = (hns > 0) & (hns != HANSEN_NODATA)

                expansion  = built_2025_mask & ~built_2000_mask
                overlap    = expansion & forest_loss

                expansion_ha = float(np.sum(expansion)) * PIXEL_HA
                overlap_ha   = float(np.sum(overlap))   * PIXEL_HA
                loss_ha      = float(np.sum(forest_loss)) * PIXEL_HA

            pct = round(overlap_ha / expansion_ha * 100, 2) if expansion_ha > 0 else 0.0

            records.append({
                "uc_id":                  row.get("uc_id"),
                "uc_nm":                  row.get("uc_nm"),
                "buffer_km":              buf_km,
                "forest_loss_ha":         round(loss_ha, 2),
                "expansion_ha":           round(expansion_ha, 2),
                "overlap_ha":             round(overlap_ha, 2),
                "pct_urban_on_deforested": pct,
            })

        print(f"  ✓ {row.get('uc_nm', row.name)}")

    return pd.DataFrame(records)


def main():
    print("[Módulo 3 — Deforestación]")
    df = compute_m3()
    out = Path(__file__).parent / "m3_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados: {out}  ({len(df)} filas)")


if __name__ == "__main__":
    main()
