"""Constructores compactos para escribir casos de prueba pequeños y legibles."""

from __future__ import annotations

from typing import Any


def sesion(dia: str, inicio: str, edificio: str = "B1", salon: str | None = None) -> dict:
    h = int(inicio[:2])
    return {"dia": dia, "inicio": inicio, "fin": f"{h + 2:02d}:00", "edificio": edificio, "salon": salon or f"{edificio}-101"}


def seccion(sid: str, materia: str, *sesiones: dict, profesor: str = "P1", cupo: int = 30) -> dict:
    return {"id": sid, "materia": materia, "profesor": profesor, "cupo": cupo, "sesiones": list(sesiones)}


def estudiante(eid: str, *materias: tuple, semestre: int = 5, **preferencias: Any) -> dict:
    """`materias`: tuplas (código, prioridad) o (código, prioridad, [sustitutas])."""
    solicitudes = []
    for m in materias:
        s = {"codigo": m[0], "prioridad": m[1]}
        if len(m) > 2:
            s["sustitutas"] = list(m[2])
        solicitudes.append(s)
    return {"id": eid, "nombre": f"Estudiante {eid}", "semestre": semestre, "materias": solicitudes, **preferencias}


def instancia(
    materias: dict[str, int],
    secciones: list[dict],
    estudiantes: list[dict],
    *,
    profesores: tuple[str, ...] = ("P1", "P2", "P3"),
    edificios: tuple[str, ...] = ("B1",),
    traslados: list[dict] | None = None,
    config: dict | None = None,
) -> dict[str, Any]:
    """`materias`: código -> créditos."""
    crudos: dict[str, Any] = {
        "materias": [{"codigo": c, "nombre": f"Materia {c}", "creditos": cr, "semestre": 1} for c, cr in materias.items()],
        "profesores": [{"id": p, "nombre": f"Prof {p}"} for p in profesores],
        "edificios": [{"id": e, "nombre": f"Edificio {e}"} for e in edificios],
        "traslados": traslados if traslados is not None else [
            {"origen": a, "destino": b, "minutos": 5} for i, a in enumerate(edificios) for b in edificios[i + 1 :]
        ],
        "secciones": secciones,
        "estudiantes": estudiantes,
    }
    if config is not None:
        crudos["config"] = config
    return crudos
