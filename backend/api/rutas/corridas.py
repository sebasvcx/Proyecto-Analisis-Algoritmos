from __future__ import annotations

from fastapi import APIRouter, HTTPException

from asignador.algoritmo import NIVELES, NivelNoDisponible
from asignador.corrida import ejecutar_corrida, guardar_corrida, leer_corrida, leer_entrada_corrida, listar_corridas

from ..dependencias import AjustesDep, Repositorio
from ..esquemas import PeticionCorrida

router = APIRouter(prefix="/api", tags=["corridas"])


@router.get("/niveles")
def niveles() -> list[dict]:
    return [
        {"numero": n.numero, "nombre": n.nombre, "descripcion": n.descripcion, "disponible": n.disponible, "reglas": list(n.reglas_cubiertas)}
        for n in NIVELES.values()
    ]


@router.get("/corridas")
def corridas(ajustes: AjustesDep) -> list[dict]:
    return listar_corridas(ajustes.carpeta_resultados)


@router.get("/corridas/{identificador}")
def corrida(identificador: str, ajustes: AjustesDep) -> dict:
    salida = leer_corrida(ajustes.carpeta_resultados, identificador)
    if salida is None:
        raise HTTPException(404, f"no existe la corrida '{identificador}'")
    return salida


@router.get("/corridas/{identificador}/entrada/{entidad}")
def entrada(identificador: str, entidad: str, ajustes: AjustesDep):
    contenido = leer_entrada_corrida(ajustes.carpeta_resultados, identificador, entidad)
    if contenido is None:
        raise HTTPException(404, f"la corrida '{identificador}' no tiene '{entidad}'")
    return contenido


@router.post("/corridas", status_code=201)
def ejecutar(peticion: PeticionCorrida, repo: Repositorio, ajustes: AjustesDep) -> dict:
    instancia, reporte, crudos = repo.cargar()
    if instancia is None:
        raise HTTPException(
            422,
            {"mensaje": "los datos tienen errores; corríjalos antes de ejecutar", "problemas": [p.como_dict() for p in reporte.errores]},
        )
    try:
        salida = ejecutar_corrida(instancia, peticion.nivel)
    except NivelNoDisponible as exc:
        raise HTTPException(422, str(exc)) from exc
    guardar_corrida(ajustes.carpeta_resultados, salida, crudos)
    return salida
