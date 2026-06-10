"""
Módulo 1: Dinámica del Crecimiento Urbano.
Extrae suma de superficie construida (m²) por ciudad y año.
Calcula tasa de crecimiento y delta entre períodos.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import GHSL_YEARS, GHSL_NODATA
from scripts.modulos_analisis.base_rasterstats import (
    extract_zonal_stats, get_raster_path, ucdb_path
)


def compute_m1() -> pd.DataFrame:
    """
    Para cada año de GHS-BUILT-S: extrae sum de píxeles por ciudad UCDB.
    GHS-BUILT-S valores = m² de superficie construida por celda (100m×100m).
    sum(píxeles) = m² totales construidos dentro del polígono.
    """
    records = []
    for year in GHSL_YEARS["built_s"]:
        raster = get_raster_path("built_s", year)
        if not raster.exists():
            print(f"  ! Raster no encontrado: {raster.name}")
            continue

        df = extract_zonal_stats(
            ucdb_path(), raster,
            stats=["sum", "count"],
            nodata=GHSL_NODATA["built_s"],
            prefix=f"bs_",
        )

        df["year"]          = year
        df["built_area_m2"] = df["bs_sum"].fillna(0)
        records.append(df[["uc_id", "uc_nm", "year", "built_area_m2"]])
        print(f"  ✓ {year}: {len(df)} ciudades procesadas")

    df_all = pd.concat(records, ignore_index=True)

    # Ordenar y calcular deltas entre períodos consecutivos
    df_all = df_all.sort_values(["uc_id", "year"]).reset_index(drop=True)
    df_all["built_area_m2_prev"] = df_all.groupby("uc_id")["built_area_m2"].shift(1)
    df_all["year_prev"]          = df_all.groupby("uc_id")["year"].shift(1)
    df_all["delta_m2"]           = df_all["built_area_m2"] - df_all["built_area_m2_prev"]
    df_all["growth_rate_pct"]    = (
        df_all["delta_m2"] / df_all["built_area_m2_prev"].replace(0, float("nan")) * 100
    ).round(2)

    df_all = df_all.drop(columns=["built_area_m2_prev"])
    return df_all


def main():
    print("[Módulo 1 — Crecimiento Urbano]")
    df = compute_m1()
    out = Path(__file__).parent / "m1_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados: {out}  ({len(df)} filas)")
    print(df.groupby("year")["built_area_m2"].sum().apply(lambda x: f"{x/1e9:.2f} Gm²").to_string())


if __name__ == "__main__":
    main()
