"""
Paso 0 - Script 00: Extracción de archivos ZIP de los datasets GHSL, UCDB y RUNAP.
Registra cada extracción en data/logs/extraction_log.csv.
"""
import zipfile
import csv
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import (
    SOURCES, EXTRACTED_DIR, LOGS_DIR, GHSL_YEARS
)


def extract_zip(zip_path: Path, dest_dir: Path) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest_dir)
            n = len(zf.namelist())
        return {"status": "OK", "n_files": n, "error": ""}
    except Exception as e:
        return {"status": "ERROR", "n_files": 0, "error": str(e)}


def extract_ghsl_product(product: str, source_dir: Path, target_base: Path) -> list:
    records = []
    for year in GHSL_YEARS[product]:
        year_dir = source_dir / str(year)
        if not year_dir.exists():
            continue
        dest = target_base / "ghsl" / product / str(year)
        for zip_path in sorted(year_dir.glob("*.zip")):
            result = extract_zip(zip_path, dest)
            records.append({
                "zip_path": str(zip_path),
                "dest_dir": str(dest),
                "product":  product,
                "year":     year,
                **result,
                "timestamp": datetime.now().isoformat(),
            })
            status_icon = "✓" if result["status"] == "OK" else "✗"
            print(f"  {status_icon} {zip_path.name} → {dest.name}/")
    return records


def extract_single_zip(name: str, zip_path: Path, dest_dir: Path) -> list:
    if not zip_path.exists():
        print(f"  ! No encontrado: {zip_path}")
        return []
    result = extract_zip(zip_path, dest_dir)
    status_icon = "✓" if result["status"] == "OK" else "✗"
    print(f"  {status_icon} {zip_path.name} → {dest_dir.name}/")
    return [{
        "zip_path": str(zip_path),
        "dest_dir": str(dest_dir),
        "product":  name,
        "year":     None,
        **result,
        "timestamp": datetime.now().isoformat(),
    }]


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "extraction_log.csv"
    all_records = []

    # ── GHSL rasters (built_s, pop, smod) ────────────────────────────────────
    for product in ("built_s", "pop", "smod"):
        print(f"\n[{product.upper()}]")
        records = extract_ghsl_product(product, SOURCES[product], EXTRACTED_DIR)
        all_records.extend(records)

    # ── UCDB ─────────────────────────────────────────────────────────────────
    print("\n[UCDB]")
    for zip_path in sorted(SOURCES["ucdb"].glob("*.zip")):
        all_records.extend(
            extract_single_zip("ucdb", zip_path, EXTRACTED_DIR / "ucdb")
        )

    # ── RUNAP ─────────────────────────────────────────────────────────────────
    print("\n[RUNAP]")
    runap_zip = SOURCES["runap"] / "latest.zip"
    all_records.extend(
        extract_single_zip("runap", runap_zip, EXTRACTED_DIR / "runap")
    )

    # ── GHSL grid shapefile ───────────────────────────────────────────────────
    print("\n[GHSL_GRID]")
    for zip_path in sorted(SOURCES["ghsl_grid"].glob("*.zip")):
        all_records.extend(
            extract_single_zip("ghsl_grid", zip_path, EXTRACTED_DIR / "ghsl_grid")
        )

    # ── Escribir log ─────────────────────────────────────────────────────────
    if all_records:
        fieldnames = ["zip_path", "dest_dir", "product", "year",
                      "status", "n_files", "error", "timestamp"]
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)

    ok  = sum(1 for r in all_records if r["status"] == "OK")
    err = sum(1 for r in all_records if r["status"] == "ERROR")
    print(f"\n── Extracción completa: {ok} OK | {err} ERROR")
    print(f"   Log: {log_path}")
    return err == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
