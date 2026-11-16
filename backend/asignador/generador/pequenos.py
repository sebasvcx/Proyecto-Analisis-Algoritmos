"""Instancias pequeñas para comparar con la solución exacta (Sección 7.3).

De 2 a 6 estudiantes, de 1 a 3 solicitudes por estudiante y de 1 a 2 secciones
por materia, con pocos cupos y pocas franjas para que haya competencia y choques.
Cada sección tiene su propio profesor y salón, así que la oferta siempre es válida.
"""

from __future__ import annotations

import random
from typing import Any

DIAS = ("L", "M")
HORAS = ("07:00", "09:00", "11:00")
EDIFICIOS = ("A", "B")


def generar_pequena(semilla: int, *, desempate_semestre: bool = False) -> dict[str, Any]:
    rng = random.Random(semilla)
    n_materias = rng.randint(2, 4)
    materias = [{"codigo": f"M{i}", "nombre": f"Materia {i}", "creditos": rng.randint(1, 6), "semestre": rng.randint(1, 10)} for i in range(1, n_materias + 1)]

    secciones, profesores = [], []
    for m in materias:
        for k in range(1, rng.randint(1, 2) + 1):
            sid = f"{m['codigo']}-{k}"
            profesores.append({"id": f"P{len(profesores) + 1}", "nombre": f"Profesor {len(profesores) + 1}"})
            inicio = rng.choice(HORAS)
            edificio = rng.choice(EDIFICIOS)
            secciones.append(
                {
                    "id": sid,
                    "materia": m["codigo"],
                    "profesor": profesores[-1]["id"],
                    "cupo": rng.randint(1, 2),
                    "sesiones": [
                        {
                            "dia": rng.choice(DIAS),
                            "inicio": inicio,
                            "fin": f"{int(inicio[:2]) + 2:02d}:00",
                            "edificio": edificio,
                            "salon": f"{edificio}-{sid}",
                        }
                    ],
                }
            )

    codigos = [m["codigo"] for m in materias]
    ids = [f"e{i:02d}" for i in range(1, rng.randint(2, 6) + 1)]
    estudiantes = []
    for eid in ids:
        pedidas = rng.sample(codigos, k=rng.randint(1, min(3, len(codigos))))
        solicitudes = []
        for codigo in pedidas:
            s: dict[str, Any] = {"codigo": codigo, "prioridad": rng.randint(1, 5)}
            libres = [c for c in codigos if c not in pedidas]
            if libres and rng.random() < 0.3:
                s["sustitutas"] = [rng.choice(libres)]
            solicitudes.append(s)
        est: dict[str, Any] = {"id": eid, "nombre": f"Estudiante {eid}", "semestre": rng.randint(1, 10), "materias": solicitudes}
        opiniones = []
        for p in rng.sample(profesores, k=min(len(profesores), rng.randint(0, 2))):
            opiniones.append({"id": p["id"], "veto": True} if rng.random() < 0.1 else {"id": p["id"], "afinidad": rng.randint(-2, 2)})
        if opiniones:
            est["profesores"] = opiniones
        if rng.random() < 0.3:
            est["franjas_preferidas"] = [{"dia": "*", "inicio": "07:00", "fin": "11:00"}]
        otros = [o for o in ids if o != eid]
        if otros and rng.random() < 0.3:
            est["social"] = [{"estudiante": rng.choice(otros), "afinidad": rng.choice((-2, -1, 1, 2))}]
        if rng.random() < 0.5:
            est["importancia"] = {c: rng.choice(("alta", "media", "baja")) for c in ("horario", "profesores", "cercania", "huecos", "social")}
        estudiantes.append(est)

    return {
        "materias": materias,
        "profesores": profesores,
        "edificios": [{"id": e, "nombre": f"Edificio {e}"} for e in EDIFICIOS],
        "traslados": [{"origen": "A", "destino": "B", "minutos": rng.choice((5, 15))}],
        "secciones": secciones,
        "estudiantes": estudiantes,
        "config": {"desempate_semestre": desempate_semestre},
    }
