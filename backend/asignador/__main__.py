"""Línea de comandos del asignador.

Ejemplos (desde backend/):
    python -m asignador generar --estudiantes 250 --semilla 42 --datos ../data
    python -m asignador validar --datos ../data
    python -m asignador ejecutar --nivel 2 --datos ../data --resultados ../resultados
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .algoritmo import NivelNoDisponible
from .corrida import ejecutar_corrida, guardar_corrida
from .datos import construir_instancia, escribir_carpeta, leer_carpeta
from .generador import Escasez, ParametrosGeneracion, generar_instancia

RAIZ = Path(__file__).resolve().parents[2]


def _cmd_generar(args) -> int:
    params = ParametrosGeneracion(
        estudiantes=args.estudiantes,
        secciones=args.secciones,
        porcentaje_trabaja=args.trabaja,
        escasez=Escasez(args.escasez),
        semilla=args.semilla,
    )
    crudos = generar_instancia(params)
    escribir_carpeta(args.datos, crudos)
    print(f"Instancia generada en {args.datos}: {len(crudos['estudiantes'])} estudiantes, {len(crudos['secciones'])} secciones")
    return 0


def _cargar(carpeta: Path):
    crudos, fallos = leer_carpeta(carpeta)
    instancia, reporte = construir_instancia(crudos, fallos)
    for p in reporte.problemas:
        print(f"[{p.gravedad.value}] {p}")
    return crudos, instancia, reporte


def _cmd_validar(args) -> int:
    _, _, reporte = _cargar(args.datos)
    print(f"{len(reporte.errores)} errores · {len(reporte.advertencias)} advertencias")
    return 0 if reporte.es_valido else 1


def _cmd_ejecutar(args) -> int:
    crudos, instancia, reporte = _cargar(args.datos)
    if instancia is None:
        print("No se ejecuta: corrija los errores anteriores.", file=sys.stderr)
        return 1
    try:
        salida = ejecutar_corrida(instancia, args.nivel)
    except NivelNoDisponible as exc:
        print(exc, file=sys.stderr)
        return 2
    destino = guardar_corrida(args.resultados, salida, crudos)
    r, c, v = salida["resumen"], salida["corrida"], salida["verificacion"]
    print(f"Nivel {c['nivel']} · {c['estudiantes']} estudiantes · {c['tiempo_algoritmo_s']} s")
    print(f"Cobertura {r['cobertura']} · Q = {r['puntaje_lexicografico']} · violaciones {v['total']} {v['por_regla']}")
    print(f"Guardado en {destino}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="asignador", description="Asignación de horarios estudiantiles")
    parser.add_argument("--datos", type=Path, default=RAIZ / "data", help="carpeta con los JSON de entrada")
    sub = parser.add_subparsers(dest="comando", required=True)

    gen = sub.add_parser("generar", help="genera una instancia sintética y reemplaza los JSON")
    gen.add_argument("--estudiantes", type=int, default=250)
    gen.add_argument("--secciones", type=int, default=96)
    gen.add_argument("--trabaja", type=float, default=0.2, help="proporción de estudiantes que trabajan (0 a 1)")
    gen.add_argument("--escasez", choices=[e.value for e in Escasez], default="ajustada")
    gen.add_argument("--semilla", type=int, default=42)
    gen.set_defaults(func=_cmd_generar)

    val = sub.add_parser("validar", help="valida los JSON sin ejecutar")
    val.set_defaults(func=_cmd_validar)

    eje = sub.add_parser("ejecutar", help="ejecuta una corrida y guarda el resultado")
    eje.add_argument("--nivel", type=int, default=2)
    eje.add_argument("--resultados", type=Path, default=RAIZ / "resultados")
    eje.set_defaults(func=_cmd_ejecutar)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
