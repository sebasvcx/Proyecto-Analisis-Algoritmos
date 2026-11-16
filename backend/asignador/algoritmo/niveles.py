"""Catálogo de niveles del algoritmo (Sección 6, Tabla 4).

Los niveles son acumulativos: el nivel k incluye las reglas de los anteriores.
Solo los niveles con `disponible=True` pueden ejecutarse.
"""

from __future__ import annotations

from dataclasses import dataclass

from .reglas import R2, R3, R4, R5, R6, R7, R8, Regla


@dataclass(frozen=True)
class Nivel:
    numero: int
    nombre: str
    descripcion: str
    reglas: tuple[Regla, ...] = ()
    disponible: bool = False
    sustitutas: bool = False  # desde N4: si la principal no cabe, se prueban sus sustitutas
    criterios: tuple[str, ...] = ()  # desde N5: criterios de satisfacción para elegir entre secciones válidas
    pesos_declarados: bool = False  # desde N8: usa la importancia declarada; antes, los pesos por defecto
    mejora: bool = False  # N10: desempate por semestre (si está activo) y mejora local tras el voraz

    @property
    def reglas_cubiertas(self) -> tuple[str, ...]:
        # R1 se cumple por construcción en todos los niveles; R9 también, porque una
        # sustituta solo se prueba cuando la principal ya no pudo inscribirse.
        return ("R1", *(r.id for r in self.reglas), *(("R9",) if self.sustitutas else ()))


_BASE = (R2, R3, R4)
_TODAS = (*_BASE, R5, R6, R7, R8)

_N5 = ("profesores",)
_N6 = (*_N5, "horario", "huecos")
_N7 = (*_N6, "cercania")
_N9 = (*_N7, "social")

NIVELES: dict[int, Nivel] = {
    n.numero: n
    for n in (
        Nivel(1, "Prioridad, choques y cupos", "Atiende de mayor a menor prioridad y toma la primera sección con cupo que no choque", _BASE, True),
        Nivel(2, "Créditos, franjas obligatorias y vetos", "Agrega tope de créditos, franjas no disponibles y profesores vetados", (*_BASE, R5, R6, R7), True),
        Nivel(3, "Traslado entre edificios", "Tiempo de caminata entre clases seguidas", _TODAS, True),
        Nivel(4, "Sustitutas y avisos", "Materias sustitutas y avisos con causa y sugerencia", _TODAS, True, sustitutas=True),
        Nivel(5, "Afinidad con profesores", "Elige la sección válida que más satisface al estudiante", _TODAS, True, True, _N5),
        Nivel(6, "Horario ideal y huecos", "Franjas preferidas, a evitar y libres deseables", _TODAS, True, True, _N6),
        Nivel(7, "Cercanía de salones", "Poca caminata entre clases consecutivas", _TODAS, True, True, _N7),
        Nivel(8, "Importancia personalizada", "Pesos alta, media o baja por criterio", _TODAS, True, True, _N7, pesos_declarados=True),
        Nivel(9, "Amigos y personas a evitar", "Compartir o no sección con otros estudiantes", _TODAS, True, True, _N9, pesos_declarados=True),
        Nivel(
            10,
            "Prioridad institucional y mejora global",
            "Desempate por semestre y cambios de sección que mejoren el resultado",
            _TODAS,
            True,
            True,
            _N9,
            pesos_declarados=True,
            mejora=True,
        ),
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
