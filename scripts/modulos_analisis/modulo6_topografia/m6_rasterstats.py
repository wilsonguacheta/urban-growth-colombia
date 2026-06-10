"""
Módulo 6: Influencia de la Topografía en el Crecimiento Urbano.
DEM y slope ya están en EPSG:9377 @ 100m, igual que BUILT-S.
→ No se requiere remuestreo on-the-fly; la máscara se aplica directamente.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import CLIPPED_DIR, SLOPE_DIR, VECTORS_DIR, GHSL_YEARS, GHSL_NODATA, DEM_NODATA

YEARS = [y for y in GHSL_YEARS["built_s"] if y != 2018]
STEEP_THRESHOLD_DEG = 15.0


def _clip_arr(raster_path: Path, geom, nodata) -> np.ndarray:
    """Retorna array float32 con nodata→NaN. Array vacío si la geometría no solapa el raster."""
    try:
        with rasterio.open(raster_path) as src:
            arr, _ = rio_mask(src, [mapping(geom)], crop=True, filled=True, nodata=nodata)
        out = arr[0].astype(np.float32)
        out[out == nodata] = np.nan
        return out
    except (ValueError, rasterio.errors.WindowError):
        return np.array([[]], dtype=np.float32)


def compute_m6() -> pd.DataFrame:
    dem_path   = CLIPPED_DIR / "dem_col.tif"
    slope_path = SLOPE_DIR   / "slope_col.tif"

    for p in [dem_path, slope_path]:
        if not p.exists():
            raise FileNotFoundError(f"No encontrado: {p}")

    gdf_ucdb = gpd.read_file(VECTORS_DIR / "ucdb_colombia.gpkg")
    records = []

    for _, row in gdf_ucdb.iterrows():
        geom = row.geometry
        dem   = _clip_arr(dem_path,   geom, DEM_NODATA)
        slope = _clip_arr(slope_path, geom, DEM_NODATA)

        # Cargar BUILT-S por año
        built_prev = None
        for year in YEARS:
            built_path = CLIPPED_DIR / f"built_s_{year}_col.tif"
            if not built_path.exists():
                continue
            built = _clip_arr(built_path, geom, GHSL_NODATA["built_s"])
            min_r = min(dem.shape[0], built.shape[0])
            min_c = min(dem.shape[1], built.shape[1])
            if dem.shape != built.shape:
                uc_nm = row.get("uc_nm", row.name)
                print(f"  ⚠ shape mismatch {uc_nm} {year}: "
                      f"DEM{dem.shape} vs BUILT{built.shape} — truncando a ({min_r},{min_c})")
            built_m  = (built[:min_r, :min_c] > 0)
            dem_m    = dem[:min_r, :min_c]
            slope_m  = slope[:min_r, :min_c]

            built_mask = built_m & ~np.isnan(dem_m)

            mean_elev  = float(np.nanmean(dem_m[built_mask]))   if built_mask.any() else np.nan
            mean_slope = float(np.nanmean(slope_m[built_mask])) if built_mask.any() else np.nan
            pct_steep  = (
                float(np.sum(slope_m[built_mask] > STEEP_THRESHOLD_DEG)) /
                float(np.sum(built_mask)) * 100
            ) if built_mask.any() else 0.0

            # Expansión respecto al período anterior
            elev_new = slope_new = np.nan
            if built_prev is not None:
                exp_mask = built_m & ~built_prev[:min_r, :min_c] & ~np.isnan(dem_m)
                if exp_mask.any():
                    elev_new  = float(np.nanmean(dem_m[exp_mask]))
                    slope_new = float(np.nanmean(slope_m[exp_mask]))

            records.append({
                "uc_id":                row.get("uc_id"),
                "uc_nm":                row.get("uc_nm"),
                "year":                 year,
                "mean_elevation_m":     round(mean_elev, 1)  if not np.isnan(mean_elev)  else None,
                "mean_slope_deg":       round(mean_slope, 2) if not np.isnan(mean_slope) else None,
                "pct_area_steep":       round(pct_steep, 2),
                "elevation_new_growth": round(elev_new, 1)   if not np.isnan(elev_new)   else None,
                "slope_new_growth":     round(slope_new, 2)  if not np.isnan(slope_new)  else None,
            })

            built_prev = built_m

        print(f"  ✓ {row.get('uc_nm', row.name)}")

    return pd.DataFrame(records)


def main():
    print("[Módulo 6 — Topografía]")
    df = compute_m6()
    out = Path(__file__).parent / "m6_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados: {out}  ({len(df)} filas)")


if __name__ == "__main__":
    main()
