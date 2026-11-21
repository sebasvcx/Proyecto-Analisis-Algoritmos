"""Compara un nivel con la respuesta plantada de los casos con respuesta conocida (Sección 7.1, tipo 2).

La respuesta plantada atiende todas las solicitudes con su principal, así que su
vector C es el máximo posible. La comparación dice si el algoritmo también
atiende todo y, si no, cuánto le falta en cada prioridad.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .corrida import ejecutar_corrida
from .datos import cargar_instancia
from .generador.conocidos import CasoConocido, generar_conocido
from .metricas import calcular_metricas
from .verificador import verificar


@dataclass(frozen=True)
class ComparacionConocida:
    atiende_todo: bool
    cobertura: float | None
    faltantes_por_prioridad: tuple[float, ...]  # C de la respuesta plantada menos C del algoritmo (5..1)
    referencia_valida: bool


NIVEL_MINIMO = 3  # desde N3 se aplican R1–R8; antes la salida puede violar reglas que la respuesta sí cumple


def comparar_con_conocido(caso: CasoConocido, nivel: int = 10) -> ComparacionConocida:
    if nivel < NIVEL_MINIMO:
        raise ValueError(f"solo se compara desde el nivel {NIVEL_MINIMO}: los anteriores no aplican todas las reglas")
    instancia = cargar_instancia(caso.crudos)
    referencia = caso.salida_de_referencia()
    referencia_valida = verificar(instancia, referencia).violaciones == []
    c_ref = calcular_metricas(instancia, referencia)["puntaje_lexicografico"]

    salida = ejecutar_corrida(instancia, nivel)
    if salida["verificacion"]["total"]:
        raise AssertionError(f"el nivel {nivel} produjo una salida inválida: {salida['verificacion']['por_regla']}")
    c_alg = salida["resumen"]["puntaje_lexicografico"]
    faltantes = tuple(round(r - a, 4) for r, a in zip(c_ref, c_alg))
    return ComparacionConocida(all(f <= 1e-9 for f in faltantes), salida["resumen"]["cobertura"], faltantes, referencia_valida)


def resumen_conocidos(semillas: range, *, nivel: int = 10, estudiantes: int = 30, materias: int = 10) -> dict:
    comparaciones = [comparar_con_conocido(generar_conocido(s, estudiantes, materias), nivel) for s in semillas]
    total = len(comparaciones)
    coberturas = [c.cobertura for c in comparaciones if c.cobertura is not None]
    return {
        "casos": total,
        "nivel": nivel,
        "estudiantes": estudiantes,
        "referencias_validas": sum(c.referencia_valida for c in comparaciones),
        "atiende_todo": sum(c.atiende_todo for c in comparaciones),
        "porcentaje_atiende_todo": round(100 * sum(c.atiende_todo for c in comparaciones) / total, 1) if total else None,
        "cobertura_promedio": round(mean(coberturas), 4) if coberturas else None,
        "cobertura_minima": round(min(coberturas), 4) if coberturas else None,
        "faltantes_promedio_por_prioridad": [round(mean(c.faltantes_por_prioridad[i] for c in comparaciones), 3) for i in range(5)] if total else [],
    }
