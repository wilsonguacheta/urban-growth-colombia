"""
Orquestador de los 6 módulos analíticos.
Ejecuta rasterstats + indicadores de cada módulo en secuencia.

Uso:
    python run_modulos.py              # Todos los módulos
    python run_modulos.py --from m3    # Desde el módulo indicado
    python run_modulos.py --only m1    # Solo un módulo
    python run_modulos.py --step rs    # Solo rasterstats (rs) o indicadores (ind)
"""
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent

MODULES = [
    ("m1", "modulo1_crecimiento_urbano",    "Crecimiento Urbano"),
    ("m2", "modulo2_presion_poblacional",   "Presión Poblacional"),
    ("m3", "modulo3_deforestacion",         "Deforestación"),
    ("m4", "modulo4_amenazas",              "Amenazas Naturales"),
    ("m5", "modulo5_runap",                 "Presión sobre RUNAP"),
    ("m6", "modulo6_topografia",            "Topografía"),
]


def run_script(script_path: Path, label: str) -> bool:
    t0 = datetime.now()
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    elapsed = (datetime.now() - t0).total_seconds()
    ok = result.returncode == 0
    icon = "✓" if ok else "✗"
    print(f"  {icon} {label}  ({elapsed:.1f}s)")
    return ok


def run_module(mod_id: str, mod_dir: str, label: str, step: str = "both") -> bool:
    print(f"\n{'='*60}")
    print(f"  [{mod_id.upper()}] {label}")
    print(f"{'='*60}")

    rs_path  = BASE / mod_dir / f"{mod_id}_rasterstats.py"
    ind_path = BASE / mod_dir / f"{mod_id}_indicadores.py"

    ok = True
    if step in ("rs", "both"):
        ok = run_script(rs_path, "rasterstats") and ok
    if step in ("ind", "both") and ok:
        ok = run_script(ind_path, "indicadores") and ok
    return ok


def main():
    parser = argparse.ArgumentParser(description="Orquestador de módulos analíticos")
    parser.add_argument("--from",  dest="from_mod",  default=None,
                        help="Módulo desde el que reanudar (m1–m6)")
    parser.add_argument("--only",  dest="only_mod",  default=None,
                        help="Ejecutar solo un módulo (m1–m6)")
    parser.add_argument("--step",  dest="step",      default="both",
                        choices=["rs", "ind", "both"],
                        help="Ejecutar solo rasterstats (rs), indicadores (ind) o ambos (both)")
    args = parser.parse_args()

    modules = MODULES
    if args.only_mod:
        modules = [(k, d, l) for k, d, l in MODULES if k == args.only_mod]
        if not modules:
            print(f"✗ Módulo '{args.only_mod}' no reconocido.")
            sys.exit(1)
    elif args.from_mod:
        ids = [k for k, _, _ in MODULES]
        if args.from_mod not in ids:
            print(f"✗ Módulo '{args.from_mod}' no reconocido. Opciones: {ids}")
            sys.exit(1)
        modules = MODULES[ids.index(args.from_mod):]

    print(f"\n{'#'*60}")
    print(f"  MÓDULOS ANALÍTICOS — {len(modules)} módulo(s)")
    print(f"  Paso: {args.step.upper()}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    failed = []
    for mod_id, mod_dir, label in modules:
        ok = run_module(mod_id, mod_dir, label, step=args.step)
        if not ok:
            failed.append(f"[{mod_id}] {label}")
            print(f"\n  ⚠ Módulo {mod_id} falló. Abortando.")
            break

    print(f"\n{'#'*60}")
    if failed:
        print(f"  INCOMPLETO — Falló: {failed}")
        sys.exit(1)
    else:
        print(f"  MÓDULOS COMPLETADOS ✓")
        print(f"  Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
