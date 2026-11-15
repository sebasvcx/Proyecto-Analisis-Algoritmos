"""Reglas obligatorias (Tabla 1) como objetos intercambiables.

Cada nivel activa un subconjunto de reglas. R1 (solo lo solicitado) se cumple
por construcción: el algoritmo solo considera secciones de materias pedidas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..dominio import Seccion
from .causas import Causa
from .horario import Contexto, Horario

Comprobacion = Callable[[Contexto, Horario, Seccion], bool]


@dataclass(frozen=True)
class Regla:
    id: str
    nombre: str
    causa: Causa
    viola: Comprobacion

    def __repr__(self) -> str:
        return self.id


def _ya_inscrita(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    return h.tiene_materia(s.materia)


def _choca(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    return any(i.seccion.choca_con(s) for i in h.inscripciones)


def _sin_cupo(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    return not ctx.tiene_cupo(s)


def _supera_creditos(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    inst = ctx.instancia
    return h.creditos() + inst.materias[s.materia].creditos > inst.configuracion.max_creditos


def _en_franja_obligatoria(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    bloqueadas = h.estudiante.preferencias.franjas_obligatorias
    return any(ses.franja.se_cruza_con(f) for ses in s.sesiones for f in bloqueadas)


def _profesor_vetado(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    return s.profesor in h.estudiante.preferencias.vetados


R2 = Regla("R2", "Una sección por materia", Causa.MATERIA_YA_INSCRITA, _ya_inscrita)
R3 = Regla("R3", "Sin choques", Causa.CHOQUE_HORARIO, _choca)
R4 = Regla("R4", "Cupos", Causa.CUPO_LLENO, _sin_cupo)
R5 = Regla("R5", "Tope de créditos", Causa.TOPE_CREDITOS, _supera_creditos)
R6 = Regla("R6", "Franjas obligatorias", Causa.FRANJA_OBLIGATORIA, _en_franja_obligatoria)
R7 = Regla("R7", "Profesores vetados", Causa.PROFESOR_VETADO, _profesor_vetado)
