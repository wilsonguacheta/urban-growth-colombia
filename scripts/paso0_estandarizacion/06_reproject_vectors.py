"""
Paso 0 - Script 06: Reproyecta todos los vectores a EPSG:9377 y los guarda como GeoPackage.

Orden de ejecución importante:
  1. LIMITE_COLOMBIA → vectors/limite_colombia_9377.gpkg  (requerido por 05_clip_to_colombia.py)
  2. AMENAZA-FLOOD   → vectors/amenaza_flood.gpkg
  3. GHS-UCDB        → vectors/ucdb_colombia.gpkg  (filtrado + recortado a Colombia)
  4. RUNAP           → vectors/runap.gpkg
"""
import sys
from pathlib import Path

import geopandas as gpd
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    SOURCES, EXTRACTED_DIR, VECTORS_DIR, TARGET_CRS
)


def to_gpkg(gdf: gpd.GeoDataFrame, out_path: Path, label: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    epsg = gdf.crs.to_epsg()
    print(f"  ✓ {out_path.name}  ({len(gdf)} features, EPSG:{epsg})")


def reproject(gdf: gpd.GeoDataFrame, fallback_epsg: int | None = None) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        if fallback_epsg is None:
            raise ValueError("Vector sin CRS y sin fallback definido.")
        print(f"    ⚠ Sin CRS — asignando EPSG:{fallback_epsg}")
        gdf = gdf.set_crs(epsg=fallback_epsg)
    return gdf.to_crs(TARGET_CRS)


# Normaliza nombres de columnas UCDB (versión 2025) y RUNAP al esquema esperado
# por los módulos de análisis y la base de datos PostGIS.
_UCDB_RENAME = {
    "ID_UC_G0":        "uc_id",
    "GC_UCN_MAI_2025": "uc_nm",
    "GC_CNT_GAD_2025": "ctr_mn_nm",
    "GC_UCA_KM2_2025": "area_km2",
    "GC_POP_TOT_2025": "pop_2025",
}
_RUNAP_RENAME = {
    "ap_id":      "gid",
    "ap_nombre":  "nombre",
    "ap_categor": "categoria",
    "area_ha_to": "area_ha",
}


def main():
    VECTORS_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Límite Colombia ────────────────────────────────────────────────────
    print("[LIMITE_COLOMBIA]")
    gdf_limite = gpd.read_file(SOURCES["limite"])
    gdf_limite = reproject(gdf_limite, fallback_epsg=4686)
    to_gpkg(gdf_limite, VECTORS_DIR / "limite_colombia_9377.gpkg", "LIMITE")

    # Geometría unificada usada para clips/filtros
    colombia_union = unary_union(gdf_limite.geometry)

    # ── 2. AMENAZA-FLOOD ──────────────────────────────────────────────────────
    print("\n[AMENAZA-FLOOD]")
    shp_files = list(SOURCES["amenaza_flood"].glob("*.shp"))
    if shp_files:
        gdf_flood = gpd.read_file(shp_files[0])
        gdf_flood = reproject(gdf_flood, fallback_epsg=4686)
        to_gpkg(gdf_flood, VECTORS_DIR / "amenaza_flood.gpkg", "FLOOD")
    else:
        print("  ! No se encontró shapefile en AMENAZA-FLOOD/")

    # ── 3. GHS-UCDB ───────────────────────────────────────────────────────────
    print("\n[GHS-UCDB]")
    ucdb_dir = EXTRACTED_DIR / "ucdb"
    ucdb_files = list(ucdb_dir.rglob("*.shp")) + list(ucdb_dir.rglob("*.gpkg"))
    if ucdb_files:
        gdf_ucdb = gpd.read_file(ucdb_files[0])
        gdf_ucdb = reproject(gdf_ucdb)

        # Filtrar por nombre de país si la columna existe
        col_country = next(
            (c for c in gdf_ucdb.columns if c.upper() in ("CTR_MN_NM", "COUNTRY", "PAIS")),
            None,
        )
        if col_country:
            gdf_ucdb = gdf_ucdb[gdf_ucdb[col_country].str.upper() == "COLOMBIA"].copy()
            print(f"    Filtrado por {col_country}='Colombia': {len(gdf_ucdb)} ciudades")
        else:
            # Fallback: filtro espacial dentro del límite
            gdf_ucdb = gdf_ucdb[gdf_ucdb.geometry.intersects(colombia_union)].copy()
            print(f"    Filtrado espacial (intersects Colombia): {len(gdf_ucdb)} ciudades")

        gdf_ucdb = gdf_ucdb.reset_index(drop=True)
        gdf_ucdb = gdf_ucdb.rename(columns={k: v for k, v in _UCDB_RENAME.items()
                                             if k in gdf_ucdb.columns})
        to_gpkg(gdf_ucdb, VECTORS_DIR / "ucdb_colombia.gpkg", "UCDB")
    else:
        print("  ! No se encontró shapefile/GPKG UCDB en extracted/ucdb/")

    # ── 4. RUNAP ──────────────────────────────────────────────────────────────
    print("\n[RUNAP]")
    runap_shps = list((EXTRACTED_DIR / "runap").rglob("*.shp"))
    if runap_shps:
        gdf_runap = gpd.read_file(runap_shps[0])
        # RUNAP suele venir en EPSG:4686 (MAGNA-SIRGAS geográfico)
        gdf_runap = reproject(gdf_runap, fallback_epsg=4686)
        gdf_runap = gdf_runap.rename(columns={k: v for k, v in _RUNAP_RENAME.items()
                                               if k in gdf_runap.columns})
        to_gpkg(gdf_runap, VECTORS_DIR / "runap.gpkg", "RUNAP")
    else:
        print("  ! No se encontró shapefile RUNAP en extracted/runap/")

    print("\n── Vectores reproyectados a EPSG:9377 y guardados como GPKG")


if __name__ == "__main__":
    main()
