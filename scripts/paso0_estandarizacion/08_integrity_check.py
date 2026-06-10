"""
Paso 0 - Script 08: Verificación de integridad post-estandarización.
Comprueba CRS, resolución, extensión, rangos de valores y completitud.
Genera data/logs/integrity_report.csv.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import rasterio
import geopandas as gpd
from pyproj import CRS as ProjCRS

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    MOSAICS_DIR, CLIPPED_DIR, VECTORS_DIR, LOGS_DIR, SLOPE_DIR,
    GHSL_YEARS, TARGET_CRS, TARGET_RES, HANSEN_VALID_MAX,
    COLOMBIA_BBOX_9377,
)

TARGET_EPSG = ProjCRS.from_string(TARGET_CRS).to_epsg()
TARGET_CRS_OBJ = ProjCRS.from_string(TARGET_CRS)
RES_TOLERANCE = 1.0  # metros

# EPSG:9377 en WKT1 (GeoTIFF default) se almacena como LOCAL_CS por GDAL —
# no tiene representación WKT1 canónica con código AUTHORITY. Los datos SÍ
# están en EPSG:9377; verificar por nombre de CRS como fallback.
_CRS9377_WKT_NAMES = ("MAGNA-SIRGAS 2018 / Origen-Nacional",
                      "MAGNA-SIRGAS 2018 / Colombia Origen Nacional")


def check(name: str, ok: bool, detail: str = "") -> dict:
    status = "OK" if ok else "FAIL"
    icon = "✓" if ok else "✗"
    print(f"  {icon} [{status}] {name}" + (f": {detail}" if detail else ""))
    return {
        "check_name": name, "status": status,
        "detail": detail, "timestamp": datetime.now().isoformat(),
    }


def raster_crs_matches_target(path: Path) -> bool:
    """Verifica que el CRS es EPSG:9377 (o su equivalente LOCAL_CS WKT1 que GDAL escribe)."""
    with rasterio.open(path) as src:
        if not src.crs:
            return False
        if src.crs.to_epsg() == TARGET_EPSG:
            return True
        try:
            if ProjCRS.from_user_input(src.crs).equals(TARGET_CRS_OBJ):
                return True
        except Exception:
            pass
        # GDAL WKT1 fallback: EPSG:9377 se serializa como LOCAL_CS sin código AUTHORITY
        wkt = src.crs.to_wkt()
        return any(name in wkt for name in _CRS9377_WKT_NAMES)


def raster_res(path: Path) -> tuple[float, float]:
    with rasterio.open(path) as src:
        return abs(src.transform.a), abs(src.transform.e)


def raster_bounds(path: Path):
    with rasterio.open(path) as src:
        return src.bounds


def raster_value_range(path: Path) -> tuple[float, float]:
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        return float(data.min()), float(data.max())


def vector_epsg(path: Path) -> int | None:
    gdf = gpd.read_file(path, rows=1)
    return gdf.crs.to_epsg() if gdf.crs else None


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    # ── 1. Mosaicos GHSL ─────────────────────────────────────────────────────
    print("\n[1] Mosaicos GHSL")
    expected_mosaics = (
        [f"built_s_{y}_mosaic_54009.tif" for y in GHSL_YEARS["built_s"] if y != 2018] +
        ["built_s_2018_mosaic_54009_100m.tif"] +
        [f"pop_{y}_mosaic_54009.tif"     for y in GHSL_YEARS["pop"]] +
        [f"smod_{y}_mosaic_54009.tif"    for y in GHSL_YEARS["smod"]]
    )
    missing = [m for m in expected_mosaics if not (MOSAICS_DIR / m).exists()]
    records.append(check(
        "mosaicos_ghsl_presentes",
        len(missing) == 0,
        f"{len(expected_mosaics) - len(missing)}/{len(expected_mosaics)} presentes"
        + (f" | Faltantes: {missing[:3]}" if missing else ""),
    ))

    # ── 2. Mosaico Hansen ─────────────────────────────────────────────────────
    print("\n[2] Mosaico Hansen")
    hansen_path = MOSAICS_DIR / "hansen_lossyear_mosaic_4326.tif"
    records.append(check("mosaico_hansen_presente", hansen_path.exists(), str(hansen_path)))

    # ── 3. CRS de rasters en clipped/ ────────────────────────────────────────
    print("\n[3] CRS rasters clipped/")
    clipped_tifs = list(CLIPPED_DIR.glob("*.tif"))
    wrong_crs = []
    for tif in clipped_tifs:
        if not raster_crs_matches_target(tif):
            wrong_crs.append(tif.name)
    records.append(check(
        "crs_rasters_clipped",
        len(wrong_crs) == 0,
        f"{len(clipped_tifs)} rasters revisados" +
        (f" | CRS incorrecto: {wrong_crs}" if wrong_crs else " | Todos en EPSG:9377 (verificado por WKT)"),
    ))

    # ── 4. Resolución 100m en clipped/ ────────────────────────────────────────
    print("\n[4] Resolución 100m en clipped/")
    wrong_res = []
    for tif in clipped_tifs:
        rx, ry = raster_res(tif)
        if abs(rx - TARGET_RES) > RES_TOLERANCE or abs(ry - TARGET_RES) > RES_TOLERANCE:
            wrong_res.append(f"{tif.name} ({rx:.1f}m × {ry:.1f}m)")
    records.append(check(
        "resolucion_100m_clipped",
        len(wrong_res) == 0,
        f"{len(clipped_tifs)} rasters revisados" +
        (f" | Resolución incorrecta: {wrong_res}" if wrong_res else " | Todos a 100m"),
    ))

    # ── 5. Bounds dentro de Colombia ─────────────────────────────────────────
    print("\n[5] Bounds solapan Colombia")
    COL_BOUNDS = COLOMBIA_BBOX_9377  # (xmin, ymin, xmax, ymax) en EPSG:9377
    out_of_bounds = []
    for tif in clipped_tifs:
        b = raster_bounds(tif)
        if (b.right < COL_BOUNDS[0] or b.left > COL_BOUNDS[2] or
                b.top < COL_BOUNDS[1] or b.bottom > COL_BOUNDS[3]):
            out_of_bounds.append(tif.name)
    records.append(check(
        "bounds_dentro_colombia",
        len(out_of_bounds) == 0,
        f"{len(clipped_tifs)} revisados" +
        (f" | Fuera de Colombia: {out_of_bounds}" if out_of_bounds else ""),
    ))

    # ── 6. BUILT-S 2018 a 100m ────────────────────────────────────────────────
    print("\n[6] BUILT-S 2018 normalizado a 100m")
    built_2018_100 = MOSAICS_DIR / "built_s_2018_mosaic_54009_100m.tif"
    if built_2018_100.exists():
        rx, ry = raster_res(built_2018_100)
        # EPSG:54009 Mollweide usa metros → resolución esperada ≈100m
        ok = abs(rx - TARGET_RES) < RES_TOLERANCE and abs(ry - TARGET_RES) < RES_TOLERANCE
        records.append(check("built_s_2018_100m", ok,
                             f"res: {rx:.2f} × {ry:.2f} m (esperado {TARGET_RES}m ±{RES_TOLERANCE}m)"))
    else:
        records.append(check("built_s_2018_100m", False, "archivo no encontrado"))

    # ── 7. Valores Hansen en rango 0–25 ───────────────────────────────────────
    print("\n[7] Valores Hansen")
    hansen_clipped = CLIPPED_DIR / "hansen_col.tif"
    if hansen_clipped.exists():
        vmin, vmax = raster_value_range(hansen_clipped)
        records.append(check(
            "hansen_valores_rango",
            vmin >= 0 and vmax <= HANSEN_VALID_MAX,
            f"min={vmin:.0f}, max={vmax:.0f} (esperado 0–{HANSEN_VALID_MAX})",
        ))
    else:
        records.append(check("hansen_valores_rango", False, "hansen_col.tif no encontrado"))

    # ── 8. CRS vectores ───────────────────────────────────────────────────────
    print("\n[8] CRS vectores en EPSG:9377")
    vector_files = list(VECTORS_DIR.glob("*.gpkg"))
    wrong_vec_crs = []
    for gpkg in vector_files:
        epsg = vector_epsg(gpkg)
        if epsg != TARGET_EPSG:
            wrong_vec_crs.append(f"{gpkg.name} (EPSG:{epsg})")
    records.append(check(
        "crs_vectores_9377",
        len(wrong_vec_crs) == 0,
        f"{len(vector_files)} GPKGs revisados" +
        (f" | CRS incorrecto: {wrong_vec_crs}" if wrong_vec_crs else " | Todos en EPSG:9377"),
    ))

    # ── 9. RUNAP completitud ──────────────────────────────────────────────────
    print("\n[9] RUNAP completitud")
    runap_path = VECTORS_DIR / "runap.gpkg"
    if runap_path.exists():
        gdf = gpd.read_file(runap_path)
        records.append(check("runap_features", len(gdf) > 100,
                             f"{len(gdf)} áreas protegidas (mínimo esperado: 100)"))
    else:
        records.append(check("runap_features", False, "runap.gpkg no encontrado"))

    # ── 10. UCDB dentro de Colombia ───────────────────────────────────────────
    print("\n[10] UCDB dentro de Colombia")
    ucdb_path   = VECTORS_DIR / "ucdb_colombia.gpkg"
    limite_path = VECTORS_DIR / "limite_colombia_9377.gpkg"
    if ucdb_path.exists() and limite_path.exists():
        gdf_ucdb   = gpd.read_file(ucdb_path)
        gdf_limite = gpd.read_file(limite_path)
        col_union  = gdf_limite.geometry.unary_union
        within = gdf_ucdb.geometry.intersects(col_union).sum()
        total  = len(gdf_ucdb)
        records.append(check(
            "ucdb_dentro_colombia",
            within == total,
            f"{within}/{total} centros urbanos dentro del límite Colombia",
        ))
    else:
        records.append(check("ucdb_dentro_colombia", False,
                             "ucdb_colombia.gpkg o limite_colombia_9377.gpkg no encontrados"))

    # ── Escribir reporte ──────────────────────────────────────────────────────
    log_path = LOGS_DIR / "integrity_report.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check_name", "status", "detail", "timestamp"])
        writer.writeheader()
        writer.writerows(records)

    ok_count   = sum(1 for r in records if r["status"] == "OK")
    fail_count = sum(1 for r in records if r["status"] == "FAIL")
    print(f"\n── Integridad: {ok_count} OK | {fail_count} FAIL")
    print(f"   Reporte: {log_path}")

    if fail_count > 0:
        print("\n  ⚠ Revisa los FAIL antes de continuar con el Paso 1.")
    return fail_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
