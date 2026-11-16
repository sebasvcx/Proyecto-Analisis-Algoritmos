"""Elección entre secciones válidas (niveles 5 a 9).

Hasta N4 se toma la primera sección válida. Desde N5, entre las válidas se elige
la mejor según este orden, que sigue la Sección 5.4 (una comodidad no compensa
perder materias):

1. Menor pérdida en las solicitudes pendientes del mismo estudiante, comparada
   de prioridad 5 a 1: una solicitud que se queda sin ninguna sección posible
   pierde 1; una que solo podría entrar por sustituta pierde 1 − valor_sustituta.
2. Mayor satisfacción con los criterios activos del nivel. Con compañeros (N9)
   se suma también la satisfacción de quienes tienen afinidad hacia el estudiante.
3. Menor identificador de sección (las candidatas llegan ordenadas).

Para medir cada candidata se inscribe de forma provisional y se quita después
(operaciones agregar/quitar del TAD Horario).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .. import satisfaccion
from ..dominio import Instancia, Seccion, Solicitud
from .horario import Horario, Inscripcion
from .niveles import Nivel

PRIORIDADES = (5, 4, 3, 2, 1)
DECIMALES = 9  # para que errores de redondeo no rompan los empates por identificador


class _SeccionesDe:
    """Vista de solo lectura: estudiante → identificadores de sus secciones inscritas ahora."""

    def __init__(self, horarios: dict[str, Horario]):
        self._horarios = horarios

    def get(self, estudiante: str, defecto: Iterable[str] = ()) -> Iterable[str]:
        horario = self._horarios.get(estudiante)
        return defecto if horario is None else [i.seccion.id for i in horario.inscripciones]


class Elector:
    def __init__(self, instancia: Instancia, nivel: Nivel, horarios: dict[str, Horario]):
        self.instancia = instancia
        self.nivel = nivel
        self.horarios = horarios
        self.secciones_de = _SeccionesDe(horarios)
        self.interesados: dict[str, list[str]] = {}
        if "social" in nivel.criterios:
            for est in sorted(instancia.estudiantes.values(), key=lambda e: e.id):
                for otro, afinidad in est.preferencias.social.items():
                    if afinidad != 0 and otro in horarios:
                        self.interesados.setdefault(otro, []).append(est.id)

    def mejor(
        self,
        horario: Horario,
        solicitud: Solicitud,
        posicion_sustituta: int | None,
        validas: Sequence[Seccion],
        pendientes: Iterable[Solicitud],
    ) -> Seccion:
        """La mejor sección entre las válidas; ante empate total, la primera (menor identificador)."""
        pendientes = list(pendientes)
        return max(validas, key=lambda s: self._puntaje(horario, Inscripcion(solicitud, s, posicion_sustituta), pendientes))

    # ------------------------------------------------------------------

    def _puntaje(self, horario: Horario, inscripcion: Inscripcion, pendientes: list[Solicitud]) -> tuple:
        horario.agregar(inscripcion)
        try:
            perdidas = self._perdidas(horario, pendientes)
            eid = horario.estudiante.id
            total = self.satisfaccion(eid) + sum(self.satisfaccion(o) for o in self.interesados.get(eid, ()))
        finally:
            horario.quitar(inscripcion)
        # max() busca el mayor: las pérdidas se niegan para que gane la menor
        return tuple(-p for p in perdidas), round(total, DECIMALES)

    def _perdidas(self, horario: Horario, pendientes: list[Solicitud]) -> tuple[float, ...]:
        perdida = dict.fromkeys(PRIORIDADES, 0.0)
        valor_sustituta = self.instancia.configuracion.valor_sustituta
        for sol in pendientes:
            if self._cabe(horario, sol.materia):
                continue
            if self.nivel.sustitutas and any(self._cabe(horario, m) for m in sol.sustitutas):
                perdida[sol.prioridad] += 1 - valor_sustituta
            else:
                perdida[sol.prioridad] += 1
        return tuple(round(perdida[k], DECIMALES) for k in PRIORIDADES)

    def _cabe(self, horario: Horario, materia: str) -> bool:
        return any(not horario.puede_agregar(s, self.nivel.reglas) for s in self.instancia.secciones_de(materia))

    def satisfaccion(self, estudiante: str) -> float:
        horario = self.horarios[estudiante]
        return satisfaccion.calcular(
            self.instancia,
            horario.estudiante,
            [i.seccion for i in horario.inscripciones],
            self.secciones_de,
            criterios=self.nivel.criterios,
            pesos_declarados=self.nivel.pesos_declarados,
        ).total
