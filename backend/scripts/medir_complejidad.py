"""Mide cómo crece el tiempo del algoritmo para contrastarlo con el análisis de complejidad.

Dos series, cada punto con la mediana de varias repeticiones:
  A) variar el número de estudiantes E con secciones por materia fijas;
  B) variar las secciones por materia σ con E fijo.
Para cada serie estima el exponente de crecimiento (pendiente en escala log-log).

Uso (desde backend/):
    .venv/Scripts/python scripts/medir_complejidad.py            # Windows
    .venv/bin/python scripts/medir_complejidad.py                # Linux / macOS
"""

from __future__ import annotations

import math
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asignador.algoritmo import asignar  # noqa: E402
from asignador.datos import cargar_instancia  # noqa: E402
from asignador.generador import Escasez, ParametrosGeneracion, generar_instancia  # noqa: E402
from asignador.generador.catalogo import MATERIAS  # noqa: E402

NIVELES = (4, 9, 10)
REPETICIONES = 3
MATERIAS_CATALOGO = len(MATERIAS)


def medir(estudiantes: int, secciones: int, semilla: int = 0) -> dict:
    inst = cargar_instancia(generar_instancia(ParametrosGeneracion(estudiantes=estudiantes, secciones=secciones, semilla=semilla, escasez=Escasez.AJUSTADA)))
    solicitudes = sum(len(e.solicitudes) for e in inst.estudiantes.values())
    fila = {"E": estudiantes, "S": secciones, "sigma": secciones / MATERIAS_CATALOGO, "R": solicitudes}
    for nivel in NIVELES:
        tiempos = []
        for _ in range(REPETICIONES):
            inicio = time.perf_counter()
            asignacion = asignar(inst, nivel)
            tiempos.append(time.perf_counter() - inicio)
        fila[f"N{nivel}"] = statistics.median(tiempos)
        if asignacion.mejora:
            fila["examinados"] = asignacion.mejora["cambios_examinados"]
    return fila


def pendiente(xs: list[float], ys: list[float]) -> float:
    """Pendiente de mínimos cuadrados de log(y) contra log(x): tiempo ≈ c · x^pendiente."""
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    mx, my = statistics.fmean(lx), statistics.fmean(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


def imprimir(titulo: str, filas: list[dict], variable: str) -> None:
    print(f"\n{titulo}")
    print(f"{'E':>6} {'S':>5} {'σ':>6} {'R':>7} " + " ".join(f"{'N' + str(n) + ' (s)':>10}" for n in NIVELES) + f" {'examinados':>11}")
    for f in filas:
        print(f"{f['E']:>6} {f['S']:>5} {f['sigma']:>6.2f} {f['R']:>7} " + " ".join(f"{f[f'N{n}']:>10.4f}" for n in NIVELES) + f" {f.get('examinados', ''):>11}")
    xs = [f[variable] for f in filas]
    print("exponente estimado (tiempo ∝ " + variable + "^p): " + ", ".join(f"N{n}: p = {pendiente(xs, [f[f'N{n}'] for f in filas]):.2f}" for n in NIVELES))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows usa cp1252 y no imprime σ
    print(f"Python {platform.python_version()} · {platform.processor() or platform.machine()} · {REPETICIONES} repeticiones (mediana)")
    # σ ≈ 2,3 fijo (96 secciones para las 42 materias del catálogo)
    serie_a = [medir(e, 96) for e in (250, 500, 1000, 2000)]
    imprimir("A) Variar estudiantes con σ fijo", serie_a, "E")
    serie_b = [medir(500, s) for s in (60, 120, 240, 480)]
    imprimir("B) Variar secciones por materia con E = 500", serie_b, "sigma")


if __name__ == "__main__":
    main()
