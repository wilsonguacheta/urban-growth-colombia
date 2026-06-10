"""
Módulo 6 — Indicadores: carga resultados en PostGIS e imprime resumen topográfico.
Requiere: m6_results.parquet (generado por m6_rasterstats.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis

RESULTS = Path(__file__).parent / "m6_results.parquet"


def main():
    if not RESULTS.exists():
        print(f"✗ No encontrado: {RESULTS}\n  Ejecuta m6_rasterstats.py primero.")
        sys.exit(1)

    df = pd.read_parquet(RESULTS)

    cols = ["uc_id", "uc_nm", "year", "mean_elevation_m", "mean_slope_deg",
            "pct_area_steep", "elevation_new_growth", "slope_new_growth"]
    df_load = df[[c for c in cols if c in df.columns]].copy()

    print("[M6] Cargando en analysis.m6_topography")
    load_to_postgis(df_load, "m6_topography", if_exists="replace")

    # ── Resumen ────────────────────────────────────────────────────────────────
    last_year = df["year"].max()
    df_last   = df[df["year"] == last_year].dropna(subset=["mean_slope_deg"])

    print(f"\n── Resumen Módulo 6: Topografía del Crecimiento Urbano ({last_year}) ──")
    print("\nCiudades con mayor pendiente promedio en área construida:")
    print(df_last.nlargest(10, "mean_slope_deg")
          [["uc_nm", "mean_elevation_m", "mean_slope_deg", "pct_area_steep"]]
          .to_string(index=False))

    print("\nCiudades que crecen hacia zonas más empinadas (slope_new_growth más alto):")
    df_growth = df[df["year"] == last_year].dropna(subset=["slope_new_growth"])
    print(df_growth.nlargest(10, "slope_new_growth")
          [["uc_nm", "slope_new_growth", "elevation_new_growth"]]
          .to_string(index=False))

    # Comparación pendiente histórica vs expansión reciente
    df_trend = df[df["year"].isin([2000, last_year])].pivot_table(
        index="uc_nm", columns="year", values="mean_slope_deg"
    ).dropna()
    df_trend["delta_slope"] = df_trend[last_year] - df_trend[2000]
    print(f"\nCiudades con mayor aumento de pendiente media (2000 → {last_year}):")
    print(df_trend.nlargest(10, "delta_slope")[["delta_slope"]].round(2).to_string())


if __name__ == "__main__":
    main()
