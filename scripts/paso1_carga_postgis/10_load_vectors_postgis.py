"""
Paso 1 - Script 10: Carga de vectores procesados en PostgreSQL/PostGIS.
Lee credenciales desde variables de entorno o archivo .env en la raíz del proyecto.

Orden de ejecución:
  1. DDL fase 1: esquemas + tablas (01, 02, 03)
  2. Carga de vectores  — to_postgis usa CASCADE drop + columna 'geom'
  3. DDL fase 2: índices + vistas (04, 05) — dependen de tablas con datos reales
  4. REFRESH de vistas materializadas
"""
import sys
from pathlib import Path

import geopandas as gpd
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import VECTORS_DIR, TARGET_CRS
from scripts.modulos_analisis.db_utils import get_engine

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "ddl"

# Mapeo de columnas originales → nombres normalizados usados por los módulos de análisis
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


def load_vector(gpkg_path: Path, table: str, schema: str, engine,
                if_exists: str = "replace", col_rename: dict | None = None):
    if not gpkg_path.exists():
        print(f"  ! No encontrado: {gpkg_path.name} — omitido")
        return
    gdf = gpd.read_file(gpkg_path)
    epsg = gdf.crs.to_epsg() if gdf.crs else None
    if epsg != 9377:
        print(f"  ⚠ {gpkg_path.name} está en EPSG:{epsg}, se esperaba 9377")

    # Renombrar columnas de origen a nombres normalizados
    if col_rename:
        gdf = gdf.rename(columns={k: v for k, v in col_rename.items() if k in gdf.columns})

    # Renombrar geometría a 'geom' para que coincida con el DDL y las vistas
    if gdf.geometry.name != "geom":
        gdf = gdf.rename_geometry("geom")

    if if_exists == "replace":
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table}" CASCADE'))
            conn.commit()
        if_exists = "fail"

    gdf.to_postgis(
        table, engine, schema=schema,
        if_exists=if_exists, index=False,
    )
    print(f"  ✓ {schema}.{table}  ({len(gdf)} features, EPSG:{epsg})")


def run_sql_file(sql_path: Path, engine):
    sql = sql_path.read_text(encoding="utf-8")
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"  ✓ SQL ejecutado: {sql_path.name}")


def main():
    engine = get_engine()

    # Fase 1: esquemas, tablas y catálogo (sin índices ni vistas aún)
    print("\n[DDL fase 1: esquemas + tablas]")
    for name in ["01_schemas.sql", "02_tables_vectors.sql", "03_tables_catalog_analysis.sql"]:
        run_sql_file(SQL_DIR / name, engine)

    # Carga de vectores — recrea tablas con columna 'geom' correcta
    print("\n[VECTORES]")
    load_vector(VECTORS_DIR / "limite_colombia_9377.gpkg", "limite_colombia", "raw", engine)
    load_vector(VECTORS_DIR / "ucdb_colombia.gpkg",        "ucdb_colombia",   "raw", engine,
                col_rename=_UCDB_RENAME)
    load_vector(VECTORS_DIR / "runap.gpkg",                "runap",           "raw", engine,
                col_rename=_RUNAP_RENAME)
    load_vector(VECTORS_DIR / "amenaza_flood.gpkg",        "amenaza_flood",   "raw", engine)

    # Fase 2: índices y vistas — ahora que las tablas tienen el schema correcto
    print("\n[DDL fase 2: índices + vistas]")
    for name in ["04_indexes.sql", "05_views.sql"]:
        run_sql_file(SQL_DIR / name, engine)

    # Refrescar vista materializada de buffers RUNAP
    print("\n[REFRESH]")
    with engine.connect() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW analysis.mv_runap_buffer_5km"))
        conn.commit()
    print("  ✓ mv_runap_buffer_5km refrescada")

    print("\n── Carga vectores completa")


if __name__ == "__main__":
    main()
