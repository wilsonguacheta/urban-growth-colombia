"""
Módulo 5 — Indicadores: carga resultados en PostGIS e imprime resumen de presión sobre RUNAP.
Requiere: m5_results.parquet (generado por m5_rasterstats.py)
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis, get_engine

RESULTS = Path(__file__).parent / "m5_results.parquet"
SQL_M5  = Path(__file__).resolve().parents[3] / "sql" / "analysis" / "m5_runap.sql"


def load_dist_from_postgis(engine) -> pd.DataFrame:
    """Ejecuta la consulta de distancia ciudad→AP y retorna DataFrame."""
    query = """
        SELECT u.uc_id, u.uc_nm, r.gid AS runap_gid, r.nombre AS runap_nombre,
               ROUND(ST_Distance(u.geom, r.geom)::numeric, 1) AS dist_m
        FROM raw.ucdb_colombia u
        CROSS JOIN LATERAL (
            SELECT gid, nombre, geom FROM raw.runap ORDER BY u.geom <-> geom LIMIT 1
        ) r
    """
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def main():
    if not RESULTS.exists():
        print(f"✗ No encontrado: {RESULTS}\n  Ejecuta m5_rasterstats.py primero.")
        sys.exit(1)

    engine = get_engine()
    df     = pd.read_parquet(RESULTS)

    # Cargar built_inside por AP y año
    cols = ["gid", "nombre", "categoria", "area_ha", "year",
            "built_inside_m2", "built_inside_ha"]
    df_load = df[[c for c in cols if c in df.columns]].rename(
        columns={"gid": "runap_gid", "nombre": "runap_nombre"}
    )
    print("[M5] Cargando en analysis.m5_protected_areas")
    load_to_postgis(df_load, "m5_protected_areas", if_exists="replace")

    # Obtener y persistir distancias ciudad→AP
    print("[M5] Calculando distancias ciudad→AP")
    df_dist = load_dist_from_postgis(engine)
    print(f"  ✓ {len(df_dist)} pares ciudad-AP calculados")
    load_to_postgis(df_dist, "m5_city_ap_distances", if_exists="replace")

    # ── Resumen ────────────────────────────────────────────────────────────────
    print("\n── Resumen Módulo 5: Presión sobre Áreas Protegidas ──")

    # APs con mayor área construida dentro (2025)
    last_year = df["year"].max()
    df_inside = df[df["year"] == last_year].nlargest(10, "built_inside_ha")
    print(f"\nTop 10 APs con mayor superficie construida dentro ({last_year}):")
    print(df_inside[["nombre", "categoria", "area_ha", "built_inside_ha"]]
          .assign(pct=lambda x: (x["built_inside_ha"] / x["area_ha"] * 100).round(2))
          .to_string(index=False))

    # Ciudades más cercanas a APs
    print("\nCiudades más próximas a un área protegida (Top 10):")
    print(df_dist.assign(dist_km=lambda x: (x["dist_m"] / 1000).round(2))
          .nsmallest(10, "dist_m")[["uc_nm", "runap_nombre", "dist_km"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
