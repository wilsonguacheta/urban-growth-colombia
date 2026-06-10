"""
Módulo 3 — Indicadores: carga resultados en PostGIS e imprime resumen de deforestación.
Requiere: m3_results.parquet (generado por m3_rasterstats.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.modulos_analisis.db_utils import load_to_postgis

RESULTS = Path(__file__).parent / "m3_results.parquet"


def main():
    if not RESULTS.exists():
        print(f"✗ No encontrado: {RESULTS}\n  Ejecuta m3_rasterstats.py primero.")
        sys.exit(1)

    df = pd.read_parquet(RESULTS)

    cols = ["uc_id", "uc_nm", "buffer_km", "forest_loss_ha",
            "expansion_ha", "overlap_ha", "pct_urban_on_deforested"]
    df_load = df[[c for c in cols if c in df.columns]].copy()

    print("[M3] Cargando en analysis.m3_deforestation")
    load_to_postgis(df_load, "m3_deforestation", if_exists="replace")

    # ── Resumen (buffer 10km) ─────────────────────────────────────────────────
    df_10 = df[df["buffer_km"] == 10].sort_values("pct_urban_on_deforested", ascending=False)

    print("\n── Resumen Módulo 3: Urbanización × Deforestación (buffer 10 km) ──")
    print(df_10[["uc_nm", "forest_loss_ha", "expansion_ha",
                 "overlap_ha", "pct_urban_on_deforested"]]
          .head(15).to_string(index=False))

    # Ciudades con mayor % de expansión sobre bosque perdido
    top3 = df_10.nlargest(3, "pct_urban_on_deforested")
    print(f"\nTop 3 ciudades con expansión sobre deforestación:")
    for _, r in top3.iterrows():
        print(f"  {r['uc_nm']}: {r['pct_urban_on_deforested']:.1f}% "
              f"({r['overlap_ha']:.0f} ha de {r['expansion_ha']:.0f} ha expandidas)")


if __name__ == "__main__":
    main()
