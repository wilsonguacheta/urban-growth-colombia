"""
Módulo 2: Presión Poblacional y Densificación.
Extrae población total por ciudad y año, calcula densidad e índice de sprawl.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings import GHSL_YEARS, GHSL_NODATA, COMMON_YEARS
from scripts.modulos_analisis.base_rasterstats import (
    extract_zonal_stats, get_raster_path, ucdb_path
)


def compute_m2() -> pd.DataFrame:
    """
    Extrae suma de población por ciudad y año.
    Importa resultados de M1 para calcular índice de sprawl.
    """
    # ── Población ─────────────────────────────────────────────────────────────
    pop_records = []
    for year in GHSL_YEARS["pop"]:
        raster = get_raster_path("pop", year)
        if not raster.exists():
            continue
        df = extract_zonal_stats(
            ucdb_path(), raster,
            stats=["sum"],
            nodata=GHSL_NODATA["pop"],
            prefix="pop_",
        )
        df["year"]      = year
        df["pop_total"] = df["pop_sum"].fillna(0)
        pop_records.append(df[["uc_id", "uc_nm", "year", "pop_total"]])
        print(f"  ✓ POP {year}")

    df_pop = pd.concat(pop_records, ignore_index=True)

    # ── Cargar resultados M1 ──────────────────────────────────────────────────
    m1_path = Path(__file__).parents[1] / "modulo1_crecimiento_urbano" / "m1_results.parquet"
    if not m1_path.exists():
        raise FileNotFoundError(f"Ejecuta primero el Módulo 1.\n  Esperado: {m1_path}")
    df_built = pd.read_parquet(m1_path)

    # Años comunes entre POP y BUILT-S (excluye 2018)
    df = df_pop[df_pop["year"].isin(COMMON_YEARS)].merge(
        df_built[["uc_id", "year", "built_area_m2"]], on=["uc_id", "year"], how="left"
    )

    # Densidad: hab / km²
    df["pop_density"] = (
        df["pop_total"] / (df["built_area_m2"] / 1e6).replace(0, float("nan"))
    ).round(2)

    # Índice de sprawl entre años consecutivos (solo COMMON_YEARS)
    df = df.sort_values(["uc_id", "year"]).reset_index(drop=True)
    df["pop_prev"]    = df.groupby("uc_id")["pop_total"].shift(1)
    df["built_prev"]  = df.groupby("uc_id")["built_area_m2"].shift(1)
    df["year_prev"]   = df.groupby("uc_id")["year"].shift(1)

    df["delta_pop_pct"]   = (df["pop_total"]   - df["pop_prev"])   / df["pop_prev"].replace(0, float("nan")) * 100
    df["delta_built_pct"] = (df["built_area_m2"] - df["built_prev"]) / df["built_prev"].replace(0, float("nan")) * 100
    df["sprawl_index"]    = (
        df["delta_built_pct"] / df["delta_pop_pct"].replace(0, float("nan"))
    ).round(3)
    df["densification"] = df["sprawl_index"] < 1.0

    # Índice de sprawl acumulado desde 2000 (base explícita del período analítico).
    # Mide el ratio total area_construida / crecimiento_poblacional desde 2000 a cada año.
    # Consistente con los ejes del scatter 2000→2025. NaN para años anteriores a 2000.
    base_2000 = (
        df[df["year"] == 2000][["uc_id", "pop_total", "built_area_m2"]]
        .rename(columns={"pop_total": "pop_base", "built_area_m2": "built_base"})
    )
    df = df.merge(base_2000, on="uc_id", how="left")
    _delta_pop_acum   = (df["pop_total"]     - df["pop_base"])   / df["pop_base"].replace(0, float("nan")) * 100
    _delta_built_acum = (df["built_area_m2"] - df["built_base"]) / df["built_base"].replace(0, float("nan")) * 100
    df["sprawl_index_acum"] = (
        _delta_built_acum / _delta_pop_acum.replace(0, float("nan"))
    ).clip(0, 3).round(3)
    df = df.drop(columns=["pop_base", "built_base"])

    return df.drop(columns=["pop_prev", "built_prev", "delta_pop_pct", "delta_built_pct"])


def main():
    print("[Módulo 2 — Presión Poblacional]")
    df = compute_m2()
    out = Path(__file__).parent / "m2_results.parquet"
    df.to_parquet(out, index=False)
    print(f"\n✓ Resultados: {out}  ({len(df)} filas)")


if __name__ == "__main__":
    main()
