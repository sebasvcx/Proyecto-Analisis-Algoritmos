"""Mejora local del nivel 10 (Sección 6).

Parte del resultado del voraz y examina cambios de sección. Un cambio solo se
acepta si cumple las reglas y mejora ESTRICTAMENTE el resultado según la
Sección 5.4, así que nunca se vuelve a una asignación peor o igual y el
proceso termina. Además se detiene al examinar `max_cambios` cambios.

Tipos de cambio, en cada pasada:
1. Solicitudes no atendidas por su principal (pendientes o sustituidas): se
   intenta inscribir la principal (o, si está pendiente, una sustituta). Si la
   sección solo está bloqueada por el cupo, se intenta mover a uno de sus
   ocupantes a otra sección de la misma materia (Tabla 4, ejemplo de N10).
2. Cualquier inscripción: se intenta pasarla a otra sección de la misma
   materia si eso sube la satisfacción.

Para comparar, basta recalcular la parte de Q que el cambio puede tocar: los
aportes (C, J y posiciones) de los estudiantes que cambian y la satisfacción de
ellos y de quienes tienen afinidad hacia ellos. El resto de Q queda igual, y
como el orden es componente a componente, comparar las partes equivale a
comparar los totales. El último desempate de la Sección 5.4 (lista de registros)
no se usa para aceptar cambios: solo se aceptan mejoras reales.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..dominio import Instancia, Seccion, Solicitud
from .causas import Causa
from .eleccion import DECIMALES, PRIORIDADES, Elector
from .horario import Horario, Inscripcion
from .voraz import Asignacion, diagnosticar, orden_de_atencion, usa_semestre


@dataclass(frozen=True)
class _Paso:
    agregar: bool  # True = agregar, False = quitar
    estudiante: str
    inscripcion: Inscripcion


class Mejora:
    def __init__(self, asignacion: Asignacion):
        self.asignacion = asignacion
        self.nivel = asignacion.nivel
        self.horarios = asignacion.horarios
        self.ctx = asignacion.contexto
        self.instancia: Instancia = asignacion.contexto.instancia
        self.cfg = self.instancia.configuracion
        self.semestre = usa_semestre(self.instancia, self.nivel)
        self.elector = Elector(self.instancia, self.nivel, self.horarios)
        self.examinados = 0
        self.aceptados = 0
        self.ocupantes: dict[str, set[str]] = defaultdict(set)
        for eid, h in self.horarios.items():
            for i in h.inscripciones:
                self.ocupantes[i.seccion.id].add(eid)

    @property
    def agotado(self) -> bool:
        return self.examinados >= self.cfg.max_cambios

    # ------------------------------------------------------------------ bucle

    def ejecutar(self) -> dict:
        orden = orden_de_atencion(self.instancia, self.semestre)
        pasadas = 0
        mejoro = True
        while mejoro and not self.agotado:
            pasadas += 1
            mejoro = False
            for estudiante, solicitud in orden:
                if self.agotado:
                    break
                mejoro |= self._mejorar_solicitud(estudiante.id, solicitud)
            for eid in sorted(self.horarios):
                for inscripcion in sorted(self.horarios[eid].inscripciones, key=lambda i: i.materia):
                    if self.agotado:
                        break
                    mejoro |= self._mejorar_seccion(eid, inscripcion)
        self.rediagnosticar()
        return {
            "cambios_examinados": self.examinados,
            "cambios_aceptados": self.aceptados,
            "pasadas": pasadas,
            "limite_alcanzado": self.agotado,
        }

    # ------------------------------------------------------------------ cambios

    def _mejorar_solicitud(self, eid: str, solicitud: Solicitud) -> bool:
        actual = self.horarios[eid].inscripcion_de(solicitud)
        if actual is not None and not actual.es_sustituta:
            return False
        objetivos: list[tuple[str, int | None]] = [(solicitud.materia, None)]
        if self.nivel.sustitutas:
            # Pendiente: cualquier sustituta. Sustituida: solo una que esté antes en la lista.
            limite = len(solicitud.sustitutas) if actual is None else actual.posicion_sustituta
            objetivos += [(m, p) for p, m in enumerate(solicitud.sustitutas[:limite])]
        for materia, posicion in objetivos:
            for seccion in self.instancia.secciones_de(materia):
                if self._intentar(eid, solicitud, actual, seccion, posicion):
                    return True
        return False

    def _intentar(self, eid: str, solicitud: Solicitud, actual: Inscripcion | None, seccion: Seccion, posicion: int | None) -> bool:
        horario = self.horarios[eid]
        nueva = Inscripcion(solicitud, seccion, posicion)
        sin_actual = [_Paso(False, eid, actual)] if actual is not None else []
        causas = self._causas_sin(horario, actual, seccion)
        if not causas:
            return self._probar([*sin_actual, _Paso(True, eid, nueva)])
        if causas != [Causa.CUPO_LLENO]:
            return False
        # Liberar el cupo: mover a un ocupante a otra sección de la misma materia que tenga cupo.
        # Si ninguna tiene, no hay a dónde mover a nadie (filtro barato antes de revisar cada ocupante).
        alternativas = [a for a in self.instancia.secciones_de(seccion.materia) if a.id != seccion.id and self.ctx.tiene_cupo(a)]
        if not alternativas:
            return False
        for otro in sorted(self.ocupantes[seccion.id]):
            suya = next(i for i in self.horarios[otro].inscripciones if i.seccion.id == seccion.id)
            for alternativa in alternativas:
                if self._causas_sin(self.horarios[otro], suya, alternativa):
                    continue
                pasos = [
                    _Paso(False, otro, suya),
                    _Paso(True, otro, Inscripcion(suya.solicitud, alternativa, suya.posicion_sustituta)),
                    *sin_actual,
                    _Paso(True, eid, nueva),
                ]
                if self._probar(pasos):
                    return True
                if self.agotado:
                    return False
        return False

    def _mejorar_seccion(self, eid: str, inscripcion: Inscripcion) -> bool:
        horario = self.horarios[eid]
        if inscripcion not in horario.inscripciones:  # ya cambió en esta pasada
            return False
        for alternativa in self.instancia.secciones_de(inscripcion.materia):
            if alternativa.id == inscripcion.seccion.id or not self.ctx.tiene_cupo(alternativa):
                continue
            if self._causas_sin(horario, inscripcion, alternativa):
                continue
            nueva = Inscripcion(inscripcion.solicitud, alternativa, inscripcion.posicion_sustituta)
            if self._probar([_Paso(False, eid, inscripcion), _Paso(True, eid, nueva)]):
                return True
            if self.agotado:
                return False
        return False

    def _causas_sin(self, horario: Horario, quitada: Inscripcion | None, seccion: Seccion) -> list[Causa]:
        """Causas que impedirían inscribir `seccion` si antes se quitara `quitada`."""
        if quitada is not None:
            self._quitar(horario.estudiante.id, quitada)
        try:
            return horario.puede_agregar(seccion, self.nivel.reglas)
        finally:
            if quitada is not None:
                self._agregar(horario.estudiante.id, quitada)

    # ------------------------------------------------------------------ evaluación

    def _probar(self, pasos: list[_Paso]) -> bool:
        """Aplica los pasos; los conserva solo si Q mejora estrictamente."""
        if self.agotado:
            return False
        self.examinados += 1
        cambiados = {p.estudiante for p in pasos}
        antes = self._parte_de_q(cambiados)
        hechos: list[_Paso] = []
        valido = True
        for paso in pasos:
            if paso.agregar and self.horarios[paso.estudiante].puede_agregar(paso.inscripcion.seccion, self.nivel.reglas):
                valido = False
                break
            self._aplicar(paso)
            hechos.append(paso)
        if valido and self._parte_de_q(cambiados) < antes:
            self.aceptados += 1
            return True
        for paso in reversed(hechos):
            self._aplicar(_Paso(not paso.agregar, paso.estudiante, paso.inscripcion))
        return False

    def _parte_de_q(self, cambiados: set[str]) -> tuple:
        """La parte de Q que pueden cambiar estos estudiantes, como clave en la que MENOR es MEJOR."""
        c = dict.fromkeys(PRIORIDADES, 0.0)
        j = dict.fromkeys(PRIORIDADES, 0.0)
        posiciones = 0
        for eid in cambiados:
            horario = self.horarios[eid]
            for sol in horario.estudiante.solicitudes:
                i = horario.inscripcion_de(sol)
                if i is None:
                    continue
                aporte = 1.0 if not i.es_sustituta else self.cfg.valor_sustituta
                c[sol.prioridad] += aporte
                j[sol.prioridad] += aporte * horario.estudiante.semestre
                if i.es_sustituta:
                    posiciones += i.posicion_sustituta + 1
        afectados = set(cambiados)
        for eid in cambiados:
            afectados.update(self.elector.interesados.get(eid, ()))
        satisfaccion = sum(self.elector.satisfaccion(eid) for eid in sorted(afectados))
        return (
            tuple(-round(c[k], DECIMALES) for k in PRIORIDADES),
            tuple(-round(j[k], DECIMALES) for k in PRIORIDADES) if self.semestre else (),
            -round(satisfaccion, DECIMALES),
            posiciones,
        )

    def _aplicar(self, paso: _Paso) -> None:
        (self._agregar if paso.agregar else self._quitar)(paso.estudiante, paso.inscripcion)

    def _agregar(self, eid: str, inscripcion: Inscripcion) -> None:
        self.horarios[eid].agregar(inscripcion)
        self.ocupantes[inscripcion.seccion.id].add(eid)

    def _quitar(self, eid: str, inscripcion: Inscripcion) -> None:
        self.horarios[eid].quitar(inscripcion)
        self.ocupantes[inscripcion.seccion.id].discard(eid)

    # ------------------------------------------------------------------ avisos

    def rediagnosticar(self) -> None:
        """Rehace los avisos con el horario final: explican lo ocurrido en el resultado entregado."""
        for eid in sorted(self.horarios):
            horario = self.horarios[eid]
            horario.avisos = []
            for sol in sorted(horario.estudiante.solicitudes, key=lambda s: (-s.prioridad, s.materia)):
                actual = horario.inscripcion_de(sol)
                if actual is not None and not actual.es_sustituta:
                    continue
                candidatas = self.instancia.secciones_de(sol.materia)
                if actual is not None:
                    self._quitar(eid, actual)
                try:
                    rechazos = [self._causas_finales(horario, sol, s) for s in candidatas]
                finally:
                    if actual is not None:
                        self._agregar(eid, actual)
                extra: list[list[Causa]] = []
                if actual is None and self.nivel.sustitutas:
                    for codigo in sol.sustitutas:
                        secciones = self.instancia.secciones_de(codigo)
                        extra += [self._causas_finales(horario, sol, s) for s in secciones] or [[Causa.SIN_SECCIONES]]
                sustituta = actual.materia if actual is not None else None
                horario.avisar(diagnosticar(sol, candidatas, rechazos, extra, sustituta))

    def _causas_finales(self, horario: Horario, solicitud: Solicitud, seccion: Seccion) -> list[Causa]:
        """Causas para el aviso; un cupo lleno se informa como cedido si lo tomó alguien de mayor semestre."""
        causas = horario.puede_agregar(seccion, self.nivel.reglas)
        if Causa.CUPO_LLENO in causas and self._cedido(horario, solicitud, seccion):
            causas = [Causa.CEDIDA_POR_PRIORIDAD if c is Causa.CUPO_LLENO else c for c in causas]
        return causas

    def _cedido(self, horario: Horario, solicitud: Solicitud, seccion: Seccion) -> bool:
        """Con desempate por semestre: algún ocupante pidió con la misma prioridad y es de mayor semestre."""
        if not self.semestre:
            return False
        for otro in self.ocupantes[seccion.id]:
            suya = next(i for i in self.horarios[otro].inscripciones if i.seccion.id == seccion.id)
            if suya.solicitud.prioridad == solicitud.prioridad and self.horarios[otro].estudiante.semestre > horario.estudiante.semestre:
                return True
        return False


def mejorar(asignacion: Asignacion) -> dict:
    return Mejora(asignacion).ejecutar()
