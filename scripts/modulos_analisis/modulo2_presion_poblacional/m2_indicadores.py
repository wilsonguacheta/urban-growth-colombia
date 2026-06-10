"""
Módulo 2 — Indicadores: carga resultados en PostGIS e imprime resumen de sprawl.
Requiere: m2_results.parquet (generado por m2_rasterstats.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis

RESULTS = Path(__file__).parent / "m2_results.parquet"


def main():
    if not RESULTS.exists():
        print(f"✗ No encontrado: {RESULTS}\n  Ejecuta m2_rasterstats.py primero.")
        sys.exit(1)

    df = pd.read_parquet(RESULTS)

    cols = ["uc_id", "uc_nm", "year", "pop_total", "built_area_m2",
            "pop_density", "sprawl_index", "densification", "year_prev"]
    df_load = df[[c for c in cols if c in df.columns]].copy()

    print("[M2] Cargando en analysis.m2_population_pressure")
    load_to_postgis(df_load, "m2_population_pressure", if_exists="replace")

    # ── Resumen ────────────────────────────────────────────────────────────────
    last_year = df["year"].max()
    df_last   = df[df["year"] == last_year].dropna(subset=["sprawl_index"])

    def classify(si):
        if si > 1.5:  return "Sprawl severo"
        if si > 1.0:  return "Sprawl moderado"
        if si >= 0.8: return "Equilibrado"
        return "Densificación"

    df_last = df_last.copy()
    df_last["tipo"] = df_last["sprawl_index"].apply(classify)

    print(f"\n── Resumen Módulo 2: Presión Poblacional (año {last_year}) ──")
    print(df_last[["uc_nm", "pop_total", "pop_density", "sprawl_index", "tipo"]]
          .sort_values("sprawl_index", ascending=False)
          .to_string(index=False))

    dist = df_last["tipo"].value_counts()
    print(f"\nDistribución de ciudades por tipo de crecimiento:\n{dist.to_string()}")


if __name__ == "__main__":
    main()
