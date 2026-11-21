"""Asignaciones de referencia para comparar el algoritmo (Sección 7.3).

- **Aleatoria válida:** todas las solicitudes en orden aleatorio y, para cada una,
  una sección elegida al azar entre las que cumplen las reglas.
- **Orden de llegada:** los estudiantes se atienden uno tras otro en el orden en
  que aparecen en `estudiantes.json` (como una inscripción por turnos); cada uno
  inscribe sus materias de mayor a menor prioridad y toma la primera sección válida.

Ambas usan los mismos datos y las mismas reglas obligatorias que el nivel 10
(R1–R9, con sustitutas), para que la comparación mida solo la calidad de las
decisiones. Ninguna usa preferencias, desempate por semestre ni mejora local.

Solo se importan piezas de `algoritmo/` (TAD Horario, reglas, diagnóstico de
avisos); este módulo no modifica el algoritmo.

Complejidad: con R solicitudes en total, a lo sumo K secciones candidatas por
solicitud (principal más sustitutas) y comprobaciones de reglas en O(m) con m las
sesiones del horario del estudiante, ambas cuestan O(R·K·m) más la ordenación
(O(R log R) en llegada; el barajado aleatorio es O(R + K) por solicitud).
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

from .algoritmo import NIVELES, Asignacion, Contexto, Horario, Inscripcion, Nivel
from .algoritmo.causas import Causa
from .algoritmo.voraz import diagnosticar
from .corrida import armar_salida
from .dominio import Estudiante, Instancia, Seccion, Solicitud


class Referencia(str, Enum):
    ALEATORIA = "aleatoria"
    LLEGADA = "llegada"

    @property
    def nombre(self) -> str:
        return {"aleatoria": "Referencia aleatoria válida", "llegada": "Referencia por orden de llegada"}[self.value]


def _nivel(tipo: Referencia) -> Nivel:
    """Las mismas reglas del nivel 10, con sustitutas, sin preferencias ni mejora."""
    reglas = NIVELES[10].reglas
    return Nivel(0, tipo.nombre, "Asignación de comparación (Sección 7.3)", reglas, disponible=True, sustitutas=True)


def _orden_aleatorio(instancia: Instancia, rng: random.Random) -> list[tuple[Estudiante, Solicitud]]:
    # Se parte de un orden fijo (por códigos) para que la semilla determine el resultado
    pares = [(e, s) for e in sorted(instancia.estudiantes.values(), key=lambda e: e.id) for s in e.solicitudes]
    rng.shuffle(pares)
    return pares


def _orden_de_llegada(instancia: Instancia) -> list[tuple[Estudiante, Solicitud]]:
    # El dict conserva el orden del archivo: ese es el orden de llegada.
    return [
        (e, s)
        for e in instancia.estudiantes.values()
        for s in sorted(e.solicitudes, key=lambda s: (-s.prioridad, s.materia))
    ]


def asignar_referencia(instancia: Instancia, tipo: Referencia, semilla: int = 0) -> Asignacion:
    nivel = _nivel(tipo)
    ctx = Contexto(instancia)
    horarios = {eid: Horario(instancia.estudiantes[eid], ctx) for eid in sorted(instancia.estudiantes)}

    if tipo is Referencia.ALEATORIA:
        rng = random.Random(semilla)
        orden = _orden_aleatorio(instancia, rng)

        def candidatas(secciones: list[Seccion]) -> list[Seccion]:
            return rng.sample(secciones, len(secciones))
    else:
        orden = _orden_de_llegada(instancia)

        def candidatas(secciones: list[Seccion]) -> list[Seccion]:
            return secciones  # ya vienen ordenadas por identificador

    for estudiante, solicitud in orden:
        _atender(horarios[estudiante.id], solicitud, nivel, instancia, candidatas)

    return Asignacion(nivel, ctx, horarios)


def _atender(
    horario: Horario,
    solicitud: Solicitud,
    nivel: Nivel,
    instancia: Instancia,
    candidatas: Callable[[list[Seccion]], list[Seccion]],
) -> None:
    """Principal primero; si no cabe, las sustitutas en el orden de la lista (R9)."""

    def inscribir(secciones: list[Seccion], posicion: int | None, rechazos: list[list[Causa]]) -> bool:
        for seccion in candidatas(secciones):
            causas = horario.puede_agregar(seccion, nivel.reglas)
            if not causas:
                horario.agregar(Inscripcion(solicitud, seccion, posicion))
                return True
            rechazos.append(causas)
        return False

    principales = instancia.secciones_de(solicitud.materia)
    rechazos: list[list[Causa]] = []
    if inscribir(principales, None, rechazos):
        return

    sustituta = None
    rechazos_sustitutas: list[list[Causa]] = []
    for posicion, codigo in enumerate(solicitud.sustitutas):
        secciones = instancia.secciones_de(codigo)
        if not secciones:
            rechazos_sustitutas.append([Causa.SIN_SECCIONES])
        elif inscribir(secciones, posicion, rechazos_sustitutas):
            sustituta = codigo
            break
    extra = () if sustituta else rechazos_sustitutas
    horario.avisar(diagnosticar(solicitud, principales, rechazos, extra, sustituta))


def ejecutar_referencia(instancia: Instancia, tipo: Referencia | str, semilla: int = 0, identificador: str | None = None) -> dict[str, Any]:
    """Como `ejecutar_corrida`, pero con una asignación de referencia. La salida tiene el mismo formato."""
    tipo = Referencia(tipo)
    inicio = time.perf_counter()
    asignacion = asignar_referencia(instancia, tipo, semilla)
    tiempo = time.perf_counter() - inicio
    salida = armar_salida(instancia, asignacion, tiempo, identificador, sufijo=tipo.value)
    salida["corrida"]["referencia"] = tipo.value
    if tipo is Referencia.ALEATORIA:
        salida["corrida"]["semilla_referencia"] = semilla
    return salida
