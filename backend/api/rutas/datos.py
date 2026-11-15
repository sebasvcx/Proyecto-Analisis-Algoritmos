from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from asignador.datos import ARCHIVOS
from asignador.generador import ParametrosGeneracion, generar_instancia

from ..dependencias import Repositorio
from ..esquemas import PeticionGenerar

router = APIRouter(prefix="/api/datos", tags=["datos"])


def _entidad_valida(entidad: str) -> None:
    if entidad not in ARCHIVOS:
        raise HTTPException(404, f"entidad desconocida '{entidad}'; use {', '.join(ARCHIVOS)}")


@router.get("")
def resumen(repo: Repositorio) -> dict:
    """Archivos presentes, número de registros y resultado de la validación."""
    return repo.resumen()


@router.get("/{entidad}")
def leer(entidad: str, repo: Repositorio) -> Any:
    _entidad_valida(entidad)
    contenido = repo.leer_entidad(entidad)
    if contenido is None:
        raise HTTPException(404, f"{ARCHIVOS[entidad]} no existe o no se pudo leer")
    return contenido


@router.put("/{entidad}")
def reemplazar(entidad: str, repo: Repositorio, contenido: Any = Body(...)) -> dict:
    """Reemplaza un archivo (se respalda antes) y devuelve la nueva validación."""
    _entidad_valida(entidad)
    esperado = dict if entidad == "config" else list
    if not isinstance(contenido, esperado):
        raise HTTPException(422, f"{ARCHIVOS[entidad]} debe ser {'un objeto' if esperado is dict else 'una lista'}")
    repo.reemplazar({entidad: contenido})
    return repo.resumen()


@router.post("/generar")
def generar(peticion: PeticionGenerar, repo: Repositorio) -> dict:
    """Genera una instancia sintética y reemplaza todos los archivos."""
    try:
        parametros = ParametrosGeneracion(**peticion.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    respaldo = repo.reemplazar(generar_instancia(parametros))
    return {**repo.resumen(), "respaldo": respaldo.name if respaldo else None}
