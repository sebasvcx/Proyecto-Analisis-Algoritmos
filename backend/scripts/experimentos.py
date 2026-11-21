"""Experimentos de la Sección 7.3 del documento.

Por defecto: 20, 200, 500 y 2.000 estudiantes × cupos holgados, ajustados y
escasos × semillas 0 a 9, comparando las referencias (aleatoria válida y por
orden de llegada) con N4 y N10 sobre los mismos datos. Guarda:

  resultados/experimentos/<fecha>/crudo.csv    una fila por instancia y método
  resultados/experimentos/<fecha>/resumen.csv  mediana y rango (mín–máx) entre semillas
  resultados/experimentos/<fecha>/meta.json    equipo, versiones y parámetros usados

Uso (desde backend/):
    .venv/bin/python scripts/experimentos.py                       # completo (~4 min)
    .venv/bin/python scripts/experimentos.py --tamanos 20 200 --semillas 3
    .venv/bin/python scripts/experimentos.py --metodos llegada N10
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asignador import __version__  # noqa: E402
from asignador.experimentos import METODOS, SEMILLAS, TAMANOS, Plan, ejecutar, resumir  # noqa: E402
from asignador.generador import Escasez  # noqa: E402
from asignador.generador.escenarios import VERSION_GENERADOR  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def escribir_csv(ruta: Path, filas: list[dict]) -> None:
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tamanos", type=int, nargs="+", default=list(TAMANOS), help="números de estudiantes")
    parser.add_argument("--escasez", nargs="+", choices=[e.value for e in Escasez], default=[e.value for e in Escasez])
    parser.add_argument("--semillas", type=int, default=len(SEMILLAS), help="se usan las semillas 0..n-1")
    parser.add_argument("--metodos", nargs="+", default=list(METODOS), help="aleatoria, llegada y/o N1..N10")
    parser.add_argument("--salida", type=Path, default=RAIZ / "resultados" / "experimentos" / datetime.now().strftime("%Y%m%d-%H%M%S"))
    args = parser.parse_args()

    plan = Plan(tuple(args.tamanos), tuple(Escasez(e) for e in args.escasez), tuple(range(args.semillas)), tuple(args.metodos))
    args.salida.mkdir(parents=True, exist_ok=True)

    hechas = 0
    inicio = time.perf_counter()

    def avanzar(fila: dict) -> None:
        nonlocal hechas
        hechas += 1
        print(
            f"\r[{hechas}/{plan.total}] {fila['estudiantes']} est · {fila['escasez']} · semilla {fila['semilla']} · {fila['metodo']}".ljust(70),
            end="",
            flush=True,
        )

    crudas = list(ejecutar(plan, avanzar))
    duracion = time.perf_counter() - inicio
    print()

    resumen = resumir(crudas)
    escribir_csv(args.salida / "crudo.csv", crudas)
    escribir_csv(args.salida / "resumen.csv", resumen)
    meta = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "duracion_s": round(duracion, 1),
        "version_algoritmo": __version__,
        "version_generador": VERSION_GENERADOR,
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "plan": {"tamanos": plan.tamanos, "escasez": [e.value for e in plan.escaseces], "semillas": list(plan.semillas), "metodos": plan.metodos},
    }
    (args.salida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    violaciones = sum(f["violaciones"] for f in crudas)
    print(f"{len(crudas)} corridas en {duracion:.1f} s · violaciones totales: {violaciones}")
    print(f"Guardado en {args.salida}")
    return 0 if violaciones == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
