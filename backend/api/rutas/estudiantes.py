"""Edición de un estudiante (pantalla Preferencias).

Guardar valida antes de escribir: se construye la instancia con el estudiante
nuevo y, si aparece algún error en su registro, no se guarda nada y se
devuelven los errores para mostrarlos en el formulario. Los errores que ya
existían en otros registros no bloquean la edición.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from asignador.datos import construir_instancia

from ..dependencias import Repositorio

router = APIRouter(prefix="/api/estudiantes", tags=["estudiantes"])


def _problemas_del_estudiante(reporte, eid: str) -> tuple[list[dict], list[dict]]:
    propios = [p for p in reporte.problemas if p.archivo == "estudiantes.json" and p.registro == eid]
    errores = [p.como_dict() for p in propios if p.gravedad.value == "error"]
    advertencias = [p.como_dict() for p in propios if p.gravedad.value == "advertencia"]
    return errores, advertencias


@router.put("/{eid}")
def guardar(eid: str, repo: Repositorio, estudiante: dict[str, Any] = Body(...)) -> dict:
    """Crea o reemplaza el estudiante `eid` en estudiantes.json."""
    if estudiante.get("id") != eid:
        raise HTTPException(422, {"mensaje": "el código del estudiante no coincide con la ruta", "problemas": []})

    crudos, fallos = repo.leer()
    lista = list(crudos.get("estudiantes") or [])
    posicion = next((i for i, e in enumerate(lista) if isinstance(e, dict) and e.get("id") == eid), None)
    if posicion is None:
        lista.append(estudiante)
    else:
        lista[posicion] = estudiante

    _, reporte = construir_instancia({**crudos, "estudiantes": lista}, fallos)
    errores, advertencias = _problemas_del_estudiante(reporte, eid)
    if errores:
        raise HTTPException(422, {"mensaje": "no se guardó: corrija los errores del formulario", "problemas": errores})

    repo.reemplazar({"estudiantes": lista})
    return {"estudiante": estudiante, "creado": posicion is None, "advertencias": advertencias}
