"""Asignación voraz por prioridad (niveles 1 a 9).

Se ordenan todas las solicitudes de todos los estudiantes de mayor a menor
prioridad. Ante empate se usa el código del estudiante y luego el de la
materia (desempate final por códigos de la Sección 5.4), de modo que el
resultado no depende del orden en que vengan los registros en los JSON.

Para cada solicitud se recorren sus secciones en orden de identificador.
Hasta N4 se toma la primera que cumpla las reglas activas del nivel; desde N5,
la mejor de las válidas según `eleccion.Elector`. Desde N4, si ninguna
sección de la principal cabe, se prueban las sustitutas en el orden de la lista
(Sección 3.2); la sustituta hereda la prioridad de la solicitud.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from ..dominio import Estudiante, Instancia, Seccion, Solicitud
from .causas import Causa
from .eleccion import Elector
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
    orden = orden_de_atencion(instancia)
    elector = Elector(instancia, nivel, horarios) if nivel.criterios else None

    # Solicitudes que a cada estudiante le quedan por atender (en el mismo orden global)
    pendientes: dict[str, deque[Solicitud]] = {eid: deque() for eid in horarios}
    for estudiante, solicitud in orden:
        pendientes[estudiante.id].append(solicitud)

    for estudiante, solicitud in orden:
        horario = horarios[estudiante.id]
        pendientes[estudiante.id].popleft()
        inscribir = _Inscriptor(horario, solicitud, nivel, elector, pendientes[estudiante.id])

        candidatas = instancia.secciones_de(solicitud.materia)
        rechazos: list[list[Causa]] = []
        if inscribir(candidatas, None, rechazos):
            continue

        sustituta = None
        rechazos_sustitutas: list[list[Causa]] = []
        if nivel.sustitutas:
            for posicion, codigo in enumerate(solicitud.sustitutas):
                secciones = instancia.secciones_de(codigo)
                if not secciones:
                    rechazos_sustitutas.append([Causa.SIN_SECCIONES])
                elif inscribir(secciones, posicion, rechazos_sustitutas):
                    sustituta = codigo
                    break

        # Sustituida: el aviso explica por qué no entró la principal.
        # No inscrita: además se registran las causas de las sustitutas que tampoco cupieron.
        extra = () if sustituta else rechazos_sustitutas
        horario.avisar(diagnosticar(solicitud, candidatas, rechazos, extra, sustituta))

    return Asignacion(nivel, ctx, horarios)


@dataclass
class _Inscriptor:
    """Inscribe una sección válida para la solicitud en turno."""

    horario: Horario
    solicitud: Solicitud
    nivel: Nivel
    elector: Elector | None
    pendientes: deque[Solicitud]

    def __call__(self, secciones: list[Seccion], posicion_sustituta: int | None, rechazos: list[list[Causa]]) -> bool:
        """Hasta N4, la primera válida; desde N5, la mejor de las válidas. Acumula las causas de las rechazadas."""
        validas: list[Seccion] = []
        for seccion in secciones:
            causas = self.horario.puede_agregar(seccion, self.nivel.reglas)
            if causas:
                rechazos.append(causas)
                continue
            validas.append(seccion)
            if self.elector is None:
                break
        if not validas:
            return False
        elegida = validas[0]
        if self.elector is not None and len(validas) > 1:
            elegida = self.elector.mejor(self.horario, self.solicitud, posicion_sustituta, validas, self.pendientes)
        self.horario.agregar(Inscripcion(self.solicitud, elegida, posicion_sustituta))
        return True


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
