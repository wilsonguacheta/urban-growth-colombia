"""
Módulo 4: Exposición a Amenazas Naturales.
- AMENAZA-FLOOD (vector): intersección espacial en PostGIS vía SQL (ver m4_queries.sql).
- AMENAZA-MM (raster): estadísticas zonales categóricas por ciudad y año.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import GHSL_YEARS, GHSL_NODATA, MM_NODATA, CLIPPED_DIR, VECTORS_DIR, PIXEL_HA
from scripts.modulos_analisis.base_rasterstats import (
    extract_zonal_stats, get_raster_path, ucdb_path
)

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

YEARS_POP  = GHSL_YEARS["pop"]
MM_CLASSES = {1: "baja", 2: "media", 3: "alta", 4: "muy_alta"}


def compute_mm_exposure() -> pd.DataFrame:
    """
    Distribución de píxeles de amenaza MM por clase dentro de cada ciudad.
    Para cada año de POP: cruza con MM (estático) para calcular exposición.
    """
    mm_path = CLIPPED_DIR / "amenaza_mm_col.tif"
    if not mm_path.exists():
        raise FileNotFoundError(f"No encontrado: {mm_path}")

    # Estadísticas categóricas una sola vez (MM es estático)
    df_mm = extract_zonal_stats(
        ucdb_path(), mm_path,
        stats=["count"],
        nodata=MM_NODATA,
        categorical=True,
    )

    # Renombrar clases: columna '1' → 'mm_baja', etc.
    for cls, label in MM_CLASSES.items():
        col_src = str(cls)
        df_mm[f"px_{label}"] = df_mm.get(col_src, 0).fillna(0)

    df_mm["px_total_mm"] = df_mm[[f"px_{v}" for v in MM_CLASSES.values()]].sum(axis=1)

    records = []
    for year in YEARS_POP:
        pop_path = get_raster_path("pop", year)
        if not pop_path.exists():
            continue

        df_pop = extract_zonal_stats(
            ucdb_path(), pop_path,
            stats=["sum"],
            nodata=GHSL_NODATA["pop"],
            prefix="pop_",
        )
        df_pop["pop_total"] = df_pop["pop_sum"].fillna(0)

        df_built = pd.read_parquet(
            Path(__file__).parents[1] / "modulo1_crecimiento_urbano" / "m1_results.parquet"
        )
        df_built_y = df_built[df_built["year"] == year][["uc_id", "built_area_m2"]]

        merged = df_pop[["uc_id", "uc_nm", "pop_total"]].merge(
            df_mm[["uc_id"] + [f"px_{v}" for v in MM_CLASSES.values()] + ["px_total_mm"]],
            on="uc_id", how="left"
        ).merge(df_built_y, on="uc_id", how="left")

        for cls, label in MM_CLASSES.items():
            px_col = f"px_{label}"
            pop_exposed = (
                merged[px_col] / merged["px_total_mm"].replace(0, float("nan"))
                * merged["pop_total"]
            ).fillna(0)
            built_exposed = (merged[px_col] * PIXEL_HA * 10000)  # ha → m²

            records.append(pd.DataFrame({
                "uc_id":             merged["uc_id"],
                "uc_nm":             merged["uc_nm"],
                "year":              year,
                "hazard_type":       "mass_movement",
                "hazard_class":      cls,
                "pop_exposed":       pop_exposed.round(0),
                "built_exposed_m2":  built_exposed.round(0),
                "pct_pop_exposed":   (pop_exposed / merged["pop_total"].replace(0, float("nan")) * 100).round(2),
                "pct_built_exposed": (built_exposed / merged["built_area_m2"].replace(0, float("nan")) * 100).round(2),
            }))
        print(f"  ✓ MM × {year}")

    return pd.concat(records, ignore_index=True)


def main():
    print("[Módulo 4 — Amenaza por Movimientos en Masa (raster)]")
    df = compute_mm_exposure()
    out = Path(__file__).parent / "m4_mm_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados MM: {out}  ({len(df)} filas)")
    print("\nNota: La exposición a FLOOD (vectorial) se calcula con m4_queries.sql en PostGIS.")


if __name__ == "__main__":
    main()
