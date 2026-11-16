"""Solución exacta por búsqueda exhaustiva, solo para instancias pequeñas (Sección 7.1).

Recorre todas las asignaciones válidas con vuelta atrás: cada solicitud puede
quedar en una sección de su principal, en una de sus sustitutas o pendiente.
Devuelve la mejor según el orden completo de la Sección 5.4 (`objetivo.py`).
Como se revisan todas, la respuesta es óptima: no existe otra mejor.

Es independiente del algoritmo: comprueba R2–R8 con su propio código (R1 y R9
se cumplen por construcción: solo se ofrecen la principal o sus sustitutas, una
por solicitud).

Poda: si, aun inscribiendo como principal todas las solicitudes que faltan, el
vector (C5..C1) de una rama queda ESTRICTAMENTE peor que el de la mejor solución
ya encontrada, la rama no puede ganar y se descarta. Nunca se descarta una rama
que pueda empatar en C, porque podría ganar por J o por satisfacción.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import pairwise

from . import satisfaccion
from .dominio import Estudiante, Instancia, Seccion, Solicitud
from .objetivo import DECIMALES, PRIORIDADES, Puntaje, Registro, puntuar

SALIDA_ANTICIPADA = 10  # Sección 5.3 (se repite a propósito: no se importa del algoritmo)


class InstanciaDemasiadoGrande(RuntimeError):
    pass


@dataclass(frozen=True)
class Optimo:
    puntaje: Puntaje
    registros: tuple[Registro, ...]
    nodos: int  # nodos del árbol de búsqueda visitados
    soluciones: int  # asignaciones completas y válidas evaluadas


class _Busqueda:
    def __init__(self, instancia: Instancia, max_nodos: int, podar: bool):
        self.inst = instancia
        self.max_nodos = max_nodos
        self.podar = podar
        self.cfg = instancia.configuracion
        # Variables: una por solicitud, de mayor a menor prioridad (encuentra antes las buenas soluciones)
        self.variables: list[tuple[Estudiante, Solicitud]] = sorted(
            ((e, s) for e in instancia.estudiantes.values() for s in e.solicitudes),
            key=lambda par: (-par[1].prioridad, par[0].id, par[1].materia),
        )
        self.elegidas: dict[str, list[Seccion]] = {eid: [] for eid in instancia.estudiantes}
        self.inscritos: Counter[str] = Counter()
        self.registros: list[Registro] = []
        self.c = dict.fromkeys(PRIORIDADES, 0.0)
        self.restantes = Counter(s.prioridad for _, s in self.variables)  # solicitudes por decidir, por prioridad
        self.mejor: Puntaje | None = None
        self.mejores_registros: tuple[Registro, ...] = ()
        self.nodos = 0
        self.soluciones = 0

    # ------------------------------------------------------------------ búsqueda

    def buscar(self, k: int = 0) -> None:
        self.nodos += 1
        if self.nodos > self.max_nodos:
            raise InstanciaDemasiadoGrande(f"se superaron {self.max_nodos} nodos; use una instancia más pequeña")
        if self.podar and self._sin_esperanza():
            return
        if k == len(self.variables):
            self._evaluar()
            return
        estudiante, solicitud = self.variables[k]
        self.restantes[solicitud.prioridad] -= 1
        for seccion, posicion in self._opciones(solicitud):
            if seccion is not None and not self._valida(estudiante, seccion):
                continue
            self._asignar(estudiante, solicitud, seccion, posicion)
            self.buscar(k + 1)
            self._deshacer(estudiante, solicitud, seccion, posicion)
        self.restantes[solicitud.prioridad] += 1

    def _opciones(self, solicitud: Solicitud):
        for seccion in self.inst.secciones_de(solicitud.materia):
            yield seccion, None
        for posicion, codigo in enumerate(solicitud.sustitutas):
            for seccion in self.inst.secciones_de(codigo):
                yield seccion, posicion
        yield None, None

    def _asignar(self, est: Estudiante, sol: Solicitud, seccion: Seccion | None, posicion: int | None) -> None:
        self.registros.append(Registro(est.id, sol.materia, seccion.id if seccion else None, posicion))
        if seccion is not None:
            self.elegidas[est.id].append(seccion)
            self.inscritos[seccion.id] += 1
            self.c[sol.prioridad] += 1.0 if posicion is None else self.cfg.valor_sustituta

    def _deshacer(self, est: Estudiante, sol: Solicitud, seccion: Seccion | None, posicion: int | None) -> None:
        self.registros.pop()
        if seccion is not None:
            self.elegidas[est.id].pop()
            self.inscritos[seccion.id] -= 1
            self.c[sol.prioridad] -= 1.0 if posicion is None else self.cfg.valor_sustituta

    def _sin_esperanza(self) -> bool:
        if self.mejor is None:
            return False
        optimista = tuple(round(self.c[k] + self.restantes[k], DECIMALES) for k in PRIORIDADES)
        return optimista < self.mejor.c

    def _evaluar(self) -> None:
        self.soluciones += 1
        secciones_de = {eid: [s.id for s in secs] for eid, secs in self.elegidas.items()}
        total = sum(
            satisfaccion.calcular(self.inst, est, self.elegidas[eid], secciones_de).total
            for eid, est in self.inst.estudiantes.items()
        )
        puntaje = puntuar(self.inst, self.registros, total)
        if self.mejor is None or puntaje.mejor_que(self.mejor):
            self.mejor = puntaje
            self.mejores_registros = tuple(self.registros)

    # ------------------------------------------------------------------ reglas (código propio)

    def _valida(self, est: Estudiante, nueva: Seccion) -> bool:
        actuales = self.elegidas[est.id]
        pref = est.preferencias
        materias = self.inst.materias
        if any(s.materia == nueva.materia for s in actuales):  # R2
            return False
        if self.inscritos[nueva.id] >= nueva.cupo:  # R4
            return False
        if sum(materias[s.materia].creditos for s in actuales) + materias[nueva.materia].creditos > self.cfg.max_creditos:  # R5
            return False
        if nueva.profesor in pref.vetados:  # R7
            return False
        for ses in nueva.sesiones:
            f = ses.franja
            if any(_solapan(f, b) for b in pref.franjas_obligatorias):  # R6
                return False
            if any(_solapan(f, o.franja) for s in actuales for o in s.sesiones):  # R3
                return False
        return self._traslados_ok([*actuales, nueva])  # R8

    def _traslados_ok(self, secciones: list[Seccion]) -> bool:
        por_dia: dict[str, list] = {}
        for s in secciones:
            for ses in s.sesiones:
                por_dia.setdefault(ses.franja.dia, []).append(ses)
        for sesiones in por_dia.values():
            for a, b in pairwise(sorted(sesiones, key=lambda x: x.franja.inicio)):
                caminata = 0 if a.edificio == b.edificio else self.inst.traslados[(a.edificio, b.edificio)]
                if caminata > b.franja.inicio - a.franja.fin + SALIDA_ANTICIPADA:
                    return False
        return True


def _solapan(a, b) -> bool:
    return a.dia == b.dia and a.inicio < b.fin and b.inicio < a.fin


def resolver(instancia: Instancia, *, max_nodos: int = 2_000_000, podar: bool = True) -> Optimo:
    """Mejor asignación según la Sección 5.4, comprobada por búsqueda exhaustiva."""
    busqueda = _Busqueda(instancia, max_nodos, podar)
    busqueda.buscar()
    assert busqueda.mejor is not None  # siempre existe al menos la asignación vacía
    return Optimo(busqueda.mejor, busqueda.mejores_registros, busqueda.nodos, busqueda.soluciones)


def a_salida(instancia: Instancia, registros: tuple[Registro, ...]) -> list[dict]:
    """Registros en el formato de la salida, para pasarlos por el verificador y las métricas."""
    por_estudiante: dict[str, list[Registro]] = {eid: [] for eid in sorted(instancia.estudiantes)}
    for r in registros:
        por_estudiante[r.estudiante].append(r)
    salida = []
    for eid, regs in por_estudiante.items():
        est = instancia.estudiantes[eid]
        prioridad = {s.materia: s.prioridad for s in est.solicitudes}
        solicitudes, avisos = [], []
        for r in sorted(regs, key=lambda r: (-prioridad[r.materia], r.materia)):
            estado = "no_inscrita" if r.seccion is None else ("principal" if r.posicion_sustituta is None else "sustituida")
            inscrita = instancia.secciones[r.seccion].materia if r.seccion else None
            solicitudes.append({"materia": r.materia, "prioridad": prioridad[r.materia], "estado": estado, "seccion": r.seccion, "materia_inscrita": inscrita})
            if estado != "principal":
                avisos.append({"materia": r.materia, "causa": "", "sugerencia": ""})
        creditos = sum(instancia.materias[instancia.secciones[r.seccion].materia].creditos for r in regs if r.seccion)
        salida.append({"id": eid, "creditos": creditos, "solicitudes": solicitudes, "avisos": avisos})
    return salida
