"""Reglas obligatorias (Tabla 1) como objetos intercambiables.

Cada nivel activa un subconjunto de reglas. R1 (solo lo solicitado) se cumple
por construcción: el algoritmo solo considera secciones de materias pedidas.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain, pairwise
from typing import Callable

from ..dominio import Seccion
from ..dominio.tiempo import SALIDA_ANTICIPADA
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


def _traslado_imposible(ctx: Contexto, h: Horario, s: Seccion) -> bool:
    """R8: entre dos sesiones consecutivas del mismo día, caminata ≤ minutos libres + salida anticipada.

    Se revisan los días que toca la sección nueva, con sus sesiones mezcladas con las
    del horario. Los pares que ya eran consecutivos antes eran válidos, así que basta
    con que algún par del día mezclado falle. Los pares que se solapan son choques (R3),
    no traslados, y se ignoran aquí para no duplicar la causa.
    """
    inst = ctx.instancia
    for dia in {ses.franja.dia for ses in s.sesiones}:
        del_dia = sorted(
            (ses for ses in chain(h.sesiones(), s.sesiones) if ses.franja.dia == dia),
            key=lambda ses: ses.franja.inicio,
        )
        for antes, despues in pairwise(del_dia):
            libres = despues.franja.inicio - antes.franja.fin
            if libres >= 0 and inst.caminata(antes.edificio, despues.edificio) > libres + SALIDA_ANTICIPADA:
                return True
    return False


R2 = Regla("R2", "Una sección por materia", Causa.MATERIA_YA_INSCRITA, _ya_inscrita)
R3 = Regla("R3", "Sin choques", Causa.CHOQUE_HORARIO, _choca)
R4 = Regla("R4", "Cupos", Causa.CUPO_LLENO, _sin_cupo)
R5 = Regla("R5", "Tope de créditos", Causa.TOPE_CREDITOS, _supera_creditos)
R6 = Regla("R6", "Franjas obligatorias", Causa.FRANJA_OBLIGATORIA, _en_franja_obligatoria)
R7 = Regla("R7", "Profesores vetados", Causa.PROFESOR_VETADO, _profesor_vetado)
R8 = Regla("R8", "Traslado posible", Causa.TRASLADO_IMPOSIBLE, _traslado_imposible)
