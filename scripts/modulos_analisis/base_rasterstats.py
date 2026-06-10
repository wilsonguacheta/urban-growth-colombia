"""
Función base reutilizable para extracción de estadísticas zonales con rasterstats.
Todos los rasters y vectores están en EPSG:9377 @ 100m post-estandarización.
"""
import sys
from pathlib import Path
from typing import Sequence

import geopandas as gpd
import pandas as pd
import rasterio
from rasterstats import zonal_stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import CLIPPED_DIR, VECTORS_DIR, SLOPE_DIR


def extract_zonal_stats(
    vector_path: Path,
    raster_path: Path,
    stats: Sequence[str],
    nodata=None,
    prefix: str = "",
    categorical: bool = False,
    all_touched: bool = False,
) -> pd.DataFrame:
    """
    Extrae estadísticas zonales de un raster sobre un vector.

    Args:
        vector_path:  GeoPackage o shapefile de zonas (EPSG:9377).
        raster_path:  GeoTIFF (EPSG:9377, 100m).
        stats:        Lista de estadísticas: ['sum','mean','count','std','min','max'].
        nodata:       Valor nodata del raster (None → usa el del archivo).
        prefix:       Prefijo de columnas en el resultado.
        categorical:  True para datos clasificados (retorna conteo por clase).
        all_touched:  True incluye píxeles que tocan el borde del polígono.

    Returns:
        DataFrame con columnas del vector (sin geometría) + columnas de estadísticas.
    """
    gdf = gpd.read_file(vector_path)
    with rasterio.open(raster_path) as src:
        if nodata is None:
            nodata = src.nodata

    results = zonal_stats(
        vectors=gdf,
        raster=str(raster_path),
        stats=stats if not categorical else None,
        categorical=categorical,
        nodata=nodata,
        prefix=prefix,
        all_touched=all_touched,
        geojson_out=False,
    )

    stats_df = pd.DataFrame(results)
    base_df  = gdf.drop(columns=["geometry"])
    return pd.concat([base_df.reset_index(drop=True), stats_df], axis=1)


def get_raster_path(product: str, year: int | None = None) -> Path:
    """Devuelve la ruta al raster procesado para un producto y año dados."""
    if product == "slope":
        return SLOPE_DIR / "slope_col.tif"
    if product in ("dem", "hansen", "amenaza_mm"):
        return CLIPPED_DIR / f"{product}_col.tif"
    if year is None:
        raise ValueError(f"Se requiere año para el producto '{product}'")
    return CLIPPED_DIR / f"{product}_{year}_col.tif"


def ucdb_path() -> Path:
    return VECTORS_DIR / "ucdb_colombia.gpkg"


def runap_path() -> Path:
    return VECTORS_DIR / "runap.gpkg"
