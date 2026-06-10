"""
Módulo 1 — Indicadores: carga resultados en PostGIS e imprime resumen.
Requiere: m1_results.parquet (generado por m1_rasterstats.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis

RESULTS = Path(__file__).parent / "m1_results.parquet"


def main():
    if not RESULTS.exists():
        print(f"✗ No encontrado: {RESULTS}\n  Ejecuta m1_rasterstats.py primero.")
        sys.exit(1)

    df = pd.read_parquet(RESULTS)

    # Seleccionar columnas que coinciden con el esquema de la tabla
    cols = ["uc_id", "uc_nm", "year", "built_area_m2", "year_prev", "delta_m2", "growth_rate_pct"]
    df_load = df[[c for c in cols if c in df.columns]].copy()

    print("[M1] Cargando en analysis.m1_urban_growth")
    load_to_postgis(df_load, "m1_urban_growth", if_exists="replace")

    # ── Resumen ────────────────────────────────────────────────────────────────
    print("\n── Resumen Módulo 1: Crecimiento Urbano ──")
    pivot = df.pivot_table(
        index="uc_nm", columns="year", values="built_area_m2", aggfunc="sum"
    ) / 1e6  # m² → km²

    print(pivot.round(2).to_string())

    top5 = (
        df[df["year"] == df["year"].max()]
        .nlargest(5, "built_area_m2")[["uc_nm", "built_area_m2"]]
        .assign(built_km2=lambda x: (x["built_area_m2"] / 1e6).round(2))
        .drop(columns=["built_area_m2"])
    )
    print(f"\nTop 5 ciudades por área construida ({df['year'].max()}):")
    print(top5.to_string(index=False))


if __name__ == "__main__":
    main()
