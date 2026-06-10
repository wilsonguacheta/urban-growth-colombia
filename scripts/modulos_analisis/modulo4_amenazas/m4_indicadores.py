"""
Módulo 4 — Indicadores: carga resultados en PostGIS e imprime resumen de exposición.
Combina resultados raster (MM) y ejecuta el SQL de FLOOD contra PostGIS.
Requiere: m4_mm_results.parquet (generado por m4_rasterstats.py)
         m2_results.parquet    (para pop_total por ciudad y año al calcular FLOOD)
"""
import os
import re
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis, get_engine

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

RESULTS_MM = Path(__file__).parent / "m4_mm_results.parquet"
RESULTS_M2 = Path(__file__).resolve().parents[1] / "modulo2_presion_poblacional" / "m2_results.parquet"
SQL_FLOOD  = Path(__file__).resolve().parents[3] / "sql" / "analysis" / "m4_amenazas.sql"

FLOOD_YEAR = 2020  # Año de referencia de la capa amenaza_flood (capa estática)


def run_flood_sql(engine) -> None:
    """Ejecuta el INSERT de FLOOD en la tabla de análisis."""
    sql = SQL_FLOOD.read_text(encoding="utf-8")
    # Extraer el INSERT INTO incluso si hay comentarios previos en el bloque
    insert_stmts = []
    for block in sql.split(";"):
        m = re.search(r"\bINSERT\s+INTO\b", block, re.IGNORECASE)
        if m:
            insert_stmts.append(block[m.start():].strip())
    if not insert_stmts:
        print("  ! No se encontró bloque INSERT en m4_amenazas.sql")
        return
    # Quitar ON CONFLICT si existe (la tabla fue recreada sin unique constraint)
    stmt = re.sub(r"\s*ON CONFLICT.*$", "", insert_stmts[0], flags=re.IGNORECASE | re.DOTALL).strip()
    with engine.connect() as conn:
        conn.execute(text(stmt))
        conn.commit()
    print(f"  ✓ FLOOD cargado en analysis.m4_hazard_exposure (año {FLOOD_YEAR})")


def update_flood_pop_exposed(engine) -> None:
    """
    Completa pop_exposed y pct_pop_exposed para registros FLOOD usando pop_total de M2.
    Supone densidad poblacional uniforme dentro de la ciudad:
      pop_exposed ≈ (pct_built_exposed / 100) × pop_total
    Usa el año más cercano disponible en M2 respecto a FLOOD_YEAR.
    """
    if not RESULTS_M2.exists():
        print(f"  ! m2_results.parquet no encontrado — pop_exposed FLOOD quedará NULL")
        print(f"    Ejecuta el Módulo 2 primero para completar esta métrica.")
        return

    df_pop = pd.read_parquet(RESULTS_M2)[["uc_id", "year", "pop_total"]]
    # Usar el año disponible más cercano a FLOOD_YEAR
    available_years = sorted(df_pop["year"].unique())
    ref_year = min(available_years, key=lambda y: abs(y - FLOOD_YEAR))
    df_ref = df_pop[df_pop["year"] == ref_year][["uc_id", "pop_total"]]

    with engine.connect() as conn:
        df_flood = pd.read_sql(
            "SELECT uc_id, pct_built_exposed "
            "FROM analysis.m4_hazard_exposure WHERE hazard_type = 'flood'",
            conn,
        )
        if df_flood.empty:
            return

        df_flood = df_flood.merge(df_ref, on="uc_id", how="left")
        df_flood["pop_exposed"] = (
            df_flood["pct_built_exposed"].fillna(0) / 100.0 * df_flood["pop_total"].fillna(0)
        ).round(0)
        df_flood["pct_pop_exposed"] = df_flood["pct_built_exposed"]

        for _, row in df_flood.iterrows():
            conn.execute(
                text(
                    "UPDATE analysis.m4_hazard_exposure "
                    "SET pop_exposed = :pe, pct_pop_exposed = :ppe "
                    "WHERE uc_id = :uc_id AND hazard_type = 'flood'"
                ),
                {"pe": row["pop_exposed"], "ppe": row["pct_pop_exposed"], "uc_id": int(row["uc_id"])},
            )
        conn.commit()
    print(f"  ✓ pop_exposed FLOOD actualizado ({len(df_flood)} ciudades, ref año {ref_year})")


def main():
    engine = get_engine()

    # ── Movimientos en masa ────────────────────────────────────────────────────
    if not RESULTS_MM.exists():
        print(f"✗ No encontrado: {RESULTS_MM}\n  Ejecuta m4_rasterstats.py primero.")
        sys.exit(1)

    df_mm = pd.read_parquet(RESULTS_MM)
    cols  = ["uc_id", "uc_nm", "year", "hazard_type", "hazard_class",
             "pop_exposed", "built_exposed_m2", "pct_pop_exposed", "pct_built_exposed"]
    df_load = df_mm[[c for c in cols if c in df_mm.columns]].copy()

    print("[M4] Cargando MM en analysis.m4_hazard_exposure")
    load_to_postgis(df_load, "m4_hazard_exposure", if_exists="replace")

    # ── Inundación (PostGIS) ───────────────────────────────────────────────────
    print("[M4] Ejecutando SQL de FLOOD")
    run_flood_sql(engine)
    update_flood_pop_exposed(engine)

    # ── Exportar FLOOD a parquet ───────────────────────────────────────────────
    print("[M4] Exportando FLOOD a parquet")
    save_flood_parquet(engine)

    # ── Resumen ────────────────────────────────────────────────────────────────
    print("\n── Resumen Módulo 4: Exposición a Amenazas ──")

    last_yr = df_mm["year"].max()
    df_high = df_mm[
        (df_mm["year"] == last_yr) & (df_mm["hazard_class"].isin([3, 4]))
    ].groupby("uc_nm")["pop_exposed"].sum().nlargest(10)

    print(f"\nTop 10 ciudades — Población expuesta a MM alta/muy alta ({last_yr}):")
    print(df_high.round(0).to_string())


def save_flood_parquet(engine) -> None:
    """Exporta registros flood de m4_hazard_exposure → m4_flood_results.parquet."""
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT uc_id, uc_nm, year, built_exposed_m2, pct_built_exposed, "
            "pop_exposed, pct_pop_exposed "
            "FROM analysis.m4_hazard_exposure WHERE hazard_type = 'flood' "
            "ORDER BY pct_built_exposed DESC NULLS LAST",
            conn,
        )
    out = Path(__file__).parent / "m4_flood_results.parquet"
    df.to_parquet(out, index=False)
    print(f"  ✓ {out}  ({len(df)} filas)")


if __name__ == "__main__":
    main()
