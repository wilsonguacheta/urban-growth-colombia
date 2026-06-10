"""
Paso 1 - Script 11: Construye el catálogo de rasters en catalog.raster_catalog.
Los rasters NO se cargan en PostGIS — solo se registran sus metadatos y rutas absolutas.
"""
import re
import sys
from pathlib import Path
from datetime import datetime

import rasterio
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import CLIPPED_DIR, SLOPE_DIR, GHSL_YEARS
from scripts.modulos_analisis.db_utils import get_engine

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

PRODUCT_PATTERNS = {
    r"built_s_(\d{4})_col\.tif$": "built_s",
    r"pop_(\d{4})_col\.tif$":     "pop",
    r"smod_(\d{4})_col\.tif$":    "smod",
    r"hansen_col\.tif$":          "hansen",
    r"dem_col\.tif$":             "dem",
    r"amenaza_mm_col\.tif$":      "amenaza_mm",
    r"slope_col\.tif$":           "slope",
}


def infer_product_year(filename: str) -> tuple[str, int | None]:
    for pattern, product in PRODUCT_PATTERNS.items():
        m = re.match(pattern, filename)
        if m:
            year = int(m.group(1)) if m.lastindex and m.lastindex >= 1 else None
            return product, year
    return "unknown", None


def build_record(tif_path: Path) -> dict:
    product, year = infer_product_year(tif_path.name)
    with rasterio.open(tif_path) as src:
        return {
            "product":      product,
            "year":         year,
            "resolution_m": round(abs(src.transform.a), 2),
            "crs_epsg":     src.crs.to_epsg() if src.crs else None,
            "file_path":    str(tif_path.resolve()),
            "bbox_xmin":    round(src.bounds.left,   2),
            "ymin":         round(src.bounds.bottom, 2),
            "bbox_xmax":    round(src.bounds.right,  2),
            "ymax":         round(src.bounds.top,    2),
            "width_px":     src.width,
            "height_px":    src.height,
            "nodata_value": src.nodata,
            "dtype":        src.dtypes[0],
            "file_size_mb": round(tif_path.stat().st_size / 1e6, 2),
            "processed_at": datetime.now().isoformat(),
        }


def main():
    records = []

    print("[Rasters clipped/]")
    for tif in sorted(CLIPPED_DIR.glob("*.tif")):
        rec = build_record(tif)
        records.append(rec)
        print(f"  {rec['product']}  {rec['year'] or '----'}  "
              f"{rec['resolution_m']}m  EPSG:{rec['crs_epsg']}  {rec['file_size_mb']:.1f}MB")

    print("\n[Slope]")
    slope_path = SLOPE_DIR / "slope_col.tif"
    if slope_path.exists():
        rec = build_record(slope_path)
        rec["product"] = "slope"
        records.append(rec)
        print(f"  slope  ----  {rec['resolution_m']}m  EPSG:{rec['crs_epsg']}")

    df = pd.DataFrame(records)
    engine = get_engine()
    df.to_sql("raster_catalog", engine, schema="catalog",
              if_exists="replace", index=False)

    print(f"\n── Catálogo: {len(records)} rasters registrados en catalog.raster_catalog")


if __name__ == "__main__":
    main()
