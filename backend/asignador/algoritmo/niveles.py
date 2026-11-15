"""Catálogo de niveles del algoritmo (Sección 6, Tabla 4).

Los niveles son acumulativos: el nivel k incluye las reglas de los anteriores.
Solo los niveles con `disponible=True` pueden ejecutarse.
"""

from __future__ import annotations

from dataclasses import dataclass

from .reglas import R2, R3, R4, R5, R6, R7, Regla


@dataclass(frozen=True)
class Nivel:
    numero: int
    nombre: str
    descripcion: str
    reglas: tuple[Regla, ...] = ()
    disponible: bool = False

    @property
    def reglas_cubiertas(self) -> tuple[str, ...]:
        # R1 se cumple por construcción en todos los niveles
        return ("R1", *(r.id for r in self.reglas))


_BASE = (R2, R3, R4)

NIVELES: dict[int, Nivel] = {
    n.numero: n
    for n in (
        Nivel(1, "Prioridad, choques y cupos", "Atiende de mayor a menor prioridad y toma la primera sección con cupo que no choque", _BASE, True),
        Nivel(2, "Créditos, franjas obligatorias y vetos", "Agrega tope de créditos, franjas no disponibles y profesores vetados", (*_BASE, R5, R6, R7), True),
        Nivel(3, "Traslado entre edificios", "Tiempo de caminata entre clases seguidas"),
        Nivel(4, "Sustitutas y avisos", "Materias sustitutas y avisos con causa y sugerencia"),
        Nivel(5, "Afinidad con profesores", "Elige la sección válida que más satisface al estudiante"),
        Nivel(6, "Horario ideal y huecos", "Franjas preferidas, a evitar y libres deseables"),
        Nivel(7, "Cercanía de salones", "Poca caminata entre clases consecutivas"),
        Nivel(8, "Importancia personalizada", "Pesos alta, media o baja por criterio"),
        Nivel(9, "Amigos y personas a evitar", "Compartir o no sección con otros estudiantes"),
        Nivel(10, "Prioridad institucional y mejora global", "Desempate por semestre y cambios de sección que mejoren el resultado"),
    )
}


class NivelNoDisponible(ValueError):
    pass


def obtener_nivel(numero: int) -> Nivel:
    nivel = NIVELES.get(numero)
    if nivel is None:
        raise NivelNoDisponible(f"el nivel {numero} no existe (1 a {len(NIVELES)})")
    if not nivel.disponible:
        raise NivelNoDisponible(f"el nivel {numero} ({nivel.nombre}) aún no está implementado")
    return nivel
