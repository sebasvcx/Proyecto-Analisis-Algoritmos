"""Cómo comparar resultados válidos (Sección 5.4 del documento de diseño).

Entre dos resultados se aplica, en este orden:

1. (C5, C4, C3, C2, C1): aportes por prioridad (1 por principal, valor_sustituta por
   sustituta, 0 por pendiente). Decide la primera posición distinta.
2. (J5, ..., J1), solo si `desempate_semestre` está activo: los mismos aportes
   multiplicados por el semestre del estudiante.
3. Mayor suma de satisfacción de los estudiantes.
4. Menor suma de posiciones en las listas de sustitutas (la primera sustituta cuenta 1).
5. La lista de registros (estudiante, solicitud, sección) ordenada por códigos que
   vaya primero alfabéticamente.

El puntaje se calcula desde una lista de `Registro`, que puede venir de la salida
serializada (métricas) o del estado interno de una corrida (mejora de N10, solver exacto).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .dominio import Instancia

PRIORIDADES = (5, 4, 3, 2, 1)
DECIMALES = 9  # evita que errores de redondeo en sumas de 0,8 decidan una comparación


@dataclass(frozen=True)
class Registro:
    """La respuesta a una solicitud."""

    estudiante: str
    materia: str  # materia solicitada (la principal)
    seccion: str | None  # None = pendiente
    posicion_sustituta: int | None = None  # None = principal; 0, 1, ... = índice en la lista de sustitutas


@dataclass(frozen=True)
class Puntaje:
    c: tuple[float, ...]  # C5..C1
    j: tuple[float, ...] | None  # J5..J1, o None si el desempate por semestre está desactivado
    satisfaccion: float
    posiciones_sustitutas: int
    registros: tuple[tuple[str, str, str], ...]  # (estudiante, solicitud, sección) inscritos, ordenados

    def clave(self) -> tuple:
        """Tupla en la que MENOR significa MEJOR: lo que se maximiza va negado."""
        return (
            tuple(-x for x in self.c),
            tuple(-x for x in self.j or ()),
            -self.satisfaccion,
            self.posiciones_sustitutas,
            self.registros,
        )

    def mejor_que(self, otro: Puntaje) -> bool:
        return self.clave() < otro.clave()

    def como_dict(self) -> dict:
        return {
            "c": list(self.c),
            "j": list(self.j) if self.j is not None else None,
            "satisfaccion": self.satisfaccion,
            "posiciones_sustitutas": self.posiciones_sustitutas,
        }


CRITERIOS_DE_ORDEN = ("C", "J", "satisfaccion", "posiciones_sustitutas", "registros")


def puntuar(instancia: Instancia, registros: Iterable[Registro], satisfaccion_total: float) -> Puntaje:
    cfg = instancia.configuracion
    c = dict.fromkeys(PRIORIDADES, 0.0)
    j = dict.fromkeys(PRIORIDADES, 0.0)
    posiciones = 0
    inscritos = []
    for r in registros:
        estudiante = instancia.estudiantes[r.estudiante]
        prioridad = next(s.prioridad for s in estudiante.solicitudes if s.materia == r.materia)
        if r.seccion is None:
            continue
        aporte = 1.0 if r.posicion_sustituta is None else cfg.valor_sustituta
        c[prioridad] += aporte
        j[prioridad] += aporte * estudiante.semestre
        if r.posicion_sustituta is not None:
            posiciones += r.posicion_sustituta + 1
        inscritos.append((r.estudiante, r.materia, r.seccion))
    return Puntaje(
        c=tuple(round(c[k], DECIMALES) for k in PRIORIDADES),
        j=tuple(round(j[k], DECIMALES) for k in PRIORIDADES) if cfg.desempate_semestre else None,
        satisfaccion=round(satisfaccion_total, DECIMALES),
        posiciones_sustitutas=posiciones,
        registros=tuple(sorted(inscritos)),
    )


def comparar(a: Puntaje, b: Puntaje) -> int:
    """1 si A es mejor, -1 si B es mejor, 0 si son idénticos."""
    ka, kb = a.clave(), b.clave()
    return (ka < kb) - (ka > kb)


def criterio_decisivo(a: Puntaje, b: Puntaje) -> str | None:
    """Primer criterio de la Sección 5.4 en que difieren A y B (None si son idénticos)."""
    for nombre, x, y in zip(CRITERIOS_DE_ORDEN, a.clave(), b.clave()):
        if x != y:
            return nombre
    return None
