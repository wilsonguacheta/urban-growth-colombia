"""
Paso 0 - Script 01: Auditoría de CRS de todos los rasters y vectores extraídos.
Genera data/logs/crs_audit.csv con metadatos de cada archivo.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

import rasterio
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import EXTRACTED_DIR, SOURCES, LOGS_DIR


def audit_raster(path: Path) -> dict:
    try:
        with rasterio.open(path) as src:
            epsg = src.crs.to_epsg() if src.crs else None
            return {
                "path":     str(path),
                "file_type": "raster",
                "epsg":     epsg,
                "crs_wkt":  src.crs.wkt[:120] if src.crs else "UNDEFINED",
                "res_x":    round(src.res[0], 6),
                "res_y":    round(src.res[1], 6),
                "width":    src.width,
                "height":   src.height,
                "xmin":     round(src.bounds.left, 4),
                "ymin":     round(src.bounds.bottom, 4),
                "xmax":     round(src.bounds.right, 4),
                "ymax":     round(src.bounds.top, 4),
                "nodata":   src.nodata,
                "dtype":    src.dtypes[0],
                "n_bands":  src.count,
                "n_features": None,
                "flag_no_crs": epsg is None,
                "status":   "OK",
                "error":    "",
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        return _error_record(path, "raster", str(e))


def audit_vector(path: Path) -> dict:
    try:
        gdf = gpd.read_file(path, rows=1)
        epsg = gdf.crs.to_epsg() if gdf.crs else None
        bounds = gdf.total_bounds  # xmin, ymin, xmax, ymax
        gdf_full = gpd.read_file(path)
        return {
            "path":       str(path),
            "file_type":  "vector",
            "epsg":       epsg,
            "crs_wkt":    gdf.crs.to_wkt()[:120] if gdf.crs else "UNDEFINED",
            "res_x":      None,
            "res_y":      None,
            "width":      None,
            "height":     None,
            "xmin":       round(float(bounds[0]), 4),
            "ymin":       round(float(bounds[1]), 4),
            "xmax":       round(float(bounds[2]), 4),
            "ymax":       round(float(bounds[3]), 4),
            "nodata":     None,
            "dtype":      str(gdf_full.geom_type.unique().tolist()),
            "n_bands":    None,
            "n_features": len(gdf_full),
            "flag_no_crs": epsg is None,
            "status":     "OK",
            "error":      "",
            "timestamp":  datetime.now().isoformat(),
        }
    except Exception as e:
        return _error_record(path, "vector", str(e))


def _error_record(path: Path, file_type: str, error: str) -> dict:
    return {
        "path": str(path), "file_type": file_type, "epsg": None,
        "crs_wkt": "", "res_x": None, "res_y": None, "width": None, "height": None,
        "xmin": None, "ymin": None, "xmax": None, "ymax": None,
        "nodata": None, "dtype": None, "n_bands": None, "n_features": None,
        "flag_no_crs": True, "status": "ERROR", "error": error,
        "timestamp": datetime.now().isoformat(),
    }


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    # Rasters extraídos (GHSL tiles)
    print("[Rasters extraídos GHSL]")
    for tif in sorted(EXTRACTED_DIR.rglob("*.tif")):
        rec = audit_raster(tif)
        records.append(rec)
        flag = " ⚠ SIN CRS" if rec["flag_no_crs"] else ""
        print(f"  {rec['status']} | EPSG:{rec['epsg']} | {tif.name}{flag}")

    # Rasters no comprimidos (DEM, AMENAZA-MM, Hansen)
    native_rasters = [
        SOURCES["dem"],
        SOURCES["amenaza_mm"],
        *sorted(SOURCES["hansen"].glob("*.tif")),
    ]
    print("\n[Rasters nativos]")
    for path in native_rasters:
        if path.exists():
            rec = audit_raster(path)
            records.append(rec)
            flag = " ⚠ SIN CRS" if rec["flag_no_crs"] else ""
            print(f"  {rec['status']} | EPSG:{rec['epsg']} | res={rec['res_x']}° | {path.name}{flag}")

    # Vectores extraídos y nativos
    vector_paths = [
        *sorted(EXTRACTED_DIR.rglob("*.shp")),
        *sorted(SOURCES["amenaza_flood"].glob("*.shp")),
        SOURCES["limite"],
    ]
    print("\n[Vectores]")
    for path in vector_paths:
        if path.exists():
            rec = audit_vector(path)
            records.append(rec)
            flag = " ⚠ SIN CRS" if rec["flag_no_crs"] else ""
            print(f"  {rec['status']} | EPSG:{rec['epsg']} | {rec['n_features']} feat | {path.name}{flag}")

    # Escribir CSV
    log_path = LOGS_DIR / "crs_audit.csv"
    fieldnames = [
        "path", "file_type", "epsg", "crs_wkt", "res_x", "res_y",
        "width", "height", "xmin", "ymin", "xmax", "ymax",
        "nodata", "dtype", "n_bands", "n_features",
        "flag_no_crs", "status", "error", "timestamp",
    ]
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    no_crs = sum(1 for r in records if r["flag_no_crs"])
    errors = sum(1 for r in records if r["status"] == "ERROR")
    print(f"\n── Auditoría completa: {len(records)} archivos | {no_crs} sin CRS | {errors} errores")
    print(f"   Log: {log_path}")
    return errors == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
