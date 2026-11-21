"""Experimentos de la Sección 7.3: tamaños × escasez × semillas, algoritmo contra referencias.

Para cada combinación se genera una instancia con el generador de escenarios y se
ejecutan los métodos pedidos (niveles del algoritmo y asignaciones de referencia)
sobre los MISMOS datos. La generación/lectura de datos y la verificación se miden
aparte del tiempo del algoritmo, como pide el documento.

El resumen agrupa por (estudiantes, escasez, método) y da la mediana y el rango
(mínimo y máximo) entre semillas.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from statistics import median
from typing import Any

from .corrida import ejecutar_corrida
from .datos import cargar_instancia
from .generador import Escasez, ParametrosGeneracion, generar_instancia
from .generador.catalogo import MATERIAS
from .referencias import Referencia, ejecutar_referencia

TAMANOS = (20, 200, 500, 2000)
SEMILLAS = tuple(range(10))
METODOS = ("aleatoria", "llegada", "N4", "N10")
# Las secciones crecen con los estudiantes (96 para 250, como la instancia de data/)
SECCIONES_POR_ESTUDIANTE = 96 / 250

# Columnas numéricas que se resumen con mediana y rango
METRICAS = (
    "cobertura",
    "indicador_academico",
    "c5",
    "c4",
    "c3",
    "c2",
    "c1",
    "principales",
    "sustituidas",
    "pendientes",
    "satisfaccion_promedio",
    "satisfaccion_minima",
    "violaciones",
    "tiempo_algoritmo_s",
    "tiempo_datos_s",
    "tiempo_verificacion_s",
)


def secciones_para(estudiantes: int) -> int:
    return max(len(MATERIAS), round(estudiantes * SECCIONES_POR_ESTUDIANTE))


def fila_resumen(salida: dict) -> dict[str, Any]:
    """Métricas compactas de una salida (también las usa la comparación entre niveles de la web)."""
    r, c, v = salida["resumen"], salida["corrida"], salida["verificacion"]
    c5, c4, c3, c2, c1 = r["puntaje_lexicografico"]
    return {
        "cobertura": r["cobertura"],
        "indicador_academico": r["indicador_academico"],
        "c5": c5,
        "c4": c4,
        "c3": c3,
        "c2": c2,
        "c1": c1,
        "principales": r["solicitudes"]["principales"],
        "sustituidas": r["solicitudes"]["sustituidas"],
        "pendientes": r["solicitudes"]["pendientes"],
        "satisfaccion_promedio": r["satisfaccion"]["promedio"],
        "satisfaccion_minima": r["satisfaccion"]["minimo"],
        "violaciones": v["total"],
        "tiempo_algoritmo_s": c["tiempo_algoritmo_s"],
        "tiempo_verificacion_s": c["tiempo_verificacion_s"],
    }


def ejecutar_metodo(instancia, metodo: str, semilla: int) -> dict:
    """`metodo`: 'aleatoria', 'llegada' o 'N<k>'."""
    if metodo in (r.value for r in Referencia):
        return ejecutar_referencia(instancia, metodo, semilla)
    if metodo.startswith("N") and metodo[1:].isdigit():
        return ejecutar_corrida(instancia, int(metodo[1:]))
    raise ValueError(f"método desconocido '{metodo}'; use aleatoria, llegada o N1..N10")


@dataclass(frozen=True)
class Plan:
    tamanos: tuple[int, ...] = TAMANOS
    escaseces: tuple[Escasez, ...] = tuple(Escasez)
    semillas: tuple[int, ...] = SEMILLAS
    metodos: tuple[str, ...] = METODOS

    @property
    def total(self) -> int:
        return len(self.tamanos) * len(self.escaseces) * len(self.semillas) * len(self.metodos)


def ejecutar(plan: Plan, al_avanzar: Callable[[dict], None] | None = None) -> Iterator[dict]:
    """Genera una fila cruda por (estudiantes, escasez, semilla, método)."""
    for estudiantes in plan.tamanos:
        for escasez in plan.escaseces:
            for semilla in plan.semillas:
                inicio = time.perf_counter()
                params = ParametrosGeneracion(estudiantes=estudiantes, secciones=secciones_para(estudiantes), escasez=escasez, semilla=semilla)
                instancia = cargar_instancia(generar_instancia(params))
                tiempo_datos = time.perf_counter() - inicio
                for metodo in plan.metodos:
                    fila = {
                        "estudiantes": estudiantes,
                        "secciones": params.secciones,
                        "escasez": escasez.value,
                        "semilla": semilla,
                        "metodo": metodo,
                        **fila_resumen(ejecutar_metodo(instancia, metodo, semilla)),
                        "tiempo_datos_s": round(tiempo_datos, 4),
                    }
                    if al_avanzar:
                        al_avanzar(fila)
                    yield fila


def resumir(filas: Iterable[dict]) -> list[dict]:
    """Mediana, mínimo y máximo de cada métrica por (estudiantes, escasez, método)."""
    grupos: dict[tuple, list[dict]] = defaultdict(list)
    for f in filas:
        grupos[(f["estudiantes"], f["escasez"], f["metodo"])].append(f)

    orden_escasez = {e.value: i for i, e in enumerate(Escasez)}
    resumen = []
    for (estudiantes, escasez, metodo), grupo in sorted(grupos.items(), key=lambda kv: (kv[0][0], orden_escasez[kv[0][1]], kv[0][2])):
        fila: dict[str, Any] = {"estudiantes": estudiantes, "escasez": escasez, "metodo": metodo, "semillas": len(grupo)}
        for m in METRICAS:
            valores = [g[m] for g in grupo if g[m] is not None]
            fila[f"{m}_mediana"] = round(median(valores), 4) if valores else None
            fila[f"{m}_min"] = round(min(valores), 4) if valores else None
            fila[f"{m}_max"] = round(max(valores), 4) if valores else None
        resumen.append(fila)
    return resumen
