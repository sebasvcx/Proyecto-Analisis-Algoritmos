"""TAD Horario y estado compartido de una corrida.

`Horario` corresponde al TAD de la Figura 2: secciones inscritas, avisos y las
operaciones puedeAgregar / agregar / quitar. La ocupación de cupos se comparte
entre todos los horarios de la corrida a través de `Contexto`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterator

from ..dominio import Estudiante, Instancia, Seccion, Sesion, Solicitud
from .causas import Causa

if TYPE_CHECKING:
    from .reglas import Regla


@dataclass
class Contexto:
    """Datos de entrada más el estado mutable de la corrida (inscritos por sección)."""

    instancia: Instancia
    inscritos: Counter[str] = field(default_factory=Counter)

    def tiene_cupo(self, seccion: Seccion) -> bool:
        return self.inscritos[seccion.id] < seccion.cupo


@dataclass(frozen=True)
class Inscripcion:
    solicitud: Solicitud
    seccion: Seccion
    posicion_sustituta: int | None = None  # None = principal; 0, 1, ... = índice en la lista de sustitutas

    @property
    def materia(self) -> str:
        return self.seccion.materia

    @property
    def es_sustituta(self) -> bool:
        return self.posicion_sustituta is not None


@dataclass(frozen=True)
class Aviso:
    solicitud: Solicitud
    causa: Causa
    todas: tuple[Causa, ...]
    sustituta: str | None = None  # materia sustituta inscrita, si la hubo


class Horario:
    def __init__(self, estudiante: Estudiante, contexto: Contexto):
        self.estudiante = estudiante
        self._ctx = contexto
        self.inscripciones: list[Inscripcion] = []
        self.avisos: list[Aviso] = []

    # --- consultas -------------------------------------------------------

    def creditos(self) -> int:
        materias = self._ctx.instancia.materias
        return sum(materias[i.materia].creditos for i in self.inscripciones)

    def tiene_materia(self, codigo: str) -> bool:
        return any(i.materia == codigo for i in self.inscripciones)

    def sesiones(self) -> Iterator[Sesion]:
        for inscripcion in self.inscripciones:
            yield from inscripcion.seccion.sesiones

    def inscripcion_de(self, solicitud: Solicitud) -> Inscripcion | None:
        return next((i for i in self.inscripciones if i.solicitud is solicitud), None)

    # --- operaciones del TAD --------------------------------------------

    def puede_agregar(self, seccion: Seccion, reglas: tuple[Regla, ...]) -> list[Causa]:
        """Lista de causas que impiden inscribir la sección (vacía si cabe). No modifica nada."""
        return [r.causa for r in reglas if r.viola(self._ctx, self, seccion)]

    def agregar(self, inscripcion: Inscripcion) -> None:
        """Precondición: `puede_agregar` devolvió una lista vacía."""
        self.inscripciones.append(inscripcion)
        self._ctx.inscritos[inscripcion.seccion.id] += 1

    def quitar(self, inscripcion: Inscripcion) -> None:
        """Precondición: la inscripción existe en este horario."""
        self.inscripciones.remove(inscripcion)
        self._ctx.inscritos[inscripcion.seccion.id] -= 1

    def avisar(self, aviso: Aviso) -> None:
        self.avisos.append(aviso)
