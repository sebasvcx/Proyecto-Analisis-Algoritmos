"""Casos con respuesta conocida (Sección 7.1, tipo 2).

Se construye primero una asignación válida para todos los estudiantes a la vez
(la "respuesta plantada") y de ella se derivan las solicitudes:

1. Se crean materias, edificios con sus traslados y una oferta de secciones.
2. Para cada estudiante se arma un horario con secciones compatibles entre sí:
   sin choques (R3), con traslado posible (R8) y sin pasar el tope de créditos (R5).
3. El cupo de cada sección es exactamente cuántos estudiantes la tienen en la
   respuesta plantada (R4 queda justa), más secciones "señuelo" sin cupo de sobra
   o que chocan, para que el algoritmo tenga que elegir bien.
4. Las materias plantadas pasan a ser las solicitudes, con prioridades al azar.
   Se agregan franjas obligatorias en horas libres (R6) y vetos solo a profesores
   de secciones señuelo (R7), así la respuesta plantada sigue siendo válida.

Como la respuesta plantada atiende el 100 % de las solicitudes con principales,
su vector (C5..C1) es el máximo posible: cualquier asignación que atienda menos
es peor según la Sección 5.4. No es necesariamente la mejor en satisfacción.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

DIAS = ("L", "M", "X", "J", "V", "S")
EDIFICIOS = (("A", 0, 0), ("B", 4, 1), ("C", 7, 5), ("D", 2, 8))
TOPE_CREDITOS = 20
SALIDA_ANTICIPADA = 10


@dataclass(frozen=True)
class CasoConocido:
    crudos: dict[str, Any]  # JSON de entrada, listos para `cargar_instancia`
    respuesta: dict[str, dict[str, str]]  # estudiante -> {materia: sección}

    def salida_de_referencia(self) -> list[dict]:
        """La respuesta plantada con el formato de la salida (para el verificador y las métricas)."""
        estudiantes = []
        creditos = {m["codigo"]: m["creditos"] for m in self.crudos["materias"]}
        for est in self.crudos["estudiantes"]:
            asignadas = self.respuesta[est["id"]]
            estudiantes.append(
                {
                    "id": est["id"],
                    "creditos": sum(creditos[m] for m in asignadas),
                    "solicitudes": [
                        {"materia": s["codigo"], "prioridad": s["prioridad"], "estado": "principal", "seccion": asignadas[s["codigo"]], "materia_inscrita": s["codigo"]}
                        for s in est["materias"]
                    ],
                    "avisos": [],
                }
            )
        return estudiantes


def _minutos(h: int) -> int:
    return h * 60


def _caminata(a: str, b: str) -> int:
    if a == b:
        return 0
    (_, xa, ya), (_, xb, yb) = (next(e for e in EDIFICIOS if e[0] == x) for x in (a, b))
    return max(2, abs(xa - xb) + abs(ya - yb))


def _compatible(sesiones_horario: list[tuple[str, int, str]], seccion: dict) -> bool:
    """Choques (R3) y traslados (R8) entre las sesiones nuevas y las del horario. Cada sesión: (día, hora, edificio)."""
    nuevas = [(s["dia"], int(s["inicio"][:2]), s["edificio"]) for s in seccion["sesiones"]]
    todas = sesiones_horario + nuevas
    for dia in {d for d, _, _ in nuevas}:
        del_dia = sorted((h, e) for d, h, e in todas if d == dia)
        for (h1, e1), (h2, e2) in zip(del_dia, del_dia[1:]):
            libres = _minutos(h2) - _minutos(h1 + 2)
            if libres < 0 or _caminata(e1, e2) > libres + SALIDA_ANTICIPADA:
                return False
    return True


def generar_conocido(semilla: int, estudiantes: int = 30, materias: int = 10, *, desempate_semestre: bool = False) -> CasoConocido:
    rng = random.Random(semilla)

    lista_materias = [
        {"codigo": f"K{i:02d}", "nombre": f"Materia {i}", "creditos": rng.choice((2, 3, 3, 4)), "semestre": rng.randint(1, 10)}
        for i in range(1, materias + 1)
    ]
    creditos = {m["codigo"]: m["creditos"] for m in lista_materias}

    # Oferta: 2 o 3 secciones por materia; cada sección con su profesor y salón (la oferta siempre es válida)
    secciones: list[dict] = []
    profesores: list[dict] = []
    for m in lista_materias:
        for k in range(1, rng.randint(2, 3) + 1):
            profesores.append({"id": f"P{len(profesores) + 1:02d}", "nombre": f"Profesor {len(profesores) + 1}"})
            edificio = rng.choice(EDIFICIOS)[0]
            hora = rng.randrange(7, 19)
            dias = rng.sample(DIAS, 2) if m["creditos"] >= 3 else [rng.choice(DIAS)]
            sid = f"{m['codigo']}-{k}"
            secciones.append(
                {
                    "id": sid,
                    "materia": m["codigo"],
                    "profesor": profesores[-1]["id"],
                    "cupo": 0,
                    "sesiones": [
                        {"dia": d, "inicio": f"{hora:02d}:00", "fin": f"{hora + 2:02d}:00", "edificio": edificio, "salon": f"{edificio}-{sid}"}
                        for d in sorted(dias, key=DIAS.index)
                    ],
                }
            )
    por_materia: dict[str, list[dict]] = {}
    for s in secciones:
        por_materia.setdefault(s["materia"], []).append(s)

    # Respuesta plantada: horarios válidos construidos estudiante por estudiante
    respuesta: dict[str, dict[str, str]] = {}
    lista_estudiantes: list[dict] = []
    for i in range(1, estudiantes + 1):
        eid = f"e{i:03d}"
        horario: dict[str, str] = {}
        sesiones: list[tuple[str, int, str]] = []
        objetivo = rng.randint(2, 5)
        for codigo in rng.sample(list(por_materia), len(por_materia)):
            if len(horario) == objetivo:
                break
            if sum(creditos[m] for m in horario) + creditos[codigo] > TOPE_CREDITOS:
                continue
            opciones = [s for s in por_materia[codigo] if _compatible(sesiones, s)]
            if not opciones:
                continue
            elegida = rng.choice(opciones)
            elegida["cupo"] += 1
            horario[codigo] = elegida["id"]
            sesiones += [(s["dia"], int(s["inicio"][:2]), s["edificio"]) for s in elegida["sesiones"]]
        respuesta[eid] = horario

        est: dict[str, Any] = {
            "id": eid,
            "nombre": f"Estudiante {eid}",
            "semestre": rng.randint(1, 10),
            "materias": [{"codigo": c, "prioridad": rng.randint(1, 5)} for c in sorted(horario)],
        }
        # R6: una franja obligatoria en un bloque libre de su horario plantado
        if rng.random() < 0.4:
            ocupados = {(d, h + k) for d, h, _ in sesiones for k in (0, 1)}
            libres = [(d, h) for d in DIAS for h in range(7, 19) if (d, h) not in ocupados and (d, h + 1) not in ocupados]
            if libres:
                d, h = rng.choice(libres)
                est["franjas_libres"] = [{"dia": d, "inicio": f"{h:02d}:00", "fin": f"{h + 2:02d}:00", "tipo": "obligatoria"}]
        # R7: veto a un profesor de una sección que el estudiante NO tiene en su respuesta
        if rng.random() < 0.3:
            ajenas = [s["profesor"] for c in horario for s in por_materia[c] if s["id"] != horario[c]]
            if ajenas:
                est["profesores"] = [{"id": rng.choice(ajenas), "veto": True}]
        lista_estudiantes.append(est)

    # Secciones que nadie tiene en la respuesta: señuelos con cupo 1 (atraen pero no alcanzan para todos)
    for s in secciones:
        if s["cupo"] == 0:
            s["cupo"] = 1

    rng.shuffle(lista_estudiantes)  # el orden del archivo no debe delatar la construcción
    traslados = [
        {"origen": a[0], "destino": b[0], "minutos": _caminata(a[0], b[0])} for i, a in enumerate(EDIFICIOS) for b in EDIFICIOS[i + 1 :]
    ]
    crudos = {
        "materias": lista_materias,
        "profesores": profesores,
        "edificios": [{"id": e, "nombre": f"Edificio {e}"} for e, _, _ in EDIFICIOS],
        "traslados": traslados,
        "secciones": secciones,
        "estudiantes": lista_estudiantes,
        "config": {"max_creditos": TOPE_CREDITOS, "desempate_semestre": desempate_semestre, "semilla": semilla},
    }
    return CasoConocido(crudos, respuesta)
