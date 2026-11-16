"""Compara un nivel del algoritmo con la solución exacta en instancias pequeñas (Sección 7.1).

Resultados posibles por instancia:
- "optimo": el algoritmo obtuvo exactamente el mejor resultado.
- "empate": difiere solo en el último desempate (lista de registros); en lo
  sustantivo (C, J, satisfacción y sustitutas) es igual de bueno.
- "peor": el óptimo gana en algún criterio; se informa en cuál.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass

from .corrida import ejecutar_corrida
from .datos import cargar_instancia
from .dominio import Instancia
from .exacto import resolver
from .generador.pequenos import generar_pequena
from .metricas import puntaje
from .objetivo import comparar, criterio_decisivo


@dataclass(frozen=True)
class Comparacion:
    resultado: str  # "optimo" | "empate" | "peor"
    criterio: str | None  # criterio de la Sección 5.4 en que gana el óptimo (si es "peor")
    c_algoritmo: tuple[float, ...]
    c_optimo: tuple[float, ...]
    nodos: int
    tiempo_exacto_s: float


def comparar_con_optimo(instancia: Instancia, nivel: int = 10) -> Comparacion:
    salida = ejecutar_corrida(instancia, nivel)
    if salida["verificacion"]["total"]:
        raise AssertionError(f"el nivel {nivel} produjo una salida inválida: {salida['verificacion']['por_regla']}")
    del_algoritmo = puntaje(instancia, salida["estudiantes"])

    inicio = time.perf_counter()
    optimo = resolver(instancia)
    tiempo = time.perf_counter() - inicio

    signo = comparar(del_algoritmo, optimo.puntaje)
    if signo > 0:
        raise AssertionError("el algoritmo superó a la solución exacta: la búsqueda exhaustiva tiene un error")
    criterio = criterio_decisivo(optimo.puntaje, del_algoritmo)
    resultado = "optimo" if criterio is None else ("empate" if criterio == "registros" else "peor")
    return Comparacion(resultado, criterio if resultado == "peor" else None, del_algoritmo.c, optimo.puntaje.c, optimo.nodos, tiempo)


def resumen_de_casos(semillas: range, *, nivel: int = 10, desempate_semestre: bool = False) -> dict:
    """Compara el nivel con el óptimo en muchas instancias pequeñas generadas."""
    comparaciones = [
        comparar_con_optimo(cargar_instancia(generar_pequena(s, desempate_semestre=desempate_semestre)), nivel) for s in semillas
    ]
    resultados = Counter(c.resultado for c in comparaciones)
    criterios = Counter(c.criterio for c in comparaciones if c.criterio)
    total = len(comparaciones)
    return {
        "casos": total,
        "nivel": nivel,
        "optimo": resultados["optimo"],
        "empate": resultados["empate"],
        "peor": resultados["peor"],
        "porcentaje_igual_de_bueno": round(100 * (resultados["optimo"] + resultados["empate"]) / total, 1) if total else None,
        "peor_por_criterio": dict(criterios),
        "max_nodos": max((c.nodos for c in comparaciones), default=0),
        "max_tiempo_exacto_s": round(max((c.tiempo_exacto_s for c in comparaciones), default=0), 4),
    }
