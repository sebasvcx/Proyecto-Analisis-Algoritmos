"""Asignación voraz por prioridad (niveles 1 y 2).

Se ordenan todas las solicitudes de todos los estudiantes de mayor a menor
prioridad. Ante empate se usa el código del estudiante y luego el de la
materia (desempate final por códigos de la Sección 5.4), de modo que el
resultado no depende del orden en que vengan los registros en los JSON.

Para cada solicitud se recorren sus secciones en orden de identificador y se
toma la primera que cumpla las reglas activas del nivel. Desde N4, si ninguna
sección de la principal cabe, se prueban las sustitutas en el orden de la lista
(Sección 3.2); la sustituta hereda la prioridad de la solicitud.
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
        if _inscribir_primera(horario, solicitud, candidatas, None, nivel, rechazos):
            continue

        sustituta = None
        rechazos_sustitutas: list[list[Causa]] = []
        if nivel.sustitutas:
            for posicion, codigo in enumerate(solicitud.sustitutas):
                secciones = instancia.secciones_de(codigo)
                if not secciones:
                    rechazos_sustitutas.append([Causa.SIN_SECCIONES])
                elif _inscribir_primera(horario, solicitud, secciones, posicion, nivel, rechazos_sustitutas):
                    sustituta = codigo
                    break

        # Sustituida: el aviso explica por qué no entró la principal.
        # No inscrita: además se registran las causas de las sustitutas que tampoco cupieron.
        extra = () if sustituta else rechazos_sustitutas
        horario.avisar(diagnosticar(solicitud, candidatas, rechazos, extra, sustituta))

    return Asignacion(nivel, ctx, horarios)


def _inscribir_primera(
    horario: Horario,
    solicitud: Solicitud,
    secciones: list[Seccion],
    posicion_sustituta: int | None,
    nivel: Nivel,
    rechazos: list[list[Causa]],
) -> bool:
    """Inscribe la primera sección que cumpla las reglas del nivel; acumula las causas de las rechazadas."""
    for seccion in secciones:
        causas = horario.puede_agregar(seccion, nivel.reglas)
        if not causas:
            horario.agregar(Inscripcion(solicitud, seccion, posicion_sustituta))
            return True
        rechazos.append(causas)
    return False


def diagnosticar(
    solicitud: Solicitud,
    candidatas: list[Seccion],
    rechazos: list[list[Causa]],
    rechazos_sustitutas: list[list[Causa]] | tuple = (),
    sustituta: str | None = None,
) -> Aviso:
    """Destaca la causa más frecuente de la principal (empate: menor número de regla) y registra todas."""
    conteo = Counter(c for causas in rechazos for c in causas)
    principal = Causa.SIN_SECCIONES if not candidatas else min(conteo, key=lambda c: (-conteo[c], c.regla))
    todas = {principal, *conteo, *(c for causas in rechazos_sustitutas for c in causas)}
    return Aviso(solicitud, principal, tuple(sorted(todas, key=lambda c: c.regla)), sustituta)
