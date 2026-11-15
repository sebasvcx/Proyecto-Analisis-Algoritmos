"""Precondiciones entre entidades (referencias, cruces de profesores y salones).

Errores: impiden ejecutar. Advertencias: situaciones válidas que el usuario
debería conocer (por ejemplo, más demanda que cupos).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations

from ..dominio import Instancia
from ..dominio.tiempo import DIAS, HORA_APERTURA, HORA_CIERRE
from .problemas import Reporte


def validar_coherencia(inst: Instancia, reporte: Reporte) -> None:
    _validar_secciones(inst, reporte)
    _validar_ocupacion_simultanea(inst, reporte)
    _validar_traslados(inst, reporte)
    _validar_estudiantes(inst, reporte)
    _advertir_demanda(inst, reporte)


def _validar_secciones(inst: Instancia, reporte: Reporte) -> None:
    for s in inst.secciones.values():
        if s.materia not in inst.materias:
            reporte.error("secciones.json", s.id, "materia", f"la materia '{s.materia}' no existe")
        if s.profesor not in inst.profesores:
            reporte.error("secciones.json", s.id, "profesor", f"el profesor '{s.profesor}' no existe")
        for i, sesion in enumerate(s.sesiones):
            if sesion.edificio not in inst.edificios:
                reporte.error("secciones.json", s.id, f"sesiones[{i}].edificio", f"el edificio '{sesion.edificio}' no existe")
        for a, b in combinations(s.sesiones, 2):
            if a.franja.se_cruza_con(b.franja):
                reporte.error("secciones.json", s.id, "sesiones", f"las sesiones {a.franja} y {b.franja} se cruzan")


def _validar_ocupacion_simultanea(inst: Instancia, reporte: Reporte) -> None:
    """Ningún profesor ni salón puede estar en dos sesiones a la vez."""
    por_profesor = defaultdict(list)
    por_salon = defaultdict(list)
    for s in inst.secciones.values():
        for sesion in s.sesiones:
            por_profesor[s.profesor].append((s.id, sesion.franja))
            por_salon[(sesion.edificio, sesion.salon)].append((s.id, sesion.franja))

    def revisar(grupos, etiqueta):
        for clave, ocupaciones in grupos.items():
            ocupaciones.sort(key=lambda o: o[1])
            for (id_a, fa), (id_b, fb) in zip(ocupaciones, ocupaciones[1:]):
                if id_a != id_b and fa.se_cruza_con(fb):
                    nombre = clave if isinstance(clave, str) else clave[1]
                    reporte.error("secciones.json", id_b, etiqueta, f"{etiqueta} '{nombre}' ya tiene {id_a} en {fa}")

    revisar(por_profesor, "profesor")
    revisar(por_salon, "salon")


def _validar_traslados(inst: Instancia, reporte: Reporte) -> None:
    for origen, destino in inst.traslados:
        for e in (origen, destino):
            if e not in inst.edificios:
                reporte.error("traslados.json", f"{origen}→{destino}", "edificio", f"el edificio '{e}' no existe")
        if origen == destino and inst.traslados[(origen, destino)] != 0:
            reporte.error("traslados.json", f"{origen}→{destino}", "minutos", "dentro del mismo edificio el tiempo es 0")
    for a, b in combinations(sorted(inst.edificios), 2):
        if (a, b) not in inst.traslados:
            reporte.error("traslados.json", f"{a}→{b}", "", "falta el tiempo de caminata entre estos edificios")


def _validar_estudiantes(inst: Instancia, reporte: Reporte) -> None:
    archivo = "estudiantes.json"
    for e in inst.estudiantes.values():
        principales = [s.materia for s in e.solicitudes]
        for codigo, veces in Counter(principales).items():
            if veces > 1:
                reporte.error(archivo, e.id, "materias", f"la materia '{codigo}' se pide {veces} veces")
        for i, sol in enumerate(e.solicitudes):
            campo = f"materias[{i}]"
            if sol.materia not in inst.materias:
                reporte.error(archivo, e.id, f"{campo}.codigo", f"la materia '{sol.materia}' no existe")
            if len(set(sol.sustitutas)) != len(sol.sustitutas):
                reporte.error(archivo, e.id, f"{campo}.sustitutas", "hay sustitutas repetidas")
            for sust in sol.sustitutas:
                if sust not in inst.materias:
                    reporte.error(archivo, e.id, f"{campo}.sustitutas", f"la materia '{sust}' no existe")
                if sust in principales:
                    reporte.error(archivo, e.id, f"{campo}.sustitutas", f"'{sust}' ya es una materia pedida por el estudiante")

        pref = e.preferencias
        for pid in set(pref.afinidad_profesores) | pref.vetados:
            if pid not in inst.profesores:
                reporte.error(archivo, e.id, "profesores", f"el profesor '{pid}' no existe")
        for otro in pref.social:
            if otro == e.id:
                reporte.error(archivo, e.id, "social", "no se admiten preferencias sociales hacia uno mismo")
            elif otro not in inst.estudiantes:
                reporte.error(archivo, e.id, "social", f"el estudiante '{otro}' no existe")

        if _bloquea_toda_la_semana(pref.franjas_obligatorias):
            reporte.advertencia(archivo, e.id, "franjas_libres", "las franjas obligatorias cubren toda la semana")
        if e.solicitudes and all(s.materia in inst.materias for s in e.solicitudes):
            pedidos = e.creditos_solicitados(inst.materias)
            if pedidos > inst.configuracion.max_creditos:
                reporte.advertencia(archivo, e.id, "materias", f"pide {pedidos} créditos y el tope es {inst.configuracion.max_creditos}")


def _bloquea_toda_la_semana(franjas) -> bool:
    if not franjas:
        return False
    cubiertos = {(f.dia, m) for f in franjas for m in range(f.inicio, f.fin, 60)}
    return all((d, m) in cubiertos for d in DIAS for m in range(HORA_APERTURA, HORA_CIERRE, 60))


def _advertir_demanda(inst: Instancia, reporte: Reporte) -> None:
    demanda = Counter(s.materia for e in inst.estudiantes.values() for s in e.solicitudes)
    for codigo, pedidos in sorted(demanda.items()):
        if codigo not in inst.materias:
            continue
        secciones = inst.secciones_de(codigo)
        if not secciones:
            reporte.advertencia("secciones.json", codigo, "", f"{pedidos} estudiante(s) piden {codigo} y no tiene secciones")
            continue
        cupos = sum(s.cupo for s in secciones)
        if pedidos > cupos:
            reporte.advertencia("secciones.json", codigo, "cupo", f"demanda {pedidos} supera los {cupos} cupos ofrecidos")
