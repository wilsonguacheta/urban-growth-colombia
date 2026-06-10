"""
Módulo 5: Presión sobre Áreas Protegidas (RUNAP).
- Distancia ciudad→AP más cercana: calculada con ST_Distance en PostGIS (ver m5_queries.sql).
- Superficie construida dentro de cada AP: rasterstats sobre polígonos RUNAP.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import GHSL_YEARS, GHSL_NODATA, PIXEL_HA
from scripts.modulos_analisis.base_rasterstats import (
    extract_zonal_stats, get_raster_path, runap_path
)


def compute_built_inside_runap() -> pd.DataFrame:
    """
    Para cada año de BUILT-S: suma de m² construidos dentro de cada AP.
    Años comunes: excluye 2018 para consistencia de serie temporal.
    """
    years = [y for y in GHSL_YEARS["built_s"] if y != 2018]
    records = []
    for year in years:
        raster = get_raster_path("built_s", year)
        if not raster.exists():
            continue
        df = extract_zonal_stats(
            runap_path(), raster,
            stats=["sum"],
            nodata=GHSL_NODATA["built_s"],
            prefix="bs_",
        )
        df["year"]           = year
        df["built_inside_m2"] = df["bs_sum"].fillna(0)
        df["built_inside_ha"] = df["built_inside_m2"] / 10000.0
        records.append(df[["gid", "nombre", "categoria", "area_ha", "year",
                             "built_inside_m2", "built_inside_ha"]])
        print(f"  ✓ RUNAP × BUILT-S {year}")

    return pd.concat(records, ignore_index=True)


def main():
    print("[Módulo 5 — Áreas Protegidas]")
    df = compute_built_inside_runap()
    out = Path(__file__).parent / "m5_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados: {out}  ({len(df)} filas)")
    print("\nNota: Distancias ciudad→AP se calculan con m5_queries.sql en PostGIS.")


if __name__ == "__main__":
    main()
