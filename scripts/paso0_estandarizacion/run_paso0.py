"""
Orquestador del Paso 0: Estandarización de datos.

Ejecuta en orden:
  00 → Extracción de ZIPs
  01 → Auditoría de CRS
  06 → Reproyección de vectores (incluye límite Colombia, requerido por 05)
  02 → Mosaico GHSL
  03 → Mosaico Hansen
  04 → Normalización BUILT-S 2018 a 100m
  05 → Clip a Colombia (EPSG:9377, 100m)
  07 → Derivar pendiente desde DEM
  08 → Verificación de integridad

Uso:
    python run_paso0.py              # Ejecuta todos los pasos
    python run_paso0.py --from 05   # Reanuda desde el script indicado
    python run_paso0.py --only 08   # Ejecuta solo un script
"""
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent

STEPS = [
    ("00", "00_extract_zips.py",      "Extracción de ZIPs"),
    ("01", "01_audit_crs.py",         "Auditoría de CRS"),
    ("06", "06_reproject_vectors.py", "Reproyección de vectores"),
    ("02", "02_mosaic_ghsl.py",       "Mosaico GHSL"),
    ("03", "03_mosaic_hansen.py",     "Mosaico Hansen"),
    ("04", "04_resample_built2018.py","Normalización BUILT-S 2018"),
    ("05", "05_clip_to_colombia.py",  "Clip a Colombia (EPSG:9377, 100m)"),
    ("07", "07_derive_slope.py",      "Derivar pendiente"),
    ("08", "08_integrity_check.py",   "Verificación de integridad"),
]


def run_step(script_name: str, label: str) -> bool:
    script_path = SCRIPTS_DIR / script_name
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {script_name}")
    print(f"{'='*60}")
    t0 = datetime.now()
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    elapsed = (datetime.now() - t0).total_seconds()
    if result.returncode == 0:
        print(f"\n  ✓ Completado en {elapsed:.1f}s")
    else:
        print(f"\n  ✗ Falló con código {result.returncode} (después de {elapsed:.1f}s)")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Orquestador Paso 0")
    parser.add_argument("--from", dest="from_step", default=None,
                        help="Número de paso desde el que reanudar (ej: 05)")
    parser.add_argument("--only", dest="only_step", default=None,
                        help="Ejecutar solo un paso específico (ej: 08)")
    args = parser.parse_args()

    steps_to_run = STEPS

    if args.only_step:
        steps_to_run = [(k, s, l) for k, s, l in STEPS if k == args.only_step]
        if not steps_to_run:
            print(f"✗ Paso '{args.only_step}' no encontrado.")
            sys.exit(1)
    elif args.from_step:
        ids = [k for k, _, _ in STEPS]
        if args.from_step not in ids:
            print(f"✗ Paso '{args.from_step}' no encontrado. Disponibles: {ids}")
            sys.exit(1)
        idx = ids.index(args.from_step)
        steps_to_run = STEPS[idx:]

    print(f"\n{'#'*60}")
    print(f"  PASO 0 — Estandarización de datos")
    print(f"  {len(steps_to_run)} script(s) a ejecutar")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    failed = []
    for step_id, script_name, label in steps_to_run:
        ok = run_step(script_name, f"[{step_id}] {label}")
        if not ok:
            failed.append(f"[{step_id}] {label}")
            print(f"\n  ⚠ El paso {step_id} falló. Abortando ejecución.")
            break

    print(f"\n{'#'*60}")
    if failed:
        print(f"  PASO 0 INCOMPLETO — Falló: {failed}")
        sys.exit(1)
    else:
        print(f"  PASO 0 COMPLETADO ✓")
        print(f"  Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
