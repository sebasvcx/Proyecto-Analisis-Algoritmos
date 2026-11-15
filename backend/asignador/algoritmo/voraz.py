"""Asignación voraz por prioridad (niveles 1 y 2).

Se ordenan todas las solicitudes de todos los estudiantes de mayor a menor
prioridad. Ante empate se usa el código del estudiante y luego el de la
materia (desempate final por códigos de la Sección 5.4), de modo que el
resultado no depende del orden en que vengan los registros en los JSON.

Para cada solicitud se recorren sus secciones en orden de identificador y se
toma la primera que cumpla las reglas activas del nivel.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..dominio import Estudiante, Instancia, Seccion, Solicitud
from .causas import Causa
from .horario import Aviso, Contexto, Horario, Inscripcion
from .niveles import Nivel


@dataclass
class Asignacion:
    """Resultado crudo del algoritmo, antes de serializar."""

    nivel: Nivel
    contexto: Contexto
    horarios: dict[str, Horario]


def orden_de_atencion(instancia: Instancia) -> list[tuple[Estudiante, Solicitud]]:
    pares = [(e, s) for e in instancia.estudiantes.values() for s in e.solicitudes]
    return sorted(pares, key=lambda par: (-par[1].prioridad, par[0].id, par[1].materia))


def asignar_voraz(instancia: Instancia, nivel: Nivel) -> Asignacion:
    ctx = Contexto(instancia)
    horarios = {eid: Horario(instancia.estudiantes[eid], ctx) for eid in sorted(instancia.estudiantes)}

    for estudiante, solicitud in orden_de_atencion(instancia):
        horario = horarios[estudiante.id]
        candidatas = instancia.secciones_de(solicitud.materia)
        rechazos: list[list[Causa]] = []
        for seccion in candidatas:
            causas = horario.puede_agregar(seccion, nivel.reglas)
            if not causas:
                horario.agregar(Inscripcion(solicitud, seccion))
                break
            rechazos.append(causas)
        else:
            horario.avisar(diagnosticar(solicitud, candidatas, rechazos))

    return Asignacion(nivel, ctx, horarios)


def diagnosticar(solicitud: Solicitud, candidatas: list[Seccion], rechazos: list[list[Causa]]) -> Aviso:
    """Registra todas las causas y destaca la más frecuente (empate: menor número de regla)."""
    if not candidatas:
        return Aviso(solicitud, Causa.SIN_SECCIONES, (Causa.SIN_SECCIONES,))
    conteo = Counter(c for causas in rechazos for c in causas)
    principal = min(conteo, key=lambda c: (-conteo[c], c.regla))
    todas = tuple(sorted(conteo, key=lambda c: c.regla))
    return Aviso(solicitud, principal, todas)
