"""Generador de escenarios variados (Sección 7.1, tipo 1).

Orden de generación: materias, profesores, edificios y traslados; después las
solicitudes de los estudiantes; luego las secciones (horario, profesor y salón
sin cruces) y por último los cupos según la demanda y la escasez pedida.
Toda decisión aleatoria pasa por un único `random.Random(semilla)`.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from ..dominio.tiempo import DIAS
from . import catalogo

VERSION_GENERADOR = "0.1.0"


class Escasez(str, Enum):
    HOLGADA = "holgada"
    AJUSTADA = "ajustada"
    ESCASA = "escasa"

    @property
    def factor(self) -> float:
        return {"holgada": 1.3, "ajustada": 1.0, "escasa": 0.7}[self.value]


@dataclass(frozen=True)
class ParametrosGeneracion:
    estudiantes: int = 250
    secciones: int = 96
    porcentaje_trabaja: float = 0.2
    escasez: Escasez = Escasez.AJUSTADA
    semilla: int = 42
    prob_sustituta: float = 0.25
    prob_veto: float = 0.05
    max_intentos: int = 60

    def __post_init__(self) -> None:
        if self.estudiantes < 0:
            raise ValueError("el número de estudiantes no puede ser negativo")
        if self.secciones < len(catalogo.MATERIAS):
            raise ValueError(f"se necesitan al menos {len(catalogo.MATERIAS)} secciones (una por materia)")
        if not 0 <= self.porcentaje_trabaja <= 1:
            raise ValueError("el porcentaje que trabaja debe estar entre 0 y 1")


def _hora(h: int) -> str:
    return f"{h:02d}:00"


class _Generador:
    def __init__(self, p: ParametrosGeneracion):
        self.p = p
        self.rng = random.Random(p.semilla)

    # --- oferta ---------------------------------------------------------

    def materias(self) -> list[dict]:
        return [{"codigo": c, "nombre": n, "creditos": cr, "semestre": s} for c, n, cr, s, _ in catalogo.MATERIAS]

    def profesores(self) -> list[dict]:
        cantidad = max(12, math.ceil(self.p.secciones / 3))
        # Cada departamento recibe profesores en proporción a sus materias (al menos uno)
        carga = Counter(m[4] for m in catalogo.MATERIAS)
        cupos = {d: max(1, round(cantidad * n / len(catalogo.MATERIAS))) for d, n in carga.items()}
        departamentos = [d for d in sorted(cupos) for _ in range(cupos[d])]
        nombres = self._nombres_unicos(len(departamentos))
        return [
            {"id": f"p{i + 1:02d}", "nombre": f"Prof. {nombre}", "departamento": depto}
            for i, (nombre, depto) in enumerate(zip(nombres, departamentos))
        ]

    def edificios(self) -> list[dict]:
        return [{"id": e, "nombre": n} for e, n, _, _ in catalogo.EDIFICIOS]

    def traslados(self) -> list[dict]:
        puntos = {e: (x, y) for e, _, x, y in catalogo.EDIFICIOS}
        ids = sorted(puntos)
        resultado = []
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                (xa, ya), (xb, yb) = puntos[a], puntos[b]
                minutos = max(2, round(abs(xa - xb) + abs(ya - yb)))  # distancia "por andenes"
                resultado.append({"origen": a, "destino": b, "minutos": minutos})
        return resultado

    def secciones(self, demanda: Counter[str], profesores: list[dict]) -> list[dict]:
        materias = catalogo.MATERIAS
        cantidad = self._repartir_secciones(demanda)
        self._todos_los_profesores = [p["id"] for p in profesores]
        por_departamento = defaultdict(list)
        for prof in profesores:
            por_departamento[prof["departamento"]].append(prof["id"])

        ocupado_prof: set[tuple[str, str, int]] = set()  # (profesor, día, hora)
        ocupado_salon: set[tuple[str, str, int]] = set()  # (salón, día, hora)
        secciones = []
        for codigo, _, creditos, _, depto in materias:
            n = cantidad[codigo]
            cupo_total = math.ceil(demanda[codigo] * self.p.escasez.factor)
            cupos = self._repartir(max(cupo_total, n * 5), n)  # mínimo 5 cupos por sección
            candidatos = por_departamento[depto] or [p["id"] for p in profesores]
            for i in range(n):
                seccion = self._ubicar_seccion(codigo, i + 1, creditos, candidatos, ocupado_prof, ocupado_salon)
                if seccion is None:
                    continue  # se agotaron los intentos; la materia queda con menos secciones
                seccion["cupo"] = cupos[i]
                secciones.append(seccion)
        return secciones

    def _ubicar_seccion(self, codigo, numero, creditos, candidatos, ocupado_prof, ocupado_salon) -> dict | None:
        rng = self.rng
        for intento in range(self.p.max_intentos):
            # primero se intenta con el departamento; si no hay espacio, con cualquier profesor
            if intento == self.p.max_intentos // 2:
                candidatos = self._todos_los_profesores
            dias = rng.choice(catalogo.PATRONES_DOS_SESIONES) if creditos >= 3 else (rng.choice(catalogo.DIAS_UNA_SESION),)
            hora = rng.choice(range(7, 19))
            profesor = rng.choice(candidatos)
            edificio = rng.choice(catalogo.EDIFICIOS)[0]
            salon = f"{edificio}-{rng.choice((1, 2, 3))}{rng.randint(1, 12):02d}"
            bloques = [(d, h) for d in dias for h in (hora, hora + 1)]
            if any((profesor, d, h) in ocupado_prof for d, h in bloques):
                continue
            if any((salon, d, h) in ocupado_salon for d, h in bloques):
                continue
            for d, h in bloques:
                ocupado_prof.add((profesor, d, h))
                ocupado_salon.add((salon, d, h))
            return {
                "id": f"{codigo}-{numero:02d}",
                "materia": codigo,
                "profesor": profesor,
                "cupo": 0,
                "sesiones": [
                    {"dia": d, "inicio": _hora(hora), "fin": _hora(hora + 2), "edificio": edificio, "salon": salon} for d in dias
                ],
            }
        return None

    def _repartir_secciones(self, demanda: Counter[str]) -> dict[str, int]:
        """Una sección por materia y el resto proporcional a la demanda."""
        codigos = [m[0] for m in catalogo.MATERIAS]
        extra = self.p.secciones - len(codigos)
        total = sum(demanda.values()) or 1
        cantidad = {c: 1 + math.floor(extra * demanda[c] / total) for c in codigos}
        sobrantes = self.p.secciones - sum(cantidad.values())
        for c in sorted(codigos, key=lambda c: (-demanda[c], c))[:sobrantes]:
            cantidad[c] += 1
        return cantidad

    def _repartir(self, total: int, partes: int) -> list[int]:
        base, resto = divmod(total, partes)
        return [base + (1 if i < resto else 0) for i in range(partes)]

    # --- estudiantes ----------------------------------------------------

    def estudiantes(self, profesores: list[dict]) -> list[dict]:
        rng = self.rng
        nombres = self._nombres_unicos(self.p.estudiantes)
        ids = [f"e{i + 1:03d}" for i in range(self.p.estudiantes)]
        por_semestre = defaultdict(list)
        for codigo, _, creditos, semestre, _ in catalogo.MATERIAS:
            por_semestre[semestre].append((codigo, creditos))
        resultado = []
        for eid, nombre in zip(ids, nombres):
            semestre = rng.randint(1, 10)
            materias = self._solicitudes(semestre, por_semestre)
            estudiante: dict[str, Any] = {"id": eid, "nombre": nombre, "semestre": semestre, "materias": materias}
            estudiante.update(self._preferencias(eid, ids, profesores))
            resultado.append(estudiante)
        return resultado

    def _solicitudes(self, semestre: int, por_semestre) -> list[dict]:
        rng = self.rng
        cercanas = [m for s in (semestre, semestre - 1, semestre + 1) for m in por_semestre.get(s, [])]
        cantidad = min(len(cercanas), rng.randint(3, 6))
        elegidas = rng.sample(cercanas, cantidad)
        principales = {c for c, _ in elegidas}
        solicitudes = []
        for codigo, _ in elegidas:
            solicitud: dict[str, Any] = {"codigo": codigo, "prioridad": rng.choices((1, 2, 3, 4, 5), weights=(1, 2, 3, 3, 3))[0]}
            if rng.random() < self.p.prob_sustituta:
                opciones = [c for c, _ in cercanas if c not in principales]
                if opciones:
                    solicitud["sustitutas"] = [rng.choice(opciones)]
            solicitudes.append(solicitud)
        return solicitudes

    def _preferencias(self, eid: str, ids: list[str], profesores: list[dict]) -> dict:
        rng = self.rng
        pref: dict[str, Any] = {}
        libres = []
        if rng.random() < self.p.porcentaje_trabaja:
            dia = rng.choice(DIAS)
            libres.append({"dia": dia, "inicio": "14:00", "fin": "20:00", "tipo": "obligatoria"})
            if rng.random() < 0.5:
                otro = rng.choice([d for d in DIAS if d != dia])
                libres.append({"dia": otro, "inicio": "14:00", "fin": "20:00", "tipo": "obligatoria"})
        if rng.random() < 0.4:
            libres.append({"dia": "*", "inicio": "13:00", "fin": "14:00", "tipo": "deseable"})
        if libres:
            pref["franjas_libres"] = libres

        jornada = rng.random()
        if jornada < 0.35:
            pref["franjas_preferidas"] = [{"dia": "*", "inicio": "07:00", "fin": "13:00"}]
        elif jornada < 0.55:
            pref["franjas_preferidas"] = [{"dia": "*", "inicio": "13:00", "fin": "20:00"}]
        if rng.random() < 0.3:
            pref["franjas_evitadas"] = [{"dia": "*", "inicio": "07:00", "fin": "09:00"}]

        opiniones = []
        for prof in rng.sample(profesores, k=min(len(profesores), rng.randint(0, 3))):
            if rng.random() < self.p.prob_veto:
                opiniones.append({"id": prof["id"], "veto": True})
            else:
                opiniones.append({"id": prof["id"], "afinidad": rng.choice((-2, -1, 1, 2))})
        if opiniones:
            pref["profesores"] = opiniones

        otros = [i for i in ids if i != eid]
        social = [{"estudiante": o, "afinidad": rng.choice((2, 2, 1, -2))} for o in rng.sample(otros, k=min(len(otros), rng.randint(0, 2)))]
        if social:
            pref["social"] = social

        if rng.random() < 0.6:
            niveles = ("baja", "media", "alta")
            pref["importancia"] = {c: rng.choice(niveles) for c in ("horario", "profesores", "cercania", "huecos", "social")}
        return pref

    # --- utilidades -----------------------------------------------------

    def _nombres_unicos(self, cantidad: int) -> list[str]:
        combinaciones = [f"{n} {a}" for n in catalogo.NOMBRES for a in catalogo.APELLIDOS]
        self.rng.shuffle(combinaciones)
        if cantidad <= len(combinaciones):
            return combinaciones[:cantidad]
        # más personas que combinaciones: se agrega un segundo apellido
        return [f"{combinaciones[i % len(combinaciones)]} {catalogo.APELLIDOS[i // len(combinaciones) % len(catalogo.APELLIDOS)]}" for i in range(cantidad)]


def generar_instancia(parametros: ParametrosGeneracion | None = None) -> dict[str, Any]:
    """Devuelve el contenido de todos los JSON de una instancia, listo para escribir."""
    p = parametros or ParametrosGeneracion()
    g = _Generador(p)
    materias = g.materias()
    profesores = g.profesores()
    estudiantes = g.estudiantes(profesores)
    demanda = Counter(s["codigo"] for e in estudiantes for s in e["materias"])
    secciones = g.secciones(demanda, profesores)
    datos_param = asdict(p)
    datos_param["escasez"] = p.escasez.value
    return {
        "materias": materias,
        "profesores": profesores,
        "edificios": g.edificios(),
        "traslados": g.traslados(),
        "secciones": secciones,
        "estudiantes": estudiantes,
        "config": {
            "max_creditos": 20,
            "valor_sustituta": 0.8,
            "desempate_semestre": False,
            "semilla": p.semilla,
            "max_cambios": 10_000,
            "generador": {"version": VERSION_GENERADOR, "parametros": datos_param},
        },
    }
